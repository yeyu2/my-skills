---
type: concept
status: active
owner: human
sources: [raw/2026-10-19-incident-webhook-queue-drop.md]
supports: [adr-001-queue-retry]
---
# Webhook backpressure

Written by Priya after the 10-19 incident. Agents: do not rewrite this section.

The gateway must never accept a webhook it cannot keep. Answering 202 and then losing the event is worse than answering 429, because a partner retries a 429 and does nothing after a 202.

Rules:

1. No trimming on the webhook stream. Memory pressure is handled at the gateway, not by evicting entries.
2. Above the high-water mark (20,000 entries) the gateway returns 429 with `Retry-After: 30`.
3. The alert fires at half the high-water mark, so a human sees it before partners do.

<!-- agent:auto:start -->
Related decisions: [[adr-001-queue-retry]]
<!-- agent:auto:end -->
