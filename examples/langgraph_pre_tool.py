from pathlib import Path
from typing import Any

from agentguard_runtime.adapters import GovernedToolRunner, from_openai_style_tool_call
from agentguard_runtime.core import load_agent_spec


spec = load_agent_spec(Path(__file__).with_name("agent.yaml"))
runner = GovernedToolRunner(spec, Path(".agentguard/langgraph-receipts.jsonl"))


def guarded_tool_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph-style pre-tool-call node.

    This function intentionally has no hard LangGraph dependency. In a real graph,
    call it immediately before the node that executes a tool.
    """
    call = from_openai_style_tool_call(state["proposed_tool_call"])
    result = runner.run(call, cost_usd=float(state.get("cost_usd", 0.0)))
    mode = result["decision"]["mode"]
    if mode == "block":
        return {**state, "agentguard": result, "next": "blocked"}
    if mode == "require_approval":
        return {**state, "agentguard": result, "next": "approval"}
    if mode == "dry_run":
        return {**state, "agentguard": result, "next": "dry_run"}
    return {**state, "agentguard": result, "next": "execute"}


if __name__ == "__main__":
    output = guarded_tool_node(
        {
            "cost_usd": 0.012,
            "proposed_tool_call": {
                "function": {
                    "name": "github.comment_issue",
                    "arguments": {"target": "owner/repo#123", "body": "Triage summary"},
                },
                "evidence": [
                    {"source": "issue", "reference": "owner/repo#123", "confidence": 0.95},
                    {"source": "policy", "reference": "triage-runbook", "confidence": 0.9},
                ],
            },
        }
    )
    print(output["next"])
    print(output["agentguard"]["receipt"]["status"])
