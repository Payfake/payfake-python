from __future__ import annotations

from typing import TYPE_CHECKING

from .types import (
    KeysResponse,
    LoginInput,
    LoginResponse,
    MerchantData,
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
