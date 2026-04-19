from __future__ import annotations

from typing import TYPE_CHECKING

from .types import (
    ChargeBankInput,
    ChargeCardInput,
    ChargeData,
    ChargeFlowResponse,
    ChargeMomoInput,
    ResendOTPInput,
    SubmitAddressInput,
    SubmitBirthdayInput,
    SubmitOTPInput,
    SubmitPINInput,
    Transaction,
)

if TYPE_CHECKING:
    from .client import Client


def _parse_flow_response(data: dict) -> ChargeFlowResponse:
    """
    Deserialize a charge flow response dict.
    All charge step endpoints return this same shape so we parse once.
    """
    from .transaction import _parse_transaction

    tx_data = dict(data.get("transaction") or {})
    charge_data = data.get("charge") or {}

    tx = (
        _parse_transaction(tx_data)
        if tx_data
        else Transaction(
            id="",
            reference="",
            amount=0,
            currency="GHS",
            status="",
            channel="",
            fees=0,
            access_code="",
            callback_url="",
            created_at="",
        )
    )

    charge = (
        ChargeData(
            **{
                k: v
                for k, v in charge_data.items()
                if k in ChargeData.__dataclass_fields__
            }
        )
        if charge_data
        else ChargeData()
    )

    return ChargeFlowResponse(
        status=data.get("status", ""),
        reference=data.get("reference", ""),
        display_text=data.get("display_text", ""),
        three_ds_url=data.get("three_ds_url", ""),
        transaction=tx,
        charge=charge,
    )


class ChargeNamespace:
    def __init__(self, client: "Client") -> None:
        self._client = client

    def card(self, input: ChargeCardInput) -> ChargeFlowResponse:
        """
        Initiate a card charge.
        Returns send_pin for local Verve cards (5061, 5062, 5063, 6500, 6501).
        Returns open_url for international Visa/Mastercard — use three_ds_url.
        """
        data = self._client._request("POST", "/api/v1/charge/card", body=input)
        return _parse_flow_response(data)

    def mobile_money(self, input: ChargeMomoInput) -> ChargeFlowResponse:
        """
        Initiate a mobile money charge.
        Always returns send_otp first — customer verifies phone with OTP.
        After OTP returns pay_offline — poll transaction for final outcome.
        """
        data = self._client._request("POST", "/api/v1/charge/mobile_money", body=input)
        return _parse_flow_response(data)

    def bank(self, input: ChargeBankInput) -> ChargeFlowResponse:
        """
        Initiate a bank transfer charge.
        Returns send_birthday — customer must enter date of birth first.
        """
        data = self._client._request("POST", "/api/v1/charge/bank", body=input)
        return _parse_flow_response(data)

    def submit_pin(self, input: SubmitPINInput) -> ChargeFlowResponse:
        """
        Submit card PIN after a send_pin response.
        Returns send_otp — OTP sent to registered phone.
        Read OTP from client.control.get_otp_logs(token, reference=input.reference).
        """
        data = self._client._request("POST", "/api/v1/charge/submit_pin", body=input)
        return _parse_flow_response(data)

    def submit_otp(self, input: SubmitOTPInput) -> ChargeFlowResponse:
        """
        Submit OTP after a send_otp response.
        Card/bank: returns success or failed.
        MoMo: returns pay_offline — poll transaction for final webhook outcome.
        """
        data = self._client._request("POST", "/api/v1/charge/submit_otp", body=input)
        return _parse_flow_response(data)

    def submit_birthday(self, input: SubmitBirthdayInput) -> ChargeFlowResponse:
        """
        Submit date of birth after a send_birthday response.
        Returns send_otp on success.
        """
        data = self._client._request(
            "POST", "/api/v1/charge/submit_birthday", body=input
        )
        return _parse_flow_response(data)

    def submit_address(self, input: SubmitAddressInput) -> ChargeFlowResponse:
        """
        Submit billing address after a send_address response.
        Returns success or failed.
        """
        data = self._client._request(
            "POST", "/api/v1/charge/submit_address", body=input
        )
        return _parse_flow_response(data)

    def resend_otp(self, input: ResendOTPInput) -> ChargeFlowResponse:
        """
        Request a new OTP when the customer hasn't received one.
        Invalidates the previous OTP. Returns send_otp with fresh OTP.
        Read new OTP from client.control.get_otp_logs(token, reference=input.reference).
        """
        data = self._client._request("POST", "/api/v1/charge/resend_otp", body=input)
        return _parse_flow_response(data)

    def simulate_3ds(self, reference: str) -> ChargeFlowResponse:
        """
        Complete the simulated 3DS verification.
        Called after customer confirms on the checkout app's 3DS page.
        Returns success or failed based on scenario config.
        """
        data = self._client._request("POST", f"/api/v1/public/simulate/3ds/{reference}")
        return _parse_flow_response(data)

    def fetch(self, reference: str) -> ChargeData:
        """Fetch the current state of a charge by transaction reference."""
        data = self._client._request("GET", f"/api/v1/charge/{reference}")
        return ChargeData(
            **{k: v for k, v in data.items() if k in ChargeData.__dataclass_fields__}
        )
