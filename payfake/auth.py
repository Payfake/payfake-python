from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPClient


class AuthNamespace:
    """
    Wraps the /auth endpoints.

    Register and Login require no authentication, they are how
    you get credentials in the first place.

    GetKeys and RegenerateKeys require a JWT token obtained from
    Login, pass it explicitly to each call.
    """

    def __init__(self, client: "_HTTPClient") -> None:
        self._client = client

    def register(self, *, business_name: str, email: str, password: str) -> dict:
        """
        Create a new merchant account.
        Returns the merchant data and a JWT token.
        The token is valid for the configured JWT_EXPIRY_HOURS.
        """
        body = {"business_name": business_name, "email": email, "password": password}
        return self._client.do_public("POST", "/api/v1/auth/register", body)

    def login(self, *, email: str, password: str) -> dict:
        """
        Authenticate a merchant and return a JWT token.
        Store the token, you need it for control and key endpoints.
        """
        body = {"email": email, "password": password}
        return self._client.do_public("POST", "/api/v1/auth/login", body)

    def get_keys(self, token: str) -> dict:
        """Fetch the merchant's current public and secret keys."""
        return self._client.do_jwt("GET", "/api/v1/auth/keys", None, token)

    def regenerate_keys(self, token: str) -> dict:
        """
        Generate a new key pair.
        The old secret key is immediately invalid after this call,
        update your environment variables before calling this in production.
        """
        return self._client.do_jwt(
            "POST", "/api/v1/auth/keys/regenerate", None, token
        )

    def get_profile(self, token: str) -> dict:
        """Fetch full merchant profile."""
        return self._client.do_jwt("GET", "/api/v1/merchant", None, token)

    def update_profile(
        self, token: str, *, business_name: str = "", webhook_url: str | None = None
    ) -> dict:
        """Update merchant business name and/or webhook URL."""
        body = {}
        if business_name:
            body["business_name"] = business_name
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        return self._client.do_jwt(
            "PUT",
            "/api/v1/merchant",
            body or None,
            token,
        )

    def get_webhook_url(self, token: str) -> dict:
        """Get current webhook URL and config."""
        return self._client.do_jwt(
            "GET", "/api/v1/merchant/webhook", None, token
        )

    def update_webhook_url(self, token: str, webhook_url: str) -> dict:
        """Set merchant webhook URL."""
        return self._client.do_jwt(
            "POST",
            "/api/v1/merchant/webhook",
            {"webhook_url": webhook_url},
            token,
        )

    def test_webhook(self, token: str) -> dict:
        """Fire a test webhook to verify the endpoint is reachable."""
        return self._client.do_jwt(
            "POST", "/api/v1/merchant/webhook/test", None, token
        )
