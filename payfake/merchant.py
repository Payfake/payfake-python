from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPClient


class MerchantNamespace:
    """
    Wraps /api/v1/merchant endpoints.
    Payfake-specific, no Paystack equivalent.
    Auth: Bearer JWT (from auth.login)
    """

    def __init__(self, http: "_HTTPClient") -> None:
        self._http = http

    def get_profile(self, token: str) -> dict:
        """Get the full merchant profile."""
        return self._http.do_jwt("GET", "/api/v1/merchant", None, token)

    def update_profile(
        self,
        token: str,
        *,
        business_name: str = "",
        webhook_url: str | None = None,
    ) -> dict:
        """Update merchant business name and/or webhook URL."""
        body: dict = {}
        if business_name:
            body["business_name"] = business_name
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        return self._http.do_jwt("PUT", "/api/v1/merchant", body, token)

    def get_webhook_url(self, token: str) -> dict:
        """Get the current webhook URL and whether it's configured."""
        return self._http.do_jwt("GET", "/api/v1/merchant/webhook", None, token)

    def update_webhook_url(self, token: str, webhook_url: str) -> dict:
        """Set the merchant's webhook URL."""
        return self._http.do_jwt(
            "POST", "/api/v1/merchant/webhook", {"webhook_url": webhook_url}, token
        )

    def test_webhook(self, token: str) -> dict:
        """
        Fire a test webhook to verify the endpoint is reachable.
        Rate limited to 5 requests per minute per merchant.
        """
        return self._http.do_jwt("POST", "/api/v1/merchant/webhook/test", None, token)
