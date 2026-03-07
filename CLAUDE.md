# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains Claude Code agents for ecommerce analytics and product management work at Sephora SEA. Agents read from Confluence/Jira via MCP, process signals, and write structured outputs consumed by downstream agents.

## Architecture

### Autonomous Growth Engineer — 3-phase monthly cycle
Triggered weekly by screenshot dropped in `inputs/screenshots/`. Orchestrated by `/growth-engineer` command.

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

Outputs per phase:
- Discovery: Confluence funnel report + "Hypotheses Under Review" section
- Validation: Same page updated → "Validated Hypotheses" section (ranked, scored)
- Delivery: Same page updated → "Sprint Actions" section + Jira ticket links

State: `outputs/growth-engineer/cycle-state.json` — stores approved hypotheses per gate, resets monthly.
Reasoning: REASON() protocol applied at every hypothesis decision point (see `.claude/skills/growth-engineer.md`).

### Sub-agents (spawned by skill, or run standalone)
```
05-funnel-monitor  →  outputs/funnel-monitor/
06-market-intel    →  outputs/market-intel/
07-validation      →  outputs/validation/
08-github-reader   →  outputs/github-reader/
09-jira-writer     →  outputs/jira-writer/ + Jira BAAPP-461
```

Each agent is defined by a `SKILL.md` under `.claude/agents/<NN>-<name>/`.

## Available Agents

| Skill | Trigger | Description |
|---|---|---|
| `03-create-prd` | `/create-prd` | Generates a PRD |
| `04-user-stories` | `/user-stories` | Generates user stories |
| `05-funnel-monitor` | `/funnel-monitor` | Weekly ecommerce funnel report — Runs every Thursday, covers prior Thu→Wed |
| `06-market-intel` | `/market-intel` | SEA web + social scanner — brand sentiment, competitor activity, ecommerce trends |
| `07-validation` | `/validate-hypotheses` | Cross-references hypotheses with Confluence research + synthetic user modeling |
| `08-github-reader` | `/github-reader` | Reads sephora-asia GitHub repos to find code relevant to validated hypotheses |
| `09-jira-writer` | `/jira-writer` | Creates quick-win Jira stories (≤3 SP) and backlog stories under BAAPP-461 |

## Skills (orchestrators — run in main conversation context)

| Skill | Trigger | Description |
|---|---|---|
| `growth-engineer` | `/growth-engineer` | **3-phase cycle orchestrator** (Discovery → Validation → Delivery) — spawns agents 05–09. Drop screenshot in `inputs/screenshots/` then run |

## Key Files

- `.mcp.json` — MCP server credentials (git-ignored). Contains `mcp-atlassian` and `github` MCP configs. Base URL: `https://sephora-asia.atlassian.net`
- `config/atlassian.yml` — Global Atlassian config defaults (committed). See Config Layers below.
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
  screenshot_watch_folder: "inputs/screenshots"  # Drop + delete pattern
```

## MCP Servers

Three MCP servers are configured in `.mcp.json`:

- `mcp-atlassian` (`uvx mcp-atlassian`) — Primary. Used for all Confluence reads/writes and Jira. Use `mcp__mcp-atlassian__confluence_update_page` for Confluence writes. Auth: Basic (username + API token).
- `Atlassian` (Rovo) — OAuth-based. Use for search/fetch only. Has no Confluence write tool.
- `github` (`npx @modelcontextprotocol/server-github`) — Read access to `sephora-asia` org repos. Token scopes: `audit_log, repo`.

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
- `memory/metrics-history.json` — **append only**, never overwrite history
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
