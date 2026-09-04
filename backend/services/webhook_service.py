import os


class WebhookService:
    def __init__(self):
        self.secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        self.processed_event_ids = set()

    def is_duplicate(self, event_id: str) -> bool:
        return event_id in self.processed_event_ids

    def mark_processed(self, event_id: str):
        self.processed_event_ids.add(event_id)

    def handle(self, payload: dict, event_id: str | None = None) -> dict:
        event = payload.get("event")

        # Prefer the x-razorpay-event-id header supplied by Razorpay.
        event_id = event_id or payload.get("id") or payload.get("event_id")

        if event_id and self.is_duplicate(event_id):
            return {"status": "duplicate_ignored", "event_id": event_id}

        if event_id:
            self.mark_processed(event_id)

        payment_entity = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        return {
            "status": "accepted",
            "event_id": event_id,
            "event": event,
            "payment_id": payment_entity.get("id"),
            "payment_status": payment_entity.get("status"),
            "amount": payment_entity.get("amount"),
            "error_code": payment_entity.get("error_code"),
            "error_description": payment_entity.get("error_description"),
        }
