# resolve_config

## Purpose
Merges global, team, and local YAML config layers into a single resolved config object.

## Inputs
- Source: `config/atlassian.yml` (required), `config/atlassian.team.yml` (optional), `config/atlassian.local.yml` (optional)
- Format: YAML files following the config layers convention (local overrides team overrides global)

## Script
`execution/resolve_config.py`

## Outputs
- Destination: stdout (default) or file path via `--output` flag
- Format: JSON object with all keys merged, later layers overriding earlier ones

## Config layer priority

| File | Level | Committed? | Purpose |
|---|---|---|---|
| `config/atlassian.yml` | Global | Yes | Shared defaults for all users |
| `config/atlassian.team.yml` | Team | Yes (optional) | Team-scoped overrides (e.g. different Jira project) |
| `config/atlassian.local.yml` | Local | No (git-ignored) | Personal overrides (test epics, sandbox pages) |

To create a local override: `cp config/atlassian.local.yml.example config/atlassian.local.yml`

## Edge cases
- Missing team or local files are skipped silently (no error)
- If global file is missing, exit with error code 1
- Nested keys are deep-merged (not replaced at top level)
- Empty YAML files treated as empty dict (no-op merge)
