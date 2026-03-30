# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Internal 3-step intelligence loop for SEA ecommerce PMs across all KPIs and markets (SG, MY, AU, NZ, PH, HK, TH, ID). Agents read from Domo, Confluence, and Jira via MCP, process signals, and write structured outputs consumed by downstream agents.

**Phase 1 (current) — Intelligence Loop:** PM-triggered, Domo MCP, no screenshots required.
**Phase 2 (not yet active) — Action Layer:** GitHub effort estimation + Jira story creation. Unlocked after ≥3 loops completed with ≥2/3 hypotheses actioned per loop.

## Architecture

### Phase 1 — Intelligence Loop (current)
Triggered by PM running `/intelligence-loop`. No screenshots required.

```
PM triggers /intelligence-loop
        │
  10-signal-agent          ← Step 1: KPI signal from Domo (datasets, pages, cards)
        │  PM gate
        ├──────────────────────────────┐
  11-feedback-agent            12-validation-agent
  (Domo feedback — primary)    (Confluence — secondary, skip if absent)
        └──────────────────────────────┘
                   │  PM gate
           13-prioritisation-agent    ← Step 3: dedup → score → rank → PM approves
                   │
          Prioritised hypothesis list
                   │
           15-trend-escalation-agent  ← Trend tracking + priority debt escalation

[Background — weekly]
  14-weekly-refresh  →  outputs/feedback/findings-store.json (append-only)
```

Outputs per step:
- Signal: `outputs/signal-agent/` — signal report surfaced to PM
- Feedback: `outputs/feedback/findings.md` + Confluence page 64760119298 update
- Validation: `outputs/validation/experiment-designs.json` + `experiment-designs.md`
- Prioritisation: `outputs/prioritisation/ranked-hypotheses.json` + PM approval gate
- Trend: `outputs/trend/signal-trend.json` + `trend-report.md` + Confluence escalation brief

State: `outputs/prioritisation/ranked-hypotheses.json` — append-only history across cycles.
Config: `config/domo.yml` — dataset/page/card registry, signal thresholds, query windows, PII exclusion list.

### Phase 2 — Action Layer (not yet active)
**Unlock condition:** ≥3 Intelligence Loop cycles completed with ≥2/3 hypotheses actioned per loop.

Orchestrated by `/growth-engineer` command. Screenshots dropped in `.claude/tmp-screenshots/funnel-weekly/`.

```
[Discovery — Signal Collection]
  Screenshot → 05-funnel-monitor → 06-market-intel
                    ↓                    ↓
          Confluence page update     signals.md
          (metrics + hypotheses)
                    ↓
              *** GATE 1 ***
         Human reviews Confluence
         Confirms hypotheses in chat

[Validation]
  Screenshot → 05-funnel-monitor (update) → 07-validation
                    ↓
          Confluence page update
          (validated + ranked hypotheses)
                    ↓
              *** GATE 2 ***
         Human approves Sprint Candidates
         in chat before tickets are created

[Delivery]
  Screenshot → 05-funnel-monitor (update) → 08-github-reader → 09-jira-writer
                    ↓                                               ↓
          Confluence page update                           BAAPP stories created
          (Sprint Actions + Jira links)
```

State: `outputs/growth-engineer/cycle-state.json` — stores approved hypotheses per gate, resets monthly.
Reasoning: REASON() protocol applied at every hypothesis decision point (see `.claude/skills/growth-engineer.md`).

Each agent is defined by a `SKILL.md` under `.claude/agents/<NN>-<name>/`.

## Available Agents

| Skill | Trigger | Description |
|---|---|---|
| `05-funnel-monitor` | `/funnel-monitor` | Weekly ecommerce funnel report — Runs every Thursday, covers prior Thu→Wed |
| `06-market-intel` | `/market-intel` | SEA web + social scanner — brand sentiment, competitor activity, ecommerce trends |
| `07-validation` | `/validate-hypotheses` | Cross-references hypotheses with Confluence research + synthetic user modeling |
| `08-github-reader` | `/github-reader` | Reads sephora-asia GitHub repos to find code relevant to validated hypotheses |
| `09-jira-writer` | `/jira-writer` | Creates quick-win Jira stories (≤3 SP) and backlog stories under BAAPP-461 |
| `10-signal-agent` | `/intelligence-loop` | Step 1 — queries registered Domo KPI sources; surfaces metric movements; PM gate. Hidden: `/sharpen` for first-principles coaching |
| `11-feedback-agent` | spawned by `/intelligence-loop` | Step 2a — memory-first Domo feedback triangulation (app reviews, Love Meter, CS tickets, Search Terms) + Confluence UX research search; off-signal risk flagging; writes to Confluence page 64760119298 |
| `12-validation-agent` | spawned by `/intelligence-loop` | Step 2b — surveys local codebase (PM selects repo); reads current implementation for each hypothesis; proposes FE or backend A/B test designs; scores Confidence/Impact/Scope from code evidence; writes `experiment-designs.json` + `experiment-designs.md` for Agent 13 |
| `13-prioritisation-agent` | spawned by `/intelligence-loop` | Step 3 — scores each failure on Confidence (from Agent 12) × Impact (Domo `29a01e0e`, PM-gated) × Scope (PM scope-intake file, Agent 08 optional enrichment); ranks by priority score; PM approval gate before Jira handoff; tracks failure lineage across cycles |
| `14-weekly-refresh` | `/weekly-refresh` | Background — refreshes findings store for all registered feedback datasets |
| `15-trend-escalation-agent` | spawned by `/intelligence-loop` after Agent 13 | Tracks confidence and priority score trends across cycles; calculates priority debt (impact × confidence × cycles unactioned); escalates persistently ignored failures to PM via Confluence brief; no GMV assumptions |

## Skills (orchestrators — run in main conversation context)

| Skill | Trigger | Description |
|---|---|---|
| `intelligence-loop` | `/intelligence-loop` | **Phase 1 orchestrator** — runs agents 10 → 11+12 → 13 → 15 with PM gates at each step |
| `growth-engineer` | `/growth-engineer` | **Phase 2 orchestrator** (Discovery → Validation → Delivery) — spawns agents 05–09. Drop screenshot in `.claude/tmp-screenshots/funnel-weekly/` then run |

## Key Files

- `.mcp.json` — MCP server credentials (git-ignored). Contains `mcp-atlassian`, `github`, `domo-mcp`, and `chrome-devtools` MCP configs. Base URL: `https://sephora-asia.atlassian.net`
- `config/atlassian.yml` — Global Atlassian config defaults (committed). See Config Layers below.
- `config/domo.yml` — Domo dataset/page/card registry, signal thresholds, PII exclusion list (committed).
- `.claude/rules/` — Project rules applied per context (atlassian, agents, workspace-setup)
- `outputs/<agent-name>/` — All agent-generated files live here

## Config Layers

Agent config is resolved in priority order — later layers override earlier ones:

| File | Level | Committed? | Purpose |
|---|---|---|---|
| `config/atlassian.yml` | Global | Yes | Shared defaults for all users |
| `config/atlassian.team.yml` | Team | Yes (optional) | Team-scoped overrides (e.g. different Jira project) |
| `config/atlassian.local.yml` | Local | No (git-ignored) | Personal overrides (test epics, sandbox pages) |

To create a local override: `cp config/atlassian.local.yml.example config/atlassian.local.yml`

### Growth agent config (in `atlassian.yml`)
```yaml
growth_agent:
  jira_project_key: "BAAPP"
  epic_key: "BAAPP-461"                  # Stories created as children of this epic
  epic_summary: "Growth Agent tasks"
  story_labels: ["growth-agent", "quick-win"]
  backlog_label: "growth-backlog"
  screenshot_watch_folder: ".claude/tmp-screenshots/funnel-weekly"  # Drop + delete pattern
```

## MCP Servers

Four MCP servers are configured in `.mcp.json`:

- `mcp-atlassian` (`uvx mcp-atlassian`) — Primary. Used for all Confluence reads/writes and Jira. Use `mcp__mcp-atlassian__confluence_update_page` for Confluence writes. Auth: Basic (username + API token).
- `Atlassian` (Rovo) — OAuth-based. Use for search/fetch only. Has no Confluence write tool.
- `github` (`npx @modelcontextprotocol/server-github`) — Read access to `sephora-asia` org repos. Token scopes: `audit_log, repo`.
- `domo-mcp` (node `dist/index.js`) — Domo MCP server. `data` scope for datasets; `dashboard` scope for pages/cards. Use `get-dashboard-signals` for page sources — NOT `get-page-cards` or `get-card` alone (those return metadata only, not live values). All sources must be registered in `config/domo.yml` before querying.

Prefer `mcp__mcp-atlassian__*` for all Atlassian operations. If write returns 401, the MCP server needs a restart (token rotation requires server restart to pick up new credentials).

## Agent Conventions

### Adding an agent
1. Create `.claude/agents/<NN>-<name>/SKILL.md` with: Role in pipeline, Trigger, Agent Steps, Output Contract, Configuration, Permissions, Error Handling.
2. Register in the agents table above.

### SKILL.md must include
- Explicit output contract: file paths, formats, `overwrite` vs `append` behavior
- Suspicious metric filter rule before writing any outputs
- Error handling for every failure mode (404, 401, missing data)

### Output contract conventions
- `pipeline-context.md`, `validation-hypotheses.md`, `lno.md` — **overwrite** each run
- `memory/metrics-history.json`, `findings-store.json`, `ranked-hypotheses.json` — **append only**, never overwrite history
- No source attribution in stakeholder-facing Confluence pages
- Suspicious metrics (YoY >50% with no known cause, value = 0%, identical across all segments) go to Data Quality Notes only — excluded from all tables and risk register

### Confluence image extraction
- Download attachments via `/wiki/rest/api/content/{pageId}/child/attachment?limit=50&expand=version`
- Filter to only attachments where `version.when` starts with current month (`YYYY-MM`)
- Download with `curl -L` to follow redirects
- Confidence: High = value + label + date range all readable; Medium = value readable; Low = skip

## Rules

- **atlassian** — Confluence/Jira permission boundaries. May write only to configured `page_id`. Token rotation: https://id.atlassian.com/manage-profile/security/api-tokens
- **agents** — Skill file structure and output file conventions
- **workspace-setup** — Onboarding a new team or Atlassian space
