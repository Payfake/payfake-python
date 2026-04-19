from __future__ import annotations

from typing import TYPE_CHECKING

from .types import (
    KeysResponse,
    LoginInput,
    LoginResponse,
    MerchantData,
    MerchantProfile,
    RegisterInput,
    RegisterResponse,
)

if TYPE_CHECKING:
    from .client import Client


class AuthNamespace:
    """
    Wraps the /auth endpoints.

    Register and Login require no authentication, they are how
    you get credentials in the first place.

    GetKeys and RegenerateKeys require a JWT token obtained from
    Login, pass it explicitly to each call.
    """

    def __init__(self, client: "Client") -> None:
        self._client = client

    def register(self, input: RegisterInput) -> RegisterResponse:
        """
        Create a new merchant account.
        Returns the merchant data and a JWT token.
        The token is valid for the configured JWT_EXPIRY_HOURS.
        """
        data = self._client._request("POST", "/api/v1/auth/register", body=input)
        merchant = MerchantData(
            **{
                k: v
                for k, v in data["merchant"].items()
                if k in MerchantData.__dataclass_fields__
            }
        )
        return RegisterResponse(merchant=merchant, token=data["token"])

    def login(self, input: LoginInput) -> LoginResponse:
        """
        Authenticate a merchant and return a JWT token.
        Store the token, you need it for control and key endpoints.
        """
        data = self._client._request("POST", "/api/v1/auth/login", body=input)
        merchant = MerchantData(
            **{
                k: v
                for k, v in data["merchant"].items()
                if k in MerchantData.__dataclass_fields__
            }
        )
        return LoginResponse(merchant=merchant, token=data["token"])

    def get_keys(self, token: str) -> KeysResponse:
        """Fetch the merchant's current public and secret keys."""
        data = self._client._request("GET", "/api/v1/auth/keys", token=token)
        return KeysResponse(
            public_key=data["public_key"],
            secret_key=data["secret_key"],
        )

    def regenerate_keys(self, token: str) -> KeysResponse:
        """
        Generate a new key pair.
        The old secret key is immediately invalid after this call,
        update your environment variables before calling this in production.
        """
        data = self._client._request(
            "POST", "/api/v1/auth/keys/regenerate", token=token
        )
        return KeysResponse(
            public_key=data["public_key"],
            secret_key=data["secret_key"],
        )

    def get_profile(self, token: str) -> "MerchantProfile":
        """Fetch full merchant profile."""
        from .types import MerchantProfile

        data = self._client._request("GET", "/api/v1/merchant", token=token)
        return MerchantProfile(
            **{
                k: v
                for k, v in data.items()
                if k in MerchantProfile.__dataclass_fields__
            }
        )

    def update_profile(
        self, token: str, business_name: str = "", webhook_url: str = ""
    ) -> "MerchantProfile":
        """Update merchant business name and/or webhook URL."""
        from .types import MerchantProfile

        body = {}
        if business_name:
            body["business_name"] = business_name
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        data = self._client._request(
            "PUT",
            "/api/v1/merchant",
            token=token,
            body=type("_B", (), {"__dict__": body})(),
        )
        return MerchantProfile(
            **{
                k: v
                for k, v in data.items()
                if k in MerchantProfile.__dataclass_fields__
            }
        )

    def get_webhook_url(self, token: str) -> dict:
        """Get current webhook URL and config."""
        return self._client._request("GET", "/api/v1/merchant/webhook", token=token)

    def update_webhook_url(self, token: str, webhook_url: str) -> None:
        """Set merchant webhook URL."""
        import dataclasses

        @dataclasses.dataclass
        class _Input:
            webhook_url: str

        self._client._request(
            "POST",
            "/api/v1/merchant/webhook",
            body=_Input(webhook_url=webhook_url),
            token=token,
        )

    def test_webhook(self, token: str) -> dict:
        """Fire a test webhook to verify the endpoint is reachable."""
        return self._client._request(
            "POST", "/api/v1/merchant/webhook/test", token=token
        )
