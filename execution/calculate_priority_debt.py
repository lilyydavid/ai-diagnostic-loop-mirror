#!/usr/bin/env python3
"""Calculate priority debt and escalation flags from ranked-hypotheses.json history.

Groups entries by failure_id across cycles, classifies trends, computes debt scores.

Usage:
    python execution/calculate_priority_debt.py \
        --input outputs/prioritisation/ranked-hypotheses.json \
        --output outputs/trend/signal-trend.json \
        --config config/domo.yml
"""

import argparse
import json
import os
import sys
from datetime import datetime

import yaml


def load_thresholds(config_path: str) -> dict:
    """Load trend escalation thresholds from domo.yml."""
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    te = config.get("thresholds", {}).get("trend_escalation", {})
    return {
        "min_cycles_for_trend": te.get("min_cycles_for_trend", 2),
        "unactioned_cycles_escalate": te.get("unactioned_cycles_escalate", 3),
        "deteriorating_unactioned": te.get("deteriorating_unactioned", 2),
        "priority_score_threshold": te.get("priority_score_threshold", 12),
    }


def classify_confidence_trend(scores: list[float]) -> str:
    """Classify confidence trend across cycles."""
    if len(scores) < 2:
        return "insufficient_data"
    diffs = [scores[i + 1] - scores[i] for i in range(len(scores) - 1)]
    if all(d > 0 for d in diffs):
        return "deteriorating"  # all rising = getting worse
    if all(d < 0 for d in diffs):
        return "improving"
    range_val = max(scores) - min(scores)
    if range_val <= 0.5:
        return "stable"
    return "volatile"


def classify_priority_trend(scores: list[float]) -> str:
    """Classify priority score trend across cycles."""
    if len(scores) < 2:
        return "insufficient_data"
    first, latest = scores[0], scores[-1]
    if first == 0:
        return "escalating" if latest > 0 else "stable"
    change_pct = abs(latest - first) / first
    if latest > first:
        return "escalating" if change_pct > 0.1 else "stable"
    elif latest < first:
        return "de-escalating" if change_pct > 0.1 else "stable"
    return "stable"


def check_consecutive_no_jira(cycle_entries: list, threshold: int) -> bool:
    """Check if jira_created was false for >= threshold consecutive recent cycles."""
    recent = cycle_entries[-threshold:]
    if len(recent) < threshold:
        return False
    return all(not e.get("jira_created", False) for e in recent)


def build_failure_timelines(cycles: list) -> dict:
    """Group entries by failure_id across all cycles."""
    timelines = {}
    for cycle in cycles:
        run_date = cycle.get("run_date", "unknown")
        for entry in cycle.get("entries", []):
            fid = entry.get("failure_id", "?")
            if fid not in timelines:
                timelines[fid] = {
                    "failure_id": fid,
                    "description": entry.get("description", ""),
                    "market": entry.get("market", ""),
                    "cycle_entries": [],
                }
            timelines[fid]["cycle_entries"].append({
                "run_date": run_date,
                "confidence_score": entry.get("confidence_score", 0),
                "impact_score": entry.get("impact_score", 0),
                "scope_score": entry.get("scope_score", 0),
                "priority_score": entry.get("priority_score", 0),
                "jira_created": entry.get("jira_created", False),
                "jira_ticket": entry.get("jira_ticket"),
                "sprint_viable": entry.get("sprint_viable", False),
                "lineage": entry.get("lineage", {}),
            })
    return timelines


def analyse_failure(fid: str, timeline: dict, thresholds: dict) -> dict:
    """Analyse a single failure's history and compute debt + escalation."""
    cycle_entries = timeline["cycle_entries"]
    cycles_count = len(cycle_entries)

    confidence_scores = [e["confidence_score"] for e in cycle_entries]
    priority_scores = [e["priority_score"] for e in cycle_entries]
    confidence_history = [
        {"run_date": e["run_date"], "confidence_score": e["confidence_score"]}
        for e in cycle_entries
    ]

    # Latest entry
    latest = cycle_entries[-1]
    lineage = latest.get("lineage", {})
    cycles_unactioned = lineage.get("cycles_unactioned", 0)

    # Trends
    confidence_trend = classify_confidence_trend(confidence_scores) if cycles_count >= thresholds["min_cycles_for_trend"] else "insufficient_data"
    priority_trend = classify_priority_trend(priority_scores) if cycles_count >= thresholds["min_cycles_for_trend"] else "insufficient_data"

    # Priority debt
    priority_debt_score = latest["impact_score"] * latest["confidence_score"] * cycles_unactioned

    # Escalation flags
    escalation_reasons = []

    if cycles_unactioned >= thresholds["unactioned_cycles_escalate"]:
        escalation_reasons.append(f"unactioned for {cycles_unactioned} cycles (threshold: {thresholds['unactioned_cycles_escalate']})")

    if confidence_trend == "deteriorating" and cycles_unactioned >= thresholds["deteriorating_unactioned"]:
        escalation_reasons.append(f"confidence deteriorating + unactioned for {cycles_unactioned} cycles")

    if latest["priority_score"] >= thresholds["priority_score_threshold"] and check_consecutive_no_jira(cycle_entries, 2):
        escalation_reasons.append(f"priority score {latest['priority_score']} >= {thresholds['priority_score_threshold']} with no Jira for 2+ cycles")

    # Collect Jira tickets
    jira_tickets = [e["jira_ticket"] for e in cycle_entries if e.get("jira_ticket")]

    return {
        "failure_id": fid,
        "description": timeline["description"],
        "market": timeline["market"],
        "first_seen_date": cycle_entries[0]["run_date"],
        "cycles_in_history": cycles_count,
        "confidence_history": confidence_history,
        "confidence_trend": confidence_trend,
        "priority_score_history": priority_scores,
        "priority_trend": priority_trend,
        "cumulative_cycles_unactioned": cycles_unactioned,
        "times_actioned": lineage.get("times_actioned", 0),
        "last_actioned_date": None,  # Would need Jira check for actual date
        "jira_tickets": list(set(jira_tickets)),
        "priority_debt_score": priority_debt_score,
        "escalate": len(escalation_reasons) > 0,
        "escalation_reasons": escalation_reasons,
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate priority debt and escalation flags")
    parser.add_argument("--input", required=True, help="Path to ranked-hypotheses.json")
    parser.add_argument("--output", required=True, help="Path to write signal-trend.json")
    parser.add_argument("--config", required=True, help="Path to config/domo.yml")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.config):
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    with open(args.input) as f:
        cycles = json.load(f)

    if not isinstance(cycles, list):
        print("ERROR: input must be a JSON array of cycle objects", file=sys.stderr)
        sys.exit(1)

    thresholds = load_thresholds(args.config)
    timelines = build_failure_timelines(cycles)
    failures = [analyse_failure(fid, tl, thresholds) for fid, tl in timelines.items()]

    # Sort by priority_debt_score descending
    failures.sort(key=lambda f: -f["priority_debt_score"])

    escalation_candidates = [f for f in failures if f["escalate"]]

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "cycles_analysed": len(cycles),
        "failures": failures,
        "summary": {
            "total_failures_tracked": len(failures),
            "escalation_candidates": len(escalation_candidates),
            "improving": sum(1 for f in failures if f["confidence_trend"] == "improving"),
            "stable": sum(1 for f in failures if f["confidence_trend"] == "stable"),
            "single_cycle_baseline": sum(1 for f in failures if f["cycles_in_history"] == 1),
        },
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Priority debt report → {args.output}")
    print(f"  Cycles analysed: {len(cycles)}")
    print(f"  Failures tracked: {len(failures)}")
    print(f"  Escalation candidates: {len(escalation_candidates)}")
    for f in escalation_candidates:
        print(f"  ⚠ {f['failure_id']}: debt={f['priority_debt_score']}, reasons: {'; '.join(f['escalation_reasons'])}")


if __name__ == "__main__":
    main()
