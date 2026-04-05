# 11-feedback-agent — Feedback Triangulation (Step 2a)

## Role in pipeline

Agent 11 of the Phase 1 Intelligence Loop. Runs in parallel with 12-validation-agent after PM gate.
Triangulates confirmed signals from Agent 10 against qualitative and quantitative feedback sources:
Domo app reviews, Love Meter / NPS, CS tickets, and Search Terms.

Memory-first: checks `outputs/feedback/findings-store.json` before querying Domo.
Writes a findings summary to Confluence and local files for handoff to the diagnosis artifact and Agent 13.

```
outputs/signal-agent/pipeline-context.md  ──┐
config/domo.yml (feedback_datasets)         ├──▶  11-feedback-agent  ──▶  Confluence page
config/domo.yml (kpi_datasets.discovery)    │                         ──▶  outputs/feedback/findings.md
config/domo.yml (kpi_datasets.discovery)    ┘                         ──▶  outputs/feedback/findings-store.json (append)
                                                                      └──▶  outputs/diagnosis/diagnosis.json (via build_diagnosis_artifact.py)
```

---

## Trigger

Spawned by `/intelligence-loop` after PM confirms signal list at Agent 10 gate.
Can also be run standalone: "run feedback triangulation" / "triangulate signals".

---

## Agent Steps

### Step 1 — Load confirmed signals

Read `outputs/signal-agent/pipeline-context.md`.
Extract the confirmed signal list and the focus market/signal from PM gate (e.g. "AU signals").
All steps below filter to confirmed signals only — do not re-open signals excluded at the PM gate.

Define the **primary signal set** as: all confirmed signals for the focus market (AU in current cycle):
- AU App ATC Rate: -21% WoW
- AU iOS Sessions: -17% WoW
- AU Cart-to-Checkout: -8.2% WoW

Define the **secondary signal set** as: all other confirmed signals (other markets, TAM, HK, TH/ID/PH checkout improvement).

### Step 2 — Memory check (findings store)

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

### Step 3 — Query Domo feedback sources (if stale)

Query window: `config/domo.yml → query_windows.app_reviews` (30 days), `love_meter` (60 days), `cs_tickets` (14 days).
All queries MUST include a date range filter. Scope to AU where a market/country filter column exists.

Apply authenticity filter from `config/domo.yml → thresholds.app_review_authenticity` before reading any review text.
Apply verbatim sampling from `config/domo.yml → thresholds.verbatim_sample_max` — do not load full text corpora.
Check all dataset columns against `pii_excluded_columns` before querying. Halt source if PII column detected.

**3a — App Store Reviews (`901f1019-a2f0-4a55-a36e-6cbd7c875c9e`)**
Source type: dataset (SQL-queryable, scope: data).
Query: `SELECT rating, review_text, version, country, date FROM table WHERE date >= [start] AND date <= [end] AND country = 'AU' ORDER BY date DESC LIMIT 40`
Note: column names may differ — run `SELECT * FROM table LIMIT 1` to discover schema if `columns_discovered: false`.
After schema discovery: write columns back to `config/domo.yml → feedback_datasets.app_reviews` and set `columns_discovered: true`.

Aggregate:
- AU average rating (current 30 days vs prior 30 days)
- Top review themes — cluster by recurring phrases, group into 3–5 themes
- Look specifically for: add-to-cart friction, app performance, checkout, session/loading issues

**3b — Love Meter / NPS (`e76f6c94-d0be-4888-9726-125bbfb9a95d`)**
Source type: dataset (SQL-queryable, scope: data).
Already discovered: date_column = `created_at`, metrics = `["rating"]`.
Query: `SELECT country, AVG(rating) AS avg_rating, COUNT(*) AS responses FROM table WHERE created_at >= '[start]' AND created_at <= '[end]' AND country = 'AU' GROUP BY country`
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

### Step 4 — Theme and synthesise findings

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
- Do search terms show intent–fulfilment gaps?
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

### Step 4b — PM review gate

Before writing any output, surface the draft synthesis in chat:

```
*** AGENT 11 — FINDINGS REVIEW GATE ***

Draft findings ready for {N} issue areas.

Primary issues:
  1. {plain-English issue area} — evidence quality: {High/Medium/Low}
  2. {plain-English issue area} — evidence quality: {High/Medium/Low}

Off-signal risks: {N found / none}

Satisfied ratings: {markets with data / "no new data"}

Reply "publish" to write to Confluence and local files.
Reply "revise: {instruction}" to adjust before publishing.
Reply "skip confluence" to write local files only.

*** END GATE ***
```

Wait for PM response before proceeding to Step 5.

---

### Step 5 — Write outputs

**6a — Confluence (primary output)**

Target page: `https://sephora-asia.atlassian.net/wiki/spaces/PI/pages/64760119298/Cross+references`
Page ID: `64760119298` (PI space — "Cross references")

Write using `mcp__mcp-atlassian__confluence_update_page`. Overwrite on each run.
No source attribution. No PM-session content. No PII.

**Confluence output rules — apply before every write:**
- Do NOT include: hypothesis IDs (H-A, H-B, H-C), source status labels (FRESH/CACHED/CARD-ONLY), Evidence Quality table, pipeline step references, or agent names
- Issue area headings must be plain English describing the user problem — never an internal code ID
- Max 3 verbatim quotes per issue area; trim each to the key phrase (≤ 20 words)
- Source Status table stays in `findings.md` only — never written to Confluence
- Off-signal risks use plain-English headings — never "Risk 1 / Risk 2" or hypothesis IDs

Format:
```
## What users are reporting — [date]

### [Issue area — plain English, e.g. "Checkout blocked by out-of-stock gift item"]
[2–3 sentence synthesis of what users are experiencing.]
- "[key phrase from verbatim quote, ≤ 20 words]" ([market], [platform], [date])
- "[key phrase]" ([market], [platform], [date])

### [Issue area 2 — e.g. "Payment charged but order not created"]
[2–3 sentence synthesis.]
- "[key phrase]" ([market], [platform], [date])

...

## Satisfaction ratings
| Market | Rating | Responses | vs baseline |
|---|---|---|---|
| [market] | [avg] | [n] | [delta] |

_Ratings reflect completed purchases only — users blocked before checkout are not captured._

## Risks to watch
- **[Risk name in plain English]** — [1–2 sentence description. Recommended action.]
- ...

_[date]_
```

If Confluence write fails (401/403): surface auth error to PM, instruct token rotation. Do NOT skip.

**6b — `outputs/feedback/findings.md`** (overwrite each run)
Mirrors Confluence content for pipeline handoff to Agent 13.

**6c — `outputs/feedback/findings-store.json`** (append-only — never overwrite)
Append a new entry per queried source:
```json
{
  "queried_at": "YYYY-MM-DD",
  "source": "app_reviews | love_meter | cs_tickets | search_terms",
  "market": "AU",
  "signal_cycle": "YYYY-MM-DD",
  "summary": "1–2 sentence summary of key finding",
  "evidence_quality": "High | Medium | Low"
}
```
If `findings-store.json` does not exist: create it with an empty array `[]` then append.

---

## Output Contract

### Confluence — "Cross references" (primary output)
Page: `https://sephora-asia.atlassian.net/wiki/spaces/PI/pages/64760119298/Cross+references`
Page ID: `64760119298` (PI space)
Overwrite each run. Format: themed sections per signal. No source attribution. No PII.

### `outputs/feedback/findings.md`
Internal handoff to Agent 13. Overwrite each run. May include pipeline-internal fields not written to Confluence.

```markdown
# Feedback Findings — [date]
Focus: [primary signals]
Period: [date range]

## User-reported issues
### [Issue area — plain English]
[Synthesis of what users are experiencing — 2–3 sentences]
Key quotes:
- "[key phrase]" ([market], [platform], [date])
- "[key phrase]" ([market], [platform], [date])

### [Issue area 2]
...

## Satisfaction ratings
| Market | Rating | Responses | vs baseline |
|---|---|---|---|
...

## Risks to watch
- **[Risk name]** — [description + recommended action]

## Evidence quality (internal — not written to Confluence)
| Issue area | Evidence strength | Sources |
|---|---|---|
| [plain description] | High / Medium / Low | [sources] |

## Source status (internal — not written to Confluence)
| Source | Status | Notes |
|---|---|---|
| App Reviews | OK / FAILED / CACHED | [note] |
| Love Meter | OK / FAILED / CACHED | [note] |
| CS Tickets | OK / FAILED / CACHED | [note] |
| Search Terms | OK / FAILED / CACHED | [note] |
```

### `outputs/feedback/findings-store.json`
Append-only. Never overwrite. Format: JSON array of entries (see Step 6c).

---

## Configuration

```yaml
# config/domo.yml
feedback_datasets:        # app_reviews, love_meter, cs_tickets
kpi_datasets.discovery:   # search_terms (997f496f)
query_windows:            # per-source date windows
thresholds:
  findings_staleness_days: 7
  verbatim_sample_max
  app_review_authenticity
  signal_threshold_pct     # used for off-signal risk qualification

```

## Permissions

- Read: `outputs/signal-agent/pipeline-context.md`
- Read: `outputs/feedback/findings-store.json`
- Read: registered Domo feedback datasets only (`feedback_datasets` + `kpi_datasets.discovery`)
- Write: Confluence — target page (short URL `wiki/x/AgABFA8`, resolved at runtime)
- Write: `outputs/feedback/findings.md`
- Write: `outputs/feedback/findings-store.json` (append-only)
- No writes to Jira, signal outputs, or any source not listed above

## Error Handling

| Error | Action |
|---|---|
| `pipeline-context.md` missing | Halt — "Run /intelligence-loop Step 1 first" |
| Domo source query fails | Log failure; continue with remaining sources; note in output |
| PII column detected in schema | Halt that dataset; surface to PM; skip to next source |
| Unregistered dataset attempted | Hard error — surface to PM, do not query |
| CS Tickets card has no dataset access | Note card-only limitation; record what is visible; continue |
| Confluence write fails (401/403) | Surface auth error to PM; instruct token rotation; do not skip |
| Short URL unresolvable | Search PI space by title; create page if absent; surface resolved ID to PM |
| findings-store.json does not exist | Create with empty array `[]`; append first entry |
| All sources return no AU data | Surface to PM: "No AU feedback data found. Options: (1) widen date window, (2) check market filter columns, (3) proceed to Agent 13 without feedback evidence" |

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/feedback/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. country_column in app_reviews is 'country_name' not 'country'"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update this SKILL.md with the new constraint (schema correction, PII column, API limit)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
