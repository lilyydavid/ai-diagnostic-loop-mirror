# 13-prioritisation-agent — Experiment Prioritisation (Step 3)

## Role in pipeline

Agent 13 of the Phase 1 Intelligence Loop. Runs after the shared diagnosis artifact has been built from Agent 11 and Agent 12 outputs.

Connects the cycle signal to each hypothesis (confirmed and emergent) and its experiment
design. Ranks experiments so the PM can decide which to proceed with. Creates Jira stories
for approved experiments and publishes a Confluence summary page with Jira links.
Nothing goes to Jira or Confluence without PM approval at the gate.

```
outputs/signal-agent/pipeline-context.md     ──┐
outputs/diagnosis/diagnosis.json             ──┤
outputs/validation/experiment-designs.json   ──┤──▶  13-prioritisation-agent
outputs/prioritisation/ranked-hypotheses.json──┤         │
  (history — lineage)                          │         │
outputs/inspiration/bet-log.json  (optional) ──┘         │
  (Agent 20 — market context + PM odds)                   │
                                              *** PM GATE (approve experiments) ***
                                                          │
                              ┌───────────────────────────┼──────────────────────────┐
                              ↓                           ↓                          ↓
              Jira stories (one per              outputs/prioritisation/      Confluence page
              approved experiment)               ranked-hypotheses.json       PI space — ranked
              under epic_key                     (append)                     experiments + Jira links
                                                 ranked-hypotheses.md
                                                 (overwrite)
                                                 needs-spike.md (overwrite)
```

---

## Trigger

Spawned by `/intelligence-loop` after `outputs/diagnosis/diagnosis.json` has been built.
Standalone: "prioritise experiments", "rank hypotheses", "run prioritisation".

---

## Agent Steps

### Step 0 — Validate input freshness

Before loading any inputs, check that upstream outputs are current:

```bash
python execution/check_input_staleness.py \
  --file outputs/validation/experiment-designs.json \
  --threshold-days 3

python execution/check_input_staleness.py \
  --file outputs/diagnosis/diagnosis.json \
  --threshold-days 3
```

For each file: if `stale: true`, surface to PM — "{file} is {age_days} days old (last updated: {last_modified}). Proceed, or re-run upstream agents first?" — halt until PM responds.
If `reason: file_not_found`: halt with the appropriate upstream instruction.
If both are fresh: proceed.

---

### Step 1 — Load inputs

1. Read `outputs/signal-agent/pipeline-context.md` — load the cycle signal and its severity
2. Read `outputs/diagnosis/diagnosis.json` — load observation, failure surface, rival diagnoses, favored diagnosis, and falsification criteria
3. Read `outputs/validation/experiment-designs.json` — load all hypotheses and experiment designs from Agent 12, including emergent hypotheses from hypothesis set 2
4. Read `outputs/prioritisation/ranked-hypotheses.json` if it exists — load history for lineage
5. Resolve config: `config/atlassian.yml` → `config/atlassian.team.yml` → `config/atlassian.local.yml`. Use `growth_agent.jira_project_key`, `growth_agent.epic_key`, `growth_agent.story_labels`.

If `experiment-designs.json` is missing → halt: "Run /intelligence-loop Steps 1–2 first"
If `pipeline-context.md` is missing → halt: "Run /intelligence-loop Step 1 first"
If `diagnosis.json` is missing → halt: "Run the diagnosis stage and build outputs/diagnosis/diagnosis.json before prioritisation"
If no history file → first run, initialise lineage from scratch

---

### Step 1b — Load Agent 20 enrichment (optional)

Read `outputs/inspiration/bet-log.json` if it exists.

**Staleness check:** read the `run_date` field of the most recent entry (highest `bet_id`).
Compare against today using the staleness threshold in `config/atlassian.yml → inspiration_loop.signal_staleness_days` (default: 7).

| Condition | Action |
|---|---|
| File absent | Skip silently — set `inspiration_enrichment_available: false` |
| File present but most recent `run_date` > staleness threshold days old | Skip — note "Agent 20 output stale ({N} days)" in ranked-hypotheses.md header; set `inspiration_enrichment_available: false` |
| File present and within staleness window | Load most recent entry; set `inspiration_enrichment_available: true` |

If loaded, extract:
- `market_context` — top market scan finding from Agent 20 (string or null)
- `pm_odds` — PM's stated confidence in the bet (string, e.g. "60%", "long shot")
- `target_metric` — the metric Agent 20's bet is targeting (used to match signal domain)

**Signal domain matching:** compare Agent 20's `target_metric` against each hypothesis's connected signal. If Agent 20's target metric overlaps with a hypothesis's signal metric, tag that hypothesis with the enrichment data. If no hypothesis matches, enrichment is loaded but not applied.

This step is **non-blocking** — Agent 13 proceeds normally whether or not enrichment is available or matched.

---

### Step 2 — Connect signal to experiments

For each experiment in `experiment-designs.json`, build the full chain:

```
[Signal] metric drop → [Hypothesis] proposed cause → [Experiment] proposed test
```

Extract per experiment:
- The specific signal movement it is trying to explain (from `pipeline-context.md`)
- The hypothesis (confirmed or emergent, from Agent 12)
- The A/B test design: control, variant, segment scope, success metric, SP estimate
- Agent 12 scores: Confidence, Impact, Scope

If an experiment does not connect to any signal movement in `pipeline-context.md`, note
the gap — do not silently drop the experiment.

If Agent 12 has flagged a Domo validation requirement for any hypothesis, include it in
the ranked output with a "pending data" flag rather than excluding it.

---

### Step 3 — Score and rank experiments

Score each experiment across three dimensions. Every score must cite its source.

**Confidence (from Agent 12)**
Use Agent 12's confidence rating directly. No modification.

| Agent 12 confidence | Score |
|---|---|
| High | 3 |
| Medium | 2 |
| Low | 1 |

**Impact (from Agent 12 + signal)**
Combine Agent 12's impact rating with signal severity from `pipeline-context.md`.
If the signal for this hypothesis is a hard block (users cannot complete the action at
all) → floor at 3 regardless of Agent 12's rating.

| Agent 12 impact | Score |
|---|---|
| High | 3 |
| Medium | 2 |
| Low | 1 |

**Scope (from Agent 12 SP estimate, inverted)**
Smaller experiments rank higher — easier to ship, lower blast radius.

| SP estimate | Scope tier | Score |
|---|---|---|
| 1 | Tight | 3 |
| 2–3 | Moderate | 2 |
| >3 | Complex | 1 |

**Priority score**
```
priority_score = confidence × impact × scope  (max 27)
```

Rank by `priority_score` descending. On ties, rank by signal severity (larger metric
drop ranks higher), then by SP ascending (tighter scope breaks further ties).

**Tie-breaker — Agent 20 pm_odds (if enrichment available and matched):**
If two hypotheses share the same `priority_score` and signal severity after the above rules, and one of them matches Agent 20's `target_metric` domain, that hypothesis ranks higher. Note the tiebreak source in the ranked output as "Agent 20 pm_odds: {value}".

---

### Step 4 — Apply lineage

For each experiment, check `ranked-hypotheses.json` history by `failure_id`:

- `first_seen_date` — earliest cycle this hypothesis appeared
- `times_ranked` — how many cycles it has appeared without being actioned
- `times_actioned` — cycles where a Jira ticket was created
- `cycles_unactioned` — `times_ranked` − `times_actioned`

If no history: first_seen_date = today, times_ranked = 1, times_actioned = 0.

Experiments with `cycles_unactioned ≥ 2` and `priority_score ≥ 8` are flagged for
Agent 15 escalation tracking.

---

### Step 5 — PM approval gate

Present the full signal→hypothesis→experiment table. PM decides which to proceed with.

```
*** AGENT 13 — EXPERIMENT APPROVAL GATE ***

Cycle signal: {signal summary}
Ranked: {N} | Sprint viable (SP ≤ 3): {N} | Pending data: {N} | Needs spike: {N}

## Full ranked table

| ID | Signal | Hypothesis | Experiment | Market | SP | C | I | S | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | ... | ... | ... | AU | 2 | High | High | 2 | 18 | Hard block |
| H4 | ... | ... | ... | All | 2 | High | High | 2 | 18 | Active experiment |
| H7 | ... | ... | ... | SG | 1 | **Low** | Med | 3 | **6** | ⚠️ No code evidence — will be blocked from Jira |
...

C = Confidence · I = Impact · S = Scope (inverted SP) · Score = C×I×S (max 27)

## Sprint Candidates (score ≥ 12, SP ≤ 3)
[subset of table above]

## Backlog Candidates (score < 12 or SP > 3)
[subset]

## Pending Data Validation
| ID | Hypothesis | Blocked on | Action |

## Needs Spike (no experiment design)
| ID | Hypothesis | Why unscoped |

## Escalation flags (≥2 cycles unactioned, score ≥ 8)
| ID | Hypothesis | Cycles unactioned | Score |

Reply:
  "approve all"      — all sprint candidates → Jira + Confluence
  "approve {IDs}"    — listed IDs only (e.g. "approve H1, H4, H2")
  "skip jira"        — record prioritisation only, no Jira or Confluence this cycle
  "edit"             — modify before approving

*** END GATE ***
```

Wait for PM response before writing any outputs.

---

### Step 5a — Code grounding check (before any Jira creation)

**Run this step before creating any Jira story, regardless of PM approval.**

Load `outputs/validation/read-audit.log`. Extract the list of files actually read.

**Check 1 — File path verification**

For each PM-approved experiment, check every entry in `code_evidence.files` against the audit log:

```
for each file in experiment.code_evidence.files:
  if file.path appears in read-audit.log → verified
  else → UNVERIFIED
```

**Check 2 — grep_anchor verification (run after Check 1, on verified files only)**

For each verified file that has a `grep_anchor` field, run Grep for the anchor string in the repo at the path confirmed in `repos.local.yml`:

```
for each verified file with a grep_anchor:
  grep grep_anchor in repo → found → anchor confirmed
                           → not found → anchor UNCONFIRMED
```

| Grep result | Action |
|---|---|
| Match found | Confirmed — proceed with full file reference in story |
| No match (identifier not found) | Strip that file from "Where in the code"; note "function not confirmed by re-verification" |
| All files in a story fail anchor check | Hard block — route to `needs-spike.md`; surface to PM: "Code claims could not be re-verified. Story requires engineering investigation before implementation." |

If `grep_anchor` is absent for a file entry, skip Check 2 for that file — Check 1 path verification is sufficient.

**Classification (after both checks):**

| State | Definition | Action |
|---|---|---|
| All files verified + anchors confirmed | Every path in audit log; every anchor found | Proceed to Step 6 — story creation allowed |
| Partially verified | ≥1 file verified, ≥1 unverified | Proceed — but use ONLY verified files in "Where in the code"; mark unverified files as excluded |
| Verified paths but anchor unconfirmed | File was read but grep_anchor not found | Strip that file from "Where in the code" — function name may be inaccurate |
| No files verified | `code_evidence.files` is empty, or no entry appears in audit log | **Hard block** — do not create a Jira story; route to `needs-spike.md`; surface to PM |
| `confidence = Low` | Confidence set to Low (no matching code found) | **Hard block** — do not create a Jira story; route to `needs-spike.md`; surface to PM |
| `read-audit.log` missing | File does not exist | **Hard block all stories** — "Code review audit log is missing. Cannot verify code grounding. Run intelligence loop Steps 1–2 first." |

**Surface blocked stories to PM before proceeding:**

```
*** AGENT 13 — CODE GROUNDING CHECK ***

{N} story/stories blocked — code references could not be verified against the code review audit log:

  H{id}: "{description}" — {reason: no files verified / confidence Low / audit log missing}
    → Routed to needs-spike.md. No Jira story created.

{N} story/stories cleared for creation:
  H{id}: "{description}" — {N} verified file(s)
    → "Where in the code" will use: {verified file paths only}

Proceed with verified stories? ("yes" / "no, cancel all")

*** END GROUNDING CHECK ***
```

Wait for PM confirmation before Step 6.

**Critical rule: never infer, guess, or reconstruct file paths.** If a file path is not in `read-audit.log`, it does not go in the Jira story. No exceptions.

---

### Step 6 — Create Jira stories (PM-approved experiments only)

#### Step 6-pre — Dedup check (MANDATORY before any story creation)

For every approved hypothesis, check whether an open Jira ticket already exists before creating a new one.

**Carry-forward hypotheses** (those with `lineage.times_ranked > 1` or referencing a prior `jira_ticket` in `ranked-hypotheses.json`) MUST be checked first:

1. Use `mcp__mcp-atlassian__jira_get_issue` on the prior ticket key from lineage history.
2. If the ticket is **open** (status ≠ Closed/Done): do NOT create a new story. Instead:
   - Add a comment to the existing ticket with: the updated cycle date, any new evidence from this cycle's code review in plain English (cite repo + function name where relevant), and whether the root cause understanding has changed. One paragraph — no score tables, no internal file references, no agent names.
   - Record `jira_ticket: "{existing_key}"` in the output — never invent a new ticket number.
3. If the ticket is **closed**: create a new story as normal and note the prior ticket key in the description.
4. For **new hypotheses** (first cycle): search `mcp__mcp-atlassian__jira_search` with JQL `project = BAAPP AND summary ~ "{hypothesis keyword}" AND status != Closed ORDER BY created DESC` to catch any manually created tickets covering the same issue before creating a new one.

**Hard rule: never write a Jira ticket key to any local file unless that key has been verified via `jira_get_issue` in the same session.** No ticket numbers from memory or prior context.

For each approved experiment, create one Jira Story using `mcp__mcp-atlassian__jira_create_issue` only if the dedup check above confirms no open ticket exists.

**Pre-write: decomposition check**

Before creating any story, check whether `ab_test.variant` (from `experiment-designs.json`) describes multiple independent deliverables. Indicators: contains ` + `, lists multiple services, or Step 5a found evidence spanning services that were not all surveyed.

If a hypothesis is compound:
- Split into one story per atomic deliverable
- Assign sub-IDs: H-D1, H-D2, H-D3
- Each sub-story must have exactly one Proposed Change, one set of Acceptance Criteria, and one SP estimate
- Link sub-stories to each other in Jira
- Note the dependency relationship in each sub-story's Scope section: "Prerequisite: {sub-story}" or "Independent — can ship in any order"

Do not create a single story that requires multiple engineers, multiple services, or multiple independent acceptance criteria.

**Classification:**
- SP ≤ 3 → Quick Win Story, labels from `growth_agent.story_labels`
- SP > 3 → Backlog Story, label from `growth_agent.backlog_label`

**Fields:**
- `project_key`: from config `growth_agent.jira_project_key`
- `issue_type`: Story
- `summary`: `[Growth] {concise action title}` — max 70 chars. Do not include the hypothesis ID (H1, H-A3, etc.) in the summary.
- `additional_fields`: `{"labels": [...], "epicKey": "{epic_key}"}` — use `epicKey`, NOT `parent`
- Do NOT include `priority` in `additional_fields` — causes field validation error

**Story description template:**
```
## Problem
{metric dropping, magnitude, window, markets affected}

## Evidence
- Funnel signal: {metric value, WoW/YoY delta, markets — from pipeline-context.md}
- Code review: {confidence_reason from experiment-designs.json — plain English, cite repo + function name}
- Why this matters: {impact_reason from experiment-designs.json — plain English}
- User signals: {app reviews / CS tickets / Love Meter findings from findings.md — omit section entirely if none}

## Proposed Change
{specific, unambiguous description — sourced from experiment-designs.json ab_test.variant only.
One change only. If this is a sub-story, the parent hypothesis is noted in Related below.}

## Scope — this ticket only
{one sentence on what is NOT in scope if related sub-stories exist — omit section entirely if standalone}

## Where in the code
⚠️ Only include files confirmed by code review verification. Never infer, guess, or reconstruct
   file paths. If a file path is not confirmed, omit it.

- Repo: {name}
- File: {path} — {function}
- File: {path} — {function}
- Change: {description from ab_test.variant — no new inference}

If no verified files: replace this section with:
"Code location not yet confirmed. Engineering investigation required before implementation begins."

## Market Context
_(Include only if enrichment is available and matched to this hypothesis's signal domain. Omit section entirely if not.)_
{market_context}
PM confidence: {pm_odds}

## Acceptance Criteria
- [ ] {primary metric} improves by ≥{MDE from experiment-designs.json ab_test.minimum_detectable_effect}
- [ ] No regression in {related metric}
- [ ] Change is behind a feature flag (if touching core funnel)
- [ ] Unit test added for changed function

## Story Points
{N} SP — Quick Win / Backlog

## Related
- Cycle: {YYYY-MM} | Markets: {markets} | Rollback: {method from ab_test.rollback}
- Prior ticket (if carry-forward): {BAAPP-NNN}
```

Record each created ticket key in memory for Step 7.

---

### Step 7 — Write Confluence page

After all Jira stories are created, publish a Confluence summary page using
`mcp__mcp-atlassian__confluence_create_page`.

**Config:**
- `space_key`: from `config/atlassian.yml → space_name`
- `parent_id`: from `config/atlassian.yml → page_id`
- `title`: `Intelligence Loop — Prioritised Experiments {YYYY-MM}`
- `emoji`: 🎯
- `content_format`: markdown

**Confluence output rules — apply before every write:**
- Do NOT include: C/I/S score columns, Score Key section, Priority Debt table, Inspiration Loop Enrichment section, hypothesis IDs (H-A, H-B, H-C) in the main table, agent names, or pipeline chain in the footer
- Strip all agent references from experiment descriptions before writing (BET-NNN IDs, "Agent 12", "Agent 20")
- If Agent 20 market context is available and matched: inline it as a natural sentence in the experiment description — do not create a separate section
- Jira ticket links are the only internal IDs that should appear on the page

**Page sections:**

```markdown
## What we're seeing
{2–3 sentence plain-English summary of the cycle signal — no metric dataset codes, no signal IDs}

---

## Experiments

| # | Issue | Proposed experiment | Markets | Story points | Ticket |
|---|---|---|---|---|---|
| 1 | {plain description of the problem} | {plain description of the test} | {markets} | {SP} | [{BAAPP-NNN}]({url}) |
...

---

## Next sprint
| Ticket | What | Markets | SP |
|---|---|---|---|
| [{BAAPP-NNN}]({url}) | {1-line plain description} | {markets} | {SP} |

{1–2 sentence plain-English rationale for why these are the priority this cycle}

---

## Backlog
| Ticket | What | Markets | SP | Why deferred |
|---|---|---|---|---|
| [{BAAPP-NNN}]({url}) | {description} | {markets} | {SP} | {plain reason: scope too large / needs spike / pending data} |

---

_[date]_
```

---

### Step 8 — Write local outputs

Write local files after Confluence page is published.

---

## Output Contract

### `outputs/prioritisation/ranked-hypotheses.json`
**Append-only** — one entry per cycle run. Never overwrite history.

```json
{
  "run_date": "YYYY-MM-DD",
  "cycle_signal": "description from pipeline-context.md",
  "pm_approved": true,
  "approved_ids": ["H1", "H4", "H2"],
  "confluence_page_id": "64768147490",
  "confluence_page_url": "https://sephora-asia.atlassian.net/spaces/PI/pages/...",
  "entries": [
    {
      "rank": 1,
      "failure_id": "H1",
      "description": "hypothesis description",
      "market": "AU",
      "signal_connected": "ATC rate -21% WoW AU",
      "experiment_summary": "one-line description of the A/B test",
      "sp_estimate": 2,
      "sprint_viable": true,
      "confidence_score": 3,
      "confidence_source": "Agent 12 — High",
      "impact_score": 3,
      "impact_source": "Agent 12 — High / hard block",
      "scope_score": 2,
      "scope_source": "Agent 12 — SP 2 / Moderate",
      "priority_score": 18.0,
      "jira_created": true,
      "jira_ticket": "BAAPP-463",
      "jira_url": "https://sephora-asia.atlassian.net/browse/BAAPP-463",
      "deployed_date": null,
      "post_deploy_metric_delta": null,
      "pending_data_validation": false,
      "needs_spike": false,
      "inspiration_market_context": null,
      "inspiration_pm_odds": null,
      "lineage": {
        "first_seen_date": "YYYY-MM-DD",
        "times_ranked": 1,
        "times_actioned": 1,
        "cycles_unactioned": 0
      }
    }
  ]
}
```

### `outputs/prioritisation/ranked-hypotheses.md`
**Overwrite** each run. Standardised signal→hypothesis→experiment table.

```markdown
# Prioritised Experiments — {YYYY-MM-DD}
Cycle signal: {signal} | Ranked: {N} | Sprint viable: {N} | PM approved: {IDs or no}

---

## Signal → Hypothesis → Experiment → Notes

| ID | Signal | Hypothesis | Experiment | Market | SP | C | I | S | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | ... | ... | ... | AU | 2 | High | High | 2 | **18** | Hard block — ATB fully replaced |
...

---

## Sprint Candidates  (score ≥ 12, SP ≤ 3)
| Rank | ID | Experiment | Market | SP | Score |
...

## Backlog Candidates  (score < 12 or SP > 3)
...

## Pending Data Validation
...

## Needs Spike
...

*Generated by 13-prioritisation-agent | {date}*
```

### `outputs/prioritisation/needs-spike.md`
**Overwrite** each run. Emergent hypotheses or entries where no experiment design exists.

### `outputs/jira-writer/created-tickets.md`
**Overwrite** each run. Log of all Jira stories created this cycle.

```markdown
# Jira Tickets Created — {YYYY-MM-DD}
Epic: {epic_key} | Project: {project_key} | Cycle: {YYYY-MM}

## Quick Win Stories ({N})
| Key | Summary | SP | Hypothesis | Confidence | Score |
...

## Backlog Stories ({N})
...

## Deferred (not approved this cycle)
| Hypothesis | Reason |
...
```

---

## Configuration

```yaml
# config/atlassian.yml
space_name: "PI"
page_id: "64742785027"          # parent for Confluence page creation

growth_agent:
  jira_project_key: "BAAPP"
  epic_key: "BAAPP-461"
  story_labels: ["growth-agent", "quick-win", "intelligence-loop"]
  backlog_label: "growth-backlog"
```

---

## Permissions

- Read: `outputs/signal-agent/pipeline-context.md`
- Read: `outputs/validation/experiment-designs.json`
- Read: `outputs/validation/read-audit.log` — **required for code grounding check; absence blocks all Jira creation**
- Read: `outputs/prioritisation/ranked-hypotheses.json` (history)
- Read: `outputs/inspiration/bet-log.json` — **optional enrichment from Agent 20; absence or staleness is non-blocking**
- Read: `config/atlassian.yml`, `config/atlassian.team.yml`, `config/atlassian.local.yml`
- Write: `outputs/prioritisation/ranked-hypotheses.json` (append-only)
- Write: `outputs/prioritisation/ranked-hypotheses.md` (overwrite)
- Write: `outputs/prioritisation/needs-spike.md` (overwrite)
- Write: `outputs/jira-writer/created-tickets.md` (overwrite)
- Write: Jira stories under configured `epic_key` — **only after PM approval**
- Write: Confluence page in configured `space_name` under `page_id` — **only after PM approval**
- No writes to any repo or memory file

---

## Error Handling

| Error | Action |
|---|---|
| `experiment-designs.json` missing | Halt — "Run Steps 1–2 of intelligence loop first" |
| `pipeline-context.md` missing | Halt — "Run Step 1 of intelligence loop first" |
| `read-audit.log` missing | Hard block all Jira creation — "Code review audit log missing. Cannot verify code grounding." Surface to PM; route all approved stories to needs-spike.md |
| All files for a story are unverified (not in audit log) | Hard block that story — route to needs-spike.md; surface to PM at Step 5a gate; do not create Jira story |
| All grep_anchors for a story fail re-verification | Hard block that story — route to needs-spike.md; surface to PM: "Code claims could not be re-verified. Engineering investigation required." |
| Confidence = Low for an approved story | Hard block that story — route to needs-spike.md; surface at Step 5a gate; no Jira story without code evidence |
| Partially verified files | Proceed with verified files only in "Where in the code"; exclude unverified paths; note exclusions in story |
| Experiment has no signal connection | Note gap; include in ranked output with "signal not mapped" flag |
| Emergent hypothesis has no experiment design | Place in needs-spike.md with reason |
| Scores missing for an entry | Set confidence = Low, impact = Low; note "scores absent" |
| No history file | First run — initialise lineage from scratch |
| `bet-log.json` absent or stale | Skip Agent 20 enrichment silently; set `inspiration_market_context: null`, `inspiration_pm_odds: null`; no impact on scoring |
| Agent 20 `target_metric` matches no hypothesis | Load enrichment but do not apply; note "Agent 20 signal domain unmatched" in ranked-hypotheses.md header |
| PM responds "skip jira" | Record prioritisation only; set `jira_created: false`; skip Steps 6–7 |
| Jira create returns 401 | Report credentials error; do not retry |
| Jira create returns 400 | Log error with response body; skip that story; continue with remaining |
| `priority` field in Jira additional_fields causes error | Remove `priority` from additional_fields — omit entirely |
| `parent.key` in Jira additional_fields causes error | Use `epicKey` field instead of `parent` |
| Confluence create fails | Log error; local outputs still written; note Confluence step failed in created-tickets.md |
| All entries in needs-spike | Surface to PM: "No scoreable experiments this cycle. Experiment designs may be incomplete — re-run Steps 1–2 of the intelligence loop." |
| `outputs/prioritisation/` missing | Create directory before writing |
| `outputs/jira-writer/` missing | Create directory before writing |

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/prioritisation/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. epicKey field causes 400 — use parent.key instead for project X"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update this SKILL.md with the new constraint (Jira field validation, Confluence auth, config key)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
