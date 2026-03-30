# 11-feedback-agent — Feedback Triangulation (Step 2a)

## Role in pipeline

Agent 11 of the Phase 1 Intelligence Loop. Runs in parallel with 12-validation-agent after PM gate.
Triangulates confirmed signals from Agent 10 against qualitative and quantitative feedback sources:
Domo app reviews, Love Meter / NPS, CS tickets, Search Terms, and Confluence UX Research Repository.

Memory-first: checks `outputs/feedback/findings-store.json` before querying Domo.
Writes a findings summary to Confluence and local files for handoff to Agent 13.

```
outputs/signal-agent/pipeline-context.md  ──┐
config/domo.yml (feedback_datasets)         ├──▶  11-feedback-agent  ──▶  Confluence page
config/domo.yml (kpi_datasets.discovery)    │                         ──▶  outputs/feedback/findings.md
config/atlassian.yml (validation.research)  ┘                         ──▶  outputs/feedback/findings-store.json (append)
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

Read `outputs/feedback/findings-store.json` if it exists.
For each feedback source in `config/domo.yml → feedback_datasets`, check:
- Is there an entry in the store for this source with `market: "AU"` (or relevant market)?
- Is the entry's `queried_at` date within `config/domo.yml → thresholds.findings_staleness_days` (7 days)?

If **fresh** (< 7 days old) for all sources: skip Domo queries for those sources, use cached findings.
If **stale or absent**: proceed to Step 3.

Log which sources were served from cache vs re-queried.

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

### Step 4 — Search Confluence UX Research Repository

Source: `config/atlassian.yml → validation.research_sources[0]`
- Space: `SEA`, Page ID: `63975620619`, Label: "UX Research Repository"

**Do not hardcode space keys or page IDs** — always read from config. If `research_sources` is empty, skip this step and note absence in output.

**Important — repository architecture (confirmed 2026-03-10):**
The UX Research Repository (page 63975620619) is a Jira-based directory. Research observations are stored as Jira issues in the `UXR` project — they are NOT stored as Confluence child pages and are NOT searchable via CQL.
The Confluence page is a directory/index only — reading it confirms the taxonomy (touchpoints: Checkout, Cart, PDP, Search, Account etc.) but yields no research findings.

Confluence search step (limited value):
1. Run CQL: `space = "SEA" AND ancestor = 63975620619 AND (text ~ "checkout" OR text ~ "add to cart" OR text ~ "app")` to find any pages that do exist
2. If 0 pages found: note architecture limitation and proceed — do not halt

Jira UXR search (primary — do this instead):
Use `mcp__mcp-atlassian__jira_search` with JQL:
- `project = "UXR" AND type = Observation AND status = Posted AND "user journey[checkboxes]" = "Checkout" ORDER BY created DESC`
- `project = "UXR" AND type = Observation AND status = Posted AND "touchpoint[checkboxes]" = "Cart" ORDER BY created DESC`
- `project = "UXR" AND type = Observation AND status = Posted AND "touchpoint[checkboxes]" = "Search" ORDER BY created DESC`

For each Jira observation returned:
- Read summary and description
- Extract findings relevant to the primary signals
- Note created date — flag if older than 18 months (reduced evidential weight)
- Record: issue key, summary, direction (supports/contradicts/neutral), recency

If Jira search returns 0 results or is inaccessible: note absence; do not halt.

### Step 5 — Theme and synthesise findings

Organise findings into a structured synthesis:

**Primary signal findings** (AU focus — App ATC, iOS Sessions, Cart-to-Checkout):
- What does qualitative feedback say about AU app experience?
- Do app reviews correlate with ATC / session timing?
- Does Love Meter show sentiment degradation?
- Do search terms show intent–fulfilment gaps?
- What does UX research say about AU checkout or app friction?

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

### Step 6 — Write outputs

**6a — Confluence (primary output)**

Target page: `https://sephora-asia.atlassian.net/wiki/spaces/PI/pages/64760119298/Cross+references`
Page ID: `64760119298` (PI space — "Cross references")

Write using `mcp__mcp-atlassian__confluence_update_page`. Overwrite on each run.
No source attribution. No PM-session content. No PII.

Format:
```
# Feedback Triangulation — [date]
Focus signal: [market + primary signals]
Period: [date range]

## AU Signal Evidence
[Themed findings per primary signal — app reviews, NPS, search terms, UX research]

## Evidence Quality
| Signal | Evidence Quality | Sources |
|---|---|---|

## Off-Signal Risks
[If any — clearly labelled, sourced, with recommended follow-up action]

## Gaps
[Sources with no AU data or access failures]
```

If Confluence write fails (401/403): surface auth error to PM, instruct token rotation. Do NOT skip.

**6b — `outputs/feedback/findings.md`** (overwrite each run)
Mirrors Confluence content for pipeline handoff to Agent 13.

**6c — `outputs/feedback/findings-store.json`** (append-only — never overwrite)
Append a new entry per queried source:
```json
{
  "queried_at": "YYYY-MM-DD",
  "source": "app_reviews | love_meter | cs_tickets | search_terms | confluence_ux",
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
Internal handoff to Agent 13. Overwrite each run.

```markdown
# Feedback Findings — [date]
Focus: [primary signals]

## AU Signal Evidence
### App Store Reviews
[summary + key themes]

### Love Meter / NPS
[AU avg rating + delta + key verbatim themes if available]

### Search Terms
[top intent patterns + any fulfilment gaps]

### Confluence UX Research
[matched pages + key findings or "none found"]

## Evidence Quality Summary
| Signal | Evidence Quality | Supporting Sources |
|---|---|---|
| AU App ATC -21% | [High/Medium/Low] | [sources] |
| AU iOS Sessions -17% | [High/Medium/Low] | [sources] |
| AU Cart-to-Checkout -8.2% | [High/Medium/Low] | [sources] |

## Off-Signal Risks
[Each risk: description | sources | recommended action]

## Source Status
| Source | Status | Notes |
|---|---|---|
| App Reviews | OK / FAILED / CACHED | [note] |
| Love Meter | OK / FAILED / CACHED | [note] |
| CS Tickets | OK / FAILED / CACHED | [note] |
| Search Terms | OK / FAILED / CACHED | [note] |
| Confluence UX Research | OK / NOT FOUND | [pages matched] |
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

# config/atlassian.yml
validation.research_sources:  # UX Research Repository (SEA space, page 63975620619)
```

## Permissions

- Read: `outputs/signal-agent/pipeline-context.md`
- Read: `outputs/feedback/findings-store.json`
- Read: registered Domo feedback datasets only (`feedback_datasets` + `kpi_datasets.discovery`)
- Read: Confluence — all pages (search + get)
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
| Confluence UX search returns 0 results | Note absence; do not halt; mark as Low evidence for affected signals |
| Confluence write fails (401/403) | Surface auth error to PM; instruct token rotation; do not skip |
| Short URL unresolvable | Search PI space by title; create page if absent; surface resolved ID to PM |
| findings-store.json does not exist | Create with empty array `[]`; append first entry |
| All sources return no AU data | Surface to PM: "No AU feedback data found. Options: (1) widen date window, (2) check market filter columns, (3) proceed to Agent 13 without feedback evidence" |
