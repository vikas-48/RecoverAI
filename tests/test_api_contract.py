def test_allowed_actions_are_stable():
    from backend.models.schemas import Action
    assert {x.value for x in Action} == {
        "retry",
        "schedule_retry",
        "send_payment_link",
        "escalate",
        "stop",
    }
