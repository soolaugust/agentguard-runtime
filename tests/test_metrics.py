from agentguard_runtime.core import ExecutionReceipt, GovernanceReport
from agentguard_runtime.metrics import build_scorecard, render_markdown_summary


def _receipt(status, evidence_score=0.8, cost=0.1):
    return ExecutionReceipt(
        receipt_id=f"r-{status}-{cost}",
        agent="repo-agent",
        tool="github.comment_issue",
        target="owner/repo#1",
        mode="require_approval",
        status=status,
        reasons=["policy_passed"],
        evidence_score=evidence_score,
        cost_usd=cost,
    )


def test_scorecard_counts_receipt_statuses():
    scorecard = build_scorecard(
        "repo-agent",
        [
            _receipt("executed", cost=0.01),
            _receipt("dry_run", cost=0.02),
            _receipt("pending_approval", cost=0.03),
            _receipt("blocked", cost=0.04),
        ],
    )

    assert scorecard.proposed_actions == 4
    assert scorecard.executed_count == 1
    assert scorecard.dry_run_count == 1
    assert scorecard.approval_required_count == 1
    assert scorecard.blocked_count == 1
    assert scorecard.total_cost_usd == 0.1
    assert scorecard.approval_burden_rate == 0.25
    assert scorecard.blocked_action_rate == 0.25


def test_scorecard_no_data_state():
    scorecard = build_scorecard("repo-agent", [])

    assert scorecard.control_state == "no_data"
    assert scorecard.proposed_actions == 0


def test_scorecard_flags_weak_evidence_before_noise():
    scorecard = build_scorecard("repo-agent", [_receipt("blocked", evidence_score=0.1)])

    assert scorecard.control_state == "weak_evidence"


def test_scorecard_flags_review_heavy():
    scorecard = build_scorecard(
        "repo-agent",
        [_receipt("pending_approval"), _receipt("pending_approval"), _receipt("executed")],
    )

    assert scorecard.control_state == "review_heavy"


def test_markdown_summary_is_human_readable():
    report = GovernanceReport(
        agent="repo-agent",
        alive=True,
        value_state="measurable",
        risk_state="approval_gated",
        receipt_count=1,
        approval_required_count=1,
        blocked_count=0,
        total_cost_usd=0.012,
        evidence_score_avg=0.8,
    )
    scorecard = build_scorecard("repo-agent", [_receipt("pending_approval", cost=0.012)])

    summary = render_markdown_summary(report, scorecard)

    assert "# AgentGuard Summary — repo-agent" in summary
    assert "## Verdict" in summary
    assert "Approval burden rate" in summary
    assert "review-heavy" in summary
