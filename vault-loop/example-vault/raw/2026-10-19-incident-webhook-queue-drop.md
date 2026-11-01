# Incident 2026-10-19: webhook events dropped during settlement

Severity: SEV-2. Duration: 41 minutes. Author: Priya.

## Impact

About 3,200 payment status events from two partners were never processed. Ledger balances for 214 merchants were stale until a manual replay the next morning.

## Timeline (UTC)

- 23:02 Month-end settlement starts. Gateway traffic climbs to 2,100 rps.
- 23:09 Queue depth passes 5,000 entries.
- 23:09 to 23:50 Stream trimming with `MAXLEN ~ 5000` silently evicts the oldest entries. The gateway keeps answering 202.
- 23:43 A partner reports missing confirmations.
- 23:50 Traffic drops. Queue drains.

## Root cause

The stream was created with approximate trimming at 5,000 entries, inherited from a logging template. Under load, trimming evicted unprocessed events. The gateway had no idea the queue was full, so partners were told everything was accepted.

## Contributing factor

Workers use a 30-second visibility timeout. Several large batch payloads took longer than 30 seconds to verify, so they were redelivered to a second worker while the first was still busy. That doubled verification calls to the partner API during the worst minutes.

## Fixes

1. Remove `MAXLEN` trimming from the webhook stream.
2. The gateway checks queue depth. Above 20,000 entries it returns 429 with `Retry-After: 30`. Partners retry 429s.
3. Keep the 30-second visibility timeout for now, and add retry with exponential backoff on the worker side.
4. Alert at 10,000 entries.
