#!/usr/bin/env python3
"""Build a deterministic signal report from normalized KPI metric inputs.

This script is intended for Agent 10's rule-heavy post-query stage. It does not
fetch Domo data itself. Instead, it consumes a normalized JSON payload produced
by orchestration or a future extractor, applies config-driven thresholds,
reuses suspicious-metric logic, and writes stable JSON + markdown outputs.

Usage:
    python execution/build_signal_report.py \
        --input .tmp/signal-input.json \
        --config config/domo.yml \
        --json-output outputs/signal-agent/signal-report.json \
        --signals-output outputs/signal-agent/signals.md \
        --pipeline-output outputs/signal-agent/pipeline-context.md

    printf '{"metrics": [...]}' | python execution/build_signal_report.py \
        --input - \
        --config config/domo.yml \
        --json-output .tmp/signal-report.json \
        --signals-output .tmp/signals.md \
        --pipeline-output .tmp/pipeline-context.md
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import yaml

from flag_suspicious_metrics import flag_metric, load_thresholds as load_suspicious_thresholds


def load_signal_thresholds(config_path: str) -> dict[str, Any]:
    with open(config_path) as handle:
        config = yaml.safe_load(handle) or {}
    return config.get("thresholds", {}).get("signal_threshold_pct", {})


def load_input(input_path: str) -> dict[str, Any]:
    if input_path == "-":
        raw = sys.stdin.read()
    else:
        with open(input_path) as handle:
            raw = handle.read()

    if not raw.strip():
        raise ValueError("input is empty")

    data = json.loads(raw)
    if isinstance(data, list):
        return {"metrics": data}
    if isinstance(data, dict):
        return data
    raise ValueError("input must be a JSON object or array")


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


def comparison_value(metric: dict[str, Any]) -> float | None:
    metric_type = (metric.get("metric_type") or "default").lower()
    if metric_type == "ratings":
        return to_float(metric.get("delta_value", metric.get("delta_pct")))
    return to_float(metric.get("delta_pct", metric.get("delta_value")))


def threshold_for_metric(metric: dict[str, Any], thresholds: dict[str, Any]) -> float:
    metric_type = (metric.get("metric_type") or "default").lower()
    default_threshold = thresholds.get("default", 10)
    return float(thresholds.get(metric_type, default_threshold))


def keep_metric(metric: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, str | None]:
    if metric.get("exclude_reason"):
        return False, str(metric["exclude_reason"])
    if metric.get("always_include"):
        return True, None

    delta = comparison_value(metric)
    if delta is None:
        return False, "missing comparable delta"

    threshold = threshold_for_metric(metric, thresholds)
    if abs(delta) >= threshold:
        return True, None

    metric_type = (metric.get("metric_type") or "default").lower()
    comparator = "absolute change" if metric_type == "ratings" else "% movement"
    return False, f"below {threshold:g} {comparator} threshold"


def format_number(value: Any, unit: str | None = None) -> str:
    numeric = to_float(value)
    if numeric is None:
        return "—"

    if unit == "percent":
        return f"{numeric:.2f}%" if abs(numeric) < 1 else f"{numeric:.1f}%"
    if unit == "currency":
        return f"{numeric:,.2f}"
    if numeric.is_integer():
        return f"{int(numeric):,}"
    return f"{numeric:,.2f}"


def render_value(metric: dict[str, Any]) -> str:
    if metric.get("value_display"):
        return str(metric["value_display"])
    return format_number(metric.get("value"), metric.get("unit"))


def render_delta(metric: dict[str, Any]) -> str:
    if metric.get("delta_display"):
        return str(metric["delta_display"])

    metric_type = (metric.get("metric_type") or "default").lower()
    delta_pct = to_float(metric.get("delta_pct"))
    delta_value = to_float(metric.get("delta_value"))

    if metric_type == "ratings" and delta_value is not None:
        prefix = "+" if delta_value > 0 else ""
        return f"{prefix}{delta_value:.2f}"
    if delta_pct is not None:
        prefix = "+" if delta_pct > 0 else ""
        return f"{prefix}{delta_pct:.1f}%"
    if delta_value is not None:
        prefix = "+" if delta_value > 0 else ""
        return f"{prefix}{delta_value:.2f}"
    return "—"


def severity(metric: dict[str, Any]) -> float:
    delta = comparison_value(metric)
    return abs(delta) if delta is not None else 0.0


def build_signal_entries(payload: dict[str, Any], config_path: str) -> dict[str, Any]:
    thresholds = load_signal_thresholds(config_path)
    suspicious_thresholds = load_suspicious_thresholds(config_path)

    confirmed = []
    excluded = []

    for metric in payload.get("metrics", []):
        if not isinstance(metric, dict):
            raise ValueError("every metric entry must be an object")

        keep, reason = keep_metric(metric, thresholds)
        enriched = flag_metric(
            {
                "metric": metric.get("metric"),
                "market": metric.get("market"),
                "value": to_float(metric.get("value")),
                "yoy_delta_pct": to_float(metric.get("yoy_delta_pct")),
                "segment_values": metric.get("segment_values"),
            },
            suspicious_thresholds,
        )

        entry = dict(metric)
        entry["suspicious"] = enriched["suspicious"]
        entry["suspicious_reason"] = enriched["suspicious_reason"]

        if keep:
            confirmed.append(entry)
        else:
            entry["excluded_reason"] = reason
            excluded.append(entry)

    confirmed.sort(
        key=lambda item: (
            -severity(item),
            str(item.get("market", "")),
            str(item.get("platform", "")),
            str(item.get("metric", "")),
        )
    )
    excluded.sort(key=lambda item: str(item.get("metric", "")))

    for index, entry in enumerate(confirmed, start=1):
        entry["signal_id"] = f"S{index}"

    return {
        "run_date": payload.get("run_date") or datetime.now().strftime("%Y-%m-%d"),
        "period_label": payload.get("period_label") or "unspecified",
        "sources": payload.get("sources", []),
        "query_windows": payload.get("query_windows", []),
        "pm_context": payload.get("pm_context", []),
        "carry_forward": payload.get("carry_forward", []),
        "hypotheses": payload.get("hypotheses", []),
        "funnel_tables": payload.get("funnel_tables", []),
        "notes": payload.get("notes", []),
        "confirmed_signals": confirmed,
        "excluded_signals": excluded,
        "summary": {
            "total_metrics": len(payload.get("metrics", [])),
            "confirmed_signals": len(confirmed),
            "excluded_signals": len(excluded),
            "suspicious_confirmed": sum(1 for entry in confirmed if entry.get("suspicious")),
        },
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_signals_markdown(report: dict[str, Any]) -> str:
    lines = [f"# Signal Report — {report['run_date']}"]
    lines.append(f"Period: {report['period_label']}")

    if report.get("sources"):
        lines.append("Sources: " + ", ".join(str(source) for source in report["sources"]))

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Confirmed Signals")
    lines.append("")

    confirmed_rows = []
    for entry in report["confirmed_signals"]:
        suspicious_display = entry.get("suspicious_reason") or "—"
        confirmed_rows.append(
            [
                entry["signal_id"],
                str(entry.get("market", "All")),
                str(entry.get("platform", "All")),
                str(entry.get("metric", "")),
                render_value(entry),
                render_delta(entry),
                str(entry.get("period", report["period_label"])),
                suspicious_display,
            ]
        )

    if confirmed_rows:
        lines.append(
            markdown_table(
                ["#", "Market", "Platform", "Metric", "Value", "Delta", "Period", "Suspicious"],
                confirmed_rows,
            )
        )
    else:
        lines.append("No signals met the configured thresholds.")

    if report["excluded_signals"]:
        lines.append("")
        lines.append("## Excluded from Triangulation")
        lines.append("")
        excluded_rows = []
        for entry in report["excluded_signals"]:
            excluded_rows.append([
                str(entry.get("metric", "")),
                str(entry.get("excluded_reason", "")),
            ])
        lines.append(markdown_table(["Signal", "Reason"], excluded_rows))

    if report["hypotheses"]:
        lines.append("")
        lines.append("## Hypotheses for Triangulation")
        lines.append("")
        hypothesis_rows = []
        for index, hypothesis in enumerate(report["hypotheses"], start=1):
            hypothesis_rows.append(
                [
                    str(hypothesis.get("id", f"H{index}")),
                    str(hypothesis.get("hypothesis", "")),
                    str(hypothesis.get("failure_point", "")),
                    str(hypothesis.get("markets", "")),
                ]
            )
        lines.append(markdown_table(["#", "Hypothesis", "Failure Point", "Markets"], hypothesis_rows))

    if report["funnel_tables"]:
        lines.append("")
        lines.append("## Funnel View")
        for table in report["funnel_tables"]:
            lines.append("")
            lines.append(f"### {table.get('title', 'Untitled table')}")
            if table.get("description"):
                lines.append(str(table["description"]))
                lines.append("")
            headers = [str(column) for column in table.get("columns", [])]
            rows = [[str(cell) for cell in row] for row in table.get("rows", [])]
            if headers and rows:
                lines.append(markdown_table(headers, rows))
            elif headers:
                lines.append(markdown_table(headers, []))
            else:
                lines.append("No table data supplied.")
            for note in table.get("notes", []):
                lines.append("")
                lines.append(str(note))

    if report.get("notes"):
        lines.append("")
        lines.append("## Notes")
        for note in report["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines).rstrip() + "\n"


def render_pipeline_context(report: dict[str, Any]) -> str:
    lines = [f"# Pipeline Context — Signal Builder — {report['run_date']}"]

    if report["query_windows"]:
        lines.append("")
        lines.append("## Query Windows")
        for item in report["query_windows"]:
            lines.append(f"- {item}")

    if report["pm_context"]:
        lines.append("")
        lines.append("## PM-Confirmed Context")
        for item in report["pm_context"]:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("## Confirmed Signal List")
    if report["confirmed_signals"]:
        for entry in report["confirmed_signals"]:
            signal = (
                f"{entry['signal_id']}: {entry.get('market', 'All')} / {entry.get('platform', 'All')} "
                f"{entry.get('metric', '')} = {render_value(entry)} ({render_delta(entry)})"
            )
            if entry.get("suspicious_reason"):
                signal += f" — suspicious: {entry['suspicious_reason']}"
            lines.append(f"- {signal}")
    else:
        lines.append("- None")

    if report["excluded_signals"]:
        lines.append("")
        lines.append("## Excluded from Triangulation")
        for entry in report["excluded_signals"]:
            lines.append(f"- {entry.get('metric', '')}: {entry.get('excluded_reason', '')}")

    if report["carry_forward"]:
        lines.append("")
        lines.append("## Carry-Forward")
        for item in report["carry_forward"]:
            lines.append(f"- {item}")

    if report["hypotheses"]:
        lines.append("")
        lines.append("## Hypotheses for Triangulation")
        for index, hypothesis in enumerate(report["hypotheses"], start=1):
            hid = hypothesis.get("id", f"H{index}")
            summary = hypothesis.get("hypothesis", "")
            failure_point = hypothesis.get("failure_point")
            markets = hypothesis.get("markets")
            extra = []
            if failure_point:
                extra.append(str(failure_point))
            if markets:
                extra.append(str(markets))
            suffix = f" ({' | '.join(extra)})" if extra else ""
            lines.append(f"- {hid}: {summary}{suffix}")

    return "\n".join(lines).rstrip() + "\n"


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic signal report")
    parser.add_argument("--input", required=True, help="JSON file with normalized signal payload, or '-' for stdin")
    parser.add_argument("--config", required=True, help="Path to config/domo.yml")
    parser.add_argument("--json-output", required=True, help="Path to write normalized JSON report")
    parser.add_argument("--signals-output", required=True, help="Path to write markdown signal report")
    parser.add_argument("--pipeline-output", required=True, help="Path to write pipeline context markdown")
    args = parser.parse_args()

    if args.input != "-" and not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.config):
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = load_input(args.input)
        report = build_signal_entries(payload, args.config)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

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
        f"Built signal report → {args.signals_output} | "
        f"confirmed={report['summary']['confirmed_signals']} "
        f"excluded={report['summary']['excluded_signals']} "
        f"suspicious={report['summary']['suspicious_confirmed']}"
    )


if __name__ == "__main__":
    main()