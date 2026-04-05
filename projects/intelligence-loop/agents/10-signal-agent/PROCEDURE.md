# 10-signal-agent — Procedure

Step-by-step execution. Resume from the labelled step when continuing a parked run.
Context: read POLICY.md for output contracts, permissions, and error handling.

---

## Step 1 — Load registry

Read `config/domo.yml`. Extract all approved KPI sources:
- `kpi_pages` where `approved: true`
- `kpi_cards` where `approved: true`
- `kpi_datasets` — iterate over all domain groups (`satisfaction`, `sessions`, `funnel`, `engagement`, `discovery`, `identity`, and any future groups). Collect all entries where `approved: true`.

Check `access_control: strict` — any source not in the registry is off-limits. Do not query it.

For each dataset entry, check `columns_discovered`:
- `false` → schema discovery required on first query (see Step 3).
- `true` → use the `metrics` array directly to build SELECT. No discovery call needed.

## Step 2 — Compute query windows

For each source, determine the date window from `config/domo.yml → query_windows`.
Use source-specific window if `query_window_days` is set on the entry; otherwise use the type default.
Every query MUST include a date range filter. No unbounded queries.

## Step 3 — Query KPI sources

**Important — `get-page-cards` and `get-card` return metadata only, not live metric values.**
Use `get-dashboard-signals` for all page sources. It chains page → cards → datasets → rows in one call and is the only reliable way to retrieve live numbers.

**If PM provides a dashboard URL (e.g. `https://sephora-sg.domo.com/page/391829894`):**
1. Extract the numeric page ID from the URL path segment `/page/{id}`.
2. Check whether that page ID is registered in `config/domo.yml → kpi_pages` with `approved: true`.
   - If **not registered**: surface to PM — "Page {id} is not in the approved registry. Add it to `config/domo.yml` under `kpi_pages` with `approved: true`, then re-run." Do not query.
   - If **registered**: proceed.
3. Call `get-dashboard-signals` with `pageIdOrUrl` = the extracted ID and `queryWindowDays` from `config/domo.yml → query_windows.kpi_pages`.

**Pages with `discover_cards: true` (from registry):**
- First: call `get-page` to get current `cardIds` array and total count.
- Check `outputs/signal-agent/card-index.json`. If it exists for this page AND `total_cards` matches the current `cardIds.length`: skip the full `get-card` scan — use the cached index directly. This saves ~172 API calls on repeat runs.
- If card count has changed (new cards added): run `get-card` only for IDs not present in the cached index, append to index, update `total_cards` and `last_scanned`.
- If no index exists (first run): scan all cards in parallel batches of 20, build the index, write to `outputs/signal-agent/card-index.json`.
- Note: `get-card` returns card metadata only (title, type) — no datasource IDs. KPI card values require the underlying dataset to be registered separately in `kpi_datasets`.
- For cards with a `dataset_id` in the index: skip `get-card` entirely. Look up the dataset in `kpi_datasets` by ID and query it directly using the domain-grouped registry.

**Registered cards (`kpi_cards`):**
- Use `get-card` to get card metadata and extract `datasources[0].dataSetId`.
- Then use `query-dataset` with a date-bounded SQL query to get live values.
- Do NOT rely on `get-card` alone — it returns metadata, not values.

**Registered datasets (`kpi_datasets`):**
- If `columns_discovered: true`: build `SELECT [metric columns] FROM dataset WHERE [date_column] BETWEEN ...` using the `metrics` array. No schema call needed.
- If `columns_discovered: false`: run `SELECT * FROM dataset LIMIT 1` first to retrieve the schema. Then:
  1. Check all column names against `pii_excluded_columns`. If any PII column is detected: halt that dataset, surface to PM, skip to next.
  2. Identify metric columns (non-date, non-id, numeric). Write them back to `config/domo.yml` under the dataset's `metrics` array and set `columns_discovered: true`. This persists for all future runs.
  3. Build the date-bounded SELECT using discovered columns.
- Query via `query-dataset` with the constructed SQL and date range filter.

Extract per source:
- Metric name and value
- Period-over-period delta (WoW, MoM as available)
- Market / platform breakdown
- Data freshness (`dataCurrentAt` or latest date in result rows)

**On query failure:** log failure with reason; call `python execution/retry_queue.py --write-failure --source-id {id} --source-name "{name}" --agent 10-signal-agent --step "Step 3" --error "{error_message}"`; continue with remaining sources.

**Traffic channel query — run for every cycle alongside funnel datasets:**
Source: `29a01e0e` (Domain KPI by Session) — uses `traffic_channel_lv1`, `traffic_channel_lv2`, `traffic_channel_lv3` dimensions.

Query (current week):
```sql
SELECT country, device_type, traffic_channel_lv1, traffic_channel_lv2,
  SUM(journey_sessions) AS sessions, SUM(order_sessions) AS orders
FROM table
WHERE date >= [current_week_start] AND date <= [current_week_end]
GROUP BY country, device_type, traffic_channel_lv1, traffic_channel_lv2
ORDER BY country, device_type, sessions DESC
```
Run an identical query for the prior week window for WoW comparison.

From the results, compute per market × channel:
- Session share % = channel sessions / total journey sessions
- CVR% = order_sessions / journey_sessions
- WoW session delta % and WoW CVR delta %

Flag channels where session share shifted ≥ 10 pp WoW (large mix shift — affects aggregate CVR interpretation).
Flag channels where CVR dropped ≥ 5 pp WoW (channel-specific conversion failure).
Known context: Retention channel surges during member campaigns are expected — note if lv1 = "Retention" and delta is large; surface to PM to confirm whether a campaign was running.

## Step 4 — Apply signal threshold

Prefer deterministic execution for this post-query stage. After raw KPI values are collected, first run `execution/normalize_signal_inputs.py` per `directives/normalize_signal_inputs.md` to flatten query results into a stable payload. Then run `execution/build_signal_report.py` per `directives/build_signal_report.md` to apply config-driven thresholds and produce stable `signals.md` and `pipeline-context.md` outputs.

For each metric, look up threshold from `config/domo.yml → thresholds.signal_threshold_pct`.
Match metric to type (`conversion_rate`, `sessions`, `revenue`, `nps_score`, `ratings`).
Use `default` if type not matched.

Keep metrics where absolute movement ≥ threshold. Drop below-threshold movements — do not surface them.

## Step 5 — Flag suspicious metrics

For each metric above threshold, apply suspicious checks from `thresholds.suspicious_metric`:
- YoY movement > `yoy_flag_pct` (50%)
- Value is exactly 0%
- Value is identical across all segments

If any check triggers: mark metric `suspicious: true` with reason.
**Do not suppress.** Surface all suspicious metrics to PM with flag and reason.
`action: surface_to_pm` — PM decides whether to include or exclude from signal list.

## Step 6 — Build funnel tables

Prefer deterministic execution here as well. Once the required aggregated dataset rows are available, run `execution/calculate_funnel_tables.py` per `directives/calculate_funnel_tables.md` to build the `funnel_tables` payload instead of hand-formatting these tables in orchestration.

After querying KPI sources, build two funnel tables from registered datasets. Always include in output regardless of signal threshold.

**Table 1a — App session funnel (all markets)**
**Table 1b — Web session funnel (all markets)**
Source: `29a01e0e` (Domain KPI by Session)
Query: `SELECT country, device_type, SUM(journey_sessions), SUM(pdp_sessions), SUM(atc_sessions), SUM(cart_sessions), SUM(order_sessions) FROM table WHERE date >= [start] AND date <= [end] GROUP BY country, device_type ORDER BY country, device_type`
Split results into two separate tables — one for `device_type = 'App'`, one for `device_type = 'Web'`. Do not combine into a single table.
Compute as % of `journey_sessions`: PDP%, ATC%, Cart%, CVR%.
Sort each table by PDP% descending.
Flag market rows in the Web table where session count is in the suspicious flags list — append ⚠️ to the market cell and add a note below the table.
Note if any market is absent from this dataset (e.g. HK) — state alternative source used for that market's signals.

**Table 2 — User-level full funnel (all markets)**
Columns: Total Users | HP% | PDP% | ATC% | Cart% | Checkout% | CVR%

HP → Cart steps — source: `843ee8fc` (ATC Rate User Level), monthly granularity, use most recent complete month in window.
Query: `SELECT country, device, SUM(total_cookies) AS total_users, SUM(cookie_with_hp_view) AS users_hp, SUM(cookie_with_pdp) AS users_pdp, SUM(cookie_with_atc) AS users_atc, SUM(cookie_with_cart) AS users_cart, SUM(cookie_with_order) AS users_order FROM table WHERE year_month = '[YYYY-MM-01]' GROUP BY country, device ORDER BY country, device`
Aggregate across all devices per market (sum all device rows per country). Exclude rows where total_cookies < 10 (smart tv etc.).
Compute HP%, PDP%, ATC%, Cart%, CVR% as % of total_users.
IMPORTANT: The flag columns (viewed_hp, viewed_pdp, added_to_cart etc.) are 0/1 cohort keys — do NOT sum these. Only sum cookie_with_* and total_cookies.

Checkout% — source: `46ef93fa` (Cart to Checkout Funnel User Level), same date window as other datasets.
Query: `SELECT country, SUM(has_clicked_secure_checkout) AS clicked_checkout FROM table WHERE date_local_default >= [start] AND date_local_default <= [end] GROUP BY country`
Compute: Checkout% = clicked_checkout / total_users (from 843ee8fc).
Denominator mismatch warning: 843ee8fc and 46ef93fa use different user counting methodologies. If Checkout% > Cart% for any market, flag with ⚠️ and note the denominator discrepancy — do not suppress, surface to PM.

Sort rows by CVR% descending.
Flag markets where cookie_with_order is known incomplete (ID, TH, PH, MY) — append † and note to use Table 3 for order rates.
Flag SG if desktop user count is suspicious (inflated by web session spike).

Include a 2–3 sentence reading below Table 2 noting: where the PDP→ATC gap is largest, any anomalies in Checkout% vs Cart%, and what the top-of-funnel HP/PDP patterns suggest about traffic intent per market.

**Table 3 — User-level checkout funnel (all markets)**
Source: `46ef93fa` (Cart to Checkout Funnel User Level)
Query: `SELECT country, SUM(has_reached_cart), SUM(has_clicked_secure_checkout), SUM(has_finished_payment_methods), SUM(has_clicked_place_order), SUM(has_reached_confirmation_page), SUM(is_order_validated) FROM table WHERE date_local_default >= [start] AND date_local_default <= [end] GROUP BY country ORDER BY country`
Compute step rates:
- Cart→Checkout% = clicked\_secure\_checkout / reached\_cart
- Checkout→Payment% = finished\_payment\_methods / clicked\_secure\_checkout
- Payment→Order% = order\_validated / finished\_payment\_methods
- Cart→Order% = order\_validated / reached\_cart (overall)
Sort rows by Cart→Order% descending. Exclude rows with < 10 cart users (noise).

Include a 2–3 sentence reading below Table 3 noting: where checkout drop-off is worst, how it cross-references the signal list, and which markets have the most room for improvement.

## Step 7 — Surface signal list to PM

Present:

```
── SIGNAL REPORT ──────────────────────────────
[Market / Platform] [Metric]: [value] [direction] [delta] [period]
⚠️  [metric]: flagged suspicious — [reason]

Sources queried: [n] | New cards detected: [n] | Period: [date range]
──────────────────────────────────────────────
── TRAFFIC MIX ────────────────────────────────
Table T — Session share & CVR by traffic channel (29a01e0e, current week vs prior week)
| Market | Platform | Channel (lv1) | Sub-channel (lv2) | Sessions | Share% | CVR% | WoW Sessions | WoW CVR |
(sorted by market, then sessions desc)
⚠️  [channel]: session share shifted [n] pp WoW — [interpretation note]
⚠️  [channel]: CVR dropped [n] pp WoW — [interpretation note]
Note: Retention channel surges during member campaigns are expected — confirm with PM if large.
──────────────────────────────────────────────
── FUNNEL VIEW ────────────────────────────────
Table 1a — App session funnel (29a01e0e)
Table 1b — Web session funnel (29a01e0e)
Table 2 — User full funnel HP→PDP→ATC→Cart→Checkout→CVR (843ee8fc + 46ef93fa)
Table 3 — User checkout deep-dive Cart→Checkout→Payment→Order (46ef93fa)
──────────────────────────────────────────────
```

PM gate — ask: "Which of these signals do you want to take forward into triangulation? Confirm or adjust."
Wait for explicit PM response. Do not auto-advance.

## Step 8 — Write outputs via deterministic pipeline

After PM confirms the signal list, run the deterministic pipeline to produce authoritative output files. Do not hand-write `signals.md` or `pipeline-context.md` directly.

**Step 8a — Serialize Domo results to `.tmp/raw-signal-input.json`**

Build a JSON object in this shape and write it to `.tmp/raw-signal-input.json`:

```json
{
  "run_date": "YYYY-MM-DD",
  "period_label": "Mar 28–Apr 3 vs Mar 21–27",
  "extracts": [
    {
      "source_id": "29a01e0e",
      "source_name": "Domain KPI by session",
      "columns": ["country", "device_type", "journey_sessions", "order_sessions"],
      "rows": [[...raw Domo rows as returned by query-dataset...]],
      "mappings": {
        "market": "country",
        "platform": "device_type",
        "metric": {"const": "CVR"},
        "metric_type": {"const": "conversion_rate"},
        "value": "order_sessions",
        "previous_value": null
      }
    }
  ],
  "pm_confirmed_signals": ["S1", "S2"],
  "pm_excluded_signals": ["S3"],
  "carry_forward": [],
  "hypotheses": [],
  "notes": []
}
```

Key rules for `extracts`:
- `columns`: the `columns` array from the Domo `query-dataset` response — required when rows are value arrays (columnar format). The normalizer auto-converts.
- `rows`: the `rows` array directly from `query-dataset` response — no reshaping needed.
- Include one extract per dataset queried. For WoW comparisons, include current and prior week as separate extracts with a `period` field to distinguish them, or pre-compute `previous_value` in the mapping.
- `funnel_inputs` (optional): separate top-level key for structured funnel table inputs consumed by `calculate_funnel_tables.py`.

**Step 8b — Run the pipeline script**

```bash
mkdir -p .tmp outputs/signal-agent
python3 execution/run_signal_pipeline.py \
  --input .tmp/raw-signal-input.json \
  --config config/domo.yml \
  --json-output outputs/signal-agent/signal-report.json \
  --signals-output outputs/signal-agent/signals.md \
  --pipeline-output outputs/signal-agent/pipeline-context.md \
  --normalized-output .tmp/normalized-signal-input.json
```

Treat script output as authoritative. Do not manually overwrite `signals.md` or `pipeline-context.md` after this point.

If the script errors: read stderr, fix the input JSON, re-run. Update PROCEDURE.md with any new edge cases found.

---

## /sharpen — First-Principles Sharpening (hidden command)

Triggered by PM typing `/sharpen` after the signal gate.
Do not mention this command unless PM asks what commands are available.

### Technique selection

Read the confirmed signal list. Identify the dominant pattern and select the technique:

| Pattern | Technique |
|---|---|
| Single metric drop in one market | **5 Whys** |
| Multiple signals across markets | **First-principles decomposition** |
| Surprising or counter-expected signal | **Pre-mortem** |
| Conflicting signals (same metric up in some markets, down in others) | **Assumption mapping** |
| Persistent low-severity signal | **Inversion** |
| Broad multi-metric movement | **Steel-man** |

If multiple patterns apply, pick the technique that matches the highest-severity signal.

### Technique prompts

**5 Whys** — single focused drop
> "Before we look for evidence, let's drill down.
> 1. Why do you think [metric] dropped in [market]?
> 2. Why would that cause be happening now?
> 3. What would have to be true one level deeper?
> 4. Is there a root cause you've seen before that fits this pattern?
> 5. What would disprove your current explanation?"

**First-principles decomposition** — multiple signals
> "Let's break this down before pattern-matching.
> 1. Strip away what you know — what does [metric] actually measure at its most basic level?
> 2. Which part of that definition do you think is breaking down?
> 3. If you had to pick one signal as the lead and treat the others as downstream effects, which would it be?
> 4. What's the simplest explanation that accounts for all the signals together?
> 5. What assumption are you making that you haven't stated out loud yet?"

**Pre-mortem** — surprising signal
> "This signal surprised you. Let's stress-test the read.
> 1. Imagine it's 3 months from now and this signal turned out to be noise — what happened?
> 2. What's the most likely data or tracking explanation for this movement?
> 3. What would a sceptical analyst say about this result?
> 4. If you presented this to leadership tomorrow, what's the first pushback you'd expect?
> 5. What would make you fully confident this is a real signal worth acting on?"

**Assumption mapping** — conflicting signals
> "The signals are pulling in different directions. Let's surface the assumptions.
> 1. What did you expect to see before running this loop — and why?
> 2. Which market or platform result surprises you most?
> 3. What assumption would you need to drop for all the signals to make sense together?
> 4. Are you treating any of these markets as the 'normal' baseline — and is that justified?
> 5. What's the one thing you'd need to know to resolve the conflict?"

**Inversion** — persistent low-severity signal
> "This has been showing up at low intensity. Let's think from the other direction.
> 1. What would have to be true for this signal to get significantly worse over the next 30 days?
> 2. What's the cost of ignoring it for one more cycle?
> 3. If you were trying to make this metric drop further, what would you do?
> 4. Is there anything you're currently doing that might be inadvertently causing this?
> 5. At what point does this cross from 'watch' to 'act'?"

**Steel-man** — broad multi-metric movement
> "Before we treat this as signal, let's make the strongest case it's noise.
> 1. What's the most compelling argument that none of these movements are product problems?
> 2. What external factors (seasonality, campaign, market event) could explain all of this?
> 3. If you had to defend the 'nothing is wrong' position to leadership, what would you say?
> 4. What evidence would you need to see to rule out the noise explanation?
> 5. Having made that case — do you still believe the signal is real?"

### After PM responds

Synthesise the PM's answers into a **Signal Frame** — 3–5 sentences capturing:
- PM's stated hypothesis before evidence
- Key assumptions surfaced
- What the PM believes would confirm vs. disconfirm the signal

**Privacy rule — PM responses are in-session only.**
Do NOT write, log, or append any PM responses or the Signal Frame to any file or Confluence page.
The Signal Frame exists only in the active conversation context and is discarded when the session ends.
Do NOT pass PM responses to `11-feedback-agent` or `12-validation-agent` as attributed quotes.
The Signal Frame may inform the agent's *direction of search* internally, but the PM's words must never appear in any output file.
