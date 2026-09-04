from pathlib import Path
import joblib
import pandas as pd


FEATURE_COLS = [
    "amount",
    "failure_reason",
    "attempt_number",
    "payment_method",
    "customer_lifetime_value",
    "customer_total_payments",
    "customer_success_rate",
    "customer_failure_rate",
    "average_payment",
    "days_since_last_success",
]


class RecoveryModel:
    def __init__(self, artifact_path: str | Path):
        self.artifact_path = Path(artifact_path)
        self.pipeline = joblib.load(self.artifact_path)
        # Compatibility fix for models trained with older scikit-learn
        model = self.pipeline.steps[-1][1]

        if not hasattr(model, "multi_class"):
            model.multi_class = "auto"

    def predict_probability(self, row: dict) -> float:
        frame = pd.DataFrame([{
            key: row[key] for key in FEATURE_COLS
        }])
        return float(self.pipeline.predict_proba(frame)[:, 1][0])
