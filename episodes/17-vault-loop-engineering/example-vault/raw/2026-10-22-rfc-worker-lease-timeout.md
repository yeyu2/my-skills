# RFC: replace the fixed 30s visibility timeout with a heartbeat lease

Author: Mei. Status: accepted 2026-10-22. Supersedes the timeout part of ADR 001.

## Problem

ADR 001 set a fixed 30-second visibility timeout. Since the 10-19 incident we measured verification time for one week:

| Payload | p50 | p99 | max |
| --- | --- | --- | --- |
| single event | 0.4s | 2.1s | 6s |
| batch (up to 500 events) | 18s | 45s | 71s |

Batch payloads regularly exceed 30 seconds. Each time, the message is redelivered while the first worker is still running. Idempotency keys stop double ledger writes, but we pay for duplicate partner API calls and the second worker blocks a slot.

Raising the fixed timeout to 90 seconds was rejected: a crashed worker would then hold a message for 90 seconds before anyone retries it.

## Decision

- Initial lease: 90 seconds.
- A worker extends its lease every 20 seconds while it is still processing, using `XCLAIM` with the same consumer name.
- If a worker stops heartbeating, the message becomes claimable 90 seconds after the last heartbeat.
- Backoff and the 429 rule from ADR 001 stay as they are.

## Rollout

Behind the flag `worker.heartbeat_lease`. Enabled for one partner on 10-23, all partners on 10-27.
