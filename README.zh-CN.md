# AgentGuard Runtime

[English](README.md)

AgentGuard Runtime 是一个面向 AI Agent 的运行时治理内核。它不负责让 Agent 更会“思考”，而是负责在 Agent 真正调用工具、修改外部状态之前，回答几个生产系统必须回答的问题：

1. 这个 Agent 有权限调用这个工具吗？
2. 这个目标资源安全吗？
3. 这个动作有没有足够证据支撑？
4. 这个动作应该自动执行、dry-run、等待审批，还是直接阻断？
5. 这个动作有没有留下可审计、可度量的收据？

项目目标不是再造一个 Agent 框架，而是让已有 Agent 更可运行、更可审计、更可衡量。

## 为什么需要它

现在 AI 生态里已经有很多强组件：

- Agent 框架负责规划和编排。
- AI IDE 负责开发者交互。
- LLM Gateway 负责模型路由和成本入口。
- Observability 工具负责 trace 和监控。
- MCP / tool protocol 负责把模型接到工具。

但生产落地时还有一个关键边界经常缺失：

```text
Agent 提议动作 -> 运行时检查 policy/evidence/risk -> 写入 action receipt -> 执行/审批/阻断
```

没有这个边界，团队很难回答：

- 谁批准了这个动作？
- 为什么允许它执行？
- 它依据了什么证据？
- 它花了多少钱？
- 哪些动作被阻断？
- 这些动作最终真的有价值吗？

AgentGuard 从这个边界开始做。

## 快速开始

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

agentguard summary \
  --agent examples/agent.yaml \
  --receipts .agentguard/receipts.jsonl \
  --language zh \
  --output .agentguard/reports/example-summary.zh.md
```

如果想用 SQLite 存储收据：

```bash
agentguard check \
  --agent examples/agent.yaml \
  --call examples/tool_call.json \
  --receipts .agentguard/receipts.sqlite \
  --store-format sqlite \
  --cost 0.012

agentguard scorecard \
  --agent examples/agent.yaml \
  --receipts .agentguard/receipts.sqlite \
  --store-format sqlite
```

## Agent 策略示例

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

这个配置表达的是：

- `github.search_issues` 是低风险动作，可以自动放行。
- `github.comment_issue` 是外部写动作，属于高风险，需要审批。
- 命中 secret / credential / billing 等目标时应被阻断。
- 每个动作至少需要 2 条证据。

## 输出长什么样

`agentguard summary --language zh` 会生成面向人读的 Markdown 报告，例如：

```markdown
# AgentGuard 摘要报告 — repo-maintainer-agent

## 结论

Agent 已被运行时控制住，但审批负担偏高。自动执行前应先提高证据质量或缩小高风险动作范围。

## 治理报告

| 字段 | 数值 |
| --- | --- |
| 是否有数据 | `True` |
| 价值状态 | `可衡量` |
| 风险状态 | `审批门控` |
| 收据数量 | `1` |
| 需要审批 | `1` |
| 已阻断 | `0` |
| 总成本 | `$0.012000` |
| 平均证据分 | `0.797` |

## 指标看板

| 指标 | 数值 |
| --- | --- |
| 提议动作数 | `1` |
| 已执行 | `0` |
| 待审批 | `1` |
| 已阻断 | `0` |
| 审批负担率 | `100.0%` |
| 阻断率 | `0.0%` |
| 平均证据质量 | `0.797` |
| 控制状态 | `审批负担偏高` |
```

完整示例见 `docs/example-report.md`。

## 当前能力

AgentGuard Runtime 当前提供：

- `agent.yaml` 策略加载。
- 工具 allowlist 和目标 denylist 检查。
- 显式 `tool_risks` 风险声明。
- 证据评分。
- 执行模式：`allow`、`dry_run`、`require_approval`、`block`。
- Action Receipt 收据。
- Governance Report 治理报告。
- Metrics Scorecard 指标看板。
- 中文 / 英文 Markdown summary 报告。
- JSONL 和 SQLite 收据存储。
- LangGraph 风格 pre-tool-call 示例。
- OpenAI/MCP-like tool-call 转换 helper。

## 核心指标

AgentGuard 不优化“调用量”，而优化 Agent 动作的运行质量。

关键指标包括：

- `accepted_action_rate`：被接受的动作比例。
- `approval_burden_rate`：需要人工审批的动作比例。
- `blocked_risky_action_rate`：被阻断的风险动作比例。
- `evidence_quality_avg`：平均证据质量。
- `cost_per_accepted_action`：每个被接受动作的成本。
- `rework_rate`：后续需要返工、回滚或修正的比例。

更完整的指标体系见 `docs/metrics.md`。

## 重要边界

v0.1 目前能证明的是：

- Agent 动作是否经过运行时边界。
- 策略是否生效。
- 风险动作是否被审批或阻断。
- 动作是否留下收据。
- 成本和证据质量是否可度量。

v0.1 还不能证明：

- 动作最终是否产生业务价值。
- 人类是否接受了这个动作。
- 动作是否被回滚或返工。

这些需要后续接入 `ApprovalEvent` 和 `OutcomeEvent`。

## 设计原则

- **Policy before execution**：执行前先过策略边界。
- **Receipts over vibes**：不要凭感觉说 Agent 有用，要留下收据。
- **Evidence-gated action**：弱证据不自动行动。
- **Framework-neutral**：不绑定 LangGraph、LiteLLM、MCP、Claude Code 或 Codex CLI。
- **Small deterministic core**：概率性推理交给 Agent，确定性边界交给代码。

## 文档入口

- `docs/architecture.md`：整体架构与 runtime boundary。
- `docs/metrics.md`：指标体系。
- `docs/example-report.md`：具体报告示例。
- `docs/stop-building-agents.md`：项目叙事。
- `docs/adapters/`：适配器草图。
- `docs/roadmap.md`：路线图。

## 非目标

AgentGuard 不是：

- 另一个 Agent loop。
- Prompt 框架。
- AI IDE。
- 托管合规平台。
- LangGraph / LiteLLM / Langfuse / OpenHands / MCP 的替代品。

它只做一件事：

> 让 Agent 从“想做动作”到“真的执行动作”之间，有一个可控、可审计、可度量的运行时边界。
