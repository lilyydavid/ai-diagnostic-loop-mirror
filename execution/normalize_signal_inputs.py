#!/usr/bin/env python3
"""Normalize raw Agent 10 query results into the build_signal_report payload.

This script flattens query-dataset style result rows into the stable `metrics`
array consumed by `execution/build_signal_report.py`. It is intentionally
generic so orchestration can adapt Domo sources without rewriting the post-query
 execution path.

Usage:
    python execution/normalize_signal_inputs.py \
        --input .tmp/raw-signal-input.json \
        --output .tmp/normalized-signal-input.json

    printf '{"extracts": [...]}' | python execution/normalize_signal_inputs.py \
        --input - \
        --output .tmp/normalized-signal-input.json
"""

import argparse
import json
import os
import sys
from typing import Any


PASSTHROUGH_DEFAULTS = {
    "run_date": None,
    "period_label": None,
    "sources": [],
    "query_windows": [],
    "pm_context": [],
    "carry_forward": [],
    "hypotheses": [],
    "funnel_tables": [],
    "notes": [],
}


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


def nested_get(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return None
            if index < 0 or index >= len(current):
                return None
            current = current[index]
        else:
            return None
    return current


def resolve_spec(spec: Any, row: dict[str, Any], extract: dict[str, Any]) -> Any:
    if spec is None:
        return None
    if isinstance(spec, dict):
        if "const" in spec:
            return spec["const"]
        if "field" in spec:
            return nested_get(row, str(spec["field"]))
        if "extract" in spec:
            return nested_get(extract, str(spec["extract"]))
        return None
    if isinstance(spec, str):
        if spec.startswith("const:"):
            return spec.split(":", 1)[1]
        if spec.startswith("extract:"):
            return nested_get(extract, spec.split(":", 1)[1])
        return nested_get(row, spec)
    return spec


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def compute_delta_pct(value: Any, previous_value: Any) -> float | None:
    current = to_float(value)
    previous = to_float(previous_value)
    if current is None or previous is None or previous == 0:
        return None
    return ((current - previous) / previous) * 100.0


def passes_filters(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    for field, expected in filters.items():
        actual = nested_get(row, field)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        else:
            if actual != expected:
                return False
    return True


def columnar_to_rows(columns: list[str], rows: list[list]) -> list[dict[str, Any]]:
    """Convert Domo-style columnar result (columns array + rows as value arrays) to row dicts."""
    return [dict(zip(columns, row)) for row in rows if isinstance(row, list)]


def normalize_extract(extract: dict[str, Any], warnings: list[str]) -> list[dict[str, Any]]:
    metrics = []

    passthrough_metrics = extract.get("metrics", [])
    if passthrough_metrics:
        if not isinstance(passthrough_metrics, list):
            warnings.append(f"extract {extract.get('source_id', '?')}: metrics passthrough must be a list")
        else:
            metrics.extend([metric for metric in passthrough_metrics if isinstance(metric, dict)])

    rows = extract.get("rows", [])
    if rows and not isinstance(rows, list):
        warnings.append(f"extract {extract.get('source_id', '?')}: rows must be a list")
        return metrics

    # Auto-detect Domo columnar format: rows are arrays, not dicts.
    # Requires a "columns" field on the extract (list of column name strings).
    if rows and isinstance(rows[0], list):
        columns = extract.get("columns")
        if not columns or not isinstance(columns, list):
            warnings.append(
                f"extract {extract.get('source_id', '?')}: rows appear columnar (arrays) but no 'columns' field provided — skipping"
            )
            return metrics
        rows = columnar_to_rows(columns, rows)

    mappings = extract.get("mappings", {}) or {}
    filters = extract.get("filters", {}) or {}
    segment_fields = extract.get("segment_fields", []) or []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            warnings.append(f"extract {extract.get('source_id', '?')}: row {index} is not an object")
            continue
        if filters and not passes_filters(row, filters):
            continue

        value = resolve_spec(mappings.get("value"), row, extract)
        previous_value = resolve_spec(mappings.get("previous_value"), row, extract)
        delta_pct = resolve_spec(mappings.get("delta_pct"), row, extract)
        if delta_pct is None and previous_value is not None:
            delta_pct = compute_delta_pct(value, previous_value)

        entry = {
            "market": resolve_spec(mappings.get("market", extract.get("market")), row, extract),
            "platform": resolve_spec(mappings.get("platform", extract.get("platform")), row, extract),
            "metric": resolve_spec(mappings.get("metric", extract.get("metric")), row, extract),
            "metric_type": resolve_spec(mappings.get("metric_type", extract.get("metric_type")), row, extract),
            "unit": resolve_spec(mappings.get("unit", extract.get("unit")), row, extract),
            "value": value,
            "value_display": resolve_spec(mappings.get("value_display"), row, extract),
            "delta_pct": delta_pct,
            "delta_value": resolve_spec(mappings.get("delta_value"), row, extract),
            "delta_display": resolve_spec(mappings.get("delta_display"), row, extract),
            "yoy_delta_pct": resolve_spec(mappings.get("yoy_delta_pct"), row, extract),
            "period": resolve_spec(mappings.get("period", extract.get("period")), row, extract),
            "always_include": bool(resolve_spec(mappings.get("always_include", extract.get("always_include", False)), row, extract)),
            "exclude_reason": resolve_spec(mappings.get("exclude_reason"), row, extract),
        }

        if segment_fields:
            entry["segment_values"] = [nested_get(row, field) for field in segment_fields if nested_get(row, field) is not None]

        for key in ["source_id", "source_name", "source_type"]:
            if key in extract:
                entry[key] = extract[key]

        if not entry.get("metric"):
            warnings.append(f"extract {extract.get('source_id', '?')}: row {index} missing metric name")
            continue
        if entry.get("value") is None and not entry.get("value_display"):
            warnings.append(f"extract {extract.get('source_id', '?')}: row {index} missing value")
            continue

        metrics.append({k: v for k, v in entry.items() if v is not None})

    return metrics


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: payload.get(key, default) for key, default in PASSTHROUGH_DEFAULTS.items()}
    warnings: list[str] = []

    metrics = []
    direct_metrics = payload.get("metrics", [])
    if direct_metrics:
        if not isinstance(direct_metrics, list):
            raise ValueError("metrics must be a list when provided")
        metrics.extend([metric for metric in direct_metrics if isinstance(metric, dict)])

    extracts = payload.get("extracts", [])
    if extracts and not isinstance(extracts, list):
        raise ValueError("extracts must be a list when provided")

    discovered_sources = []
    for extract in extracts:
        if not isinstance(extract, dict):
            warnings.append("extract entry is not an object")
            continue
        metrics.extend(normalize_extract(extract, warnings))
        source_id = extract.get("source_id")
        if source_id:
            discovered_sources.append(source_id)

    existing_sources = normalized.get("sources") or []
    if not isinstance(existing_sources, list):
        existing_sources = [existing_sources]
    normalized["sources"] = list(dict.fromkeys([str(item) for item in existing_sources + discovered_sources]))

    normalized["metrics"] = metrics
    if warnings:
        notes = normalized.get("notes") or []
        if not isinstance(notes, list):
            notes = [str(notes)]
        notes.extend([f"Normalizer warning: {warning}" for warning in warnings])
        normalized["notes"] = notes

    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize raw Agent 10 signal inputs")
    parser.add_argument("--input", required=True, help="JSON input file, or '-' for stdin")
    parser.add_argument("--output", required=True, help="Path to write normalized JSON")
    args = parser.parse_args()

    if args.input != "-" and not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = load_input(args.input)
        normalized = normalize_payload(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as handle:
        json.dump(normalized, handle, indent=2)
        handle.write("\n")

    print(
        f"Normalized signal inputs → {args.output} | "
        f"extracts={len(payload.get('extracts', []))} metrics={len(normalized['metrics'])}"
    )


if __name__ == "__main__":
    main()