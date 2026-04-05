# run_signal_pipeline

## Purpose
Runs the deterministic Agent 10 execution path in one command: normalize raw query outputs, calculate funnel tables, and build the signal report.

## Inputs
- Source: raw orchestration payload containing `extracts` and optional `funnel_inputs`, plus `config/domo.yml`
- Format: same input contract accepted by `normalize_signal_inputs.py`, with optional `funnel_inputs` for `calculate_funnel_tables.py`

## Script
`execution/run_signal_pipeline.py`

## Outputs
- Destination: `outputs/signal-agent/signal-report.json`
- Format: final normalized JSON report
- Destination: `outputs/signal-agent/signals.md`
- Format: final markdown signal report
- Destination: `outputs/signal-agent/pipeline-context.md`
- Format: final markdown handoff to downstream agents
- Optional: normalized intermediate JSON and funnel tables JSON for debugging

## Edge cases
- If `funnel_inputs` is absent, the wrapper skips funnel table generation and uses any provided `funnel_tables`
- If intermediate outputs are requested, they are written after normalization and funnel generation but before final rendering
- Wrapper is deterministic and local-only; it does not fetch Domo data itself