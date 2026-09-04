from backend.services.recovery_service import RecoveryService


def test_external_payment_reconciliation_records_real_recovery():
    service = RecoveryService()
    result = service.reconcile_external_payment(
        payment_id="PAY200005",
        razorpay_payment_id="pay_test_123",
        amount_rupees=500.0,
        payment_link_id="plink_test_123",
    )

    assert result["status"] == "reconciled"
    assert result["amount_recovered"] == 500.0
    assert any(e["event_type"] == "RAZORPAY_PAYMENT_CONFIRMED" for e in service.audit.events)
    assert any(
        e["event_type"] == "OUTCOME_VERIFIED"
        and e["payload"]["source"] == "razorpay_webhook"
        for e in service.audit.events
    )


class FakeRazorpayAdapter:
    enabled = True

    def create_recovery_link(self, payment_id, amount_rupees, description):
        from backend.tools.razorpay_tools import RazorpayResult
        return RazorpayResult(True, "Recovery payment link created.", {
            "id": "plink_demo_123",
            "short_url": "https://rzp.io/i/demo123",
        })


def test_external_payment_link_waits_for_webhook():
    from backend.services.recovery_service import RecoveryService
    from backend.tools.payment_tools import PaymentTools
    from backend.models.schemas import RecoveryCase

    service = RecoveryService()
    service.payment_tools.razorpay = FakeRazorpayAdapter()
    case = RecoveryCase(
        payment_id="PAY200018", customer_id="C101107", amount=4693.53,
        failure_reason="expired_card", attempt_number=1, payment_method="card",
        customer_lifetime_value=10000, customer_total_payments=10,
        customer_success_rate=0.9, customer_failure_rate=0.1,
        average_payment=1000, days_since_last_success=2,
        recovery_probability=0.466,
    )
    result = service.recover(case)
    assert result.final_action.value == "send_payment_link"
    assert result.outcome_status == "pending"
    assert result.success is False
    assert result.external_payment_link_url == "https://rzp.io/i/demo123"
