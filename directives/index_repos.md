# index_repos

## Purpose
Builds a structural index of configured repos for Agent 08 code search.

## Inputs
- Source: `config/repos.yml` (required), `config/repos.local.yml` (optional local path overrides)
- Format: YAML with repo name, remote URL, and optional local_path per entry

## Script
`execution/index_repos.py`

## Outputs
- Destination: `outputs/github-reader/repo-index.json`
- Format: JSON object keyed by repo name, each with file tree, key directories, and language breakdown

## Edge cases
- Missing local paths result in that repo being skipped (logged, not errored)
- repos.local.yml is optional; missing file skipped silently
- If repo-index.json is absent at query time, Agent 08 falls back to direct GitHub search
- Large repos: index top 3 directory levels only to cap runtime
