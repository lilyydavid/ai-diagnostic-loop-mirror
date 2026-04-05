#!/usr/bin/env python3
"""Calculate deterministic funnel tables for Agent 10.

Consumes pre-aggregated market rows and emits the `funnel_tables` structure used by
`execution/build_signal_report.py`.

Usage:
    python execution/calculate_funnel_tables.py \
        --input .tmp/funnel-input.json \
        --output .tmp/funnel-tables.json
"""

import argparse
import json
import os
import sys
from typing import Any


def load_input(input_path: str) -> dict[str, Any]:
    if input_path == "-":
        raw = sys.stdin.read()
    else:
        with open(input_path) as handle:
            raw = handle.read()

    if not raw.strip():
        raise ValueError("input is empty")

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    return data


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def safe_pct(numerator: Any, denominator: Any) -> float | None:
    num = to_float(numerator)
    den = to_float(denominator)
    if num is None or den is None or den == 0:
        return None
    return (num / den) * 100.0


def fmt_int(value: Any) -> str:
    numeric = to_float(value)
    if numeric is None:
        return "—"
    return f"{int(round(numeric)):,}"


def fmt_pct(value: Any) -> str:
    numeric = to_float(value)
    if numeric is None:
        return "—"
    return f"{numeric:.1f}%"


def session_funnel_tables(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows", [])
    if not rows:
        return []

    period_label = payload.get("period_label", "")
    missing_markets = payload.get("missing_markets", []) or []
    suspicious_web_markets = set(payload.get("suspicious_web_markets", []) or [])
    notes = list(payload.get("notes", []) or [])

    tables = []
    for device_type, title_prefix in [("App", "Table 1a — App Session Funnel"), ("Web", "Table 1b — Web Session Funnel")]:
        device_rows = []
        device_notes = []
        for row in rows:
            if str(row.get("device_type", "")).lower() != device_type.lower():
                continue
            journey = to_float(row.get("journey_sessions"))
            if journey is None or journey <= 0:
                continue

            market = str(row.get("country", ""))
            market_label = market
            if device_type == "Web" and market in suspicious_web_markets:
                market_label += " ⚠️"
                device_notes.append(f"⚠️ {market} web sessions are flagged as suspicious; funnel rates may be diluted by low-intent traffic.")

            device_rows.append({
                "market": market_label,
                "sessions": journey,
                "pdp_pct": safe_pct(row.get("pdp_sessions"), journey),
                "atc_pct": safe_pct(row.get("atc_sessions"), journey),
                "cart_pct": safe_pct(row.get("cart_sessions"), journey),
                "cvr_pct": safe_pct(row.get("order_sessions"), journey),
            })

        device_rows.sort(key=lambda item: (-(item["pdp_pct"] or 0), item["market"]))
        if not device_rows:
            continue

        if missing_markets:
            device_notes.append("Note: " + ", ".join(missing_markets) + " absent from this dataset.")
        device_notes.extend(notes)

        tables.append({
            "title": f"{title_prefix} ({payload.get('source_id', 'session funnel')}, {period_label})" if period_label else title_prefix,
            "description": "Sorted by PDP% ↓",
            "columns": ["Market", "Sessions", "PDP%", "ATC%", "Cart%", "CVR%"],
            "rows": [
                [
                    row["market"],
                    fmt_int(row["sessions"]),
                    fmt_pct(row["pdp_pct"]),
                    fmt_pct(row["atc_pct"]),
                    fmt_pct(row["cart_pct"]),
                    fmt_pct(row["cvr_pct"]),
                ]
                for row in device_rows
            ],
            "notes": list(dict.fromkeys(device_notes)),
        })
    return tables


def user_full_funnel_table(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows", [])
    if not rows:
        return []

    aggregate: dict[str, dict[str, float]] = {}
    for row in rows:
        total_users = to_float(row.get("total_users"))
        if total_users is None or total_users < 10:
            continue
        country = str(row.get("country", ""))
        aggregate.setdefault(country, {
            "total_users": 0.0,
            "users_hp": 0.0,
            "users_pdp": 0.0,
            "users_atc": 0.0,
            "users_cart": 0.0,
            "users_order": 0.0,
        })
        aggregate[country]["total_users"] += total_users
        aggregate[country]["users_hp"] += to_float(row.get("users_hp")) or 0.0
        aggregate[country]["users_pdp"] += to_float(row.get("users_pdp")) or 0.0
        aggregate[country]["users_atc"] += to_float(row.get("users_atc")) or 0.0
        aggregate[country]["users_cart"] += to_float(row.get("users_cart")) or 0.0
        aggregate[country]["users_order"] += to_float(row.get("users_order")) or 0.0

    checkout_map = {
        str(row.get("country", "")): to_float(row.get("clicked_checkout")) or 0.0
        for row in payload.get("checkout_rows", [])
        if isinstance(row, dict)
    }
    incomplete_markets = set(payload.get("incomplete_order_markets", []) or [])
    suspicious_markets = set(payload.get("suspicious_markets", []) or [])
    suspicious_notes = list(payload.get("suspicious_notes", []) or [])

    table_rows = []
    mismatch_markets = []
    largest_gap_market = None
    largest_gap_value = -1.0
    for country, values in aggregate.items():
        total_users = values["total_users"]
        hp_pct = safe_pct(values["users_hp"], total_users)
        pdp_pct = safe_pct(values["users_pdp"], total_users)
        atc_pct = safe_pct(values["users_atc"], total_users)
        cart_pct = safe_pct(values["users_cart"], total_users)
        checkout_pct = safe_pct(checkout_map.get(country), total_users)
        cvr_pct = safe_pct(values["users_order"], total_users)

        if pdp_pct is not None and atc_pct is not None and (pdp_pct - atc_pct) > largest_gap_value:
            largest_gap_value = pdp_pct - atc_pct
            largest_gap_market = country

        market_label = country
        suffix = ""
        if country in incomplete_markets:
            suffix += "†"
        if country in suspicious_markets:
            suffix += " ⚠️"
        if suffix:
            market_label += f" {suffix.strip()}"

        checkout_display = fmt_pct(checkout_pct)
        if checkout_pct is not None and cart_pct is not None and checkout_pct > cart_pct:
            checkout_display += " ⚠️"
            mismatch_markets.append(country)

        cvr_display = fmt_pct(cvr_pct)
        if country in incomplete_markets:
            cvr_display += "†"

        table_rows.append({
            "country": country,
            "market": market_label,
            "total_users": total_users,
            "cvr_sort": cvr_pct or 0.0,
            "row": [
                market_label,
                fmt_int(total_users),
                fmt_pct(hp_pct),
                fmt_pct(pdp_pct),
                fmt_pct(atc_pct),
                fmt_pct(cart_pct),
                checkout_display,
                cvr_display,
            ],
        })

    table_rows.sort(key=lambda item: (-item["cvr_sort"], item["country"]))
    if not table_rows:
        return []

    notes = []
    if mismatch_markets:
        notes.append("⚠️ " + ", ".join(sorted(mismatch_markets)) + " Checkout% > Cart% — denominator mismatch between user and checkout datasets.")
    if incomplete_markets:
        notes.append("† " + ", ".join(sorted(incomplete_markets)) + " order tracking incomplete in the user-level dataset — use Table 3 for order completion rates.")
    notes.extend(suspicious_notes)

    if largest_gap_market:
        notes.append(f"Reading: {largest_gap_market} has the largest PDP→ATC gap in this cut, indicating intent is reaching PDP but not converting into cart activity.")

    return [{
        "title": f"Table 2 — User-Level Full Funnel ({payload.get('source_id', 'user full funnel')}, {payload.get('period_label', '')})".rstrip(" ,"),
        "description": "Sorted by CVR% ↓ | † = order tracking incomplete, use Table 3",
        "columns": ["Market", "Tot. Users", "HP%", "PDP%", "ATC%", "Cart%", "Checkout%", "CVR%"],
        "rows": [item["row"] for item in table_rows],
        "notes": notes,
    }]


def checkout_funnel_table(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows", [])
    if not rows:
        return []

    incomplete_markets = set(payload.get("incomplete_order_markets", []) or [])
    table_rows = []
    worst_checkout_market = None
    worst_checkout_rate = None
    best_market = None
    best_rate = None
    for row in rows:
        cart_users = to_float(row.get("has_reached_cart"))
        if cart_users is None or cart_users < 10:
            continue
        country = str(row.get("country", ""))
        cart_to_checkout = safe_pct(row.get("has_clicked_secure_checkout"), cart_users)
        checkout_to_payment = safe_pct(row.get("has_finished_payment_methods"), row.get("has_clicked_secure_checkout"))
        payment_to_order = safe_pct(row.get("is_order_validated"), row.get("has_finished_payment_methods"))
        cart_to_order = safe_pct(row.get("is_order_validated"), cart_users)

        if worst_checkout_rate is None or (checkout_to_payment or 0) < worst_checkout_rate:
            worst_checkout_rate = checkout_to_payment or 0
            worst_checkout_market = country
        if best_rate is None or (cart_to_order or 0) > best_rate:
            best_rate = cart_to_order or 0
            best_market = country

        market_label = country + ("†" if country in incomplete_markets else "")
        cart_to_order_display = fmt_pct(cart_to_order) + ("†" if country in incomplete_markets else "")

        table_rows.append({
            "country": country,
            "sort": cart_to_order or 0.0,
            "row": [
                market_label,
                fmt_int(cart_users),
                fmt_pct(cart_to_checkout),
                fmt_pct(checkout_to_payment),
                fmt_pct(payment_to_order),
                cart_to_order_display,
            ],
        })

    table_rows.sort(key=lambda item: (-item["sort"], item["country"]))
    if not table_rows:
        return []

    notes = []
    if worst_checkout_market:
        notes.append(f"Reading: {worst_checkout_market} has the weakest Checkout→Payment rate in this cut, indicating the sharpest payment-stage friction.")
    if best_market:
        notes.append(f"Reading: {best_market} leads on Cart→Order conversion quality in this cut.")

    return [{
        "title": f"Table 3 — User-Level Checkout Funnel ({payload.get('source_id', 'checkout funnel')}, {payload.get('period_label', '')})".rstrip(" ,"),
        "description": "Sorted by Cart→Order% ↓ | † = order tracking incomplete",
        "columns": ["Market", "Cart Users", "Cart→Checkout%", "Checkout→Payment%", "Payment→Order%", "Cart→Order%"],
        "rows": [item["row"] for item in table_rows],
        "notes": notes,
    }]


def calculate_tables(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tables = []
    if isinstance(payload.get("session_funnel"), dict):
        tables.extend(session_funnel_tables(payload["session_funnel"]))
    if isinstance(payload.get("user_full_funnel"), dict):
        tables.extend(user_full_funnel_table(payload["user_full_funnel"]))
    if isinstance(payload.get("checkout_funnel"), dict):
        tables.extend(checkout_funnel_table(payload["checkout_funnel"]))
    return tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate deterministic funnel tables")
    parser.add_argument("--input", required=True, help="JSON input file, or '-' for stdin")
    parser.add_argument("--output", required=True, help="Path to write funnel tables JSON")
    args = parser.parse_args()

    if args.input != "-" and not os.path.exists(args.input):
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = load_input(args.input)
        tables = calculate_tables(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as handle:
        json.dump({"funnel_tables": tables}, handle, indent=2)
        handle.write("\n")

    print(f"Calculated funnel tables → {args.output} | tables={len(tables)}")


if __name__ == "__main__":
    main()