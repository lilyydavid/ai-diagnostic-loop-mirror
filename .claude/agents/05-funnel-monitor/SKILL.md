# /funnel-monitor — Ecommerce Funnel Monitor (Agent 1)

## Role in pipeline
Agent 1 of 4. Reads Domo dashboard screenshots and Confluence pages, extracts funnel metrics,
produces a stakeholder report and four structured output files consumed by downstream agents.

```
Agent 1: funnel-monitor  →  outputs/funnel-monitor/
         ├── pipeline-context.md       → read by ALL agents
         ├── validation-hypotheses.md  → read by Agent 2 (validation) + Agent 3 (github-reader)
         ├── lno.md                    → read by product/business team
         └── memory/metrics-history.json      → read by Agent 1 on next run (WoW comparison)
Agent 2: validation      →  reads pipeline-context + validation-hypotheses
Agent 3: github-reader   →  reads pipeline-context + validation-hypotheses (code_area field)
Agent 4: jira-pr-writer  →  reads Agent 2 + Agent 3 outputs + pipeline-context
```

## Trigger
User runs `/funnel-monitor` or asks to "check the funnel", "monitor funnel metrics", or "pull funnel data".

## Schedule
Runs every **Thursday**. Each run covers the **previous 7 days (Thursday through Wednesday)**.
Date range is computed dynamically — never hardcoded.

---

## Funnel Stages

| Stage | Metrics |
|---|---|
| Awareness / Traffic | Sessions, unique visitors, traffic sources, bounce rate, app engagement |
| Product Discovery | PDP view rate, search CVR, share of PDP views, sign-in rate |
| Add to Cart | ATC rate (user level), add-to-cart volume, rewards redemption |
| Checkout / Purchase | Cart→Checkout CTR, checkout success rate, AOV, payment failure rate, address completion, C&C rate |
| Fulfilment | Shipped rate, delivered on-time rate |

---

## Agent Steps

### Step 1 — Compute date range
- `week_start` = today − 7 days
- `week_end`   = today − 1 day
- `week_number` = ISO week number
- `current_month` = YYYY-MM (used to filter images)

### Step 2 — Load prior week metrics
Read `outputs/funnel-monitor/memory/metrics-history.json` if it exists.
Extract last week's values for each metric — used in the scorecard WoW column and the Action Impact section.
If the file does not exist (first run), continue without WoW data.

### Step 3 — Discover Confluence pages
Search all spaces for: `funnel conversion ecommerce checkout ATC product discovery traffic sessions revenue AOV abandonment domo dashboard metrics KPI`

Also always check the primary Domo embed page: `64742228008` (PI space).

Collect all matching page IDs, titles, and last-modified dates.

### Step 4 — Extract text metrics
For each page, fetch content and extract numbers/percentages mapped to funnel stages with source attribution.

### Step 5 — Download and analyse images
For each page, list attachments via:
```
GET /wiki/rest/api/content/{pageId}/child/attachment?limit=50&expand=version
```
Keep only attachments where `version.when` starts with `{current_month}`. Download with `-L` to follow redirects.

For each image, visually extract metrics. Keep: KPI cards, funnel charts, Domo dashboards, A/B result slides.
Skip: UX surveys, infra cost dashboards, product photos, mockups.

Confidence: **High** = value + label + date range all readable. **Medium** = value readable, label/date ambiguous. **Low** = skip (note in gaps).

**Extract week-over-week from trend charts:** When reading weekly bar/line charts, always extract both the current week value and the prior week value. Record both. If `memory/metrics-history.json` is missing, these chart-extracted prior-week values are the WoW source.

### Step 6 — Merge and deduplicate
Prefer image over text for same metric. Flag conflicts. Use most recent source when duplicated across pages.

### Step 7 — Filter suspicious metrics
Before writing any output, apply this filter to every extracted metric.
If ANY of the following are true, mark the metric as `suspicious: true` — it goes to **Data Quality Notes** only, excluded from all main tables, risk register, and team actions:

- YoY change is **>50% in either direction** AND there is no confirmed product launch or definition change explaining it
- Value is exactly **0%** (almost always a tracking break, not a real conversion)
- Value is **identical across all segments** (web/app/combined) — suggests a roll-up or filter error

### Step 8 — Identify anomalies and hypotheses
For each non-suspicious metric with a significant signal (YoY drop >15%, absolute value below known threshold), generate a hypothesis following the Output Contract schema.

Classify each:
- **Likely data/tracking issue** → `output_type: overhead` — delegate to data team, no hypothesis
- **Likely real product issue** → `output_type: jira_story`
- **Likely code regression** → `output_type: pr`

### Step 9 — Write stakeholder report to Confluence
Use `mcp__mcp-atlassian__confluence_update_page` on page `64742948865`.

**Report sections (stakeholder-facing only — no LNO, no hypotheses):**

**1. Situation** — one sentence. State the dominant signal plainly.

**2. Action Impact** _(omit on first run; present from week 2 onwards)_
For each prior week's Leverage action (L1, L2 etc.), show whether the targeted metric recovered, degraded, or held steady vs last week.
Format per row: `L{n} — {action title}: {metric} {last week value} → {this week value} ({Δ with direction arrow})`
Use 🟢 if improving, 🔴 if degrading, ⚪ if insufficient data.

**3. Team Actions** — Ecommerce team | Store / Retail team. Specific, owned, time-bound.

**4. Risk Register** — 🔴 High / 🟡 Medium / 🟢 Watch. Suspicious metrics excluded.

**5. Weekly Scorecard**
Columns: Stage | Metric | This Week | Last Week | WoW | YoY | Status
- Last Week and WoW come from `memory/metrics-history.json` or weekly trend charts
- Suspicious metrics excluded — see Data Quality Notes
- Status: 🟢 On track / 🟡 Watch / 🔴 Act

**6. Monthly Sessions Trend** — rolling 3-month table

**7. Data Quality Notes**
Metrics excluded from the report due to suspicious signals. One line each.
Format: `{Metric}: {value} — excluded: {reason}. Action: {who should investigate}.`

**Footer:** `_Next run: {date} · Covers: {period}_`
No source attribution in footer.

### Step 10 — Write pipeline outputs
Write all four files to `outputs/funnel-monitor/`. Overwrite pipeline-context, validation-hypotheses, lno on each run. **Append** to memory/metrics-history.json (never overwrite history).

---

## Output Contract

### `outputs/funnel-monitor/memory/metrics-history.json`
Append one entry per run. Used by Agent 1 on the next run for WoW comparison and Action Impact.

```json
{
  "weeks": [
    {
      "week": "2026-W09",
      "period": "2026-02-25/2026-03-03",
      "generated": "2026-03-05",
      "leverage_actions": ["L1: Cart-to-checkout investigation", "L2: Payment retry flow", "L3: Address completion audit", "L4: Checkout success war room"],
      "metrics": {
        "sessions_week": 3352617,
        "app_engagement_rate": 0.2753,
        "search_cvr_combined": 0.031,
        "pdp_view_rate_combined": 2.28,
        "share_pdp_nonlanding": 0.337,
        "atc_rate_combined": 0.194,
        "cart_to_checkout_ctr_combined": 0.1709,
        "checkout_success_rate_combined": 0.3925,
        "aov_combined": 58.76,
        "payment_failure_rate": 0.1109,
        "address_completion_rate": 0.5863,
        "cnc_pct_ecomm": 0.0751,
        "orders_shipped_rate": 0.9434,
        "orders_ontime_rate": 0.9493
      }
    }
  ]
}
```

### `outputs/funnel-monitor/pipeline-context.md`
Shared context read by all agents. Includes metrics snapshot, risk map, Confluence pages scanned, product context, and active hypotheses index. See current file for format.

### `outputs/funnel-monitor/validation-hypotheses.md`
Read by Agent 2 and Agent 3. One entry per hypothesis with: hypothesis, validation_criteria (confirms/denies), confluence_search_terms, code_area, suggested_jira_fields, output_type. See current file for full schema.

### `outputs/funnel-monitor/lno.md`
Read by product/business teams. L/N/O tables. N items must have escalation thresholds. O items must name the delegate and expected output.

---

## Configuration
```yaml
# config/atlassian.yml
space_name: "PI"
funnel_monitor_page_id: "64742948865"
domo_embed_page_id: "64742228008"
```

Credentials: `CONFLUENCE_API_TOKEN` from `.mcp.json`, username `ldavid@sephora.sg`.

## Permissions
- Read: all Confluence pages and attachments
- Write: page `64742948865` only (Confluence)
- Write: `outputs/funnel-monitor/` directory

## Error Handling
- No pages found → report in chat, skip Confluence write and pipeline outputs
- Image not from current month → skip silently
- Image download 403/404 → skip, note in pipeline-context data gaps
- MCP write 401 → fall back to Confluence REST API directly
- `memory/metrics-history.json` missing → proceed without WoW, note in scorecard as "—"
- Never write outside `64742948865` or `outputs/funnel-monitor/`
