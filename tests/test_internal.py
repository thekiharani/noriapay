from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
import requests

from noriapay import (
    ApiError,
    AuthenticationError,
    ConfigurationError,
    Hooks,
    MpesaClient,
    NetworkError,
    RetryDecisionContext,
    RetryPolicy,
    SasaPayClient,
    TimeoutError,
)
from noriapay.http import HttpClient, _normalize_hook_sequence
from noriapay.oauth import ClientCredentialsTokenProvider
from noriapay.types import HttpRequestOptions
from noriapay.utils import (
    append_path,
    build_error_message,
    encode_basic_auth,
    merge_headers,
    normalize_headers,
    parse_response_body,
    to_amount_string,
    to_object,
)


@dataclass(slots=True)
class FakeResponse:
    status_code: int
    payload: Any = None
    headers: dict[str, str] = field(default_factory=lambda: {"content-type": "application/json"})
    text_value: str = ""
    json_error: Exception | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if self.json_error is not None:
            raise self.json_error
        return self.payload

    @property
    def text(self) -> str:
        return self.text_value


@dataclass(slots=True)
class FakeSession:
    responses: list[Any]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def request(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("No fake responses left.")

        next_response = self.responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


def test_utils_cover_non_json_and_helper_paths() -> None:
    assert append_path("https://api.example.com/", "v1/test") == "https://api.example.com/v1/test"
    assert append_path("https://api.example.com", "https://override.example.com/path") == (
        "https://override.example.com/path"
    )
    assert encode_basic_auth("user", "pass") == "dXNlcjpwYXNz"
    assert to_amount_string("1.00") == "1.00"
    assert to_amount_string(1) == "1"
    assert to_amount_string(1.50) == "1.5"

    assert parse_response_body(FakeResponse(200, {"ok": True})) == {"ok": True}
    assert parse_response_body(
        FakeResponse(
            200,
            headers={"content-type": "text/plain"},
            text_value='{"hello":"world"}',
        )
    ) == {"hello": "world"}
    assert (
        parse_response_body(
            FakeResponse(
                200,
                headers={"content-type": "text/plain"},
                text_value="raw text",
            )
        )
        == "raw text"
    )
    assert parse_response_body(FakeResponse(200, headers={"content-type": "text/plain"})) is None

    assert to_object({"ok": True}) == {"ok": True}
    assert to_object("nope") == {}
    assert build_error_message(400, {"errorMessage": "provider error"}) == "provider error"
    assert build_error_message(422, {"detail": "invalid"}) == "invalid"
    assert build_error_message(500, {"message": "broken"}) == "broken"
    assert build_error_message(418, {"missing": "message"}) == "Request failed with status 418"
    assert normalize_headers(None) == {}
    assert normalize_headers({"x-test": "1"}) == {"x-test": "1"}
    assert merge_headers({"a": "1"}, None, {"b": "2"}) == {"a": "1", "b": "2"}


def test_http_client_creates_default_session_and_normalizes_hooks() -> None:
    client = HttpClient(base_url="https://example.com")
    assert isinstance(client.session, requests.Session)

    def hook(context: Any) -> None:
        return None

    assert _normalize_hook_sequence(None) == []
    assert _normalize_hook_sequence(hook) == [hook]
    assert _normalize_hook_sequence([hook]) == [hook]


def test_http_client_posts_text_and_runs_hooks() -> None:
    before_calls: list[str] = []
    after_bodies: list[object] = []

    def before_request(context: Any) -> None:
        before_calls.append(context.url)
        context.headers["x-hooked"] = "yes"

    def after_response(context: Any) -> None:
        after_bodies.append(context.response_body)

    session = FakeSession(
        responses=[
            FakeResponse(
                200,
                headers={"content-type": "text/plain"},
                text_value="ok",
            )
        ]
    )
    client = HttpClient(
        base_url="https://example.com",
        session=session,
        default_headers={"x-default": "1"},
        hooks=Hooks(
            before_request=before_request,
            after_response=after_response,
        ),
    )

    response = client.request(HttpRequestOptions(path="/echo", method="POST", body="hello"))

    assert response == "ok"
    assert before_calls == ["https://example.com/echo"]
    assert after_bodies == ["ok"]
    assert session.calls[0]["headers"]["x-default"] == "1"
    assert session.calls[0]["headers"]["x-hooked"] == "yes"
    assert session.calls[0]["headers"]["content-type"] == "text/plain;charset=UTF-8"


def test_http_client_retries_timeout_and_wraps_network_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    timeout_errors: list[Exception] = []

    def on_error(context: Any) -> None:
        timeout_errors.append(context.error)

    monkeypatch.setattr("noriapay.http.time.sleep", lambda seconds: sleeps.append(seconds))

    retrying_session = FakeSession(
        responses=[
            requests.Timeout("slow"),
            FakeResponse(200, {"status": "ok"}),
        ]
    )
    retrying_client = HttpClient(
        base_url="https://example.com",
        session=retrying_session,
        retry=RetryPolicy(
            max_attempts=2,
            retry_methods=("GET",),
            retry_on_network_error=True,
            base_delay_seconds=0.25,
        ),
        hooks=Hooks(on_error=on_error),
    )

    assert retrying_client.request(HttpRequestOptions(path="/timeout", method="GET")) == {
        "status": "ok"
    }
    assert isinstance(timeout_errors[0], TimeoutError)
    assert sleeps == [0.25]

    failing_session = FakeSession(responses=[requests.RequestException("boom")])
    failing_client = HttpClient(base_url="https://example.com", session=failing_session)
    with pytest.raises(NetworkError):
        failing_client.request(HttpRequestOptions(path="/network", method="GET"))


def test_http_client_covers_remaining_timeout_and_retry_guard_paths() -> None:
    timeout_client = HttpClient(
        base_url="https://example.com",
        session=FakeSession(responses=[requests.Timeout("still slow")]),
    )
    with pytest.raises(TimeoutError):
        timeout_client.request(HttpRequestOptions(path="/timeout-once", method="GET"))

    network_retry_client = HttpClient(
        base_url="https://example.com",
        session=FakeSession(
            responses=[
                requests.RequestException("temporary network issue"),
                FakeResponse(200, {"status": "recovered"}),
            ]
        ),
        retry=RetryPolicy(
            max_attempts=2,
            retry_methods=("GET",),
            retry_on_network_error=True,
        ),
    )
    assert network_retry_client.request(
        HttpRequestOptions(path="/network-retry", method="GET")
    ) == {"status": "recovered"}

    impossible_client = HttpClient(
        base_url="https://example.com",
        session=FakeSession(responses=[]),
        retry=RetryPolicy(max_attempts=0),
    )
    with pytest.raises(RuntimeError, match="unreachable retry state"):
        impossible_client.request(HttpRequestOptions(path="/impossible", method="GET"))


def test_http_client_wraps_api_errors_and_covers_retry_helpers() -> None:
    on_error_payloads: list[object] = []
    session = FakeSession(
        responses=[
            FakeResponse(500, {"message": "try again"}),
            FakeResponse(200, {"status": True}),
        ]
    )
    client = HttpClient(
        base_url="https://example.com",
        session=session,
        retry=RetryPolicy(
            max_attempts=2,
            retry_methods=("GET",),
            retry_on_statuses=(500,),
            should_retry=lambda context: context.status == 500,
        ),
        hooks=Hooks(on_error=lambda context: on_error_payloads.append(context.response_body)),
    )

    assert client.request(HttpRequestOptions(path="/status", method="GET")) == {"status": True}
    assert on_error_payloads == [{"message": "try again"}]

    api_session = FakeSession(responses=[FakeResponse(400, {"message": "bad request"})])
    api_client = HttpClient(base_url="https://example.com", session=api_session)
    with pytest.raises(ApiError) as error:
        api_client.request(HttpRequestOptions(path="/bad", method="GET"))
    assert error.value.status_code == 400

    base_retry = RetryPolicy(
        max_attempts=4,
        retry_methods=("GET",),
        retry_on_statuses=(500,),
        retry_on_network_error=True,
    )
    helper_client = HttpClient(
        base_url="https://example.com",
        session=FakeSession(responses=[]),
        retry=base_retry,
    )
    assert helper_client._resolve_retry_policy(False) is None
    assert helper_client._resolve_retry_policy(None) == base_retry
    override = RetryPolicy(max_attempts=3)
    merged = helper_client._resolve_retry_policy(override)
    assert merged is not None
    assert merged.max_attempts == 3
    assert merged.retry_methods == ("GET",)
    assert merged.retry_on_statuses == (500,)

    no_default_client = HttpClient(
        base_url="https://example.com",
        session=FakeSession(responses=[]),
    )
    assert no_default_client._resolve_retry_policy(override) == override
    assert not helper_client._should_retry(
        base_retry,
        RetryDecisionContext(
            attempt=1,
            max_attempts=2,
            method="POST",
            url="https://example.com",
            status=500,
        ),
    )
    assert not helper_client._should_retry(
        base_retry,
        RetryDecisionContext(
            attempt=1,
            max_attempts=2,
            method="GET",
            url="https://example.com",
            status=404,
        ),
    )
    assert not helper_client._should_retry(
        RetryPolicy(max_attempts=2, retry_methods=("GET",)),
        RetryDecisionContext(
            attempt=1,
            max_attempts=2,
            method="GET",
            url="https://example.com",
            error=NetworkError("network"),
        ),
    )
    helper_client._sleep_before_retry(None, 1)


def test_token_provider_caches_clears_and_wraps_failures() -> None:
    provider_without_session = ClientCredentialsTokenProvider(
        token_url="https://example.com/token",
        client_id="client-id",
        client_secret="client-secret",
    )
    assert isinstance(provider_without_session.session, requests.Session)

    session = FakeSession(
        responses=[
            FakeResponse(200, {"access_token": "token-1", "expires_in": 3600}),
            FakeResponse(200, {"access_token": "token-2", "expires_in": 3600}),
        ]
    )
    provider = ClientCredentialsTokenProvider(
        token_url="https://example.com/token",
        client_id="client-id",
        client_secret="client-secret",
        session=session,
    )

    assert provider.get_access_token() == "token-1"
    assert provider.get_token().access_token == "token-1"
    assert len(session.calls) == 1

    provider.clear_cache()
    assert provider.get_access_token() == "token-2"
    assert len(session.calls) == 2

    timeout_provider = ClientCredentialsTokenProvider(
        token_url="https://example.com/token",
        client_id="client-id",
        client_secret="client-secret",
        session=FakeSession(responses=[requests.Timeout("slow")]),
    )
    with pytest.raises(AuthenticationError):
        timeout_provider.get_token()

    network_provider = ClientCredentialsTokenProvider(
        token_url="https://example.com/token",
        client_id="client-id",
        client_secret="client-secret",
        session=FakeSession(responses=[requests.RequestException("boom")]),
    )
    with pytest.raises(AuthenticationError):
        network_provider.get_token()

    bad_response_provider = ClientCredentialsTokenProvider(
        token_url="https://example.com/token",
        client_id="client-id",
        client_secret="client-secret",
        session=FakeSession(
            responses=[
                FakeResponse(
                    401,
                    headers={"content-type": "application/json"},
                    json_error=ValueError("invalid json"),
                )
            ]
        ),
    )
    with pytest.raises(AuthenticationError):
        bad_response_provider.get_token()


def test_mpesa_client_covers_remaining_methods_and_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        MpesaClient()

    session = FakeSession(
        responses=[
            FakeResponse(200, {"access_token": "mpesa-token", "expires_in": 3600}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "stk query"}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "register"}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "b2c"}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "b2b"}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "reversal"}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "status"}),
            FakeResponse(200, {"ResponseCode": "0", "Result": "qr"}),
        ]
    )
    client = MpesaClient(
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        session=session,
    )

    assert client.get_access_token() == "mpesa-token"
    assert (
        client.stk_push_query(
            {
                "BusinessShortCode": "174379",
                "Password": "password",
                "Timestamp": "20250102030405",
                "CheckoutRequestID": "ws_CO_123",
            }
        )["Result"]
        == "stk query"
    )
    assert (
        client.register_c2b_urls(
            {
                "ShortCode": "600000",
                "ResponseType": "Completed",
                "ConfirmationURL": "https://example.com/confirm",
                "ValidationURL": "https://example.com/validate",
            },
            version="v1",
        )["Result"]
        == "register"
    )
    assert (
        client.b2c_payment(
            {
                "InitiatorName": "apiuser",
                "SecurityCredential": "EncryptedPassword",
                "CommandID": "BusinessPayment",
                "Amount": 10,
                "PartyA": "600000",
                "PartyB": "254700000000",
                "Remarks": "B2C",
                "QueueTimeOutURL": "https://example.com/timeout",
                "ResultURL": "https://example.com/result",
            }
        )["Result"]
        == "b2c"
    )
    assert (
        client.b2b_payment(
            {
                "Initiator": "apiuser",
                "SecurityCredential": "EncryptedPassword",
                "CommandID": "BusinessPayBill",
                "Amount": 20,
                "PartyA": "600000",
                "PartyB": "600001",
                "Remarks": "B2B",
                "AccountReference": "ACC-1",
                "QueueTimeOutURL": "https://example.com/timeout",
                "ResultURL": "https://example.com/result",
            }
        )["Result"]
        == "b2b"
    )
    assert (
        client.reversal(
            {
                "Initiator": "apiuser",
                "SecurityCredential": "EncryptedPassword",
                "CommandID": "TransactionReversal",
                "TransactionID": "LKXXXX1234",
                "Amount": 30,
                "ReceiverParty": "600000",
                "RecieverIdentifierType": "11",
                "ResultURL": "https://example.com/result",
                "QueueTimeOutURL": "https://example.com/timeout",
                "Remarks": "Reverse",
            }
        )["Result"]
        == "reversal"
    )
    assert (
        client.transaction_status(
            {
                "Initiator": "apiuser",
                "SecurityCredential": "EncryptedPassword",
                "CommandID": "TransactionStatusQuery",
                "TransactionID": "LKXXXX1234",
                "PartyA": "600000",
                "IdentifierType": "4",
                "ResultURL": "https://example.com/result",
                "QueueTimeOutURL": "https://example.com/timeout",
                "Remarks": "Status",
            }
        )["Result"]
        == "status"
    )
    assert (
        client.generate_qr_code(
            {
                "MerchantName": "Noria",
                "MerchantShortCode": "174379",
                "Amount": 40,
                "QRType": "Dynamic",
            }
        )["Result"]
        == "qr"
    )
    assert session.calls[1]["json"]["CheckoutRequestID"] == "ws_CO_123"
    assert session.calls[3]["json"]["Amount"] == "10"
    assert session.calls[7]["json"]["Amount"] == "40"


def test_sasapay_client_covers_remaining_methods_and_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        SasaPayClient(environment="sandbox")

    session = FakeSession(
        responses=[
            FakeResponse(200, {"access_token": "sasapay-token", "expires_in": 3600}),
            FakeResponse(200, {"status": True, "detail": "b2c"}),
            FakeResponse(200, {"status": True, "detail": "b2b"}),
        ]
    )
    client = SasaPayClient(
        client_id="client-id",
        client_secret="client-secret",
        environment="production",
        base_url="https://api.example.com/sasapay",
        session=session,
    )

    assert client.get_access_token() == "sasapay-token"
    assert (
        client.b2c_payment(
            {
                "MerchantCode": "600980",
                "Amount": 10,
                "Currency": "KES",
                "MerchantTransactionReference": "ref-1",
                "ReceiverNumber": "254700000080",
                "Channel": "63902",
                "Reason": "Payout",
                "CallBackURL": "https://example.com/callback",
            }
        )["detail"]
        == "b2c"
    )
    assert (
        client.b2b_payment(
            {
                "MerchantCode": "600980",
                "MerchantTransactionReference": "ref-2",
                "Currency": "KES",
                "Amount": 12,
                "ReceiverMerchantCode": "600981",
                "AccountReference": "ACC-2",
                "ReceiverAccountType": "merchant",
                "NetworkCode": "63902",
                "Reason": "Settlement",
                "CallBackURL": "https://example.com/callback",
            }
        )["detail"]
        == "b2b"
    )
    assert session.calls[1]["json"]["Amount"] == "10"
    assert session.calls[2]["json"]["Amount"] == "12"
