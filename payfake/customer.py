from __future__ import annotations

from typing import TYPE_CHECKING

from .transaction import _parse_transaction
from .types import (
    CreateCustomerInput,
    Customer,
    CustomerList,
    ListOptions,
    PaginationMeta,
    TransactionList,
    UpdateCustomerInput,
)

if TYPE_CHECKING:
    from .client import Client


def _parse_customer(data: dict) -> Customer:
    return Customer(
        **{k: v for k, v in data.items() if k in Customer.__dataclass_fields__}
    )


class CustomerNamespace:
    def __init__(self, client: "Client") -> None:
        self._client = client

    def create(self, input: CreateCustomerInput) -> Customer:
        """Create a new customer under the merchant account."""
        data = self._client._request("POST", "/api/v1/customer", body=input)
        return _parse_customer(data)

    def list(self, opts: ListOptions | None = None) -> CustomerList:
        """List customers with pagination."""
        opts = opts or ListOptions()
        data = self._client._request(
            "GET",
            f"/api/v1/customer?page={opts.page}&per_page={opts.per_page}",
        )
        customers = [_parse_customer(c) for c in data.get("customers", [])]
        meta = PaginationMeta(
            **{
                k: v
                for k, v in data.get("meta", {}).items()
                if k in PaginationMeta.__dataclass_fields__
            }
        )
        return CustomerList(customers=customers, meta=meta)

    def get(self, code: str) -> Customer:
        """Fetch a customer by their code (CUS_xxxxxxxx)."""
        data = self._client._request("GET", f"/api/v1/customer/{code}")
        return _parse_customer(data)

    def update(self, code: str, input: UpdateCustomerInput) -> Customer:
        """
        Partially update a customer.
        Only non-None fields are sent, None means "don't touch this field".
        """
        data = self._client._request("PUT", f"/api/v1/customer/{code}", body=input)
        return _parse_customer(data)

    def transactions(
        self, code: str, opts: ListOptions | None = None
    ) -> TransactionList:
        """Fetch paginated transactions for a specific customer."""
        opts = opts or ListOptions()
        data = self._client._request(
            "GET",
            f"/api/v1/customer/{code}/transactions?page={opts.page}&per_page={opts.per_page}",
        )
        transactions = [_parse_transaction(tx) for tx in data.get("transactions", [])]
        meta = PaginationMeta(
            **{
                k: v
                for k, v in data.get("meta", {}).items()
                if k in PaginationMeta.__dataclass_fields__
            }
        )
        return TransactionList(transactions=transactions, meta=meta)
