from __future__ import annotations

import httpx

from .auth import AuthNamespace
from .charge import ChargeNamespace
from .control import ControlNamespace
from .customer import CustomerNamespace
from .errors import ErrorField, PayfakeError
from .merchant import MerchantNamespace
from .transaction import TransactionNamespace

DEFAULT_BASE_URL = "https://api.payfake.co"
DEFAULT_TIMEOUT = 30.0


class _HTTPClient:
    """Internal HTTP client shared by all namespaces."""

    def __init__(self, secret_key: str, base_url: str, timeout: float) -> None:
        self._secret_key = secret_key
        self._base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def do(self, method: str, path: str, body: dict | None = None) -> dict:
        return self._request(method, path, body, self._secret_key)

    def do_jwt(self, method: str, path: str, body: dict | None, token: str) -> dict:
        return self._request(method, path, body, token or None)

    def do_public(self, method: str, path: str, body: dict | None = None) -> dict:
        return self._request(method, path, body, None)

    def _request(
        self, method: str, path: str, body: dict | None, token: str | None
    ) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = self._http.request(
            method, self._base_url + path, json=body, headers=headers
        )

        try:
            envelope = response.json()
        except Exception as exc:
            raise PayfakeError(
                "PARSE_ERROR",
                f"Failed to parse response (HTTP {response.status_code})",
                http_status=response.status_code,
            ) from exc

        if envelope.get("status") is not True:
            raw_errors = envelope.get("errors") or {}
            fields: list[ErrorField] = []
            for field_name, rules in raw_errors.items():
                for rule in rules:
                    fields.append(
                        ErrorField(
                            field=field_name,
                            rule=rule.get("rule", ""),
                            message=rule.get("message", ""),
                        )
                    )
            raise PayfakeError(
                code=response.headers.get("X-Payfake-Code", "UNKNOWN_ERROR"),
                message=envelope.get("message", "An error occurred"),
                fields=fields,
                http_status=response.status_code,
            )

        return envelope.get("data") or {}


class Client:
    """
    Payfake SDK client.

    Usage::

        from payfake import Client

        client = Client(secret_key="sk_test_xxx")

        # Self-hosted:
        client = Client(secret_key="sk_test_xxx", base_url="http://localhost:8080")

    Use as a context manager to ensure the underlying HTTP session is closed::

        with Client(secret_key="sk_test_xxx") as client:
            tx = client.transaction.initialize(email="...", amount=10000)
    """

    def __init__(
        self,
        *,
        secret_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        http = _HTTPClient(secret_key, base_url, timeout)
        #: Auth — register, login, me, keys
        self.auth = AuthNamespace(http)
        #: Transaction — initialize, verify, fetch, list, refund, public_fetch, public_verify
        self.transaction = TransactionNamespace(http)
        #: Charge — card, mobile_money, bank, submit_*, resend_otp, simulate_3ds
        self.charge = ChargeNamespace(http)
        #: Customer — create, list, fetch, update, transactions
        self.customer = CustomerNamespace(http)
        #: Merchant — profile, webhook management
        self.merchant = MerchantNamespace(http)
        #: Control — stats, scenarios, logs, OTP logs, force transaction
        self.control = ControlNamespace(http)
        self._http = http

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
