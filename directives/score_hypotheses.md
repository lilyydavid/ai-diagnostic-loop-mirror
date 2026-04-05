# score_hypotheses

## Purpose
Scores and ranks hypotheses by priority_score = Confidence x Impact x Scope for Agent 13 output.

## Inputs
- Source: `outputs/validation/experiment-designs.json` (required), `outputs/prioritisation/bet-log.json` (optional)
- Format: JSON array of hypothesis objects with confidence_label, impact_score, scope_score fields

## Script
`execution/score_hypotheses.py`

## Outputs
- Destination: `outputs/prioritisation/ranked-hypotheses.json` (append-only)
- Format: JSON array sorted descending by priority_score, each entry includes hypothesis_id, priority_score, C/I/S breakdown, rank

## Edge cases
- Composite labels like "Low-Medium" map to midpoint (e.g. 1.5)
- scope_score may arrive as text; convert via label map (Low=1, Medium=2, High=3)
- Impact hard-floor: if impact_score < 3, block hypothesis (exclude from ranking, flag reason)
- pm_odds field is optional tiebreaker when priority_scores are equal
- Missing bet-log.json is not an error; lineage tracking skipped
