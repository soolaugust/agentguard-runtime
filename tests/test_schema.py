from dataclasses import asdict

from agentguard_runtime.core import AgentSpec, Evidence, ToolCall, assess_tool_call, build_report, make_receipt
from agentguard_runtime.schema import (
    load_json,
    validate_action_receipt,
    validate_approval_event,
    validate_governance_report,
    validate_outcome_event,
)


RECEIPT_SCHEMA = "spec/action_receipt.schema.json"
REPORT_SCHEMA = "spec/governance_report.schema.json"
APPROVAL_SCHEMA = "spec/approval_event.schema.json"
OUTCOME_SCHEMA = "spec/outcome_event.schema.json"


def test_valid_action_receipt_fixture_matches_schema():
    receipt = load_json("spec/fixtures/action_receipt.valid.json")

    assert validate_action_receipt(receipt, RECEIPT_SCHEMA) == []


def test_invalid_action_receipt_fixture_reports_errors():
    receipt = load_json("spec/fixtures/action_receipt.invalid.json")

    errors = validate_action_receipt(receipt, RECEIPT_SCHEMA)

    assert errors
    assert any("mode" in error for error in errors)
    assert any("evidence_score" in error for error in errors)


def test_generated_receipt_matches_schema():
    spec = AgentSpec(name="repo-agent", owner="platform", purpose="repo maintenance")
    call = ToolCall(
        name="github.search_issues",
        target="owner/repo",
        evidence=[Evidence(source="issue", reference="#1")],
    )
    decision = assess_tool_call(spec, call)
    receipt = make_receipt(spec, call, decision, cost_usd=0.01)

    assert validate_action_receipt(asdict(receipt), RECEIPT_SCHEMA) == []


def test_valid_governance_report_fixture_matches_schema():
    report = load_json("spec/fixtures/governance_report.valid.json")

    assert validate_governance_report(report, REPORT_SCHEMA) == []


def test_generated_governance_report_matches_schema():
    spec = AgentSpec(name="repo-agent", owner="platform", purpose="repo maintenance")
    call = ToolCall(
        name="github.search_issues",
        target="owner/repo",
        evidence=[Evidence(source="issue", reference="#1")],
    )
    decision = assess_tool_call(spec, call)
    receipt = make_receipt(spec, call, decision, cost_usd=0.01)
    report = build_report(spec, [receipt])

    assert validate_governance_report(asdict(report), REPORT_SCHEMA) == []


def test_valid_approval_event_fixture_matches_schema():
    event = load_json("spec/fixtures/approval_event.valid.json")

    assert validate_approval_event(event, APPROVAL_SCHEMA) == []


def test_valid_outcome_event_fixture_matches_schema():
    event = load_json("spec/fixtures/outcome_event.valid.json")

    assert validate_outcome_event(event, OUTCOME_SCHEMA) == []
