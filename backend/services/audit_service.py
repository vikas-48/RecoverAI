from datetime import datetime, timezone
import json
import uuid


class AuditService:
    def __init__(self):
        self.events = []

    def record(self, event_type: str, payment_id: str, payload: dict) -> str:
        event_id = str(uuid.uuid4())
        self.events.append({
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payment_id": payment_id,
            "payload": payload,
        })
        return event_id
