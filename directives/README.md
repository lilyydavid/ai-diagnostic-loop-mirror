# Directives

SOPs for deterministic execution scripts. Each directive maps to one script in `execution/` or `scripts/`.

---

## BMAD → DOE Handoff

BMAD handles planning. DOE handles building. The handoff is explicit:

```
BMAD produces:
  _bmad-output/implementation-artifacts/<story>.md
            ↓
DOE reads:
  directives/<feature>.md        ← what to do (inputs, outputs, edge cases)
            ↓
DOE runs:
  execution/<script>.py          ← how to do it (deterministic)
  scripts/<script>.js            ← (Node.js scripts)
```

When a BMAD story is ready to build:
1. Check if a directive already exists in `directives/` for that feature
2. If not, create one — describe inputs, outputs, the script to use, edge cases
3. Check if the execution script exists in `execution/` or `scripts/`
4. If not, write it
5. Run the script, self-anneal on errors, update the directive with learnings

---

## Directive file format

```markdown
# <feature-name>

## Purpose
One sentence on what this does and why.

## Inputs
- Source: where the data comes from
- Format: what it looks like

## Script
`execution/<script>.py` or `scripts/<script>.js`

## Outputs
- Destination: where results go
- Format: file path, schema, cloud URL

## Edge cases
- Known API limits, timing constraints, error modes
- Updated as you learn
```

---

## Index

| Directive | Script | Used by |
|---|---|---|
| [assemble_diagnosis_input](assemble_diagnosis_input.md) | `execution/assemble_diagnosis_input.py` | Intelligence-loop orchestrator |
| [build_diagnosis_artifact](build_diagnosis_artifact.md) | `execution/build_diagnosis_artifact.py` | Agents 11, 12, 13 |
| [run_signal_pipeline](run_signal_pipeline.md) | `execution/run_signal_pipeline.py` | Agent 10 |
| [normalize_signal_inputs](normalize_signal_inputs.md) | `execution/normalize_signal_inputs.py` | Agent 10 |
| [calculate_funnel_tables](calculate_funnel_tables.md) | `execution/calculate_funnel_tables.py` | Agent 10 |
| [build_signal_report](build_signal_report.md) | `execution/build_signal_report.py` | Agent 10 |
| [resolve_config](resolve_config.md) | `execution/resolve_config.py` | Agents 09, 13 |
| [score_hypotheses](score_hypotheses.md) | `execution/score_hypotheses.py` | Agents 07, 12, 13 |
| [verify_code_grounding](verify_code_grounding.md) | `execution/verify_code_grounding.py` | Agent 13 |
| [flag_suspicious_metrics](flag_suspicious_metrics.md) | `execution/flag_suspicious_metrics.py` | Agent 10 |
| [check_findings_cache](check_findings_cache.md) | `execution/check_findings_cache.py` | Agent 11 |
| [check_signals_staleness](check_signals_staleness.md) | `execution/check_signals_staleness.py` | Agent 20 |
| [calculate_priority_debt](calculate_priority_debt.md) | `execution/calculate_priority_debt.py` | Agent 15 |
| [index_repos](index_repos.md) | `execution/index_repos.py` | Agents 08, 12 |
| [mcp_servers](mcp_servers.md) | — (reference) | All agents using MCP |
| [mcp_token_guardrails](mcp_token_guardrails.md) | — (SOP) | All agents using MCP |
| [context_window_budget](context_window_budget.md) | — (SOP) | All orchestrators and agents |
| [confluence_image_extraction](confluence_image_extraction.md) | — (manual) | Agent 05 |
| [scope_intake](scope_intake.md) | — (PM template) | Agent 13 |
