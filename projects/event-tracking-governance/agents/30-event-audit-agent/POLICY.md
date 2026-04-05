# 30-event-audit-agent — Policy

## Role in pipeline

Agent 30 of the Event Tracking Governance project. Entry point.
Scans registered repos for analytics event calls, cross-references against a provided taxonomy spec, and produces a structured audit report for PM review.

```
PM triggers /event-audit
      │
 30-event-audit-agent
 (codebase scan + spec cross-reference)
      │
      │  audit-report.md + event-inventory.json
      ▼
 PM reviews → approves → outputs written
      │
 (future) 31-governance-writer → Confluence spec update
```

---

## Output Contract

### outputs/event-tracking-governance/audit-report.md (overwrite)

Sections:
- **Summary** — total events found, % with spec coverage, % firing correctly
- **Missing from spec** — events in code with no taxonomy entry
- **Stale / deprecated** — events in spec but not found in code
- **Naming violations** — events that deviate from the naming convention
- **Undocumented** — events with no description in the spec
- **Data quality notes** — any ambiguous findings excluded from the main tables

Rules:
- No causal inference; observations only
- No source file paths in stakeholder-facing sections (move to appendix)
- Suspicious events (e.g. event names that are generic catch-alls) go to data quality notes only

### outputs/event-tracking-governance/event-inventory.json (overwrite)

```json
[
  {
    "event_name": "product_viewed",
    "surface": "PDP",
    "found_in_code": true,
    "in_spec": true,
    "naming_compliant": true,
    "has_description": true,
    "status": "ok" // ok | missing_from_spec | stale | naming_violation | undocumented
  }
]
```

### outputs/event-tracking-governance/pipeline-context.md (overwrite)

Handoff summary for downstream agents:
- Scope of this run (repos, surfaces, feature areas)
- Key findings (counts per status category)
- PM-approved changes to act on
- Suggested next step

---

## Permissions

| Resource | Access |
|---|---|
| `config/repos.yml`, `config/repos.local.yml` | Read |
| Registered repo clones (via `index_repos.py`) | Read |
| Confluence (taxonomy/spec pages) | Read only |
| `outputs/event-tracking-governance/` | Write |
| Any unregistered repo or Domo source | No access |

---

## Error Handling

| Condition | Action |
|---|---|
| `config/repos.local.yml` missing or empty | Halt — ask PM to configure repo paths before proceeding |
| No taxonomy doc provided by PM | Proceed with inventory-only audit; mark `in_spec` as `null`; flag report as no-spec run |
| Event name is ambiguous (e.g. `track("event")`) | Surface individual instance to PM; exclude from counts until resolved |
| Confluence page not found | Log in data quality notes; continue without spec cross-reference |
| PM rejects findings at gate | Revise scope or re-scan; do not write outputs until PM approves |
