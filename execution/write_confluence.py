#!/usr/bin/env python3
"""Write or update a Confluence page via the Atlassian REST API.

Reads credentials from .mcp.json (atlassian server entry).
Reads write targets from config/atlassian.yml (resolved through team/local overrides).

Usage:
    # Create a new page under a parent
    python execution/write_confluence.py \\
        --mode create \\
        --space PI \\
        --parent-id 64742785027 \\
        --title "Intelligence Loop — 2026-04-05" \\
        --body-file .tmp/confluence-body.md \\
        --content-format wiki

    # Update an existing page (overwrites)
    python execution/write_confluence.py \\
        --mode update \\
        --page-id 64760119298 \\
        --title "Cross references" \\
        --body-file .tmp/confluence-body.md \\
        --content-format wiki

    # Create or update: create if title absent under parent, update if found
    python execution/write_confluence.py \\
        --mode upsert \\
        --space PI \\
        --parent-id 64759660546 \\
        --title "Sephora Pulse — 2026-04-05" \\
        --body-file .tmp/confluence-body.md \\
        --content-format wiki

Output (stdout, JSON):
    {"status": "created"|"updated"|"skipped", "page_id": "...", "url": "..."}

Exit codes:
    0  success
    1  auth error (401/403) — rotate token
    2  bad request (400) — check title/space/parent
    3  input error — missing args or files
    4  config error — credentials or config not found
"""

import argparse
import json
import os
import sys
import base64
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(4)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(4)


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_mcp_credentials(mcp_path: str = ".mcp.json") -> dict:
    """Extract Atlassian credentials from .mcp.json."""
    if not os.path.exists(mcp_path):
        print(f"ERROR: {mcp_path} not found. Add Atlassian credentials.", file=sys.stderr)
        sys.exit(4)
    with open(mcp_path) as f:
        mcp = json.load(f)
    # Support both mcpServers and servers key layouts
    servers = mcp.get("mcpServers", mcp.get("servers", {}))
    atlassian = servers.get("mcp-atlassian", servers.get("atlassian", {}))
    env = atlassian.get("env", {})
    url = env.get("CONFLUENCE_URL", "")
    username = env.get("CONFLUENCE_USERNAME", "")
    token = env.get("CONFLUENCE_API_TOKEN", "")
    if not all([url, username, token]):
        print("ERROR: Missing CONFLUENCE_URL, CONFLUENCE_USERNAME, or CONFLUENCE_API_TOKEN in .mcp.json", file=sys.stderr)
        sys.exit(4)
    return {"url": url.rstrip("/"), "username": username, "token": token}


def make_auth_header(username: str, token: str) -> dict:
    creds = base64.b64encode(f"{username}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ---------------------------------------------------------------------------
# Confluence REST helpers
# ---------------------------------------------------------------------------

def get_page_by_title(base_url: str, headers: dict, space_key: str, title: str, parent_id: str = None) -> dict | None:
    """Return page dict if a page with this title exists in space, else None."""
    params = {"spaceKey": space_key, "title": title, "expand": "version"}
    r = requests.get(f"{base_url}/rest/api/content", headers=headers, params=params)
    if r.status_code == 401:
        print("ERROR: 401 Unauthorized. Rotate your Atlassian API token.", file=sys.stderr)
        sys.exit(1)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    if parent_id:
        # Filter to pages under the specified parent
        for page in results:
            ancestors = page.get("ancestors", [])
            if any(str(a.get("id")) == str(parent_id) for a in ancestors):
                return page
        # If parent filter yields nothing, fall back to first result
    return results[0]


def get_page_version(base_url: str, headers: dict, page_id: str) -> int:
    """Get the current version number of a page."""
    r = requests.get(f"{base_url}/rest/api/content/{page_id}?expand=version", headers=headers)
    if r.status_code == 401:
        print("ERROR: 401 Unauthorized. Rotate your Atlassian API token.", file=sys.stderr)
        sys.exit(1)
    r.raise_for_status()
    return r.json()["version"]["number"]


def create_page(base_url: str, headers: dict, space_key: str, parent_id: str, title: str, body: str, content_format: str) -> dict:
    """Create a new Confluence page. Returns {page_id, url}."""
    storage_format = "storage" if content_format == "wiki" else content_format
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {storage_format: {"value": body, "representation": storage_format}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    r = requests.post(f"{base_url}/rest/api/content", headers=headers, json=payload)
    if r.status_code == 401:
        print("ERROR: 401 Unauthorized. Rotate your Atlassian API token.", file=sys.stderr)
        sys.exit(1)
    if r.status_code == 400:
        print(f"ERROR: 400 Bad Request — {r.text}", file=sys.stderr)
        sys.exit(2)
    r.raise_for_status()
    data = r.json()
    page_id = data["id"]
    url = f"{base_url}/wiki/spaces/{space_key}/pages/{page_id}"
    return {"page_id": page_id, "url": url}


def update_page(base_url: str, headers: dict, page_id: str, title: str, body: str, content_format: str, space_key: str = None) -> dict:
    """Update an existing Confluence page. Returns {page_id, url}."""
    version = get_page_version(base_url, headers, page_id)
    storage_format = "storage" if content_format == "wiki" else content_format
    payload = {
        "type": "page",
        "title": title,
        "version": {"number": version + 1},
        "body": {storage_format: {"value": body, "representation": storage_format}},
    }
    r = requests.put(f"{base_url}/rest/api/content/{page_id}", headers=headers, json=payload)
    if r.status_code == 401:
        print("ERROR: 401 Unauthorized. Rotate your Atlassian API token.", file=sys.stderr)
        sys.exit(1)
    if r.status_code == 400:
        print(f"ERROR: 400 Bad Request — {r.text}", file=sys.stderr)
        sys.exit(2)
    r.raise_for_status()
    data = r.json()
    sk = space_key or data.get("space", {}).get("key", "PI")
    url = f"{base_url}/wiki/spaces/{sk}/pages/{page_id}"
    return {"page_id": page_id, "url": url}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Write a Confluence page via REST API.")
    parser.add_argument("--mode", choices=["create", "update", "upsert"], required=True,
                        help="create: always create new | update: update existing page-id | upsert: create-or-update by title")
    parser.add_argument("--space", help="Confluence space key (e.g. PI). Required for create/upsert.")
    parser.add_argument("--parent-id", help="Parent page ID. Required for create/upsert.")
    parser.add_argument("--page-id", help="Existing page ID to update. Required for update mode.")
    parser.add_argument("--title", required=True, help="Page title.")
    parser.add_argument("--body-file", required=True, help="Path to file containing the page body.")
    parser.add_argument("--content-format", default="wiki", choices=["wiki", "storage", "markdown"],
                        help="Body format: wiki (Confluence wiki markup), storage (XHTML), markdown.")
    parser.add_argument("--mcp", default=".mcp.json", help="Path to .mcp.json credentials file.")
    args = parser.parse_args()

    # Validate inputs
    if args.mode in ("create", "upsert") and not args.space:
        print("ERROR: --space required for create/upsert mode.", file=sys.stderr)
        sys.exit(3)
    if args.mode == "update" and not args.page_id:
        print("ERROR: --page-id required for update mode.", file=sys.stderr)
        sys.exit(3)
    if not os.path.exists(args.body_file):
        print(f"ERROR: body file not found: {args.body_file}", file=sys.stderr)
        sys.exit(3)

    with open(args.body_file, encoding="utf-8") as f:
        body = f.read()

    creds = load_mcp_credentials(args.mcp)
    headers = make_auth_header(creds["username"], creds["token"])
    base_url = creds["url"]

    if args.mode == "create":
        result = create_page(base_url, headers, args.space, args.parent_id, args.title, body, args.content_format)
        print(json.dumps({"status": "created", **result}))

    elif args.mode == "update":
        result = update_page(base_url, headers, args.page_id, args.title, body, args.content_format, args.space)
        print(json.dumps({"status": "updated", **result}))

    elif args.mode == "upsert":
        existing = get_page_by_title(base_url, headers, args.space, args.title, args.parent_id)
        if existing:
            page_id = existing["id"]
            result = update_page(base_url, headers, page_id, args.title, body, args.content_format, args.space)
            print(json.dumps({"status": "updated", **result}))
        else:
            result = create_page(base_url, headers, args.space, args.parent_id, args.title, body, args.content_format)
            print(json.dumps({"status": "created", **result}))


if __name__ == "__main__":
    main()
