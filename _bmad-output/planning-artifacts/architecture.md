---
stepsCompleted: [step-01-init, step-02-context, step-03-starter, step-04-decisions]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
workflowType: 'architecture'
project_name: 'squad-enhancement'
user_name: 'Ldavid'
date: '2026-03-07'
lastUpdated: '2026-03-09'
contextRewrittenFrom: 'prd.md (updated 2026-03-09 — Phase 1 Domo MCP loop, Feedback Intelligence, PII policy)'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements — Phase 1 (36 FRs across 6 capability groups):**

| Group | FRs | Architectural unit |
|---|---|---|
| Domo Signal Detection | FR1–5 | Signal agent — queries KPI datasets, pages, cards via Domo MCP |
| Feedback Intelligence | FR6–13 | Feedback agent — findings store read/write, weekly refresh, PII enforcement, aggregation-first |
| Evidence Validation | FR14–19 | Validation agent — Confluence search (secondary), confidence scoring, gap surfacing |
| Hypothesis Management | FR21–23 | Loop state manager — dedup, park, resume |
| Hypothesis Prioritisation | FR24–27 | Prioritisation agent — scoring, ranking, PM gate |
| Registry & Configuration | FR28–31 | Config layer — dataset/page/card registry, thresholds, human approval gate |
| Loop State & Memory | FR32–36 | State manager — cycle state, metrics history, Confluence output, pipeline context |

**Non-Functional Requirements:**
- **Reliability (NFR1–3):** All failures surface explicitly with specific reason; steps idempotent; findings store and metrics history append-only, no overwrite.
- **Security & Data Governance (NFR4–7):** Credentials never committed; PII never retrieved/processed/surfaced at any layer; schema verification before any unverified dataset query; writes scoped to configured targets only.
- **Integration (NFR8–10):** `mcp-atlassian` handles all Confluence writes; Rovo for reads only; 401 errors surface to operator; Domo queries use only registered IDs with correct OAuth scope (`data` for datasets, `dashboard` for pages/cards).
- **Output Quality (NFR11–12):** Confluence history sections append-only; pipeline context overwrites each run; findings store append-only enforced.
- **Performance & Sustainability (NFR13–15):** Findings refreshed within 24h of weekly trigger; signal threshold config-driven; aggregation-first SQL, verbatim capped at configured max — no raw rows to LLM.

**Scale & Complexity:**
- Primary domain: AI agent orchestration, CLI tool
- Complexity: Medium — 4 active MCP integrations (Domo, Confluence, Jira Phase 2, GitHub Phase 2)
- Estimated architectural components: signal agent + feedback agent + validation agent + prioritisation agent + loop state manager + findings store + config/registry layer + weekly scheduler

### Technical Constraints & Dependencies

- Runs within Claude Code CLI — no server, no deployment pipeline, no containerisation
- All persistence is file-based (JSON state, markdown outputs, findings store)
- MCP servers defined in `.mcp.json`; credentials git-ignored
- Domo MCP is **connected** — queries via `domo-mcp` server; OAuth scope `data` for datasets, `dashboard` for pages/cards
- Dataset, page, and card IDs configured in registry (`config/domo.yml`); never hardcoded; new IDs require human approval before first query
- Agent scaffold (05–09) already exists; new agents build on established SKILL.md conventions
- Phase 2 (GitHub MCP + Jira story creation) deferred until Phase 1 gate passed

### Cross-Cutting Concerns

- **PII enforcement** — enforced at SQL SELECT layer before any data leaves Domo; schema verified before querying any new dataset; excluded fields: `user_id`, `account_number`, `card_number`, `payment_details`, `address`, `password`, `login`, name
- **Memory-first pattern** — findings store checked before every Domo feedback query; staleness check determines whether to re-query; eliminates redundant API calls across the loop
- **Aggregation-first** — all Domo queries return SQL aggregates; verbatim sampled to configured max; raw rows never reach the LLM
- **No-assumption enforcement** — applied at every agent reasoning step; Domo evidence absence = hard gate; Confluence absence = graceful skip
- **HIL gate pattern** — PM approval required at evidence review and prioritisation; each gate is a hard stop; system never auto-advances
- **Failure surfacing** — every external call failure (Domo, Confluence, findings store write) propagates to PM with specific reason; no silent skips; fail-safe continues with available sources
- **Loop state durability** — state survives session interruption; interrupted loops detected from cycle state file and offered for resumption on next run
- **Idempotency** — findings store writes and Confluence page updates must not create duplicates on re-run; hypothesis dedup enforced at cycle-state level

---

## Agent Decomposition

### Component Map

Five agents extend the existing scaffold (05–09) with numbered continuity:

| Agent | Number | Responsibility | FRs |
|---|---|---|---|
| `10-signal-agent` | 10 | Step 1 — Query registered KPI datasets, pages, cards via Domo MCP; apply signal threshold; surface metric movements | FR1–5 |
| `11-feedback-agent` | 11 | Step 2a — Memory-first findings store read; Domo feedback query (aggregation-first, PII-safe); staleness check; write aggregated findings; weekly refresh mode | FR6–13 |
| `12-validation-agent` | 12 | Step 2b — Confluence evidence search (secondary); confidence scoring; gap surfacing with PM options; accept PM-provided evidence | FR14–19 |
| `13-prioritisation-agent` | 13 | Step 3 — Hypothesis dedup (cycle-scoped); score by signal strength + evidence weight + business impact; rank; PM gate | FR21–27 |
| `14-weekly-refresh` | 14 | Background — Weekly findings refresh for all registered datasets; append-only findings store write; no PM interaction | FR13, FR32–35 |

### Loop Orchestration

```
PM triggers loop
       │
  10-signal-agent
  (Domo KPI signal)
       │
  ┌────┴────────────┐
  11-feedback-agent  12-validation-agent
  (Domo primary)     (Confluence secondary)
  └────┬────────────┘
       │
  13-prioritisation-agent
  (dedup → score → rank → PM gate)
       │
  Prioritised hypothesis list

[Background, weekly]
  14-weekly-refresh
  (all registered datasets → findings store)
```

### State & Persistence

| Artefact | Path | Mode |
|---|---|---|
| Cycle state | `outputs/growth-engineer/cycle-state.json` | Overwrite per cycle, reset monthly |
| Findings store | `outputs/feedback/findings-store.json` | Append-only |
| Metrics history | `outputs/growth-engineer/metrics-history.json` | Append-only |
| Pipeline context | `outputs/growth-engineer/pipeline-context.md` | Overwrite each run |
| Confluence output | Configured `page_id` | Append to history sections |

### Config & Registry

| File | Purpose | Committed |
|---|---|---|
| `config/domo.yml` | Dataset IDs (KPI, feedback types), page IDs, card IDs, signal threshold, staleness window, verbatim max | Yes |
| `config/atlassian.yml` | Confluence space, page_id, Jira project/epic (Phase 2) | Yes |
| `.mcp.json` | MCP credentials (Domo, Confluence, GitHub) | No (git-ignored) |

---

## Architectural Decisions

**AD1: File-based persistence (no database)**
- **Decision:** All state (cycle state, findings store, metrics history) stored as JSON/markdown files under `outputs/`.
- **Rationale:** Runs in Claude Code CLI — no server infrastructure. Files are diffable, git-trackable, human-readable. Append-only semantics enforced in agent logic.
- **Trade-off:** No concurrent writes — acceptable, single operator per loop.

**AD2: Memory-first before every Domo query**
- **Decision:** `11-feedback-agent` reads findings store and checks staleness before issuing any Domo API call.
- **Rationale:** Weekly refresh cadence means findings valid for 7 days. Re-querying within window wastes OAuth tokens and adds latency.
- **Trade-off:** Stale window is config-driven — operator can tighten if needed.

**AD3: Aggregation-first SQL with verbatim sampling cap**
- **Decision:** All Domo feedback queries use GROUP BY aggregations; verbatim sampled to configured max. Raw rows never passed to LLM.
- **Rationale:** NFR15 + PII policy. Aggregates are sufficient for triangulation; LLM context is not a data lake.
- **Trade-off:** Representative verbatim may miss edge cases — PM can request analyst review.

**AD4: Domo evidence = hard gate; Confluence = graceful skip**
- **Decision:** No Domo evidence → loop halts, PM presented with options (provide evidence / proceed with stated assumption risk / park). No Confluence evidence → loop continues, no PM decision required.
- **Rationale:** PRD specifies different precedence and skip behaviour per source. Gate logic is unambiguous.

**AD5: Hypothesis dedup is cycle-scoped**
- **Decision:** `13-prioritisation-agent` checks `cycle-state.json` for active/parked/actioned hypotheses with same signal + segment. Suppresses duplicates within the monthly cycle.
- **Rationale:** FR21 — prevents PM fatigue from re-reviewing the same hypothesis. Resets monthly.

**AD6: HIL gates are hard stops — no auto-advance**
- **Decision:** Every gate (signal review, evidence confirmation, prioritisation) requires explicit PM input before proceeding.
- **Rationale:** Core product principle — system ranks evidence, PM makes decisions.

**AD7: OAuth scope per call type**
- **Decision:** Dataset queries use `data` scope; page/card reads use `dashboard` scope. Enforced by Domo MCP config.
- **Rationale:** NFR10 — least-privilege at API layer.

**AD8: Schema verification before any new dataset query**
- **Decision:** Before querying any unverified dataset, `11-feedback-agent` calls `get-dataset` metadata and checks column names against PII exclusion list. Query halts if PII column detected.
- **Rationale:** NFR6 — schema verification at query layer, not assumption layer.

