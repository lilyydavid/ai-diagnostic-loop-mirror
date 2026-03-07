# Funnel Monitor — LNO Output
# Week: 2026-02-25 → 2026-03-03
# Generated: 2026-03-05
# For: product and business team prioritization

## L — Leverage (act this week)

| # | Action | Owner | Signal |
|---|---|---|---|
| L1 | Investigate cart-to-checkout drop — pull session recordings, identify where users are abandoning the cart page. Is it a UX change, a promotion mechanic, or a pricing signal? | Ecommerce PM + UX | Cart→Checkout CTR 17.09% ↓ -18.66% YoY |
| L2 | Fix payment retry flow — 11.09% of orders fail at payment. ~70% of those users never retry. Build a retry nudge (push/email within 1 hr). | Ecommerce Eng + CRM | Payment Failure Rate 11.09% |
| L3 | Audit address completion drop-off — 58.63% completion rate. Run funnel analysis: where do they drop (sign-in, form fields, postcode lookup)? | Ecommerce PM + UX | Address Completion Rate 58.63% |
| L4 | Checkout success rate war room — 39.25% combined, -7.22% YoY, below 40% threshold. Convene ecommerce + eng + data this week. This is a P1. | Ecommerce PM + Eng Lead | Checkout Success Rate 39.25% |

## N — Neutral (monitor, weekly check-in)

| # | Signal | What to watch | Escalate if |
|---|---|---|---|
| N1 | Sessions: Feb 14.7M (+19% vs Jan) | March partial: 1.3M (5 days). On track for ~8M if sustained. | Drop below 10M in March |
| N2 | AOV: €58.76 combined (-1.40% YoY) | Stable. App AOV (€61.84) > web (€50.92). | Drop below €55 |
| N3 | C&C Orders as % of Ecomm: 7.51% (↓ from 8.47% Week 1) | Slow 10-week decline. Not a crisis yet. | Drop below 6% or 3 consecutive weeks of decline |
| N4 | Search CVR: 3.1% (Week 9), stable week-on-week | YTD combined 2.9% ↓-11.6% YoY — concerning but weekly stable. | Weekly drops below 2.5% |
| N5 | App Engagement Rate: 27.53% ↓-10.21% YoY | Watch in context of Storyly rollout. | Drop below 25% |

## O — Overhead (delegate or automate)

| # | Action | Delegate to |
|---|---|---|
| O1 | Verify ATC Rate YoY drop (-69.2% combined) — almost certainly a metric definition change, not real. | Data team — confirm definition before acting |
| O2 | Email sign-up success rate = 0% — tracking break, not a conversion issue. | Data/Analytics — check event firing |
| O3 | Weekly report generation — already automated via /funnel-monitor agent. | Agent runs every Thursday |
