from pathlib import Path
import sys
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ARTIFACT_DIR = ROOT / "artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA / "ml_dataset_v1.csv")

features = [
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

numeric = [
    "amount", "attempt_number", "customer_lifetime_value",
    "customer_total_payments", "customer_success_rate",
    "customer_failure_rate", "average_payment",
    "days_since_last_success"
]
categorical = ["failure_reason", "payment_method"]

preprocessor = ColumnTransformer([
    ("num", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]), numeric),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical),
])

pipeline = Pipeline([
    ("preprocess", preprocessor),
    ("model", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )),
])

train = df[df["split"] == "train"]
pipeline.fit(train[features], train["recoverable"])

artifact = ARTIFACT_DIR / "recovery_model.joblib"
joblib.dump(pipeline, artifact)

print(f"Saved model artifact: {artifact}")
