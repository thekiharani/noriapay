from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from noriapay import ConfigurationError, Hooks, PaystackClient, RequestOptions


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


def test_paystack_client_requires_secret_key() -> None:
    with pytest.raises(ConfigurationError):
        PaystackClient()


def test_paystack_client_supports_payment_and_transfer_flows() -> None:
    seen_headers: list[str] = []

    def before_request(context: Any) -> None:
        context.headers["x-hooked"] = "yes"
        seen_headers.append(context.headers["authorization"])

    session = FakeSession(
        responses=[
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Authorization URL created",
                    "data": {
                        "authorization_url": "https://checkout.paystack.com/test",
                        "access_code": "ACCESS_test",
                        "reference": "ref-init",
                    },
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Verification successful",
                    "data": {
                        "id": 123,
                        "status": "success",
                        "reference": "ref-init",
                        "amount": 5000,
                        "currency": "KES",
                    },
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Banks retrieved",
                    "data": [
                        {
                            "name": "Safaricom",
                            "code": "MPESA",
                            "country": "Kenya",
                            "currency": "KES",
                            "type": "mobile_money",
                        }
                    ],
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Account number resolved",
                    "data": {
                        "account_number": "247247",
                        "account_name": "Till Transfer Example",
                    },
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Transfer recipient created successfully",
                    "data": {
                        "recipient_code": "RCP_paystack",
                        "type": "mobile_money_business",
                        "currency": "KES",
                        "details": {
                            "account_number": "247247",
                            "bank_code": "MPTILL",
                        },
                    },
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Transfer has been queued",
                    "data": {
                        "transfer_code": "TRF_queued",
                        "status": "otp",
                        "reference": "ref-transfer",
                        "amount": 5000,
                        "currency": "KES",
                    },
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Transfer has been queued",
                    "data": {
                        "transfer_code": "TRF_queued",
                        "status": "success",
                        "reference": "ref-transfer",
                    },
                },
            ),
            FakeResponse(
                200,
                {
                    "status": True,
                    "message": "Transfer retrieved",
                    "data": {
                        "transfer_code": "TRF_queued",
                        "status": "success",
                        "reference": "ref-transfer",
                    },
                },
            ),
        ]
    )

    client = PaystackClient(
        secret_key="sk_test_123",
        session=session,
        default_headers={"x-client-header": "client"},
        hooks=Hooks(before_request=before_request),
    )

    initialize = client.initialize_transaction(
        {
            "amount": 5000,
            "email": "customer@example.com",
            "currency": "KES",
            "reference": "ref-init",
        }
    )
    verify = client.verify_transaction("ref-init")
    banks = client.list_banks({"currency": "KES", "type": "mobile_money"})
    account = client.resolve_account(account_number="247247", bank_code="MPTILL")
    recipient = client.create_transfer_recipient(
        {
            "type": "mobile_money_business",
            "name": "Till Transfer Example",
            "account_number": "247247",
            "bank_code": "MPTILL",
            "currency": "KES",
        }
    )
    transfer = client.initiate_transfer(
        {
            "source": "balance",
            "amount": 5000,
            "recipient": "RCP_paystack",
            "reference": "ref-transfer",
            "currency": "KES",
            "account_reference": "ACC-123",
        }
    )
    finalized = client.finalize_transfer(
        {
            "transfer_code": "TRF_queued",
            "otp": "123456",
        },
        options=RequestOptions(
            access_token="sk_test_override",
            headers={"x-request-id": "req-123"},
        ),
    )
    verified_transfer = client.verify_transfer("ref-transfer")

    assert initialize["data"]["reference"] == "ref-init"
    assert verify["data"]["status"] == "success"
    assert banks["data"][0]["code"] == "MPESA"
    assert account["data"]["account_name"] == "Till Transfer Example"
    assert recipient["data"]["recipient_code"] == "RCP_paystack"
    assert transfer["data"]["status"] == "otp"
    assert finalized["data"]["status"] == "success"
    assert verified_transfer["data"]["reference"] == "ref-transfer"

    assert session.calls[0]["headers"]["authorization"] == "Bearer sk_test_123"
    assert session.calls[0]["headers"]["x-client-header"] == "client"
    assert session.calls[0]["headers"]["x-hooked"] == "yes"
    assert session.calls[0]["json"]["email"] == "customer@example.com"
    assert session.calls[1]["method"] == "GET"
    assert session.calls[2]["params"] == {"currency": "KES", "type": "mobile_money"}
    assert session.calls[3]["params"] == {
        "account_number": "247247",
        "bank_code": "MPTILL",
    }
    assert session.calls[6]["headers"]["authorization"] == "Bearer sk_test_override"
    assert session.calls[6]["headers"]["x-request-id"] == "req-123"
    assert seen_headers[0] == "Bearer sk_test_123"
