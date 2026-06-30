from dataclasses import asdict

from agentguard_runtime.core import AgentSpec, Evidence, ToolCall, assess_tool_call, make_receipt
from agentguard_runtime.schema import load_json, validate_action_receipt


SCHEMA = "spec/action_receipt.schema.json"


def test_valid_action_receipt_fixture_matches_schema():
    receipt = load_json("spec/fixtures/action_receipt.valid.json")

    assert validate_action_receipt(receipt, SCHEMA) == []


def test_invalid_action_receipt_fixture_reports_errors():
    receipt = load_json("spec/fixtures/action_receipt.invalid.json")

    errors = validate_action_receipt(receipt, SCHEMA)

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

    assert validate_action_receipt(asdict(receipt), SCHEMA) == []
