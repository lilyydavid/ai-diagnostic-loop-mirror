#!/usr/bin/env python3
"""Check if signals.md is stale (file age > configured staleness window).

Used by Agent 20 Step 2 (FR41).

Usage:
    python execution/check_signals_staleness.py --signals-file outputs/signal-agent/signals.md --config config/atlassian.yml
"""

import argparse
import json
import os
import sys
from datetime import datetime

import yaml


def main():
    parser = argparse.ArgumentParser(description="Check signals.md staleness")
    parser.add_argument("--signals-file", required=True, help="Path to signals.md")
    parser.add_argument("--config", required=True, help="Path to config/atlassian.yml")
    parser.add_argument("--output", default=None, help="Output file (stdout if omitted)")
    args = parser.parse_args()

    # Load staleness threshold
    if not os.path.exists(args.config):
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    with open(args.config) as f:
        config = yaml.safe_load(f) or {}
    limit_days = config.get("inspiration_loop", {}).get("signal_staleness_days", 7)

    # Check file
    if not os.path.exists(args.signals_file):
        result = {
            "stale": True,
            "age_days": None,
            "limit_days": limit_days,
            "signals_file": args.signals_file,
            "reason": "file_not_found",
        }
    else:
        mtime = os.path.getmtime(args.signals_file)
        mtime_dt = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - mtime_dt).days

        result = {
            "stale": age_days > limit_days,
            "age_days": age_days,
            "limit_days": limit_days,
            "signals_file": args.signals_file,
            "last_modified": mtime_dt.strftime("%Y-%m-%d %H:%M"),
        }

    output_str = json.dumps(result, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output_str + "\n")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
