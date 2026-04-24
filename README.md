# payfake

Official Python SDK for [Payfake](https://payfake.co) — a Paystack-compatible payment
simulator for African developers.

```bash
pip install payfake
```

---

## Quick Start

```python
from payfake import Client

client = Client(secret_key="sk_test_xxx")

# Self-hosted:
client = Client(secret_key="sk_test_xxx", base_url="http://localhost:8080")
```

Change one env var to switch to real Paystack:

```bash
# Development
PAYSTACK_BASE_URL=https://api.payfake.co
PAYSTACK_SECRET_KEY=sk_test_xxx

# Production
PAYSTACK_BASE_URL=https://api.paystack.co
PAYSTACK_SECRET_KEY=sk_live_xxx
```

---

## Full Card Flow

```python
# Initialize
tx = client.transaction.initialize(
    email="customer@example.com",
    amount=10000,  # GHS 100.00 — amounts in pesewas
    currency="GHS",
)

# Charge — local Verve card
step1 = client.charge.card(
    email="customer@example.com",
    access_code=tx["access_code"],
    card={
        "number":       "5061000000000000",
        "cvv":          "123",
        "expiry_month": "12",
        "expiry_year":  "2026",
    },
)
# step1["status"] == "send_pin"

# Submit PIN
step2 = client.charge.submit_pin(reference=tx["reference"], pin="1234")
# step2["status"] == "send_otp"

# Get OTP from logs (no real phone needed)
logs = client.control.get_otp_logs(token, reference=tx["reference"])
otp  = logs[0]["otp_code"]

# Submit OTP
step3 = client.charge.submit_otp(reference=tx["reference"], otp=otp)
# step3["status"] == "success"

# Verify
verified = client.transaction.verify(tx["reference"])
# verified["status"] == "success"
# verified["gateway_response"] == "Approved"
```

---

## Charge Flow Status Reference

| Status | Meaning | Next Call |
|--------|---------|-----------|
| `send_pin` | Enter card PIN | `charge.submit_pin` |
| `send_otp` | Enter OTP | `charge.submit_otp` |
| `send_birthday` | Enter date of birth | `charge.submit_birthday` |
| `send_address` | Enter billing address | `charge.submit_address` |
| `open_url` | Complete 3DS — open `url` field | Navigate checkout to `url` |
| `pay_offline` | Approve USSD prompt | Poll `transaction.public_verify` |
| `success` | Payment complete | Call `transaction.verify` |
| `failed` | Payment declined | Read `gateway_response` |

---

## Mobile Money

```python
step1 = client.charge.mobile_money(
    email="customer@example.com",
    access_code=tx["access_code"],
    mobile_money={"phone": "+233241234567", "provider": "mtn"},
)
# step1["status"] == "send_otp"

logs  = client.control.get_otp_logs(token, reference=tx["reference"])
step2 = client.charge.submit_otp(reference=tx["reference"], otp=logs[0]["otp_code"])
# step2["status"] == "pay_offline"

# Poll every 3 seconds
import time
while True:
    result = client.transaction.public_verify(tx["reference"])
    if result["status"] in ("success", "failed"):
        break
    time.sleep(3)
```

---

## Scenario Testing

```python
# Login to get JWT
resp  = client.auth.login(email="dev@acme.com", password="secret123")
token = resp["access_token"]

# Force failure
client.control.update_scenario(
    token,
    force_status="failed",
    error_code="CHARGE_INSUFFICIENT_FUNDS",
)

# Reset
client.control.reset_scenario(token)
```

---

## Error Handling

```python
from payfake import Client, PayfakeError

try:
    client.charge.submit_otp(reference=ref, otp="000000")
except PayfakeError as e:
    if e.is_code(PayfakeError.CODE_INVALID_OTP):
        client.charge.resend_otp(reference=ref)
    else:
        print(e.code, e.message, e.http_status)
        for f in e.fields:
            print(f.field, f.rule, f.message)
```

---

## Context Manager

```python
with Client(secret_key="sk_test_xxx") as client:
    tx = client.transaction.initialize(email="...", amount=10000)
```

---

## License

MIT
