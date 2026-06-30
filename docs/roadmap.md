# Roadmap

AgentGuard Runtime should grow from a small action gate into an operations layer for AI agents. The roadmap is organized by adoption risk, not feature ambition.

## v0.1 — Receipt-first runtime

- CLI and Python SDK for checking proposed tool calls.
- `agent.yaml` policy model.
- Evidence scoring and target denylist.
- Execution modes: `allow`, `dry_run`, `require_approval`, `block`.
- JSONL and SQLite receipts and governance report.
- Action receipt and governance report schemas.
- Metrics system for control/value scorecards.
- Receipt-based scorecard CLI.

## v0.2 — Framework adapters

- LangGraph middleware example for pre-tool-call interception.
- LiteLLM callback/proxy example for identity, cost, and receipt propagation.
- Generic subprocess/tool-runner wrapper.
- OpenTelemetry attributes for governed tool calls.

## v0.3 — Stronger audit trail

- Optional receipt signing.
- Policy bundle format.
- Redaction rules for secrets and sensitive targets.

## v0.4 — Agent operations scorecard

- Liveness from recent receipts.
- Cost trend and budget burn rate.
- Approval rate and blocked-action rate.
- Evidence quality trend.
- ApprovalEvent and OutcomeEvent ingestion.
- Value metrics provided by caller.

## v1.0 — Stable integration contract

- Stable `agent.yaml` schema.
- Stable receipt schema.
- Backward-compatible adapter API.
- Reference integrations for at least two production-grade agent stacks.
