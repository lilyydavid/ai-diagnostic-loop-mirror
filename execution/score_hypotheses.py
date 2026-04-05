#!/usr/bin/env python3
"""Score and rank hypotheses from experiment-designs.json.

Computes priority_score = confidence × impact × scope, sorts, assigns ranks.
Optionally reads bet-log.json for pm_odds tiebreaker (FR49).

Usage:
    python execution/score_hypotheses.py --input outputs/validation/experiment-designs.json --output .tmp/scored.json
    python execution/score_hypotheses.py --input outputs/validation/experiment-designs.json --output .tmp/scored.json --bet-log outputs/inspiration/bet-log.json
"""

import argparse
import json
import os
import sys


# ── Score mappings ──────────────────────────────────────────────────────────

LABEL_TO_SCORE = {
    "high": 3,
    "medium-high": 2.5,
    "medium": 2,
    "low-medium": 1.5,
    "low": 1,
}

SCOPE_LABEL_TO_SCORE = {
    "tight": 3,
    "moderate": 2,
    "complex": 1,
}

PM_ODDS_ORDER = {
    "i'd bet on it": 0,
    "likely": 1,
    "maybe": 2,
    "long shot": 3,
}


def map_score(label: str, mapping: dict, field_name: str) -> float:
    """Map a string label to a numeric score."""
    key = label.strip().lower()
    if key in mapping:
        return mapping[key]
    print(f"WARNING: unknown {field_name} label '{label}', defaulting to 1", file=sys.stderr)
    return 1


def parse_pm_odds(odds_str: str | None) -> int:
    """Convert pm_odds string to sort key (lower = better)."""
    if not odds_str:
        return 99
    key = odds_str.strip().lower()
    return PM_ODDS_ORDER.get(key, 50)


def load_bet_log(path: str) -> list:
    """Load bet-log.json if it exists."""
    if not path or not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def match_bet(entry: dict, bets: list) -> dict | None:
    """Find a bet whose target_metric matches the entry's funnel_stage or description."""
    if not bets:
        return None
    desc = (entry.get("description", "") + " " + entry.get("funnel_stage", "")).lower()
    for bet in bets:
        target = (bet.get("target_metric") or "").lower()
        if target and target in desc:
            return bet
    return None


def score_entry(entry: dict, bets: list) -> dict:
    """Score a single hypothesis entry."""
    confidence_score = map_score(entry.get("confidence", "Low"), LABEL_TO_SCORE, "confidence")
    impact_score = map_score(entry.get("impact", "Low"), LABEL_TO_SCORE, "impact")

    # Prefer numeric scope_score if present
    if "scope_score" in entry and isinstance(entry["scope_score"], (int, float)):
        scope_score = entry["scope_score"]
    else:
        scope_score = map_score(entry.get("scope", "Complex"), SCOPE_LABEL_TO_SCORE, "scope")

    # Hard-block rule: floor impact at 3 if signal is flagged hard block
    signal = (entry.get("signal_connected") or "").lower()
    if "hard block" in signal:
        impact_score = max(impact_score, 3)

    priority_score = confidence_score * impact_score * scope_score

    # SP and sprint viability
    ab_test = entry.get("ab_test", {})
    sp_estimate = ab_test.get("sp_estimate", entry.get("sp_estimate", 99))
    sprint_viable = sp_estimate <= 3

    # Bet-log enrichment
    matched_bet = match_bet(entry, bets)
    pm_odds = matched_bet.get("pm_odds") if matched_bet else None
    market_context = matched_bet.get("market_context") if matched_bet else None

    return {
        "failure_id": entry.get("hypothesis_id") or entry.get("failure_id") or entry.get("id"),
        "description": entry.get("description", ""),
        "market": entry.get("market", ""),
        "confidence_score": confidence_score,
        "impact_score": impact_score,
        "scope_score": scope_score,
        "priority_score": priority_score,
        "sprint_viable": sprint_viable,
        "sp_estimate": sp_estimate,
        "inspiration_pm_odds": pm_odds,
        "inspiration_market_context": market_context,
        "_pm_odds_sort": parse_pm_odds(pm_odds),
    }


def main():
    parser = argparse.ArgumentParser(description="Score and rank hypotheses")
    parser.add_argument("--input", required=True, help="Path to experiment-designs.json")
    parser.add_argument("--output", required=True, help="Path to write scored output JSON")
    parser.add_argument("--bet-log", default=None, help="Path to bet-log.json (optional, FR49)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input) as f:
        data = json.load(f)

    entries = data.get("entries", data if isinstance(data, list) else [])
    if not entries:
        print("ERROR: no entries found in input", file=sys.stderr)
        sys.exit(1)

    bets = load_bet_log(args.bet_log)

    scored = [score_entry(e, bets) for e in entries]

    # Sort: priority_score desc → sp_estimate asc → pm_odds (lower = better)
    scored.sort(key=lambda x: (-x["priority_score"], x["sp_estimate"], x["_pm_odds_sort"]))

    # Assign ranks and clean up sort key
    for i, entry in enumerate(scored, 1):
        entry["rank"] = i
        del entry["_pm_odds_sort"]

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(scored, f, indent=2)

    print(f"Scored {len(scored)} hypotheses → {args.output}")
    for s in scored:
        print(f"  #{s['rank']} {s['failure_id']} — score {s['priority_score']} (C{s['confidence_score']}×I{s['impact_score']}×S{s['scope_score']}) SP={s['sp_estimate']} sprint={s['sprint_viable']}")


if __name__ == "__main__":
    main()
