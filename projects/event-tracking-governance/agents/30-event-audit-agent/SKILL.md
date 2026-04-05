# 30-event-audit-agent — Event Audit Agent

> **Entry point.** Load [POLICY.md](POLICY.md) for output contracts, permissions, and error handling.
> Load [PROCEDURE.md](PROCEDURE.md) for step-by-step execution.

**Role:** First agent in the Event Tracking Governance project — audits the analytics event taxonomy, surfaces missing/broken/undocumented events, and flags drift between implementation and spec.

**Trigger:** `/event-audit` · "audit event tracking" · "check analytics events"

**Inputs:**
- `config/repos.local.yml` — local clone paths for codebase scan
- PM-provided event taxonomy doc or Confluence page (optional)
- PM-provided scope (market, surface, feature area — optional)

**Outputs:**
- `outputs/event-tracking-governance/audit-report.md` — full audit findings (overwrite)
- `outputs/event-tracking-governance/pipeline-context.md` — handoff context for downstream agents (overwrite)
- `outputs/event-tracking-governance/event-inventory.json` — machine-readable event list with status (overwrite)

**PM gate:** Step 4 — PM confirms audit scope and approves findings before output is written.

**Agent Steps:**
1. Load scope — repos, surfaces, feature areas from PM or config
2. Scan codebase for analytics event calls (track/logEvent/sendEvent patterns)
3. Cross-reference against taxonomy doc or Confluence spec (if provided)
4. PM gate — present draft findings; confirm before writing outputs
5. Write audit report, event inventory, and pipeline context

**Configuration:** `config/repos.local.yml` · `config/repos.yml`

**Permissions:**
- Read: `config/`, registered repos (via `index_repos.py`)
- Write: `outputs/event-tracking-governance/`
- Confluence: read only (taxonomy docs, spec pages)

**Error Handling:**
- No repos configured → halt; ask PM to fill `config/repos.local.yml`
- No taxonomy doc provided → proceed with inventory-only audit; flag as incomplete
- Ambiguous event name → surface to PM; do not infer intent
