# 10-signal-agent — Signal Agent

> **Entry point.** Load [POLICY.md](POLICY.md) for output contracts, permissions, and error handling.
> Load [PROCEDURE.md](PROCEDURE.md) for step-by-step execution. When resuming a parked run, load PROCEDURE.md and jump to the labelled step.

**Role:** First agent in the Intelligence Loop — queries Domo KPI sources, applies signal thresholds, surfaces confirmed signal list for PM approval.

**Trigger:** `/intelligence-loop` · "run the intelligence loop" · "check KPI signals"
**Hidden:** `/sharpen` — first-principles sharpening after PM gate (see PROCEDURE.md)

**Inputs:**
- `config/domo.yml` — registered KPI sources, thresholds, query windows
- Domo KPI pages / cards / datasets (approved only)

**Outputs:**
- `outputs/signal-agent/signals.md` — confirmed signal table (overwrite)
- `outputs/signal-agent/pipeline-context.md` — pipeline handoff to agents 11 + 12 (overwrite)
- `outputs/signal-agent/signal-report.json` — machine-readable signal data (overwrite)
- `outputs/signal-agent/card-index.json` — cached card index (incremental update)
- `outputs/signal-agent/run-log.json` — self-anneal log (append)
- Confluence: date-stamped child page under Sephora Pulse (`64759660546`)

**PM gate:** Step 7 — PM must confirm signal list before outputs are written.
