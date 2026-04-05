# 10-signal-agent — Policy

## Role in pipeline

Agent 10 of the Phase 1 Intelligence Loop. First agent to run.
Reads registered Domo KPI sources, extracts metric movements, applies signal filters, and surfaces a confirmed signal list for the PM to approve before Step 2 begins.

```
PM triggers loop
      │
 10-signal-agent  ──────────────────────────────────────────┐
 (Domo KPI signal)                                          │
      │                                              [/sharpen command]
      │ confirmed signal list                        First-principles sharpening
      ▼                                              (optional, PM-triggered)
 11-feedback-agent + 12-validation-agent
```

## Trigger

- PM runs `/intelligence-loop` or says "run the intelligence loop" / "check KPI signals"
- Hidden sharpening command: `/sharpen` — run after PM gate to sharpen signal interpretation

---

## Output Contract

### Confluence — Sephora Pulse update page (primary stakeholder output)

Write signal report as a **child page** under the Sephora Pulse parent page via the deterministic script.
Parent page ID: `64759660546`
Parent URL: `https://sephora-asia.atlassian.net/wiki/spaces/PI/pages/64759660546/Sephora+Pulse+update`

**Content rules — apply before every write:**
- Include: confirmed signals table, traffic mix table, funnel tables (session web/app, user-level, checkout), data quality notes
- Do NOT include: hypotheses, causes, experiment ideas, source dataset codes, agent names
- Each funnel table gets a 2–3 sentence narrative reading (where the drop-off is, what it implies — no causal inference)
- Suspicious metrics go to data quality notes only — not the main signal table

**Each run upserts a date-stamped child page:**

Step 1 — Write body to `.tmp/pulse-body.md` formatted as Confluence wiki markup.

Step 2 — Run the script:
```bash
python execution/write_confluence.py \
  --mode upsert \
  --space PI \
  --parent-id 64759660546 \
  --title "Sephora Pulse — $(date +%Y-%m-%d)" \
  --body-file .tmp/pulse-body.md \
  --content-format wiki
```

Parse stdout JSON: record `page_id` and `url` into `outputs/signal-agent/pipeline-context.md` under `## Confluence`.

If script exits non-zero:
- Exit 1 (401/403): surface auth error to PM, instruct token rotation. Do NOT skip.
- Exit 2 (400): check title length and parent ID; fix and retry once.
- Exit 3/4: config or input error — surface to PM.

The parent page (`64759660546`) is never modified.

### `outputs/signal-agent/signals.md`
Internal record — overwrite each run. Mirrors Confluence content for pipeline handoff.

```markdown
# Signal Report — [date]
## Confirmed Signals
| Market | Metric | Value | Delta | Period | PM Confirmed | Suspicious |
|---|---|---|---|---|---|---|
...

## Suspicious Flags
[metric]: [reason] — PM decision: [include / exclude]

## Traffic Mix
| Market | Platform | Channel (lv1) | Sub-channel (lv2) | Sessions | Share% | CVR% | WoW Sessions | WoW CVR |
...
[channel shift flags and campaign context notes]

## Funnel View
### Session Funnel (all markets)
| Market | Platform | Sessions | PDP% | ATC% | Cart% | CVR% |
...

### User-Level Checkout Funnel (all markets)
| Market | Cart Users | Cart→Checkout% | Checkout→Payment% | Payment→Order% | Cart→Order% |
...

## Sources
- [source name] ([type]) — [n cards] — queried [date range]
```

### `outputs/signal-agent/pipeline-context.md`
Internal pipeline handoff to agents 11 and 12 — overwrite each run.

```markdown
# Pipeline Context — Signal Agent — [date]
## Query Windows
[source type]: [n] days

## Confirmed Signal List
[confirmed signals from PM gate]

## PM Signal Frame
[appended by /sharpen if run — PM's first-principles reasoning]

## Handoff
Ready for: 11-feedback-agent, 12-validation-agent
Signals to triangulate: [n]
```

---

## Configuration

```yaml
# config/domo.yml
access_control: strict
kpi_pages / kpi_cards / kpi_datasets  # registered sources
query_windows                          # per-source-type date windows
thresholds.signal_threshold_pct        # per metric type
thresholds.suspicious_metric           # flag rules
```

## Permissions

- Read: registered Domo KPI sources only (`kpi_pages`, `kpi_cards`, `kpi_datasets`)
- Write: `outputs/signal-agent/` (pipeline handoff files)
- Write: Confluence child pages under Sephora Pulse (parent ID `64759660546`) — signal report only; parent page never modified
- No writes to Jira or any feedback source

## Error Handling

| Error | Action |
|---|---|
| Domo query fails (any source) | Log failure with reason; write to retry queue via `execution/retry_queue.py --write-failure`; continue with remaining sources; surface failures to PM in signal report |
| PII column detected in dataset schema | Halt that dataset; surface to PM; skip to next source |
| Unregistered ID attempted | Hard error — surface to PM, do not query |
| No approved sources in registry | Halt loop; tell PM to register at least one KPI source in `config/domo.yml` |
| No signals above threshold | Surface to PM: "No signals exceeded threshold. Options: (1) lower threshold in config, (2) widen query window, (3) proceed to triangulation without signal anchor" |
| PM gate timeout / no response | Park loop; write current state to pipeline-context; resume on next run |

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/signal-agent/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. column 'date' renamed to 'date_local' in dataset X"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update PROCEDURE.md with the new constraint (schema correction, API limit, timing, tool behaviour)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
