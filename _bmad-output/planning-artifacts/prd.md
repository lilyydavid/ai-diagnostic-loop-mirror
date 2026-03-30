---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete, step-e-01-discovery, step-e-02-review, step-e-03-edit]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-squad-enhancement-2026-03-07.md
classification:
  projectType: saas_b2b
  domain: ecommerce_analytics
  complexity: medium
  projectContext: brownfield
workflowType: 'prd'
lastEdited: '2026-03-30'
editHistory:
  - date: '2026-03-09'
    changes: 'Phase 1 = Intelligence Loop via Domo MCP (no screenshots). Phase 2 = Action Layer (GitHub + Jira). Added Feedback Intelligence, dataset/dashboard/card registry, hypothesis dedup, PII policy, 10 data access ground rules.'
  - date: '2026-03-09'
    changes: 'Stripped to first-principles language. Removed all prose padding.'
  - date: '2026-03-15'
    changes: 'Added loop visual. Step 2 split into 2a (feedback) + 2b (independent code review). Agent 14 weekly-refresh background trigger added. FRs added for code survey, journey mapping, experiment design, emergent hypothesis synthesis.'
  - date: '2026-03-30'
    changes: 'Added Inspiration Loop (agents 20–24). Agent 20 built and live — first run completed 2026-03-30. Agent 13 enrichment integration: bet-log.json read as optional enrichment for signal domain matching and pm_odds tiebreaker. Updated loop visual, product scope, user journeys, FRs, and risk register.'
---

# PRD — squad-enhancement

**Author:** Ldavid | **Date:** 2026-03-07 | **Updated:** 2026-03-30

---

## Executive Summary

Two complementary loops for SEA ecommerce PMs across all KPIs and markets (SG, MY, AU, NZ, PH, HK, TH, ID):

**Intelligence Loop (Phase 1 — active):** 3-step diagnostic loop.
1. **Signal** — query configured Domo KPI datasets; surface which metrics moved, where, by how much
2. **Triangulate** — two parallel sub-steps: (2a) Domo feedback datasets for corroborating voice-of-customer evidence; (2b) independent code review to map the current implementation and design A/B experiments
3. **Prioritise** — score and rank experiments by confidence × impact × scope; PM approves which advance

**Inspiration Loop (Phase 3 — active):** PM-triggered ideation loop that produces prototype bets.
1. **Scout** — load Agent 10 signals (what's broken) + browse SEA frontends (what we have today) + scoped market scan (what's possible)
2. **Gate 1** — PM confirms pre-mortem scenario and prototype idea; bet recorded with target metric and odds
3. **Classify** — bet classified by type (pain / shine / pain+shine); drives downstream loop investment
4. Downstream: prototype builder → launch validator → fit tracker (agents 22–24, in design)

Both loops feed Agent 13: the Intelligence Loop provides code-grounded experiment designs; the Inspiration Loop provides market context and PM odds as optional enrichment for scoring and tiebreaking.

Every gate is human-approved. Domo evidence absence is a hard stop — the system halts and asks, it does not infer. Phase 2 adds the action layer (GitHub effort estimation + Jira story creation) once Phase 1 is proven.

### Loop Visuals

**Intelligence Loop**
```
PM triggers /intelligence-loop
          │
    ┌─────▼──────┐
    │  10-signal │  Step 1: query Domo KPI sources
    │   agent    │  → metric movements by market/platform
    └─────┬──────┘
          │  *** PM GATE — confirm hypotheses ***
          │
    ┌─────┴──────────────────────────┐
    │                                │
┌───▼──────────────┐   ┌────────────▼──────────────┐
│  11-feedback     │   │  12-validation             │
│  agent           │   │  agent                     │
│  Step 2a         │   │  Step 2b                   │
│  Domo feedback   │   │  Independent code review   │
│  Confluence UXR  │   │  Journey map + A/B design  │
└───┬──────────────┘   └────────────┬──────────────┘
    └────────────────┬───────────────┘
                     │  *** PM GATE — approve experiments ***
                     │
           ┌─────────▼──────────┐        outputs/inspiration/
           │  13-prioritisation │ ◄──── bet-log.json (optional
           │  agent             │        enrichment from Agent 20)
           └─────────┬──────────┘
                     │
           ┌─────────▼──────────┐
           │  15-trend          │  Trend tracking + priority debt
           │  escalation agent  │
           └────────────────────┘

[Background — weekly]
  14-weekly-refresh  →  findings-store.json (append-only)
```

**Inspiration Loop**
```
PM triggers /inspiration-loop
          │
    ┌─────▼──────────────┐
    │  20-inspiration    │  Step 1: Agent 10 signals (what's broken)
    │  scout             │  Step 2: SEA frontend browse (current state)
    │                    │  Step 3: scoped market scan (what's possible)
    │                    │  *** PM GATE 1 — pre-mortem + prototype idea ***
    └─────┬──────────────┘
          │  writes bet-log.json → consumed by Agent 13
          │
    ┌─────▼──────────────┐
    │  21-bet-classifier │  Classify bet: pain / shine / pain+shine
    └─────┬──────────────┘
          │
    ┌─────▼──────────────┐
    │  22-prototype      │  (in design)
    │  builder           │
    └─────┬──────────────┘
          │
    ┌─────▼──────────────┐
    │  23-launch         │  (in design)
    │  validator         │
    └─────┬──────────────┘
          │
    ┌─────▼──────────────┐
    │  24-fit-tracker    │  (in design)
    └────────────────────┘
```

## Project Classification

- **Type:** Internal tool, single-org, forkable
- **Domain:** Ecommerce analytics — SEA markets (SG, MY, AU, NZ, PH, HK, TH, ID)
- **Complexity:** Medium — Domo MCP + Confluence + Jira + GitHub integrations, AI reasoning, HIL gates
- **Context:** Brownfield — agent scaffold (05–09) exists; Phase 1 Intelligence Loop is current build

## Success Criteria

| Metric | Definition | Target |
|---|---|---|
| **Loop completion rate** | % of initiated Intelligence Loops that produce a PM-approved prioritised hypothesis list | ≥80% over rolling 3 months |
| **Hypothesis action rate** | % of surfaced hypotheses the PM acts on (presents to leadership or routes to Phase 2) | ≥2 of 3 per completed loop |
| **Inspiration Loop bet rate** | % of initiated Inspiration Loops that produce a fully-populated bet entry with PM Gate 1 confirmed | ≥80% over rolling 3 months |
| **Inspiration → Intelligence enrichment rate** | % of Agent 13 runs where Agent 20 enrichment is present, within staleness window, and signal domain matched | Tracked — no target yet (baseline being established) |

**Technical gates:**
- No assumption at any step — gaps surfaced, not filled
- Domo evidence absence = hard gate; Confluence absence = graceful skip
- Duplicate hypothesis for same signal + segment suppressed within cycle
- Failed steps surface specific error — never silently skipped

## Product Scope

### Phase 1 — Intelligence Loop (All KPIs)

**Trigger:** PM initiates loop.

| Step | Action | Source |
|---|---|---|
| 1. Signal | Query registered KPI datasets, pages, and cards; extract metric movement by market/platform | Domo MCP (dataset + page + card registry) |
| 2a. Feedback triangulation | Check registered feedback datasets for corroborating voice-of-customer evidence; then check Confluence UX research | Domo feedback (primary) → Confluence UXR (secondary, skip if absent) |
| 2b. Independent code review | Map the current FE/BE journey for each hypothesis; read targeted code; identify mechanism; propose A/B experiment design; synthesise emergent hypotheses from branch conditions and feature flags | Local codebase (PM selects repos) |
| 3. Prioritise | Dedup hypotheses; score by confidence × impact × scope; PM approves which experiments advance to Jira | PM gate |

Steps 2a and 2b run in parallel after the Step 1 PM gate. Both feed Agent 13.

**Output:** Ranked, experiment-ready hypothesis list with Jira stories and Confluence summary

**Hard rules:** no assumptions at any step; Domo feedback absence = hard gate; Confluence absence = graceful skip; hypothesis dedup before ranking; PM approves at every gate; code review never writes raw code to any output.

### Phase 2 — Action Layer

**Trigger:** Phase 1 gate passed (≥3 loops, ≥2/3 hypotheses actioned).
**Steps:** GitHub effort estimation → Complexity gate (Low/Med only) → Jira story creation
**Output:** Sprint-ready Jira stories

### Phase 3 — Inspiration Loop (active)

**Trigger:** PM runs `/inspiration-loop`. Independent of Intelligence Loop cadence — can be triggered any time.

| Step | Agent | Action | Output |
|---|---|---|---|
| 1. Scout | 20-inspiration-scout | Load Agent 10 signals + browse SEA frontends + scoped market scan + PM Gate 1 (pre-mortem + prototype idea) | `bet-log.json` (append), `inspiration-signal.md` (overwrite), `cycle-state.json` (overwrite) |
| 2. Classify | 21-bet-classifier | Classify bet as pain / shine / pain+shine; set loop investment level | `bet-log.json` (update entry) |
| 3–5. Build → Validate → Track | 22–24 | Prototype builder → launch validator → fit tracker | In design |

**Bet log schema** (Agent 20 fully populates all fields — no nulls):

| Field | Source |
|---|---|
| `bet_id` | Sequential (BET-NNN) |
| `run_date` | Today |
| `signal` | Agent 10 `signals.md` |
| `current_state` | SEA frontend browse (sephora.sg, .my, .com.au, .co.th) |
| `market_context` | Scoped web search — cite source URL |
| `prototype_idea` | PM Gate 1 — PM's exact words |
| `target_metric` | PM Gate 1 |
| `premortem` | PM Gate 1 — PM's confirmed scenario |
| `pm_odds` | PM Gate 1 |

**Agent 13 enrichment integration:** Agent 13 reads `bet-log.json` as optional non-blocking enrichment. If present and within staleness window, Agent 13 matches Agent 20's `target_metric` against hypothesis signal domains; applies `pm_odds` as tiebreaker for equal-scoring experiments; surfaces `market_context` in Jira story "Market Context" section.

**sephora.com vs SEA frontends:** sephora.com (US) is the inspiration benchmark for what's possible. sephora.sg, sephora.my, sephora.com.au, sephora.co.th are the actual frontends observed for current state.


## User Journeys

### J1: PM — Intelligence Loop (Happy Path)

**Step 1 — Signal**
PM triggers loop. System queries all registered KPI datasets via Domo MCP. Surfaces: which metrics moved, direction, magnitude, market/platform breakdown across all KPIs.

**Step 2a — Feedback triangulation (parallel)**
System checks findings store (memory-first). If stale, re-queries registered Domo feedback datasets — returns aggregated evidence: topic distribution, rating trends, volume by segment, representative verbatim.
System then queries Confluence UX research (Jira UXR project, Observation issues). Incorporates result if found; skips gracefully if absent.
If no Domo feedback evidence found → surfaces gap with options; PM decides before loop continues.

**Step 2b — Independent code review (parallel)**
PM confirms which repos and funnel scope to survey.
System maps the current FE+BE journey: locates entry/exit points, traces step-by-step flow, notes branch conditions and feature flags.
For each hypothesis, reads targeted code at the relevant journey step. Extracts current behaviour (descriptions only — no raw code). Checks for existing A/B experiment flags.
Synthesises emergent hypotheses from branch conditions, feature flags, and fragility notes. PM approves emergent hypotheses before experiment design proceeds.
Produces one A/B test design per hypothesis with Confidence/Impact/Scope scores from code evidence.

**Step 3 — Prioritise**
Hypothesis dedup runs — suppresses any hypothesis already active/actioned this cycle for same signal + segment.
System scores experiments: Confidence (code review) × Impact (code + signal severity) × Scope (SP, inverted); presents full ranked signal→hypothesis→experiment table.
PM approves which experiments advance to Jira stories.
Output: prioritised, experiment-ready hypothesis list + Jira stories + Confluence summary.

### J2: PM — No Domo Evidence

Domo feedback queries return no corroborating evidence. System surfaces: "No evidence found. Options: (1) provide evidence directly, (2) loop in UX researcher, (3) proceed with stated assumption risk." PM decides. Loop parks if awaiting input.

### J3: PM — Hypothesis Deduplication

Signal matches segment + metric already actioned this cycle. System suppresses: "Hypothesis already active this cycle. Showing novel hypotheses only."

### J4: Weekly Findings Refresh (Background)

Triggered by PM running `/weekly-refresh`. Agent 14 queries all registered Domo feedback datasets within the configured date window. Aggregates topic distribution, rating trends, volume by market/platform. Samples representative verbatim rows. Writes to findings store (append-only). No PII fields retrieved at any step.

### J5: Emergent Hypothesis (from Code Review)

During Step 2b, agent 12 finds a failure mechanism in the code that was not surfaced by the Domo signal (e.g. a stale feature flag, a platform-specific branch, a silent error path). Surfaces emergent hypothesis to PM with source (journey map / flag / fragility note / Agent 11 signal). PM approves or defers before experiment design proceeds.

### J6: PM — Inspiration Loop (Happy Path)

**Step 1 — Scout (Agent 20)**
PM triggers `/inspiration-loop`. Agent 20 checks cycle-state for in-progress run (resume or fresh). Loads Agent 10 `signals.md` — identifies primary signal domain (largest confirmed movement). Browses the relevant SEA frontend (sephora.sg, .my, .com.au, or .co.th) to observe current state in the signal's funnel area. Runs scoped web search for competitor/industry signals in the same domain. Surfaces combined brief to PM.

**PM Gate 1 — Pre-mortem + Prototype Idea**
Agent 20 surfaces 2–3 failure scenarios grounded in the brief. PM confirms one (or provides their own). Agent 20 offers 3 prototype directions; PM selects or narrows. PM provides target metric and confidence odds. Agent 20 records fully-populated bet entry in `bet-log.json` and updates `cycle-state.json`.

**Step 2 — Classify (Agent 21, in design)**
Bet classified as pain (fixes a confirmed failure), shine (creates new value), or pain+shine (both). Classification drives downstream loop investment level.

**Agent 13 enrichment**
On the next Intelligence Loop run, Agent 13 reads `bet-log.json`. If the bet's `target_metric` matches an experiment's signal domain, Agent 13 applies `pm_odds` as tiebreaker and includes `market_context` in the Jira story.

### Journey Capability Map

| Capability | Journey |
|---|---|
| Domo MCP KPI signal detection (all KPIs, dataset-agnostic) | J1 |
| Dashboard/card registry reads | J1 |
| Findings store read (memory-first) + staleness check | J1, J2, J4 |
| Domo feedback triangulation (primary evidence) | J1, J2 |
| Confluence UX research search (secondary, skippable) | J1 |
| Independent code review — journey map + targeted code reading | J1, J5 |
| A/B experiment design (FE or backend, per hypothesis) | J1, J5 |
| Emergent hypothesis synthesis from code evidence | J5 |
| Confidence/Impact/Scope scoring from code evidence | J1 |
| Hypothesis deduplication (cycle-scoped) | J1, J3 |
| Experiment scoring + ranking + PM gate | J1 |
| Evidence gap surfacing with options | J2 |
| Loop parking + resumption | J2 |
| External evidence input | J2 |
| Weekly findings refresh + write | J4 |
| Aggregation-first SQL + verbatim sampling | J4 |
| PII exclusion at query layer | J4 |
| Inspiration Loop — signal + frontend browse + market scan | J6 |
| PM Gate 1 — pre-mortem + prototype idea facilitation | J6 |
| Bet log — fully-populated entry at point of creation | J6 |
| Agent 13 enrichment — signal domain matching + pm_odds tiebreaker | J6 |
| Cycle state resumability (resume / fresh run) | J6 |

## Domain-Specific Requirements

### Integrations

| System | Access | Purpose | Status |
|---|---|---|---|
| Domo MCP (`domo-mcp`) | Read | KPI signal detection; feedback triangulation; findings store queries | Connected |
| Confluence MCP (`mcp-atlassian`) | Read/Write | Secondary evidence retrieval (Step 2a); loop output pages | Connected |
| Jira MCP (`mcp-atlassian`) | Read/Write | Story creation under BAAPP-461; UXR research query (Step 2a) | Connected |
| Local codebase (file system) | Read | Independent code review — journey mapping + A/B experiment design (Step 2b) | Connected |
| GitHub MCP | Read | `sephora-asia` repos (Phase 2 action layer only) | Phase 2 |

### Registered Dataset Types

| Type | Signal | Registry |
|---|---|---|
| Domain KPI | Quantitative — metric values by market/platform/KPI | Dataset + Page + Card |
| App store reviews | Qualitative verbatim + quantitative (rating, topic, volume) | Dataset |
| Love Meter (NPS) | Quantitative score trend + qualitative open text | Dataset |
| Skincredible feedback | Qualitative verbatim | Dataset |
| Customer service tickets | Qualitative (issue, verbatim) + quantitative (volume) | Dataset |

All IDs configured in registry file — never hardcoded. New sources require human approval before first query.

### PII Policy

**Governing rule:** The system must never retrieve, process, or surface PII at any layer — query, findings store, Confluence, or any output.

**Excluded fields:** `user_id` · `account_number` · `card_number` · `payment_details` · `address` · `password` · `login` · username · email · phone · name

Exclusion enforced at SQL SELECT layer. Unverified schema → query halts, human review required.

### Data Access Ground Rules

1. **Least privilege** — query only sources in approved registry
2. **Read-only** — no writes, modifications, or deletes to source systems
3. **Aggregation-first** — no raw rows to LLM; SQL aggregates at DB layer; verbatim sampled to configured max
4. **Scoped date windows** — every query includes date range filter; no unbounded SELECT *
5. **Schema verification** — PII column detected → query halts, human review before proceeding
6. **Memory-first** — read findings store before querying Domo; re-query only when absent or stale
7. **No raw data in outputs** — findings store, Confluence, and all outputs contain aggregated insights only
8. **Human approval for new sources** — any new dataset/dashboard/card ID requires explicit approval before first query
9. **Fail-safe** — failed query logs failure, continues with available sources; never fabricates
10. **Purpose limitation** — data used for hypothesis triangulation only; repurposing requires new approval gate

### Technical Constraints

- **No assumptions** — system does not infer or fill gaps at any step; PM decides at every gate
- **Suspicious metric filter** — runs before any output; anomalous metrics excluded from hypothesis formation
- **Signal threshold** — defined in config, not hardcoded

### Risk Register

| Risk | Mitigation |
|---|---|
| Domo feedback returns no evidence | Gap surfaced with options; PM decides (J2) |
| Stale findings store | Staleness check on every read; re-query if stale |
| Duplicate hypothesis | Cycle-scoped dedup before prioritisation (J5) |
| Scoring miscalibrated | PM gate — PM approves which hypotheses advance |
| Schema verification fails | Query halted; human review required |
| Confluence returns no evidence | Skipped gracefully; loop continues |
| Loop stalls (5+ months, <3 loops) | Fix trigger mechanism — not a Phase 2 trigger |
| **Hallucinated code references in Jira stories** | Code grounding check (Step 5a): every file in "Where in the code" must appear in Agent 12's `read-audit.log` before story creation. Unverified → hard block. Confidence = Low → hard block. No audit log → all stories blocked. |
| **Inspiration Loop — fabricated market scan findings** | Every claim must cite a source URL. If search returns no results: state "No market signals found" — no continuation. Agent 20 describes only visibly present UI — no inference from visual to backend behaviour. |
| **Inspiration Loop — stale Agent 10 signals** | Staleness check against `signal_staleness_days` config. If stale: surface to PM with options before proceeding. |
| **Inspiration Loop — bet entry with null fields** | Agent 20 never advances past Gate 1 without PM confirming both pre-mortem and prototype idea. All bet fields owned by Agent 20 must be populated before writing. |
| **Agent 13 over-relying on Inspiration Loop enrichment** | Enrichment is strictly non-blocking and tiebreaker-only. Agent 13 scores and ranks from Intelligence Loop inputs first; Agent 20 data never overrides confidence/impact/scope scores. |

## Innovation Patterns

- **3-step intelligence loop** — Signal → Triangulate → Prioritise maps directly to how a PM thinks; no translation layer between tool output and leadership conversation
- **Dataset-agnostic signal detection** — any KPI from config registry; no hardcoded metrics; loop adapts to whichever domain KPI the PM owns
- **Domo-first triangulation** — feedback datasets (primary) before Confluence (secondary); each source has defined precedence and skip behaviour; no ambiguity about what gates progression
- **Memory-first sustainability** — findings pre-computed weekly; system reads store before querying Domo; redundant API calls eliminated
- **Two-phase separation** — Phase 1 (intelligence, no Jira/GitHub) delivers standalone leadership value; Phase 2 (action layer) added only after Phase 1 is proven
- **HIL at every gate** — PM judgment at signal review, evidence confirmation, and prioritisation; system never proceeds without explicit approval

## Internal Tool Requirements

- **Deployment:** Claude Code CLI; file-based config; forkable per team
- **Credentials:** `.mcp.json` git-ignored; `config/atlassian.yml` + `config/domo.yml` committed
- **Config isolation:** All keys (`jira_project_key`, `epic_key`, `page_id`, `space_name`, dataset/dashboard/card registries) overridable via `*.local.yml`; no shared state between instances
- **Permissions:** Single operator runs full Phase 1 loop; role separation introduced in Phase 2

## Functional Requirements

### Domo Signal Detection
- FR1: Query all registered domain KPI datasets via Domo MCP; extract metric values, period-over-period deltas, market/platform breakdown
- FR2: Read from registered page IDs (`/v1/pages/{id}`) or card IDs (`/v1/cards/{id}`) as pre-aggregated KPI signal sources; both require `dashboard` OAuth scope
- FR3: Apply configurable signal threshold (from config) to determine which movements trigger hypothesis formation
- FR4: Apply suspicious metric filter; flag anomalous values before processing
- FR5: Surface data quality concerns to PM with recommendation to involve analyst

### Feedback Intelligence
- FR6: Query registered Domo feedback datasets for evidence corroborating detected signal
- FR7: Read findings store before querying Domo; re-query only when findings are absent or stale
- FR8: Write aggregated findings to findings store after each query; append-only — never overwrite history
- FR9: Check findings staleness against configured time window before deciding to re-query
- FR10: Sample verbatim fields to configured row maximum; never pass full dataset rows to LLM
- FR11: Verify dataset schema for PII fields before querying; halt and flag if PII columns detected
- FR12: Never retrieve, process, or surface PII fields (`user_id`, `account_number`, `card_number`, `payment_details`, `address`, `password`, `login`, name)
- FR13: Refresh findings for all registered datasets on weekly cadence

### Evidence Validation (Step 2a — Feedback)
- FR14: Search Jira UXR project (type = Observation, status = Posted) for hypothesis-relevant UX research evidence (secondary source)
- FR15: Score evidence confidence (High/Medium/Low) by source count, recency, relevance
- FR16: When Domo feedback evidence absent — surface gap with options: provide evidence directly or proceed with stated assumption risk
- FR17: Accept PM-provided evidence into evidence summary
- FR18: Block progression past Domo evidence gate without confirmed evidence or explicit PM skip
- FR19: Skip Confluence/UXR gracefully when no evidence found — no PM decision required

### Independent Code Review (Step 2b)
- FR20: PM gate before any file is read — confirm repos to survey and funnel scope
- FR21a: Map current FE+BE journey for the approved funnel scope using Glob/Grep/Read; produce step-by-step plain-text flow with branch conditions and feature flags noted
- FR21b: For each hypothesis, read targeted code at the relevant journey step; extract current behaviour as descriptions only — no raw code, no stack traces, no secrets in any output
- FR21c: Check for existing A/B experiment flags (`featureFlag`, `experiment`, `variant`, `toggle`) in the same code area; flag overlap or conflict
- FR21d: Synthesise emergent hypotheses from branch conditions, feature flags, TODOs, and fragility notes not covered by the original hypothesis list; present to PM with source attribution before proceeding
- FR21e: Propose one A/B test design per hypothesis (FE or backend, justified); include control, variant, segment scope, success metric, SP estimate, risk, and rollback method
- FR21f: Score each hypothesis — Confidence (code directly confirms / related fragility / no code evidence), Impact (core funnel path / conditional path / edge case), Scope (SP 1 / SP 2–3 / SP >3)
- FR21g: Write journey map, experiment designs, and scores to `outputs/validation/` — never to Confluence, Jira, or any memory file; outputs are local only

### Hypothesis Management
- FR22: Before surfacing any hypothesis, check for existing active/parked/actioned hypothesis for same signal + segment in current cycle — suppress duplicates
- FR23: PM can park loop pending evidence or analyst input
- FR24: PM can resume parked or interrupted loop; interrupted loops detected from cycle state on next run

### Experiment Prioritisation
- FR25: Score experiments by Confidence (from code review) × Impact (code + signal severity) × Scope (SP, inverted); priority score = C × I × S (max 27)
- FR26: Rank experiments; surface full signal→hypothesis→experiment chain with scores; present ranked table to PM
- FR27: PM reviews and approves which experiments advance to Jira story creation
- FR28: Output prioritised, experiment-ready list with Jira stories and Confluence summary as Phase 1 loop result

### Registry & Configuration
- FR29: Operator registers Domo dataset IDs by type (KPI, app reviews, NPS, Skincredible, CS tickets); datasets use `data` OAuth scope
- FR30: Operator registers Domo page IDs or card IDs for pre-aggregated KPI signal; both use `dashboard` OAuth scope
- FR31: New dataset, page, or card ID requires human approval before first query
- FR32: Operator configures signal threshold, findings staleness window, and verbatim sampling maximum
- FR33: Operator registers repos in `config/repos.yml` (metadata) and `config/repos.local.yml` (local paths, git-ignored); agent 12 reads only registered repos at PM-confirmed paths

### Loop State & Memory
- FR34: Track loop state across stages (signal → triangulation → prioritisation)
- FR35: Store approved hypotheses and gate decisions in persistent cycle state file; reset monthly
- FR36: Update designated Confluence page with loop output per run
- FR37: Append to persistent ranked-hypotheses history and findings store — never overwrite
- FR38: Generate pipeline context file summarising current run state for downstream agents
- FR39: Agent 12 must never write code patterns, implementations, file paths, or code-derived content to memory files — code evolves and cached code insights create false confidence

### Inspiration Loop (Phase 3)

- FR40: PM triggers `/inspiration-loop`; Agent 20 checks `cycle-state.json` for in-progress run and surfaces resume/fresh choice before proceeding
- FR41: Agent 20 reads Agent 10 `signals.md`; if absent, surfaces options (re-run intelligence loop or proceed without); if stale beyond `signal_staleness_days`, surfaces staleness and waits for PM decision
- FR42: Agent 20 browses the SEA frontend area corresponding to the primary signal domain (sephora.sg / .my / .com.au / .co.th); uses visible UI only — no source code inspection; documents only what is visibly present; if inaccessible, records "not accessible" and continues
- FR43: Agent 20 runs a scoped web search for the primary signal domain; every market scan claim must cite a source URL; if no results, records "No market signals found" — no fabrication
- FR44: Agent 20 surfaces the combined brief (KPI signals + current state + market scan) to PM before Gate 1; posts to Teams `inspiration_signal_ready` if enabled
- FR45: PM Gate 1 is non-skippable — Agent 20 does not advance until PM has confirmed both pre-mortem scenario and prototype idea
- FR46: Agent 20 fully populates all bet entry fields at creation — no null fields it owns; downstream agents append their own fields
- FR47: `bet-log.json` is append-only — one entry per run; never overwritten; Agent 20 determines bet ID by reading prior entries
- FR48: `cycle-state.json` is overwritten at each step — tracks `current_step`, `gates_passed`, `active_bet_ids`, and PM-confirmed gate values
- FR49: Agent 13 reads `bet-log.json` if present and within staleness window; matches `target_metric` against hypothesis signal domains; applies `pm_odds` as tiebreaker for equal-scoring experiments; includes `market_context` in Jira story "Market Context" section; absence or staleness is non-blocking
- FR50: sephora.com (US) is used as the inspiration benchmark for what's possible; SEA frontends (sephora.sg, .my, .com.au, .co.th) are used as the current state observation targets

## Non-Functional Requirements

### Reliability
- NFR1: All failures (failed Domo query, Confluence error, findings store write failure) reported with specific reason — never silently skipped
- NFR2: Steps are idempotent — re-running on same input produces no duplicate findings store entries or Confluence updates
- NFR3: Findings store and metrics history are append-only; no overwrite under any condition

### Security & Data Governance
- NFR4: All MCP credentials stored in `.mcp.json` (git-ignored) — never committed
- NFR5: PII never retrieved, processed, or surfaced at any layer
- NFR6: Schema verification runs before any new or unverified dataset is queried; PII column detected = query halted
- NFR7: Writes scoped to configured Confluence page and Jira project only — no writes outside these boundaries

### Integration
- NFR8: Confluence writes use `mcp-atlassian` exclusively; Rovo server for reads/search only
- NFR9: 401 from Confluence or Jira surfaces error and prompts credential rotation — no silent retry
- NFR10: Domo queries use only registered IDs from config registry (datasets, pages, cards) — no ad-hoc access; correct OAuth scope (`data` for datasets, `dashboard` for pages/cards) enforced per call

### Output Quality
- NFR11: Confluence updates append to history sections — no overwrite of prior content
- NFR12: Pipeline context file overwrites each run; findings store and metrics history append-only — enforced, not optional
- NFR13: Every file path in a Jira story's "Where in the code" section must be verified against Agent 12's `read-audit.log` before story creation — Agent 13 must never infer, guess, or reconstruct file paths not confirmed by actual code reading
- NFR14: Jira stories must not be created for experiments where Agent 12 returned `confidence = Low` or where no files were read — these route to `needs-spike.md` and require PM decision before any ticket is opened

### Performance & Sustainability
- NFR15: Findings refreshed within 24 hours of weekly trigger for all registered datasets
- NFR14: Signal threshold defined in config — not hardcoded in agent logic
- NFR15: All dataset insights derived from SQL aggregations; verbatim capped at configured sampling maximum — no raw rows to LLM
