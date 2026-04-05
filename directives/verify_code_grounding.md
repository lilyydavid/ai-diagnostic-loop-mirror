# verify_code_grounding

## Purpose
Verifies that file paths and code anchors in experiment designs are grounded in actual repo reads.

## Inputs
- Source: `outputs/validation/experiment-designs.json`, `outputs/validation/read-audit.log`, `config/atlassian.yml`
- Format: experiment-designs.json contains file_path and anchor fields per hypothesis; read-audit.log is line-delimited list of files read by Agent 12

## Script
`execution/verify_code_grounding.py`

## Outputs
- Destination: `outputs/validation/grounding-report.json`
- Format: JSON array with hypothesis_id, status (blocked/viable), unverified_paths list, reason

## Edge cases
- Missing read-audit.log blocks all hypotheses (no grounding evidence)
- confidence=Low hypotheses are blocked regardless of path verification
- Unverified file paths are stripped from Jira story payloads downstream
- Grep for anchor strings (function/class names) as secondary verification
