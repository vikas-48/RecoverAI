# RecoverAI Agent Layer — v0.1

## Architecture

Agent proposes → Policy authorizes → Tool executor acts → Audit records.

The LLM is intentionally NOT given direct authority over payment tools.

## Current implementation

The `RecoveryAgent` has a provider-agnostic LLM adapter and a deterministic fallback.
This lets the whole workflow run without an API key while preserving the interface
needed for structured LLM output.

## Run

```bash
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

Then POST a `RecoveryCase` to:

`/v1/recovery/decide`

## Tests

```bash
pytest -q
```
