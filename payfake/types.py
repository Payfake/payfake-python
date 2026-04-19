from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Auth


@dataclass
class RegisterInput:
    business_name: str
    email: str
    password: str


@dataclass
class LoginInput:
    email: str
    password: str


@dataclass
class MerchantData:
    id: str
    business_name: str
    email: str
    public_key: str


@dataclass
class RegisterResponse:
    merchant: MerchantData
    token: str


@dataclass
class LoginResponse:
    merchant: MerchantData
    token: str


@dataclass
class KeysResponse:
    public_key: str
    secret_key: str


# Transaction


@dataclass
class InitializeInput:
    email: str
    amount: int
    # currency defaults to GHS, most integrations won't need to set this
    currency: str = "GHS"
    reference: str = ""
    callback_url: str = ""
    channels: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InitializeResponse:
    authorization_url: str
    access_code: str
    reference: str


@dataclass
class CustomerSummary:
    """Minimal customer data embedded in transaction responses."""

    id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    customer_code: str = ""


@dataclass
class Transaction:
    id: str
    reference: str
    amount: int
    currency: str
    status: str
    channel: str
    fees: int
    access_code: str
    callback_url: str
    created_at: str
    customer: CustomerSummary = field(default_factory=CustomerSummary)
    paid_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaginationMeta:
    total: int
    page: int
    per_page: int
    pages: int


@dataclass
class TransactionList:
    transactions: list[Transaction]
    meta: PaginationMeta


# Charge


@dataclass
class ChargeCardInput:
    card_number: str
    card_expiry: str
    cvv: str
    email: str
    access_code: str = ""
    reference: str = ""


@dataclass
class ChargeMomoInput:
    phone: str
    # provider must be one of: mtn, vodafone, airteltigo
    provider: str
    email: str
    access_code: str = ""
    reference: str = ""


@dataclass
class ChargeBankInput:
    bank_code: str
    account_number: str
    email: str
    access_code: str = ""
    reference: str = ""


@dataclass
class ChargeData:
    id: str = ""
    channel: str = ""
    status: str = ""
    card_brand: str = ""
    card_last4: str = ""
    momo_phone: str = ""
    momo_provider: str = ""


@dataclass
class ChargeResponse:
    transaction: Transaction
    charge: ChargeData


# Customer


@dataclass
class CreateCustomerInput:
    email: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateCustomerInput:
    """
    All fields are optional — only non-None fields are sent to the API.
    This matches the PATCH semantics of the update endpoint.
    """

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class Customer:
    id: str
    email: str
    customer_code: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerList:
    customers: list[Customer]
    meta: PaginationMeta


# Control


@dataclass
class ScenarioConfig:
    id: str
    merchant_id: str
    failure_rate: float
    delay_ms: int
    force_status: str
    error_code: str


@dataclass
class UpdateScenarioInput:
    """
    All fields are optional, only non-None fields are sent.
    failure_rate must be between 0.0 and 1.0.
    delay_ms must be between 0 and 30000.
    force_status must be one of: success, failed, abandoned, or empty string to clear.
    """

    failure_rate: float | None = None
    delay_ms: int | None = None
    force_status: str | None = None
    error_code: str | None = None


@dataclass
class ForceTransactionInput:
    # status must be one of: success, failed, abandoned
    status: str
    error_code: str = ""


@dataclass
class WebhookEvent:
    id: str
    event: str
    transaction_id: str
    delivered: bool
    attempts: int
    created_at: str
    last_attempt_at: str | None = None


@dataclass
class WebhookAttempt:
    id: str
    status_code: int
    response_body: str
    succeeded: bool
    attempted_at: str


@dataclass
class RequestLog:
    id: str
    method: str
    path: str
    status_code: int
    request_body: str
    response_body: str
    duration_ms: int
    request_id: str
    logged_at: str


# Shared


@dataclass
class ListOptions:
    page: int = 1
    per_page: int = 50


#
# Charge flow v0.2.0
#


@dataclass
class SubmitPINInput:
    reference: str
    pin: str


@dataclass
class SubmitOTPInput:
    reference: str
    otp: str


@dataclass
class SubmitBirthdayInput:
    reference: str
    # format: YYYY-MM-DD
    birthday: str


@dataclass
class SubmitAddressInput:
    reference: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str


@dataclass
class ResendOTPInput:
    reference: str


@dataclass
class ChargeFlowResponse:
    """
    Returned by every charge step endpoint.
    Read status to decide what the checkout page renders next.

    status values:
        send_pin      → show PIN input
        send_otp      → show OTP input
        send_birthday → show date of birth input
        send_address  → show address form
        open_url      → navigate to three_ds_url
        pay_offline   → show approve on phone screen, poll transaction
        success       → show success screen
        failed        → show failure screen
    """

    status: str
    reference: str
    display_text: str = ""
    three_ds_url: str = ""
    transaction: Transaction = field(default_factory=Transaction)
    charge: ChargeData = field(default_factory=ChargeData)


@dataclass
class OTPLog:
    """A generated OTP stored for developer inspection during testing."""

    id: str
    merchant_id: str
    reference: str
    channel: str
    otp_code: str
    step: str
    used: bool
    expires_at: str
    created_at: str
