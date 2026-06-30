from agentguard_runtime.core import (
    AgentSpec,
    Evidence,
    ToolCall,
    assess_tool_call,
    build_report,
    load_agent_spec,
    make_receipt,
    read_receipts,
    record_receipt,
)


def test_allowed_mutating_tool_requires_approval_with_strong_evidence():
    spec = AgentSpec(
        name="repo-agent",
        owner="platform",
        purpose="repo maintenance",
        risk_level="medium",
        allowed_tools=["github.comment_issue"],
        required_evidence=2,
        mode_by_risk={"medium": "dry_run", "high": "require_approval"},
    )
    call = ToolCall(
        name="github.comment_issue",
        target="owner/repo#1",
        evidence=[
            Evidence(source="issue", reference="#1", confidence=0.9),
            Evidence(source="log", reference="trace", confidence=0.9),
        ],
    )

    decision = assess_tool_call(spec, call)

    assert decision.allowed is True
    assert decision.mode == "require_approval"
    assert decision.evidence_score > 0.5


def test_denied_target_blocks_even_when_tool_is_allowed():
    spec = AgentSpec(
        name="repo-agent",
        owner="platform",
        purpose="repo maintenance",
        allowed_tools=["git.open_pr"],
        denied_targets=["*billing*"],
    )
    call = ToolCall(name="git.open_pr", target="services/billing/config.py")

    decision = assess_tool_call(spec, call)

    assert decision.allowed is False
    assert decision.mode == "block"
    assert "target_denied:*billing*" in decision.reasons


def test_load_agent_spec_from_yaml():
    spec = load_agent_spec("examples/agent.yaml")

    assert spec.name == "repo-maintainer-agent"
    assert "github.comment_issue" in spec.allowed_tools
    assert spec.required_evidence == 2


def test_receipts_build_governance_report(tmp_path):
    spec = AgentSpec(
        name="repo-agent",
        owner="platform",
        purpose="repo maintenance",
        allowed_tools=["github.comment_issue"],
        required_evidence=1,
    )
    call = ToolCall(
        name="github.comment_issue",
        target="owner/repo#1",
        evidence=[Evidence(source="issue", reference="#1", confidence=1.0)],
    )
    decision = assess_tool_call(spec, call)
    receipt = make_receipt(spec, call, decision, cost_usd=0.01)
    store = tmp_path / "receipts.jsonl"

    record_receipt(receipt, store)
    report = build_report(spec, read_receipts(store))

    assert report.alive is True
    assert report.receipt_count == 1
    assert report.total_cost_usd == 0.01
    assert report.evidence_score_avg > 0.5


def test_unknown_tool_is_blocked_by_allowlist():
    spec = AgentSpec(
        name="repo-agent",
        owner="platform",
        purpose="repo maintenance",
        allowed_tools=["github.search_issues"],
    )

    decision = assess_tool_call(spec, ToolCall(name="github.delete_repo", target="owner/repo"))

    assert decision.mode == "block"
    assert decision.allowed is False
    assert "tool_not_allowed:github.delete_repo" in decision.reasons


def test_weak_evidence_downgrades_allow_to_dry_run():
    spec = AgentSpec(
        name="read-agent",
        owner="platform",
        purpose="read-only inspection",
        risk_level="low",
        allowed_tools=["github.search_issues"],
        required_evidence=2,
        mode_by_risk={"low": "allow"},
    )

    decision = assess_tool_call(spec, ToolCall(name="github.search_issues", target="owner/repo"))

    assert decision.mode == "dry_run"
    assert any(reason.startswith("weak_evidence") for reason in decision.reasons)


def test_tool_risk_overrides_default_risk_level():
    spec = AgentSpec(
        name="local-agent",
        owner="platform",
        purpose="local automation",
        risk_level="medium",
        allowed_tools=["dashboard.view_artifact"],
        tool_risks={"dashboard.view_artifact": "low"},
        mode_by_risk={"low": "allow", "medium": "dry_run"},
        required_evidence=1,
    )
    call = ToolCall(
        name="dashboard.view_artifact",
        target="docs/report.md",
        evidence=[Evidence(source="route", reference="allowlist")],
    )

    decision = assess_tool_call(spec, call)

    assert decision.mode == "allow"
    assert decision.risk_level == "low"


def test_denied_target_checks_url_inside_args():
    spec = AgentSpec(
        name="local-agent",
        owner="platform",
        purpose="local automation",
        allowed_tools=["dashboard.view_artifact"],
        denied_targets=["https://*.feishu.cn/*"],
    )
    call = ToolCall(
        name="dashboard.view_artifact",
        args={"url": "https://team.feishu.cn/wiki/example"},
        evidence=[Evidence(source="rule", reference="feishu")],
    )

    decision = assess_tool_call(spec, call)

    assert decision.mode == "block"
    assert "target_denied:https://*.feishu.cn/*" in decision.reasons


def test_over_budget_report_marks_value_state(tmp_path):
    spec = AgentSpec(
        name="repo-agent",
        owner="platform",
        purpose="repo maintenance",
        cost_budget_usd=0.01,
    )
    call = ToolCall(name="github.search_issues", evidence=[Evidence(source="issue", reference="#1")])
    decision = assess_tool_call(spec, call)
    store = tmp_path / "receipts.jsonl"

    record_receipt(make_receipt(spec, call, decision, cost_usd=0.02), store)
    report = build_report(spec, read_receipts(store))

    assert report.value_state == "over_budget"
