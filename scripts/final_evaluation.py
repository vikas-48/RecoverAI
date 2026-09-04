from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

path = DATA / "baseline_vs_recoverai_v1.csv"
df = pd.read_csv(path)

baseline = df[df.strategy == "Baseline"].iloc[0]
recover = df[df.strategy == "RecoverAI Policy v1"].iloc[0]

def pct(x):
    return f"{x * 100:.1f}%"

improvement = recover.expected_revenue_recovered / baseline.expected_revenue_recovered - 1
intervention_reduction = 1 - recover.interventions / baseline.interventions

print("RECOVERAI FINAL EVALUATION")
print("=" * 34)
print(f"Revenue at risk:             ₹{recover.total_revenue_at_risk:,.2f}")
print(f"Baseline expected recovery:  ₹{baseline.expected_revenue_recovered:,.2f}")
print(f"RecoverAI expected recovery: ₹{recover.expected_revenue_recovered:,.2f}")
print(f"Improvement:                 {pct(improvement)}")
print(f"Baseline interventions:      {baseline.interventions:,.0f}")
print(f"RecoverAI interventions:     {recover.interventions:,.0f}")
print(f"Intervention reduction:      {pct(intervention_reduction)}")
print(f"Baseline recovery rate:      {pct(baseline.expected_revenue_recovered / baseline.total_revenue_at_risk)}")
print(f"RecoverAI recovery rate:     {pct(recover.expected_revenue_recovered / recover.total_revenue_at_risk)}")

# Return machine-readable values for submission docs.
out = {
    "revenue_at_risk": float(recover.total_revenue_at_risk),
    "baseline_expected_recovery": float(baseline.expected_revenue_recovered),
    "recoverai_expected_recovery": float(recover.expected_revenue_recovered),
    "expected_recovery_improvement": float(improvement),
    "baseline_interventions": int(baseline.interventions),
    "recoverai_interventions": int(recover.interventions),
    "intervention_reduction": float(intervention_reduction),
}
(ROOT/"docs/final_metrics.json").write_text(__import__("json").dumps(out, indent=2))
