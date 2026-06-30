# Architecture

AgentGuard Runtime is an action-governance kernel for AI agents. It is not an agent framework, an IDE, an LLM gateway, or an observability dashboard. It sits at the boundary where an agent's reasoning becomes an external action.

```text
Agent framework / AI IDE / LLM gateway / MCP tool runner
                         |
                         v
              AgentGuard Runtime Boundary
                         |
        policy -> evidence -> decision -> receipt
                         |
                         v
          external tool, approval queue, or block
```

## Why this boundary exists

Agent frameworks are good at planning and orchestration. LLM gateways are good at routing model calls. Observability tools are good at tracing what happened. Production agent systems also need a deterministic layer that answers:

- Is this agent allowed to call this tool?
- Is this target safe?
- Is there enough evidence for the action?
- Should the action run, dry-run, wait for approval, or be blocked?
- Did the action leave a receipt that can be audited and measured later?

This is the runtime boundary AgentGuard standardizes.

## Layer model

AgentGuard is designed as a small kernel that can grow in layers without becoming a monolithic platform.

```text
┌──────────────────────────────────────────┐
│ 6. Experience Layer                       │
│ CLI / GitHub App / Dashboard / IDE UI     │
├──────────────────────────────────────────┤
│ 5. Integration Layer                      │
│ LangGraph / LiteLLM / MCP / CLI hooks     │
├──────────────────────────────────────────┤
│ 4. Operations Layer                       │
│ Liveness / Cost / Value / Drift / Replay  │
├──────────────────────────────────────────┤
│ 3. Receipt Layer                          │
│ Action receipt / Evidence / Audit trail   │
├──────────────────────────────────────────┤
│ 2. Policy Layer                           │
│ Tool risk / Target denylist / Approval    │
├──────────────────────────────────────────┤
│ 1. Action Boundary                        │
│ Proposed tool call -> decision -> receipt │
└──────────────────────────────────────────┘
```

The v0.1 implementation focuses on layers 1-3.

## Core objects

### AgentSpec

`AgentSpec` describes an agent's authority and operating mode.

```yaml
agent:
  name: repo-maintainer-agent
  owner: platform-team
  purpose: Triage repository issues and prepare low-risk maintenance changes.
  allowed_tools:
    - github.search_issues
    - github.comment_issue
  denied_targets:
    - "*secret*"
    - "*.env"
    - "prod/*"
  tool_risks:
    github.search_issues: low
    github.comment_issue: high
  mode_by_risk:
    low: allow
    medium: dry_run
    high: require_approval
    critical: block
```

This is the agent's authority envelope.

### ToolCall

`ToolCall` describes the action an agent wants to take.

```json
{
  "name": "github.comment_issue",
  "target": "owner/repo#123",
  "args": {},
  "evidence": []
}
```

AgentGuard treats tool calls as proposed actions, not as actions that have already happened.

### GuardDecision

`GuardDecision` is the deterministic result of applying policy and evidence checks.

```json
{
  "allowed": true,
  "mode": "require_approval",
  "risk_level": "high",
  "reasons": ["policy_passed"],
  "evidence_score": 0.82
}
```

The caller decides how to execute, queue, or display this decision.

### ActionReceipt

`ActionReceipt` records what decision was made at the boundary.

```json
{
  "agent": "repo-maintainer-agent",
  "tool": "github.comment_issue",
  "target": "owner/repo#123",
  "mode": "require_approval",
  "status": "pending_approval",
  "cost_usd": 0.012,
  "evidence_score": 0.82
}
```

Receipts are the foundation for audit, replay, cost analysis, and value measurement.

### GovernanceReport

`GovernanceReport` summarizes receipts into an operational view.

```json
{
  "alive": true,
  "value_state": "measurable",
  "risk_state": "approval_gated",
  "receipt_count": 128,
  "approval_required_count": 37,
  "blocked_count": 9,
  "total_cost_usd": 4.82
}
```

The report is intentionally coarse in v0.1. The goal is to make value measurable before adding dashboards. The full measurement model is defined in `docs/metrics.md`; features should improve accepted value, reduce unsafe actions, reduce review burden, reduce cost per accepted action, improve evidence quality, or improve audit completeness.

## Decision flow

```text
1. Load AgentSpec
2. Receive proposed ToolCall
3. Check tool allowlist
4. Check target denylist across target/url/path/resource
5. Infer or read tool risk
6. Score evidence
7. Map risk to execution mode
8. Write ActionReceipt
9. Return GuardDecision to caller
```

AgentGuard does not execute external actions by default. It produces decisions and receipts. The caller integrates execution according to its own approval and tool-running model.

## Execution modes

| Mode | Meaning |
| --- | --- |
| `allow` | The action can proceed automatically. |
| `dry_run` | The action should be recorded but not executed. |
| `require_approval` | A human or separate checker must approve before execution. |
| `block` | The action must not execute. |

## Non-goals

AgentGuard should not become:

- Another agent loop.
- A prompt framework.
- A hosted compliance product.
- A replacement for LangGraph, OpenHands, LiteLLM, Langfuse, or MCP.
- A UI-first platform before the runtime boundary is stable.

## Integration strategy

AgentGuard should integrate at the narrowest possible point: immediately before a tool call mutates external state.

Recommended integration points:

- LangGraph: before tool node execution.
- LiteLLM: join model cost and agent identity with action receipts.
- MCP: wrap tool invocations before dispatch.
- Local coding agents: hook before GitHub, filesystem, CI, deploy, Jira, Slack, or email actions.

## Long-term direction

The durable open-source asset is not just the Python package. It is the schema and operating model around governed agent actions.

Possible future modules:

```text
spec/
  agent.spec.schema.json
  tool_call.schema.json
  action_receipt.schema.json
  governance_report.schema.json
  approval_event.schema.json
  outcome_event.schema.json
adapters/
  langgraph
  litellm
  mcp
  claude-code
  codex-cli
stores/
  jsonl
  sqlite
  otel
policies/
  github.yaml
  jira.yaml
  filesystem.yaml
  deploy.yaml
ops/
  liveness
  cost
  value
  drift
  replay
```

The project should grow from runtime boundary to adapters, then to operations, then to stable schemas.

## Design principle

AgentGuard follows a simple rule:

> Probabilistic agents may propose actions. Deterministic runtime code decides how those actions cross the boundary.

That boundary is where reliability, safety, cost control, and auditability begin.
