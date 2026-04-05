Read `.claude/skills/intelligence-loop.md` and execute the full intelligence-loop orchestration.

1. Run Agent 10 and stop at the PM signal gate.
2. After PM confirmation, run Agent 11 and Agent 12 as diagnosis input stages.
3. Build `outputs/diagnosis/diagnosis.json` and `outputs/diagnosis/diagnosis.md` via `execution/build_diagnosis_artifact.py` before running Agent 13.
4. Run Agent 13 only after the diagnosis artifact exists.
5. Run Agent 15 after Agent 13 completes.
6. Do not skip PM gates or infer missing diagnosis fields.
