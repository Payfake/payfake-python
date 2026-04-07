# payfake-python

Official Python SDK for [Payfake API](https://github.com/payfake/payfake-api) — a self-hostable African payment simulator that mirrors the Paystack API exactly. Test every payment scenario without touching real money.

## Installation

```bash
pip install payfake
```

Or from source:

```bash
git clone https://github.com/payfake/payfake-python
cd payfake-python
pip install -e .
```

## Quick Start

```python
from payfake import Client
from payfake.types import InitializeInput, ChargeCardInput
from payfake.errors import PayfakeError

client = Client(
    secret_key="sk_test_xxx",
    base_url="http://localhost:8080",  # your Payfake server
)

# Initialize a transaction
tx = client.transaction.initialize(InitializeInput(
    email="customer@example.com",
    amount=10000,  # GHS 100.00 — amounts in smallest unit (pesewas)
    currency="GHS",
))

print("Access code:", tx.access_code)
print("Auth URL:", tx.authorization_url)

# Charge a card
try:
    charge = client.charge.card(ChargeCardInput(
        access_code=tx.access_code,
        card_number="4111111111111111",
        card_expiry="12/26",
        cvv="123",
        email="customer@example.com",
    ))
    print("Status:", charge.transaction.status)
except PayfakeError as e:
    if e.is_code(PayfakeError.CODE_CHARGE_FAILED):
        print("Charge failed:", e.code)
    else:
        raise

# Verify the transaction
verified = client.transaction.verify(tx.reference)
print("Verified:", verified.status)
```

## Namespaces

| Namespace | Access | Description |
|-----------|--------|-------------|
| `client.auth` | Public + JWT | Register, login, key management |
| `client.transaction` | Secret key | Initialize, verify, list, refund |
| `client.charge` | Secret key | Card, mobile money, bank transfer |
| `client.customer` | Secret key | Create, list, fetch, update |
| `client.control` | JWT | Scenarios, webhooks, logs, force outcomes |

## Error Handling

Every failed API call raises `PayfakeError`. Use `is_code()` for programmatic handling:

```python
from payfake.errors import PayfakeError

try:
    client.transaction.initialize(input)
except PayfakeError as e:
    if e.is_code(PayfakeError.CODE_REFERENCE_TAKEN):
        # duplicate reference, verify the existing transaction instead
        pass
    elif e.is_code(PayfakeError.CODE_INVALID_AMOUNT):
        # amount is zero or negative
        pass
    else:
        raise
```

Available error code constants:

```python
PayfakeError.CODE_EMAIL_TAKEN
PayfakeError.CODE_INVALID_CREDENTIALS
PayfakeError.CODE_UNAUTHORIZED
PayfakeError.CODE_TOKEN_EXPIRED
PayfakeError.CODE_TRANSACTION_NOT_FOUND
PayfakeError.CODE_REFERENCE_TAKEN
PayfakeError.CODE_INVALID_AMOUNT
PayfakeError.CODE_CHARGE_FAILED
PayfakeError.CODE_CHARGE_PENDING
PayfakeError.CODE_CUSTOMER_NOT_FOUND
PayfakeError.CODE_CUSTOMER_EMAIL_TAKEN
PayfakeError.CODE_VALIDATION_ERROR
PayfakeError.CODE_INTERNAL_ERROR
```

## Scenario Control

```python
from payfake.types import UpdateScenarioInput, ForceTransactionInput

# Login first to get a JWT
login = client.auth.login(LoginInput(email="dev@acme.com", password="secret123"))
token = login.token

# 30% failure rate with 1 second delay
client.control.update_scenario(token, UpdateScenarioInput(
    failure_rate=0.3,
    delay_ms=1000,
))

# Force a specific transaction to fail
client.control.force_transaction(token, reference, ForceTransactionInput(
    status="failed",
    error_code="CHARGE_INSUFFICIENT_FUNDS",
))

# Reset everything back to defaults
client.control.reset_scenario(token)
```

## Mobile Money

MoMo charges are async, always return `pending` immediately.
The final outcome arrives via webhook after the simulated delay:

```python
charge = client.charge.mobile_money(ChargeMomoInput(
    access_code=tx.access_code,
    phone="+233241234567",
    provider="mtn",  # mtn | vodafone | airteltigo
    email="customer@example.com",
))

# charge.transaction.status is always "pending" here
# implement a webhook handler for the final outcome
```

## Context Manager

The client supports the context manager protocol for automatic cleanup:

```python
with Client(secret_key="sk_test_xxx") as client:
    tx = client.transaction.initialize(...)
# HTTP connections are released automatically here
```

## Requirements

- Python 3.10+
- httpx
- A running [Payfake API](https://github.com/payfake/payfake-api) server

## License

MIT
