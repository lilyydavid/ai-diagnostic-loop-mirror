# assemble_diagnosis_input

## Purpose
Builds the diagnosis-input JSON contract from the existing signal, feedback, and validation outputs.

## Inputs
- Source: `outputs/signal-agent/pipeline-context.md`
- Source: `outputs/feedback/findings.md`
- Source: `outputs/validation/experiment-designs.json`
- Format: markdown + JSON from the intelligence loop's earlier stages

## Script
`execution/assemble_diagnosis_input.py`

## Outputs
- Destination: `.tmp/diagnosis-input.json` or another orchestration-selected path
- Format: JSON object compatible with `execution/build_diagnosis_artifact.py`

## Assembly rules
- Use the confirmed signal list and cycle signal for observation
- Use Agent 12 mechanism notes for localisation
- Use PM-confirmed segment cuts and applied segments for affected segments
- Derive at least 3 rival diagnoses from the validation entries, preferring the PM-confirmed signal order from `pipeline-context.md`
- Choose the favored diagnosis deterministically from the ordered rival set
- Carry forward experiment constraint and open questions so Agent 13 has a diagnosis artifact with explicit rivalry and falsification

## Edge cases
- Fewer than 3 experiment entries is a hard error because rival diagnoses cannot be assembled
- Missing signal order in `pipeline-context.md` falls back to experiment score ordering
- Findings evidence summary is optional enrichment; the script still assembles a valid payload without it