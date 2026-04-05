# flag_suspicious_metrics

## Purpose
Flags metrics that look suspicious before they reach agent outputs or Confluence pages.

## Inputs
- Source: JSON array of metric objects (stdin or file), `config/domo.yml` for thresholds
- Format: Each metric has name, value, yoy_change, and optional segment_values array

## Script
`execution/flag_suspicious_metrics.py`

## Outputs
- Destination: stdout (annotated JSON array)
- Format: Same array with added `suspicious: bool` and `suspicious_reason: string` fields per metric

## Edge cases
- YoY change > 50% with no known cause flagged as suspicious
- Value = 0% flagged as suspicious
- Identical values across all segments flagged as suspicious
- segment_values field is optional; segment check skipped if absent
- Thresholds read from `config/domo.yml` under `suspicious_metric_thresholds`; defaults used if key missing
