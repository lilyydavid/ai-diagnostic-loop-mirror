# calculate_funnel_tables

## Purpose
Calculates deterministic funnel tables for Agent 10 from pre-aggregated market rows.

## Inputs
- Source: JSON object with optional `session_funnel`, `user_full_funnel`, and `checkout_funnel` sections
- Format: each section contains source metadata plus pre-aggregated rows ready for percentage calculation; no MCP calls or SQL happen in this script

## Script
`execution/calculate_funnel_tables.py`

## Outputs
- Destination: `.tmp/funnel-tables.json` or another orchestration-selected path
- Format: JSON object with `funnel_tables` array compatible with `execution/build_signal_report.py`

## Supported sections
- `session_funnel`: rows with `country`, `device_type`, `journey_sessions`, `pdp_sessions`, `atc_sessions`, `cart_sessions`, `order_sessions`
- `user_full_funnel`: rows with `country`, `device`, `total_users`, `users_hp`, `users_pdp`, `users_atc`, `users_cart`, `users_order`, plus `checkout_rows` with `country` and `clicked_checkout`
- `checkout_funnel`: rows with `country`, `has_reached_cart`, `has_clicked_secure_checkout`, `has_finished_payment_methods`, `is_order_validated`

## Edge cases
- Rows with zero or missing denominators are skipped from rate calculations
- `user_full_funnel` excludes device rows where `total_users < 10`
- `checkout_funnel` excludes rows where cart users are `< 10`
- Markets may be annotated via `missing_markets`, `suspicious_web_markets`, `incomplete_order_markets`, `suspicious_markets`, and `suspicious_notes`