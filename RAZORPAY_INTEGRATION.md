# Razorpay Integration Boundary

RecoverAI uses Razorpay in two places:

1. **Payment status / webhook ingestion**
2. **Recovery payment link creation**

## Why Payment Links?

A failed Razorpay payment does not have a generic "retry this payment" API.
The Payments API is used for retrieving payment details and changing authorized
payments to captured. RecoverAI therefore maps an agent "retry" decision to a
fresh customer re-attempt workflow, represented by a Payment Link in the Test
Mode adapter.

## Test Mode

Configure Test Mode credentials:

```bash
RAZORPAY_ENABLED=true
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

The Razorpay dashboard has separate Test and Live modes and separate API keys.

## Webhooks

Endpoint:

```text
POST /webhooks/razorpay
```

The handler:

- verifies `X-Razorpay-Signature`
- uses the raw request body for signature validation
- extracts `payment.failed`, `payment.authorized`, and `payment.captured`
- rejects invalid signatures
- ignores duplicate event IDs

For the buildathon demo, subscribe to at least:

```text
payment.failed
payment.authorized
payment.captured
```

## Important production controls

- Keep keys in environment/secret storage.
- Verify every webhook signature.
- Make webhook processing idempotent.
- Return quickly and process heavy work asynchronously.
- Treat webhooks as the source of asynchronous state changes.
- Use a payment fetch API when immediate verification is required.

## Current hackathon scope

The default environment remains disabled, so the project continues to run fully
against the synthetic simulator until Test Mode credentials are configured.
