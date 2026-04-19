from __future__ import annotations

from typing import TYPE_CHECKING

from .transaction import _parse_transaction
from .types import (
    CustomerList,
    ForceTransactionInput,
    ListOptions,
    OTPLog,
    PaginationMeta,
    RequestLog,
    ScenarioConfig,
    Transaction,
    TransactionList,
    UpdateScenarioInput,
    WebhookAttempt,
    WebhookEvent,
)

if TYPE_CHECKING:
    from .client import Client


def _parse_scenario(data: dict) -> ScenarioConfig:
    return ScenarioConfig(
        **{k: v for k, v in data.items() if k in ScenarioConfig.__dataclass_fields__}
    )


class ControlNamespace:
    """
    Wraps the /control endpoints, Payfake's power layer.
    All methods require a JWT token from client.auth.login().
    These are dashboard operations, not application-level API calls.
    """

    def __init__(self, client: "Client") -> None:
        self._client = client

    def get_scenario(self, token: str) -> ScenarioConfig:
        """Fetch the current scenario config for the merchant."""
        data = self._client._request("GET", "/api/v1/control/scenario", token=token)
        return _parse_scenario(data)

    def update_scenario(self, token: str, input: UpdateScenarioInput) -> ScenarioConfig:
        """
        Update the scenario config.
        Only non-None fields are sent.

        Examples::

            # 30% failure rate
            client.control.update_scenario(token, UpdateScenarioInput(failure_rate=0.3))

            # Force all charges to fail with insufficient funds
            client.control.update_scenario(token, UpdateScenarioInput(
                force_status="failed",
                error_code="CHARGE_INSUFFICIENT_FUNDS",
            ))

            # Add 2 second delay to all charges
            client.control.update_scenario(token, UpdateScenarioInput(delay_ms=2000))
        """
        data = self._client._request(
            "PUT", "/api/v1/control/scenario", body=input, token=token
        )
        return _parse_scenario(data)

    def reset_scenario(self, token: str) -> ScenarioConfig:
        """
        Reset scenario config to defaults.
        After reset: failure_rate=0, delay_ms=0, no forced status.
        All charges will succeed instantly.
        """
        data = self._client._request(
            "POST", "/api/v1/control/scenario/reset", token=token
        )
        return _parse_scenario(data)

    def list_webhooks(
        self, token: str, opts: ListOptions | None = None
    ) -> list[WebhookEvent]:
        """List webhook events with delivery status."""
        opts = opts or ListOptions()
        data = self._client._request(
            "GET",
            f"/api/v1/control/webhooks?page={opts.page}&per_page={opts.per_page}",
            token=token,
        )
        return [
            WebhookEvent(
                **{k: v for k, v in w.items() if k in WebhookEvent.__dataclass_fields__}
            )
            for w in data.get("webhooks", [])
        ]

    def retry_webhook(self, token: str, webhook_id: str) -> None:
        """Manually re-trigger delivery for a failed webhook event."""
        self._client._request(
            "POST", f"/api/v1/control/webhooks/{webhook_id}/retry", token=token
        )

    def get_webhook_attempts(self, token: str, webhook_id: str) -> list[WebhookAttempt]:
        """Fetch all delivery attempts for a webhook event."""
        data = self._client._request(
            "GET", f"/api/v1/control/webhooks/{webhook_id}/attempts", token=token
        )
        return [
            WebhookAttempt(
                **{
                    k: v
                    for k, v in a.items()
                    if k in WebhookAttempt.__dataclass_fields__
                }
            )
            for a in data.get("attempts", [])
        ]

    def force_transaction(
        self, token: str, reference: str, input: ForceTransactionInput
    ) -> Transaction:
        """
        Force a pending transaction to a specific terminal state.
        This bypasses the scenario engine entirely,
        the outcome is always exactly what you specify.

        status must be one of: success, failed, abandoned.
        """
        data = self._client._request(
            "POST",
            f"/api/v1/control/transactions/{reference}/force",
            body=input,
            token=token,
        )
        return _parse_transaction(data)

    def get_logs(self, token: str, opts: ListOptions | None = None) -> list[RequestLog]:
        """Fetch paginated request/response introspection logs."""
        opts = opts or ListOptions()
        data = self._client._request(
            "GET",
            f"/api/v1/control/logs?page={opts.page}&per_page={opts.per_page}",
            token=token,
        )
        return [
            RequestLog(
                **{k: v for k, v in log.items() if k in RequestLog.__dataclass_fields__}
            )
            for log in data.get("logs", [])
        ]

    def clear_logs(self, token: str) -> None:
        """Permanently delete all logs for the merchant."""
        self._client._request("DELETE", "/api/v1/control/logs", token=token)

    def get_otp_logs(
        self,
        token: str,
        reference: str = "",
        opts: ListOptions | None = None,
    ) -> list[OTPLog]:
        """
        Fetch OTP codes generated during charge flows.
        Pass reference to filter for a specific transaction.

        This is the primary way to get OTPs during testing without a real phone::

            logs = client.control.get_otp_logs(token, reference=tx.reference)
            otp = logs[0].otp_code
        """
        from .types import OTPLog

        path = "/api/v1/control/otp-logs"
        if reference:
            path += f"?reference={reference}"
        elif opts:
            path += f"?page={opts.page}&per_page={opts.per_page}"

        data = self._client._request("GET", path, token=token)

        raw_logs = data.get("otp_logs", [])
        return [
            OTPLog(**{k: v for k, v in log.items() if k in OTPLog.__dataclass_fields__})
            for log in raw_logs
        ]

    def list_transactions(
        self,
        token: str,
        page: int = 1,
        per_page: int = 50,
        status: str = "",
        search: str = "",
    ) -> TransactionList:
        """
        JWT-authenticated transaction list for the dashboard.
        Supports filtering by status and searching by reference or customer email.
        """
        path = f"/api/v1/control/transactions?page={page}&per_page={per_page}"
        if status:
            path += f"&status={status}"
        if search:
            path += f"&search={search}"

        data = self._client._request("GET", path, token=token)
        transactions = [_parse_transaction(tx) for tx in data.get("transactions", [])]
        meta = PaginationMeta(
            **{
                k: v
                for k, v in data.get("meta", {}).items()
                if k in PaginationMeta.__dataclass_fields__
            }
        )
        return TransactionList(transactions=transactions, meta=meta)

    def list_customers(
        self,
        token: str,
        opts: ListOptions | None = None,
    ) -> CustomerList:
        """JWT-authenticated customer list for the dashboard."""
        from .customer import _parse_customer

        opts = opts or ListOptions()
        data = self._client._request(
            "GET",
            f"/api/v1/control/customers?page={opts.page}&per_page={opts.per_page}",
            token=token,
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
