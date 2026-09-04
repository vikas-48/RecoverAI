# RecoverAI Architecture

## Core principle

**AI proposes. Policy authorizes. Tools execute. Webhooks verify.**

This prevents an LLM from having direct authority over money-moving actions.

## Components

### 1. Event ingestion
Razorpay payment events enter through a signed webhook endpoint.

### 2. Context builder
Fetches the payment and customer context required for recovery prediction.

### 3. Recovery ML model
Outputs a probability between 0 and 1 representing estimated recoverability.

### 4. Recovery Agent
Uses structured LLM output to propose one of five actions:

- retry
- schedule_retry
- send_payment_link
- escalate
- stop

The agent cannot invent a new action.

### 5. Policy Engine
Deterministic authorization layer.

Current guardrails:

- > ₹50,000 → human review
- attempt >= 3 → stop
- probability < 0.30 → stop
- invalid/expired payment method → no blind retry
- unknown action → reject/escalate

### 6. Tool layer
Adapters for payment, customer communication and operations.

### 7. Outcome verification
Current demo uses a deterministic simulator.

Production uses Razorpay payment status and webhook events.

### 8. Audit
Records:

`CASE_DETECTED → AGENT_PROPOSAL → POLICY_DECISION → TOOL_EXECUTION → OUTCOME_VERIFIED`

## Why this architecture?

A payment recovery agent needs more than LLM reasoning.

The architecture separates:

- probabilistic prediction
- probabilistic reasoning
- deterministic financial policy
- external execution
- asynchronous verification

This makes the system safer, testable and auditable.
