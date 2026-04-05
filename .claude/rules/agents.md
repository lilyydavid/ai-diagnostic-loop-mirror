---
description: Apply when adding a new agent, running a skill, or working inside the .claude/skills/ directory
---

# Agent Conventions

## Adding an agent

1. Decide scope: is this agent used by one project (→ `projects/{loop}/agents/`) or multiple projects (→ `shared/agents/`)?
2. Create a new directory with a numeric prefix (e.g. `projects/intelligence-loop/agents/16-my-agent/`).
3. Add `SKILL.md` (index card), `POLICY.md` (contracts + permissions + error handling), and `PROCEDURE.md` (step-by-step execution).
4. Register the agent in `config/agents.yml` under the correct project or shared key.
5. Add a row to the relevant agent table in `CLAUDE.md`.

## Skill file structure

Each `SKILL.md` should include:

- **Role in pipeline** — position relative to other agents and data flow
- **Trigger** — slash command or natural language phrases that activate the skill
- **Agent Steps** — numbered, deterministic steps
- **Output Contract** — exact file paths, formats, and append vs overwrite behavior
- **Configuration** — relevant `config/` keys
- **Permissions** — what the agent may read and write
- **Error Handling** — explicit fallback for every failure mode

## Output files

All agent outputs go under `outputs/<agent-name>/`. Overwrite pipeline context files on each run. Never overwrite history/append-only files — only append.

### Canonical overwrite/append list

**Overwrite each run:**
`pipeline-context.md`, `validation-hypotheses.md`, `lno.md`, `experiment-designs.json`, `experiment-designs.md`, `ranked-hypotheses.md`, `needs-spike.md`, `signal-trend.json`, `trend-report.md`, `cycle-state.json`

**Append only — never overwrite:**
`metrics-history.json`, `findings-store.json`, `ranked-hypotheses.json`, `bet-log.json`

### Stakeholder output rules

- No source attribution in stakeholder-facing Confluence pages.
- Suspicious metrics (YoY >50% with no known cause, value = 0%, identical across all segments) go to Data Quality Notes only — excluded from all tables and risk register. Use `execution/flag_suspicious_metrics.py` for deterministic flagging.
