from agentguard_runtime.adapters import GovernedToolRunner, from_openai_style_tool_call
from agentguard_runtime.core import AgentSpec, Evidence, ToolCall, read_receipts


def test_governed_runner_records_receipt_and_requests_approval(tmp_path):
    spec = AgentSpec(
        name="repo-agent",
        owner="platform",
        purpose="repo maintenance",
        allowed_tools=["github.comment_issue"],
        required_evidence=1,
        mode_by_risk={"high": "require_approval"},
    )
    approvals = []

    def request_approval(call, receipt):
        approvals.append((call.name, receipt["status"]))
        return {"queued": receipt["receipt_id"]}

    runner = GovernedToolRunner(spec, tmp_path / "receipts.jsonl", approval_requester=request_approval)
    result = runner.run(
        ToolCall(
            name="github.comment_issue",
            target="owner/repo#1",
            evidence=[Evidence(source="issue", reference="#1")],
        )
    )

    assert result["decision"]["mode"] == "require_approval"
    assert approvals == [("github.comment_issue", "pending_approval")]
    assert len(read_receipts(tmp_path / "receipts.jsonl")) == 1


def test_openai_style_tool_call_conversion():
    call = from_openai_style_tool_call(
        {
            "function": {"name": "filesystem.write", "arguments": {"path": "README.md"}},
            "evidence": [{"source": "plan", "reference": "step-1", "confidence": 0.8}],
        }
    )

    assert call.name == "filesystem.write"
    assert call.target == "README.md"
    assert call.evidence[0].source == "plan"
