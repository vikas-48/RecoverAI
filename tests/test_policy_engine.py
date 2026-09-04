from backend.models.schemas import Action, AgentDecision, RecoveryCase
from backend.policies.policy_engine import PolicyEngine


def case(amount=18000, attempts=1, probability=0.85, reason="network_error"):
    return RecoveryCase(
        payment_id="PAY_TEST",
        customer_id="C_TEST",
        amount=amount,
        failure_reason=reason,
        attempt_number=attempts,
        payment_method="card",
        customer_lifetime_value=100000,
        customer_total_payments=20,
        customer_success_rate=0.95,
        customer_failure_rate=0.05,
        average_payment=10000,
        days_since_last_success=10,
        recovery_probability=probability,
    )


def test_high_value_requires_human():
    result = PolicyEngine().evaluate(
        case(amount=80000),
        AgentDecision(
            action=Action.RETRY,
            reason="retry",
            confidence=0.9,
        ),
    )
    assert result.final_action == Action.ESCALATE
    assert result.requires_human is True


def test_attempt_limit_stops():
    result = PolicyEngine().evaluate(
        case(attempts=3),
        AgentDecision(
            action=Action.RETRY,
            reason="retry",
            confidence=0.9,
        ),
    )
    assert result.final_action == Action.STOP


def test_invalid_card_cannot_be_blindly_retried():
    result = PolicyEngine().evaluate(
        case(reason="expired_card"),
        AgentDecision(
            action=Action.RETRY,
            reason="retry",
            confidence=0.9,
        ),
    )
    assert result.final_action == Action.SEND_PAYMENT_LINK
