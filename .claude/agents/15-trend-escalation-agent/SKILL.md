# 15-trend-escalation-agent — Signal Trend + Escalation

## Role in pipeline

Agent 15 of the Phase 1 Intelligence Loop. Runs after Agent 13 each cycle (or standalone on demand).
Watches signal strength and priority scores across cycles, identifies failures that are deteriorating
or being persistently ignored, and surfaces them as a structured escalation brief.

**No revenue assumptions. No hallucinated cost figures.**
Cost of inaction is expressed as priority debt score and session exposure — both grounded in
data already collected by Agents 12 and 13.

```
outputs/validation/signal-strength-store.json  ──┐
outputs/prioritisation/ranked-hypotheses.json   ├──▶  15-trend-escalation-agent
config/domo.yml (kpi_datasets.sessions)          │         │
Jira BAAPP (MCP read)                            ┘         ├──▶  outputs/trend/signal-trend.json (overwrite)
                                                            ├──▶  outputs/trend/trend-report.md (overwrite)
                                                            └──▶  Confluence escalation brief (append to cross-references)
```

---

## Trigger

Spawned by `/intelligence-loop` after Agent 13 completes.
Can also be run standalone: "run trend analysis", "check signal trends", "escalation report".

---

## Agent Steps

### Step 0 — Validate input freshness

Before loading any inputs, check that upstream outputs are current:

```bash
python execution/check_input_staleness.py \
  --file outputs/prioritisation/ranked-hypotheses.json \
  --threshold-days 7
```

Read the JSON output:
- If `stale: true`: surface to PM — "ranked-hypotheses.json is {age_days} days old (last updated: {last_modified}). Trend analysis may reflect an old cycle. Proceed, or re-run Agent 13 first?" — halt until PM responds.
- If `reason: file_not_found`: halt — "Run the intelligence loop through Agent 13 first".
- If `stale: false`: proceed.

---

### Step 1 — Load historical signal strength

Read `outputs/validation/signal-strength-store.json` — full append-only history from Agent 12.
If file is missing or has only one entry: note "insufficient history for trend — minimum 2 cycles needed".
Continue with what is available; flag single-cycle entries as "baseline only, no trend".

Build a per-`failure_id` timeline:
```
failure_id → [ {run_date, confidence, raw_score, verbatim_count}, ... ] ordered by run_date asc
```

### Step 2 — Load prioritisation history

Read `outputs/prioritisation/ranked-hypotheses.json` — full append-only history from Agent 13.
For each failure_id, extract across all cycles:
- `priority_score` per cycle
- `sprint_candidate` flag per cycle
- `jira_created` flag per cycle
- `jira_ticket` per cycle (null if not actioned)
- `cumulative_cycles_unactioned` (latest value)

### Step 3 — Check Jira for actioned tickets

For each failure_id that has `jira_ticket` not null in prioritisation history:
Query Jira: `mcp__mcp-atlassian__jira_get_issue` for each ticket key.
Check status — Done / In Progress / To Do / Backlog.

Update `times_actioned` and `last_actioned_date` with ground truth from Jira.
If Jira is inaccessible: use `ranked-hypotheses.json` `jira_created` flags as proxy; note limitation.

### Step 4 — Query session exposure (PM-gated)

To calculate current session exposure per failure, propose a Domo query:

```
*** AGENT 15 — SESSION EXPOSURE GATE ***

To calculate current session exposure for trend context:
Proposed query: Domain KPI — by session (29a01e0e)
  SQL: SELECT date, journey_sessions, pdp_sessions, atc_sessions
       FROM table WHERE date >= '{28 days ago}'
  Purpose: current % of sessions exposed to each failure's affected flow
  Registered: approved: true

Reply "approved" or "skip" (will use last known session % from Agent 13 history).
*** END GATE ***
```

If skipped: use most recent `impact_score` from `ranked-hypotheses.json` as session exposure proxy.

### Step 5 — Calculate trend per failure

For each failure_id with ≥2 cycles of history:

**Confidence trend**:
- All scores rising → `deteriorating` (failure is becoming more evidenced)
- Stable (±0.5 across cycles) → `stable`
- Scores falling → `improving` (evidence weakening — may be resolving)
- Mixed → `volatile`

**Priority score trend**:
- Latest score > first score → `escalating`
- Latest score < first score → `de-escalating`
- Within 10% across cycles → `stable`

**Priority debt score**:
```
priority_debt = latest_impact_score × latest_confidence_score × cumulative_cycles_unactioned
```
Max theoretical value unbounded — higher = more urgent.
This is the primary escalation signal: a failure that is Medium confidence, high impact, and has
been unactioned for 4 cycles scores higher priority debt than a new High confidence low-impact failure.

**Escalation flag** — set `escalate: true` if ANY of:
- `cumulative_cycles_unactioned` ≥ 3
- `confidence_trend` = `deteriorating` AND `cumulative_cycles_unactioned` ≥ 2
- `priority_score` ≥ 12 AND `jira_created` = false for ≥ 2 consecutive cycles
- `sprint_candidate` = true for ≥ 2 cycles with no Jira ticket created

### Step 6 — Suspicious signal check

Before writing output, apply filter:
- Confidence trend `deteriorating` with verbatim count unchanged (0 new verbatims since last cycle)
  → flag as "trend driven by scoring model, not new evidence — verify before escalating"
- Priority debt score spike >50% in one cycle with no new signal evidence
  → flag "rapid debt increase — check if scoring inputs changed"

Surface all flags to PM. Do not suppress.

### Step 7 — Write outputs

---

## Output Contract

### `outputs/trend/signal-trend.json`
**Overwrite** each run.

```json
{
  "generated_at": "YYYY-MM-DD",
  "cycles_analysed": 3,
  "session_exposure_source": "domo_query | agent13_history",
  "failures": [
    {
      "failure_id": 2,
      "description": "Stock display inaccuracy — OOS shown on in-stock items",
      "market": "AU",
      "version": "5.0.8",
      "first_seen_date": "YYYY-MM-DD",
      "cycles_in_history": 3,
      "confidence_history": [
        {"run_date": "YYYY-MM-DD", "confidence": "Low-Medium", "raw_score": 3},
        {"run_date": "YYYY-MM-DD", "confidence": "Medium", "raw_score": 4},
        {"run_date": "YYYY-MM-DD", "confidence": "Medium", "raw_score": 5}
      ],
      "confidence_trend": "deteriorating | stable | improving | volatile",
      "priority_score_history": [6.0, 9.0, 12.0],
      "priority_trend": "escalating | de-escalating | stable",
      "cumulative_cycles_unactioned": 3,
      "times_actioned": 0,
      "last_actioned_date": null,
      "jira_tickets": [],
      "jira_status": null,
      "session_exposure_pct": 18.0,
      "priority_debt_score": 54.0,
      "escalate": true,
      "escalation_reasons": [
        "3+ cycles unactioned",
        "confidence trend deteriorating"
      ],
      "suspicious_flag": false,
      "suspicious_reason": null
    }
  ],
  "summary": {
    "total_failures_tracked": 0,
    "escalation_candidates": 0,
    "improving": 0,
    "stable": 0,
    "single_cycle_baseline": 0,
    "suspicious_flagged": 0
  }
}
```

### `outputs/trend/trend-report.md`
**Overwrite** each run.

```markdown
# Signal Trend Report — {YYYY-MM-DD}
Cycles analysed: {N} | Escalation candidates: {N} | Improving: {N}

## Escalation Candidates
Failures requiring forced PM attention this cycle.

| Failure | Market | Ver | Confidence trend | Priority debt | Cycles unactioned | Jira status |
|---|---|---|---|---|---|---|
| Stock display inaccuracy | AU | 5.0.8 | deteriorating ↑ | 54 | 3 | none |

### {Failure description}
- **Pattern**: {confidence history summary}
- **Priority debt**: {score} — {plain English explanation}
- **Session exposure**: {%} of {market} PDP sessions
- **Why it hasn't been actioned**: {from lineage — never ranked / ranked but not approved / approved but no ticket}
- **Recommended action**: {force into sprint / assign spike / escalate to leadership}

## Stable / Improving
{brief table — failures not requiring escalation}

## Suspicious Flags
{any flags from Step 6}

## Single-cycle baselines (no trend yet)
{failures seen for first time this cycle}

*Generated by 15-trend-escalation-agent | {date}*
```

### Confluence escalation brief
**Append** to page `64760119298` (Cross references, PI space) when escalation candidates exist.
Skip Confluence write if zero escalation candidates — do not append empty sections.

Section format:
```markdown
## Signal Escalation Brief — {YYYY-MM-DD}
{N} failure(s) have been unactioned for ≥{N} cycles and require PM decision this sprint.

| Failure | Cycles unactioned | Priority debt | Recommended action |
|---|---|---|---|

### Why these matter
{1–2 sentence plain-English explanation of priority debt concept for stakeholders}
{No revenue figures. No GMV. Session exposure % and cycle count only.}

*Generated by 15-trend-escalation-agent | {date}*
```

---

## Configuration

```yaml
# config/domo.yml
kpi_datasets:
  sessions:
    - id: "29a01e0e-8ef8-476b-bdff-4090f1941e7f"
      approved: true
      # Used by Agent 15 for current session exposure calculation

# Escalation thresholds (add to config/domo.yml thresholds section):
thresholds:
  trend_escalation:
    min_cycles_for_trend: 2          # minimum cycles before trend is calculated
    unactioned_cycles_escalate: 3   # escalate if unactioned >= this
    deteriorating_unactioned: 2     # escalate if deteriorating + unactioned >= this
    priority_score_threshold: 12    # sprint candidate threshold (matches Agent 13)
```

---

## Permissions

- Read: `outputs/validation/signal-strength-store.json`
- Read: `outputs/prioritisation/ranked-hypotheses.json`
- Read: Jira BAAPP — issue read (status check only)
- Read: Domo `29a01e0e` (PM-gated)
- Write: `outputs/trend/signal-trend.json` (overwrite)
- Write: `outputs/trend/trend-report.md` (overwrite)
- Write: Confluence page `64760119298` — append only, escalation candidates only
- No writes to Jira, no writes to signal or prioritisation outputs

---

## Error Handling

| Error | Action |
|---|---|
| `signal-strength-store.json` missing | Halt — "Run at least one cycle of intelligence loop first" |
| Only 1 cycle in store | Note "baseline only" — write trend report with no trend calculations; useful for first-cycle reference |
| `ranked-hypotheses.json` missing | Note absence; compute trend from signal-strength-store only; skip lineage fields |
| Jira inaccessible | Use `jira_created` flags from ranked-hypotheses.json; note "Jira unverified" |
| PM skips session exposure gate | Use last known impact scores from Agent 13 history; note source |
| Domo query fails | Fall back to Agent 13 impact scores; continue |
| Zero escalation candidates | Write trend-report.md; skip Confluence append; note "no escalations this cycle" |
| Confluence write fails | Surface auth error to PM; do not retry silently |
| `outputs/trend/` missing | Create directory before writing |

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/trend/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. signal-strength-store.json schema changed — confidence field now nested"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update this SKILL.md with the new constraint (schema change, Jira API limit, config key rename)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
