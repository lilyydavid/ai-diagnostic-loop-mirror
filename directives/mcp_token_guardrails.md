# MCP Token Guardrails

## Purpose
Minimise token consumption from MCP server calls. Each round-trip consumes tokens for the request, the full response payload, and follow-up reasoning.

## Rules

### 1. Call MCP only when the data cannot be obtained locally
- Check `outputs/`, `findings-store.json`, or `.tmp/` for cached/prior-run data first (memory-first principle)
- Use `execution/` scripts for computation — don't call MCP to get data you can derive
- Read local files via Read/Glob/Grep — these are free; MCP calls are not

### 2. Never dump MCP responses into context for browsing
- Before calling, know exactly what field or answer you need
- Extract the relevant values immediately; do not store the full response for later reasoning
- If an MCP tool returns a large payload (page content, dataset rows, issue list), extract only the fields you need and discard the rest in the same step

### 3. Batch and scope MCP calls tightly
- Use JQL/CQL filters to narrow results at the server — don't fetch all then filter locally
- For Domo: use `get-dashboard-signals` (one call per page) instead of `get-card` per card (N calls)
- For Confluence: search with specific terms, not broad queries that return 50+ pages
- For Jira: always include `project =`, `status =`, and `type =` in JQL — never unscoped searches

### 4. Cache MCP results when reusable
- If an agent will reference the same data multiple times in one run, write it to `.tmp/` on first fetch
- Staleness thresholds are in `config/domo.yml` — re-query only when findings are genuinely stale
- `execution/check_findings_cache.py` enforces this for feedback sources

### 5. Prefer read-only MCP over write MCP when possible
- Verify before writing: check if the Confluence page or Jira issue already has the content
- Don't update a page with identical content — compare first

## Edge cases
- If local cache is missing or corrupted, MCP call is justified — note it in agent output
- First run of any agent has no cache — all MCP calls are expected; subsequent runs should hit cache first
