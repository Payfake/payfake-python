from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPClient


class CustomerNamespace:
    """
    Wraps /customer endpoints.
    Matches https://api.paystack.co/customer exactly.
    Auth: Bearer sk_test_xxx
    """

    def __init__(self, http: "_HTTPClient") -> None:
        self._http = http

    def create(
        self,
        *,
        email: str,
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
        metadata: dict | None = None,
    ) -> dict:
        """Create a new customer."""
        body: dict = {"email": email}
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if phone:
            body["phone"] = phone
        if metadata:
            body["metadata"] = metadata
        return self._http.do("POST", "/customer", body)

    def list(self, *, page: int = 1, per_page: int = 50) -> dict:
        """List customers with pagination."""
        return self._http.do("GET", f"/customer?page={page}&perPage={per_page}")

    def fetch(self, code: str) -> dict:
        """Fetch a customer by their code (CUS_xxxxxxxx)."""
        return self._http.do("GET", f"/customer/{code}")

    def update(self, code: str, **kwargs) -> dict:
        """
        Partially update a customer.
        Pass only the fields you want to update.
        kwargs: first_name, last_name, phone, metadata
        """
        return self._http.do("PUT", f"/customer/{code}", kwargs or None)

    def transactions(self, code: str, *, page: int = 1, per_page: int = 50) -> dict:
        """Get paginated transactions for a customer."""
        return self._http.do(
            "GET", f"/customer/{code}/transactions?page={page}&perPage={per_page}"
        )
