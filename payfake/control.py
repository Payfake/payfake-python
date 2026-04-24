from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPClient


class ControlNamespace:
    """
    Wraps /api/v1/control endpoints.
    Payfake-specific, no Paystack equivalent.
    Auth: Bearer JWT (from auth.login)
    """

    def __init__(self, http: "_HTTPClient") -> None:
        self._http = http

    def get_stats(self, token: str) -> dict:
        """Get aggregated overview stats for the dashboard."""
        return self._http.do_jwt("GET", "/api/v1/control/stats", None, token)

    def get_scenario(self, token: str) -> dict:
        """Get the current scenario config."""
        return self._http.do_jwt("GET", "/api/v1/control/scenario", None, token)

    def update_scenario(
        self,
        token: str,
        *,
        failure_rate: float | None = None,
        delay_ms: int | None = None,
        force_status: str | None = None,
        error_code: str | None = None,
    ) -> dict:
        """
        Update the scenario config.
        Only keyword args that are not None are sent.

        Example::

            # Force all charges to fail
            client.control.update_scenario(
                token,
                force_status="failed",
                error_code="CHARGE_INSUFFICIENT_FUNDS",
            )

            # 30% random failure rate with 2 second delay
            client.control.update_scenario(token, failure_rate=0.3, delay_ms=2000)
        """
        body: dict = {}
        if failure_rate is not None:
            body["failure_rate"] = failure_rate
        if delay_ms is not None:
            body["delay_ms"] = delay_ms
        if force_status is not None:
            body["force_status"] = force_status
        if error_code is not None:
            body["error_code"] = error_code
        return self._http.do_jwt("PUT", "/api/v1/control/scenario", body, token)

    def reset_scenario(self, token: str) -> dict:
        """Reset scenario to defaults. All charges succeed with no delay."""
        return self._http.do_jwt("POST", "/api/v1/control/scenario/reset", None, token)

    def list_transactions(
        self,
        token: str,
        *,
        page: int = 1,
        per_page: int = 50,
        status: str = "",
        search: str = "",
    ) -> dict:
        """
        JWT-authenticated transaction list for the dashboard.
        search matches reference or customer email.
        """
        path = f"/api/v1/control/transactions?page={page}&perPage={per_page}"
        if status:
            path += f"&status={status}"
        if search:
            path += f"&search={search}"
        return self._http.do_jwt("GET", path, None, token)

    def list_customers(self, token: str, *, page: int = 1, per_page: int = 50) -> dict:
        """JWT-authenticated customer list for the dashboard."""
        return self._http.do_jwt(
            "GET",
            f"/api/v1/control/customers?page={page}&perPage={per_page}",
            None,
            token,
        )

    def force_transaction(
        self,
        token: str,
        reference: str,
        *,
        status: str,
        error_code: str = "",
    ) -> dict:
        """
        Force a pending transaction to a specific terminal state.
        Bypasses the scenario engine — useful for deterministic test cases.
        status: "success" | "failed" | "abandoned"
        """
        body: dict = {"status": status}
        if error_code:
            body["error_code"] = error_code
        return self._http.do_jwt(
            "POST", f"/api/v1/control/transactions/{reference}/force", body, token
        )

    def list_webhooks(self, token: str, *, page: int = 1, per_page: int = 50) -> dict:
        """List webhook events."""
        return self._http.do_jwt(
            "GET",
            f"/api/v1/control/webhooks?page={page}&perPage={per_page}",
            None,
            token,
        )

    def retry_webhook(self, token: str, id: str) -> None:
        """Manually re-trigger delivery for a webhook event."""
        self._http.do_jwt("POST", f"/api/v1/control/webhooks/{id}/retry", None, token)

    def get_webhook_attempts(self, token: str, id: str) -> dict:
        """Get all delivery attempts for a webhook event."""
        return self._http.do_jwt(
            "GET", f"/api/v1/control/webhooks/{id}/attempts", None, token
        )

    def get_logs(self, token: str, *, page: int = 1, per_page: int = 50) -> dict:
        """Get paginated request/response introspection logs."""
        return self._http.do_jwt(
            "GET", f"/api/v1/control/logs?page={page}&perPage={per_page}", None, token
        )

    def clear_logs(self, token: str) -> None:
        """Permanently delete all request logs for the merchant."""
        self._http.do_jwt("DELETE", "/api/v1/control/logs", None, token)

    def get_otp_logs(
        self,
        token: str,
        reference: str = "",
        *,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict]:
        """
        Get OTP codes generated during charge flows.
        Primary way to read OTPs during testing without a real phone.

        Example::

            logs = client.control.get_otp_logs(token, reference=tx["reference"])
            otp  = logs[0]["otp_code"]

        Pass reference to filter for a specific transaction.
        """
        if reference:
            path = f"/api/v1/control/otp-logs?reference={reference}"
        else:
            path = f"/api/v1/control/otp-logs?page={page}&perPage={per_page}"
        data = self._http.do_jwt("GET", path, None, token)
        # Handle both flat array and paginated { data: [], meta: {} } shapes
        if isinstance(data, list):
            return data
        return data.get("data", data) if isinstance(data, dict) else []
