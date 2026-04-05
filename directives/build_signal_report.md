# build_signal_report

## Purpose
Normalises raw KPI metric inputs into a deterministic signal report for Agent 10.

## Inputs
- Source: normalized JSON payload from orchestration or a future Domo extractor, plus `config/domo.yml`
- Format: JSON object with `metrics` array and optional `query_windows`, `sources`, `pm_context`, `hypotheses`, `funnel_tables`, `carry_forward`, `notes`

## Script
`execution/build_signal_report.py`

## Outputs
- Destination: `outputs/signal-agent/signal-report.json`
- Format: normalized JSON with `confirmed_signals`, `excluded_signals`, summary counts, and passthrough context fields
- Destination: `outputs/signal-agent/signals.md`
- Format: deterministic markdown report with confirmed signals, excluded signals, optional hypotheses, and funnel tables
- Destination: `outputs/signal-agent/pipeline-context.md`
- Format: deterministic markdown handoff summarizing query windows, PM context, confirmed signals, exclusions, carry-forward items, and hypotheses

## Metric schema
- Required for useful filtering: `metric`, `market`, `platform`, `value`, and either `delta_pct` or `delta_value`
- Optional: `metric_type`, `period`, `yoy_delta_pct`, `segment_values`, `value_display`, `delta_display`, `always_include`, `exclude_reason`
- `metric_type = ratings` uses `delta_value` against the absolute rating threshold in `config/domo.yml`

## Edge cases
- Input may be a raw metrics array instead of an object; script wraps it as `{ "metrics": [...] }`
- `--input -` reads JSON from stdin for piping and test runs
- Metrics with explicit `exclude_reason` are excluded before thresholding
- Metrics with `always_include: true` bypass threshold filtering but still receive suspicious flags
- Suspicious metric checks reuse `execution/flag_suspicious_metrics.py` logic so thresholding and flagging stay aligned
- Script does not fetch Domo data; it only builds deterministic outputs from normalized inputs