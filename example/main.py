# example/main.py
from payfake import Client, PayfakeError
from payfake.types import (
    ChargeCardInput,
    ChargeMomoInput,
    ForceTransactionInput,
    InitializeInput,
    ListOptions,
    LoginInput,
    RegisterInput,
    UpdateScenarioInput,
)


def main():

    # STEP 1: Create auth client (no secret key needed)

    auth_client = Client(
        secret_key="",  # Not required for auth endpoints
        base_url="http://localhost:8080",
    )

    # STEP 2: Register or Login to get auth token

    try:
        reg = auth_client.auth.register(
            RegisterInput(
                business_name="Acme Store",
                email="dev@acme.com",
                password="secret123",
            )
        )
        print(f"Registered: {reg.merchant.id}")
        token = reg.token
    except PayfakeError as e:
        if e.is_code(PayfakeError.CODE_EMAIL_TAKEN):
            login = auth_client.auth.login(
                LoginInput(
                    email="dev@acme.com",
                    password="secret123",
                )
            )
            token = login.token
            print(f"Logged in as: {login.merchant.email}")
        else:
            raise

    # STEP 3: Get actual API keys using auth token

    keys = auth_client.auth.get_keys(token)
    print("\nAPI Keys retrieved:")
    print(f"Public Key: {keys.public_key}")
    print(f"Secret Key: {keys.secret_key}")

    # STEP 4: Create authenticated client with real secret key

    client = Client(
        secret_key=keys.secret_key,
        base_url="http://localhost:8080",
    )

    # STEP 5: Initialize a transaction

    tx = client.transaction.initialize(
        InitializeInput(
            email="customer@example.com",
            amount=10000,  # GHS 100.00
            currency="GHS",
        )
    )
    print(f"\nTransaction initialized")
    print(f"Reference:         {tx.reference}")
    print(f"Access code:       {tx.access_code}")
    print(f"Authorization URL: {tx.authorization_url}")

    # STEP 6: Charge a card

    #  Full local card flow
    from payfake.types import SubmitOTPInput, SubmitPINInput

    tx = client.transaction.initialize(
        InitializeInput(
            email="customer@example.com",
            amount=10000,
            currency="GHS",
        )
    )
    print(f"Reference: {tx.reference}")

    # Step 1 — initiate card charge (local Verve card)
    step1 = client.charge.card(
        ChargeCardInput(
            access_code=tx.access_code,
            card_number="5061000000000000",
            card_expiry="12/26",
            cvv="123",
            email="customer@example.com",
        )
    )
    print(f"Step 1 status: {step1.status}")  # send_pin

    # Step 2 — submit PIN
    step2 = client.charge.submit_pin(
        SubmitPINInput(
            reference=tx.reference,
            pin="1234",
        )
    )
    print(f"Step 2 status: {step2.status}")  # send_otp

    # Step 3 — get OTP from logs
    otp_logs = client.control.get_otp_logs(token, reference=tx.reference)
    otp_code = otp_logs[0].otp_code
    print(f"OTP: {otp_code}")

    # Step 4 — submit OTP
    step3 = client.charge.submit_otp(
        SubmitOTPInput(
            reference=tx.reference,
            otp=otp_code,
        )
    )
    print(f"Step 3 status: {step3.status}")  # success

    verified = client.transaction.verify(tx.reference)
    print(f"Verified: {verified.status}")

    # STEP 7: Verify transaction

    verified = client.transaction.verify(tx.reference)
    print(f"Verified status: {verified.status}")

    # STEP 8: Mobile Money flow

    tx2 = client.transaction.initialize(
        InitializeInput(
            email="momo@example.com",
            amount=5000,
        )
    )
    momo = client.charge.mobile_money(
        ChargeMomoInput(
            access_code=tx2.access_code,
            phone="+233241234567",
            provider="mtn",
            email="momo@example.com",
        )
    )
    print(f"\nMoMo charge status: {momo.transaction.status}")

    # STEP 9: Control panel operations (using auth token, not secret key)

    scenario = auth_client.control.update_scenario(
        token,
        UpdateScenarioInput(
            failure_rate=0.5,
            delay_ms=1000,
        ),
    )
    print(f"\nScenario updated - failure rate: {scenario.failure_rate}")

    # Force a specific transaction to fail
    tx3 = client.transaction.initialize(
        InitializeInput(
            email="force@example.com",
            amount=2000,
        )
    )
    forced = auth_client.control.force_transaction(
        token,
        tx3.reference,
        ForceTransactionInput(
            status="failed",
            error_code="CHARGE_INSUFFICIENT_FUNDS",
        ),
    )
    print(f"Forced transaction status: {forced.status}")

    # Reset scenario
    auth_client.control.reset_scenario(token)
    print("Scenario reset")

    # STEP 10: Get recent logs

    try:
        logs = auth_client.control.get_logs(token, ListOptions(page=1, per_page=5))
        print(f"\nRecent requests: {len(logs)}")
        for log in logs:
            print(f"  {log.method} {log.path} -> {log.status_code}")
    except PayfakeError as e:
        if e.is_code("LOGS_EMPTY"):
            print("\nNo logs found yet (expected for new merchant)")
        else:
            raise


if __name__ == "__main__":
    main()
