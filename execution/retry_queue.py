#!/usr/bin/env python3
"""
retry_queue.py — Dead-letter queue for failed Domo / MCP source queries.

When a data source query fails during an agent run, the agent calls this script
to record the failure. A subsequent run (or a manual retry) can call --list-pending
to see what needs to be retried, and --resolve to mark items resolved.

Queue file: .tmp/retry-queue.json
Format: JSON array of failure entries.

Usage:
  # Record a failure (called by agent on Domo/MCP error):
  python execution/retry_queue.py --write-failure \
    --source-id 29a01e0e \
    --source-name "Domain KPI by Session" \
    --agent 10-signal-agent \
    --step "Step 3" \
    --error "Domo query timeout after 30s"

  # List all pending items (items not yet resolved):
  python execution/retry_queue.py --list-pending

  # Mark an item resolved by source-id + agent (use after successful retry):
  python execution/retry_queue.py --resolve \
    --source-id 29a01e0e \
    --agent 10-signal-agent

  # Clear all resolved items (housekeeping):
  python execution/retry_queue.py --clear-resolved

Exit codes:
  0  success
  1  queue file corrupted (invalid JSON)
  2  required argument missing
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

QUEUE_PATH = Path(".tmp/retry-queue.json")


def _load_queue() -> list:
    if not QUEUE_PATH.exists():
        return []
    try:
        return json.loads(QUEUE_PATH.read_text()) or []
    except json.JSONDecodeError as e:
        print(f"ERROR: retry-queue.json is corrupted: {e}", file=sys.stderr)
        sys.exit(1)


def _save_queue(queue: list) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(queue, indent=2))


def write_failure(source_id: str, source_name: str, agent: str, step: str, error: str) -> None:
    queue = _load_queue()
    entry = {
        "queued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M"),
        "source_id": source_id,
        "source_name": source_name,
        "agent": agent,
        "step": step,
        "error": error,
        "status": "pending",
        "retry_count": 0,
        "last_retry_at": None,
    }
    queue.append(entry)
    _save_queue(queue)
    print(json.dumps({"written": True, "entry": entry}))


def list_pending() -> None:
    queue = _load_queue()
    pending = [e for e in queue if e.get("status") == "pending"]
    print(json.dumps({"pending_count": len(pending), "items": pending}, indent=2))


def resolve(source_id: str, agent: str) -> None:
    queue = _load_queue()
    resolved_count = 0
    for entry in queue:
        if entry.get("source_id") == source_id and entry.get("agent") == agent and entry.get("status") == "pending":
            entry["status"] = "resolved"
            entry["last_retry_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
            resolved_count += 1
    _save_queue(queue)
    print(json.dumps({"resolved": resolved_count}))


def clear_resolved() -> None:
    queue = _load_queue()
    before = len(queue)
    queue = [e for e in queue if e.get("status") != "resolved"]
    _save_queue(queue)
    print(json.dumps({"removed": before - len(queue), "remaining": len(queue)}))


def main():
    parser = argparse.ArgumentParser(description="Dead-letter queue for failed data source queries")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-failure", action="store_true", help="Record a new failure")
    group.add_argument("--list-pending", action="store_true", help="List all pending (unresolved) failures")
    group.add_argument("--resolve", action="store_true", help="Mark a failure as resolved")
    group.add_argument("--clear-resolved", action="store_true", help="Remove all resolved entries from queue")

    parser.add_argument("--source-id", help="Dataset or card ID that failed")
    parser.add_argument("--source-name", help="Human-readable source name")
    parser.add_argument("--agent", help="Agent that encountered the failure (e.g. 10-signal-agent)")
    parser.add_argument("--step", help="Step label where failure occurred (e.g. 'Step 3')")
    parser.add_argument("--error", help="Error message or exception string")

    args = parser.parse_args()

    if args.write_failure:
        for required in ["source_id", "source_name", "agent", "step", "error"]:
            if not getattr(args, required):
                print(f"ERROR: --{required.replace('_', '-')} is required for --write-failure", file=sys.stderr)
                sys.exit(2)
        write_failure(args.source_id, args.source_name, args.agent, args.step, args.error)

    elif args.list_pending:
        list_pending()

    elif args.resolve:
        for required in ["source_id", "agent"]:
            if not getattr(args, required):
                print(f"ERROR: --{required.replace('_', '-')} is required for --resolve", file=sys.stderr)
                sys.exit(2)
        resolve(args.source_id, args.agent)

    elif args.clear_resolved:
        clear_resolved()


if __name__ == "__main__":
    main()
