from dataclasses import dataclass
import uuid


@dataclass
class OpsToolResult:
    success: bool
    message: str
    tool_call_id: str = ""


class OpsTools:
    def escalate_to_human(self, payment_id: str, reason: str) -> OpsToolResult:
        return OpsToolResult(
            success=True,
            message=f"{payment_id} escalated for human review: {reason}",
            tool_call_id=str(uuid.uuid4()),
        )

    def stop_recovery(self, payment_id: str, reason: str) -> OpsToolResult:
        return OpsToolResult(
            success=True,
            message=f"Recovery stopped for {payment_id}: {reason}",
            tool_call_id=str(uuid.uuid4()),
        )
