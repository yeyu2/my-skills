---
type: decision
status: active
sources: [raw/2026-10-19-incident-webhook-queue-drop.md]
supports: [webhook-backpressure]
---
# ADR 001: queue retry, 30s visibility timeout, 429 on overflow

Date: 2026-10-20. Decided after the 10-19 incident.

## Decision

1. Remove `MAXLEN` trimming from the webhook stream.
2. Return 429 with `Retry-After: 30` above 20,000 queued entries to preserve [[webhook-backpressure]].
3. Workers keep a 30-second visibility timeout before an unacknowledged message is redelivered.
4. Failed verifications retry with exponential backoff: 2s, 4s, 8s, up to 5 attempts.

## Consequences

- No silent loss under load. Partners see 429 and retry.
- Slow batch payloads can still exceed 30 seconds and be redelivered. Accepted for now; revisit with data.
