# 13-prioritisation-agent — Procedure

Step-by-step execution. Resume from the labelled step when continuing a parked run.
Context: read POLICY.md for output contracts, permissions, and error handling.

---

## Step 0 — Validate input freshness

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

## Step 1 — Load inputs

1. Read `outputs/signal-agent/pipeline-context.md` — load the cycle signal and its severity
2. Read `outputs/diagnosis/diagnosis.json` — load observation, failure surface, rival diagnoses, favored diagnosis, and falsification criteria
3. Read `outputs/validation/experiment-designs.json` — load all hypotheses and experiment designs from Agent 12
4. Read `outputs/prioritisation/ranked-hypotheses.json` if it exists — load history for lineage
5. Resolve config: `config/atlassian.yml` → `config/atlassian.team.yml` → `config/atlassian.local.yml`. Use `growth_agent.jira_project_key`, `growth_agent.epic_key`, `growth_agent.story_labels`.

If `experiment-designs.json` is missing → halt: "Run /intelligence-loop Steps 1–2 first"
If `pipeline-context.md` is missing → halt: "Run /intelligence-loop Step 1 first"
If `diagnosis.json` is missing → halt: "Run the diagnosis stage first"
If no history file → first run, initialise lineage from scratch

---

## Step 1b — Load Agent 20 enrichment (optional)

Read `outputs/inspiration/bet-log.json` if it exists.

**Staleness check:** read the `run_date` field of the most recent entry.
Compare against staleness threshold in `config/atlassian.yml → inspiration_loop.signal_staleness_days` (default: 7).

| Condition | Action |
|---|---|
| File absent | Skip silently — set `inspiration_enrichment_available: false` |
| File present but stale | Skip — note "Agent 20 output stale ({N} days)" in ranked-hypotheses.md header |
| File present and within staleness window | Load most recent entry; set `inspiration_enrichment_available: true` |

If loaded, extract:
- `market_context` — top market scan finding from Agent 20
- `pm_odds` — PM's stated confidence in the bet
- `target_metric` — the metric Agent 20's bet is targeting

**Signal domain matching:** compare Agent 20's `target_metric` against each hypothesis's connected signal. If overlap: tag that hypothesis with the enrichment data. Non-blocking — Agent 13 proceeds whether or not enrichment is available.

---

## Step 2 — Connect signal to experiments

For each experiment in `experiment-designs.json`, build the full chain:
```
[Signal] metric drop → [Hypothesis] proposed cause → [Experiment] proposed test
```

Extract per experiment: the specific signal movement, the hypothesis, the A/B test design (control, variant, segment scope, success metric, SP estimate), and Agent 12 scores.

If an experiment does not connect to any signal movement: note the gap — do not silently drop the experiment.
If Agent 12 flagged a Domo validation requirement: include with "pending data" flag rather than excluding.

---

## Step 3 — Score and rank experiments

Score each experiment. Every score must cite its source.

**Confidence (from Agent 12)**
| Agent 12 confidence | Score |
|---|---|
| High | 3 |
| Medium | 2 |
| Low | 1 |

**Impact (from Agent 12 + signal)**
If the signal for this hypothesis is a hard block → floor at 3 regardless of Agent 12's rating.
| Agent 12 impact | Score |
|---|---|
| High | 3 |
| Medium | 2 |
| Low | 1 |

**Scope (from Agent 12 SP estimate, inverted)**
| SP estimate | Score |
|---|---|
| 1 | 3 |
| 2–3 | 2 |
| >3 | 1 |

**Priority score:** `priority_score = confidence × impact × scope  (max 27)`

Rank by `priority_score` descending. Ties: signal severity (larger drop ranks higher), then SP ascending.
Tie-breaker if scores still equal: Agent 20 `pm_odds` match (if enrichment available and matched).

---

## Step 4 — Apply lineage

For each experiment, check `ranked-hypotheses.json` history by `failure_id`:
- `first_seen_date`, `times_ranked`, `times_actioned`, `cycles_unactioned`

If no history: first_seen_date = today, times_ranked = 1, times_actioned = 0.
Experiments with `cycles_unactioned ≥ 2` and `priority_score ≥ 8` are flagged for Agent 15 escalation.

---

## Step 5 — PM approval gate

Present the full signal→hypothesis→experiment table:

```
*** AGENT 13 — EXPERIMENT APPROVAL GATE ***

Cycle signal: {signal summary}
Ranked: {N} | Sprint viable (SP ≤ 3): {N} | Pending data: {N} | Needs spike: {N}

## Full ranked table
| ID | Signal | Hypothesis | Experiment | Market | SP | C | I | S | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
...

## Sprint Candidates (score ≥ 12, SP ≤ 3)
## Backlog Candidates (score < 12 or SP > 3)
## Pending Data Validation
## Needs Spike (no experiment design)
## Escalation flags (≥2 cycles unactioned, score ≥ 8)

Reply:
  "approve all"      — all sprint candidates → Jira + Confluence
  "approve {IDs}"    — listed IDs only
  "skip jira"        — record prioritisation only, no Jira or Confluence this cycle
  "edit"             — modify before approving

*** END GATE ***
```

Wait for PM response before writing any outputs.

---

## Step 5a — Code grounding check (before any Jira creation)

**Run before creating any Jira story, regardless of PM approval.**

Load `outputs/validation/read-audit.log`. Extract the list of files actually read.

**Check 1 — File path verification**
For each PM-approved experiment, check every entry in `code_evidence.files` against the audit log:
- If file.path appears in read-audit.log → verified
- Else → UNVERIFIED

**Check 2 — grep_anchor verification (on verified files only)**
For each verified file with a `grep_anchor` field, run Grep for the anchor string in the repo:
- Match found → anchor confirmed
- No match → strip that file from "Where in the code"

| State | Action |
|---|---|
| All files verified + anchors confirmed | Proceed to Step 6 |
| Partially verified | Proceed with verified files only |
| No files verified | Hard block — route to needs-spike.md |
| confidence = Low | Hard block — route to needs-spike.md |
| read-audit.log missing | Hard block all stories |

Surface blocked stories to PM before proceeding:
```
*** AGENT 13 — CODE GROUNDING CHECK ***
{N} story/stories blocked — code references could not be verified:
  H{id}: "{description}" — {reason}
    → Routed to needs-spike.md. No Jira story created.
{N} story/stories cleared for creation.
Proceed with verified stories? ("yes" / "no, cancel all")
*** END GROUNDING CHECK ***
```

Wait for PM confirmation before Step 6.

**Critical rule: never infer, guess, or reconstruct file paths.** If a file path is not in `read-audit.log`, it does not go in the Jira story.

---

## Step 6 — Create Jira stories (PM-approved experiments only)

### Step 6-pre — Dedup check (MANDATORY before any story creation)

For carry-forward hypotheses (those with `lineage.times_ranked > 1` or prior `jira_ticket` in history):
1. Use `mcp__mcp-atlassian__jira_get_issue` on the prior ticket key.
2. If **open** (status ≠ Closed/Done): add a comment with updated cycle date and new evidence — do NOT create a new story. Record `jira_ticket: "{existing_key}"`.
3. If **closed**: create a new story and note the prior ticket key in the description.

For **new hypotheses** (first cycle): the deterministic label `intel-loop-{project_key_lower}-{hid_lower}` (e.g. `intel-loop-baapp-h1`) is added to every story by `create_jira_stories.py`. Before calling `jira_create_issue`, search: `project = {project_key} AND labels = "intel-loop-{project_key_lower}-{hid_lower}" AND status not in (Done, Closed) ORDER BY created DESC` — if a match is found, comment on it instead of creating a new story.

**Hard rule: never write a Jira ticket key to any local file unless that key has been verified via `jira_get_issue` in the same session.**

Run the script:
```bash
python execution/create_jira_stories.py \
  --approved-ids {space-separated hypothesis IDs} \
  --experiment-designs outputs/validation/experiment-designs.json \
  --pipeline-context outputs/signal-agent/pipeline-context.md \
  --audit-log outputs/validation/read-audit.log \
  --history outputs/prioritisation/ranked-hypotheses.json \
  --findings outputs/feedback/findings.md
```

Parse stdout JSON. For each entry in `operations`:
- `op: "create"` — run dedup search first using `dedup_search_labels` field, then call `mcp__mcp-atlassian__jira_create_issue` with `create_payload` if no open match found
- `op: "check_and_comment_or_create"` — call `mcp__mcp-atlassian__jira_get_issue` on `prior_ticket`; if open → `mcp__mcp-atlassian__jira_add_comment`; if closed → `mcp__mcp-atlassian__jira_create_issue`

Record each created/updated ticket key in memory for Step 7. Do not invent ticket keys.

**Pre-write: decomposition check**
Before creating any story, check if `ab_test.variant` describes multiple independent deliverables. Indicators: contains ` + `, lists multiple services, or Step 5a found evidence spanning services.
If compound: split into sub-stories H-D1, H-D2 etc., each with one Proposed Change, one set of Acceptance Criteria, and one SP estimate. Link sub-stories to each other in Jira.

**Story description template:**
```
## Problem
{metric dropping, magnitude, window, markets affected}

## Evidence
- Funnel signal: {metric value, WoW/YoY delta, markets}
- Code review: {confidence_reason — plain English, cite repo + function name}
- Why this matters: {impact_reason — plain English}
- User signals: {from findings.md — omit section entirely if none}

## Proposed Change
{specific, unambiguous description from ab_test.variant only. One change only.}

## Where in the code
⚠️ Only include files confirmed by code review verification.
- Repo: {name}
- File: {path} — {function}
- Change: {description from ab_test.variant}

## Market Context
_(Include only if enrichment matched. Omit section entirely if not.)_
{market_context}
PM confidence: {pm_odds}

## Acceptance Criteria
- [ ] {primary metric} improves by ≥{MDE}
- [ ] No regression in {related metric}
- [ ] Change is behind a feature flag (if touching core funnel)
- [ ] Unit test added for changed function

## Story Points
{N} SP — Quick Win / Backlog

## Related
- Cycle: {YYYY-MM} | Markets: {markets} | Rollback: {method}
- Prior ticket (if carry-forward): {BAAPP-NNN}
```

Fields:
- `summary`: `[{repo-name}] {action title}` — max 70 chars. Do NOT include hypothesis ID (H1 etc.) in the summary.
- `additional_fields`: `{"labels": [..., "intel-loop-baapp-{hid_lower}"], "epicKey": "{epic_key}"}` — use `epicKey`, NOT `parent`
- Do NOT include `priority` in `additional_fields`

---

## Step 7 — Write Confluence page

After all Jira stories are created, publish a single Confluence page.

**Config:**
- `space_key`: from `config/atlassian.yml → space_name` (PI)
- `parent_id`: from `config/atlassian.yml → page_id`
- `title`: `Intelligence Loop — {YYYY-MM-DD}`

**Confluence output rules:**
- Do NOT include: C/I/S score columns, hypothesis IDs (H-A, H-B), agent names, dataset codes, BET-NNN IDs, pipeline step references, source attribution
- Rival explanations in plain English only — no internal classification labels
- Experiment descriptions from `ab_test.variant` only — no new inference
- Jira ticket links are the only internal IDs that should appear on the page
- Verbatim user quotes: max 2 per evidence bullet, ≤ 20 words each

Write body to `.tmp/intelligence-loop-body.md`:

```markdown
## What we're seeing
{2–3 sentence plain-English summary — metric, direction, market, period.}

---

## Why we think this is happening

**Evidence reviewed**
- Users reported: {2–3 bullet themes from findings.md}
- Code review found: {1–2 bullet plain-English finding — cite repo + function name if verified}

**Three explanations we considered**
1. {rival_diagnosis_1 — plain English}
2. {rival_diagnosis_2}
3. {rival_diagnosis_3}

**Favoured explanation**
{2–3 sentences. Include counterfactual: "If X were not the case, we would expect to see Y."}

**What would change our view**
{falsification_criteria — 1–2 sentences}

---

## What we're testing
| # | Issue | Proposed experiment | Markets | Story points | Ticket |
|---|---|---|---|---|---|
...

---

## Next sprint
| Ticket | What | Markets | SP |
...

{1–2 sentence plain-English rationale for why these are the priority}

---

## Backlog
| Ticket | What | Markets | SP | Why deferred |
...

---

_[date]_
```

Run the script:
```bash
python execution/write_confluence.py \
  --mode create \
  --space PI \
  --parent-id {page_id from config/atlassian.yml} \
  --title "Intelligence Loop — $(date +%Y-%m-%d)" \
  --body-file .tmp/intelligence-loop-body.md \
  --content-format wiki
```

Parse stdout JSON: record `page_id` and `url` into `outputs/prioritisation/ranked-hypotheses.json` entry.

Error handling: Exit 1 (401/403) → surface auth error, instruct token rotation, local outputs still written. Exit 2 (400) → check title and parent ID; fix and retry once.

---

## Step 7b — Raise GitHub PRs (PM-triggered, per ticket)

Triggered on-demand when PM adds a comment to a Jira ticket: `raise PR -> {repo-name}`

1. Fetch the ticket: `mcp__mcp-atlassian__jira_get_issue(issue_key="{ticket_key}")`
   Write to `.tmp/jira-{ticket_key}.json`.

2. Run the script:
```bash
python execution/raise_github_pr.py --ticket {ticket_key}
```

3. Parse stdout JSON:
   - `op: "fetch_required"` → write `.tmp/jira-{ticket}.json` first, re-run
   - `op: "error"` → surface the `error` field to PM
   - `op: "create_pr"` → execute `execution_steps` array in order:
     1. Verify access via `mcp__github__get_file_contents` — if 403, halt
     2. Create branch via `mcp__github__create_branch`
     3. Create draft PR via `mcp__github__create_pull_request`
     4. Comment PR URL back to Jira ticket via `mcp__mcp-atlassian__jira_add_comment`

Always create as draft (`draft: true`). Never push code changes.

---

## Step 8 — Write local outputs

Write local files after Confluence page is published (see POLICY.md for schemas):
- `outputs/prioritisation/ranked-hypotheses.json` (append)
- `outputs/prioritisation/ranked-hypotheses.md` (overwrite)
- `outputs/prioritisation/needs-spike.md` (overwrite)
- `outputs/jira-writer/created-tickets.md` (overwrite)
