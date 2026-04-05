#!/usr/bin/env python3
"""Run the deterministic Agent 10 signal pipeline in one command.

Flow:
1. normalize_signal_inputs.py logic
2. calculate_funnel_tables.py logic (optional, when funnel_inputs provided)
3. build_signal_report.py logic

Usage:
    python execution/run_signal_pipeline.py \
        --input .tmp/raw-signal-input.json \
        --config config/domo.yml \
        --json-output outputs/signal-agent/signal-report.json \
        --signals-output outputs/signal-agent/signals.md \
        --pipeline-output outputs/signal-agent/pipeline-context.md
"""

import argparse
import json
import os
import sys

from build_signal_report import build_signal_entries, ensure_parent, load_input as load_builder_input, render_pipeline_context, render_signals_markdown
from calculate_funnel_tables import calculate_tables
from normalize_signal_inputs import normalize_payload


def funnel_source_ids(funnel_inputs: dict) -> list[str]:
    source_ids = []
    for section in ["session_funnel", "user_full_funnel", "checkout_funnel"]:
        value = funnel_inputs.get(section)
        if isinstance(value, dict) and value.get("source_id"):
            source_ids.append(str(value["source_id"]))
    return source_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic Agent 10 signal pipeline")
    parser.add_argument("--input", required=True, help="Raw signal pipeline input JSON, or '-' for stdin")
    parser.add_argument("--config", required=True, help="Path to config/domo.yml")
    parser.add_argument("--json-output", required=True, help="Final normalized signal report JSON")
    parser.add_argument("--signals-output", required=True, help="Final markdown signal report")
    parser.add_argument("--pipeline-output", required=True, help="Final pipeline context markdown")
    parser.add_argument("--normalized-output", default=None, help="Optional path to write normalized intermediate JSON")
    parser.add_argument("--tables-output", default=None, help="Optional path to write calculated funnel tables JSON")
    args = parser.parse_args()

    if args.input != "-" and not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.config):
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    try:
        raw_payload = load_builder_input(args.input)
        normalized = normalize_payload(raw_payload)
        funnel_inputs = raw_payload.get("funnel_inputs", {}) if isinstance(raw_payload.get("funnel_inputs"), dict) else {}
        generated_tables = calculate_tables(funnel_inputs) if funnel_inputs else []
        existing_tables = normalized.get("funnel_tables") or []
        if not isinstance(existing_tables, list):
            existing_tables = [existing_tables]
        if generated_tables:
            normalized["funnel_tables"] = generated_tables
        elif existing_tables:
            normalized["funnel_tables"] = existing_tables

        existing_sources = normalized.get("sources") or []
        if not isinstance(existing_sources, list):
            existing_sources = [existing_sources]
        normalized["sources"] = list(dict.fromkeys([str(item) for item in existing_sources + funnel_source_ids(funnel_inputs)]))

        report = build_signal_entries(normalized, args.config)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.normalized_output:
        ensure_parent(args.normalized_output)
        with open(args.normalized_output, "w") as handle:
            json.dump(normalized, handle, indent=2)
            handle.write("\n")

    if args.tables_output:
        ensure_parent(args.tables_output)
        with open(args.tables_output, "w") as handle:
            json.dump({"funnel_tables": normalized.get("funnel_tables", [])}, handle, indent=2)
            handle.write("\n")

    ensure_parent(args.json_output)
    ensure_parent(args.signals_output)
    ensure_parent(args.pipeline_output)

    with open(args.json_output, "w") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    with open(args.signals_output, "w") as handle:
        handle.write(render_signals_markdown(report))

    with open(args.pipeline_output, "w") as handle:
        handle.write(render_pipeline_context(report))

    print(
        f"Ran signal pipeline → {args.signals_output} | "
        f"metrics={len(normalized.get('metrics', []))} tables={len(normalized.get('funnel_tables', []))} "
        f"confirmed={report['summary']['confirmed_signals']} excluded={report['summary']['excluded_signals']}"
    )


if __name__ == "__main__":
    main()