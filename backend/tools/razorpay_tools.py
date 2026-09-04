import os
import time
import uuid
from dataclasses import dataclass
from urllib import response

import requests


@dataclass
class RazorpayResult:
    success: bool
    message: str
    data: dict


class RazorpayAdapter:
    """
    Thin Razorpay Test Mode adapter.

    Important:
    Razorpay's Payments API is primarily for fetching/capturing payments;
    a failed payment is not "retried" by calling a retry endpoint.
    For RecoverAI, a retry action therefore maps to creating a fresh
    Payment Link / customer re-attempt workflow.

    Live API usage is opt-in with RAZORPAY_LIVE=true.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.enabled = (
            os.getenv("RAZORPAY_ENABLED", "false").lower() == "true"
            and bool(self.key_id and self.key_secret)
        )

    def _auth(self):
        if not self.enabled:
            raise RuntimeError("Razorpay adapter is disabled")
        return (self.key_id, self.key_secret)

    def fetch_payment(self, payment_id: str) -> RazorpayResult:
        response = requests.get(
            f"{self.BASE_URL}/payments/{payment_id}",
            auth=self._auth(),
            timeout=8,
        )
        if not response.ok:
            print("RAZORPAY ERROR:", response.status_code)
            print("RAZORPAY RESPONSE:", response.text)
            response.raise_for_status()
        return RazorpayResult(
            True,
            "Payment fetched from Razorpay.",
            response.json(),
        )

    def create_recovery_link(
        self,
        payment_id: str,
        amount_rupees: float,
        description: str = "RecoverAI payment recovery",
    ) -> RazorpayResult:
        # Razorpay API amounts are in the smallest currency unit.
        payload = {
            "amount": int(round(amount_rupees * 100)),
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "reference_id": f"RA-{payment_id}-{uuid.uuid4().hex[:8]}"[:40],
            "notes": {"recoverai_payment_id": payment_id},
            "reminder_enable": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/payment_links",
            auth=self._auth(),
            json=payload,
            timeout=8,
        )
        response.raise_for_status()

        return RazorpayResult(
            True,
            "Recovery payment link created.",
            response.json(),
        )


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    Razorpay webhook signatures must be validated against the raw request body.
    Uses the official HMAC-SHA256 verification pattern.
    """
    import hmac
    import hashlib

    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
