# build_diagnosis_artifact

## Purpose
Materialises the diagnosis layer between signal detection and hypothesis formation.

## Inputs
- Source: orchestration-produced JSON describing observation, localisation, segments, rival diagnoses, evidence matrix, favored diagnosis, falsification, and optional hypotheses
- Format: JSON object with required keys `observation`, `localisation`, `segments`, `rival_diagnoses`, `favored_diagnosis`, `falsification`

## Script
`execution/build_diagnosis_artifact.py`

## Outputs
- Destination: `outputs/diagnosis/diagnosis.json`
- Format: stable JSON artifact used by downstream prioritisation and review steps
- Destination: `outputs/diagnosis/diagnosis.md`
- Format: human-readable markdown with bare claims, rival diagnoses, evidence matrix, favored diagnosis, and falsification criteria

## Required diagnosis contract
- `observation`: uninterpreted signal statement and scope
- `localisation`: where in the journey or funnel the failure is concentrated
- `segments`: affected cohorts, markets, platforms, releases, or traffic cuts
- `rival_diagnoses`: at least 3 rival explanations spanning different causal classes
- `favored_diagnosis`: must match one rival diagnosis ID
- `falsification`: at least one condition that would weaken or reject the favored diagnosis

## Edge cases
- Fewer than 3 rival diagnoses is a hard validation error
- `favored_diagnosis` must reference a listed rival diagnosis ID
- Bare claims are generated automatically if orchestration does not provide them explicitly
- Script does not infer evidence; it only validates and formats what orchestration supplies