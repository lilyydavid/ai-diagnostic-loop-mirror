#!/usr/bin/env python3
"""Assemble diagnosis-builder input from current intelligence-loop outputs.

This script converts the existing signal, feedback, and validation outputs into the
stable JSON contract consumed by execution/build_diagnosis_artifact.py.

Usage:
    python execution/assemble_diagnosis_input.py \
        --pipeline outputs/signal-agent/pipeline-context.md \
        --findings outputs/feedback/findings.md \
        --experiments outputs/validation/experiment-designs.json \
        --output .tmp/diagnosis-input.json
"""

import argparse
import json
import os
import re
import sys
from typing import Any


CONFIDENCE_SCORE = {
    "high": 3.0,
    "medium-high": 2.5,
    "medium": 2.0,
    "low-medium": 1.5,
    "low": 1.0,
}

IMPACT_SCORE = {
    "high": 3.0,
    "medium-high": 2.5,
    "medium": 2.0,
    "low-medium": 1.5,
    "low": 1.0,
}


def load_text(path: str) -> str:
    with open(path) as handle:
        return handle.read()


def load_json(path: str) -> Any:
    with open(path) as handle:
        return json.load(handle)


def first_sentence(text: str | None) -> str:
    if not text:
        return ""
    normalized = " ".join(str(text).split())
    match = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)
    return match[0].strip()


def extract_run_date(pipeline_text: str, experiments: dict[str, Any]) -> str | None:
    match = re.search(r"Pipeline Context .*? (\d{4}-\d{2}-\d{2})", pipeline_text)
    if match:
        return match.group(1)
    generated_at = experiments.get("generated_at")
    if isinstance(generated_at, str):
        return generated_at
    return None


def extract_bullets(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    collected = []
    in_section = False
    for line in lines:
        if line.startswith("## ") and line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip().startswith("- "):
            collected.append(line.strip()[2:])
    return collected


def extract_product_signal_ids(pipeline_text: str) -> list[tuple[str, str]]:
    results = []
    in_section = False
    for raw_line in pipeline_text.splitlines():
        line = raw_line.strip()
        if line == "### Product signals (for triangulation):":
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        match = re.match(r"\d+\.\s+\*\*(H-[A-Z0-9]+)\*\*:\s+(.*)$", line)
        if match:
            results.append((match.group(1), match.group(2).strip()))
    return results


def extract_findings_evidence_table(findings_text: str) -> dict[str, dict[str, str]]:
    evidence = {}
    in_table = False
    for raw_line in findings_text.splitlines():
        line = raw_line.strip()
        if line == "## Evidence Quality Summary":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table and line.startswith("| H-"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 4:
                evidence[cells[0].split(":", 1)[0]] = {
                    "evidence_quality": cells[1],
                    "basis": cells[2],
                    "change": cells[3],
                }
    return evidence


def split_markets(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r",|/", value)
    return [part.strip() for part in parts if part.strip()]


def normalize_label(value: str | None) -> str:
    return str(value or "").strip().lower()


def score_entry(entry: dict[str, Any]) -> float:
    confidence = CONFIDENCE_SCORE.get(normalize_label(entry.get("confidence")), 1.0)
    impact = IMPACT_SCORE.get(normalize_label(entry.get("impact")), 1.0)
    scope = float(entry.get("scope_score") or 1.0)
    return confidence * impact * scope


def classify_diagnosis(entry: dict[str, Any]) -> str:
    haystack = " ".join(
        [
            str(entry.get("description", "")),
            str(entry.get("funnel_stage", "")),
            str(entry.get("segment_scope", "")),
        ]
    ).lower()

    if any(token in haystack for token in ["kameleoon", "occlusion", "nav", "pdp"]):
        return "Visibility"
    if any(token in haystack for token in ["discount", "gold", "trust"]):
        return "Trust"
    if any(token in haystack for token in ["payment", "reconciliation", "order", "gateway"]):
        return "Technical"
    if any(token in haystack for token in ["cart", "checkout", "selector", "regression", "gwp", "oos"]):
        return "Technical"
    return "Operational"


def why_it_may_not_fit(entry: dict[str, Any]) -> str:
    confidence_reason = str(entry.get("confidence_reason", "")).strip()
    if "limited" in confidence_reason.lower():
        return first_sentence(confidence_reason)
    return f"Competes with other diagnoses at the {entry.get('funnel_stage', 'same')} stage and still needs falsification."


def build_falsification(favored: dict[str, Any], all_entries: list[dict[str, Any]]) -> list[str]:
    market = favored.get("market") or "the affected markets"
    success_metric = favored.get("ab_test", {}).get("success_metric") or favored.get("funnel_stage") or "the target metric"
    segment_scope = favored.get("segment_scope") or "the affected segment"
    favored_description = favored.get("description") or favored.get("hypothesis_id") or "the favored diagnosis"

    return [
        f"If users outside {segment_scope} show the same deterioration pattern, {favored_description} is likely incomplete.",
        f"If removing or bypassing the suspected failure mechanism does not improve {success_metric} in {market}, the favored diagnosis weakens materially.",
        f"If instrumentation or logs do not show concentrated failure at {favored.get('funnel_stage', 'the implicated step')}, the favored diagnosis should be re-ranked against its rivals.",
    ]


def build_experiment_constraint(favored: dict[str, Any], rivals: list[dict[str, Any]]) -> str:
    favored_stage = favored.get("funnel_stage") or "the implicated stage"
    rival_labels = [
        str(rival.get("hypothesis_id") or rival.get("id"))
        for rival in rivals
        if str(rival.get("hypothesis_id") or rival.get("id")) != str(favored.get("hypothesis_id"))
    ]
    if rival_labels:
        rival_text = ", ".join(rival_labels)
        return f"The experiment must isolate whether the failure at {favored_stage} is explained by {favored.get('hypothesis_id')} rather than competing diagnoses {rival_text}."
    return f"The experiment must isolate the mechanism at {favored_stage} rather than measuring a generic uplift."


def assemble_payload(pipeline_text: str, findings_text: str, experiments: dict[str, Any]) -> dict[str, Any]:
    entries = list(experiments.get("entries", []))
    if len(entries) < 3:
        raise ValueError("experiment-designs.json must contain at least 3 entries to assemble rival diagnoses")

    signal_order = extract_product_signal_ids(pipeline_text)
    findings_evidence = extract_findings_evidence_table(findings_text)
    pm_context = extract_bullets(pipeline_text, "## PM-Confirmed Context")
    off_signal = extract_bullets(pipeline_text, "### Off-signal risks (surfaced by Agent 11):")

    entries_by_id = {str(entry.get("hypothesis_id")): entry for entry in entries}
    ordered_entries = [entries_by_id[hypothesis_id] for hypothesis_id, _ in signal_order if hypothesis_id in entries_by_id]
    for entry in sorted(entries, key=score_entry, reverse=True):
        if entry not in ordered_entries:
            ordered_entries.append(entry)

    favored = ordered_entries[0]
    rivals = ordered_entries[: max(3, min(4, len(ordered_entries)))]

    rival_diagnoses = []
    evidence_matrix = []
    for entry in rivals:
        hypothesis_id = str(entry.get("hypothesis_id"))
        findings_row = findings_evidence.get(hypothesis_id, {})
        rival_diagnoses.append(
            {
                "id": hypothesis_id,
                "class": classify_diagnosis(entry),
                "statement": str(entry.get("description", "")).strip(),
                "why_it_fits": first_sentence(entry.get("confidence_reason") or entry.get("code_evidence", {}).get("current_behaviour") or findings_row.get("basis")),
                "why_it_may_not_fit": why_it_may_not_fit(entry),
            }
        )
        evidence_matrix.append(
            {
                "diagnosis_id": hypothesis_id,
                "evidence": first_sentence(entry.get("code_evidence", {}).get("current_behaviour") or entry.get("confidence_reason")),
                "direction": "supports",
                "source_strength": normalize_label(entry.get("confidence")) or "medium",
            }
        )
        if findings_row:
            evidence_matrix.append(
                {
                    "diagnosis_id": hypothesis_id,
                    "evidence": findings_row.get("basis", ""),
                    "direction": "supports",
                    "source_strength": findings_row.get("evidence_quality", "medium").lower(),
                }
            )

    favored_id = str(favored.get("hypothesis_id"))
    markets = split_markets(str(favored.get("market", "")))
    platforms = sorted(
        {
            platform.strip()
            for item in experiments.get("segments_applied", [])
            if isinstance(item, str) and item.lower().startswith("platform:")
            for platform in [item.split(":", 1)[1]]
        }
    )

    open_questions = []
    for entry in entries:
        if entry is favored:
            continue
        if normalize_label(entry.get("confidence")) in {"low", "low-medium", "medium"}:
            open_questions.append(
                f"What evidence would decisively separate {entry.get('hypothesis_id')} from {favored_id} at {entry.get('funnel_stage', 'the implicated step')}?"
            )
    open_questions.extend(off_signal)

    payload = {
        "run_date": extract_run_date(pipeline_text, experiments),
        "signal_ids": [hypothesis_id for hypothesis_id, _ in signal_order],
        "observation": {
            "summary": experiments.get("cycle_signal"),
            "metric": favored.get("ab_test", {}).get("success_metric") or favored.get("funnel_stage"),
            "direction": "down",
            "market": favored.get("market"),
            "funnel_scope": experiments.get("funnel_scope"),
        },
        "localisation": {
            "failure_surface": favored.get("funnel_stage"),
            "journey_step": favored.get("ab_test", {}).get("success_metric") or favored.get("funnel_stage"),
            "mechanism_summary": first_sentence(favored.get("code_evidence", {}).get("current_behaviour")),
        },
        "segments": {
            "markets": markets,
            "platforms": platforms,
            "segment_scope": favored.get("segment_scope"),
            "applied_segments": experiments.get("segments_applied", []),
        },
        "rival_diagnoses": rival_diagnoses,
        "evidence_matrix": evidence_matrix,
        "favored_diagnosis": favored_id,
        "falsification": build_falsification(favored, rivals),
        "hypotheses": [
            {
                "id": favored_id,
                "diagnosis_id": favored_id,
                "statement": favored.get("description"),
                "test_type": favored.get("ab_test", {}).get("test_type") or "A/B",
            }
        ],
        "bare_claim_observation": first_sentence(experiments.get("cycle_signal")),
        "bare_claim_localisation": f"Failure surface: {favored.get('funnel_stage', 'not specified')}.",
        "bare_claim_favored": f"Favored diagnosis: {favored_id} - {first_sentence(favored.get('description'))}",
        "experiment_constraint": build_experiment_constraint(favored, rivals),
        "open_questions": open_questions,
        "notes": [
            "Assembled deterministically from pipeline-context.md, findings.md, and experiment-designs.json.",
            *pm_context,
        ],
    }

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble diagnosis input from intelligence-loop outputs")
    parser.add_argument("--pipeline", required=True, help="Path to outputs/signal-agent/pipeline-context.md")
    parser.add_argument("--findings", required=True, help="Path to outputs/feedback/findings.md")
    parser.add_argument("--experiments", required=True, help="Path to outputs/validation/experiment-designs.json")
    parser.add_argument("--output", required=True, help="Path to write diagnosis-input JSON")
    args = parser.parse_args()

    for path in [args.pipeline, args.findings, args.experiments]:
        if not os.path.exists(path):
            print(f"ERROR: input not found: {path}", file=sys.stderr)
            sys.exit(1)

    try:
        pipeline_text = load_text(args.pipeline)
        findings_text = load_text(args.findings)
        experiments = load_json(args.experiments)
        payload = assemble_payload(pipeline_text, findings_text, experiments)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(
        f"Assembled diagnosis input → {args.output} | "
        f"rivals={len(payload['rival_diagnoses'])} favored={payload['favored_diagnosis']}"
    )


if __name__ == "__main__":
    main()