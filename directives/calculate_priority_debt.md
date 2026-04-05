# calculate_priority_debt

## Purpose
Calculates priority debt (impact x confidence x cycles_unactioned) and flags escalation candidates.

## Inputs
- Source: `outputs/prioritisation/ranked-hypotheses.json`, `config/domo.yml` (escalation thresholds)
- Format: ranked-hypotheses.json is append-only array with cycle metadata per entry

## Script
`execution/calculate_priority_debt.py`

## Outputs
- Destination: `outputs/trend/signal-trend.json`
- Format: JSON array with hypothesis_id, priority_debt, cycles_unactioned, escalation_flag, trend_direction

## Edge cases
- Single cycle of data returns results with `trend: "insufficient_data"`
- verbatim_count field may be absent; do not check for it
- signal-strength-store.json does not exist; derive all data from ranked-hypotheses.json only
- Escalation threshold from `config/domo.yml`; default debt >= 27 (3x3x3)
