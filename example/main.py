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
    # Initialize the client, point it at your running Payfake server.
    client = Client(
        secret_key="sk_test_your_key_here",
        base_url="http://localhost:8080",
    )

    # Register a merchant
    try:
        reg = client.auth.register(
            RegisterInput(
                business_name="Acme Store",
                email="dev@acme.com",
                password="secret123",
            )
        )
        print(f"Registered: {reg.merchant.id}")
        print(f"Public key: {reg.merchant.public_key}")
        token = reg.token
    except PayfakeError as e:
        if e.is_code(PayfakeError.CODE_EMAIL_TAKEN):
            # Already registered, just login instead.
            login = client.auth.login(
                LoginInput(
                    email="dev@acme.com",
                    password="secret123",
                )
            )
            token = login.token
            print(f"Logged in as: {login.merchant.email}")
        else:
            raise

    #  Initialize a transaction
    tx = client.transaction.initialize(
        InitializeInput(
            email="customer@example.com",
            amount=10000,  # GHS 100.00 — amounts in smallest unit (pesewas)
            currency="GHS",
        )
    )
    print(f"\nTransaction initialized")
    print(f"Reference:         {tx.reference}")
    print(f"Access code:       {tx.access_code}")
    print(f"Authorization URL: {tx.authorization_url}")

    #  Charge a card
    try:
        charge = client.charge.card(
            ChargeCardInput(
                access_code=tx.access_code,
                card_number="4111111111111111",
                card_expiry="12/26",
                cvv="123",
                email="customer@example.com",
            )
        )
        print(f"\nCard charge status: {charge.transaction.status}")
    except PayfakeError as e:
        if e.is_code(PayfakeError.CODE_CHARGE_FAILED):
            print(
                f"\nCharge failed — error: {e.fields[0].message if e.fields else e.code}"
            )
        else:
            raise

    #  Verify the transaction
    verified = client.transaction.verify(tx.reference)
    print(f"Verified status: {verified.status}")

    #  Test MoMo flow
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
    # MoMo always returns pending immediately,
    # the real outcome arrives via webhook after the delay.
    print(f"\nMoMo charge status: {momo.transaction.status}")  # always "pending"

    # Control panel operations

    # Set 50% failure rate + 1 second delay
    scenario = client.control.update_scenario(
        token,
        UpdateScenarioInput(
            failure_rate=0.5,
            delay_ms=1000,
        ),
    )
    print(f"\nScenario updated — failure rate: {scenario.failure_rate}")

    # Force a specific transaction to fail
    tx3 = client.transaction.initialize(
        InitializeInput(
            email="force@example.com",
            amount=2000,
        )
    )
    forced = client.control.force_transaction(
        token,
        tx3.reference,
        ForceTransactionInput(
            status="failed",
            error_code="CHARGE_INSUFFICIENT_FUNDS",
        ),
    )
    print(f"Forced transaction status: {forced.status}")

    # Reset scenario back to defaults
    client.control.reset_scenario(token)
    print("Scenario reset, all charges will succeed again")

    # List recent logs
    logs = client.control.get_logs(token, ListOptions(page=1, per_page=5))
    print(f"\nRecent requests: {len(logs)}")
    for log in logs:
        print(f"  {log.method} {log.path} → {log.status_code}")


if __name__ == "__main__":
    main()
