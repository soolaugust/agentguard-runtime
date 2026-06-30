# Stop Building Agents. Start Operating Them.

Most AI agent demos focus on what the agent can think through. Production systems fail at a different boundary: what the agent is allowed to do.

An agent that summarizes a file is a model feature. An agent that comments on an issue, opens a pull request, deploys a service, edits a ticket, or sends a message is an operational actor. Operational actors need boundaries.

## The missing layer

The current ecosystem already has strong building blocks:

- Agent frameworks for orchestration.
- AI IDEs for coding workflows.
- LLM gateways for provider routing.
- Observability tools for traces and metrics.
- MCP and tool protocols for connectivity.

What is still underspecified is the action boundary:

```text
agent proposes action -> runtime checks policy/evidence/risk -> action receipt is recorded
```

Without that boundary, teams end up asking the same questions repeatedly:

- Who approved this action?
- What evidence supported it?
- What did it cost?
- Why was it allowed?
- What was blocked?
- Did the accepted actions justify the spend?

## Activity is not value

Agent systems often measure calls, tokens, traces, or tasks attempted. Those are activity metrics. Production systems need accepted-action metrics.

A useful agent should improve over time on metrics like:

- Accepted action rate.
- Blocked risky action count.
- Cost per accepted action.
- Approval rate by tool and target.
- Evidence quality trend.
- Rollback or correction rate.

This is why AgentGuard starts with receipts. Receipts turn isolated actions into an operational dataset.

## Receipts before dashboards

Dashboards are useful after the data model is right. The first primitive should be a receipt that any framework can emit and any store can query.

An action receipt answers:

```json
{
  "agent": "repo-maintainer-agent",
  "tool": "github.comment_issue",
  "target": "owner/repo#123",
  "mode": "require_approval",
  "status": "pending_approval",
  "reasons": ["policy_passed"],
  "evidence_score": 0.82,
  "cost_usd": 0.012
}
```

The receipt is not a compliance claim. It is the minimum durable record required to audit and improve an agent.

## The design bet

AgentGuard makes one design bet:

> Probabilistic agents may propose actions. Deterministic runtime code decides how those actions cross the boundary.

That boundary should be small, composable, and framework-neutral. AgentGuard should plug into LangGraph, LiteLLM, MCP, local coding agents, or custom tool runners without replacing them.

## What this project is not

AgentGuard is not another agent loop. It is not a prompt framework. It is not an IDE. It is not a hosted governance platform.

It is a runtime kernel for agent actions:

```text
policy + evidence + approval mode + receipt + report
```

If the AI bubble produces thousands of agents, the durable layer will be the one that helps teams operate them.
