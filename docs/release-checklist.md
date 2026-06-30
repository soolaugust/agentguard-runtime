# Release Checklist

Use this checklist before publishing AgentGuard Runtime to GitHub or PyPI.

## Repository readiness

- [ ] `README.md` explains the problem, quick start, policy model, and scope.
- [ ] `LICENSE` contains the full Apache-2.0 license text.
- [ ] `CONTRIBUTING.md` explains the project boundary.
- [ ] `.github/workflows/ci.yml` runs tests and CLI smoke checks.
- [ ] `docs/research.md` cites real public demand signals.
- [ ] Private dogfood has been run against non-toy local actions, but private scenarios are not committed.
- [ ] No private paths, tokens, company names, or local-only assumptions remain.

## Validation

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/agentguard check --agent examples/agent.yaml --call examples/tool_call.json --receipts /tmp/agentguard-receipts.jsonl --cost 0.012
.venv/bin/agentguard report --agent examples/agent.yaml --receipts /tmp/agentguard-receipts.jsonl
```

## First GitHub release goals

- [ ] Publish v0.1.0 as a CLI/SDK seed, not a complete platform.
- [ ] Open three starter issues: LangGraph adapter, LiteLLM adapter, Claude/Codex CLI hook adapter.
- [ ] Write one launch post: "Stop building agents. Start operating them."
- [ ] Invite users to submit real `agent.yaml` + `tool_call.json` failure modes.

## Non-goals for v0.1.0

- No hosted service.
- No compliance certification claim.
- No replacement for Langfuse, LiteLLM, LangGraph, or OpenHands.
- No automatic execution of external actions without caller integration.
