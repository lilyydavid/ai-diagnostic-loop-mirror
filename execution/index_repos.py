#!/usr/bin/env python3
"""Build a lightweight structural index of registered repos.

Walks local repo clones, extracts file-level metadata (exports, path keywords, line counts).
Agents 08 and 12 read the index to narrow file search before doing targeted reads.

Usage:
    python execution/index_repos.py --repos-cfg config/repos.yml --local-cfg config/repos.local.yml --output .tmp/repo-index.json
    python execution/index_repos.py --repos-cfg config/repos.yml --local-cfg config/repos.local.yml --output .tmp/repo-index.json --extensions .ts,.tsx,.jsx,.rb --max-depth 4
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

import yaml


# ── File extension defaults ──────────────────────────────────────────────────

DEFAULT_EXTENSIONS = {".ts", ".tsx", ".jsx", ".js", ".rb", ".py"}

SKIP_DIRS = {
    "node_modules", "dist", "build", ".git", "vendor", "__pycache__",
    ".next", ".nuxt", "coverage", ".cache", "tmp", "log", "logs",
}

# ── Export extraction patterns (simple regex, not AST) ───────────────────────

PATTERNS = {
    ".ts":  [
        r"export\s+(?:default\s+)?(?:function|class|const|let|var|interface|type|enum)\s+(\w+)",
        r"export\s+\{([^}]+)\}",
    ],
    ".tsx": None,  # same as .ts
    ".jsx": None,  # same as .js
    ".js":  [
        r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)",
        r"export\s+\{([^}]+)\}",
        r"module\.exports\s*=\s*\{([^}]+)\}",
        r"module\.exports\s*=\s*(\w+)",
    ],
    ".rb":  [
        r"^\s*def\s+(\w+)",
        r"^\s*class\s+(\w+)",
        r"^\s*module\s+(\w+)",
    ],
    ".py":  [
        r"^\s*def\s+(\w+)",
        r"^\s*class\s+(\w+)",
    ],
}

# .tsx uses .ts patterns, .jsx uses .js patterns
PATTERNS[".tsx"] = PATTERNS[".ts"]
PATTERNS[".jsx"] = PATTERNS[".js"]


def extract_exports(file_path: str, ext: str) -> list[str]:
    """Extract exported/defined names from a file using regex."""
    patterns = PATTERNS.get(ext)
    if not patterns:
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    names = []
    for pattern in patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            group = match.group(1)
            # Handle "export { Foo, Bar, Baz }" style
            if "," in group:
                names.extend(n.strip().split(" ")[0] for n in group.split(",") if n.strip())
            else:
                name = group.strip()
                if name and not name.startswith("_"):
                    names.append(name)

    return sorted(set(names))


def extract_path_keywords(rel_path: str) -> list[str]:
    """Extract meaningful keywords from path segments."""
    parts = rel_path.replace("\\", "/").split("/")
    keywords = []
    skip_segments = {"src", "app", "lib", "components", "pages", "views", "controllers", "models", "services", "utils", "helpers", "test", "tests", "spec", "specs", "__tests__"}
    for part in parts:
        name = os.path.splitext(part)[0].lower()
        # Split camelCase and PascalCase
        tokens = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).lower().split()
        # Also split on - and _
        for token in tokens:
            for sub in re.split(r"[-_]", token):
                if sub and sub not in skip_segments and len(sub) > 2:
                    keywords.append(sub)
    return sorted(set(keywords))


def count_lines(file_path: str) -> int:
    try:
        with open(file_path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def walk_repo(root: str, extensions: set, max_depth: int) -> list[dict]:
    """Walk a repo directory and collect file metadata."""
    files = []
    root = os.path.abspath(root)

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        # Check depth
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if depth > max_depth:
            dirnames.clear()
            continue

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in extensions:
                continue

            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root)

            exports = extract_exports(full_path, ext)
            path_keywords = extract_path_keywords(rel_path)
            lines = count_lines(full_path)
            mtime = os.path.getmtime(full_path)

            files.append({
                "path": rel_path,
                "exports": exports,
                "path_keywords": path_keywords,
                "last_modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lines": lines,
            })

    return files


def main():
    parser = argparse.ArgumentParser(description="Index registered repos for agent search optimisation")
    parser.add_argument("--repos-cfg", required=True, help="Path to config/repos.yml")
    parser.add_argument("--local-cfg", default=None, help="Path to config/repos.local.yml")
    parser.add_argument("--output", required=True, help="Output path for repo-index.json")
    parser.add_argument("--extensions", default=None, help="Comma-separated file extensions (e.g. .ts,.tsx,.rb)")
    parser.add_argument("--max-depth", type=int, default=5, help="Max directory depth (default 5)")
    args = parser.parse_args()

    if not os.path.exists(args.repos_cfg):
        print(f"ERROR: repos config not found: {args.repos_cfg}", file=sys.stderr)
        sys.exit(1)

    # Parse extensions
    extensions = DEFAULT_EXTENSIONS
    if args.extensions:
        extensions = set(e.strip() if e.strip().startswith(".") else f".{e.strip()}" for e in args.extensions.split(","))

    # Load repo metadata
    with open(args.repos_cfg) as f:
        repos_cfg = yaml.safe_load(f) or {}
    repos = repos_cfg.get("repos", [])

    # Load local paths
    local_paths = {}
    if args.local_cfg and os.path.exists(args.local_cfg):
        with open(args.local_cfg) as f:
            local_cfg = yaml.safe_load(f) or {}
        if isinstance(local_cfg, dict):
            # Handle nested "repos:" key or flat {repo_name: path} format
            data = local_cfg.get("repos", local_cfg)
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, str):
                        local_paths[key] = val
                    elif isinstance(val, dict):
                        local_paths[key] = val.get("local_path", "")

    # Index each repo
    index = []
    total_indexed = 0

    for repo in repos:
        name = repo.get("name", "")
        local_path = local_paths.get(name, "")

        if not local_path or not os.path.isdir(local_path):
            print(f"  SKIP {name} — no local path or directory not found", file=sys.stderr)
            index.append({
                "repo": name,
                "type": repo.get("type", ""),
                "keywords": repo.get("keywords", []),
                "indexed_at": None,
                "files": [],
                "total_files": 0,
                "indexed_files": 0,
                "status": "skipped",
                "reason": "no local path" if not local_path else f"directory not found: {local_path}",
            })
            continue

        print(f"  Indexing {name} ({local_path}) ...", file=sys.stderr)
        files = walk_repo(local_path, extensions, args.max_depth)

        repo_entry = {
            "repo": name,
            "type": repo.get("type", ""),
            "keywords": repo.get("keywords", []),
            "indexed_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "files": files,
            "total_files": sum(1 for _ in os.walk(local_path) for _ in _[2]) if os.path.isdir(local_path) else 0,
            "indexed_files": len(files),
            "status": "indexed",
        }
        index.append(repo_entry)
        total_indexed += len(files)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nRepo index → {args.output}")
    print(f"  Repos: {len(repos)} registered, {sum(1 for r in index if r.get('status') == 'indexed')} indexed")
    print(f"  Files indexed: {total_indexed}")


if __name__ == "__main__":
    main()
