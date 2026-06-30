import importlib.util
from pathlib import Path


def _load_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "examples" / "langgraph_pre_tool.py"
    spec = importlib.util.spec_from_file_location("langgraph_pre_tool_example", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_langgraph_pre_tool_example_routes_approval(tmp_path, monkeypatch):
    module = _load_example(tmp_path, monkeypatch)

    result = module.guarded_tool_node(
        {
            "cost_usd": 0.01,
            "proposed_tool_call": {
                "function": {
                    "name": "github.comment_issue",
                    "arguments": {"target": "owner/repo#123"},
                },
                "evidence": [
                    {"source": "issue", "reference": "owner/repo#123", "confidence": 1.0},
                    {"source": "policy", "reference": "runbook", "confidence": 1.0},
                ],
            },
        }
    )

    assert result["next"] == "approval"
    assert result["agentguard"]["receipt"]["status"] == "pending_approval"


def test_langgraph_pre_tool_example_routes_block(tmp_path, monkeypatch):
    module = _load_example(tmp_path, monkeypatch)

    result = module.guarded_tool_node(
        {
            "proposed_tool_call": {
                "function": {
                    "name": "git.open_pr",
                    "arguments": {"target": "services/billing/config.py"},
                },
                "evidence": [
                    {"source": "scan", "reference": "path", "confidence": 1.0},
                    {"source": "policy", "reference": "denylist", "confidence": 1.0},
                ],
            },
        }
    )

    assert result["next"] == "blocked"
    assert result["agentguard"]["receipt"]["status"] == "blocked"
