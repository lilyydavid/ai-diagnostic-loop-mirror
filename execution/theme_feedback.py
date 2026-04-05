#!/usr/bin/env python3
"""Cluster verbatim feedback into themes using keyword frequency and co-occurrence.

Deterministic: same input → same output. No LLM calls.

Usage:
    python execution/theme_feedback.py \
      --verbatims '[{"text": "checkout broken", "market": "AU", "platform": "iOS", "date": "2026-04-01"}, ...]' \
      --max-themes 5 \
      --output .tmp/themes.json

    # Or pipe verbatims from a file:
    python execution/theme_feedback.py --verbatims-file .tmp/verbatims.json --max-themes 5

Output JSON:
    {
      "themes": [
        {
          "label": "checkout_friction",
          "keywords": ["checkout", "payment", "failed"],
          "verbatim_count": 12,
          "market_breakdown": {"AU": 8, "SG": 4},
          "platform_breakdown": {"iOS": 10, "Android": 2},
          "representative_quotes": [
            {"text": "...", "market": "AU", "platform": "iOS", "date": "2026-04-01"}
          ]
        }
      ],
      "total_verbatims": 40,
      "themes_found": 3,
      "unclustered_count": 5
    }
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict


# Keyword → theme label mapping. Ordered: first match wins.
THEME_KEYWORDS = [
    ("checkout_friction", ["checkout", "payment", "pay", "order", "purchase", "confirm"]),
    ("atc_issues", ["add to cart", "add-to-cart", "atc", "cart", "basket", "add item"]),
    ("app_performance", ["crash", "slow", "freeze", "lag", "loading", "load", "hang", "error"]),
    ("promo_voucher", ["promo", "voucher", "discount", "code", "coupon", "gift", "free gift"]),
    ("login_auth", ["login", "sign in", "sign-in", "log in", "password", "otp", "verify"]),
    ("delivery_shipping", ["delivery", "shipping", "ship", "arrive", "tracking", "dispatch"]),
    ("search_discovery", ["search", "find", "filter", "browse", "category", "result"]),
    ("loyalty_rewards", ["points", "rewards", "loyalty", "tier", "redeem", "black", "gold"]),
    ("product_stock", ["stock", "out of stock", "oos", "unavailable", "sold out"]),
    ("cs_support", ["support", "customer service", "refund", "return", "exchange", "complaint"]),
]


def normalise(text: str) -> str:
    return text.lower().strip()


def classify_verbatim(text: str) -> str | None:
    """Return the first matching theme label, or None if unclustered."""
    norm = normalise(text)
    for label, keywords in THEME_KEYWORDS:
        for kw in keywords:
            if kw in norm:
                return label
    return None


def top_keywords(verbatims: list[str], n: int = 5) -> list[str]:
    """Extract top N meaningful words from a list of verbatims."""
    stopwords = {"the", "a", "an", "is", "it", "to", "and", "or", "but", "i", "my",
                 "this", "that", "was", "not", "can", "with", "for", "on", "in",
                 "of", "at", "be", "as", "by", "are", "have", "has", "had", "its"}
    words = []
    for text in verbatims:
        tokens = re.findall(r'\b[a-z]{3,}\b', normalise(text))
        words.extend(t for t in tokens if t not in stopwords)
    return [w for w, _ in Counter(words).most_common(n)]


def cluster(verbatim_entries: list[dict], max_themes: int) -> dict:
    """Cluster verbatim entries into themes."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    unclustered: list[dict] = []

    for entry in verbatim_entries:
        text = entry.get("text", "")
        label = classify_verbatim(text)
        if label:
            buckets[label].append(entry)
        else:
            unclustered.append(entry)

    # Sort buckets by verbatim count descending; respect max_themes
    sorted_labels = sorted(buckets.keys(), key=lambda l: len(buckets[l]), reverse=True)[:max_themes]

    themes = []
    for label in sorted_labels:
        entries = buckets[label]
        market_counts: Counter = Counter()
        platform_counts: Counter = Counter()
        for e in entries:
            if e.get("market"):
                market_counts[e["market"]] += 1
            if e.get("platform"):
                platform_counts[e["platform"]] += 1

        # Representative quotes: up to 3, prefer entries with shortest text (most signal-dense)
        sorted_entries = sorted(entries, key=lambda e: len(e.get("text", "")))
        rep_quotes = sorted_entries[:3]

        themes.append({
            "label": label,
            "keywords": top_keywords([e.get("text", "") for e in entries]),
            "verbatim_count": len(entries),
            "market_breakdown": dict(market_counts.most_common()),
            "platform_breakdown": dict(platform_counts.most_common()),
            "representative_quotes": [
                {k: v for k, v in e.items() if k in ("text", "market", "platform", "date")}
                for e in rep_quotes
            ],
        })

    # Overflow from truncated themes → unclustered
    for label in sorted(buckets.keys(), key=lambda l: len(buckets[l]), reverse=True)[max_themes:]:
        unclustered.extend(buckets[label])

    return {
        "themes": themes,
        "total_verbatims": len(verbatim_entries),
        "themes_found": len(themes),
        "unclustered_count": len(unclustered),
    }


def main():
    parser = argparse.ArgumentParser(description="Cluster verbatim feedback into themes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verbatims", help="JSON array of verbatim entries (inline)")
    group.add_argument("--verbatims-file", help="Path to JSON file containing verbatim array")
    parser.add_argument("--max-themes", type=int, default=5, help="Maximum number of themes (default: 5)")
    parser.add_argument("--output", default=None, help="Output file path (stdout if omitted)")
    args = parser.parse_args()

    # Load verbatims
    if args.verbatims:
        try:
            entries = json.loads(args.verbatims)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON in --verbatims: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not os.path.exists(args.verbatims_file):
            print(f"ERROR: file not found: {args.verbatims_file}", file=sys.stderr)
            sys.exit(1)
        with open(args.verbatims_file) as f:
            entries = json.load(f)

    if not isinstance(entries, list):
        print("ERROR: verbatims must be a JSON array", file=sys.stderr)
        sys.exit(1)

    result = cluster(entries, args.max_themes)
    output_str = json.dumps(result, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output_str + "\n")
    else:
        print(output_str)

    print(
        f"Clustered {result['total_verbatims']} verbatims into {result['themes_found']} themes "
        f"({result['unclustered_count']} unclustered)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
