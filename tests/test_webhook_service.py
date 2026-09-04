from backend.services.webhook_service import WebhookService


def payload():
    return {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test",
                    "status": "failed",
                    "amount": 50000,
                }
            }
        },
    }


def test_webhook_event_is_idempotent():
    service = WebhookService()

    first = service.handle(payload(), event_id="evt_123")
    second = service.handle(payload(), event_id="evt_123")

    assert first["status"] == "accepted"
    assert second["status"] == "duplicate_ignored"
