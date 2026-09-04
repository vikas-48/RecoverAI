# RecoverAI Final Runbook

## 1. Backend

```bash
cd recover-ai
python -m venv .venv
# activate the venv
pip install -r requirements.txt
python scripts/train_model.py
pytest -q
uvicorn backend.api.main:app --reload
```

Health check:

`GET /health`

## 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL.

The dashboard should show **API connected**.

## 3. Judge flow

### A — Autonomous recovery

Open Recovery Queue → select the curated successful case → Run Recovery Agent.

Show:

1. probability
2. agent proposal
3. policy approval
4. tool execution
5. outcome
6. recovered amount
7. audit

### B — Human protection

Select the high-value case.

Show:

AI proposal → Policy override → Human approval required.

### C — Stop

Select the exhausted-attempt case.

Show:

attempt limit → stop → no automated action.

## 4. Razorpay Test Mode

Set:

```env
RAZORPAY_ENABLED=true
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

Use Test Mode credentials only.

Create a public HTTPS webhook endpoint and subscribe to:

- payment.failed
- payment.authorized
- payment.captured
- payment_link.paid

The webhook handler verifies `X-Razorpay-Signature` against the raw body and uses
`x-razorpay-event-id` for idempotency.

## 5. LLM mode

Set:

```env
USE_LLM=true
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

The LLM returns only a strict structured action. The deterministic Policy Engine
still has final authority.

If the LLM is unavailable, the deterministic fallback keeps the demo working.

## 6. Submission claims

Use only numbers from `docs/final_metrics.json`.

Label them as **synthetic held-out evaluation results**.

Do not claim real merchant revenue, production deployment, or production ML accuracy.
