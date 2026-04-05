# check_signals_staleness

## Purpose
Checks whether the signals.md file is stale based on file modification time.

## Inputs
- Source: path to `signals.md` (CLI arg), `config/atlassian.yml` for staleness threshold
- Format: signals.md is a markdown file; staleness threshold in config under `signals_staleness_hours` (default 168 = 7 days)

## Script
`execution/check_signals_staleness.py`

## Outputs
- Destination: stdout
- Format: JSON object with `stale: bool`, `age_hours: number`, `reason: string`

## Edge cases
- Missing signals.md file returns `stale: true` with reason "file not found"
- Threshold sourced from config; falls back to 168 hours if absent
