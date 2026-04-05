# normalize_signal_inputs

## Purpose
Flattens raw Agent 10 query outputs into the normalized payload consumed by `execution/build_signal_report.py`.

## Inputs
- Source: orchestration-produced JSON object containing optional context fields plus either direct `metrics` or `extracts`
- Format: `extracts` is a list of source descriptors with `rows`, `mappings`, and optional `filters`, `segment_fields`, and source metadata

## Script
`execution/normalize_signal_inputs.py`

## Outputs
- Destination: `.tmp/normalized-signal-input.json` or another orchestration-chosen path
- Format: JSON object containing passthrough context plus a normalized `metrics` array compatible with `execution/build_signal_report.py`

## Extract schema
- `source_id`, `source_name`, `source_type`: optional metadata copied onto each metric
- `columns`: list of column name strings — **required when `rows` are value arrays (Domo columnar format)**. The script auto-detects and converts.
- `rows`: either a list of row dicts (`{"country": "AU", ...}`) or a list of value arrays (`["AU", "App", 426779]`). Value arrays require `columns` to be present.
- `mappings`: field specs for `market`, `platform`, `metric`, `metric_type`, `unit`, `value`, `previous_value`, `delta_pct`, `delta_value`, `yoy_delta_pct`, `period`, `value_display`, `delta_display`, `always_include`, `exclude_reason`
- Field specs may be a row path string like `country`, a literal like `const:Checkout`, or an object such as `{ "const": "Checkout->Payment" }`
- `filters`: exact-match include filters applied before normalization
- `segment_fields`: list of row paths collected into `segment_values`

## Edge cases
- Direct `metrics` passthrough is allowed for mixed-mode payloads
- If `delta_pct` is not provided but `previous_value` is, the script computes percentage change deterministically
- Missing metric names or values are skipped and recorded as notes in the output
- **Domo columnar format**: `query-dataset` returns `{"columns": [...], "rows": [[val,...], ...]}`. Pass `columns` and `rows` directly from the response — the script converts automatically. If `rows` are arrays but `columns` is absent, the extract is skipped with a warning.
- Script is source-agnostic; it does not depend on Domo tool response shapes beyond the row mappings supplied by orchestration