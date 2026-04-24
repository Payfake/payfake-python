from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPClient


class ChargeNamespace:
    """
    Wraps /charge endpoints.
    Matches https://api.paystack.co/charge exactly.
    All methods call POST /charge, channel detected from body object.
    Auth: Bearer sk_test_xxx
    """

    def __init__(self, http: "_HTTPClient") -> None:
        self._http = http

    def card(
        self,
        *,
        email: str,
        card: dict,
        amount: int = 0,
        access_code: str = "",
        reference: str = "",
    ) -> dict:
        """
        Initiate a card charge via POST /charge.

        Local Ghana cards (Verve: 5061, 5062, 5063, 6500, 6501):
            returns status "send_pin" → call submit_pin

        International cards (Visa 4xxx, Mastercard 5xxx):
            returns status "open_url" + url → checkout navigates to url

        card dict: { "number": str, "cvv": str, "expiry_month": str, "expiry_year": str }
        """
        body: dict = {"email": email, "card": card}
        if amount:
            body["amount"] = amount
        if access_code:
            body["access_code"] = access_code
        if reference:
            body["reference"] = reference
        return self._http.do("POST", "/charge", body)

    def mobile_money(
        self,
        *,
        email: str,
        mobile_money: dict,
        amount: int = 0,
        access_code: str = "",
        reference: str = "",
    ) -> dict:
        """
        Initiate a MoMo charge via POST /charge.
        Returns status "send_otp" → call submit_otp.
        After OTP returns "pay_offline" → poll transaction.public_verify.

        mobile_money dict: { "phone": str, "provider": "mtn"|"vodafone"|"airteltigo" }
        """
        body: dict = {"email": email, "mobile_money": mobile_money}
        if amount:
            body["amount"] = amount
        if access_code:
            body["access_code"] = access_code
        if reference:
            body["reference"] = reference
        return self._http.do("POST", "/charge", body)

    def bank(
        self,
        *,
        email: str,
        bank: dict,
        amount: int = 0,
        access_code: str = "",
        reference: str = "",
        birthday: str = "",
    ) -> dict:
        """
        Initiate a bank transfer charge via POST /charge.
        Returns status "send_birthday" → call submit_birthday.

        bank dict: { "code": str, "account_number": str }
        """
        body: dict = {"email": email, "bank": bank}
        if amount:
            body["amount"] = amount
        if access_code:
            body["access_code"] = access_code
        if reference:
            body["reference"] = reference
        if birthday:
            body["birthday"] = birthday
        return self._http.do("POST", "/charge", body)

    def submit_pin(self, *, reference: str, pin: str) -> dict:
        """
        Submit card PIN after status "send_pin".
        Returns status "send_otp", OTP sent to registered phone.
        Read OTP from client.control.get_otp_logs() during testing.
        """
        return self._http.do(
            "POST", "/charge/submit_pin", {"reference": reference, "pin": pin}
        )

    def submit_otp(self, *, reference: str, otp: str) -> dict:
        """
        Submit OTP after status "send_otp".
        Card/bank: returns "success" or "failed".
        MoMo: returns "pay_offline", poll transaction.public_verify.
        """
        return self._http.do(
            "POST", "/charge/submit_otp", {"reference": reference, "otp": otp}
        )

    def submit_birthday(self, *, reference: str, birthday: str) -> dict:
        """
        Submit date of birth after status "send_birthday".
        Returns status "send_otp" on success.
        birthday format: YYYY-MM-DD
        """
        return self._http.do(
            "POST",
            "/charge/submit_birthday",
            {
                "reference": reference,
                "birthday": birthday,
            },
        )

    def submit_address(
        self,
        *,
        reference: str,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        country: str,
    ) -> dict:
        """Submit billing address after status "send_address". Returns success or failed."""
        return self._http.do(
            "POST",
            "/charge/submit_address",
            {
                "reference": reference,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "country": country,
            },
        )

    def resend_otp(self, *, reference: str) -> dict:
        """
        Request a fresh OTP when the customer hasn't received one.
        Invalidates the previous OTP. Returns status "send_otp".
        Read the new OTP from client.control.get_otp_logs().
        """
        return self._http.do("POST", "/charge/resend_otp", {"reference": reference})

    def fetch(self, reference: str) -> dict:
        """Fetch the current state of a charge by transaction reference."""
        return self._http.do("GET", f"/charge/{reference}")

    def simulate_3ds(self, reference: str) -> dict:
        """
        Complete the simulated 3DS verification.
        Called by the checkout app after the customer confirms on the 3DS page.
        Returns "success" or "failed" based on the scenario config.
        """
        return self._http.do_public("POST", f"/api/v1/public/simulate/3ds/{reference}")
