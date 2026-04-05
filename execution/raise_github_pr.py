#!/usr/bin/env python3
"""
raise_github_pr.py — Layer 3 execution script for GitHub PR creation from a Jira ticket.

Trigger: PM adds a comment to a Jira ticket in the format:
  raise PR -> {repo-name}
  (case-insensitive, arrow variants: ->, →, =>)

What this script does:
  1. Fetch the Jira ticket (summary + description + comments)
  2. Parse PM's comment to find the target repo name
  3. Resolve the repo to a GitHub org/repo path via config/atlassian.yml (github.org)
     and config/repos.local.yml (local clone paths)
  4. Verify GitHub permissions (check write access to the repo)
  5. Build PR title and body from the Jira ticket
  6. Output a JSON operation payload for the agent to execute via mcp__github tools
     (same pattern as create_jira_stories.py — this script is deterministic;
      the agent executes the MCP calls)

Usage:
  python execution/raise_github_pr.py --ticket BAAPP-463

  # Dry run — print payload without agent execution
  python execution/raise_github_pr.py --ticket BAAPP-463 --dry-run

Output (stdout JSON):
  {
    "op": "create_pr" | "error",
    "ticket_key": "BAAPP-463",
    "repo": "sephora-asia/sea-web-app",
    "branch_name": "BAAPP-463-fix-payment-retry-402",
    "base_branch": "main",
    "pr_title": "[sea-web-app] Fix payment retry on 402 response",
    "pr_body": "...",           # full Jira description rendered as PR body
    "jira_link": "https://...", # for PR body footer
    "permissions_check": "write_confirmed" | "unknown" | "no_write"
  }

Exit codes:
  0  payload built successfully
  1  ticket not found or Jira fetch failed
  2  no "raise PR" comment found on the ticket
  3  repo name in comment does not match any known repo in config
  4  config error
  5  GitHub permissions cannot be confirmed (warn, not block)

Note on permissions:
  GitHub write access is checked via mcp__github__get_file_contents on a known
  path (README.md or package.json). A 403/404 on a known file indicates no write
  access; the agent surfaces this to the PM before creating the PR.
  This script outputs the check parameters; the agent performs the actual check.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Config resolution (same pattern as create_jira_stories.py)
# ---------------------------------------------------------------------------

def resolve_config() -> dict:
    try:
        import yaml
    except ImportError:
        print(json.dumps({"error": "PyYAML not installed. Run: pip install pyyaml", "exit_code": 4}))
        sys.exit(4)

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


def resolve_repos_local() -> dict:
    """Load config/repos.local.yml — maps repo short name to local clone path."""
    try:
        import yaml
    except ImportError:
        return {}
    p = Path("config/repos.local.yml")
    if not p.exists():
        return {}
    with open(p) as f:
        data = yaml.safe_load(f) or {}
    return data.get("repos", {})


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ---------------------------------------------------------------------------
# Comment parsing
# ---------------------------------------------------------------------------

# Matches: "raise PR -> sea-web-app", "raise pr => sea-web-app", "raise PR → sea-web-app"
_RAISE_PR_RE = re.compile(
    r"raise\s+pr\s*(?:->|=>|→)\s*([a-zA-Z0-9_.\-]+)",
    re.IGNORECASE,
)


def parse_raise_pr_comment(comments: list[dict]) -> str | None:
    """
    Scan comments (newest first preferred) for a 'raise PR -> {repo}' instruction.
    Returns the repo name string, or None if not found.
    """
    for comment in reversed(comments):  # newest last in Jira API; scan newest first
        body = comment.get("body", "")
        m = _RAISE_PR_RE.search(body)
        if m:
            return m.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Repo resolution
# ---------------------------------------------------------------------------

def resolve_repo(repo_name: str, config: dict, repos_local: dict) -> dict | None:
    """
    Match repo_name (from PM comment) against known repos in config.
    Returns {"short_name": str, "github_path": str, "local_path": str | None}
    or None if no match.

    Matching is case-insensitive and tolerates partial matches
    (e.g. "web-app" matches "sea-web-app").
    """
    org = config.get("github", {}).get("org", "")

    # Build candidate list from atlassian.yml github section
    all_repos = list(config.get("github", {}).get("always_read", []))
    conditional = config.get("github", {}).get("conditional", {})
    all_repos += list(conditional.values())

    # Also include any repo in repos.local.yml not already listed
    for name in repos_local:
        if name not in all_repos:
            all_repos.append(name)

    repo_name_lower = repo_name.lower()

    # Exact match first
    for r in all_repos:
        if r.lower() == repo_name_lower:
            return {
                "short_name": r,
                "github_path": f"{org}/{r}" if org else r,
                "local_path": repos_local.get(r),
            }

    # Partial / substring match
    for r in all_repos:
        if repo_name_lower in r.lower() or r.lower() in repo_name_lower:
            return {
                "short_name": r,
                "github_path": f"{org}/{r}" if org else r,
                "local_path": repos_local.get(r),
            }

    return None


# ---------------------------------------------------------------------------
# PR content assembly
# ---------------------------------------------------------------------------

def slug_from(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:max_len].rstrip("-")


def build_branch_name(ticket_key: str, summary: str) -> str:
    # Strip the [{repo}] prefix from summary if present
    clean = re.sub(r"^\[[^\]]+\]\s*", "", summary)
    return f"{ticket_key}-{slug_from(clean)}"


def build_pr_title(summary: str) -> str:
    """PR title = Jira summary verbatim (already contains [{repo}] prefix)."""
    return summary[:72]  # GitHub recommends ≤72 chars for PR title


def build_pr_body(ticket_key: str, summary: str, description: str, jira_url: str) -> str:
    """
    PR body = Jira description + footer linking back to the ticket.
    Sections already structured in Jira format (## headings) render fine in GitHub.
    """
    body = description.strip()
    body += f"\n\n---\n**Jira:** [{ticket_key} — {summary}]({jira_url})"
    return body


# ---------------------------------------------------------------------------
# Permissions check descriptor
# ---------------------------------------------------------------------------

def permissions_check_descriptor(github_path: str) -> dict:
    """
    Return a descriptor telling Agent 13 how to verify write access.
    The agent will call mcp__github__get_file_contents with these params.
    A successful read (any response) confirms API access; 403 = no access.
    """
    return {
        "tool": "mcp__github__get_file_contents",
        "params": {
            "owner": github_path.split("/")[0],
            "repo": github_path.split("/")[1],
            "path": "README.md",
        },
        "interpretation": {
            "success": "write_confirmed",  # repo accessible via MCP token
            "403": "no_write",
            "404": "no_write",
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build GitHub PR payload from a Jira ticket")
    parser.add_argument("--ticket", required=True, help="Jira ticket key, e.g. BAAPP-463")
    parser.add_argument("--base-branch", default="main", help="Target base branch for the PR")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = resolve_config()
    repos_local = resolve_repos_local()

    jira_base = "https://sephora-asia.atlassian.net"

    # This script outputs the operation payload.
    # Agent 13 must have already fetched the ticket details and passed them,
    # OR the agent calls this script after fetching — see integration note below.
    #
    # Integration pattern (Agent 13 step):
    #   1. Call mcp__mcp-atlassian__jira_get_issue(ticket_key) → ticket data
    #   2. Call mcp__mcp-atlassian__jira_get_comments(ticket_key) → comments
    #   3. Write ticket + comments to .tmp/jira-{ticket}.json
    #   4. python execution/raise_github_pr.py --ticket BAAPP-463 --ticket-data .tmp/jira-BAAPP-463.json
    #   5. Agent reads stdout JSON and executes the PR creation

    ticket_data_path = Path(f".tmp/jira-{args.ticket}.json")
    if not ticket_data_path.exists():
        # Emit an instruction for the agent to fetch first
        print(json.dumps({
            "op": "fetch_required",
            "ticket_key": args.ticket,
            "instruction": (
                f"Fetch the ticket and comments first, then write to .tmp/jira-{args.ticket}.json:\n"
                f"  1. mcp__mcp-atlassian__jira_get_issue(issue_key='{args.ticket}')\n"
                f"  2. mcp__mcp-atlassian__jira_get_comments(issue_key='{args.ticket}') "
                f"[or extract comments from jira_get_issue response]\n"
                f"  3. Write combined JSON to .tmp/jira-{args.ticket}.json\n"
                f"  4. Re-run: python execution/raise_github_pr.py --ticket {args.ticket}"
            ),
        }, indent=2))
        sys.exit(0)  # Not an error — just a pre-flight instruction

    with open(ticket_data_path) as f:
        ticket_data = json.load(f)

    summary = ticket_data.get("summary", "")
    description = ticket_data.get("description", "")
    comments = ticket_data.get("comments", [])
    ticket_url = ticket_data.get("url") or f"{jira_base}/browse/{args.ticket}"

    # Parse PM's raise-PR comment
    repo_name = parse_raise_pr_comment(comments)
    if not repo_name:
        print(json.dumps({
            "op": "error",
            "exit_code": 2,
            "ticket_key": args.ticket,
            "error": (
                f"No 'raise PR -> {{repo}}' comment found on {args.ticket}. "
                "Add a comment in the format: raise PR -> sea-web-app"
            ),
        }, indent=2))
        sys.exit(2)

    # Resolve repo
    repo = resolve_repo(repo_name, config, repos_local)
    if not repo:
        known = list(config.get("github", {}).get("always_read", []))
        known += list(config.get("github", {}).get("conditional", {}).values())
        known += list(repos_local.keys())
        print(json.dumps({
            "op": "error",
            "exit_code": 3,
            "ticket_key": args.ticket,
            "error": (
                f"Repo '{repo_name}' (from PM comment) does not match any known repo. "
                f"Known repos: {', '.join(sorted(set(known)))}. "
                "Add it to config/atlassian.yml github section or config/repos.local.yml."
            ),
        }, indent=2))
        sys.exit(3)

    branch_name = build_branch_name(args.ticket, summary)
    pr_title = build_pr_title(summary)
    pr_body = build_pr_body(args.ticket, summary, description, ticket_url)

    output = {
        "op": "create_pr",
        "ticket_key": args.ticket,
        "repo_short_name": repo["short_name"],
        "repo": repo["github_path"],
        "local_path": repo["local_path"],
        "branch_name": branch_name,
        "base_branch": args.base_branch,
        "pr_title": pr_title,
        "pr_body": pr_body,
        "jira_link": ticket_url,
        "permissions_check": permissions_check_descriptor(repo["github_path"]),
        "execution_steps": [
            {
                "step": 1,
                "description": "Verify GitHub access",
                "tool": "mcp__github__get_file_contents",
                "params": permissions_check_descriptor(repo["github_path"])["params"],
                "on_403": "Surface to PM: no GitHub write access for this repo via configured MCP token. Do not proceed.",
            },
            {
                "step": 2,
                "description": "Create branch",
                "tool": "mcp__github__create_branch",
                "params": {
                    "owner": repo["github_path"].split("/")[0],
                    "repo": repo["github_path"].split("/")[1],
                    "branch": branch_name,
                    "from_branch": args.base_branch,
                },
            },
            {
                "step": 3,
                "description": "Create pull request",
                "tool": "mcp__github__create_pull_request",
                "params": {
                    "owner": repo["github_path"].split("/")[0],
                    "repo": repo["github_path"].split("/")[1],
                    "title": pr_title,
                    "body": pr_body,
                    "head": branch_name,
                    "base": args.base_branch,
                    "draft": True,
                },
                "note": "Created as draft — PM or engineer promotes to ready when implementation is complete.",
            },
            {
                "step": 4,
                "description": "Comment PR link back to Jira ticket",
                "tool": "mcp__mcp-atlassian__jira_add_comment",
                "params": {
                    "issue_key": args.ticket,
                    "comment": f"PR raised: {{pr_url}} (draft — branch: `{branch_name}`, repo: `{repo['github_path']}`)",
                },
                "note": "Replace {pr_url} with the actual URL returned by step 3.",
            },
        ],
    }

    if args.dry_run:
        print("=== DRY RUN — no GitHub PR will be created ===")

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
