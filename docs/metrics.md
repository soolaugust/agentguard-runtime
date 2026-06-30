# Metrics System

AgentGuard is only useful if it can prove that governed agent actions are safer, cheaper, and more valuable than ungoverned automation. This document defines the measurement system that keeps the project grounded.

## Measurement thesis

Agent activity is not value. Tokens, traces, and tool-call counts are inputs. The value of an agent runtime is measured by accepted, safe, evidence-backed actions per unit cost and risk.

AgentGuard should optimize for:

```text
valuable accepted actions / (cost + human review load + operational risk)
```

The exact formula will evolve, but the direction should not: more accepted value, less unbounded risk.

## Event model

AgentGuard metrics should be derived from three event classes.

### 1. Action decision event

Produced when AgentGuard evaluates a proposed tool call. In v0.1 this is the `ActionReceipt`.

It answers:

- What did the agent propose?
- What policy decision was made?
- What evidence supported the action?
- What did the model/tool step cost?

### 2. Approval event

Produced when a human or checker approves, rejects, or expires a pending action.

It answers:

- Did humans accept the action?
- How long did review take?
- Which tools create the most review burden?

### 3. Outcome event

Produced after an action has had time to succeed, fail, be reverted, or be corrected.

It answers:

- Did the action achieve the intended outcome?
- Was it rolled back or corrected?
- Did it create downstream work?

v0.1 only has action decision events. Approval and outcome events are planned because without them the system can measure control, but not full business value.

## North-star metric

### Accepted value per dollar

```text
accepted_value_per_usd = accepted_action_value / total_cost_usd
```

In early versions, `accepted_action_value` may be a caller-provided score. Later it should be derived from outcome events or domain-specific integrations.

Why this matters: it prevents the project from optimizing for activity, traces, or blocked-action theater.

## Core metrics

### Accepted action rate

```text
accepted_action_rate = accepted_actions / proposed_actions
```

Meaning: how often proposed actions survive policy and review.

Interpretation:

- Too low: the agent is noisy or policies are misconfigured.
- Too high: policies may be too permissive, especially for high-risk tools.

Requires: approval events for full accuracy. In v0.1, `allow` and `dry_run` receipts can act as a weak proxy.

### Approval burden rate

```text
approval_burden_rate = approval_required_actions / proposed_actions
```

Meaning: how much human review load the agent creates.

Interpretation:

- High with low acceptance: the agent wastes reviewer attention.
- High with high value: the agent may be useful but needs better evidence or safer scopes.

Available from v0.1 receipts.

### Blocked risky action rate

```text
blocked_risky_action_rate = blocked_actions / proposed_actions
```

Meaning: how often the runtime prevents unsafe or out-of-policy actions.

Interpretation:

- Useful early signal, but not a success metric by itself.
- A high blocked rate can mean the guard works, or that the agent is poorly constrained upstream.

Available from v0.1 receipts.

### Evidence quality average

```text
evidence_quality_avg = mean(evidence_score)
```

Meaning: whether actions are grounded in enough evidence.

Interpretation:

- Low score: improve retrieval, context, or tool result provenance.
- High score with poor outcomes: evidence may be irrelevant or misleading.

Available from v0.1 receipts.

### Cost per accepted action

```text
cost_per_accepted_action = total_cost_usd / accepted_actions
```

Meaning: unit economics of agent automation.

Requires: approval or outcome events for accurate accepted action count.

### Rework rate

```text
rework_rate = corrected_or_reverted_actions / executed_actions
```

Meaning: how often accepted actions create cleanup work.

Requires: outcome events.

### Time to decision

```text
time_to_decision = decision_time - proposed_time
```

Meaning: runtime overhead added by policy/evidence checks.

Requires: explicit proposed timestamp. v0.1 receipts only capture receipt creation time.

### Time to approval

```text
time_to_approval = approval_time - receipt_created_at
```

Meaning: human review latency introduced by approval gates.

Requires: approval events.

## Guardrail metrics

These metrics prevent AgentGuard from becoming security theater or productivity drag.

### False block rate

```text
false_block_rate = incorrectly_blocked_actions / blocked_actions
```

A high false block rate means policy is hurting useful work.

### Approval rejection rate

```text
approval_rejection_rate = rejected_approval_actions / approval_required_actions
```

A high rejection rate means agents are proposing too many bad actions or evidence is weak.

### Reviewer interruption cost

```text
reviewer_interruption_cost = approval_required_actions * estimated_review_minutes
```

A runtime that shifts all risk to humans without reducing work is not valuable.

### Silent execution rate

```text
silent_execution_rate = executed_actions_without_receipts / executed_actions
```

This should be zero for integrated tools. Non-zero means the integration has bypass paths.

## Anti-metrics

Do not optimize for these in isolation:

- Number of tool calls.
- Number of traces.
- Number of blocked actions.
- Number of approvals requested.
- Total token volume.
- Number of agents connected.

These are activity indicators, not value indicators.

## v0.1 scorecard

The current receipt schema supports these metrics directly:

| Metric | Source fields |
| --- | --- |
| `proposed_actions` | count of receipts |
| `approval_burden_rate` | `status == pending_approval` |
| `blocked_risky_action_rate` | `status == blocked` |
| `total_cost_usd` | sum of `cost_usd` |
| `evidence_quality_avg` | mean of `evidence_score` |
| `risk_state` | receipt status distribution |

The v0.1 scorecard is intentionally limited. It proves the runtime is controlling and recording actions, not that the actions created business value.

## v0.2 required events

To measure real value, add two schemas:

### ApprovalEvent

```json
{
  "receipt_id": "example-0001",
  "decision": "approved",
  "reviewer": "human-or-checker-id",
  "reason": "Evidence matches issue state",
  "created_at": "2026-06-30T00:05:00+00:00"
}
```

### OutcomeEvent

```json
{
  "receipt_id": "example-0001",
  "outcome": "succeeded",
  "value_score": 1.0,
  "rework_required": false,
  "created_at": "2026-06-30T01:00:00+00:00"
}
```

These events let AgentGuard distinguish a merely governed action from a valuable action.

## Health states

AgentGuard reports should use explicit states instead of vague health language.

| State | Meaning |
| --- | --- |
| `no_data` | No receipts or events available. |
| `measuring_control` | Receipts exist, but no approval/outcome feedback yet. |
| `measuring_value` | Approval or outcome events exist. |
| `valuable` | Accepted value is positive after cost and rework. |
| `noisy` | High block/reject rate and low accepted value. |
| `too_expensive` | Cost per accepted action exceeds budget. |
| `too_risky` | Rework, rollback, or false-allow rate exceeds budget. |

## Minimum viable dashboard

The first dashboard should fit on one screen:

```text
Agent: repo-maintainer-agent
Period: 7d

Proposed actions:        128
Allowed:                 51
Pending approval:        37
Blocked:                 9
Dry-run:                 31
Total cost:              $4.82
Evidence avg:            0.78
Approval burden:         28.9%
Blocked action rate:     7.0%
Cost / accepted action:  pending approval data
State:                   measuring_control
```

If this dashboard cannot convince a user that AgentGuard changes operational outcomes, the project should improve metrics before adding more adapters.

## Product implication

Every new feature should improve at least one of these metric classes:

- Increase accepted value.
- Reduce unsafe actions.
- Reduce review burden.
- Reduce cost per accepted action.
- Improve evidence quality.
- Improve audit completeness.

If a feature does not move one of these, it is probably platform bloat.
