#!/usr/bin/env python3
"""Check whether an input file is stale (age > threshold).

Generic version of check_signals_staleness.py — works for any upstream output file.

Usage:
    python execution/check_input_staleness.py --file outputs/signal-agent/pipeline-context.md --threshold-days 3
    python execution/check_input_staleness.py --file outputs/validation/experiment-designs.json --threshold-days 3
    python execution/check_input_staleness.py --file outputs/prioritisation/ranked-hypotheses.json --threshold-days 7
"""

import argparse
import json
import os
import sys
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Check if an input file is stale")
    parser.add_argument("--file", required=True, help="Path to file to check")
    parser.add_argument("--threshold-days", type=int, default=3, help="Staleness threshold in days (default: 3)")
    parser.add_argument("--output", default=None, help="Output file path (stdout if omitted)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        result = {
            "stale": True,
            "age_days": None,
            "threshold_days": args.threshold_days,
            "file": args.file,
            "reason": "file_not_found",
        }
    else:
        mtime = os.path.getmtime(args.file)
        mtime_dt = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - mtime_dt).days

        result = {
            "stale": age_days > args.threshold_days,
            "age_days": age_days,
            "threshold_days": args.threshold_days,
            "file": args.file,
            "last_modified": mtime_dt.strftime("%Y-%m-%d %H:%M"),
        }

    output_str = json.dumps(result, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output_str + "\n")
    else:
        print(output_str)

    status = "STALE" if result["stale"] else "FRESH"
    age = f"{result['age_days']}d" if result.get("age_days") is not None else "missing"
    print(f"{status}: {args.file} ({age}, threshold {args.threshold_days}d)", file=sys.stderr)


if __name__ == "__main__":
    main()
