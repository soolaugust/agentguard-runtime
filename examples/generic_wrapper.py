from pathlib import Path

from agentguard_runtime.adapters import GovernedToolRunner
from agentguard_runtime.core import Evidence, ToolCall, load_agent_spec


SPEC = load_agent_spec(Path(__file__).with_name("agent.yaml"))


def execute_tool(call: ToolCall) -> dict:
    return {"executed": call.name, "target": call.target}


def request_approval(call: ToolCall, receipt: dict) -> dict:
    return {
        "approval_required": True,
        "tool": call.name,
        "target": call.target,
        "receipt_id": receipt["receipt_id"],
    }


runner = GovernedToolRunner(
    spec=SPEC,
    receipts_path=Path(".agentguard/generic-wrapper-receipts.jsonl"),
    executor=execute_tool,
    approval_requester=request_approval,
)

result = runner.run(
    ToolCall(
        name="github.comment_issue",
        target="owner/repo#123",
        evidence=[
            Evidence(source="github_issue", reference="owner/repo#123", confidence=0.9),
            Evidence(source="runbook", reference="triage-policy", confidence=0.8),
        ],
    ),
    cost_usd=0.004,
)

print(result)
