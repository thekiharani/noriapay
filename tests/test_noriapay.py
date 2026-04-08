from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from noriapay import (
    ConfigurationError,
    Hooks,
    MpesaClient,
    RequestOptions,
    RetryPolicy,
    SasaPayClient,
    build_mpesa_stk_password,
    build_mpesa_timestamp,
)


@dataclass(slots=True)
class FakeResponse:
    status_code: int
    payload: Any
    headers: dict[str, str] = field(default_factory=lambda: {"content-type": "application/json"})

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        return self.payload

    @property
    def text(self) -> str:
        return ""


@dataclass(slots=True)
class FakeSession:
    responses: list[FakeResponse]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def request(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("No fake responses left.")
        return self.responses.pop(0)


def test_build_mpesa_timestamp_formats_datetime() -> None:
    import datetime as dt

    timestamp = build_mpesa_timestamp(dt.datetime(2025, 1, 2, 3, 4, 5))
    assert timestamp == "20250102030405"


def test_build_mpesa_stk_password_encodes_components() -> None:
    value = build_mpesa_stk_password(
        business_short_code="174379",
        passkey="passkey",
        timestamp="20250102030405",
    )
    assert value == "MTc0Mzc5cGFzc2tleTIwMjUwMTAyMDMwNDA1"


def test_mpesa_client_authenticates_and_sends_stk_push() -> None:
    session = FakeSession(
        responses=[
            FakeResponse(200, {"access_token": "token-123", "expires_in": 3599}),
            FakeResponse(200, {"ResponseCode": "0", "CheckoutRequestID": "ws_CO_123"}),
        ]
    )

    client = MpesaClient(
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        environment="sandbox",
        session=session,
    )

    response = client.stk_push(
        {
            "BusinessShortCode": "174379",
            "Password": "password",
            "Timestamp": "20250102030405",
            "TransactionType": "CustomerPayBillOnline",
            "Amount": 1,
            "PartyA": "254700000000",
            "PartyB": "174379",
            "PhoneNumber": "254700000000",
            "CallBackURL": "https://example.com/callback",
            "AccountReference": "INV-001",
            "TransactionDesc": "Payment",
        }
    )

    assert response["ResponseCode"] == "0"
    assert len(session.calls) == 2
    assert session.calls[0]["params"] == {"grant_type": "client_credentials"}
    assert session.calls[1]["headers"]["authorization"] == "Bearer token-123"
    assert session.calls[1]["json"]["Amount"] == "1"


def test_mpesa_client_supports_external_tokens_hooks_and_headers() -> None:
    session = FakeSession(responses=[FakeResponse(200, {"ResponseCode": "0"})])
    token_calls = {"count": 0}

    class StaticTokenProvider:
        def get_access_token(self, force_refresh: bool = False) -> str:
            token_calls["count"] += 1
            return "external-token"

    def before_request(context: Any) -> None:
        context.headers["x-hook-header"] = "hooked"

    client = MpesaClient(
        token_provider=StaticTokenProvider(),
        default_headers={"x-client-header": "client"},
        hooks=Hooks(before_request=before_request),
        session=session,
    )

    client.account_balance(
        {
            "Initiator": "apiuser",
            "SecurityCredential": "EncryptedPassword",
            "CommandID": "AccountBalance",
            "PartyA": "600000",
            "IdentifierType": "4",
            "ResultURL": "https://example.com/result",
            "QueueTimeOutURL": "https://example.com/timeout",
            "Remarks": "Account balance",
        },
        options=RequestOptions(headers={"x-request-header": "request"}),
    )

    assert token_calls["count"] == 1
    assert session.calls[0]["headers"]["authorization"] == "Bearer external-token"
    assert session.calls[0]["headers"]["x-client-header"] == "client"
    assert session.calls[0]["headers"]["x-request-header"] == "request"
    assert session.calls[0]["headers"]["x-hook-header"] == "hooked"


def test_sasapay_requires_explicit_production_base_url() -> None:
    with pytest.raises(ConfigurationError):
        SasaPayClient(
            client_id="client-id",
            client_secret="client-secret",
            environment="production",
        )


def test_sasapay_client_requests_token_and_c2b_payment() -> None:
    session = FakeSession(
        responses=[
            FakeResponse(
                200,
                {
                    "status": True,
                    "detail": "SUCCESS",
                    "access_token": "sasapay-token",
                    "expires_in": 3600,
                },
            ),
            FakeResponse(
                200, {"status": True, "ResponseCode": "0", "CheckoutRequestID": "checkout-123"}
            ),
        ]
    )

    client = SasaPayClient(
        client_id="client-id",
        client_secret="client-secret",
        environment="sandbox",
        session=session,
    )

    response = client.request_payment(
        {
            "MerchantCode": "600980",
            "NetworkCode": "63902",
            "Currency": "KES",
            "Amount": 1,
            "PhoneNumber": "254700000080",
            "AccountReference": "12345678",
            "TransactionDesc": "Request Payment",
            "CallBackURL": "https://example.com/callback",
        }
    )

    assert response["ResponseCode"] == "0"
    assert len(session.calls) == 2
    assert session.calls[0]["params"] == {"grant_type": "client_credentials"}
    assert session.calls[1]["headers"]["authorization"] == "Bearer sasapay-token"
    assert session.calls[1]["json"]["Amount"] == "1"


def test_sasapay_supports_post_retry_when_explicitly_enabled() -> None:
    session = FakeSession(
        responses=[
            FakeResponse(200, {"access_token": "sasapay-token", "expires_in": 3600}),
            FakeResponse(500, {"detail": "temporary failure"}),
            FakeResponse(200, {"status": True, "ResponseCode": "0"}),
        ]
    )

    client = SasaPayClient(
        client_id="client-id",
        client_secret="client-secret",
        environment="sandbox",
        session=session,
    )

    response = client.request_payment(
        {
            "MerchantCode": "600980",
            "NetworkCode": "63902",
            "Currency": "KES",
            "Amount": "1.00",
            "PhoneNumber": "254700000080",
            "AccountReference": "12345678",
            "TransactionDesc": "Request Payment",
            "CallBackURL": "https://example.com/callback",
        },
        options=RequestOptions(
            retry=RetryPolicy(
                max_attempts=2,
                retry_methods=("POST",),
                retry_on_statuses=(500,),
                base_delay_seconds=0.0,
            )
        ),
    )

    assert response["ResponseCode"] == "0"
    assert len(session.calls) == 3


def test_sasapay_per_request_access_token_override_skips_auth() -> None:
    session = FakeSession(
        responses=[FakeResponse(200, {"status": True, "detail": "Transaction is being processed"})]
    )

    class BadTokenProvider:
        def get_access_token(self, force_refresh: bool = False) -> str:
            raise AssertionError("token provider should not be called")

    client = SasaPayClient(token_provider=BadTokenProvider(), session=session)

    client.process_payment(
        {
            "MerchantCode": "600980",
            "CheckoutRequestID": "checkout-123",
            "VerificationCode": "123456",
        },
        options=RequestOptions(
            access_token="manual-token",
            headers={"x-request-id": "abc-123"},
        ),
    )

    assert len(session.calls) == 1
    assert session.calls[0]["headers"]["authorization"] == "Bearer manual-token"
    assert session.calls[0]["headers"]["x-request-id"] == "abc-123"
