# `noriapay`

Reference-first Python SDK for African payment providers.

Current provider support:

- M-PESA Daraja
- SasaPay
- Paystack

This README is intended to be the public API reference for the package exported from `noriapay`.

## Install

```bash
pip install noriapay
```

Python requirement: `>=3.11`

## Scope

Implemented now:

- M-PESA OAuth client credentials
- M-PESA STK push
- M-PESA STK push query
- M-PESA C2B URL registration (`v1` and `v2`)
- M-PESA B2C
- M-PESA B2B
- M-PESA reversal
- M-PESA transaction status query
- M-PESA account balance query
- M-PESA QR generation
- SasaPay OAuth client credentials
- SasaPay C2B request payment
- SasaPay C2B OTP completion
- SasaPay B2C
- SasaPay B2B
- SasaPay callback and IPN payload type definitions
- Paystack transaction initialize
- Paystack transaction verify
- Paystack bank listing
- Paystack account resolution
- Paystack transfer recipient creation
- Paystack transfer initiation
- Paystack transfer finalization
- Paystack transfer verification
- Paystack webhook signature verification helpers

Not implemented yet:

- SasaPay checkout payments
- SasaPay remittance
- SasaPay utilities
- SasaPay WaaS
- Daraja Bill Manager and portal-only APIs with undocumented request bodies
- Most other Paystack APIs outside the initial payment and transfer flows above

## Public Export Index

Everything in this section is exported by `from noriapay import ...`.

### Shared Exports

- `AccessToken`
- `AccessTokenProvider`
- `AfterResponseContext`
- `ApiError`
- `AuthenticationError`
- `BeforeRequestContext`
- `ClientCredentialsTokenProvider`
- `ConfigurationError`
- `Environment`
- `ErrorContext`
- `Hooks`
- `NetworkError`
- `NoriapayError`
- `RequestOptions`
- `RetryDecisionContext`
- `RetryPolicy`
- `TimeoutError`
- `WebhookVerificationError`

### M-PESA Exports

- `MPESA_BASE_URLS`
- `MpesaAccountBalanceRequest`
- `MpesaApiResponse`
- `MpesaB2BRequest`
- `MpesaB2CRequest`
- `MpesaClient`
- `MpesaQrCodeRequest`
- `MpesaRegisterC2BUrlsRequest`
- `MpesaReversalRequest`
- `MpesaStkPushRequest`
- `MpesaStkPushResponse`
- `MpesaStkQueryRequest`
- `MpesaTransactionStatusRequest`
- `build_mpesa_stk_password`
- `build_mpesa_timestamp`

### SasaPay Exports

- `SASAPAY_SANDBOX_BASE_URL`
- `SasaPayAuthResponse`
- `SasaPayB2BRequest`
- `SasaPayB2BResponse`
- `SasaPayB2CRequest`
- `SasaPayB2CResponse`
- `SasaPayC2BCallback`
- `SasaPayC2BIpn`
- `SasaPayClient`
- `SasaPayProcessPaymentRequest`
- `SasaPayProcessPaymentResponse`
- `SasaPayRequestPaymentRequest`
- `SasaPayRequestPaymentResponse`
- `SasaPayTransferCallback`

### Paystack Exports

- `PAYSTACK_BASE_URL`
- `PaystackApiResponse`
- `PaystackBank`
- `PaystackClient`
- `PaystackCreateTransferRecipientRequest`
- `PaystackCreateTransferRecipientResponse`
- `PaystackFinalizeTransferRequest`
- `PaystackFinalizeTransferResponse`
- `PaystackInitializeTransactionData`
- `PaystackInitializeTransactionRequest`
- `PaystackInitializeTransactionResponse`
- `PaystackInitiateTransferRequest`
- `PaystackInitiateTransferResponse`
- `PaystackListBanksQuery`
- `PaystackListBanksResponse`
- `PaystackResolveAccountData`
- `PaystackResolveAccountResponse`
- `PaystackTransaction`
- `PaystackTransfer`
- `PaystackTransferRecipient`
- `PaystackTransferRecipientDetails`
- `PaystackVerifyTransactionResponse`
- `PaystackVerifyTransferResponse`

### Webhook Helper Exports

- `PAYSTACK_WEBHOOK_IPS`
- `compute_paystack_signature`
- `require_paystack_signature`
- `require_source_ip`
- `verify_paystack_signature`
- `verify_source_ip`

## Quick Start

### M-PESA

```python
from noriapay import MpesaClient, build_mpesa_stk_password, build_mpesa_timestamp

mpesa = MpesaClient(
    consumer_key="consumer-key",
    consumer_secret="consumer-secret",
    environment="sandbox",
)

timestamp = build_mpesa_timestamp()

response = mpesa.stk_push(
    {
        "BusinessShortCode": "174379",
        "Password": build_mpesa_stk_password(
            business_short_code="174379",
            passkey="passkey",
            timestamp=timestamp,
        ),
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": 1,
        "PartyA": "254700000000",
        "PartyB": "174379",
        "PhoneNumber": "254700000000",
        "CallBackURL": "https://example.com/mpesa/callback",
        "AccountReference": "INV-001",
        "TransactionDesc": "Payment",
    }
)
```

### SasaPay

```python
from noriapay import SasaPayClient

sasapay = SasaPayClient(
    client_id="client-id",
    client_secret="client-secret",
    environment="sandbox",
)

response = sasapay.request_payment(
    {
        "MerchantCode": "600980",
        "NetworkCode": "63902",
        "Currency": "KES",
        "Amount": "1.00",
        "PhoneNumber": "254700000080",
        "AccountReference": "12345678",
        "TransactionDesc": "Request Payment",
        "CallBackURL": "https://example.com/sasapay/callback",
    }
)
```

### Paystack

```python
from noriapay import PaystackClient

paystack = PaystackClient(secret_key="sk_test_xxx")

response = paystack.initialize_transaction(
    {
        "email": "customer@example.com",
        "amount": 5000,
        "reference": "order-123",
        "callback_url": "https://example.com/paystack/callback",
    }
)
```

### Environment-Based Setup

```python
from noriapay import MpesaClient, PaystackClient, SasaPayClient

mpesa = MpesaClient.from_env()
sasapay = SasaPayClient.from_env()
paystack = PaystackClient.from_env()
```

## Source Docs

This package was implemented against:

- local Daraja reference: `../daraja.md`
- SasaPay getting started: <https://developer.sasapay.app/docs/getting-started>
- SasaPay authentication: <https://developer.sasapay.app/docs/apis/authentication>
- SasaPay C2B: <https://developer.sasapay.app/docs/apis/c2b>
- SasaPay B2C: <https://developer.sasapay.app/docs/apis/b2c>
- SasaPay B2B: <https://developer.sasapay.app/docs/apis/b2b>
- Paystack API reference: <https://paystack.com/docs/api/>
- Paystack transfer recipient guide: <https://paystack.com/docs/transfers/creating-transfer-recipients/>
- Paystack webhooks: <https://paystack.com/docs/payments/webhooks/>

Important SasaPay note:

- the sandbox host is explicitly documented and is the default
- the reviewed docs did not clearly state the production API host, so this package requires an explicit `base_url` for SasaPay production

## Shared Reference

### `Environment`

`Environment = Literal["sandbox", "production"]`

Used by `MpesaClient` and `SasaPayClient`.

### `AccessTokenProvider`

Protocol:

```python
class AccessTokenProvider(Protocol):
    def get_access_token(self, force_refresh: bool = False) -> str: ...
```

You can pass a custom implementation as `token_provider=` to `MpesaClient` or `SasaPayClient`.

### `AccessToken`

Dataclass fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `access_token` | `str` | OAuth access token. |
| `expires_in` | `int` | Token lifetime in seconds. |
| `token_type` | `str \| None` | Optional provider token type. |
| `scope` | `str \| None` | Optional provider scope string. |
| `raw` | `dict[str, Any]` | Original parsed provider payload. |

### `ClientCredentialsTokenProvider`

Reusable OAuth client-credentials token provider.

Constructor fields:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `token_url` | `str` | required | Token endpoint URL. |
| `client_id` | `str` | required | OAuth client id. |
| `client_secret` | `str` | required | OAuth client secret. |
| `session` | `requests.Session \| compatible object \| None` | `None` | Custom HTTP session. |
| `timeout_seconds` | `float \| None` | `None` | Token request timeout. |
| `query` | `dict[str, str \| int \| float \| bool \| None] \| None` | `None` | Optional query params. |
| `cache_skew_seconds` | `float` | `60.0` | Refresh early before expiry. |
| `map_response` | `Callable[[dict[str, Any]], AccessToken] \| None` | `None` | Custom token mapper. |

Methods:

| Method | Returns | Meaning |
| --- | --- | --- |
| `get_access_token(force_refresh=False)` | `str` | Returns a token string. |
| `get_token(force_refresh=False)` | `AccessToken` | Returns the structured token object. |
| `clear_cache()` | `None` | Clears the cached token. |

Behavior:

- creates its own `requests.Session()` if `session` is not supplied
- caches tokens in memory
- wraps timeout and request failures as `AuthenticationError`

### `RequestOptions`

Per-request overrides supported by client methods.

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `headers` | `Mapping[str, str] \| None` | `None` | Extra headers for the request. |
| `timeout_seconds` | `float \| None` | `None` | Request-specific timeout. |
| `retry` | `RetryPolicy \| bool \| None` | `None` | Override retry behavior. Use `False` to disable inherited retry. |
| `access_token` | `str \| None` | `None` | Override the bearer token for M-PESA and SasaPay, or the secret key for Paystack. |
| `force_token_refresh` | `bool` | `False` | Forces the next OAuth token lookup to refresh for M-PESA and SasaPay. |

Paystack note:

- `force_token_refresh` has no practical effect because `PaystackClient` does not use OAuth token lookup

### `RetryDecisionContext`

Dataclass fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `attempt` | `int` | Current attempt number, starting at `1`. |
| `max_attempts` | `int` | Total configured attempts. |
| `method` | `HttpMethod` | HTTP method. |
| `url` | `str` | Absolute request URL. |
| `status` | `int \| None` | HTTP status code for failed responses. |
| `error` | `object` | Wrapped exception object when the failure is not an HTTP status failure. |

### `RetryPolicy`

Dataclass fields:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `max_attempts` | `int` | `1` | Total attempts including the first request. |
| `retry_methods` | `tuple[HttpMethod, ...]` | `()` | Restrict retries to specific methods. |
| `retry_on_statuses` | `tuple[int, ...]` | `()` | Retry these HTTP status codes. |
| `retry_on_network_error` | `bool` | `False` | Retry timeouts and request exceptions. |
| `base_delay_seconds` | `float` | `0.0` | Base retry delay. |
| `max_delay_seconds` | `float` | `60.0` | Maximum retry delay. |
| `backoff_multiplier` | `float` | `2.0` | Exponential backoff multiplier. |
| `should_retry` | `Callable[[RetryDecisionContext], bool] \| None` | `None` | Final custom retry decision hook. |

Retries are opt-in by default. That is deliberate for payments.

### Hook Context Types

#### `BeforeRequestContext`

| Field | Type |
| --- | --- |
| `url` | `str` |
| `path` | `str` |
| `method` | `HttpMethod` |
| `headers` | `MutableMapping[str, str]` |
| `body` | `object` |
| `attempt` | `int` |

#### `AfterResponseContext`

`AfterResponseContext` includes all `BeforeRequestContext` fields plus:

| Field | Type |
| --- | --- |
| `response` | `object` |
| `response_body` | `object` |

#### `ErrorContext`

`ErrorContext` includes all `BeforeRequestContext` fields plus:

| Field | Type |
| --- | --- |
| `error` | `object` |
| `response` | `object \| None` |
| `response_body` | `object \| None` |

### `Hooks`

Dataclass fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `before_request` | `Callable[[BeforeRequestContext], None] \| Sequence[Callable[[BeforeRequestContext], None]] \| None` | Observe or mutate outgoing headers/body before dispatch. |
| `after_response` | `Callable[[AfterResponseContext], None] \| Sequence[Callable[[AfterResponseContext], None]] \| None` | Observe parsed responses. |
| `on_error` | `Callable[[ErrorContext], None] \| Sequence[Callable[[ErrorContext], None]] \| None` | Observe wrapped failures and unsuccessful responses. |

Header merge order:

1. client `default_headers`
2. per-request `RequestOptions.headers`
3. SDK auth headers
4. `before_request` hook mutations

Example:

```python
from noriapay import Hooks, MpesaClient

def before_request(context):
    context.headers["x-correlation-id"] = "corr-123"

client = MpesaClient(
    consumer_key="consumer-key",
    consumer_secret="consumer-secret",
    hooks=Hooks(before_request=before_request),
)
```

### Exception Classes

All package exceptions inherit from `NoriapayError`.

#### `NoriapayError`

Base exception attributes:

| Attribute | Type |
| --- | --- |
| `code` | `str` |
| `details` | `object` |

#### `ConfigurationError`

Raised for invalid package or provider configuration.

#### `AuthenticationError`

Raised for OAuth token acquisition failures.

#### `TimeoutError`

Raised when the underlying HTTP request times out.

#### `NetworkError`

Raised for non-timeout request exceptions.

#### `ApiError`

Raised for non-2xx provider responses.

Additional attributes:

| Attribute | Type |
| --- | --- |
| `status_code` | `int` |
| `response_body` | `object` |

#### `WebhookVerificationError`

Raised by webhook verification helpers when signature or source validation fails.

## Environment Configuration

Every client exposes a `from_env()` constructor.

Shared `from_env()` behavior:

- `environ` defaults to `os.environ`
- blank env values are treated as missing
- `*_TIMEOUT_SECONDS` and `*_TOKEN_CACHE_SKEW_SECONDS` are parsed as floats
- `*_ENVIRONMENT` must be `sandbox` or `production`

### `MpesaClient.from_env()`

Signature:

```python
MpesaClient.from_env(
    *,
    prefix: str = "NORIAPAY_MPESA_",
    environ: Mapping[str, str] | None = None,
    token_provider: AccessTokenProvider | None = None,
    session: requests.Session | compatible object | None = None,
    default_headers: dict[str, str] | None = None,
    retry: RetryPolicy | None = None,
    hooks: Hooks | None = None,
)
```

Environment variables:

- `NORIAPAY_MPESA_CONSUMER_KEY`
- `NORIAPAY_MPESA_CONSUMER_SECRET`
- `NORIAPAY_MPESA_ENVIRONMENT`
- `NORIAPAY_MPESA_BASE_URL`
- `NORIAPAY_MPESA_TIMEOUT_SECONDS`
- `NORIAPAY_MPESA_TOKEN_CACHE_SKEW_SECONDS`

If `token_provider` is supplied, `CONSUMER_KEY` and `CONSUMER_SECRET` are not required.

### `SasaPayClient.from_env()`

Signature:

```python
SasaPayClient.from_env(
    *,
    prefix: str = "NORIAPAY_SASAPAY_",
    environ: Mapping[str, str] | None = None,
    token_provider: AccessTokenProvider | None = None,
    session: requests.Session | compatible object | None = None,
    default_headers: dict[str, str] | None = None,
    retry: RetryPolicy | None = None,
    hooks: Hooks | None = None,
)
```

Environment variables:

- `NORIAPAY_SASAPAY_CLIENT_ID`
- `NORIAPAY_SASAPAY_CLIENT_SECRET`
- `NORIAPAY_SASAPAY_ENVIRONMENT`
- `NORIAPAY_SASAPAY_BASE_URL`
- `NORIAPAY_SASAPAY_TIMEOUT_SECONDS`
- `NORIAPAY_SASAPAY_TOKEN_CACHE_SKEW_SECONDS`

If `token_provider` is supplied, `CLIENT_ID` and `CLIENT_SECRET` are not required.

### `PaystackClient.from_env()`

Signature:

```python
PaystackClient.from_env(
    *,
    prefix: str = "NORIAPAY_PAYSTACK_",
    environ: Mapping[str, str] | None = None,
    session: requests.Session | compatible object | None = None,
    default_headers: Mapping[str, str] | None = None,
    retry: RetryPolicy | None = None,
    hooks: Hooks | None = None,
)
```

Environment variables:

- `NORIAPAY_PAYSTACK_SECRET_KEY`
- `NORIAPAY_PAYSTACK_BASE_URL`
- `NORIAPAY_PAYSTACK_TIMEOUT_SECONDS`

For all three clients, you can change the env var prefix by passing `prefix="MYAPP_PAYMENTS_"`.

## Webhook Verification Helpers

### `PAYSTACK_WEBHOOK_IPS`

Tuple of Paystack webhook source IPs currently hardcoded by the package:

- `52.31.139.75`
- `52.49.173.169`
- `52.214.14.220`

### `compute_paystack_signature(raw_body, secret_key)`

Computes the lowercase hex SHA-512 HMAC digest used for Paystack webhook verification.

Arguments:

| Argument | Type |
| --- | --- |
| `raw_body` | `bytes \| str` |
| `secret_key` | `str` |

Returns: `str`

### `verify_paystack_signature(raw_body, signature, secret_key)`

Validates a supplied Paystack signature.

Arguments:

| Argument | Type |
| --- | --- |
| `raw_body` | `bytes \| str` |
| `signature` | `str \| None` |
| `secret_key` | `str` |

Returns: `bool`

### `require_paystack_signature(raw_body, signature, secret_key)`

Same inputs as `verify_paystack_signature`, but raises `WebhookVerificationError` on failure.

### `verify_source_ip(source_ip, allowed_ips)`

Generic helper for source-IP allowlisting.

Arguments:

| Argument | Type |
| --- | --- |
| `source_ip` | `str \| None` |
| `allowed_ips` | `Collection[str]` |

Returns: `bool`

Behavior:

- strips whitespace from the incoming IP
- strips blank values from the allowlist

### `require_source_ip(source_ip, allowed_ips)`

Same inputs as `verify_source_ip`, but raises `WebhookVerificationError` on failure.

Example:

```python
from noriapay import PAYSTACK_WEBHOOK_IPS, require_paystack_signature, require_source_ip

raw_body = request.get_data()
signature = request.headers.get("x-paystack-signature")
source_ip = request.headers.get("x-forwarded-for", request.remote_addr)

require_paystack_signature(raw_body, signature, secret_key="sk_live_xxx")
require_source_ip(source_ip, PAYSTACK_WEBHOOK_IPS)
```

M-PESA and SasaPay note:

- the reviewed Daraja and SasaPay sources used for this package did not clearly document a signed webhook header scheme
- for those providers, use HTTPS, correlate callbacks with your own identifiers, and verify final state with follow-up API queries where appropriate

## M-PESA Reference

### Constants and Helpers

#### `MPESA_BASE_URLS`

```python
{
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}
```

#### `build_mpesa_timestamp(dt=None)`

Formats a `datetime` as `YYYYMMDDHHMMSS`.

Arguments:

| Argument | Type | Default |
| --- | --- | --- |
| `dt` | `datetime \| None` | `None` |

Returns: `str`

#### `build_mpesa_stk_password(business_short_code, passkey, timestamp)`

Returns `base64(shortCode + passkey + timestamp)`.

Arguments:

| Argument | Type |
| --- | --- |
| `business_short_code` | `str` |
| `passkey` | `str` |
| `timestamp` | `str` |

Returns: `str`

### `MpesaClient`

Constructor:

```python
MpesaClient(
    *,
    consumer_key: str | None = None,
    consumer_secret: str | None = None,
    token_provider: AccessTokenProvider | None = None,
    environment: Environment = "sandbox",
    base_url: str | None = None,
    session: requests.Session | compatible object | None = None,
    timeout_seconds: float | None = None,
    token_cache_skew_seconds: float = 60.0,
    default_headers: dict[str, str] | None = None,
    retry: RetryPolicy | None = None,
    hooks: Hooks | None = None,
)
```

Auth modes:

| Mode | Required |
| --- | --- |
| Built-in OAuth | `consumer_key`, `consumer_secret` |
| External token provider | `token_provider` |

Notes:

- `environment="production"` uses `https://api.safaricom.co.ke`
- `base_url` overrides the environment-derived base URL
- `Amount` fields are serialized to strings before dispatch

Methods:

| Method | Returns | Endpoint |
| --- | --- | --- |
| `from_env(...)` | `MpesaClient` | env-based constructor |
| `get_access_token(force_refresh=False)` | `str` | `GET /oauth/v1/generate?grant_type=client_credentials` |
| `stk_push(payload, options=None)` | `MpesaStkPushResponse` | `POST /mpesa/stkpush/v1/processrequest` |
| `stk_push_query(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/stkpushquery/v1/query` |
| `register_c2b_urls(payload, version="v2", options=None)` | `MpesaApiResponse` | `POST /mpesa/c2b/v1/registerurl` or `v2` |
| `b2c_payment(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/b2c/v1/paymentrequest` |
| `b2b_payment(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/b2b/v1/paymentrequest` |
| `reversal(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/reversal/v1/request` |
| `transaction_status(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/transactionstatus/v1/query` |
| `account_balance(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/accountbalance/v1/query` |
| `generate_qr_code(payload, options=None)` | `MpesaApiResponse` | `POST /mpesa/qrcode/v1/generate` |

### `MpesaApiResponse`

Common response fields:

| Field | Type |
| --- | --- |
| `ConversationID` | `str` |
| `OriginatorConversationID` | `str` |
| `ResponseCode` | `str` |
| `ResponseDescription` | `str` |
| `CustomerMessage` | `str` |
| `errorCode` | `str` |
| `errorMessage` | `str` |

### `MpesaStkPushRequest`

| Field | Type | Required |
| --- | --- | --- |
| `BusinessShortCode` | `str` | Yes |
| `Password` | `str` | Yes |
| `Timestamp` | `str` | Yes |
| `TransactionType` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `PartyA` | `str` | Yes |
| `PartyB` | `str` | Yes |
| `PhoneNumber` | `str` | Yes |
| `CallBackURL` | `str` | Yes |
| `AccountReference` | `str` | Yes |
| `TransactionDesc` | `str` | Yes |

### `MpesaStkPushResponse`

Includes all `MpesaApiResponse` fields plus:

| Field | Type |
| --- | --- |
| `MerchantRequestID` | `str` |
| `CheckoutRequestID` | `str` |

### `MpesaStkQueryRequest`

| Field | Type | Required |
| --- | --- | --- |
| `BusinessShortCode` | `str` | Yes |
| `Password` | `str` | Yes |
| `Timestamp` | `str` | Yes |
| `CheckoutRequestID` | `str` | Yes |

### `MpesaRegisterC2BUrlsRequest`

| Field | Type | Required |
| --- | --- | --- |
| `ShortCode` | `str` | Yes |
| `ResponseType` | `str` | Yes |
| `ConfirmationURL` | `str` | Yes |
| `ValidationURL` | `str` | Yes |

### `MpesaB2CRequest`

| Field | Type | Required |
| --- | --- | --- |
| `InitiatorName` | `str` | Yes |
| `SecurityCredential` | `str` | Yes |
| `CommandID` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `PartyA` | `str` | Yes |
| `PartyB` | `str` | Yes |
| `Remarks` | `str` | Yes |
| `QueueTimeOutURL` | `str` | Yes |
| `ResultURL` | `str` | Yes |
| `Occasion` | `str` | No |

### `MpesaB2BRequest`

| Field | Type | Required |
| --- | --- | --- |
| `Initiator` | `str` | Yes |
| `SecurityCredential` | `str` | Yes |
| `CommandID` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `PartyA` | `str` | Yes |
| `PartyB` | `str` | Yes |
| `Remarks` | `str` | Yes |
| `AccountReference` | `str` | Yes |
| `QueueTimeOutURL` | `str` | Yes |
| `ResultURL` | `str` | Yes |

### `MpesaReversalRequest`

| Field | Type | Required |
| --- | --- | --- |
| `Initiator` | `str` | Yes |
| `SecurityCredential` | `str` | Yes |
| `CommandID` | `str` | Yes |
| `TransactionID` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `ReceiverParty` | `str` | Yes |
| `RecieverIdentifierType` | `str` | Yes |
| `ResultURL` | `str` | Yes |
| `QueueTimeOutURL` | `str` | Yes |
| `Remarks` | `str` | Yes |
| `Occasion` | `str` | No |

### `MpesaTransactionStatusRequest`

| Field | Type | Required |
| --- | --- | --- |
| `Initiator` | `str` | Yes |
| `SecurityCredential` | `str` | Yes |
| `CommandID` | `str` | Yes |
| `TransactionID` | `str` | Yes |
| `PartyA` | `str` | Yes |
| `IdentifierType` | `str` | Yes |
| `ResultURL` | `str` | Yes |
| `QueueTimeOutURL` | `str` | Yes |
| `Remarks` | `str` | Yes |
| `Occasion` | `str` | No |

### `MpesaAccountBalanceRequest`

| Field | Type | Required |
| --- | --- | --- |
| `Initiator` | `str` | Yes |
| `SecurityCredential` | `str` | Yes |
| `CommandID` | `str` | Yes |
| `PartyA` | `str` | Yes |
| `IdentifierType` | `str` | Yes |
| `ResultURL` | `str` | Yes |
| `QueueTimeOutURL` | `str` | Yes |
| `Remarks` | `str` | Yes |

### `MpesaQrCodeRequest`

| Field | Type | Required |
| --- | --- | --- |
| `MerchantName` | `str` | Yes |
| `MerchantShortCode` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `QRType` | `str` | Yes |

## SasaPay Reference

### Constants

#### `SASAPAY_SANDBOX_BASE_URL`

`https://sandbox.sasapay.app/api/v1`

### `SasaPayClient`

Constructor:

```python
SasaPayClient(
    *,
    client_id: str | None = None,
    client_secret: str | None = None,
    token_provider: AccessTokenProvider | None = None,
    environment: Environment = "sandbox",
    base_url: str | None = None,
    session: requests.Session | compatible object | None = None,
    timeout_seconds: float | None = None,
    token_cache_skew_seconds: float = 60.0,
    default_headers: dict[str, str] | None = None,
    retry: RetryPolicy | None = None,
    hooks: Hooks | None = None,
)
```

Auth modes:

| Mode | Required |
| --- | --- |
| Built-in OAuth | `client_id`, `client_secret` |
| External token provider | `token_provider` |

Notes:

- `environment="sandbox"` defaults to `SASAPAY_SANDBOX_BASE_URL`
- `environment="production"` requires explicit `base_url` unless you override it yourself
- `Amount` fields are serialized to strings before dispatch

Methods:

| Method | Returns | Endpoint |
| --- | --- | --- |
| `from_env(...)` | `SasaPayClient` | env-based constructor |
| `get_access_token(force_refresh=False)` | `str` | `GET /auth/token/?grant_type=client_credentials` |
| `request_payment(payload, options=None)` | `SasaPayRequestPaymentResponse` | `POST /payments/request-payment/` |
| `process_payment(payload, options=None)` | `SasaPayProcessPaymentResponse` | `POST /payments/process-payment/` |
| `b2c_payment(payload, options=None)` | `SasaPayB2CResponse` | `POST /payments/b2c/` |
| `b2b_payment(payload, options=None)` | `SasaPayB2BResponse` | `POST /payments/b2b/` |

### `SasaPayAuthResponse`

| Field | Type |
| --- | --- |
| `status` | `bool` |
| `detail` | `str` |
| `access_token` | `str` |
| `expires_in` | `int` |
| `token_type` | `str` |
| `scope` | `str` |

### `SasaPayRequestPaymentRequest`

| Field | Type | Required |
| --- | --- | --- |
| `MerchantCode` | `str` | Yes |
| `NetworkCode` | `str` | Yes |
| `Currency` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `PhoneNumber` | `str` | Yes |
| `AccountReference` | `str` | Yes |
| `TransactionDesc` | `str` | Yes |
| `CallBackURL` | `str` | Yes |

### `SasaPayRequestPaymentResponse`

| Field | Type |
| --- | --- |
| `status` | `bool` |
| `detail` | `str` |
| `PaymentGateway` | `str` |
| `MerchantRequestID` | `str` |
| `CheckoutRequestID` | `str` |
| `TransactionReference` | `str` |
| `ResponseCode` | `str` |
| `ResponseDescription` | `str` |
| `CustomerMessage` | `str` |

Network behavior from the reviewed docs:

- `NetworkCode="0"` is SasaPay wallet and requires OTP completion with `process_payment()`
- values such as `63902` are mobile money channels like M-PESA

### `SasaPayProcessPaymentRequest`

| Field | Type | Required |
| --- | --- | --- |
| `MerchantCode` | `str` | Yes |
| `CheckoutRequestID` | `str` | Yes |
| `VerificationCode` | `str` | Yes |

### `SasaPayProcessPaymentResponse`

| Field | Type |
| --- | --- |
| `status` | `bool` |
| `detail` | `str` |

### `SasaPayB2CRequest`

| Field | Type | Required |
| --- | --- | --- |
| `MerchantCode` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `Currency` | `str` | Yes |
| `MerchantTransactionReference` | `str` | Yes |
| `ReceiverNumber` | `str` | Yes |
| `Channel` | `str` | Yes |
| `Reason` | `str` | Yes |
| `CallBackURL` | `str` | Yes |

### `SasaPayB2CResponse`

| Field | Type |
| --- | --- |
| `status` | `bool` |
| `detail` | `str` |
| `B2CRequestID` | `str` |
| `ConversationID` | `str` |
| `OriginatorConversationID` | `str` |
| `ResponseCode` | `str` |
| `TransactionCharges` | `str` |
| `ResponseDescription` | `str` |

### `SasaPayB2BRequest`

| Field | Type | Required |
| --- | --- | --- |
| `MerchantCode` | `str` | Yes |
| `MerchantTransactionReference` | `str` | Yes |
| `Currency` | `str` | Yes |
| `Amount` | `str \| int \| float` | Yes |
| `ReceiverMerchantCode` | `str` | Yes |
| `AccountReference` | `str` | Yes |
| `ReceiverAccountType` | `str` | Yes |
| `NetworkCode` | `str` | Yes |
| `Reason` | `str` | Yes |
| `CallBackURL` | `str` | Yes |

### `SasaPayB2BResponse`

| Field | Type |
| --- | --- |
| `status` | `bool` |
| `detail` | `str` |
| `B2BRequestID` | `str` |
| `ConversationID` | `str` |
| `OriginatorConversationID` | `str` |
| `TransactionCharges` | `str` |
| `ResponseCode` | `str` |
| `ResponseDescription` | `str` |

### `SasaPayC2BCallback`

| Field | Type |
| --- | --- |
| `MerchantRequestID` | `str` |
| `CheckoutRequestID` | `str` |
| `PaymentRequestID` | `str` |
| `ResultCode` | `str` |
| `ResultDesc` | `str` |
| `SourceChannel` | `str` |
| `TransAmount` | `str` |
| `RequestedAmount` | `str` |
| `Paid` | `bool` |
| `BillRefNumber` | `str` |
| `TransactionDate` | `str` |
| `CustomerMobile` | `str` |
| `TransactionCode` | `str` |
| `ThirdPartyTransID` | `str` |

### `SasaPayC2BIpn`

| Field | Type |
| --- | --- |
| `MerchantCode` | `str` |
| `BusinessShortCode` | `str` |
| `InvoiceNumber` | `str` |
| `PaymentMethod` | `str` |
| `TransID` | `str` |
| `ThirdPartyTransID` | `str` |
| `FullName` | `str` |
| `FirstName` | `str` |
| `MiddleName` | `str` |
| `LastName` | `str` |
| `TransactionType` | `str` |
| `MSISDN` | `str` |
| `OrgAccountBalance` | `str` |
| `TransAmount` | `str` |
| `TransTime` | `str` |
| `BillRefNumber` | `str` |

### `SasaPayTransferCallback`

| Field | Type | Required |
| --- | --- | --- |
| `MerchantCode` | `str` | No |
| `DestinationChannel` | `str` | No |
| `RecipientName` | `str` | No |
| `RecipientAccountNumber` | `str` | No |
| `ResultCode` | `str` | No |
| `ResultDesc` | `str` | No |
| `SourceChannel` | `str` | No |
| `SasaPayTransactionCode` | `str` | No |
| `CheckoutRequestID` | `str` | No |
| `SasaPayTransactionID` | `str` | No |
| `ThirdPartyTransactionCode` | `str` | No |
| `TransactionAmount` | `str` | No |
| `TransactionCharge` | `str` | No |
| `TransactionCharges` | `str` | No |
| `MerchantRequestID` | `str` | No |
| `MerchantTransactionReference` | `str` | No |
| `TransactionDate` | `str` | No |
| `MerchantAccountBalance` | `str` | No |
| `LinkedTransactionCode` | `str` | No |

## Paystack Reference

### Constants

#### `PAYSTACK_BASE_URL`

`https://api.paystack.co`

Environment selection is determined by the secret key you use.

### `PaystackClient`

Constructor:

```python
PaystackClient(
    *,
    secret_key: str | None = None,
    base_url: str | None = None,
    session: requests.Session | compatible object | None = None,
    timeout_seconds: float | None = None,
    default_headers: Mapping[str, str] | None = None,
    retry: RetryPolicy | None = None,
    hooks: Hooks | None = None,
)
```

Required:

| Field | Type |
| --- | --- |
| `secret_key` | `str` |

Notes:

- `secret_key` is sent as `Authorization: Bearer ...`
- `RequestOptions.access_token` overrides the secret key for a single request
- transaction and transfer amounts are provider lowest-unit integers
- the current package only covers the initial payment and transfer subset described here

Methods:

| Method | Returns | Endpoint |
| --- | --- | --- |
| `from_env(...)` | `PaystackClient` | env-based constructor |
| `initialize_transaction(payload, options=None)` | `PaystackInitializeTransactionResponse` | `POST /transaction/initialize` |
| `verify_transaction(reference, options=None)` | `PaystackVerifyTransactionResponse` | `GET /transaction/verify/:reference` |
| `list_banks(query=None, options=None)` | `PaystackListBanksResponse` | `GET /bank` |
| `resolve_account(account_number, bank_code, options=None)` | `PaystackResolveAccountResponse` | `GET /bank/resolve` |
| `create_transfer_recipient(payload, options=None)` | `PaystackCreateTransferRecipientResponse` | `POST /transferrecipient` |
| `initiate_transfer(payload, options=None)` | `PaystackInitiateTransferResponse` | `POST /transfer` |
| `finalize_transfer(payload, options=None)` | `PaystackFinalizeTransferResponse` | `POST /transfer/finalize_transfer` |
| `verify_transfer(reference, options=None)` | `PaystackVerifyTransferResponse` | `GET /transfer/verify/:reference` |

### `PaystackApiResponse`

Common response envelope fields:

| Field | Type |
| --- | --- |
| `status` | `bool` |
| `message` | `str` |

### `PaystackInitializeTransactionRequest`

| Field | Type | Required |
| --- | --- | --- |
| `amount` | `str \| int` | Yes |
| `email` | `str` | Yes |
| `channels` | `Sequence[Literal["card", "bank", "apple_pay", "ussd", "qr", "mobile_money", "bank_transfer", "eft", "capitec_pay", "payattitude"]]` | No |
| `currency` | `str` | No |
| `reference` | `str` | No |
| `callback_url` | `str` | No |
| `plan` | `str` | No |
| `invoice_limit` | `int` | No |
| `metadata` | `object` | No |
| `split_code` | `str` | No |
| `subaccount` | `str` | No |
| `transaction_charge` | `int` | No |
| `bearer` | `Literal["account", "subaccount"]` | No |

### `PaystackInitializeTransactionData`

| Field | Type |
| --- | --- |
| `authorization_url` | `str` |
| `access_code` | `str` |
| `reference` | `str` |

### `PaystackInitializeTransactionResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackInitializeTransactionData` |

### `PaystackTransaction`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `domain` | `str` |
| `status` | `str` |
| `reference` | `str` |
| `receipt_number` | `str \| None` |
| `amount` | `int` |
| `message` | `str \| None` |
| `gateway_response` | `str` |
| `paid_at` | `str` |
| `created_at` | `str` |
| `channel` | `str` |
| `currency` | `str` |
| `ip_address` | `str` |
| `metadata` | `object` |
| `log` | `object` |
| `fees` | `int` |
| `fees_split` | `object` |
| `authorization` | `PaystackTransactionAuthorization` |
| `customer` | `PaystackTransactionCustomer` |
| `plan` | `object` |
| `split` | `object` |
| `order_id` | `object` |
| `paidAt` | `str` |
| `createdAt` | `str` |
| `requested_amount` | `int` |
| `pos_transaction_data` | `object` |
| `source` | `object` |
| `fees_breakdown` | `object` |
| `connect` | `object` |
| `transaction_date` | `str` |
| `plan_object` | `object` |
| `subaccount` | `object` |

### `PaystackVerifyTransactionResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackTransaction` |

### `PaystackTransactionAuthorization`

Nested object inside `PaystackTransaction.authorization`.

This type is part of the response model but is not exported directly.

| Field | Type |
| --- | --- |
| `authorization_code` | `str` |
| `bin` | `str` |
| `last4` | `str` |
| `exp_month` | `str` |
| `exp_year` | `str` |
| `channel` | `str` |
| `card_type` | `str` |
| `bank` | `str` |
| `country_code` | `str` |
| `brand` | `str` |
| `reusable` | `bool` |
| `signature` | `str` |
| `account_name` | `str \| None` |

### `PaystackTransactionCustomer`

Nested object inside `PaystackTransaction.customer`.

This type is part of the response model but is not exported directly.

| Field | Type |
| --- | --- |
| `id` | `int` |
| `first_name` | `str \| None` |
| `last_name` | `str \| None` |
| `email` | `str` |
| `customer_code` | `str` |
| `phone` | `str \| None` |
| `metadata` | `object` |
| `risk_action` | `str` |
| `international_format_phone` | `str \| None` |

### `PaystackBank`

| Field | Type |
| --- | --- |
| `name` | `str` |
| `slug` | `str` |
| `code` | `str` |
| `longcode` | `str` |
| `gateway` | `str \| None` |
| `pay_with_bank` | `bool` |
| `active` | `bool` |
| `is_deleted` | `bool \| None` |
| `country` | `str` |
| `currency` | `str` |
| `type` | `str` |
| `id` | `int` |
| `createdAt` | `str` |
| `updatedAt` | `str` |

### `PaystackListBanksQuery`

| Field | Type | Required |
| --- | --- | --- |
| `country` | `str` | No |
| `use_cursor` | `bool` | No |
| `perPage` | `int` | No |
| `pay_with_bank_transfer` | `bool` | No |
| `pay_with_bank` | `bool` | No |
| `enabled_for_verification` | `bool` | No |
| `next` | `str` | No |
| `previous` | `str` | No |
| `gateway` | `str` | No |
| `type` | `str` | No |
| `currency` | `str` | No |
| `include_nip_sort_code` | `bool` | No |

### `PaystackListBanksResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `list[PaystackBank]` |
| `meta` | `PaystackCursorMeta` |

### `PaystackCursorMeta`

Nested object inside `PaystackListBanksResponse.meta`.

This type is part of the response model but is not exported directly.

| Field | Type |
| --- | --- |
| `total` | `int` |
| `skipped` | `int` |
| `perPage` | `int` |
| `page` | `int` |
| `pageCount` | `int` |
| `next` | `str \| None` |
| `previous` | `str \| None` |

### `PaystackResolveAccountData`

| Field | Type |
| --- | --- |
| `account_number` | `str` |
| `account_name` | `str` |
| `bank_id` | `int` |

### `PaystackResolveAccountResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackResolveAccountData` |

### `PaystackTransferRecipientDetails`

| Field | Type |
| --- | --- |
| `authorization_code` | `str \| None` |
| `account_number` | `str \| None` |
| `account_name` | `str \| None` |
| `bank_code` | `str \| None` |
| `bank_name` | `str \| None` |

### `PaystackTransferRecipient`

| Field | Type |
| --- | --- |
| `active` | `bool` |
| `createdAt` | `str` |
| `currency` | `str` |
| `description` | `str \| None` |
| `domain` | `str` |
| `email` | `str \| None` |
| `id` | `int` |
| `integration` | `int` |
| `metadata` | `object` |
| `name` | `str` |
| `recipient_code` | `str` |
| `type` | `str` |
| `updatedAt` | `str` |
| `is_deleted` | `bool` |
| `isDeleted` | `bool` |
| `details` | `PaystackTransferRecipientDetails` |

### `PaystackCreateTransferRecipientRequest`

| Field | Type | Required |
| --- | --- | --- |
| `type` | `Literal["authorization", "basa", "ghipss", "kepss", "mobile_money", "mobile_money_business", "nuban"]` | Yes |
| `name` | `str` | Yes |
| `account_number` | `str` | No |
| `bank_code` | `str` | No |
| `description` | `str` | No |
| `currency` | `str` | No |
| `authorization_code` | `str` | No |
| `email` | `str` | No |
| `metadata` | `object` | No |

### `PaystackCreateTransferRecipientResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackTransferRecipient` |

### `PaystackTransfer`

| Field | Type |
| --- | --- |
| `transfersessionid` | `list[object]` |
| `transfertrials` | `list[object]` |
| `domain` | `str` |
| `amount` | `int` |
| `currency` | `str` |
| `reference` | `str` |
| `source` | `str` |
| `source_details` | `object` |
| `reason` | `str \| None` |
| `status` | `str` |
| `failures` | `object` |
| `transfer_code` | `str` |
| `titan_code` | `object` |
| `transferred_at` | `str \| None` |
| `id` | `int` |
| `integration` | `int` |
| `request` | `object` |
| `recipient` | `object` |
| `createdAt` | `str` |
| `updatedAt` | `str` |

### `PaystackInitiateTransferRequest`

| Field | Type | Required |
| --- | --- | --- |
| `source` | `str` | Yes |
| `amount` | `int` | Yes |
| `recipient` | `str` | Yes |
| `reference` | `str` | No |
| `reason` | `str` | No |
| `currency` | `str` | No |
| `account_reference` | `str` | No |

### `PaystackInitiateTransferResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackTransfer` |

### `PaystackFinalizeTransferRequest`

| Field | Type | Required |
| --- | --- | --- |
| `transfer_code` | `str` | Yes |
| `otp` | `str` | Yes |

### `PaystackFinalizeTransferResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackTransfer` |

### `PaystackVerifyTransferResponse`

Includes `PaystackApiResponse` plus:

| Field | Type |
| --- | --- |
| `data` | `PaystackTransfer` |

## Async and Validation Notes

- many payment APIs are asynchronous even when the initial HTTP request succeeds
- treat the initial response as accepted, queued, or processing unless the provider explicitly states final settlement
- final outcomes may arrive through callbacks, IPNs, or follow-up query endpoints
- the package uses type hints and `TypedDict` payload models for developer guidance
- the package does not perform full runtime schema validation of request or response payloads
- provider JSON is returned as parsed provider payloads

## Live Sandbox Checks

The test suite includes opt-in live tests in `tests/test_live_sandbox.py`.

They are skipped by default. To run them:

```bash
export NORIAPAY_RUN_LIVE_SANDBOX_TESTS=1
uv run pytest -m integration
```

Provide the relevant environment variables documented above before running them.

For Paystack, use a test secret key, not a live key.

## Notes

- the Python package is synchronous by design
- for concurrent or async-heavy systems, wrap calls in your own worker pool or use a future async variant
- request payloads accept numbers for `Amount`, but the SDK serializes them to provider-compatible strings where implemented
