# Webhook Ingestion: Knowledge Index

Start here. Each line is one note. Superseded decisions stay listed so the history is visible.

<!-- agent:auto:start -->
## Concepts
- [[webhook-backpressure]]: never drop a webhook silently; reject with 429 above 20,000 queued items

## Decisions
- [[adr-001-queue-retry]]: 30s visibility timeout, retry with backoff, reject overflow with 429
<!-- agent:auto:end -->
