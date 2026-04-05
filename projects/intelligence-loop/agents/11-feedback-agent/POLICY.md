# 11-feedback-agent — Policy

## Role in pipeline

Agent 11 of the Phase 1 Intelligence Loop. Runs in parallel with 12-validation-agent after PM gate.
Triangulates confirmed signals from Agent 10 against qualitative and quantitative feedback sources:
Domo app reviews, Love Meter / NPS, CS tickets, and Search Terms.

Memory-first: checks `outputs/feedback/findings-store.json` before querying Domo.
Writes a findings summary to local files for handoff to the diagnosis artifact and Agent 13.

```
outputs/signal-agent/pipeline-context.md  ──┐
config/domo.yml (feedback_datasets)         ├──▶  11-feedback-agent  ──▶  outputs/feedback/findings.md
config/domo.yml (kpi_datasets.discovery)    ┘                         ──▶  outputs/feedback/findings-store.json (append)
                                                                      └──▶  outputs/diagnosis/diagnosis.json (via build_diagnosis_artifact.py)
```

## Trigger

Spawned by `/intelligence-loop` after PM confirms signal list at Agent 10 gate.
Can also be run standalone: "run feedback triangulation" / "triangulate signals".

---

## Output Contract

### `outputs/feedback/findings.md`
Internal handoff to Agent 13. Overwrite each run. May include pipeline-internal fields.

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
Append-only. Never overwrite. Format: JSON array of entries.

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
- Update PROCEDURE.md with the new constraint (schema correction, PII column, API limit)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
