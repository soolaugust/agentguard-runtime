# Example Report

This page shows concrete AgentGuard output from the repository examples. It is generated from:

```bash
agentguard check \
  --agent examples/agent.yaml \
  --call examples/tool_call.json \
  --receipts /tmp/agentguard-example/receipts.jsonl \
  --cost 0.012

agentguard report \
  --agent examples/agent.yaml \
  --receipts /tmp/agentguard-example/receipts.jsonl

agentguard scorecard \
  --agent examples/agent.yaml \
  --receipts /tmp/agentguard-example/receipts.jsonl
```

The sample tool call proposes a GitHub issue comment on `langchain-ai/langgraph#8026`. The policy marks `github.comment_issue` as a high-risk mutating action, so the action is not executed automatically.

## Decision and receipt

```json
{
  "decision": {
    "allowed": true,
    "mode": "require_approval",
    "risk_level": "high",
    "reasons": [
      "policy_passed"
    ],
    "evidence_score": 0.7975
  },
  "receipt": {
    "receipt_id": "feb21759b45220d6",
    "agent": "repo-maintainer-agent",
    "tool": "github.comment_issue",
    "target": "langchain-ai/langgraph#8026",
    "mode": "require_approval",
    "status": "pending_approval",
    "reasons": [
      "policy_passed"
    ],
    "evidence_score": 0.7975,
    "cost_usd": 0.012,
    "created_at": "2026-06-30T05:51:25.875464+00:00"
  }
}
```

Interpretation:

- `allowed: true` means the action is within the agent's declared authority envelope.
- `mode: require_approval` means the runtime will not auto-execute it.
- `risk_level: high` comes from the tool policy.
- `evidence_score: 0.7975` means the action has enough supporting evidence to be considered, but risk still requires approval.
- The receipt is the durable audit object used by reports and scorecards.

## Governance report

```json
{
  "agent": "repo-maintainer-agent",
  "alive": true,
  "value_state": "measurable",
  "risk_state": "approval_gated",
  "receipt_count": 1,
  "approval_required_count": 1,
  "blocked_count": 0,
  "total_cost_usd": 0.012,
  "evidence_score_avg": 0.797,
  "generated_at": "2026-06-30T05:51:25.935731+00:00"
}
```

Interpretation:

- `alive: true` means the agent has produced at least one receipt.
- `risk_state: approval_gated` means at least one action requires approval.
- `value_state: measurable` means there is enough receipt data for v0.1 control measurement.
- `total_cost_usd` is caller-supplied and accumulated across receipts.

This report answers: is the agent producing governed actions and what is the current risk/cost posture?

## Metrics scorecard

```json
{
  "agent": "repo-maintainer-agent",
  "proposed_actions": 1,
  "executed_count": 0,
  "dry_run_count": 0,
  "approval_required_count": 1,
  "blocked_count": 0,
  "failed_count": 0,
  "total_cost_usd": 0.012,
  "evidence_quality_avg": 0.797,
  "approval_burden_rate": 1.0,
  "blocked_action_rate": 0.0,
  "control_state": "review_heavy",
  "generated_at": "2026-06-30T05:51:26.000437+00:00"
}
```

Interpretation:

- `proposed_actions: 1` means one proposed tool call crossed the runtime boundary.
- `approval_burden_rate: 1.0` means 100% of proposed actions required approval in this sample.
- `blocked_action_rate: 0.0` means no actions were blocked by policy.
- `control_state: review_heavy` means the runtime is currently creating review load rather than automatic execution.

This scorecard answers: is the agent useful to operate, or is it creating too much review burden/noise?

## What this example does not prove

This example proves v0.1 control metrics, not business value. It does not yet prove that the GitHub comment was accepted, useful, or outcome-positive. That requires future `ApprovalEvent` and `OutcomeEvent` ingestion.

The intended progression is:

```text
ActionReceipt -> GovernanceReport -> MetricsScorecard -> ApprovalEvent -> OutcomeEvent -> accepted value per dollar
```

AgentGuard should not claim value until approval and outcome data support it.
