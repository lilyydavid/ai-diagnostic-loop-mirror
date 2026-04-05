#!/usr/bin/env python3
"""Build a deterministic diagnosis artifact for the intelligence loop.

The diagnosis artifact is the bridge between signal detection and hypothesis
formation. It captures observation, localisation, segmentation, rival
diagnoses, evidence quality, favored diagnosis, and falsification criteria in a
stable JSON + markdown contract.

Usage:
    python execution/build_diagnosis_artifact.py \
        --input .tmp/diagnosis-input.json \
        --json-output outputs/diagnosis/diagnosis.json \
        --markdown-output outputs/diagnosis/diagnosis.md
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = [
    "observation",
    "localisation",
    "segments",
    "rival_diagnoses",
    "favored_diagnosis",
    "falsification",
]


def load_input(input_path: str) -> dict[str, Any]:
    if input_path == "-":
        raw = sys.stdin.read()
    else:
        with open(input_path) as handle:
            raw = handle.read()

    if not raw.strip():
        raise ValueError("input is empty")

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    return data


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = []
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"missing required field: {key}")

    rival_diagnoses = ensure_list(payload.get("rival_diagnoses"))
    if len(rival_diagnoses) < 3:
        errors.append("rival_diagnoses must contain at least 3 entries")

    favored_id = payload.get("favored_diagnosis")
    rival_ids = {entry.get("id") for entry in rival_diagnoses if isinstance(entry, dict)}
    if favored_id and favored_id not in rival_ids:
        errors.append("favored_diagnosis must match one of rival_diagnoses.id")

    if not ensure_list(payload.get("falsification")):
        errors.append("falsification must contain at least one condition")

    return errors


def build_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    rival_diagnoses = ensure_list(payload.get("rival_diagnoses"))
    evidence_matrix = ensure_list(payload.get("evidence_matrix"))
    hypotheses = ensure_list(payload.get("hypotheses"))
    favored_id = payload.get("favored_diagnosis")
    favored = next((item for item in rival_diagnoses if isinstance(item, dict) and item.get("id") == favored_id), None)

    favored_statement = favored.get("statement") if isinstance(favored, dict) else None
    favored_statement_text = (favored_statement or "not specified").rstrip(". ")
    bare_claims = [
        payload.get("bare_claim_observation")
        or f"Observation: {payload.get('observation', {}).get('metric', 'unknown metric')} moved materially in the configured window.",
        payload.get("bare_claim_localisation")
        or f"Failure surface: {payload.get('localisation', {}).get('failure_surface', 'not specified')}.",
        payload.get("bare_claim_favored")
        or f"Favored diagnosis: {favored_id} - {favored_statement_text}.",
    ]

    return {
        "run_date": payload.get("run_date") or datetime.now().strftime("%Y-%m-%d"),
        "signal_ids": ensure_list(payload.get("signal_ids")),
        "observation": payload.get("observation", {}),
        "localisation": payload.get("localisation", {}),
        "segments": payload.get("segments", {}),
        "rival_diagnoses": rival_diagnoses,
        "evidence_matrix": evidence_matrix,
        "favored_diagnosis": favored_id,
        "favored_diagnosis_statement": favored_statement,
        "falsification": ensure_list(payload.get("falsification")),
        "hypotheses": hypotheses,
        "bare_claims": [claim for claim in bare_claims if claim],
        "experiment_constraint": payload.get("experiment_constraint"),
        "open_questions": ensure_list(payload.get("open_questions")),
        "notes": ensure_list(payload.get("notes")),
    }


def render_dict_list(items: list[dict[str, Any]], fields: list[str]) -> str:
    if not items:
        return "None\n"
    lines = []
    for item in items:
        parts = []
        for field in fields:
            value = item.get(field)
            if value is not None and value != "":
                parts.append(f"{field}: {value}")
        lines.append(f"- {' | '.join(parts)}")
    return "\n".join(lines) + "\n"


def render_markdown(artifact: dict[str, Any]) -> str:
    lines = [f"# Diagnosis Artifact — {artifact['run_date']}"]

    if artifact.get("signal_ids"):
        lines.append("Signals: " + ", ".join(str(signal_id) for signal_id in artifact["signal_ids"]))

    lines.append("")
    lines.append("## Bare Claims")
    for claim in artifact.get("bare_claims", []):
        lines.append(f"- {claim}")

    lines.append("")
    lines.append("## Observation")
    lines.append(json.dumps(artifact.get("observation", {}), indent=2))

    lines.append("")
    lines.append("## Failure Surface")
    lines.append(json.dumps(artifact.get("localisation", {}), indent=2))

    lines.append("")
    lines.append("## Affected Segments")
    lines.append(json.dumps(artifact.get("segments", {}), indent=2))

    lines.append("")
    lines.append("## Rival Diagnoses")
    lines.append(render_dict_list(artifact.get("rival_diagnoses", []), ["id", "class", "statement", "why_it_fits", "why_it_may_not_fit"]).rstrip())

    lines.append("")
    lines.append("## Evidence Matrix")
    lines.append(render_dict_list(artifact.get("evidence_matrix", []), ["diagnosis_id", "evidence", "direction", "source_strength"]).rstrip())

    lines.append("")
    lines.append("## Favored Diagnosis")
    lines.append(f"- {artifact.get('favored_diagnosis')}: {artifact.get('favored_diagnosis_statement')}")

    lines.append("")
    lines.append("## Falsification")
    for item in artifact.get("falsification", []):
        lines.append(f"- {item}")

    if artifact.get("hypotheses"):
        lines.append("")
        lines.append("## Hypotheses Descending From Diagnosis")
        lines.append(render_dict_list(artifact.get("hypotheses", []), ["id", "diagnosis_id", "statement", "test_type"]).rstrip())

    if artifact.get("experiment_constraint"):
        lines.append("")
        lines.append("## Experiment Constraint")
        lines.append(f"- {artifact['experiment_constraint']}")

    if artifact.get("open_questions"):
        lines.append("")
        lines.append("## Open Questions")
        for item in artifact["open_questions"]:
            lines.append(f"- {item}")

    if artifact.get("notes"):
        lines.append("")
        lines.append("## Notes")
        for item in artifact["notes"]:
            lines.append(f"- {item}")

    return "\n".join(lines).rstrip() + "\n"


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a diagnosis artifact")
    parser.add_argument("--input", required=True, help="Diagnosis input JSON, or '-' for stdin")
    parser.add_argument("--json-output", required=True, help="Path to write diagnosis JSON")
    parser.add_argument("--markdown-output", required=True, help="Path to write diagnosis markdown")
    args = parser.parse_args()

    if args.input != "-" and not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = load_input(args.input)
        errors = validate_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        artifact = build_artifact(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    ensure_parent(args.json_output)
    ensure_parent(args.markdown_output)

    with open(args.json_output, "w") as handle:
        json.dump(artifact, handle, indent=2)
        handle.write("\n")

    with open(args.markdown_output, "w") as handle:
        handle.write(render_markdown(artifact))

    print(
        f"Built diagnosis artifact → {args.json_output} | "
        f"rivals={len(artifact['rival_diagnoses'])} hypotheses={len(artifact['hypotheses'])}"
    )


if __name__ == "__main__":
    main()