# 30-event-audit-agent — Procedure

Step-by-step execution. Resume from the labelled step when continuing a parked run.
Context: read POLICY.md for output contracts, permissions, and error handling.

---

## Step 1 — Load scope

Ask PM (or read from prior pipeline context if resuming):
- Which repos / surfaces to scan (default: all repos in `config/repos.local.yml`)
- Which feature area or market to focus on (optional — leave empty for full audit)
- Confluence URL of the event taxonomy spec (optional but recommended)

Read `config/repos.local.yml` and `config/repos.yml`.
If `repos.local.yml` is empty or missing → halt. Ask PM to configure repo paths.

---

## Step 2 — Index repos

Run `execution/index_repos.py` with the scoped repo paths.
This produces a file index for targeted grep-style searches.

Search for analytics event call patterns across indexed repos. Common patterns to match:
- `analytics.track(`, `tracker.track(`, `logEvent(`, `sendEvent(`, `trackEvent(`
- `.track("`, `Analytics.log(`, `gtm.push(`
- Adjust patterns if PM provides framework-specific callsites

For each match, extract:
- Event name (string literal if static; flag as dynamic if interpolated)
- File path and line number (for appendix; not stakeholder-facing)
- Surface / platform (inferred from repo or file path)

---

## Step 3 — Cross-reference spec (if provided)

If PM provided a Confluence taxonomy page:
- Fetch the page content via MCP
- Parse event entries (name, description, properties, owner, status)
- For each event found in code: check if it exists in spec → `in_spec: true/false`
- For each event in spec: check if found in code → flag stale entries

If no spec provided → set `in_spec: null` for all entries; mark report as no-spec run.

Check naming convention compliance:
- Default convention: `snake_case`, `object_action` pattern (e.g. `product_viewed`, `cart_updated`)
- If PM provides a different convention, apply that instead

---

## Step 4 — PM gate

Present draft findings to PM as a compact table:

| Category | Count |
|---|---|
| Total events found in code | N |
| In spec | N |
| Missing from spec | N |
| Stale (in spec, not in code) | N |
| Naming violations | N |
| Undocumented | N |

Ask PM:
- "Does this scope look right? Anything to add or exclude?"
- "Any known dynamic events I should be aware of?"

Do not write outputs until PM confirms.

---

## Step 5 — Write outputs

Write `outputs/event-tracking-governance/event-inventory.json` — full event list with status per POLICY.md schema.

Write `outputs/event-tracking-governance/audit-report.md`:
- Summary section (counts + coverage %)
- Tables for each status category (missing, stale, naming violations, undocumented)
- Data quality notes for ambiguous/dynamic events
- Appendix: file paths and line numbers for engineering reference

Write `outputs/event-tracking-governance/pipeline-context.md`:
- Scope of this run
- Key counts per category
- PM-approved action items
- Suggested next step (e.g. "Update spec with missing events", "Deprecate stale entries")

---

## Step 6 — Confirm and hand off

Confirm outputs written. Summarise key findings for PM in 3–5 bullet points.
If any events need spec updates, suggest next step: governance-writer agent (Agent 31, when available).
