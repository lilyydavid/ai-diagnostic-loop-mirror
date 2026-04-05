#!/usr/bin/env python3
"""
create_jira_stories.py — Layer 3 execution script for Jira story creation.

Called by Agent 13 after PM approval and code grounding check.

Reads:
  outputs/validation/experiment-designs.json
  outputs/validation/read-audit.log
  outputs/prioritisation/ranked-hypotheses.json  (lineage, optional)
  outputs/diagnosis/diagnosis.json
  outputs/signal-agent/pipeline-context.md
  config/atlassian.yml (+ team/local overrides)

Writes:
  outputs/jira-writer/created-tickets.md  (overwrite)
  stdout: JSON result — list of created/updated tickets for Agent 13 to embed

Usage:
  python execution/create_jira_stories.py \
    --approved-ids H1 H4 H2 \
    --experiment-designs outputs/validation/experiment-designs.json \
    --pipeline-context outputs/signal-agent/pipeline-context.md \
    --dry-run  # optional — print payloads without creating tickets

Exit codes:
  0  success (all approved stories created or deduped)
  1  credentials error (401)
  2  config error (missing project/epic)
  3  input files missing
  4  partial failure (some stories created, some failed — see stdout JSON)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------

def resolve_config() -> dict:
    """Load config/atlassian.yml with team and local overrides."""
    import yaml  # optional dep — only needed at runtime

    layers = [
        "config/atlassian.yml",
        "config/atlassian.team.yml",
        "config/atlassian.local.yml",
    ]
    merged = {}
    for path in layers:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            _deep_merge(merged, data)
    return merged


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ---------------------------------------------------------------------------
# MCP Jira bridge
# ---------------------------------------------------------------------------
# Agent 13 runs inside Claude Code where MCP tools are available.
# This script is called as a subprocess; it cannot call MCP tools directly.
# Instead, it OUTPUTS a JSON payload describing every Jira operation needed.
# Agent 13 reads that payload and executes the MCP calls — keeping this script
# fully deterministic and testable without MCP access.
#
# Output schema per operation:
#   {"op": "create" | "comment" | "link",
#    "payload": {...},          # args to pass to the MCP tool
#    "hypothesis_id": "H1",
#    "story_type": "quick_win" | "backlog"}
# ---------------------------------------------------------------------------

def make_dedup_label(project_key: str, hypothesis_id: str) -> str:
    """
    Return a deterministic, exact-match Jira label for this hypothesis.
    Used for idempotent dedup: if a story with this label exists and is open,
    comment on it instead of creating a duplicate.

    Format: intel-loop-{project_key_lower}-{hid_slug}
    Example: intel-loop-baapp-h1
    """
    slug = re.sub(r"[^a-z0-9]+", "-", hypothesis_id.lower()).strip("-")
    return f"intel-loop-{project_key.lower()}-{slug}"


def build_summary(repo_name: str, action_title: str) -> str:
    """
    Format: [{repo-name}] {action title}
    Truncated to 70 chars total.
    """
    prefix = f"[{repo_name}] "
    max_title = 70 - len(prefix)
    title = action_title[:max_title] if len(action_title) > max_title else action_title
    return f"{prefix}{title}"


def build_description(exp: dict, pipeline_context: str, verified_files: list, findings_md: str | None) -> str:
    """Assemble the Jira story description from experiment design fields."""

    signal = exp.get("signal_movement", "")
    market = exp.get("market", "All")
    hypothesis = exp.get("hypothesis", "")
    confidence_reason = exp.get("confidence_reason", "")
    impact_reason = exp.get("impact_reason", "")
    variant = exp.get("ab_test", {}).get("variant", "")
    mde = exp.get("ab_test", {}).get("minimum_detectable_effect", "")
    rollback = exp.get("ab_test", {}).get("rollback", "")
    sp = exp.get("sp_estimate", "?")
    sprint_viable = sp <= 3 if isinstance(sp, int) else False
    sp_label = "Quick Win" if sprint_viable else "Backlog"

    # --- Code section ---
    if verified_files:
        code_lines = []
        for f in verified_files:
            repo = f.get("repo", "")
            path = f.get("path", "")
            fn = f.get("function", "")
            code_lines.append(f"- Repo: {repo}\n- File: `{path}` — `{fn}`")
        code_section = "\n".join(code_lines)
        code_section += f"\n- Change: {variant}"
    else:
        code_section = "Code location not yet confirmed. Engineering investigation required before implementation begins."

    # --- User signals ---
    user_signals_section = ""
    if findings_md:
        user_signals_section = f"\n- User signals: {findings_md}"

    # --- Market context (placeholder; Agent 13 injects if enrichment matched) ---
    market_context_section = ""
    if exp.get("market_context"):
        market_context_section = (
            f"\n## Market Context\n{exp['market_context']}"
            + (f"\nPM confidence: {exp['pm_odds']}" if exp.get("pm_odds") else "")
        )

    desc = f"""## Problem
{signal} — {market}

## Evidence
- Funnel signal: {signal}
- Code review: {confidence_reason}
- Why this matters: {impact_reason}{user_signals_section}

## Proposed Change
{variant}

## Where in the code
{code_section}
{market_context_section}
## Acceptance Criteria
- [ ] Primary metric improves by ≥{mde}
- [ ] No regression in related metric
- [ ] Change is behind a feature flag (if touching core funnel)
- [ ] Unit test added for changed function

## Story Points
{sp} SP — {sp_label}

## Related
- Cycle: {datetime.today().strftime('%Y-%m')} | Markets: {market} | Rollback: {rollback}
"""
    return desc.strip()


def slug_from_title(title: str) -> str:
    """Convert a title to a branch-name-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:50].rstrip("-")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict | list | None:
    p = Path(path)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def load_text(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    return p.read_text()


def load_verified_files(exp: dict, audit_log_path: str) -> list:
    """
    Return only the file entries from experiment code_evidence that appear
    in the read-audit.log. Grep_anchor verification is done by Agent 13
    before calling this script; entries passed here are already cleared.
    """
    audit_text = load_text(audit_log_path) or ""
    files = exp.get("code_evidence", {}).get("files", [])
    verified = []
    for f in files:
        if f.get("path", "") in audit_text:
            verified.append(f)
    return verified


def load_lineage(history_path: str, failure_id: str) -> dict:
    history = load_json(history_path)
    if not history:
        return {}
    for run in reversed(history if isinstance(history, list) else [history]):
        for entry in run.get("entries", []):
            if entry.get("failure_id") == failure_id:
                return {
                    "jira_ticket": entry.get("jira_ticket"),
                    "jira_url": entry.get("jira_url"),
                    "times_ranked": entry.get("lineage", {}).get("times_ranked", 0),
                }
    return {}


def build_operations(
    approved_ids: list[str],
    experiment_designs: list,
    pipeline_context: str,
    audit_log_path: str,
    history_path: str,
    config: dict,
    findings_md: str | None,
    cycle_date: str,
) -> list[dict]:
    """
    Return a list of Jira operations (create / comment / link) for Agent 13 to execute.
    Does NOT call any MCP tool — fully deterministic.
    """
    ga = config.get("growth_agent", {})
    project_key = ga.get("jira_project_key", "BAAPP")
    epic_key = ga.get("epic_key", "")
    story_labels = ga.get("story_labels", ["growth-agent"])
    backlog_label = ga.get("backlog_label", "growth-backlog")

    if not project_key:
        print(json.dumps({"error": "jira_project_key not set in config", "exit_code": 2}))
        sys.exit(2)
    if not epic_key:
        print(json.dumps({"error": "epic_key not set in config", "exit_code": 2}))
        sys.exit(2)

    ops = []
    skipped = []

    exp_by_id = {e["hypothesis_id"]: e for e in experiment_designs}

    for hid in approved_ids:
        exp = exp_by_id.get(hid)
        if not exp:
            skipped.append({"hypothesis_id": hid, "reason": "not found in experiment-designs.json"})
            continue

        # Repo name — comes from the primary verified file's repo field, or falls back to project_key
        verified_files = load_verified_files(exp, audit_log_path)
        repo_name = verified_files[0]["repo"] if verified_files else project_key

        sp = exp.get("sp_estimate", 99)
        sprint_viable = isinstance(sp, int) and sp <= 3
        story_type = "quick_win" if sprint_viable else "backlog"
        base_labels = story_labels if sprint_viable else [backlog_label]
        dedup_label = make_dedup_label(project_key, hid)
        labels = base_labels + [dedup_label]

        action_title = exp.get("action_title") or exp.get("hypothesis", "")[:60]
        summary = build_summary(repo_name, action_title)
        description = build_description(exp, pipeline_context, verified_files, findings_md)

        lineage = load_lineage(history_path, hid)
        prior_ticket = lineage.get("jira_ticket")
        times_ranked = lineage.get("times_ranked", 0)

        # Carry-forward: if prior open ticket exists, emit a comment op instead
        # Agent 13 will check status via jira_get_issue and decide
        if prior_ticket and times_ranked > 0:
            ops.append({
                "op": "check_and_comment_or_create",
                "hypothesis_id": hid,
                "story_type": story_type,
                "prior_ticket": prior_ticket,
                "comment_body": (
                    f"Cycle update ({cycle_date}): This hypothesis surfaced again this cycle. "
                    f"New evidence from code review: {exp.get('confidence_reason', '')}. "
                    f"Root cause assessment unchanged. Priority score: {exp.get('priority_score', '?')}/27."
                ),
                "create_payload": _create_payload(
                    project_key, summary, description, labels, epic_key, prior_ticket
                ),
            })
        else:
            ops.append({
                "op": "create",
                "hypothesis_id": hid,
                "story_type": story_type,
                "summary": summary,
                # Exact-match label search — reliable dedup even on re-runs with same hypothesis ID
                "dedup_search_labels": dedup_label,
                "dedup_search_jql": f'project = {project_key} AND labels = "{dedup_label}" AND status not in (Done, Closed) ORDER BY created DESC',
                "create_payload": _create_payload(
                    project_key, summary, description, labels, epic_key, None
                ),
            })

    return {"operations": ops, "skipped": skipped}


def _create_payload(project_key, summary, description, labels, epic_key, prior_ticket):
    payload = {
        "project_key": project_key,
        "issue_type": "Story",
        "summary": summary,
        "description": description,
        "additional_fields": {
            "labels": labels,
            "epicKey": epic_key,
        },
    }
    if prior_ticket:
        payload["description"] += f"\n\n## Prior Ticket\n{prior_ticket}"
    return payload


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------

def write_output_log(results: list, output_path: str, cycle_date: str, config: dict) -> None:
    ga = config.get("growth_agent", {})
    lines = [
        f"# Jira Tickets Created — {cycle_date}",
        f"Epic: {ga.get('epic_key', '')} | Project: {ga.get('jira_project_key', '')} | Cycle: {cycle_date[:7]}",
        "",
        "## Quick Win Stories",
        "| Key | Summary | SP | Hypothesis | Confidence | Score |",
        "|---|---|---|---|---|---|",
    ]
    quick_wins = [r for r in results if r.get("story_type") == "quick_win" and r.get("key")]
    for r in quick_wins:
        lines.append(f"| {r['key']} | {r['summary']} | {r.get('sp','')} | {r['hypothesis_id']} | {r.get('confidence','')} | {r.get('score','')} |")

    lines += ["", "## Backlog Stories", "| Key | Summary | SP | Hypothesis | Confidence | Score |", "|---|---|---|---|---|---|"]
    backlog = [r for r in results if r.get("story_type") == "backlog" and r.get("key")]
    for r in backlog:
        lines.append(f"| {r['key']} | {r['summary']} | {r.get('sp','')} | {r['hypothesis_id']} | {r.get('confidence','')} | {r.get('score','')} |")

    lines += ["", "## Deferred / Skipped", "| Hypothesis | Reason |", "|---|---|"]
    for r in results:
        if not r.get("key"):
            lines.append(f"| {r['hypothesis_id']} | {r.get('reason','no ticket created')} |")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build Jira story operation payloads for Agent 13")
    parser.add_argument("--approved-ids", nargs="+", required=True, help="Hypothesis IDs approved by PM")
    parser.add_argument("--experiment-designs", default="outputs/validation/experiment-designs.json")
    parser.add_argument("--pipeline-context", default="outputs/signal-agent/pipeline-context.md")
    parser.add_argument("--audit-log", default="outputs/validation/read-audit.log")
    parser.add_argument("--history", default="outputs/prioritisation/ranked-hypotheses.json")
    parser.add_argument("--findings", default="outputs/feedback/findings.md")
    parser.add_argument("--output-log", default="outputs/jira-writer/created-tickets.md")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads only — no ticket creation")
    args = parser.parse_args()

    # Validate required inputs
    for path, label in [
        (args.experiment_designs, "experiment-designs.json"),
        (args.audit_log, "read-audit.log"),
    ]:
        if not Path(path).exists():
            print(json.dumps({"error": f"{label} not found at {path}", "exit_code": 3}))
            sys.exit(3)

    config = resolve_config()
    experiment_designs = load_json(args.experiment_designs) or []
    pipeline_context = load_text(args.pipeline_context) or ""
    findings_md = load_text(args.findings)
    cycle_date = datetime.today().strftime("%Y-%m-%d")

    result = build_operations(
        approved_ids=args.approved_ids,
        experiment_designs=experiment_designs if isinstance(experiment_designs, list) else experiment_designs.get("experiments", []),
        pipeline_context=pipeline_context,
        audit_log_path=args.audit_log,
        history_path=args.history,
        config=config,
        findings_md=findings_md,
        cycle_date=cycle_date,
    )

    if args.dry_run:
        print("=== DRY RUN — no Jira tickets will be created ===")
        print(json.dumps(result, indent=2))
        return

    # In live mode: output JSON for Agent 13 to consume and execute via MCP
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
