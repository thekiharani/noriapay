from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import requests

from .exceptions import AuthenticationError
from .types import AccessToken
from .utils import encode_basic_auth, to_object


@dataclass(slots=True)
class ClientCredentialsTokenProvider:
    token_url: str
    client_id: str
    client_secret: str
    session: requests.Session | Any | None = None
    timeout_seconds: float | None = None
    query: dict[str, str | int | float | bool | None] | None = None
    cache_skew_seconds: float = 60.0
    map_response: Callable[[dict[str, Any]], AccessToken] | None = None
    _cached_token: AccessToken | None = field(default=None, init=False)
    _expires_at: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()

    def get_access_token(self, force_refresh: bool = False) -> str:
        return self.get_token(force_refresh=force_refresh).access_token

    def get_token(self, force_refresh: bool = False) -> AccessToken:
        now = time.monotonic()
        if not force_refresh and self._cached_token is not None and now < self._expires_at:
            return self._cached_token

        headers = {
            "authorization": f"Basic {encode_basic_auth(self.client_id, self.client_secret)}",
            "accept": "application/json",
        }
        params = {key: value for key, value in (self.query or {}).items() if value is not None}

        try:
            response = self.session.request(
                method="GET",
                url=self.token_url,
                headers=headers,
                params=params or None,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as error:
            raise AuthenticationError(
                "Authentication request timed out.", details={"error": error}
            ) from error
        except requests.RequestException as error:
            raise AuthenticationError(
                "Unable to obtain access token.", details={"error": error}
            ) from error

        try:
            payload = to_object(response.json())
        except ValueError:
            payload = {}

        if not response.ok:
            raise AuthenticationError("Authentication request failed.", details=payload)

        mapper = self.map_response or _default_access_token_mapper
        token = mapper(payload)
        self._cached_token = token
        ttl_seconds = max(0.0, float(token.expires_in) - self.cache_skew_seconds)
        self._expires_at = time.monotonic() + ttl_seconds
        return token

    def clear_cache(self) -> None:
        self._cached_token = None
        self._expires_at = 0.0


def _default_access_token_mapper(payload: dict[str, Any]) -> AccessToken:
    return AccessToken(
        access_token=str(payload.get("access_token", "")),
        expires_in=int(payload.get("expires_in", 0)),
        token_type=payload.get("token_type")
        if isinstance(payload.get("token_type"), str)
        else None,
        scope=payload.get("scope") if isinstance(payload.get("scope"), str) else None,
        raw=payload,
    )
