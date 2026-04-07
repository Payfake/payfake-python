from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Type, TypeVar

import httpx

from .errors import APIErrorField, PayfakeError

T = TypeVar("T")

DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_TIMEOUT = 30.0


def _clean(data: Any) -> Any:
    """
    Recursively remove None values from a dict before sending to the API.
    This implements the partial-update pattern, fields set to None
    in UpdateCustomerInput, UpdateScenarioInput etc are not included
    in the request body, so the API treats them as "don't touch".
    """
    if isinstance(data, dict):
        return {k: _clean(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [_clean(i) for i in data]
    return data


def _to_dict(obj: Any) -> dict:
    """
    Convert a dataclass to a dict, stripping None values.
    We use dataclasses for all input types, this helper converts
    them to clean dicts for JSON serialization.
    """
    if is_dataclass(obj):
        return _clean(asdict(obj))
    return obj


def _from_dict(data: dict, cls: Type[T]) -> T:
    """
    Deserialize a dict into a dataclass.
    We only map keys that exist in the dataclass, extra keys from
    the API response are ignored rather than raising an error. This
    means new fields added to the API won't break older SDK versions.
    """
    import inspect

    params = inspect.signature(cls.__init__).parameters
    filtered = {k: v for k, v in data.items() if k in params}
    return cls(**filtered)


class Client:
    """
    The root Payfake SDK client.

    All API namespaces are accessible as attributes::

        client = Client(secret_key="sk_test_xxx")
        client.transaction.initialize(...)
        client.charge.card(...)
        client.customer.create(...)

    The client uses httpx for HTTP, synchronous by default.
    All methods accept an optional timeout parameter that overrides
    the client-level default for that specific call.
    """

    def __init__(
        self,
        secret_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")

        # httpx.Client is the underlying HTTP client.
        # We configure it once here and reuse it across all requests,
        # this enables HTTP connection pooling which reduces latency
        # on repeated calls compared to creating a new connection each time.
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        # Import namespace services here to avoid circular imports,
        # each service imports Client for type hints.
        from .auth import AuthNamespace
        from .charge import ChargeNamespace
        from .control import ControlNamespace
        from .customer import CustomerNamespace
        from .transaction import TransactionNamespace

        self.auth = AuthNamespace(self)
        self.transaction = TransactionNamespace(self)
        self.charge = ChargeNamespace(self)
        self.customer = CustomerNamespace(self)
        self.control = ControlNamespace(self)

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        token: str | None = None,
    ) -> dict:
        """
        Execute an HTTP request and return the unwrapped data dict.

        This is the single HTTP execution point for the entire SDK —
        auth headers, error parsing and response unwrapping all happen
        here exactly once. Namespace methods call this; they never
        use httpx directly.

        token overrides the secret key for JWT-authenticated endpoints.
        Pass the dashboard JWT token here for /control and /auth/keys routes.
        """
        auth_value = token if token else self.secret_key

        headers = {"Authorization": f"Bearer {auth_value}"} if auth_value else {}

        kwargs: dict[str, Any] = {"headers": headers}
        if body is not None:
            # Serialize dataclass inputs to clean dicts before sending.
            kwargs["content"] = json.dumps(_to_dict(body))

        resp = self._http.request(method, path, **kwargs)

        # Parse the envelope regardless of HTTP status.
        # We need the code and message from the envelope body
        # even on 4xx/5xx responses to build the SDKError correctly.
        try:
            envelope = resp.json()
        except Exception:
            raise PayfakeError(
                code="PARSE_ERROR",
                message=f"Failed to parse response: {resp.text}",
                http_status=resp.status_code,
            )

        if envelope.get("status") != "success":
            raw_fields = envelope.get("errors", [])
            fields = [
                APIErrorField(field=f.get("field", ""), message=f.get("message", ""))
                for f in raw_fields
            ]
            raise PayfakeError(
                code=envelope.get("code", "UNKNOWN_ERROR"),
                message=envelope.get("message", "An error occurred"),
                fields=fields,
                http_status=resp.status_code,
            )

        return envelope.get("data") or {}

    def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
