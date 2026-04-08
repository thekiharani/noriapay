from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from noriapay import (
    PAYSTACK_WEBHOOK_IPS,
    ConfigurationError,
    MpesaClient,
    PaystackClient,
    SasaPayClient,
    WebhookVerificationError,
    compute_paystack_signature,
    require_paystack_signature,
    require_source_ip,
    verify_paystack_signature,
    verify_source_ip,
)
from noriapay.config import (
    get_env_environment,
    get_env_float,
    get_optional_env,
    get_required_env,
    resolve_environ,
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


def test_config_helpers_handle_optional_required_and_typed_env_values() -> None:
    environ = {
        "PRESENT": " value ",
        "FLOAT_VALUE": "15.5",
        "ENVIRONMENT": "production",
    }

    assert resolve_environ(environ) is environ
    assert get_optional_env("PRESENT", environ=environ) == "value"
    assert get_optional_env("MISSING", environ=environ) is None
    assert get_required_env("PRESENT", environ=environ) == "value"
    assert get_env_float("FLOAT_VALUE", environ=environ) == 15.5
    assert get_env_float("MISSING_FLOAT", environ=environ) is None
    assert get_env_environment("ENVIRONMENT", environ=environ, default="sandbox") == "production"
    assert get_env_environment("MISSING_ENV", environ=environ) == "sandbox"

    with pytest.raises(ConfigurationError):
        get_required_env("MISSING", environ=environ)

    with pytest.raises(ConfigurationError):
        get_env_float("BAD_FLOAT", environ={"BAD_FLOAT": "abc"})

    with pytest.raises(ConfigurationError):
        get_env_environment("BAD_ENV", environ={"BAD_ENV": "staging"})


def test_mpesa_client_from_env_reads_credentials_and_common_options() -> None:
    session = FakeSession(
        responses=[FakeResponse(200, {"access_token": "mpesa-token", "expires_in": 3600})]
    )
    client = MpesaClient.from_env(
        environ={
            "NORIAPAY_MPESA_CONSUMER_KEY": "consumer-key",
            "NORIAPAY_MPESA_CONSUMER_SECRET": "consumer-secret",
            "NORIAPAY_MPESA_ENVIRONMENT": "production",
            "NORIAPAY_MPESA_TIMEOUT_SECONDS": "12.5",
            "NORIAPAY_MPESA_TOKEN_CACHE_SKEW_SECONDS": "30",
        },
        session=session,
    )

    assert client.get_access_token() == "mpesa-token"
    assert session.calls[0]["url"] == "https://api.safaricom.co.ke/oauth/v1/generate"
    assert session.calls[0]["timeout"] == 12.5


def test_sasapay_client_from_env_supports_production_base_url() -> None:
    session = FakeSession(
        responses=[FakeResponse(200, {"access_token": "sasapay-token", "expires_in": 3600})]
    )
    client = SasaPayClient.from_env(
        environ={
            "NORIAPAY_SASAPAY_CLIENT_ID": "client-id",
            "NORIAPAY_SASAPAY_CLIENT_SECRET": "client-secret",
            "NORIAPAY_SASAPAY_ENVIRONMENT": "production",
            "NORIAPAY_SASAPAY_BASE_URL": "https://api.example.com/sasapay",
            "NORIAPAY_SASAPAY_TIMEOUT_SECONDS": "20",
        },
        session=session,
    )

    assert client.get_access_token() == "sasapay-token"
    assert session.calls[0]["url"] == "https://api.example.com/sasapay/auth/token/"
    assert session.calls[0]["timeout"] == 20.0


def test_paystack_client_from_env_reads_secret_key() -> None:
    session = FakeSession(
        responses=[FakeResponse(200, {"status": True, "message": "Banks", "data": []})]
    )
    client = PaystackClient.from_env(
        environ={
            "NORIAPAY_PAYSTACK_SECRET_KEY": "sk_test_123",
            "NORIAPAY_PAYSTACK_TIMEOUT_SECONDS": "9",
        },
        session=session,
    )

    assert client.list_banks()["status"] is True
    assert session.calls[0]["headers"]["authorization"] == "Bearer sk_test_123"
    assert session.calls[0]["timeout"] == 9.0


def test_webhook_helpers_verify_signatures_and_source_ips() -> None:
    raw_body = '{"event":"charge.success"}'
    secret_key = "sk_test_123"
    signature = compute_paystack_signature(raw_body, secret_key)
    bytes_signature = compute_paystack_signature(raw_body.encode("utf-8"), secret_key)

    assert verify_paystack_signature(raw_body, signature, secret_key)
    assert verify_paystack_signature(raw_body.encode("utf-8"), bytes_signature, secret_key)
    assert not verify_paystack_signature(raw_body, "bad-signature", secret_key)
    assert not verify_paystack_signature(raw_body, None, secret_key)

    require_paystack_signature(raw_body, signature, secret_key)
    with pytest.raises(WebhookVerificationError):
        require_paystack_signature(raw_body, "bad-signature", secret_key)

    assert verify_source_ip(PAYSTACK_WEBHOOK_IPS[0], PAYSTACK_WEBHOOK_IPS)
    assert verify_source_ip(" 52.31.139.75 ", PAYSTACK_WEBHOOK_IPS)
    assert not verify_source_ip(None, PAYSTACK_WEBHOOK_IPS)
    assert not verify_source_ip("   ", PAYSTACK_WEBHOOK_IPS)
    assert not verify_source_ip("127.0.0.1", PAYSTACK_WEBHOOK_IPS)
    assert verify_source_ip(PAYSTACK_WEBHOOK_IPS[2], ["", *PAYSTACK_WEBHOOK_IPS])

    require_source_ip(PAYSTACK_WEBHOOK_IPS[1], PAYSTACK_WEBHOOK_IPS)
    with pytest.raises(WebhookVerificationError):
        require_source_ip("127.0.0.1", PAYSTACK_WEBHOOK_IPS)
