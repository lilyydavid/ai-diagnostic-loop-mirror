# 20-inspiration-scout — Procedure

Step-by-step execution. Resume from the labelled step when continuing a parked run.
Context: read POLICY.md for output contracts, permissions, and error handling.

---

## Step 1 — Check cycle state

Read `outputs/inspiration/cycle-state.json` if it exists.

If `loop_initiated: true` AND `loop_completed: false`:
```
*** INSPIRATION LOOP — IN-PROGRESS RUN DETECTED ***
Run date: {run_date} | Current step: {current_step}
Active bet: {prototype_idea or "(Gate 1 not yet reached)"}

Resume at Step {current_step}? Or start a fresh run?
Reply "resume" or "fresh".
*** END ***
```
Wait for PM reply. If "resume": skip to the step matching `current_step`.
If "fresh" or no prior state: initialise new cycle state and proceed.

Initialise `outputs/inspiration/cycle-state.json` (overwrite):
```json
{
  "run_date": "YYYY-MM-DD",
  "current_step": 1,
  "loop_initiated": true,
  "loop_completed": false,
  "gates_passed": [],
  "active_bet_id": null,
  "target_metric": null,
  "pm_confirmed_premortem": null,
  "pm_confirmed_idea": null
}
```

Create `outputs/inspiration/` directory if it does not exist.

---

## Step 2 — Load diagnosis artifact (required)

Read `outputs/diagnosis/diagnosis.md` (or `outputs/diagnosis/diagnosis.json`).

If missing:
> "Diagnosis artifact not found. Agent 20 runs after the Intelligence Loop diagnosis stage. Run `/intelligence-loop` first."
Halt.

Extract:
- Favored diagnosis (what is broken)
- Failure surface (where in the journey it breaks)
- Mechanism summary (why it breaks)
- Affected markets/segments

This diagnosis context determines sephora.com browse scope (Step 4) and market scan scope (Step 5).

---

## Step 3 — Load Agent 10 signals (optional context)

Read `outputs/signal-agent/signals.md`.

If missing: note absence and continue. Diagnosis is primary context.

If present: check file age against `inspiration_loop.signal_staleness_days` (default: 7).
If stale:
> "Agent 10 signals are {N} days old (limit: {signal_staleness_days}). Proceed anyway or re-run intelligence loop first? Reply 'proceed' or 're-run'."
If "proceed": note staleness in combined brief; continue.

Extract optional context:
- Confirmed signal movement (metric, delta, market, period)
- 2–3 funnel observations

---

## Step 4 — Browse sephora.com — current UX state

Navigate to the relevant sephora.com feature area based on the diagnosis failure surface.
If diagnosis scope is unclear, fall back to primary signal domain.

| Signal domain | Browse target |
|---|---|
| Search / discovery | sephora.com search bar, zero-result page, autocomplete, search results page |
| Checkout / payment | sephora.com cart → checkout flow, payment method screen |
| ATC / cart | sephora.com PDP → add-to-cart → cart review |
| Sessions / engagement | sephora.com homepage, app-like onboarding or personalisation surfaces |
| PDP / conversion | sephora.com product detail page, reviews section, recommendations |
| Identity / loyalty | sephora.com sign-in flow, loyalty/rewards page, account dashboard |

Use `mcp__chrome-devtools__navigate_page` and `mcp__chrome-devtools__take_screenshot`.
Extract as a plain-language description:
- What the feature area looks like today
- Any obvious gaps, missing affordances, or friction points relative to the diagnosis
- Anything that would explain the metric movement if it were broken or suboptimal

**Hallucination prevention:** describe only what is visibly present. Do not infer backend behaviour from UI alone. If inaccessible or region-restricted: note the limitation and proceed; do not fabricate.

---

## Step 5 — Scoped market scan

Run web search scoped to the diagnosis failure surface/mechanism. Scope to SEA ecommerce and beauty.

| Signal domain | Search focus |
|---|---|
| Search / discovery | Competitor search UX innovations, zero-result handling, autocomplete patterns |
| Checkout / payment | Checkout UX improvements, one-click patterns, payment failure recovery |
| ATC / cart | Add-to-cart UX, cart optimisation, PDP-to-cart conversion patterns |
| Sessions / engagement | App engagement features, personalisation, re-engagement tactics |
| PDP / conversion | PDP layout innovations, social proof, product page conversion lifts |
| Identity / loyalty | Loyalty programme redesigns, rewards discovery, sign-in UX |

**Hallucination prevention:** every claim must cite a source URL or publication. Do not invent competitor features. If search returns no usable results: state "No market signals found in scoped search" — do not fabricate.

Extract 2–5 signals: competitor launches, industry innovations, UX patterns from the past 90 days.

---

## Step 6 — Surface combined brief

Present to PM before Gate 1:

```
── INSPIRATION LOOP — COMBINED BRIEF ────────────────────────────────────────
Run: {YYYY-MM-DD}

## KPI Signals  (Agent 10 — {date}{" ⚠️ STALE" if stale})
{confirmed signals table}
{2–3 funnel observations}

## Current State  (sephora.com — {date})
Feature area: {browse target}
{plain-language description of what exists today}
{gaps or friction observed}
{or: "sephora.com not accessible — skipped"}

## Market Scan  ({signal domain})
{2–5 signals with source citations}
{or: "No market signals found in scoped search."}
─────────────────────────────────────────────────────────────────────────────
```

Post to Teams (`inspiration_signal_ready`) if `teams.enabled: true`. If Teams fails: note and continue.

---

## Step 7 — PM Gate 1 — Pre-mortem + Prototype Idea

Do not advance until PM has confirmed both the pre-mortem and the prototype idea.

**Phase A — Pre-mortem**

Based on the combined brief, surface 2–3 plausible failure scenarios.
Each must be grounded in a specific signal or observation — no fabricated scenarios.

```
── PM GATE 1 — PRE-MORTEM ───────────────────────────────────────────────────
Here are 3 plausible failure scenarios based on the brief:

1. {scenario — cite specific signal or observation}
2. {scenario — cite specific signal or observation}
3. {scenario — cite specific signal or observation}

Which resonates? Confirm, reject, or describe your own.
─────────────────────────────────────────────────────────────────────────────
```
Wait for PM. Record confirmed pre-mortem in PM's own words if they provide their own.

**Phase B — Prototype Idea**

Based on confirmed pre-mortem + combined brief, offer 2–3 directions:

```
── PM GATE 1 — PROTOTYPE IDEA ───────────────────────────────────────────────
Given "{PM's confirmed scenario}", here are 3 directions:

1. {direction — specific, actionable, signal-grounded}
2. {direction — different form or angle}
3. {direction — more exploratory, inspired by market scan}

Select one, narrow it, or propose your own.
─────────────────────────────────────────────────────────────────────────────
```
Wait for PM. Record prototype idea in PM's exact words.

**Phase C — Target metric and odds**

```
Two quick questions:
1. Which metric are you targeting? (e.g. "search conversion rate")
2. How confident are you this moves it? (e.g. "60%", "long shot", "I'd bet on it")
```
Wait for both answers.

---

## Step 8 — Write outputs

**8a — Determine Bet ID**
Read `outputs/inspiration/bet-log.json` if it exists. Find the highest BET-NNN number and increment by 1. If no prior bets: start at BET-001.

**8b — Append to `outputs/inspiration/bet-log.json`**

```json
{
  "bet_id": "BET-{NNN}",
  "run_date": "YYYY-MM-DD",
  "signal": "{diagnosis-linked signal context — metric, delta, market, period}",
  "current_state": "{plain-language description of sephora.com today in the relevant area}",
  "market_context": "{top market scan finding with source, or null if none found}",
  "prototype_idea": "{PM's stated prototype idea — exact words}",
  "target_metric": "{PM's stated metric}",
  "premortem": "{PM-confirmed failure scenario — PM's words}",
  "pm_odds": "{PM's stated confidence}"
}
```

If `bet-log.json` does not exist: create with `[]` then append.

**8c — Update `outputs/inspiration/cycle-state.json`** (overwrite):

```json
{
  "run_date": "YYYY-MM-DD",
  "current_step": "complete",
  "loop_initiated": true,
  "loop_completed": true,
  "gates_passed": [1],
  "active_bet_id": "BET-{NNN}",
  "target_metric": "{PM's stated metric}",
  "pm_confirmed_premortem": "{PM's confirmed scenario}",
  "pm_confirmed_idea": "{PM's stated idea}"
}
```

**8d — Write `outputs/inspiration/signal-brief.md`** (overwrite):

```markdown
# Inspiration Loop — Signal Brief {YYYY-MM-DD}

## KPI Signals
{confirmed signals table from signals.md}

## Current State — sephora.com
Feature area: {browse target}
{description}

## Market Scan
{signals with source citations, or "None found"}

## Bet Recorded
BET-{NNN} | Target: {metric} | PM odds: {odds}
Pre-mortem: {scenario}
Idea: {prototype idea}
```

Confirm to PM:
```
Gate 1 complete ✓
BET-{NNN} recorded | Target: {metric} | Odds: {odds}
Advancing to prioritisation...
```

**8e — Write to Confluence**

Target: PI space, `parent_id` from `config/atlassian.yml → page_id`
Title: `Inspiration Brief — YYYY-MM-DD`
New page per run — do not overwrite prior runs.

**Confluence output rules:**
- Do NOT include: BET-NNN IDs, PM odds label, "Pre-mortem:" header, signal IDs, dataset codes, agent names, or internal loop terminology
- PM's prototype idea goes verbatim under "What we want to try" — no wrapper language
- If no market signals were found in Step 5: omit the "What others are doing" section entirely
- Include a diagnosis anchor link to the Intelligence Loop page if `confluence_page_url` is available in `outputs/prioritisation/ranked-hypotheses.json`

Write body to `.tmp/inspiration-brief-body.md`:

```markdown
## Diagnosis context
{1-sentence plain-English summary of the favored diagnosis.
Link: [Intelligence Loop — {date}]({confluence_page_url, if available — otherwise omit link})}

## What sephora.com looks like today
{plain-language description of current UX state.
If inaccessible: "Current state not observed this run."}

## What others are doing
- {Source name} — {1-sentence description}. {URL}
- ...

## What we want to try
{PM's prototype idea — exact PM wording. No labels, no framing.}

_[date]_
```

Run the script:
```bash
python execution/write_confluence.py \
  --mode create \
  --space PI \
  --parent-id {page_id from config/atlassian.yml} \
  --title "Inspiration Brief — $(date +%Y-%m-%d)" \
  --body-file .tmp/inspiration-brief-body.md \
  --content-format wiki
```

Parse stdout JSON: record `page_id` and `url` into `outputs/inspiration/signal-brief.md` header.

If script exits non-zero:
- Exit 1 (401/403): surface auth error; instruct token rotation. Do NOT skip.
- Exit 2 (400): check title and parent ID; fix and retry once.
