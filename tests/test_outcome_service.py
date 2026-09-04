from backend.services.outcome_service import OutcomeService


def test_outcome_is_reproducible():
    service = OutcomeService()

    a = service.verify("PAY123", 18000, "retry", 0.85)
    b = service.verify("PAY123", 18000, "retry", 0.85)

    assert a.status == b.status
    assert a.amount_recovered == b.amount_recovered


def test_stop_cannot_recover_money():
    service = OutcomeService()

    result = service.verify("PAY123", 18000, "stop", 0.95)

    assert result.status == "failed"
    assert result.amount_recovered == 0
