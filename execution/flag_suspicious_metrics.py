#!/usr/bin/env python3
"""Flag suspicious metrics based on configurable thresholds.

Stateless — reads metric array, annotates with suspicious flags, writes output.

Usage:
    python execution/flag_suspicious_metrics.py --input .tmp/metrics.json --config config/domo.yml --output .tmp/flagged.json
"""

import argparse
import json
import os
import sys

import yaml


def load_thresholds(config_path: str) -> dict:
    """Load suspicious metric thresholds from domo.yml."""
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    thresholds = config.get("thresholds", {}).get("suspicious_metric", {})
    return {
        "yoy_flag_pct": thresholds.get("yoy_flag_pct", 50),
        "flag_zero_values": thresholds.get("flag_zero_values", True),
        "flag_identical_segments": thresholds.get("flag_identical_segments", True),
    }


def flag_metric(metric: dict, thresholds: dict) -> dict:
    """Annotate a metric entry with suspicious flags."""
    reasons = []

    yoy = metric.get("yoy_delta_pct")
    if yoy is not None and abs(yoy) > thresholds["yoy_flag_pct"]:
        reasons.append(f"YoY delta {yoy}% exceeds ±{thresholds['yoy_flag_pct']}% threshold")

    value = metric.get("value")
    if thresholds["flag_zero_values"] and value is not None and value == 0.0:
        reasons.append("Value is exactly 0%")

    segments = metric.get("segment_values")
    if thresholds["flag_identical_segments"] and segments and len(segments) > 1:
        if len(set(segments)) == 1:
            reasons.append(f"All {len(segments)} segment values are identical ({segments[0]})")

    result = metric.copy()
    result["suspicious"] = len(reasons) > 0
    result["suspicious_reason"] = "; ".join(reasons) if reasons else None
    return result


def main():
    parser = argparse.ArgumentParser(description="Flag suspicious metrics")
    parser.add_argument("--input", required=True, help="JSON file with metric array")
    parser.add_argument("--config", required=True, help="Path to config/domo.yml")
    parser.add_argument("--output", required=True, help="Path to write flagged results")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.config):
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    with open(args.input) as f:
        metrics = json.load(f)

    if not isinstance(metrics, list):
        print("ERROR: input must be a JSON array", file=sys.stderr)
        sys.exit(1)

    thresholds = load_thresholds(args.config)
    flagged = [flag_metric(m, thresholds) for m in metrics]

    suspicious_count = sum(1 for m in flagged if m["suspicious"])

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(flagged, f, indent=2)

    print(f"Processed {len(flagged)} metrics → {args.output} ({suspicious_count} flagged)")
    for m in flagged:
        if m["suspicious"]:
            print(f"  ⚠ {m.get('metric', '?')} ({m.get('market', '?')}): {m['suspicious_reason']}")


if __name__ == "__main__":
    main()
