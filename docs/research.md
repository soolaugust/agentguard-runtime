# Research Notes: Agent Reliability and Governance Demand Signals

This project started from a simple question: are agent reliability and governance real open-source needs, or just a plausible story?

The initial scan looked at mature AI infrastructure and agent repositories. The signal is not that one project is missing one feature. The signal is that similar pain appears across different layers: observability, model gateways, agent orchestration, and developer agents.

## Observed demand signals

### Langfuse

Langfuse already covers LLM tracing, evaluation, prompt management, datasets, and observability. Open issues still show adjacent needs around governed tool calls, runtime enforcement, provenance, cost accuracy, and long-running agent drift.

Representative public issues found during the scan:

- `langfuse/langfuse#14139` — trace attributes for governed agent tool calls.
- `langfuse/langfuse#13676` — inline OPA/Rego enforcement proxy for runtime tool execution paths.
- `langfuse/langfuse#12907` — trust scores and source provenance on traced generations.
- `langfuse/langfuse#12873` — session-boundary behavioral drift monitoring across long-running agents.
- `langfuse/langfuse#12635` and `#14249` — accurate Anthropic cache-read/cache-write cost tracking.

Interpretation: tracing is necessary but not sufficient. Teams also want policy, provenance, and cost correctness at the tool/action boundary.

### LiteLLM

LiteLLM is a strong model gateway and proxy. Its issue tracker shows repeated needs around budget enforcement, actual usage cost, sandboxing, identity headers, and audit trails.

Representative public issues found during the scan:

- `BerriAI/litellm#26672` — budget enforcement bypassed despite spend exceeding max budget.
- `BerriAI/litellm#30816` — report actual usage cost to SSE clients in streaming mode.
- `BerriAI/litellm#24904` — agent identity headers for LiteLLM proxy.
- `BerriAI/litellm#29895` — post-call receipt middleware for tamper-evident audit trails.
- `BerriAI/litellm#30891` — route code execution to a self-hosted sandbox.

Interpretation: model gateways are becoming control planes. Agent governance needs a small action-level receipt and policy layer that can plug into gateways without replacing them.

### LangGraph

LangGraph is a stateful agent orchestration framework. Its public issues show demand for approval nodes, policy interception, governance checkpoints, auditable receipts, deterministic subflows, and production human-in-the-loop patterns.

Representative public issues found during the scan:

- `langchain-ai/langgraph#8026` — high-level ApprovalNode for human-in-the-loop workflows.
- `langchain-ai/langgraph#8102` — pre-execution tool call interception hooks for policy enforcement.
- `langchain-ai/langgraph#7303` — trust-gated checkpoints and governance nodes.
- `langchain-ai/langgraph#7844` — auditable final-state receipts for agent completion claims.
- `langchain-ai/langgraph#8032` — when repeated agent paths should become deterministic subflows.

Interpretation: orchestration frameworks need reusable governance patterns, but should not be forced to own all policy semantics themselves.

### OpenHands and AI coding agents

OpenHands and similar developer agents focus on execution environments, coding tasks, and automation. The governance gap appears less as a single missing feature and more as an operational question: how do teams approve, audit, budget, and measure autonomous coding actions across tools?

Interpretation: coding agents need a framework-neutral runtime boundary that can be placed before filesystem, GitHub, CI, deployment, ticketing, or notification actions.

## Product thesis

The durable open-source opportunity is not another agent loop. It is an agent operations layer:

```text
before action: policy + evidence + risk
at action: mode decision + approval gate
after action: receipt + cost + value signal
later: liveness + drift + usefulness report
```

## What AgentGuard Runtime should not do

- It should not replace LangGraph, OpenHands, LiteLLM, or Langfuse.
- It should not claim full compliance or safety certification.
- It should not require a specific LLM provider or agent framework.
- It should not make probabilistic safety claims without deterministic receipts.

## Initial wedge

The first useful wedge is a CLI/SDK that wraps tool calls and produces receipts. This is small enough to adopt and concrete enough to validate:

1. Define `agent.yaml`.
2. Pass each proposed tool call through AgentGuard.
3. Execute only if the returned mode allows it.
4. Store JSONL receipts.
5. Report alive/value/risk/cost from receipts.

That creates a bridge from demo agents to operable agents.
