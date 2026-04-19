from __future__ import annotations

from typing import TYPE_CHECKING

from .types import (
    CustomerSummary,
    InitializeInput,
    InitializeResponse,
    ListOptions,
    PaginationMeta,
    PublicTransactionResponse,
    PublicVerifyResponse,
    Transaction,
    TransactionList,
)

if TYPE_CHECKING:
    from .client import Client


def _parse_transaction(data: dict) -> Transaction:
    """
    Deserialize a raw transaction dict into a Transaction dataclass.
    We handle the nested customer object separately since it needs
    its own deserialization, dataclass fields don't auto-nest.
    """
    customer_data = data.pop("customer", {}) or {}
    customer = CustomerSummary(
        **{
            k: v
            for k, v in customer_data.items()
            if k in CustomerSummary.__dataclass_fields__
        }
    )
    tx_fields = {k: v for k, v in data.items() if k in Transaction.__dataclass_fields__}
    tx_fields["customer"] = customer
    return Transaction(**tx_fields)


class TransactionNamespace:
    def __init__(self, client: "Client") -> None:
        self._client = client

    def initialize(self, input: InitializeInput) -> InitializeResponse:
        """
        Create a new pending transaction.
        Returns the authorization_url for the payment popup and the
        access_code the popup uses to identify the transaction.
        """
        data = self._client._request(
            "POST", "/api/v1/transaction/initialize", body=input
        )
        return InitializeResponse(
            authorization_url=data["authorization_url"],
            access_code=data["access_code"],
            reference=data["reference"],
        )

    def verify(self, reference: str) -> Transaction:
        """
        Verify a transaction by reference.
        Call this after the payment popup closes to confirm the outcome.
        A status of "success" means the charge went through.
        """
        data = self._client._request("GET", f"/api/v1/transaction/verify/{reference}")
        return _parse_transaction(data)

    def get(self, id: str) -> Transaction:
        """Fetch a single transaction by its ID."""
        data = self._client._request("GET", f"/api/v1/transaction/{id}")
        return _parse_transaction(data)

    def list(self, opts: ListOptions | None = None) -> TransactionList:
        """
        List transactions with pagination.
        Pass a ListOptions instance to control page and per_page.
        Defaults to page=1, per_page=50.
        """
        opts = opts or ListOptions()
        data = self._client._request(
            "GET",
            f"/api/v1/transaction?page={opts.page}&per_page={opts.per_page}",
        )
        transactions = [_parse_transaction(tx) for tx in data.get("transactions", [])]
        meta_data = data.get("meta", {})
        meta = PaginationMeta(
            **{
                k: v
                for k, v in meta_data.items()
                if k in PaginationMeta.__dataclass_fields__
            }
        )
        return TransactionList(transactions=transactions, meta=meta)

    def refund(self, id: str) -> Transaction:
        """
        Refund a successful transaction.
        Only transactions with status "success" can be refunded.
        """
        data = self._client._request("POST", f"/api/v1/transaction/{id}/refund")
        return _parse_transaction(data)

    def public_fetch(self, access_code: str) -> "PublicTransactionResponse":
        """
        Load transaction details for the checkout page.
        No secret key required — authenticated via access code.
        Returns amount, currency, merchant branding, customer email
        and current charge flow status.

        Called on checkout page mount::

            tx = client.transaction.public_fetch(access_code)
            print(f"Pay {tx.merchant['business_name']} GHS {tx.amount / 100:.2f}")
        """

        data = self._client._request("GET", f"/api/v1/public/transaction/{access_code}")
        return PublicTransactionResponse(
            **{
                k: v
                for k, v in data.items()
                if k in PublicTransactionResponse.__dataclass_fields__
            }
        )

    def public_verify(self, reference: str) -> "PublicVerifyResponse":
        """
        Poll transaction status for MoMo pay_offline state.
        No secret key required.
        Poll every 3 seconds, stop when status is success or failed::

            import time
            while True:
                result = client.transaction.public_verify(reference)
                if result.status in ("success", "failed"):
                    break
                time.sleep(3)
        """

        data = self._client._request(
            "GET", f"/api/v1/public/transaction/verify/{reference}"
        )
        return PublicVerifyResponse(
            **{
                k: v
                for k, v in data.items()
                if k in PublicVerifyResponse.__dataclass_fields__
            }
        )
