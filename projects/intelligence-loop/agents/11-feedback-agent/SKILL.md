# 11-feedback-agent — Feedback Triangulation

> **Entry point.** Load [POLICY.md](POLICY.md) for output contracts, permissions, and error handling.
> Load [PROCEDURE.md](PROCEDURE.md) for step-by-step execution. When resuming a parked run, load PROCEDURE.md and jump to the labelled step.

**Role:** Triangulates confirmed signals from Agent 10 against Domo app reviews, Love Meter / NPS, CS tickets, and Search Terms. Memory-first — checks findings cache before querying Domo.

**Trigger:** Spawned by `/intelligence-loop` after PM signal gate · "run feedback triangulation" · "triangulate signals"

**Inputs:**
- `outputs/signal-agent/pipeline-context.md` — confirmed signal list from Agent 10
- `outputs/feedback/findings-store.json` — prior findings cache
- Domo feedback datasets (registered only)

**Outputs:**
- `outputs/feedback/findings.md` — structured findings for diagnosis handoff (overwrite)
- `outputs/feedback/findings-store.json` — cumulative findings cache (append-only)
- `outputs/feedback/run-log.json` — self-anneal log (append)

**PM gate:** Step 4b — PM must approve findings before outputs are written.
