from __future__ import annotations

from typing import TYPE_CHECKING

from .transaction import _parse_transaction
from .types import (
    ChargeBankInput,
    ChargeCardInput,
    ChargeData,
    ChargeMomoInput,
    ChargeResponse,
)

if TYPE_CHECKING:
    from .client import Client


def _parse_charge_response(data: dict) -> ChargeResponse:
    """
    Deserialize a raw charge response into a ChargeResponse dataclass.
    Handles the nested transaction and charge objects.
    """
    tx = _parse_transaction(dict(data.get("transaction", {})))
    charge_data = data.get("charge", {}) or {}
    charge = ChargeData(
        **{k: v for k, v in charge_data.items() if k in ChargeData.__dataclass_fields__}
    )
    return ChargeResponse(transaction=tx, charge=charge)


class ChargeNamespace:
    def __init__(self, client: "Client") -> None:
        self._client = client

    def card(self, input: ChargeCardInput) -> ChargeResponse:
        """
        Charge a card directly.
        Provide either access_code (popup flow) or reference (direct API flow).
        The charge outcome is determined by the merchant's scenario config.
        """
        data = self._client._request("POST", "/api/v1/charge/card", body=input)
        return _parse_charge_response(data)

    def mobile_money(self, input: ChargeMomoInput) -> ChargeResponse:
        """
        Initiate a mobile money charge.
        Always returns immediately with status "pending".
        The final outcome (success or failed) arrives via webhook
        after the simulated approval window (delay_ms in scenario config).
        Implement a webhook handler, don't poll for the result.
        """
        data = self._client._request("POST", "/api/v1/charge/mobile_money", body=input)
        return _parse_charge_response(data)

    def bank(self, input: ChargeBankInput) -> ChargeResponse:
        """Initiate a bank transfer charge."""
        data = self._client._request("POST", "/api/v1/charge/bank", body=input)
        return _parse_charge_response(data)

    def fetch(self, reference: str) -> ChargeData:
        """Fetch a charge by transaction reference."""
        data = self._client._request("GET", f"/api/v1/charge/{reference}")
        return ChargeData(
            **{k: v for k, v in data.items() if k in ChargeData.__dataclass_fields__}
        )
