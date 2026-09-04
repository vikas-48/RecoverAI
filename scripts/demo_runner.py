from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT))

from backend.models.recovery_model import RecoveryModel
from backend.services.data_service import DataService
from backend.services.recovery_service import RecoveryService
from backend.services.recovery_orchestrator import RecoveryOrchestrator
from backend.agent.recovery_agent import RecoveryAgent


def main():
    ds = DataService(
        str(DATA / "customers.csv"),
        str(DATA / "payments.csv"),
    )
    model = RecoveryModel(ROOT / "artifacts" / "recovery_model.joblib")
    service = RecoveryService(agent=RecoveryAgent())
    orch = RecoveryOrchestrator(ds, model, service)

    print("\n=== RecoverAI Judge Demo ===\n")

    # Prefer curated cases generated during development.
    demo_file = ROOT / "demo_cases.json"
    if demo_file.exists():
        demo = json.loads(demo_file.read_text())
        ids = [
            ("Autonomous recovery", demo.get("successful_autonomous_recovery", {}).get("payment_id")),
            ("High-value human review", demo.get("high_value_human_review", {}).get("payment_id")),
            ("Stopping rule", demo.get("stopping_rule", {}).get("payment_id")),
        ]
    else:
        ids = []

    for title, payment_id in ids:
        if not payment_id:
            continue

        result = orch.run(payment_id)
        context = ds.get_case(payment_id)
        probability = model.predict_probability(context)

        print(f"--- {title} ---")
        print(f"Payment:       {payment_id}")
        print(f"Amount:        ₹{context['amount']:,.2f}")
        print(f"Failure:       {context['failure_reason']}")
        print(f"Probability:   {probability:.0%}")
        print(f"Agent:         {result.proposed_action.value}")
        print(f"Final action:  {result.final_action.value}")
        print(f"Policy:        {'APPROVED' if result.policy_approved else 'OVERRIDDEN'}")
        print(f"Human review:  {result.requires_human}")
        print(f"Outcome:       {result.outcome_status}")
        print(f"Recovered:     ₹{result.amount_recovered:,.2f}")
        print()

    print("Architecture: Model → Agent → Policy → Tool → Verification → Audit")
    print("LLM mode: set USE_LLM=true + OPENAI_API_KEY to enable.")
    print("Razorpay mode: set RAZORPAY_ENABLED=true + Test Mode credentials.")
    print()


if __name__ == "__main__":
    main()
