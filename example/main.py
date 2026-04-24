import time

from payfake import Client, PayfakeError

client = Client(
    secret_key="sk_test_your_key_here",
    base_url="http://localhost:8080",
)

#  Register
try:
    resp = client.auth.register(
        business_name="Acme Store",
        email="dev@acme.com",
        password="secret123",
    )
    token = resp["access_token"]
    print("Registered:", resp["merchant"]["id"])
except PayfakeError as e:
    if e.is_code(PayfakeError.CODE_EMAIL_TAKEN):
        print("Email taken — logging in")
        resp = client.auth.login(email="dev@acme.com", password="secret123")
        token = resp["access_token"]
    else:
        raise

#  Get keys
keys = client.auth.get_keys(token)
print("Secret key:", keys["secret_key"][:20] + "...")

authed = Client(secret_key=keys["secret_key"], base_url="http://localhost:8080")

#  Initialize
tx = authed.transaction.initialize(
    email="customer@example.com",
    amount=10000,
    currency="GHS",
)
print("\nReference:        ", tx["reference"])
print("Authorization URL:", tx["authorization_url"])

#  Full local Verve card flow
print("\n── Card flow (local Verve) ──")

step1 = authed.charge.card(
    email="customer@example.com",
    reference=tx["reference"],
    card={
        "number": "5061000000000000",
        "cvv": "123",
        "expiry_month": "12",
        "expiry_year": "2026",
    },
)
print("Step 1:", step1["status"])  # send_pin

step2 = authed.charge.submit_pin(reference=tx["reference"], pin="1234")
print("Step 2:", step2["status"])  # send_otp

otp_logs = authed.control.get_otp_logs(token, reference=tx["reference"])
otp = otp_logs[0]["otp_code"]
print("OTP:   ", otp)

step3 = authed.charge.submit_otp(reference=tx["reference"], otp=otp)
print("Step 3:", step3["status"])  # success

#  Verify
verified = authed.transaction.verify(tx["reference"])
print("\nVerified:         ", verified["status"])
print("Gateway response: ", verified["gateway_response"])
print("Auth code:        ", verified.get("authorization", {}).get("authorization_code"))

#  MoMo flow
print("\n── MoMo flow ──")

tx2 = authed.transaction.initialize(email="momo@example.com", amount=5000)
momo1 = authed.charge.mobile_money(
    email="momo@example.com",
    reference=tx2["reference"],
    mobile_money={"phone": "+233241234567", "provider": "mtn"},
)
print("MoMo step 1:", momo1["status"])  # send_otp

momo_logs = authed.control.get_otp_logs(token, reference=tx2["reference"])
momo2 = authed.charge.submit_otp(
    reference=tx2["reference"],
    otp=momo_logs[0]["otp_code"],
)
print("MoMo step 2:", momo2["status"])  # pay_offline

print("Polling for resolution...")
for i in range(10):
    result = authed.transaction.public_verify(tx2["reference"], tx2["access_code"])
    flow = (result.get("charge") or {}).get("flow_status", "–")
    print(f"  poll {i + 1}: status={result['status']} flow={flow}")
    if result["status"] in ("success", "failed"):
        print("Resolved:", result["status"])
        break
    time.sleep(1)

#  Scenario testing
print("\n── Scenario testing ──")

authed.control.update_scenario(
    token,
    force_status="failed",
    error_code="CHARGE_INSUFFICIENT_FUNDS",
)
print("Scenario: force insufficient funds")

tx3 = authed.transaction.initialize(email="fail@example.com", amount=10000)
try:
    authed.charge.card(
        email="fail@example.com",
        reference=tx3["reference"],
        card={
            "number": "5061000000000000",
            "cvv": "123",
            "expiry_month": "12",
            "expiry_year": "2026",
        },
    )
except PayfakeError as e:
    print("Charge failed as expected:", e.code)
    if e.is_code(PayfakeError.CODE_INSUFFICIENT_FUNDS):
        print("Correctly identified as insufficient funds")

authed.control.reset_scenario(token)
print("Scenario reset")

stats = authed.control.get_stats(token)
txs = stats.get("transactions", {})
print(
    f"\nStats: total={txs.get('total')} success_rate={txs.get('success_rate', 0):.1f}%"
)
