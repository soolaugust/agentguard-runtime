from agentguard_runtime.core import AgentSpec, Evidence, ToolCall, assess_tool_call, build_report, make_receipt
from agentguard_runtime.stores import JsonlReceiptStore, SQLiteReceiptStore, open_receipt_store


def _receipt():
    spec = AgentSpec(name="repo-agent", owner="platform", purpose="repo maintenance")
    call = ToolCall(
        name="github.search_issues",
        target="owner/repo",
        evidence=[Evidence(source="issue", reference="#1")],
    )
    decision = assess_tool_call(spec, call)
    return spec, make_receipt(spec, call, decision, cost_usd=0.02)


def test_jsonl_receipt_store_roundtrip(tmp_path):
    spec, receipt = _receipt()
    store = JsonlReceiptStore(tmp_path / "receipts.jsonl")

    store.append(receipt)
    report = build_report(spec, store.read_all())

    assert report.receipt_count == 1
    assert report.total_cost_usd == 0.02


def test_sqlite_receipt_store_roundtrip(tmp_path):
    spec, receipt = _receipt()
    store = SQLiteReceiptStore(tmp_path / "receipts.sqlite")

    store.append(receipt)
    report = build_report(spec, store.read_all())

    assert report.receipt_count == 1
    assert report.total_cost_usd == 0.02


def test_open_receipt_store_selects_backend(tmp_path):
    assert isinstance(open_receipt_store(tmp_path / "receipts.jsonl"), JsonlReceiptStore)
    assert isinstance(open_receipt_store(tmp_path / "receipts.sqlite", "sqlite"), SQLiteReceiptStore)
