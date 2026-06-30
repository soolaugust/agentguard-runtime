# LangGraph Adapter Sketch

AgentGuard does not replace LangGraph. It wraps the tool execution boundary.

## Integration point

See `examples/langgraph_pre_tool.py` for an executable no-hard-dependency example.

Place AgentGuard immediately before a node executes a tool call:

```python
from agentguard_runtime.adapters import GovernedToolRunner
from agentguard_runtime.core import load_agent_spec

spec = load_agent_spec("agent.yaml")
runner = GovernedToolRunner(spec, ".agentguard/receipts.jsonl")


def guarded_tool_node(state):
    call = state["proposed_tool_call"]
    result = runner.run(call, cost_usd=state.get("cost_usd", 0.0))
    if result["decision"]["mode"] == "block":
        return {"status": "blocked", "guard": result}
    if result["decision"]["mode"] == "require_approval":
        return {"status": "waiting_for_approval", "guard": result}
    return {"status": "ready_to_execute", "guard": result}
```

## Why this boundary

LangGraph owns stateful orchestration. AgentGuard owns deterministic action policy and receipts. Keeping the boundary narrow makes the adapter easy to audit and easy to remove.

## Public demand signal

The initial scan found public LangGraph issues asking for approval nodes, pre-execution tool interception, governance checkpoints, and auditable completion receipts. AgentGuard's first adapter should target exactly that pre-tool-call interception point.
