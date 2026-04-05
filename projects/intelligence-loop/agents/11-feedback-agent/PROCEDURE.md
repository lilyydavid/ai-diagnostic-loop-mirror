# 11-feedback-agent — Procedure

Step-by-step execution. Resume from the labelled step when continuing a parked run.
Context: read POLICY.md for output contracts, permissions, and error handling.

---

## Step 1 — Load confirmed signals

Read `outputs/signal-agent/pipeline-context.md`.
Extract the confirmed signal list and the focus market/signal from PM gate (e.g. "AU signals").
All steps below filter to confirmed signals only — do not re-open signals excluded at the PM gate.

Define the **primary signal set** as: all confirmed signals for the focus market (AU in current cycle):
- AU App ATC Rate: -21% WoW
- AU iOS Sessions: -17% WoW
- AU Cart-to-Checkout: -8.2% WoW

Define the **secondary signal set** as: all other confirmed signals (other markets, TAM, HK, TH/ID/PH checkout improvement).

## Step 2 — Memory check (findings store)

Run the findings cache check script:

```bash
python execution/check_findings_cache.py \
  --store outputs/feedback/findings-store.json \
  --config config/domo.yml \
  --signal-date {today_YYYY-MM-DD}
```

Parse the JSON output:
- `fresh` list → skip Domo queries for those `source/market` pairs; use cached findings
- `stale` list → re-query those sources in Step 3
- `missing` list → query those sources in Step 3 (no prior data)

Log which sources were served from cache vs re-queried (use `stderr` output from the script).
If the script errors (missing config, bad JSON): halt — surface error to PM before querying Domo.

## Step 3 — Query Domo feedback sources (if stale)

Query window: `config/domo.yml → query_windows.app_reviews` (30 days), `love_meter` (60 days), `cs_tickets` (14 days).
All queries MUST include a date range filter. Scope to AU where a market/country filter column exists.

Apply authenticity filter from `config/domo.yml → thresholds.app_review_authenticity` before reading any review text.
Apply verbatim sampling from `config/domo.yml → thresholds.verbatim_sample_max` — do not load full text corpora.
Check all dataset columns against `pii_excluded_columns` before querying. Halt source if PII column detected.

**3a — App Store Reviews (`901f1019-a2f0-4a55-a36e-6cbd7c875c9e`)**
Source type: dataset (SQL-queryable, scope: data).
Query: `SELECT rating, review_text, version, country, date FROM table WHERE date >= [start] AND date <= [end] AND country = 'AU' ORDER BY date DESC LIMIT 40`
Note: actual date column = `date_created`; country column = `country_name` (full name e.g. 'Australia').
After schema discovery: write columns back to `config/domo.yml → feedback_datasets.app_reviews` and set `columns_discovered: true`.

Aggregate:
- AU average rating (current 30 days vs prior 30 days)
- Top review themes — cluster by recurring phrases, group into 3–5 themes
- Look specifically for: add-to-cart friction, app performance, checkout, session/loading issues

**3b — Love Meter / NPS (`e76f6c94-d0be-4888-9726-125bbfb9a95d`)**
Source type: dataset (SQL-queryable, scope: data).
Already discovered: date_column = `created_at`, country_column = `country` (full name e.g. 'Australia', not 'AU'), metrics = `["rating"]`.
Query: `SELECT country, AVG(rating) AS avg_rating, COUNT(*) AS responses FROM table WHERE created_at >= '[start]' AND created_at <= '[end]' AND country = 'Australia' GROUP BY country`
Note: `account_number` is NOT PII — safe to use as a count key.
Compare against MEMORY baseline: AU avg 4.67 (1,761 responses, Feb 10–Mar 10, 2026).
If `suggestion` column exists: sample up to 20 AU verbatims. Theme any negative suggestions.

**3c — CS Tickets (card `369925860`, parent page `515305475`)**
Source type: card (scope: dashboard).
Use `get-card` to retrieve card metadata — note card is on page 515305475, not registered as a standalone page.
If the card returns a datasourceId: use `query-dataset` with AU filter and 14-day window.
If no dataset access: note card-only read limitation in output; record card title and any visible summary.

**3d — Search Terms (`997f496f-9154-4f32-b746-8615261ad764`)**
Source: `config/domo.yml → kpi_datasets.discovery`.
Date column: `date_local`. Query window: 28 days.
Query: `SELECT search_term, SUM(frequency) AS search_volume, SUM(total_orders) AS orders, SUM(total_revenue) AS revenue FROM table WHERE date_local >= '[start]' AND date_local <= '[end]' GROUP BY search_term ORDER BY search_volume DESC LIMIT 50`
Note: this dataset does not have a country column — results are global. Filter interpretation to AU context by cross-referencing with AU session decline signals.
Look for: rising search volume with low order conversion (discovery demand without fulfilment), drop in high-intent search terms, new brand/category terms appearing.

**UX Research evidence — Jira-based:**
Query Jira for UXR observations relevant to confirmed signals:
```
project = "UXR" AND type = Observation AND status = Posted AND "user journey[checkboxes]" = "Checkout"
```
Note: UXR research is Jira-based, not Confluence-based. CQL confluence search returns 0 results — do not rely on it.

## Step 4 — Theme and synthesise findings

**4a — Cluster verbatims (deterministic)**

Before reasoning over verbatims, run the clustering script on all collected review/suggestion text:

```bash
# Save sampled verbatims to .tmp/verbatims.json as:
# [{"text": "...", "market": "AU", "platform": "iOS", "date": "2026-04-01"}, ...]

python execution/theme_feedback.py \
  --verbatims-file .tmp/verbatims.json \
  --max-themes 5 \
  --output .tmp/themes.json
```

Read `.tmp/themes.json`. Use the `themes` array as the authoritative structure for Step 4b.
Do not invent theme categories that the script did not find.
If `unclustered_count > 0`: scan the unclustered entries manually for any high-severity signals (payment, security, identity) — add as a separate note, not a theme.

**4b — Synthesise findings**

Organise findings into a structured synthesis using the script's theme output:

Also prepare diagnosis-layer evidence inputs for orchestration:
- Which rival diagnosis does each finding support, contradict, or leave unresolved?
- What segment, market, or journey step does the finding localise?
- What evidence would weaken the currently favored diagnosis?

**Primary signal findings** (AU focus — App ATC, iOS Sessions, Cart-to-Checkout):
- What does qualitative feedback say about AU app experience?
- Do app reviews correlate with ATC / session timing?
- Does Love Meter show sentiment degradation?
- Do search terms show intent–fulfilment gaps correlated with AU signals?

**Off-signal risk flags** (critical risks from any source NOT related to confirmed AU signals):
Scan all feedback for strong risk signals beyond the focus area.
A risk qualifies as off-signal if:
- It appears in 2+ independent sources
- OR it involves payment failure, security, or identity (high severity regardless of source count)
- OR it involves a different market with magnitude ≥ threshold (apply same signal thresholds from `config/domo.yml`)

If off-signal risks are found: surface them in a clearly labelled `## Off-Signal Risks` section.
Do NOT fold these into the primary findings — keep them separate so they don't dilute the AU focus.
Do NOT suppress or deprioritise high-severity off-signal risks.

**Evidence quality rating per primary signal:**
- High: 2+ independent sources corroborate (e.g. app reviews + Love Meter)
- Medium: 1 source corroborates
- Low: no corroboration found — flag as "needs further investigation"

## Step 4b — PM review gate

Before writing any output, surface the draft synthesis in chat:

```
*** AGENT 11 — FINDINGS REVIEW GATE ***

Draft findings ready for {N} issue areas.

Primary issues:
  1. {plain-English issue area} — evidence quality: {High/Medium/Low}
  2. {plain-English issue area} — evidence quality: {High/Medium/Low}

Off-signal risks: {N found / none}

Satisfied ratings: {markets with data / "no new data"}

Reply "publish" to write findings to local files and advance to diagnosis.
Reply "revise: {instruction}" to adjust before publishing.

*** END GATE ***
```

Wait for PM response before proceeding to Step 5.

## Step 5 — Write outputs

Agent 11 does not write to Confluence directly. Feedback evidence flows into the diagnosis artifact
(`outputs/diagnosis/diagnosis.json`) and from there into Agent 13's Intelligence Loop page.
This keeps all reasoning — evidence, rival explanations, favored diagnosis, experiments — in one
coherent page rather than split across disconnected Confluence pages.

**5a — `outputs/feedback/findings.md`** (overwrite each run)
Full structured findings for pipeline handoff to Agent 13 and `build_diagnosis_artifact.py`.

**5b — `outputs/feedback/findings-store.json`** (append-only — never overwrite)
Append a new entry per queried source (see POLICY.md for schema).
If `findings-store.json` does not exist: create it with an empty array `[]` then append.
