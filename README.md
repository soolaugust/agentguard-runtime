# AgentGuard Runtime

AgentGuard Runtime is a small reliability and governance layer for AI agents. It sits before tool execution and answers five production questions:

1. Is this agent allowed to call this tool?
2. Is the target safe for this agent?
3. Does the action have enough evidence?
4. Should it run, dry-run, wait for approval, or be blocked?
5. Did the agent leave an audit receipt that can be measured later?

The goal is not to build another agent framework. The goal is to make existing agents operable.

## Why this exists

Most agent projects focus on reasoning, orchestration, IDE UX, or model routing. Real production teams also need the boring control plane: tool permissions, approval gates, cost visibility, evidence trails, receipts, liveness, and value measurement.

This repository turns that gap into a minimal runtime:

```text
agent.yaml + tool_call.json -> policy decision -> execution receipt -> governance report
```

## Quick start

```bash
python -m pip install -e '.[dev]'
agentguard check \
  --agent examples/agent.yaml \
  --call examples/tool_call.json \
  --receipts .agentguard/receipts.jsonl \
  --cost 0.012
agentguard report \
  --agent examples/agent.yaml \
  --receipts .agentguard/receipts.jsonl
agentguard scorecard \
  --agent examples/agent.yaml \
  --receipts .agentguard/receipts.jsonl

# Optional SQLite store
agentguard check \
  --agent examples/agent.yaml \
  --call examples/tool_call.json \
  --receipts .agentguard/receipts.sqlite \
  --store-format sqlite
```

Expected behavior: the sample GitHub comment is classified as a mutating action and runs as `require_approval`, while producing a JSON receipt and report.

## Python wrapper

```python
from agentguard_runtime import GovernedToolRunner, load_agent_spec

spec = load_agent_spec("examples/agent.yaml")
runner = GovernedToolRunner(spec, ".agentguard/receipts.jsonl")
result = runner.run(tool_call, cost_usd=0.012)
```

See `examples/generic_wrapper.py` and `docs/adapters/` for LangGraph, LiteLLM, and CLI hook integration sketches.

## Agent policy

```yaml
agent:
  name: repo-maintainer-agent
  owner: platform-team
  purpose: Triage repository issues and prepare low-risk maintenance changes.
  risk_level: medium
  allowed_tools:
    - github.search_issues
    - github.comment_issue
  denied_targets:
    - "*secret*"
    - "*credential*"
    - "*billing*"
  tool_risks:
    github.search_issues: low
    github.comment_issue: high
  required_evidence: 2
  mode_by_risk:
    low: allow
    medium: dry_run
    high: require_approval
    critical: block
```

## Design principles

- **Policy before execution**: a tool call is checked before anything external changes.
- **Receipts over vibes**: every decision can be written as JSONL for later audit.
- **Evidence is first-class**: weakly grounded actions are downgraded or blocked.
- **Framework-neutral**: wrap Claude Code, Codex, OpenHands, LangGraph, custom scripts, or MCP tools.
- **Small core**: deterministic code handles policy; agents handle uncertain reasoning.

## Current scope

AgentGuard Runtime is alpha software. It currently provides:

- `agent.yaml` policy loading.
- Tool allowlist and target denylist checks.
- Evidence scoring.
- Risk inference for mutating and sensitive actions.
- Execution modes: `allow`, `dry_run`, `require_approval`, `block`.
- Tamper-evident-style receipt IDs.
- Receipt-based governance reports.
- Framework-neutral `GovernedToolRunner` wrapper.
- OpenAI/MCP-like tool-call conversion helper.
- `spec/action_receipt.schema.json` for framework-neutral receipts.
- JSONL and SQLite receipt stores.
- Receipt-based metrics scorecard.
- LangGraph-style pre-tool-call example.

See `docs/architecture.md` for the runtime boundary, layer model, core objects, and long-term architecture. See `docs/metrics.md` for the measurement system that keeps the project tied to accepted value instead of activity. See `docs/stop-building-agents.md` for the project narrative.

Planned next steps:

- OpenTelemetry span attributes for governed tool calls.
- LiteLLM proxy callback example.
- Claude Code / Codex CLI hook examples.
- Cryptographic receipt signing.
- Policy bundles for OWASP AI security risks.

## Evidence that this is a real need

See `docs/research.md` for the issue-level market scan that motivated this project. The runtime was also dogfooded against private local automation boundaries before publication; those private scenarios are intentionally not included in the public repository.
