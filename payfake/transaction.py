from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPClient


class TransactionNamespace:
    """
    Wraps /transaction endpoints.
    Matches https://api.paystack.co/transaction exactly.
    Auth: Bearer sk_test_xxx
    """

    def __init__(self, http: "_HTTPClient") -> None:
        self._http = http

    def initialize(
        self,
        *,
        email: str,
        amount: int,
        currency: str = "GHS",
        reference: str = "",
        callback_url: str = "",
        channels: list[str] | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Create a new pending transaction.
        Returns authorization_url, access_code and reference.
        Redirect your customer to authorization_url.
        """
        body = {"email": email, "amount": amount, "currency": currency}
        if reference:
            body["reference"] = reference
        if callback_url:
            body["callback_url"] = callback_url
        if channels:
            body["channels"] = channels
        if metadata:
            body["metadata"] = metadata
        return self._http.do("POST", "/transaction/initialize", body)

    def verify(self, reference: str) -> dict:
        """
        Verify a transaction by reference.
        Always call this before delivering value.
        """
        return self._http.do("GET", f"/transaction/verify/{reference}")

    def fetch(self, id: str) -> dict:
        """Fetch a transaction by ID."""
        return self._http.do("GET", f"/transaction/{id}")

    def list(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        status: str = "",
    ) -> dict:
        """
        List transactions with pagination.
        status: "success" | "failed" | "pending" | "abandoned"
        """
        path = f"/transaction?page={page}&perPage={per_page}"
        if status:
            path += f"&status={status}"
        return self._http.do("GET", path)

    def refund(self, id: str) -> dict:
        """Refund (reverse) a successful transaction."""
        return self._http.do("POST", f"/transaction/{id}/refund")

    def public_fetch(self, access_code: str) -> dict:
        """
        Load transaction details for the checkout page using the access code.
        No secret key required. Returns merchant branding, amount, currency
        and current charge flow status. Call this on checkout page mount.
        """
        return self._http.do_public("GET", f"/api/v1/public/transaction/{access_code}")

    def public_verify(self, reference: str, access_code: str) -> dict:
        """
        Poll transaction status for MoMo pay_offline state.
        No secret key required. Poll every 3 seconds, stop when
        status is "success" or "failed".

        Example::

            while True:
                result = client.transaction.public_verify(reference, access_code)
                if result["status"] in ("success", "failed"):
                    break
                time.sleep(3)
        """
        return self._http.do_public(
            "GET",
            f"/api/v1/public/transaction/verify/{reference}?access_code={access_code}",
        )
