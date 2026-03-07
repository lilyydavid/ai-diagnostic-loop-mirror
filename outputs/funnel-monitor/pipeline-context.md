# Pipeline Context
week: 2026-W09
period: 2026-02-25 → 2026-03-03
generated: 2026-03-05
domo_dashboard: https://sephora-sg-asia.domo.com/page/83026514
domo_embed_page: 64742228008
confluence_report_page: 64742948865

---

## Metrics Snapshot

| Stage | Metric | Value | YoY | Status |
|---|---|---|---|---|
| Traffic | Sessions (week) | ~3,352,617 | — | 🟢 Growing |
| Traffic | Sessions (Feb total) | 14,696,666 | +19% vs Jan | 🟢 |
| Traffic | App Engagement Rate | 27.53% | ↓ -10.21% | 🟡 |
| Discovery | Non-Landing PDP View Rate (combined) | 2.28 | ↓ -20.81% | 🟡 |
| Discovery | Share of PDP Views (Non-Landing) | 33.7% | — | 🟡 |
| Discovery | Search CVR (combined) | 2.9% YTD / 3.1% week | ↓ -11.6% | 🟡 |
| Discovery | Sign-In Rate (combined) | 43.1% | ↓ -7.1% | 🟡 |
| Add to Cart | ATC Rate (combined) | ~19.5% | ↓ -69.2%* | 🟢 *verify metric |
| Add to Cart | Rewards Redemption Rate | 44.13% | ↑ +1.71% | 🟢 |
| Checkout | Cart→Checkout CTR (combined) | 17.09% | ↓ -18.66% | 🔴 |
| Checkout | Checkout Success Rate (combined) | 39.25% | ↓ -7.22% | 🔴 |
| Checkout | AOV (combined) | €58.76 | ↓ -1.40% | 🟢 |
| Checkout | Payment Failure Rate | 11.09% | — | 🔴 |
| Checkout | Address Completion Rate | 58.63% | — | 🔴 |
| Checkout | C&C as % of Ecomm | 7.51% | declining 10wk | 🟡 |
| Fulfilment | Orders Shipped Rate | 94.34% | ↓ -1.08% | 🟡 (target 99%) |
| Fulfilment | Orders Delivered On-Time | 94.93% | ↑ +2.67% | 🟢 |

*ATC YoY drop is likely a metric definition change — verify with data team before treating as real.

---

## Risk Map

| Risk ID | Severity | Signal | Linked Hypothesis |
|---|---|---|---|
| R1 | 🔴 High | Checkout success rate 39.25%, ↓ -7.22% YoY | H1, H3 |
| R2 | 🔴 High | Cart→Checkout CTR ↓ -18.66% YoY, 10-week trend | H1 |
| R3 | 🔴 High | Payment failure 11.09%, ~70% no retry | H2 |
| R4 | 🟡 Medium | Orders shipped 94.34% vs 99% target | H4 |
| R5 | 🟡 Medium | C&C declining 8.47% → 7.51% over 10 weeks | H4 |
| R6 | 🟡 Medium | App engagement ↓ -10.21% YoY | none (monitor) |
| R7 | 🟢 Watch | ATC rate ↓ -69.2% — likely metric definition mismatch | none (data team) |
| R8 | 🟢 Watch | Email signup success rate 0% — tracking break | none (data team) |

---

## Confluence Pages Scanned

Agents 2 and 3 should NOT re-read these for general context.
They MAY query specific pages for hypothesis-targeted evidence.

| Page ID | Title | Space | Relevance |
|---|---|---|---|
| 64742228008 | Domo Embed | PI | Primary data source (dashboard screenshots) |
| 64742948865 | Metric Monitor | PI | Output page — do not read as input |
| 63001919747 | Org Structure Proposal (PI Squad KPIs) | ENG | Baseline KPI definitions |
| 63708168503 | 2025 PI Roadmap | PI | Product context, PDP research |
| 64117440712 | Q1'25 Achievements | DATA | Historical conversion uplifts |
| 64212336699 | App: Skincredible Results on PDP | ISD | H5 source |
| 64741441552 | Competitive Research and Synthesis | ISD | Market benchmarks |
| 63635128321 | Stackable Promotions on Cart | PI | H1 source — check launch date |
| 64699236362 | Cart Discount Breakdown | PI | H1 source — cart metrics spec |

---

## Product Context

Recent launches relevant to current anomalies:

- **Stackable Promotions on Cart** — launched Jan 2026 (exact date: check page 63635128321).
  Suspect cause of Cart→Checkout CTR decline. H1 investigates this.

- **Skincredible PDP feature** — in-store scan with app handoff. AOV signal (€122 vs €69 baseline).
  H5 investigates whether this is scalable as a discovery flow.

- **Storyly AU** — launched Q1'25. Drove +8.5% assisted conversion uplift.
  Relevant context for App Engagement Rate decline — Storyly may be masking a deeper engagement drop.

---

## Active Hypotheses Index

| ID | Title | Priority | Product Area | Output Type |
|---|---|---|---|---|
| H1 | Cart-to-checkout drop caused by stackable promotions | High | cart | jira_story |
| H2 | Payment failure recovery gap | High | payment | jira_story |
| H3 | Address completion friction at postcode lookup | High | checkout | jira_story |
| H4 | C&C decline driven by in-store experience | Medium | fulfilment | jira_story |
| H5 | Skincredible sessions convert at 2× | Medium | discovery | jira_story |

Full details in: outputs/funnel-monitor/validation-hypotheses.md

---

## Data Gaps

- Organic traffic sessions: no data in filtered range (Domo filter issue)
- ATC YoY: suspected metric definition change — data team to verify
- Email signup success rate: 0% — tracking break
- Week 9 specific values for Web vs App checkout breakdown: not available in screenshots
