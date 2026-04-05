# check_findings_cache

## Purpose
Checks freshness of cached feedback findings and appends new entries atomically.

## Inputs
- Source: `outputs/feedback/findings-store.json`, `config/domo.yml` (dataset registry), signal date (CLI arg)
- Format: findings-store.json is append-only JSON array; each entry has dataset_id, date, findings

## Script
`execution/check_findings_cache.py`

## Outputs
- Destination: stdout (freshness report) or appended entry in `outputs/feedback/findings-store.json`
- Format: Report JSON with per-dataset status: stale, fresh, or missing

## Edge cases
- Missing findings-store.json means all datasets report as missing
- Atomic writes via temp file + rename to prevent corruption
- Staleness window derived from `config/domo.yml` per dataset (default 7 days)
- Duplicate date+dataset entries are skipped on append
