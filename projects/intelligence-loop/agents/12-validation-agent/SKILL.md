# 12-validation-agent — Journey Mapping + Experiment Design (Step 2b)

> **Entry point.** Load [POLICY.md](POLICY.md) for output contracts, permissions, security rules, and error handling.
> Load [PROCEDURE.md](PROCEDURE.md) for step-by-step execution. When resuming a parked run, load PROCEDURE.md and jump to the labelled step.

**Role:** Agent 12 of the Intelligence Loop — runs in parallel with Agent 11 after the Agent 10 PM gate. Maps the FE/BE journey for confirmed hypotheses, reads targeted code, designs A/B experiments, and scores entries for Agent 13.

**Trigger:** Spawned by `/intelligence-loop` after PM gate · "survey codebase" · "design experiments" · "run validation agent"

**Inputs:**
- `outputs/signal-agent/pipeline-context.md` — confirmed hypothesis list
- `outputs/feedback/findings.md` — Agent 11 qualitative context (optional)
- `outputs/feedback/segment-cuts.md` — PM-approved segment cuts (optional)
- `config/repos.yml` — repo metadata
- `config/repos.local.yml` — local paths per repo

**Outputs:**
- `outputs/validation/experiment-designs.json` — scored experiment designs (overwrite)
- `outputs/validation/experiment-designs.md` — human-readable designs + journey map (overwrite)
- `outputs/validation/read-audit.log` — files read this session (overwrite)
- `outputs/validation/run-log.json` — self-anneal log (append)
- `outputs/diagnosis/diagnosis.json` — shared diagnosis artifact (via script)

**Local file system only. No Confluence, no Jira, no GitHub MCP, no Domo.**
