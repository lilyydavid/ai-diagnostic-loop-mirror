#!/usr/bin/env python3
"""Verify code grounding: check experiment file paths against read-audit.log and grep for anchors.

Mandatory hard block before any Jira story creation (Agent 13 Step 5a, NFR13, NFR14).

Usage:
    python execution/verify_code_grounding.py \
        --designs outputs/validation/experiment-designs.json \
        --audit-log outputs/validation/read-audit.log \
        --repos-cfg config/atlassian.yml \
        --output .tmp/grounding-report.json
"""

import argparse
import json
import os
import re
import subprocess
import sys

import yaml


def load_audit_log(path: str) -> set:
    """Parse read-audit.log and extract all file paths that were read."""
    if not os.path.exists(path):
        return set()
    paths = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Audit log lines may be: "READ path" or just "path"
            parts = line.split(None, 1)
            if len(parts) == 2 and parts[0].upper() == "READ":
                paths.add(parts[1])
            elif len(parts) >= 1:
                # Accept any line that looks like a file path
                candidate = parts[-1]
                if "/" in candidate or "." in candidate:
                    paths.add(candidate)
    return paths


def load_repo_paths(config_path: str) -> dict:
    """Load validation.repos from atlassian.yml to get local paths."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    repos = config.get("validation", {}).get("repos", [])
    return {r["name"]: r.get("local_path", "") for r in repos if "name" in r}


def grep_anchor(anchor: str, file_path: str, repo_paths: dict) -> bool:
    """Grep for anchor string in the file. Returns True if found."""
    # Try to resolve full path via repo_paths
    for repo_name, local_path in repo_paths.items():
        if not local_path:
            continue
        full_path = os.path.join(local_path, file_path)
        if os.path.exists(full_path):
            try:
                result = subprocess.run(
                    ["grep", "-q", "-F", anchor, full_path],
                    capture_output=True, timeout=10
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, OSError):
                return False

    # If no repo path matched, try the path directly (might be absolute)
    if os.path.exists(file_path):
        try:
            result = subprocess.run(
                ["grep", "-q", "-F", anchor, file_path],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    return False


def verify_entry(entry: dict, audited_paths: set, repo_paths: dict) -> dict:
    """Verify code grounding for a single experiment-designs entry."""
    failure_id = entry.get("hypothesis_id") or entry.get("failure_id") or entry.get("id", "?")
    confidence = (entry.get("confidence") or "").lower()
    code_evidence = entry.get("code_evidence", {})
    files = code_evidence.get("files", [])

    verified_files = []
    unverified_files = []
    anchor_results = []
    all_anchors_ok = True

    for file_entry in files:
        path = file_entry.get("path", "")
        anchor = file_entry.get("grep_anchor")

        # Check 1: path in audit log
        # Try exact match, then suffix match (audit log might have full paths)
        path_verified = path in audited_paths
        if not path_verified:
            path_verified = any(ap.endswith(path) or path.endswith(ap) for ap in audited_paths)

        if path_verified:
            verified_files.append(path)
            # Check 2: grep anchor (only on verified files with an anchor)
            if anchor:
                anchor_ok = grep_anchor(anchor, path, repo_paths)
                anchor_results.append({"path": path, "anchor": anchor, "confirmed": anchor_ok})
                if not anchor_ok:
                    all_anchors_ok = False
            else:
                anchor_results.append({"path": path, "anchor": None, "confirmed": None})
        else:
            unverified_files.append(path)

    # Classify
    blocked = False
    block_reason = None

    if confidence == "low":
        blocked = True
        block_reason = "confidence is Low — requires spike"
    elif len(verified_files) == 0 and len(files) > 0:
        blocked = True
        block_reason = "no files verified against audit log"
    elif not all_anchors_ok and all(not r["confirmed"] for r in anchor_results if r["anchor"]):
        blocked = True
        block_reason = "all grep_anchors failed re-verification"

    if len(verified_files) == 0 and len(files) == 0:
        grounded = "no_files"
    elif blocked:
        grounded = "false"
    elif all_anchors_ok and len(unverified_files) == 0:
        grounded = "true"
    else:
        grounded = "partial"

    return {
        "failure_id": str(failure_id),
        "grounded": grounded,
        "blocked": blocked,
        "block_reason": block_reason,
        "verified_files": verified_files,
        "unverified_files": unverified_files,
        "anchor_results": anchor_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify code grounding for experiment designs")
    parser.add_argument("--designs", required=True, help="Path to experiment-designs.json")
    parser.add_argument("--audit-log", required=True, help="Path to read-audit.log")
    parser.add_argument("--repos-cfg", default="config/atlassian.yml", help="Path to atlassian.yml (for repo local paths)")
    parser.add_argument("--output", required=True, help="Path to write grounding report JSON")
    args = parser.parse_args()

    if not os.path.exists(args.designs):
        print(f"ERROR: designs file not found: {args.designs}", file=sys.stderr)
        sys.exit(1)

    audit_log_present = os.path.exists(args.audit_log)
    audited_paths = load_audit_log(args.audit_log) if audit_log_present else set()
    repo_paths = load_repo_paths(args.repos_cfg)

    with open(args.designs) as f:
        data = json.load(f)
    entries = data.get("entries", data if isinstance(data, list) else [])

    # If audit log is missing, hard block everything
    if not audit_log_present:
        results = [{
            "failure_id": str(e.get("hypothesis_id") or e.get("failure_id") or e.get("id", "?")),
            "grounded": "false",
            "blocked": True,
            "block_reason": "read-audit.log missing — cannot verify code grounding",
            "verified_files": [],
            "unverified_files": [f.get("path", "") for f in e.get("code_evidence", {}).get("files", [])],
            "anchor_results": [],
        } for e in entries]
    else:
        results = [verify_entry(e, audited_paths, repo_paths) for e in entries]

    blocked_ids = [r["failure_id"] for r in results if r["blocked"]]
    sprint_viable_ids = [r["failure_id"] for r in results if not r["blocked"]]

    report = {
        "audit_log_present": audit_log_present,
        "audited_paths_count": len(audited_paths),
        "entries": results,
        "blocked_ids": blocked_ids,
        "sprint_viable_ids": sprint_viable_ids,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Code grounding report → {args.output}")
    print(f"  Audit log: {'present' if audit_log_present else 'MISSING'} ({len(audited_paths)} paths)")
    print(f"  Entries: {len(results)} total, {len(sprint_viable_ids)} grounded, {len(blocked_ids)} blocked")
    for r in results:
        status = "BLOCKED" if r["blocked"] else "OK"
        reason = f" — {r['block_reason']}" if r["blocked"] else ""
        print(f"  {r['failure_id']}: {status} (grounded={r['grounded']}){reason}")


if __name__ == "__main__":
    main()
