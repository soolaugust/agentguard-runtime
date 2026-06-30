# LiteLLM Adapter Sketch

LiteLLM is a model gateway. AgentGuard should not sit in the token path unless needed. The most useful integration is at the agent/tool boundary where model output becomes an action.

## Integration options

1. Add AgentGuard receipt metadata to proxy logs after a tool decision.
2. Use LiteLLM spend data as `cost_usd` when recording receipts.
3. Add agent identity headers to connect model usage with action receipts.

## Minimal pattern

```python
from agentguard_runtime.adapters import from_openai_style_tool_call, GovernedToolRunner
from agentguard_runtime.core import load_agent_spec

spec = load_agent_spec("agent.yaml")
runner = GovernedToolRunner(spec, ".agentguard/receipts.jsonl")


def on_tool_call(raw_tool_call, usage_cost_usd):
    call = from_openai_style_tool_call(raw_tool_call)
    return runner.run(call, cost_usd=usage_cost_usd)
```

## Public demand signal

The initial scan found public LiteLLM issues around budget enforcement, actual streaming cost reporting, agent identity headers, sandboxed code execution, and audit-trail middleware. AgentGuard should complement LiteLLM by producing action-level receipts that can be joined with gateway cost data.
