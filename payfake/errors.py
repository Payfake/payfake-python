from __future__ import annotations

from dataclasses import dataclass


@dataclass
class APIErrorField:
    """A single field-level error returned by the Payfake API."""

    field: str
    message: str


class PayfakeError(Exception):
    """
    Base exception for all Payfake SDK errors.

    Every failed API call raises this, catch it to handle errors
    from any namespace without importing namespace-specific exceptions.

    Use the `code` attribute for programmatic error handling instead
    of parsing the message string, message text may change, codes won't.

    Example::

        try:
            client.transaction.initialize(input)
        except PayfakeError as e:
            if e.code == PayfakeError.CODE_REFERENCE_TAKEN:
                # handle duplicate reference
                pass
            raise
    """

    # Common error codes as class constants
    # so callers can do PayfakeError.CODE_EMAIL_TAKEN
    # instead of the raw string "AUTH_EMAIL_TAKEN".
    CODE_EMAIL_TAKEN = "AUTH_EMAIL_TAKEN"
    CODE_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    CODE_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    CODE_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    CODE_TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    CODE_REFERENCE_TAKEN = "TRANSACTION_REFERENCE_TAKEN"
    CODE_INVALID_AMOUNT = "TRANSACTION_INVALID_AMOUNT"
    CODE_CHARGE_FAILED = "CHARGE_FAILED"
    CODE_CHARGE_PENDING = "CHARGE_PENDING"
    CODE_CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    CODE_CUSTOMER_EMAIL_TAKEN = "CUSTOMER_EMAIL_TAKEN"
    CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
    CODE_INTERNAL_ERROR = "INTERNAL_ERROR"

    def __init__(
        self,
        code: str,
        message: str,
        fields: list[APIErrorField] | None = None,
        http_status: int = 0,
    ) -> None:
        self.code = code
        self.message = message
        # fields is a list of field-level errors, populated on
        # validation failures, empty for all other error types.
        self.fields: list[APIErrorField] = fields or []
        self.http_status = http_status
        super().__init__(self._format())

    def _format(self) -> str:
        if self.fields:
            field_messages = ", ".join(f"{f.field}: {f.message}" for f in self.fields)
            return f"payfake [{self.code}] {self.message} — {field_messages}"
        return f"payfake [{self.code}] {self.message}"

    def is_code(self, code: str) -> bool:
        """Check if this error matches a specific response code."""
        return self.code == code
