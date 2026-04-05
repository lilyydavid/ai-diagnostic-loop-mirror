#!/usr/bin/env python3
"""Check findings-store.json for stale entries; optionally append new entries.

Usage:
    python execution/check_findings_cache.py --store outputs/feedback/findings-store.json --config config/domo.yml --signal-date 2026-04-04
    python execution/check_findings_cache.py --store outputs/feedback/findings-store.json --config config/domo.yml --signal-date 2026-04-04 --mode append --entry '{"queried_at":"2026-04-04","source":"app_reviews","market":"AU","signal_cycle":"2026-04-04","summary":"...","evidence_quality":"High"}'
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime

import yaml


SOURCES = ["app_reviews", "love_meter", "cs_tickets", "search_terms", "confluence_ux", "jira_uxr"]
REQUIRED_FIELDS = {"queried_at", "source", "market", "signal_cycle", "summary", "evidence_quality"}


def load_staleness_days(config_path: str) -> int:
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    return config.get("thresholds", {}).get("findings_staleness_days", 7)


def load_store(store_path: str) -> list:
    if not os.path.exists(store_path):
        return []
    with open(store_path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def check_staleness(entries: list, signal_date: str, staleness_days: int) -> dict:
    """Classify each source/market pair as stale, fresh, or missing."""
    signal_dt = datetime.strptime(signal_date, "%Y-%m-%d")

    # Build latest queried_at per source/market
    latest = {}
    for entry in entries:
        key = f"{entry.get('source', 'unknown')}/{entry.get('market', 'unknown')}"
        queried = entry.get("queried_at", "")
        if queried > latest.get(key, ""):
            latest[key] = queried

    # Find all unique source/market combos from entries
    known_keys = set(latest.keys())

    stale = []
    fresh = []
    missing = []

    # Check all known combos
    for key, queried_at in latest.items():
        try:
            queried_dt = datetime.strptime(queried_at, "%Y-%m-%d")
            age_days = (signal_dt - queried_dt).days
            if age_days > staleness_days:
                stale.append(key)
            else:
                fresh.append(key)
        except ValueError:
            stale.append(key)

    # Check for sources with no entries at all
    markets_seen = set()
    for entry in entries:
        markets_seen.add(entry.get("market", "unknown"))

    for source in SOURCES:
        for market in markets_seen:
            key = f"{source}/{market}"
            if key not in known_keys:
                missing.append(key)

    return {"stale": sorted(stale), "fresh": sorted(fresh), "missing": sorted(missing)}


def validate_entry(entry_dict: dict) -> list:
    """Validate that an entry has required fields."""
    errors = []
    missing = REQUIRED_FIELDS - set(entry_dict.keys())
    if missing:
        errors.append(f"Missing fields: {', '.join(sorted(missing))}")
    if entry_dict.get("source") and entry_dict["source"] not in SOURCES:
        errors.append(f"Unknown source: {entry_dict['source']}. Expected one of: {', '.join(SOURCES)}")
    return errors


def atomic_append(store_path: str, new_entry: dict):
    """Append entry to JSON array file atomically."""
    entries = load_store(store_path)
    entries.append(new_entry)
    dir_name = os.path.dirname(store_path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(entries, f, indent=2)
        shutil.move(tmp_path, store_path)
    except Exception:
        os.unlink(tmp_path)
        raise


def main():
    parser = argparse.ArgumentParser(description="Check/append findings cache")
    parser.add_argument("--store", required=True, help="Path to findings-store.json")
    parser.add_argument("--config", required=True, help="Path to config/domo.yml")
    parser.add_argument("--signal-date", required=True, help="Signal cycle date (YYYY-MM-DD)")
    parser.add_argument("--mode", default="check", choices=["check", "append"])
    parser.add_argument("--entry", default=None, help="JSON string of entry to append (append mode)")
    parser.add_argument("--output", default=None, help="Output file (stdout if omitted, check mode)")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    staleness_days = load_staleness_days(args.config)

    if args.mode == "check":
        entries = load_store(args.store)
        result = check_staleness(entries, args.signal_date, staleness_days)
        result["staleness_days"] = staleness_days
        result["signal_date"] = args.signal_date
        result["total_entries"] = len(entries)

        output_str = json.dumps(result, indent=2)
        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w") as f:
                f.write(output_str + "\n")
        else:
            print(output_str)

        print(f"Staleness check: {len(result['stale'])} stale, {len(result['fresh'])} fresh, {len(result['missing'])} missing (threshold: {staleness_days} days)", file=sys.stderr)

    elif args.mode == "append":
        if not args.entry:
            print("ERROR: --entry required in append mode", file=sys.stderr)
            sys.exit(1)
        try:
            new_entry = json.loads(args.entry)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON in --entry: {e}", file=sys.stderr)
            sys.exit(1)

        errors = validate_entry(new_entry)
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            sys.exit(1)

        atomic_append(args.store, new_entry)
        print(f"Appended entry to {args.store} (source={new_entry.get('source')}, market={new_entry.get('market')})")


if __name__ == "__main__":
    main()
