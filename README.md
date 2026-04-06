# AI diagnostic loop

AI-assisted PM diagnostic tool for SEA ecommerce teams. Two complementary loops that turn KPI signals into ranked, experiment-ready hypotheses and prototype bets — across SG, MY, AU, NZ, PH, HK, TH, and ID.

---

## How it works

The system uses a **3-layer architecture** that separates intent from execution:

- **Layer 1 — Directives** (`directives/`, agent `SKILL.md` files): SOPs in Markdown — what to do, in what order, and how to handle edge cases
- **Layer 2 — Orchestration** (Claude): reads directives, routes to execution scripts, handles errors, asks for clarification
- **Layer 3 — Execution** (`execution/`): deterministic Python scripts — API calls, data processing, file I/O

LLMs handle decision-making. Scripts handle computation. This separation prevents error compounding.

---

## Loops

### Intelligence Loop

4-step diagnostic pipeline triggered by `/intelligence-loop`.

1. **Signal**  — queries Domo KPI datasets; surfaces which metrics moved, where, by how much; PM reviews and approves
2. **Diagnose** — two parallel sub-steps:
   - (2a) **Feedback** — DWH feedback triangulation (app reviews, NPS, CS tickets) + Confluence UX research
   - (2b) **Validation** — independent codebase survey; localises the failure mechanism; designs A/B experiments
3. **Prioritise**  — scores experiments C×I×S; PM approves; produces Jira stories + Confluence summary
4. **Escalate** (Agent 15) — tracks priority debt; escalates persistently unactioned hypotheses

### Inspiration Loop

PM-triggered ideation loop triggered by `/inspiration-loop`.

1. **Scout**  — loads signals + browses SEA frontends + scoped market scan → PM Gate 1 (pre-mortem + prototype idea) → bet recorded with target metric and odds


Both loops feed prioritise step: the Intelligence Loop provides a diagnosis artifact plus code-grounded experiment designs; the Inspiration Loop provides market context and PM odds as optional enrichment for scoring.

---

## Trigger commands

| Command | What it does |
|---|---|
| `/intelligence-loop` | Run the full 4-step intelligence pipeline |
| `/inspiration-loop` | Run the inspiration scout and record a bet |
| `/weekly-refresh` | Background refresh of all Domo feedback datasets |

---

## Setup

### 1. Clone

```bash
git clone https://github.com/lilyydavid/product-experiments.git
cd product-experiments
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure MCP credentials

Create `.mcp.json` (git-ignored). It must contain credentials for four MCP servers:

### 4. Configure Atlassian targets

Edit `config/atlassian.yml`:
```yaml
```

For personal overrides (local page IDs, test epics):
```bash
cp config/atlassian.local.yml.example config/atlassian.local.yml
```
`atlassian.local.yml` is git-ignored.

### 5. Configure DWH sources

Edit `config/dwh.yml` — register all KPI datasets, pages, and cards before running the agent. Every source requires explicit registration before first query.

### 6. Configure local repo paths 

```bash
cp config/repos.local.yml.example config/repos.local.yml
```

Fill in the local clone paths for each repo Agent 12 surveys. `repos.local.yml` is git-ignored.

### 7. Build the Domo MCP server

```bash
cd domo-mcp-server
npm install
npm run build
```

Point `.mcp.json → domo-mcp → command` at the built `dist/index.js` path.

---

## Directory structure

```
config/
  agents.yml          # Agent registry — all agent paths resolved from here
  atlassian.yml       # Global Atlassian config (committed)
  domo.yml            # Domo dataset/page/card registry (committed)
  repos.yml           # Repo metadata (committed)
  repos.local.yml     # Local clone paths (git-ignored)
directives/           # SOPs for execution scripts and operational procedures
execution/            # Deterministic Python scripts (Layer 3)
projects/
  intelligence-loop/agents/   # Agents 10–12, 15
  inspiration-loop/agents/    # Agent 20
  action-layer/agents/        # Agents 05–09 (not yet active)
shared/
  agents/                     # Agents 13–14 (used by multiple loops)
outputs/              # Agent-generated files (operational data)
domo-mcp-server/      # Domo MCP server source (build before use)
.claude/
  rules/              # Auto-loaded context rules
  skills/             # Skill orchestrators (intelligence-loop, inspiration-loop)
```

---

## Agents

**Intelligence Loop** (`projects/intelligence-loop/agents/`):

| Agent | Trigger | Role |
|---|---|---|
| 10-signal-agent | `/intelligence-loop` | Query Domo KPI sources; surface metric movements; PM gate |
| 11-feedback-agent | spawned by loop | Domo feedback triangulation + Confluence UXR |
| 12-validation-agent | spawned by loop | Codebase survey; mechanism localisation; A/B experiment design |
| 15-trend-escalation-agent | spawned by loop | Priority debt tracking and escalation |

**Inspiration Loop** (`projects/inspiration-loop/agents/`):

| Agent | Trigger | Role |
|---|---|---|
| 20-inspiration-scout | `/inspiration-loop` | Scout signals + SEA frontend browse + market scan + PM Gate 1 → bet log |

**Shared** (`shared/agents/`):

| Agent | Trigger | Role |
|---|---|---|
| 13-prioritisation-agent | spawned by loop | C×I×S scoring; PM approval gate; Jira stories + Confluence summary |
| 14-weekly-refresh | `/weekly-refresh` | Background refresh of all Domo feedback datasets |

---

## Key design decisions

- **No assumptions** — system halts and asks at every gap; never infers missing data
- **Code grounding** — every file path in a Jira story must appear in Agent 12's `read-audit.log`; unverified = hard block
- **Aggregation-first** — no raw rows to the LLM; SQL aggregates at DB layer; verbatim sampled to configured max
- **PII exclusion at query layer** — enforced in SQL SELECT; unverified schema = query halts
- **Memory-first** — findings store read before querying Domo; re-query only when absent or stale
- **Context-budgeted orchestration** — agents load directive + script + active outputs first, expand only when blocked
- **Human-in-the-loop at every gate** — PM approves at signal review, diagnosis, and prioritisation

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
| `github` | Read access to product repos |
| `chrome-devtools` | Browser automation for Inspiration Loop frontend browsing |
