# RecoverAI

## AI Revenue Recovery Agent for Razorpay

RecoverAI detects failed-payment revenue at risk, estimates recoverability,
proposes a bounded recovery action, authorizes it through deterministic
financial policy, executes the appropriate tool, and verifies the outcome.

### Core principle

**AI proposes → Policy authorizes → Tools execute → Webhooks verify → Audit records**

## What is implemented

- Synthetic customer/payment dataset
- Recovery ML model
- Recovery agent with deterministic fallback
- Optional structured LLM adapter
- Prompt-injection validation boundary
- Deterministic financial policy engine
- Payment/customer/operations tool layer
- Razorpay Test Mode Payment Link adapter
- Razorpay webhook signature verification
- Webhook idempotency using event ID
- Outcome verification simulator
- Audit trail
- FastAPI API
- React merchant dashboard
- Held-out baseline evaluation
- Judge-demo runner
- Architecture, pitch and runbook documents

## Important scope disclosure

The ML/economic evaluation uses synthetic held-out data.

The default recovery outcome layer is a deterministic simulator so the project
can run without external credentials.

Razorpay integration is implemented behind environment flags and is intended
for Test Mode. Production deployment would require additional monitoring,
calibration, authentication, secret management, retry handling and operational
controls.

The LLM is optional. If it is unavailable, RecoverAI falls back to deterministic
agent logic so the core demo remains reproducible.

## Evaluation

Synthetic held-out evaluation:

- Revenue at risk: ₹3.69 Cr
- Baseline expected recovery: ₹1.29 Cr
- RecoverAI expected recovery: ₹1.50 Cr
- Expected recovery improvement: 16.0%
- Baseline interventions: 2,653
- RecoverAI interventions: 2,004
- Intervention reduction: 24.5%
- Baseline recovery rate: 34.9%
- RecoverAI recovery rate: 40.5%

These are not real Razorpay merchant results.

## Backend

```bash
pip install -r requirements.txt
python scripts/train_model.py
pytest -q
uvicorn backend.api.main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE` if the FastAPI server is not on localhost:8000.

## Optional LLM mode

Copy `.env.example` to `.env` and configure:

```env
USE_LLM=true
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

The model output is constrained to a fixed action schema and is still passed
through the deterministic policy engine.

## Optional Razorpay Test Mode

```env
RAZORPAY_ENABLED=true
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

Never commit API keys or webhook secrets.

## Judge demo

```bash
python scripts/demo_runner.py
```

Demo cases:

1. Autonomous recovery
2. High-value human review
3. Exhausted-attempt stopping rule

## Documents

- `ARCHITECTURE.md`
- `PITCH.md`
- `DEMO_FLOW.md`
- `RAZORPAY_INTEGRATION.md`
- `docs/FINAL_RUNBOOK.md`
- `docs/final_metrics.json`

## Submission positioning

RecoverAI is designed for the **AI Revenue Recovery** track:

> Detect revenue at risk → determine the right intervention → execute a
> bounded recovery workflow → verify the outcome.

The strongest demo emphasizes measurable recovery, fewer unnecessary
interventions, bounded money-moving actions and a complete audit trail.
