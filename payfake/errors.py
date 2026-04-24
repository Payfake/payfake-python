from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ErrorField:
    """A single field-level validation error."""

    field: str
    rule: str
    message: str


class PayfakeError(Exception):
    """
    Raised by every SDK method on failure.
    Use is_code() for programmatic error handling — never parse message.

    Example::

        try:
            client.charge.submit_otp(reference=ref, otp="000000")
        except PayfakeError as e:
            if e.is_code(PayfakeError.CODE_INVALID_OTP):
                client.charge.resend_otp(reference=ref)
    """

    def __init__(
        self,
        code: str,
        message: str,
        fields: list[ErrorField] | None = None,
        http_status: int = 0,
    ) -> None:
        super().__init__(message)
        #: X-Payfake-Code header value — use this for programmatic handling.
        self.code: str = code
        #: Human-readable error message — log this, don't parse it.
        self.message: str = message
        #: Field-level validation errors (populated when code is VALIDATION_ERROR).
        self.fields: list[ErrorField] = fields or []
        #: HTTP status code of the failed response.
        self.http_status: int = http_status

    def is_code(self, code: str) -> bool:
        """Return True if this error has the given Payfake code."""
        return self.code == code

    def __str__(self) -> str:
        if self.fields:
            parts = ", ".join(f"{f.field}: {f.message}" for f in self.fields)
            return f"PayfakeError [{self.code}] {self.message} — {parts}"
        return f"PayfakeError [{self.code}] {self.message}"

    # Response code constants

    # Auth
    CODE_EMAIL_TAKEN = "AUTH_EMAIL_TAKEN"
    CODE_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    CODE_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    CODE_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    CODE_TOKEN_INVALID = "AUTH_TOKEN_INVALID"

    # Transaction
    CODE_TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    CODE_REFERENCE_TAKEN = "TRANSACTION_REFERENCE_TAKEN"
    CODE_INVALID_AMOUNT = "TRANSACTION_INVALID_AMOUNT"
    CODE_ALREADY_VERIFIED = "TRANSACTION_ALREADY_VERIFIED"

    # Charge
    CODE_CHARGE_FAILED = "CHARGE_FAILED"
    CODE_CHARGE_SUCCESSFUL = "CHARGE_SUCCESSFUL"
    CODE_SEND_PIN = "CHARGE_SEND_PIN"
    CODE_SEND_OTP = "CHARGE_SEND_OTP"
    CODE_SEND_BIRTHDAY = "CHARGE_SEND_BIRTHDAY"
    CODE_SEND_ADDRESS = "CHARGE_SEND_ADDRESS"
    CODE_OPEN_URL = "CHARGE_OPEN_URL"
    CODE_PAY_OFFLINE = "CHARGE_PAY_OFFLINE"
    CODE_INVALID_OTP = "CHARGE_INVALID_OTP"
    CODE_INSUFFICIENT_FUNDS = "CHARGE_INSUFFICIENT_FUNDS"
    CODE_DO_NOT_HONOR = "CHARGE_DO_NOT_HONOR"
    CODE_MOMO_TIMEOUT = "CHARGE_MOMO_TIMEOUT"
    CODE_MOMO_PROVIDER_UNAVAILABLE = "CHARGE_MOMO_PROVIDER_UNAVAILABLE"

    # Customer
    CODE_CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    CODE_CUSTOMER_EMAIL_TAKEN = "CUSTOMER_EMAIL_TAKEN"

    # Generic
    CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
    CODE_INTERNAL_ERROR = "INTERNAL_ERROR"
    CODE_NOT_FOUND = "NOT_FOUND"
    CODE_RATE_LIMITED = "RATE_LIMIT_EXCEEDED"
