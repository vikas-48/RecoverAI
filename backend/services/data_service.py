from pathlib import Path
import pandas as pd


class DataService:
    def __init__(self, customers_path: str, payments_path: str):
        self.customers = pd.read_csv(customers_path)
        self.payments = pd.read_csv(payments_path)

    def get_case(self, payment_id: str) -> dict:
        payment = self.payments[
            self.payments["payment_id"] == payment_id
        ]

        if payment.empty:
            raise KeyError(f"Payment not found: {payment_id}")

        p = payment.iloc[0]
        customer = self.customers[
            self.customers["customer_id"] == p["customer_id"]
        ]

        if customer.empty:
            raise KeyError(f"Customer not found: {p['customer_id']}")

        c = customer.iloc[0]

        return {
            "payment_id": str(p["payment_id"]),
            "customer_id": str(p["customer_id"]),
            "amount": float(p["amount"]),
            "failure_reason": str(p["failure_reason"]),
            "attempt_number": int(p["attempt_number"]),
            "payment_method": str(p["payment_method"]),
            "customer_lifetime_value": float(c["customer_lifetime_value"]),
            "customer_total_payments": int(c["customer_total_payments"]),
            "customer_success_rate": float(c["customer_success_rate"]),
            "customer_failure_rate": float(c["customer_failure_rate"]),
            "average_payment": float(c["average_payment"]),
            "days_since_last_success": int(c["days_since_last_success"]),
        }
