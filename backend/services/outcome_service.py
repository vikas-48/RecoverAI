from dataclasses import dataclass
import hashlib


@dataclass
class Outcome:
    status: str
    amount_recovered: float
    message: str


class OutcomeService:
    """
    Deterministic, reproducible outcome simulator for the hackathon dataset.

    In production this boundary becomes a Razorpay webhook/payment-status lookup.
    The simulator lets us demonstrate the complete recovery lifecycle safely.
    """

    ACTION_MULTIPLIER = {
        "retry": 0.90,
        "schedule_retry": 1.00,
        "send_payment_link": 0.88,
        "escalate": 0.78,
        "stop": 0.00,
    }

    def verify(
        self,
        payment_id: str,
        amount: float,
        action: str,
        recovery_probability: float,
    ) -> Outcome:
        multiplier = self.ACTION_MULTIPLIER[action]
        success_probability = min(
            0.98,
            max(0.0, recovery_probability * multiplier),
        )

        # Stable pseudo-random number derived from payment/action.
        # This makes demo results reproducible across runs.
        digest = hashlib.sha256(
            f"{payment_id}:{action}:recoverai-v1".encode()
        ).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF

        recovered = bucket < success_probability

        if recovered:
            return Outcome(
                status="recovered",
                amount_recovered=round(amount, 2),
                message="Payment recovery verified successfully.",
            )

        return Outcome(
            status="failed",
            amount_recovered=0.0,
            message="Recovery action executed but payment was not recovered.",
        )
