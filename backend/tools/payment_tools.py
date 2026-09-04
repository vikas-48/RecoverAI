from dataclasses import dataclass
import os
import uuid


@dataclass
class ToolResult:
    success: bool
    message: str
    amount_recovered: float = 0.0
    tool_call_id: str = ""
    external_id: str | None = None
    external_url: str | None = None


class PaymentTools:
    """
    Payment execution boundary.

    Default: safe local simulator.
    Optional: Razorpay Test Mode payment-link workflow when
    RAZORPAY_ENABLED=true and credentials are configured.
    """

    def __init__(self):
        self.razorpay = None

        if os.getenv("RAZORPAY_ENABLED", "false").lower() == "true":
            from .razorpay_tools import RazorpayAdapter
            self.razorpay = RazorpayAdapter()

    def retry_payment(self, payment_id: str, amount: float) -> ToolResult:
        # There is no generic "retry failed payment" endpoint in Razorpay's
        # Payments API. In live/Test Mode this workflow creates a fresh
        # customer payment opportunity instead.
        if self.razorpay and self.razorpay.enabled:
            result = self.razorpay.create_recovery_link(
                payment_id,
                amount,
                "RecoverAI payment recovery retry",
            )
            return ToolResult(
                success=result.success,
                message=result.message,
                tool_call_id=str(uuid.uuid4()),
                external_id=result.data.get("id"),
                external_url=result.data.get("short_url"),
            )

        return ToolResult(
            success=True,
            message=f"Retry workflow initiated for {payment_id}.",
            tool_call_id=str(uuid.uuid4()),
        )

    def schedule_retry(self, payment_id: str, delay_hours: int) -> ToolResult:
        return ToolResult(
            success=True,
            message=f"Retry scheduled for {payment_id} in {delay_hours}h.",
            tool_call_id=str(uuid.uuid4()),
        )

    def create_payment_link(self, payment_id: str, amount: float) -> ToolResult:
        if self.razorpay and self.razorpay.enabled:
            result = self.razorpay.create_recovery_link(
                payment_id,
                amount,
                "RecoverAI payment recovery link",
            )
            return ToolResult(
                success=result.success,
                message=result.message,
                tool_call_id=str(uuid.uuid4()),
                external_id=result.data.get("id"),
                external_url=result.data.get("short_url"),
            )

        return ToolResult(
            success=True,
            message=f"Payment link created for {payment_id}.",
            tool_call_id=str(uuid.uuid4()),
        )
