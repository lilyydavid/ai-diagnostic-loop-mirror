---
status: draft
version: 0.5
author: Ldavid
date: 2026-03-18
phase: Phase 1 scoped — Phase 2 next step
---

# PRD — Inspiration Loop

**Author:** Ldavid | **Date:** 2026-03-18 | **Status:** Draft v0.5

---

## Executive Summary

A PM-triggered discovery and execution pipeline that surfaces hidden bets from KPI signals and market activity, puts the PM in the driver's seat for the pre-mortem and prototype idea, then executes a portfolio of sub-prototypes to move one metric clearly.

Without this loop, the bets were never on the surface. The loop makes them visible. The PM decides what to bet on and how. The loop executes it in the lightest possible form — design first, always reversible, always tested.

**Three principles:**
1. **Surface before building** — every bet originates from evidence, not assumption
2. **PM bets, loop executes** — PM runs the pre-mortem and names the prototype idea; the loop classifies, plans, and builds
3. **Prototype or it didn't happen** — no bet advances without a prototype form; no prototype ships without knowing what we want to learn

**The decision gate for every bet:**
> Does this solve a known pain point *and* does it inspire or delight the customer enough to make the brand or the team shine?

---

### Loop Visual

```
PM triggers /inspiration-loop
          │
    ┌─────▼────────────────┐
    │  20-inspiration-scout │  Step 1: Agent 10 signals + scoped market scan
    └─────┬────────────────┘          → Teams notification
          │
          │  *** PM GATE 1 ***
          │  PM reviews signals
          │  Loop facilitates pre-mortem brainstorm
          │  PM names prototype idea
          │
    ┌─────▼─────────────┐
    │  21-bet-classifier │  Step 2: Classifies PM's prototype idea
    │                    │  → pain / shine / pain+shine
    │                    │  → sub-prototypes within that space
    └─────┬──────────────┘          → Teams notification
          │
          │  *** PM GATE 2 — approve bet + sub-prototype portfolio ***
          │
    ┌─────▼──────────────┐
    │  22-prototype-     │  Step 3: Builds each sub-prototype
    │  builder           │  (Miro / Confluence / Frontend / Middleware)
    └─────┬──────────────┘          → Teams notification
          │
          │  *** PM GATE 3 — approve prototypes ***
          │
    ┌─────▼──────────────┐
    │  23-launch-        │  Step 4: Jira prototype stories
    │  validator         │
    └─────┬──────────────┘
          │
    ┌─────▼──────────────┐
    │  24-fit-tracker    │  Step 5: Lifecycle tracking + bet log
    └────────────────────┘          + Bet Story on completion

[Phase 2 — unlocked after ≥3 loops, ≥2/3 bets validated]
  Code generation → PR → feature flag → real-world fit measurement
```

---

## Project Classification

- **Type:** Internal tool, PM-operated, forkable
- **Domain:** Ecommerce product discovery — SEA markets (SG, MY, AU, NZ, PH, HK, TH, ID)
- **Complexity:** Medium — Domo MCP + Confluence + Jira + Miro MCP + Teams webhook + local codebase
- **Context:** Brownfield — built alongside Intelligence Loop; Agent 20 reads Agent 10 outputs directly; shares Domo registry, MCP config, Teams webhook, and output conventions

---

## Success Criteria

| Metric | Definition | Target |
|---|---|---|
| **Loop completion rate** | % of initiated loops that produce ≥1 Jira story | ≥70% |
| **Prototypes tested** | Count of sub-prototypes with Jira stories created | ≥2 per run |
| **Prototypes validated** | Count where Jira story reaches Done | ≥1 per run |
| **Validation rate** | Validated / tested | ≥50% rolling 3 months |
| **Time to market** | Bet surfaced → Jira story created | ≤14 days (pain); ≤21 days (shine) |
| **Bet log completeness** | Bets with pre-mortem + outcome recorded | 100% — no silent bets |

**Technical gates:**
- No bet advances without a PM-authored prototype idea
- No Jira story created without knowing what the prototype is meant to learn
- All implementations feature-flagged or config-only — no irreversible changes
- Every claim in any agent output must be traceable to a cited source

---

## Cycle Definition

A **cycle** = one loop run. Identified by `run_date: YYYY-MM-DD`. If multiple runs occur on the same day, IDs increment: `YYYY-MM-DD-2`, `YYYY-MM-DD-3`. Monthly reporting groups by `YYYY-MM` prefix. Cycle state is written to `outputs/inspiration/cycle-state.json` on trigger and updated at each step.

---

## Bet Taxonomy

A bet is one of two types. Classification drives how much the loop invests in the prototype.

| Bet type | Definition | Loop investment |
|---|---|---|
| **Pain bet** | Evidence exists that customers are blocked or frustrated; fixing it will move a metric | Tight scope, one sub-prototype, predictable return |
| **Shine bet** | Strong signal (market or instinct) this will delight; metric impact is secondary or unknown at time of betting | More exploration room, multiple sub-prototypes, explicit permission to fail fast |

**Priority order when building the portfolio:**
1. **Pain + Shine** — evidenced pain *and* delight potential → ship first
2. **Pain only** → certainty lane, reliable metric move
3. **Shine only** → inspiration lane, smallest stake

**Portfolio rule:** Every run targets one metric. Max 3 bets per run.
- Minimum 1 pain bet per run
- Minimum 1 shine bet per run
- 1 optional dark horse (PM instinct + emerging signal, smallest possible stake)

**Market intel scope:** Agent 20 derives the web search scope from the detected signal — no pre-configured competitor list. If the signal is search drop, look at competitor search experiences. If checkout abandonment, look at checkout UX innovations. Scope is always signal-led.

---

## Product Scope

### Phase 1 — Inspiration Loop (current build)

| Step | Agent | Who acts | Action |
|---|---|---|---|
| 1. Signal + Market Scan | 20 | Loop | Reads Agent 10 signals; checks cycle-state for in-progress run; adds scoped market scan; posts to Teams |
| PM Gate 1 | — | PM + Loop | Loop facilitates pre-mortem brainstorm; PM names prototype idea |
| 2. Bet Classification | 21 | Loop | Classifies PM's idea (pain / shine / pain+shine); checks bet-log dedup; generates sub-prototypes; posts to Teams |
| PM Gate 2 | — | PM | Approves bet + sub-prototype portfolio |
| 3. Prototype Build | 22 | Loop | Builds each sub-prototype; verifies assumptions against evidence; posts to Teams |
| PM Gate 3 | — | PM | Approves prototypes |
| 4. Launch Validation | 23 | Loop | Creates Jira prototype stories |
| 5. Fit Tracking | 24 | Loop | Tracks lifecycle; writes bet log; generates Bet Story on completion; updates Confluence |

### Phase 2 — Code Generation Layer (next step)

**Unlock:** ≥3 Inspiration Loop runs completed, ≥2/3 bets validated per run.
Steps: code change generated → PR created → PM reviews → merged behind feature flag → real-world fit measurement. *Scoped separately after Phase 1 is proven.*

---

## Prototype Implementation Scope

Design and implementation prototype forms are independent — they can be built in parallel or in any order. No sequential dependency between forms.

| Form | In scope | Reversibility | Output |
|---|---|---|---|
| **Miro journey** | Yes — primary design form | Immediate | Customer journey + decision points via Miro MCP |
| **Confluence page** | Yes — MVP idea doc | Immediate | One page: what the feature does, who it's for, core user action, what done looks like |
| **Frontend** | Yes | Feature flag | UI copy, layout, new component, CTA placement, interaction pattern |
| **Middleware / Search config** | Yes | Config change | Ranking rules, autocomplete, recommendation weights, zero-result fallbacks |
| **Backend — config only** | Narrow | Config/flag | Feature flag wiring, parameter tuning, API field additions |
| **Backend — new models/services** | Out of scope | — | New data models, services, migrations, ML retraining |

### Sub-prototypes

Agent 21 generates sub-prototypes within the PM's prototype idea space. Each is a distinct angle or form targeting the same problem and the same target metric. Max 3 sub-prototypes per bet.

Example — PM idea: "improve gift purchase discovery and checkout"
- Sub-prototype A: Miro journey — gift wrap selection at cart
- Sub-prototype B: Search config — merchandising rules for 'gift' queries
- Sub-prototype C: Frontend — gift message input field at checkout

---

## User Journeys

### J1: Full Loop (Happy Path)

**Step 1 — Signal + Market Scan**
Agent 20 checks `outputs/inspiration/cycle-state.json` for an in-progress run. If found, prompts PM: "Resume run [date] at Step [N] — active bet: [idea]? Or start fresh?" PM decides. If starting fresh, writes new cycle state. Reads `outputs/signal-agent/signals.md`. Runs scoped web search. Surfaces combined view. Posts to Teams.

**PM Gate 1 — Pre-mortem + Prototype Idea**
Loop surfaces 2–3 plausible failure scenarios from evidence, asks PM to confirm or add. Offers 2–3 prototype idea directions; PM selects or proposes their own. Agent records both in `outputs/inspiration/bet-log.json` and posts confirmation to Teams. Updates cycle-state to `current_step: 2`. Loop does not advance without both confirmed.

**Step 2 — Bet Classification**
Agent 21 checks bet-log history for prior bets on the same metric + signal domain before classifying. If found, surfaces prior context to PM. Classifies the confirmed bet, generates sub-prototypes. Posts to Teams. PM approves in chat.

**Step 3 — Prototype Build**
Agent 22 builds each approved sub-prototype. Verifies every assumption against a cited source. Produces Miro board content, Confluence page, or implementation feasibility check. Posts to Teams. Updates cycle-state to `current_step: 3`.

**PM Gate 3 — Approve Prototypes**
PM approves in chat. Updates cycle-state to `gates_passed: [1,2,3]`.

**Step 4 — Launch Validation**
Agent 23 creates one Jira story per sub-prototype. Writes `loop_completed: true` to cycle-state. Updates cycle-state to `current_step: 4`.

**Step 5 — Fit Tracking**
Agent 24 (inline) checks stories created this run. On completion: writes bet log outcome. If outcome = completed, generates Bet Story, appends to Validated Bets Confluence page, posts to Teams.

---

### J2: No Usable Signal Found
Agent 20 finds no signals above threshold and no market signals. Surfaces options in chat and Teams: lower threshold / widen window / provide signal directly. Writes `loop_completed: false` to cycle-state. Loop parks.

### J3: PM Pre-mortem Kills the Bet
PM concludes bet is not worth taking. Recorded as `outcome: closed — pre-mortem` in bet log. Writes `loop_completed: false` to cycle-state. No downstream agents run.

### J4: Sub-prototype Assumption Cannot Be Verified
Agent 22 cannot cite a source. Surfaces gap: "Assumption unverified — [assumption]. Proceeding requires PM to provide evidence or accept unverified risk." PM decides.

### J5: Prior Bet Detected (Dedup)
Agent 21 finds a prior bet with same target metric + signal domain. Surfaces: "Similar bet run [date] — outcome: [X]. Sub-prototypes tried: [list]. Proceed as new bet, build on prior learning, or skip?" PM decides.

### J6: Mid-cycle Resume
PM re-triggers `/inspiration-loop`. Agent 20 finds in-progress cycle-state. Prompts: "Resume run [date] at Step [N]?" PM confirms. Loop continues from last confirmed gate.

---

## Output Contract

| Output | Path | Behaviour |
|---|---|---|
| Cycle state | `outputs/inspiration/cycle-state.json` | Overwrite each run |
| Bet log | `outputs/inspiration/bet-log.json` | Append-only — never overwrite |
| Portfolio brief (Confluence) | Child of `64781058049` — title: `YYYY-MM-DD — Inspiration Loop Portfolio` | Create or update per run (find-or-create by title) |
| Validated Bets (Confluence) | Child of `64781058049` — title: `YYYY-MM-DD — Inspiration Loop Validated Bets` (date = first creation date) | Create once on first completion; append-only thereafter |

All Confluence pages created as children of parent page `64781058049` ("I'm feeling lucky", PI space).
`confluence_create_page` → `parent_id: 64781058049`. Title always prefixed with the run date.
Find-or-create by title: call `confluence_get_page_children` on `64781058049`, check for matching title before creating.

---

## Bet Log — Canonical Schema

Append-only. One entry per bet per run. Pre-mortem and PM odds locked at Gate 1 — no retroactive changes.

```json
{
  "bet_id": "BET-001",
  "run_date": "YYYY-MM-DD",
  "trigger_signal": "rising search for 'gift wrap' — 0 results, SG",
  "market_signal": "competitor X launched gift messaging Jan 2026",
  "classification": "pain+shine",
  "target_metric": "search conversion rate",
  "pm_assessed_odds": "60% confident",
  "premortem": "most likely failure: feature exists but not discoverable",
  "prototype_idea": "improve gift purchase discovery and checkout experience",
  "sub_prototypes": [
    {"id": "A", "form": "miro", "description": "gift wrap selection at cart"},
    {"id": "B", "form": "search-config", "description": "'gift' query merchandising"},
    {"id": "C", "form": "frontend", "description": "gift message field at checkout"}
  ],
  "jira_stories": [],
  "outcome": "completed | invalidated | deferred | closed",
  "bet_story": null
}
```

`bet_story` is `null` until `outcome = completed`. Sub-prototypes are objects so Jira story keys can be appended at Step 4. `jira_stories` is populated by Agent 23.

---

## Cycle State Schema

```json
{
  "run_date": "YYYY-MM-DD",
  "current_step": 1,
  "loop_initiated": true,
  "loop_completed": false,
  "gates_passed": [],
  "active_bet_ids": [],
  "target_metric": null,
  "pm_confirmed_premortem": null,
  "pm_confirmed_idea": null
}
```

---

## Domain-Specific Requirements

### Integrations

| System | Access | Purpose |
|---|---|---|
| Agent 10 outputs (`outputs/signal-agent/`) | Read | KPI signal input for Agent 20 — no re-querying Domo |
| Domo MCP | Read | Discovery KPIs + Search Terms to supplement Agent 10 signals |
| Web search | Read | Scoped market intel — competitor activity within detected signal domain |
| Miro MCP | Write | Customer journey boards per sub-prototype — *pending PM connection* |
| Confluence MCP | Read/Write | Portfolio brief + Validated Bets pages under parent `64781058049`; MVP idea pages |
| Jira MCP | Read/Write | Prototype story creation; lifecycle tracking |
| Teams webhook | Write | Gate notifications — uses `config/atlassian.yml → teams` config |
| Local codebase | Read | Feasibility check for frontend/middleware sub-prototypes |
| GitHub MCP | Read | Phase 2 only |

### Configuration

All keys in `config/atlassian.yml` under `inspiration_loop:`:

```yaml
inspiration_loop:
  signal_staleness_days: 7              # FR2 — max age of Agent 10 signals before re-run prompt
  max_bets_per_cycle: 3                 # portfolio cap per run
  confluence_parent_page_id: "64781058049"   # "I'm feeling lucky" — all pages created here
  portfolio_page_title_prefix: "Inspiration Loop Portfolio"
  validated_bets_page_title_prefix: "Inspiration Loop Validated Bets"
  # page titles = YYYY-MM-DD — {prefix}
```

Teams notification events — add to `config/atlassian.yml → teams.notify_on`:

```yaml
teams:
  notify_on:
    # Intelligence Loop (existing)
    - gate_1
    - gate_2
    - week_3_complete
    # Inspiration Loop
    - inspiration_signal_ready
    - inspiration_bet_classified
    - inspiration_prototypes_ready
    - inspiration_bet_completed
```

### Data Access Ground Rules

Inherits all 10 rules from Intelligence Loop PRD, plus:

11. **Agent 10 first** — Agent 20 reads Agent 10's signal output before querying Domo; no duplicate signal work
12. **Scoped market scan** — web search scoped to the signal domain detected by Agent 20; if PM has chosen a hypothesis, scope narrows further
13. **One metric per run** — sub-prototypes that don't connect to PM-defined target metric are deferred
14. **Reversibility gate** — every implementation sub-prototype requires a defined rollback method before Jira story creation
15. **Bet log immutability** — pre-mortem and PM odds locked at Gate 1; no retroactive changes
16. **Source citation required** — every claim must cite a source; unverified assumptions flagged explicitly, not suppressed

### PII Policy

Inherits Intelligence Loop PII policy unchanged.

### Risk Register

| Risk | Mitigation |
|---|---|
| Agent 10 output stale or absent | Surface to PM; offer to re-run Intelligence Loop first or proceed with market scan only |
| PM pre-mortem kills bet | Recorded as "closed — pre-mortem"; no downstream agents run; cycle-state updated |
| No market signals in scoped search | Noted in combined view; PM decides if KPI signal alone is sufficient |
| Sub-prototype assumption unverified | Surface gap to PM (J4); PM provides evidence or accepts risk |
| Prior bet detected on same metric + signal | Surface to PM (J5); PM decides: new bet / build on prior / skip |
| Miro MCP not connected | Agent 22 produces Miro-ready text description; flags "Miro MCP pending — manual board creation required" |
| Teams webhook not configured | Notifications fall back to chat; no loop failure |
| Prototype not reversible | Reversibility gate blocks Jira story creation until rollback method defined |
| Loop abandoned at Gate 1 or 2 | `loop_completed: false` written to cycle-state; counted in completion rate metric |

---

## Innovation Patterns

- **Bets as first-class objects** — every hypothesis has a type (pain / shine / pain+shine), a pre-mortem, and an outcome; nothing is implicit
- **PM-facilitated discovery** — loop brainstorms with the PM rather than prompting; pre-mortem is co-produced, not a blank field
- **Pain + shine as portfolio lens** — pain bets move metrics; shine bets build brand and team pride; the best bets do both
- **Signal-led market scan** — competitor scope derived from the signal itself, not a pre-configured list
- **Sub-prototype portfolio** — one PM idea generates multiple angles; max 3 per bet; portfolio capped at 3 bets per run
- **Bet Story as narrative artifact** — auto-generated on completion; raw material for external storytelling
- **Source-cited outputs** — every agent output must cite its evidence; unverified assumptions surfaced, not smoothed over
- **Cycle state persistence** — loop is resumable at any gate; no work lost on interruption

---

## Functional Requirements

### Step 1 — Signal + Market Scan (Agent 20)

- FR1: On trigger, check `outputs/inspiration/cycle-state.json` for an in-progress run; if found, prompt PM to resume or start fresh before proceeding; write `loop_initiated: true` and `run_date` to cycle-state
- FR2: Read `outputs/signal-agent/signals.md` from most recent Intelligence Loop run; check recency against `inspiration_loop.signal_staleness_days`; if stale, surface to PM with option to re-run Intelligence Loop first or proceed
- FR3: Run web search scoped to the signal domain detected; if PM has already chosen a hypothesis, narrow search to that hypothesis space; do not surface competitor intel outside the detected signal's domain
- FR4: Post combined signal view to Teams with event `inspiration_signal_ready`; if Teams disabled, surface in chat only

### PM Gate 1 — Pre-mortem + Prototype Idea

- FR5: Facilitate structured pre-mortem brainstorm — surface 2–3 plausible failure scenarios from evidence; ask PM to confirm, reject, or add; agreed scenarios become the pre-mortem record
- FR6: Offer 2–3 prototype idea directions based on confirmed signal and pre-mortem risks; PM selects, narrows, or proposes their own; final idea is PM-owned but loop-facilitated
- FR7: Capture confirmed pre-mortem and prototype idea from chat; write to `outputs/inspiration/bet-log.json`; post confirmation to Teams; update cycle-state (`gates_passed: [1]`, `pm_confirmed_premortem`, `pm_confirmed_idea`)
- FR8: Block loop progression if PM has not confirmed both pre-mortem risk and prototype idea; bet log entry must exist before Agent 21 runs

### Step 2 — Bet Classification (Agent 21)

- FR9: Before classifying, check bet-log history for prior bets sharing the same `target_metric` and signal domain; if found with outcome ≠ `deferred`, surface prior context to PM (J5); PM decides before classification proceeds
- FR10: Accept PM's prototype idea as free-text from chat; treat any screenshot or image as supplementary context only
- FR11: Classify the bet as pain, shine, or pain+shine; classification determines loop investment — pain = tight scope, one sub-prototype; shine = more exploration, multiple sub-prototypes; pain+shine = highest priority, ships first
- FR12: For pain bets, cite the specific Domo signal or customer voice evidence; for shine bets, cite the market signal or competitor example; pain+shine requires both citations
- FR13: Generate sub-prototypes within the PM's prototype idea space; each a distinct angle or form targeting the same problem and metric; max 3 sub-prototypes per bet
- FR14: Post classified bet + sub-prototype list to Teams with event `inspiration_bet_classified`; present in chat: bet type, classification rationale, sub-prototype list with form per prototype; PM approves or adjusts in chat; update cycle-state (`gates_passed: [1,2]`)

### Step 3 — Prototype Build (Agent 22)

- FR15: Produce MVP-level description per sub-prototype — one Confluence page max: what the feature does, who it's for, the core user action, what done looks like
- FR16: For journey-based sub-prototypes, create a Miro board frame via Miro MCP: customer journey steps, decision points, emotion at each step; if Miro MCP not connected, produce Miro-ready plain-language description and flag "Miro MCP pending — manual board creation required"
- FR17: Before writing any sub-prototype, verify the core assumption against at least one cited source (Domo signal, Love Meter verbatim, App Review topic, UXR observation, web-sourced competitor example); if unverifiable, state: "Assumption unverified — [assumption]"; surface to PM before proceeding
- FR18: For frontend/middleware sub-prototypes, read targeted codebase sections to confirm feasibility and identify implementation location; note rollback method
- FR19: PM override to skip design step: PM types confirmation in chat; agent records override reason and timestamp in cycle-state; that confirmation is the permission
- FR20: Post to Teams with event `inspiration_prototypes_ready` when all sub-prototypes are built; update cycle-state (`gates_passed: [1,2,3]`)

### Step 4 — Launch Validation (Agent 23)

- FR21: Create one Jira story per approved sub-prototype using the following template:
  ```
  ## Problem
  [from pre-mortem: customer pain or delight opportunity]

  ## Prototype
  Form: [Miro | Confluence | Frontend | Middleware]
  Built: [one-sentence description from Agent 22]

  ## Learning Question
  We want to know if [assumption] is true for [customer segment].

  ## Rollback
  [method — from Agent 22 feasibility check]
  ```
- FR22: Tag all stories: loop tag = `inspo`; prototype form tag = `proto-design`, `proto-fe`, or `proto-mw`; maximum two tags per story
- FR23: Append Jira story keys to the corresponding sub-prototype entries in `bet-log.json`; write `loop_completed: true` and `current_step: 4` to cycle-state

### Step 5 — Fit Tracking (Agent 24)

- FR24: **Inline trigger** — spawned by inspiration-loop orchestrator after Agent 23; checks status of stories created in this run only
- FR25: **Standalone trigger** — PM runs `/inspiration-fit-check`; Agent 24 checks all open inspiration loop stories across all prior runs; updates bet log and cycle-state; posts summary to Teams
- FR26: On Jira story status change to Done: record completion in bet log (`outcome: completed`); note Jira story key
- FR27: On bet completion, generate Bet Story and append to the Validated Bets Confluence page (`YYYY-MM-DD — Inspiration Loop Validated Bets` under parent `64781058049`); post to Teams with event `inspiration_bet_completed`. Bet Story format:
  ```
  Signal:    [what Domo/market told us]
  Bet:       [pain / shine / pain+shine — what we thought would happen]
  Prototype: [what we built, in what form]
  Outcome:   [what actually happened]
  Next:      [what this unlocks or closes]
  ```
- FR28: Update or create Portfolio brief Confluence page (`YYYY-MM-DD — Inspiration Loop Portfolio` under parent `64781058049`) with: bet list, classifications, sub-prototype list, lifecycle status, loop completion rate to date

---

## Error Handling

### Agent 20

| Error | Action |
|---|---|
| Agent 10 signal file missing | Surface to PM; offer to run Intelligence Loop first or proceed with market scan only |
| Agent 10 signal file stale (> `signal_staleness_days`) | Surface staleness; same options as above |
| Web search fails or times out | Note failure; continue with KPI signals only; flag in combined view |
| No signals above threshold | Surface options: lower threshold / widen window / provide signal directly (J2) |

### Agent 21

| Error | Action |
|---|---|
| PM idea too vague to classify | Ask one clarifying question; if still unclear after PM responds, surface: "Idea needs more specificity — what customer action or metric should this affect?" |
| No evidence to support pain classification | Classify as shine-only; flag: "No Domo or customer voice evidence found for pain — treated as shine bet" |
| Prior bet match found | Surface context to PM (J5); PM decides before proceeding |

### Agent 22

| Error | Action |
|---|---|
| Miro MCP fails | Produce Miro-ready text description; flag "Miro MCP failed — manual board creation required" |
| Codebase read fails (repo inaccessible) | Skip feasibility check; flag in sub-prototype: "Feasibility unverified — repo not accessible" |
| Assumption unverified | Surface to PM (J4); PM provides evidence or accepts risk before proceeding |
| Confluence create/update fails (401/403) | Surface auth error; instruct token rotation; do not skip write |

### Agent 23

| Error | Action |
|---|---|
| Jira create returns 400 | Log error with response body; surface specific field causing failure; do not retry automatically |
| Jira create returns 401 | Surface auth error; prompt credential rotation; halt story creation |
| Rollback method undefined for implementation sub-prototype | Block story creation; surface to PM: "Rollback method required before story can be created for [sub-prototype]" |

### Agent 24

| Error | Action |
|---|---|
| Jira read fails | Log failure; use last known status from cycle-state.json; flag as "Jira unverified" |
| Confluence append fails (401/403) | Surface auth error; prompt token rotation; do not silently skip |
| Bet Story generation with no outcome data | Skip generation; flag: "Outcome not recorded — Bet Story cannot be generated" |

---

## Non-Functional Requirements

- NFR1: All failures reported with specific reason — never silently skipped
- NFR2: Bet log is append-only; no overwrite under any condition
- NFR3: Cycle-state preserves all PM-confirmed values; loop resumable at any gate without data loss
- NFR4: Every prototype implementation is feature-flagged or config-gated; irreversible changes blocked
- NFR5: Codebase reads scoped to feasibility only — no raw code in any output; descriptions only
- NFR6: Inherits all Intelligence Loop data governance and PII rules
- NFR7: Agent 20 never re-queries Domo KPI sources already covered by Agent 10 in the same run
- NFR8: **Hallucination prevention** — every claim in every agent output must be traceable to a cited source; claims that cannot be cited are flagged as unverified; no fabricated data points, invented user behaviours, or assumed competitor features at any step from Agent 20 through Agent 24
- NFR9: All Confluence pages created by the Inspiration Loop are children of parent page `64781058049`; page titles always prefixed with the run date (`YYYY-MM-DD —`); the parent page itself is never modified
