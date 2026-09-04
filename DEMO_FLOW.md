# RecoverAI Demo Flow

## Scenario A — Autonomous recovery

Use the payment ID in `demo_cases.json` under `successful_autonomous_recovery`.

Show:
1. Recovery probability
2. Agent proposal
3. Policy approval
4. Tool execution
5. Outcome verification
6. Amount recovered
7. Audit events

## Scenario B — High-value human approval

Use the payment ID in `high_value_human_review`.

Expected:
- Agent may propose a recovery action.
- Policy overrides it because amount > ₹50,000.
- Final action = `escalate`.
- `requires_human = true`.
- No automatic revenue recovery.

## Scenario C — Stopping rule

Use the payment ID in `stopping_rule`.

Expected:
- Attempt number >= 3.
- Final action = `stop`.
- No further automated recovery.
- Audit records the stopping rule.

## Outcome semantics

`tool execution success` means the system successfully invoked the tool.

`recovery success` means the payment outcome was actually recovered.

These are intentionally separate.

## Production boundary

The current `OutcomeService` is a deterministic simulator for the hackathon.
In production, replace it with Razorpay payment-status verification/webhooks.


## Live Razorpay Payment Link demo

Use **PAY200018** (₹4,693.53, expired card, ~47% recovery probability). The agent should propose `send_payment_link`, policy should approve it, and RecoverAI should create a real Razorpay Test Mode Payment Link with `reference_id=RA-PAY200018`.

Do not mark the case recovered when the link is created. Pay the link in Test Mode. The `payment_link.paid` webhook then reconciles the reference ID, records the Razorpay payment ID and amount, and marks the case recovered.
