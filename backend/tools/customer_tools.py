from dataclasses import dataclass
import uuid


@dataclass
class CustomerToolResult:
    success: bool
    message: str
    tool_call_id: str = ""


class CustomerTools:
    def send_payment_reminder(self, customer_id: str, payment_id: str) -> CustomerToolResult:
        return CustomerToolResult(
            success=True,
            message=f"Payment reminder sent to {customer_id} for {payment_id}.",
            tool_call_id=str(uuid.uuid4()),
        )
