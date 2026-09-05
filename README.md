# RecoverAI — AI-Powered Revenue Recovery Engine

> **AI proposes. Policy authorizes. Tools execute.**

RecoverAI is an AI-driven revenue recovery decision engine built for the **Razorpay AI Revenue Recovery Buildathon**.

Instead of treating every failed payment the same way, RecoverAI combines **ML-based recovery prediction, Gemini-powered reasoning, deterministic policy enforcement, Razorpay execution, and verified payment outcomes** to decide the safest and most effective next action for each failed payment.

---

## Problem

Payment recovery mechanisms such as retries and payment links already exist.

The harder problem is:

> **When a payment fails, what should we do next?**

Different failures require different interventions:

- A temporary network failure may be worth retrying.
- An expired card may require a new payment method.
- A high-value transaction may require human approval.
- A low-probability recovery attempt may be better stopped.

RecoverAI acts as the **intelligence and governance layer** between a failed payment and the available recovery mechanisms.

---

## Solution

RecoverAI follows a simple principle:

```text
AI proposes → Policy authorizes → Tools execute → Outcome is verified
```

For every failed payment, the system:

1. Detects the failed payment.
2. Estimates its recovery probability.
3. Provides payment and customer context to an AI Recovery Agent.
4. Gemini proposes exactly one bounded recovery action.
5. A deterministic Policy Engine validates the proposal.
6. The approved action is executed.
7. Razorpay webhooks verify actual payment recovery.
8. Every step is recorded in an audit trail.

---

## Architecture

```text
                         ┌─────────────────────┐
                         │   Failed Payment    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  ML Prediction      │
                         │ Recovery Probability│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Gemini Recovery     │
                         │ Agent               │
                         │ Proposes ONE action │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Policy Engine          │
                    │                              │
                    │ • Amount limits              │
                    │ • Probability threshold      │
                    │ • Retry limits               │
                    │ • Payment-method constraints │
                    │ • Escalation rules           │
                    └──────────────┬───────────────┘
                                   │
                          Approved / Overridden
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       Tool Execution          │
                    │                              │
                    │ Retry                         │
                    │ Schedule Retry                │
                    │ Razorpay Payment Link         │
                    │ Human Escalation              │
                    │ Stop                          │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │ Outcome Verification│
                         │ Razorpay Webhook    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Audit Trail     │
                         └─────────────────────┘
```

---

## Recovery Actions

| Action | Use Case |
|---|---|
| `retry` | Immediate retry is appropriate |
| `schedule_retry` | Temporary failure where retrying later is preferable |
| `send_payment_link` | Existing payment method is invalid/expired |
| `escalate` | Human intervention is required |
| `stop` | Recovery is unlikely or retry limits are reached |

The agent cannot invent arbitrary financial actions.

---

## AI Safety & Policy Engine

The Gemini agent **does not have unrestricted authority**.

The deterministic Policy Engine can override an AI recommendation.

Example:

```text
Payment Amount: ₹71,853.45
Failure: network_error
Recovery Probability: 81.5%

Gemini:
    → Schedule Retry

Policy:
    → Amount > ₹50,000
    → Automatic recovery not allowed

Final Action:
    → Escalate to Human
```

This creates a clear separation:

```text
AI = Intelligence
Policy = Control
Tools = Execution
```

### Current policy controls

- Maximum automatic recovery amount: **₹50,000**
- Minimum recovery probability: **30%**
- Maximum retry attempts: **3**
- Invalid/expired payment methods cannot be retried directly.
- High-value transactions are escalated.
- Low-probability cases can be stopped.
- Scheduled retries cannot exceed the configured maximum window.

---

## Gemini Recovery Agent

RecoverAI uses Gemini for contextual decision-making.

The agent receives payment and customer context such as:

```json
{
  "payment_id": "PAY219999",
  "amount": 71853.45,
  "failure_reason": "network_error",
  "attempt_number": 2,
  "recovery_probability": 0.8149,
  "customer_success_rate": 0.995,
  "customer_lifetime_value": "...",
  "average_payment": "..."
}
```

The model returns a structured decision:

```json
{
  "action": "schedule_retry",
  "confidence": 0.92,
  "reason": "High recovery probability with a temporary failure."
}
```

The response is schema-validated before reaching the Policy Engine.

If Gemini is unavailable or produces an invalid response, RecoverAI falls back to deterministic recovery logic.

---

## Razorpay Integration

RecoverAI integrates with Razorpay Test Mode to execute actual recovery workflows.

For payment-link recovery:

```text
Failed Payment
      ↓
AI Proposal
      ↓
Policy Approval
      ↓
Razorpay Payment Link
      ↓
Customer Pays
      ↓
payment_link.paid
      ↓
Webhook Verification
      ↓
Revenue Recovered
```

### Important distinction

Creating a payment link **does not mean revenue has been recovered**.

The system initially records:

```text
OUTCOME_PENDING
```

Only after receiving and validating the Razorpay `payment_link.paid` webhook does the system record:

```text
OUTCOME_VERIFIED
status = recovered
```

This prevents recovery opportunities from being incorrectly counted as recovered revenue.

---

## Webhook Security

The Razorpay webhook implementation:

- Reads the raw webhook body.
- Validates the `X-Razorpay-Signature`.
- Uses HMAC-SHA256 verification.
- Handles `payment_link.paid` events.
- Maps the payment back to the original RecoverAI case.
- Records the verified recovery.
- Handles duplicate webhook events safely.

---

## Audit Trail

Every recovery decision produces an end-to-end audit trail.

```text
CASE_DETECTED
      ↓
AGENT_LLM_CALL
      ↓
AGENT_PROPOSAL
      ↓
POLICY_DECISION
      ↓
TOOL_EXECUTION
      ↓
OUTCOME_PENDING / OUTCOME_VERIFIED
```

The audit records:

- Original payment context
- ML prediction
- AI provider/model
- Gemini proposal
- Confidence
- Reasoning summary
- Policy decision
- Policy override
- Tool execution
- Razorpay payment-link information
- Webhook confirmation
- Final recovery outcome

This makes every decision traceable.

---

## Dashboard

The React dashboard provides an operations-oriented view of the recovery system.

### Customer Intelligence

Displays:

- Recovery probability
- Payment success rate
- Total payments
- Customer lifetime value
- Average payment
- Failure rate
- Last successful payment

### Decision Trace

```text
01 ML PREDICTION
       ↓
02 AI RECOVERY AGENT
       ↓
03 POLICY ENGINE
       ↓
04 TOOL EXECUTION
       ↓
05 OUTCOME
```

### Audit Trail

Operators can inspect:

- Latest recovery run
- Previous runs
- Agent proposal
- Policy decision
- Overrides
- Tool execution
- Verified outcomes

---

# Demonstration Cases

## Case 1 — High-Value Transaction

**Payment:** `PAY219999`

```text
Amount:               ₹71,853.45
Failure:              network_error
Attempt:              2
Recovery Probability: ~81.5%
```

Gemini proposes:

```text
Schedule Retry
```

Policy detects:

```text
Amount > ₹50,000
```

Therefore:

```text
AI Proposal:
    Schedule Retry

Policy:
    OVERRIDE

Final Action:
    Escalate
```

This demonstrates that the AI cannot bypass deterministic financial controls.

---

## Case 2 — Expired Card + Real Razorpay Recovery

**Payment:** `PAY200018`

```text
Amount:        ₹4,693.53
Failure:       expired_card
Attempt:       1
```

Gemini identifies that retrying the existing payment method is inappropriate and proposes:

```text
Send Payment Link
```

Policy approves the action.

RecoverAI creates a real Razorpay Payment Link.

After the customer completes payment:

```text
payment_link.paid
       ↓
Webhook verification
       ↓
Payment reconciliation
       ↓
₹4,693.53 recovered
```

The system only marks the transaction as recovered after webhook confirmation.

---

## Graceful Failure

RecoverAI is designed to fail safely.

### LLM unavailable

```text
Gemini unavailable
      ↓
Deterministic fallback
      ↓
Policy Engine
      ↓
Safe execution
```

### Invalid LLM response

```text
Invalid structured response
      ↓
Validation failure
      ↓
Deterministic fallback
```

### Low recovery probability

```text
Recovery Probability < threshold
      ↓
Stop recovery
```

### High-value transaction

```text
Amount > automatic limit
      ↓
Human escalation
```

### Payment Link created but not paid

```text
Payment Link created
      ↓
PENDING
      ↓
Wait for webhook
```

The system never treats link creation alone as recovered revenue.

---

# Tech Stack

### Backend

- Python
- FastAPI
- Gemini API
- Razorpay API
- Pydantic
- Requests

### Frontend

- React
- Vite
- JavaScript
- CSS

### AI / ML

- Recovery probability prediction
- Gemini Recovery Agent
- Structured JSON responses
- Deterministic fallback logic

### Payments

- Razorpay Test Mode
- Razorpay Payment Links
- Razorpay Webhooks
- HMAC-SHA256 signature verification

---

# Project Structure

```text
RecoverAI/
│
├── backend/
│   ├── agent/
│   │   ├── recovery_agent.py
│   │   └── gemini_client.py
│   │
│   ├── api/
│   │   └── main.py
│   │
│   ├── tools/
│   │   └── razorpay_tools.py
│   │
│   ├── policy/
│   │   └── policy_engine.py
│   │
│   ├── services/
│   │   ├── recovery_service.py
│   │   ├── audit_service.py
│   │   └── outcome_service.py
│   │
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
│
├── .env
├── requirements.txt
└── README.md
```

---

# Setup

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd RecoverAI
```

## 2. Backend setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

Create a `.env` file:

```env
RAZORPAY_KEY_ID=your_razorpay_test_key_id
RAZORPAY_KEY_SECRET=your_razorpay_test_key_secret
RAZORPAY_ENABLED=true
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret

USE_LLM=true
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash
```

**Never commit your `.env` file or API keys to GitHub.**

## 4. Start the backend

```bash
uvicorn backend.api.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

## 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at the Vite development URL shown in the terminal.

---

# Razorpay Webhook Setup

For local development, expose the FastAPI server using Cloudflare Quick Tunnel:

```powershell
.\cloudflared.exe tunnel --url http://localhost:8000
```

Use the generated URL:

```text
https://<your-tunnel>.trycloudflare.com/webhooks/razorpay
```

Configure this endpoint in Razorpay Test Mode and use the same webhook secret configured in `.env`.

---

# API Endpoints

### Get payments

```http
GET /v1/payments
```

### Run recovery

```http
POST /v1/recovery/run/{payment_id}
```

### Get audit trail

```http
GET /v1/recovery/audit?payment_id={payment_id}
```

### Check external recovery

```http
GET /v1/recovery/external/{payment_id}
```

### Razorpay webhook

```http
POST /webhooks/razorpay
```

---

# Example Recovery Flow

```text
PAY200018
   │
   ▼
Payment fetched
   │
   ▼
ML predicts recovery probability
   │
   ▼
Gemini:
"send_payment_link"
   │
   ▼
Policy:
"APPROVED"
   │
   ▼
Razorpay Payment Link
   │
   ▼
Customer completes payment
   │
   ▼
Razorpay webhook
   │
   ▼
Signature verified
   │
   ▼
Payment reconciled
   │
   ▼
RECOVERED
```

---

# Design Principles

### 1. AI is not the final authority

Gemini can recommend an action, but deterministic business rules can override it.

### 2. Recovery must be measurable

A recovery opportunity is not revenue until the payment is verified.

### 3. Financial boundaries are deterministic

Amount limits, retry limits and escalation rules should not depend on an LLM.

### 4. Every decision should be explainable

The system records why an action was proposed, whether policy changed it, what was executed and what ultimately happened.

### 5. Failure should degrade safely

If the AI fails, deterministic logic takes over rather than stopping the entire recovery pipeline.

---

# Buildathon Alignment

RecoverAI addresses the core revenue-recovery workflow:

```text
Detect revenue at risk
        ↓
Understand the payment context
        ↓
Choose an intervention
        ↓
Apply financial/operational controls
        ↓
Execute recovery
        ↓
Verify actual revenue recovered
        ↓
Measure and audit
```

The central objective is:

> **Turn failed-payment recovery from a generic rule-based action into a contextual, governed, and measurable decision process.**

---

# Future Improvements

Potential production extensions include:

- Persistent audit/event storage
- Persistent webhook idempotency
- More sophisticated customer segmentation
- Online learning from recovery outcomes
- Merchant-configurable policies
- Multi-channel recovery orchestration
- Email/SMS/WhatsApp recovery workflows
- Recovery-cost optimization
- Batch-level recovery optimization
- A/B testing of recovery strategies
- Human approval workflow with SLA tracking

---

# Security Notes

This project is intended for Razorpay Test Mode / development use.

Do not commit:

```text
.env
API keys
Razorpay secrets
Gemini API keys
Webhook secrets
```

Use environment variables or a secure secrets manager in production.

---

# License

This project was developed as part of the **Razorpay AI Revenue Recovery Buildathon**.

---

## RecoverAI

**Detect. Decide. Recover. Verify.**

> **AI proposes. Policy authorizes. Tools execute.**
