#!/usr/bin/env python3
"""Merge global → team → local YAML config; output resolved JSON.

Usage:
    python execution/resolve_config.py --global config/atlassian.yml
    python execution/resolve_config.py --global config/atlassian.yml --key growth_agent.epic_key
    python execution/resolve_config.py --global config/atlassian.yml --team config/atlassian.team.yml --local config/atlassian.local.yml --output .tmp/config.json
"""

import argparse
import json
import os
import sys

import yaml


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins at every key."""
    merged = base.copy()
    for key, val in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = deep_merge(merged[key], val)
        else:
            merged[key] = val
    return merged


def extract_key(config: dict, dotted_key: str):
    """Extract a value from config using dot-notation (e.g. 'growth_agent.epic_key')."""
    parts = dotted_key.split(".")
    current = config
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            print(f"ERROR: key '{dotted_key}' not found (failed at '{part}')", file=sys.stderr)
            sys.exit(1)
        current = current[part]
    return current


def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def main():
    parser = argparse.ArgumentParser(description="Merge layered YAML config → JSON")
    parser.add_argument("--global", dest="global_cfg", required=True, help="Global config (required)")
    parser.add_argument("--team", dest="team_cfg", default=None, help="Team config (optional)")
    parser.add_argument("--local", dest="local_cfg", default=None, help="Local config (optional)")
    parser.add_argument("--key", default=None, help="Dot-notation key to extract")
    parser.add_argument("--output", default=None, help="Output file (stdout if omitted)")
    args = parser.parse_args()

    if not os.path.exists(args.global_cfg):
        print(f"ERROR: global config not found: {args.global_cfg}", file=sys.stderr)
        sys.exit(1)

    config = load_yaml(args.global_cfg)

    if args.team_cfg and os.path.exists(args.team_cfg):
        config = deep_merge(config, load_yaml(args.team_cfg))

    if args.local_cfg and os.path.exists(args.local_cfg):
        config = deep_merge(config, load_yaml(args.local_cfg))

    result = extract_key(config, args.key) if args.key else config

    output_str = json.dumps(result, indent=2, default=str) if isinstance(result, (dict, list)) else str(result)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output_str + "\n")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
