# context_window_budget

## Purpose
Keep agent runs reliable by spending context on decision-critical evidence, not on broad document loading.

## When to apply
- Any multi-step loop run (`/intelligence-loop`, `/inspiration-loop`, `/growth-engineer`)
- Any run that uses MCP or reads large markdown/json outputs

## Context budget policy

### 1. Load only the minimum required scope
- Start from directive + script + active output files for the current step
- Do not preload planning artifacts in `_bmad-output/` unless the current step explicitly requires them
- Read targeted line ranges for long files; avoid full-file reads by default

### 2. Prefer deterministic reduction before reasoning
- Use `execution/` scripts to aggregate, score, filter, and validate
- Do not manually reason over raw tables when a script already exists
- For MCP responses, extract required fields immediately and discard the rest

### 3. Use progressive disclosure
- First pass: 1-2 sentence summary + hard decision points
- Second pass (only if needed): top evidence snippets, capped to essential items
- Full payloads only for blocked or disputed decisions

### 4. Keep handoff artifacts compact
- `pipeline-context.md`: only current-cycle state, open questions, and required next inputs
- `validation-hypotheses.md`: top rival set only (no long narrative background)
- `trend-report.md`: deltas and threshold breaches, not full historical replay

### 5. Cap repeated content
- Do not restate unchanged assumptions across steps; reference previous artifact instead
- Avoid duplicating the same evidence in chat and output files
- If data is unchanged, write "no material change" and continue

## Practical checklist (run before MCP calls)
1. Is the answer already available in `outputs/`, `.tmp/`, or cache files?
2. Can an existing `execution/` script derive it deterministically?
3. Can the query be narrowed by market/date/status before fetching?
4. Can output be summarized to only fields needed for the next decision?

## Related directives
- `directives/mcp_token_guardrails.md`
- `directives/check_findings_cache.md`
- `directives/check_signals_staleness.md`
