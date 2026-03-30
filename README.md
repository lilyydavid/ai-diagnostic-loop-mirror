# squad-enhancement

Internal intelligence and ideation system for SEA ecommerce PMs. Two complementary loops that turn KPI signals into ranked, experiment-ready hypotheses and prototype bets.

## What this does

**Intelligence Loop** — 3-step diagnostic pipeline triggered by the PM.
1. **Signal** (Agent 10) — queries registered Domo KPI datasets; surfaces which metrics moved, where, by how much
2. **Triangulate** — two parallel steps:
   - (2a) Agent 11 — Domo feedback (app reviews, Love Meter, CS tickets) + Confluence UX research
   - (2b) Agent 12 — independent code review; maps FE/BE journey; designs A/B experiments; scores confidence/impact/scope
3. **Prioritise** (Agent 13) — scores experiments by C×I×S; PM approves; creates Jira stories + Confluence summary

**Inspiration Loop** — PM-triggered ideation loop that produces prototype bets.
1. **Scout** (Agent 20) — loads Agent 10 signals + browses SEA frontends + scoped market scan → PM Gate 1 (pre-mortem + prototype idea) → bet recorded
2. **Classify** (Agent 21, in design) — classifies bet as pain / shine / pain+shine
3. Agents 22–24 (in design) — prototype builder → launch validator → fit tracker

Both loops feed Agent 13: Intelligence Loop provides code-grounded experiments; Inspiration Loop provides market context and PM odds as optional enrichment.

## Markets

SG · MY · AU · NZ · PH · HK · TH · ID

---

## Trigger commands

| Command | What it does |
|---|---|
| `/intelligence-loop` | Run the full 3-step intelligence pipeline |
| `/inspiration-loop` | Run the inspiration scout and record a bet |
| `/weekly-refresh` | Background refresh of all Domo feedback datasets |

---

## Setup

### 1. Clone

```bash
git clone git@github.com:lilyydavid/squad-enhancements.git
cd squad-enhancements
```

### 2. Configure MCP credentials

Create `.mcp.json` (git-ignored). It must contain credentials for four MCP servers:
- `mcp-atlassian` — Atlassian API token → https://id.atlassian.com/manage-profile/security/api-tokens
- `domo-mcp` — Domo OAuth client_id + client_secret
- `github` — GitHub PAT (scopes: `audit_log, repo`)
- `chrome-devtools` — Chrome DevTools MCP (used by Inspiration Loop for frontend browsing)

### 3. Configure Atlassian targets

Edit `config/atlassian.yml`:
```yaml
space_name: "PI"
page_id: "your-parent-page-id"
growth_agent:
  jira_project_key: "BAAPP"
  epic_key: "BAAPP-461"
```

For personal overrides (local page IDs, test epics):
```bash
cp config/atlassian.local.yml.example config/atlassian.local.yml
```
`atlassian.local.yml` is git-ignored.

### 4. Configure Domo sources

Edit `config/domo.yml` — register all KPI datasets, pages, and cards before the agent queries them. Every source requires explicit approval before first query.

### 5. Configure local repo paths (Agent 12)

```bash
cp config/repos.local.yml.example config/repos.local.yml
```

Fill in the local clone paths for each repo Agent 12 surveys (luxola, sea-web-app, sephora-ios, etc.). `repos.local.yml` is git-ignored.

### 6. Build the Domo MCP server

The Domo MCP server source lives in `domo-mcp-server/`:

```bash
cd domo-mcp-server
npm install
npm run build
```

Point `.mcp.json → domo-mcp → command` at the built `dist/index.js` path.

---

## Directory structure

```
.claude/
  agents/          # Agent SKILL.md files (10–15, 20)
  commands/        # Slash command definitions
  rules/           # Project rules (atlassian, agents, workspace-setup)
config/
  atlassian.yml    # Global Atlassian config (committed)
  domo.yml         # Domo dataset/page/card registry (committed)
  repos.yml        # Repo metadata (committed)
  repos.local.yml  # Local clone paths (git-ignored)
domo-mcp-server/   # Domo MCP server source (build before use)
inputs/
  scope-intake/    # PM scope intake files for Agent 13
_bmad-output/
  planning-artifacts/  # PRD, architecture, product brief
```

---

## Agents

| Agent | Trigger | Role |
|---|---|---|
| 10-signal-agent | `/intelligence-loop` | Query Domo KPI sources; surface metric movements; PM gate |
| 11-feedback-agent | spawned by loop | Domo feedback triangulation (app reviews, Love Meter, CS tickets) + Confluence UXR |
| 12-validation-agent | spawned by loop | Independent code review; journey map; A/B experiment design; C/I/S scoring |
| 13-prioritisation-agent | spawned by loop | Score × rank; PM approval gate; Jira stories + Confluence summary |
| 14-weekly-refresh | `/weekly-refresh` | Background refresh of all Domo feedback datasets |
| 15-trend-escalation-agent | spawned by loop | Trend tracking; priority debt escalation for persistently unactioned hypotheses |
| 20-inspiration-scout | `/inspiration-loop` | Scout signals + SEA frontend browse + market scan + PM Gate 1 → bet log |

---

## Key design decisions

- **No assumptions** — system halts and asks at every gap; never infers
- **Code grounding** — every file path in a Jira story must appear in Agent 12's `read-audit.log`; unverified = hard block
- **Aggregation-first** — no raw rows to the LLM; SQL aggregates at DB layer; verbatim sampled to configured max
- **PII exclusion at query layer** — enforced in SQL SELECT; unverified schema = query halts
- **Memory-first** — findings store read before querying Domo; re-query only when absent or stale
- **HIL at every gate** — PM approves at signal review, evidence confirmation, and prioritisation

---

## Configuration layers

| File | Committed | Purpose |
|---|---|---|
| `config/atlassian.yml` | Yes | Shared defaults |
| `config/atlassian.team.yml` | Yes (optional) | Team-scoped overrides |
| `config/atlassian.local.yml` | No | Personal overrides |
| `config/repos.local.yml` | No | Local clone paths for Agent 12 |
| `.mcp.json` | No | MCP credentials |

---

## MCP servers

| Server | Purpose |
|---|---|
| `mcp-atlassian` | All Confluence reads/writes and Jira |
| `domo-mcp` | Domo datasets, pages, cards — built from `domo-mcp-server/` |
| `github` | Read access to `sephora-asia` org repos |
| `chrome-devtools` | Browser automation for Inspiration Loop frontend browsing |
