# 20-inspiration-scout — Policy

## Role in pipeline

Agent 20 of the Inspiration Loop. Runs AFTER the Intelligence Loop diagnosis is complete.
Uses the diagnosis as context to understand what mechanism is broken, then scouts for prototype ideas grounded in the diagnosis. Facilitates PM Gate 1: pre-mortem brainstorm and prototype idea. Produces a fully populated bet entry that feeds as optional enrichment to Agent 13.

```
Intelligence Loop: 10 → 11+12 → diagnosis artifact
          │
  20-inspiration-scout
  ├─ read diagnosis artifact             ← what mechanism is broken?
  ├─ browse sephora.com                  ← what we have today
  ├─ scoped market scan                  ← what's possible
  ├─ surface combined brief grounded in diagnosis
  │
  *** PM GATE 1 — pre-mortem + prototype idea ***
  ├─ PM confirms failure scenario + idea + target metric + odds
  └─ write fully-populated bet entry + cycle-state
          │
  → Agent 13 (Prioritisation reads bets as optional enrichment)
```

## Trigger

- PM runs `/inspiration-loop` or says "run the inspiration loop"
- Spawned by the inspiration-loop orchestrator

---

## Output Contract

| Output | Path | Behaviour |
|---|---|---|
| Signal brief | `outputs/inspiration/signal-brief.md` | Overwrite each run |
| Bet log | `outputs/inspiration/bet-log.json` | Append-only — one entry per run, fully populated |
| Cycle state | `outputs/inspiration/cycle-state.json` | Overwrite — updated at each step |
| Confluence brief | PI space — `Inspiration Brief — YYYY-MM-DD` | New page per run |
| Teams notification | Webhook | `inspiration_signal_ready` event |

### Bet log entry — fields (all fully populated, no nulls)

| Field | Source |
|---|---|
| `bet_id` | Sequential from prior entries |
| `run_date` | Today |
| `signal` | Diagnosis-linked signal context |
| `current_state` | sephora.com browse |
| `market_context` | Web search |
| `prototype_idea` | PM Gate 1 |
| `target_metric` | PM Gate 1 |
| `premortem` | PM Gate 1 |
| `pm_odds` | PM Gate 1 |

---

## Configuration

```yaml
# config/atlassian.yml
inspiration_loop:
  signal_staleness_days: 7

teams:
  enabled: false
  notify_on:
    - inspiration_signal_ready
```

## Permissions

- Read: `outputs/diagnosis/diagnosis.md` and `outputs/diagnosis/diagnosis.json`
- Read: `outputs/signal-agent/signals.md` (optional context)
- Read: `outputs/inspiration/cycle-state.json`
- Read: `outputs/inspiration/bet-log.json`
- Read: `config/atlassian.yml`
- Browse: `sephora.com` — visible UI only; no source code inspection
- Web search: scoped to diagnosis failure surface / mechanism
- Write: `outputs/inspiration/signal-brief.md` (overwrite)
- Write: `outputs/inspiration/bet-log.json` (append-only)
- Write: `outputs/inspiration/cycle-state.json` (overwrite)
- Write: Teams webhook (if enabled)
- Write: Confluence — new child page in PI space under `page_id` from `config/atlassian.yml`
- No Domo queries; no Jira writes

## Error Handling

| Error | Action |
|---|---|
| In-progress cycle-state found | Surface to PM: resume or fresh; wait for response |
| `diagnosis.md` / `diagnosis.json` missing | Halt — run `/intelligence-loop` first |
| `signals.md` missing | Proceed with diagnosis-only context; note in brief |
| `signals.md` stale | Surface staleness warning; same options as above |
| sephora.com inaccessible or region-blocked | Note limitation in brief; proceed; `current_state: "sephora.com not accessible"` in bet entry |
| Web search returns no results | State "No market signals found"; do not fabricate; continue |
| PM does not confirm both pre-mortem and idea | Do not advance; re-surface Gate 1 prompts |
| `bet-log.json` missing | Create with `[]`; append first entry |
| `outputs/inspiration/` missing | Create directory before writing |
| Confluence write fails (401/403) | Surface to PM; instruct token rotation; do not skip |
| Teams notification fails | Log failure; continue; surface in chat |

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/inspiration/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. sephora.com region-blocked, used cached screenshots"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update PROCEDURE.md with the new constraint
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
