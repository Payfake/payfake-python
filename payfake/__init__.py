"""
Payfake Python SDK


A Python SDK for the Payfake payment simulator, built for African developers
testing against Paystack-compatible payment flows without touching real money.

Basic usage::

    from payfake import Client
    from payfake.types import InitializeInput, ChargeCardInput
    from payfake.errors import PayfakeError

    client = Client(secret_key="sk_test_xxx")

    # Initialize a transaction
    tx = client.transaction.initialize(InitializeInput(
        email="customer@example.com",
        amount=10000,
        currency="GHS",
    ))

    # Charge a card
    charge = client.charge.card(ChargeCardInput(
        access_code=tx.access_code,
        card_number="4111111111111111",
        card_expiry="12/26",
        cvv="123",
        email="customer@example.com",
    ))

    print(charge.transaction.status)  # "success" or "failed"

Full documentation: https://github.com/payfake/payfake-python
"""

from .client import Client
from .errors import APIErrorField, PayfakeError
from .types import (
    ChargeBankInput,
    ChargeCardInput,
    ChargeMomoInput,
    CreateCustomerInput,
    ForceTransactionInput,
    InitializeInput,
    InitializeResponse,
    ListOptions,
    LoginInput,
    RegisterInput,
    ResendOTPInput,
    SubmitAddressInput,
    SubmitBirthdayInput,
    SubmitOTPInput,
    SubmitPINInput,
    UpdateCustomerInput,
    UpdateScenarioInput,
)

__version__ = "0.1.0"
__all__ = [
    "Client",
    "PayfakeError",
    "APIErrorField",
    "RegisterInput",
    "LoginInput",
    "InitializeInput",
    "InitializeResponse",
    "ChargeCardInput",
    "ChargeMomoInput",
    "ChargeBankInput",
    "CreateCustomerInput",
    "UpdateCustomerInput",
    "UpdateScenarioInput",
    "ForceTransactionInput",
    "ListOptions",
]
