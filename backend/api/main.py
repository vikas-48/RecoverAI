from pathlib import Path
from typing import Any
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from ..agent.recovery_agent import RecoveryAgent
from ..models.recovery_model import RecoveryModel
from ..services.data_service import DataService
from ..services.recovery_orchestrator import RecoveryOrchestrator
from ..services.recovery_service import RecoveryService
from ..services.webhook_service import WebhookService
from ..tools.razorpay_tools import RazorpayAdapter, verify_webhook_signature

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
ARTIFACT = ROOT / "artifacts" / "recovery_model.joblib"

app = FastAPI(
    title="RecoverAI",
    description="AI-assisted revenue recovery decision engine",
    version="0.6.0",
)

# Frontend runs on a separate Vite origin during local development.
# Restrict CORS to local development origins rather than allowing every origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator: RecoveryOrchestrator | None = None
webhooks = WebhookService()


@app.on_event("startup")
def startup():
    global orchestrator

    if not ARTIFACT.exists():
        raise RuntimeError(
            f"Model artifact missing: {ARTIFACT}. "
            "Run `python scripts/train_model.py` first."
        )

    data_service = DataService(
        str(DATA / "customers.csv"),
        str(DATA / "payments.csv"),
    )
    model = RecoveryModel(ARTIFACT)
    recovery_service = RecoveryService(agent=RecoveryAgent())

    orchestrator = RecoveryOrchestrator(
        data_service=data_service,
        model=model,
        recovery_service=recovery_service,
    )


def require_orchestrator() -> RecoveryOrchestrator:
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return orchestrator


@app.get("/health")
def health():
    return {"status": "ok", "service": "recoverai", "version": "0.6.0"}


@app.get("/v1/payments")
def list_payments(
    limit: int = 25,
    failure_reason: str | None = None,
    status: str | None = None,
):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")

    orch = require_orchestrator()
    frame = orch.data.payments.copy()

    if failure_reason:
        frame = frame[frame["failure_reason"] == failure_reason]

    # Dataset contains failed payments. `status` is accepted for dashboard
    # compatibility; outcome state is produced by the recovery endpoint.
    if status and status != "failed":
        frame = frame.iloc[0:0]

    # Keep four judge-ready cases visible at the top of the queue while
    # preserving the rest of the dataset for exploration. PAY200018 is the
    # real Payment Link integration case.
    priority_ids = ["PAY200005", "PAY200011", "PAY200006", "PAY200018"]
    frame["_priority"] = frame["payment_id"].map(
        {pid: i for i, pid in enumerate(priority_ids)}
    ).fillna(9999)
    frame = frame.sort_values(["_priority"]).drop(columns=["_priority"]).head(limit)

    return {
        "count": len(frame),
        "payments": frame.fillna("").to_dict(orient="records"),
    }


@app.get("/v1/payments/{payment_id}")
def get_payment(payment_id: str):
    orch = require_orchestrator()
    try:
        return orch.data.get_case(payment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/v1/recovery/run/{payment_id}")
def run_recovery(payment_id: str):
    orch = require_orchestrator()
    try:
        result = orch.run(payment_id)
        # Include probability for the dashboard without changing RecoveryResult.
        context = orch.data.get_case(payment_id)
        probability = orch.model.predict_probability(context)

        response = result.model_dump()
        response["recovery_probability"] = probability
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/v1/recovery/external/{payment_id}")
def external_recovery(payment_id: str):
    orch = require_orchestrator()

    # Already reconciled by webhook
    state = orch.recovery_service.external_recoveries.get(payment_id)
    if state:
        return state

    razorpay = RazorpayAdapter()

    if not razorpay.enabled:
        return {"payment_id": payment_id, "status": "pending"}

    # Find the Payment Link created by RecoverAI for this case
    try:
        response = requests.get(
            f"{razorpay.BASE_URL}/payment_links",
            auth=razorpay._auth(),
            params={"count": 100},
            timeout=8,
        )
        response.raise_for_status()

        links = response.json().get("items", [])

        for link in links:
            notes = link.get("notes") or {}
            reference_id = link.get("reference_id", "")

            linked_case = notes.get("recoverai_payment_id")

            if not linked_case and reference_id.startswith("RA-"):
                linked_case = reference_id[3:].split("-", 1)[0]

            if linked_case != payment_id:
                continue

            if link.get("status") != "paid":
                continue

            amount_paise = (
                link.get("amount_paid")
                or link.get("amount")
                or 0
            )

            result = orch.recovery_service.reconcile_external_payment(
                payment_id=payment_id,
                razorpay_payment_id="payment_link_paid",
                amount_rupees=float(amount_paise) / 100,
                payment_link_id=link.get("id"),
            )

            return orch.recovery_service.external_recoveries[payment_id]

    except Exception as exc:
        return {
            "payment_id": payment_id,
            "status": "pending",
            "error": str(exc),
        }

    return {
        "payment_id": payment_id,
        "status": "pending",
    }


@app.get("/v1/recovery/audit")
def audit(payment_id: str | None = None):
    orch = require_orchestrator()
    events = orch.recovery_service.audit.events

    if payment_id:
        events = [e for e in events if e["payment_id"] == payment_id]

    return {"count": len(events), "events": events}


@app.get("/v1/analytics")
def analytics() -> dict[str, Any]:
    """
    Dashboard-level analytics from the held-out evaluation file.
    This keeps evaluation metrics separate from live recovery execution.
    """
    evaluation_file = DATA / "baseline_vs_recoverai_v1.csv"

    if not evaluation_file.exists():
        raise HTTPException(status_code=404, detail="Evaluation results unavailable")

    import pandas as pd

    df = pd.read_csv(evaluation_file)

    baseline = df[df["strategy"] == "Baseline"].iloc[0].to_dict()
    recoverai = df[df["strategy"] == "RecoverAI Policy v1"].iloc[0].to_dict()

    improvement = (
        (recoverai["expected_revenue_recovered"] /
         max(baseline["expected_revenue_recovered"], 1)) - 1
    )

    intervention_reduction = (
        1 - recoverai["interventions"] / max(baseline["interventions"], 1)
    )

    return {
        "baseline": baseline,
        "recoverai": recoverai,
        "expected_revenue_improvement": improvement,
        "intervention_reduction": intervention_reduction,
        "evaluation_note": "Synthetic held-out evaluation; not real merchant revenue.",
    }
@app.post("/webhooks/test")
async def webhook_test(request: Request):
    print("🔥 TEST WEBHOOK REACHED FASTAPI")
    body = await request.body()
    print("BODY:", body)
    return {"ok": True}

@app.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    secret = webhooks.secret

    if not secret:
        raise HTTPException(
            status_code=503,
            detail="RAZORPAY_WEBHOOK_SECRET is not configured",
        )

    if not verify_webhook_signature(raw_body, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    print("========== RAZORPAY WEBHOOK ==========")
    print("EVENT:", payload.get("event"))
    print("PAYLOAD:", payload)
    print("======================================")
    event_id = request.headers.get("x-razorpay-event-id")
    result = webhooks.handle(payload, event_id=event_id)

    # Close the loop for real Razorpay Payment Link recoveries.
    # The adapter stores the RecoverAI case id in Payment Link reference_id.
    if result.get("status") == "accepted" and result.get("event") == "payment_link.paid":
        payment_link = (
            payload.get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )
        payment = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )
        reference_id = payment_link.get("reference_id", "")

        notes = payment_link.get("notes") or {}

        case_payment_id = notes.get("recoverai_payment_id")

        if not case_payment_id and reference_id.startswith("RA-"):
            case_payment_id = reference_id[3:].split("-", 1)[0]
        
            try:
                amount_paise = payment_link.get("amount_paid") or payment.get("amount") or payment_link.get("amount") or 0
                amount_rupees = float(amount_paise) / 100
                print("🔥 RECONCILIATION TRIGGERED")
                print("CASE:", case_payment_id)
                print("PAYMENT:", payment.get("id"))
                print("AMOUNT:", amount_rupees)
                print("LINK:", payment_link.get("id"))
                reconciliation = require_orchestrator().recovery_service.reconcile_external_payment(
                    payment_id=case_payment_id,
                    razorpay_payment_id=payment.get("id", ""),
                    amount_rupees=amount_rupees,
                    payment_link_id=payment_link.get("id"),
                )
                result["reconciliation"] = reconciliation
            except Exception as exc:
                    import traceback
                    traceback.print_exc()
                    result["reconciliation_error"] = str(exc)

    return result
