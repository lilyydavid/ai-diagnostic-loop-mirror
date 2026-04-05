---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
date: 2026-03-07
author: Ldavid
---

# Product Brief: squad-enhancement

## Executive Summary

squad-enhancement is an AI-orchestrated growth engineer co-pilot for ecommerce
Product Managers across SEA markets (SG, MY, TH, AU, NZ, HK, ID). It closes the
broken loop between funnel signal and business action — replacing a fragmented,
manual process (Domo + Teams + Jira) with a continuous, evidence-grounded workflow
that handles the grunt work of growth so PMs can focus on judgment.

The system monitors the complete ecommerce funnel (by platform and market), surfaces
calibrated alerts with context, proposes evidence-based hypotheses for PM fine-tuning,
and guides a structured human-in-the-loop cycle: Monitor → Hypothesise → Triangulate
→ Validate → Estimate → Ship. Each gate requires PM approval before proceeding.

The flywheel compounds over time: every completed PM loop enriches domain memory and
feeds a continuously updated prioritisation signal for leadership — translating
ground-level growth work into strategic confidence at the C-suite level.

This is also a flagship use case for scalable AI agent adoption within the organisation.

---

## Core Vision

### Problem Statement

Ecommerce PMs across SEA markets have no end-to-end system to move from funnel
signal to business action. Three overlapping failures compound the problem:

**P1 — Broken monitoring loop:** Alerts are miscalibrated (too many or none), fire
without context or call to action, and require each PM to manually track their domain
KPI slice. No one owns the complete funnel view. Country teams focus on lagging
revenue metrics; leading ecommerce metrics have no clear owner and no incentive to fix.

**P2 — Siloed, incomparable data:** UX pulse survey data cannot be triangulated
against funnel metrics. There is no time or budget to form hypotheses. Insights stay
siloed and never inform each other.

**P3 — Hypothesis graveyard:** When an alert fires, the PM drops everything,
investigates, and prepares a hypothesis — but it stalls on engineering grooming
dependency and goes unactioned. The PM is left exposed and the insight is lost.

### Problem Impact

- PM time consumed by reactive firefighting rather than strategic growth work
- Dropping KPIs go unaddressed; growing KPIs go unrecognised
- Hypotheses prepared but never actioned represent compounding lost opportunity
- No closed loop means no organisational learning — the same problems recur
- Leadership lacks the signal quality needed to prioritise with confidence

### Why Existing Solutions Fall Short

| Tool | Gap |
|---|---|
| Domo dashboards | Visibility only — no action layer, no intelligence, fully manual |
| Teams alerts | Notifications without context, no hypothesis, no tracking, no closure |
| Jira tickets | Manual grooming at every step, blocked by engineering bandwidth |

All three require full human input at every step with no intelligence layer
connecting them. No co-pilot, no coaching, no flywheel — just more PM time spent.

### Proposed Solution

An AI-orchestrated growth engineer co-pilot that:

1. **Monitors** the complete funnel across all SEA markets and platforms —
   calibrated alerts with context, not noise
2. **Proposes hypotheses grounded in evidence** — never concludes without
   material signal (funnel data, UX research, GitHub repo); asks for evidence
   if none is found
3. **Triangulates** across KPIs, trends, UX pulse data, and code changes
   to build a complete picture
4. **Routes to action** — effort estimate, impact estimate, Jira ticket —
   all with PM approval at each HIL gate
5. **Feeds leadership** — completed loops aggregate into a prioritisation
   signal: ranked domain health, hypothesis pipeline, and estimated revenue
   impact across SEA

### Key Differentiators

- **Growth engineer framing:** Not a dashboard or alert system — a skilled
  co-pilot that handles the grunt work so the PM focuses on judgment
- **Evidence-grounded:** Never hypothesises without material proof. Asks
  for evidence rather than hallucinating conclusions.
- **Two-audience flywheel:** PMs experience it as a daily co-pilot;
  leadership experiences it as quarterly prioritisation confidence. Same
  loop, two compelling value propositions.
- **End-to-end, not a point solution:** Alert to ticket to KPI recovery —
  one continuous loop replacing three disconnected tools.
- **Scalable agent adoption:** A concrete, high-value proof point for
  AI agents at scale across product domains.

---


## Success Metrics

### User Success — Priya (Platform PM)

Success for the PM is defined by two outcomes: completing the loop reliably, and
seeing real KPI recovery as a result. The tool works when Priya doesn't have to
think about the process — she just follows the flow and a sprint-ready ticket emerges.

**Loop Completion:**
- At least 1 completed growth loop (alert → Jira ticket) per sprint
- Target: achieved in ≥80% of sprints

**Trigger-to-Ticket Conversion:**
- ≥40% of triggered loops reach Jira ticket creation
- Reflects signal quality and hypothesis strength, not just system activity

**Domain Recovery:**
- Measurable conversion rate improvement attributable to a sprint action
  that originated from a completed loop
- Measurement window: within 1 month of ticket delivery
- Attribution method: compare pre/post KPI trajectory for the targeted
  market/platform segment

---

### Business Objectives

**1. Leadership Integration**
The flywheel becomes a standing input to monthly tech business meetings — Marcus
and leadership reference the hypothesis pipeline and domain health signal, replacing
ad-hoc firefighting conversations with structured, evidence-grounded briefings.

**2. PM Adoption**
The loop expands beyond the pilot (one PM, one domain KPI) to other domain PMs
running their own growth loops. Each new PM running the loop represents a validated
proof point for AI agent adoption at scale.

**3. Organisational Learning**
Completed loops accumulate as institutional memory — hypotheses tested, evidence
gathered, outcomes measured. The system compounds in value over time.

---

### Key Performance Indicators

| KPI | Target | Timeframe | Type |
|---|---|---|---|
| Completed loops per sprint | ≥1 | Per sprint | Leading |
| Sprint loop completion rate | ≥80% of sprints | Rolling 3 months | Leading |
| Trigger-to-ticket conversion rate | ≥40% | Rolling 3 months | Leading |
| Post-delivery KPI recovery | Measurable improvement | Within 1 month of delivery | Lagging |
| Leadership meeting references to loop output | Monthly (consistent) | From Month 2 | Adoption |
| Additional PMs running the loop | ≥2 new PMs | Within 6 months | Expansion |

---

### What We Are Not Measuring

- **Ticket volume for its own sake** — more tickets is not better; quality and
  conversion to sprint action matter
- **Time spent in the tool** — success is completing the loop efficiently, not
  engagement time
- **Hypothesis quantity** — one strong, evidence-grounded hypothesis beats five
  weak ones

---

## MVP Scope

### MVP Definition: Intelligence Loop (Phase 1 — Live)

The MVP is the full PM-triggered Intelligence Loop: the system detects KPI
signal from Domo, triangulates with qualitative feedback, maps the relevant
engineering journey, reads targeted code, proposes and scores A/B experiment
designs, ranks them by priority, and creates sprint-ready Jira tickets —
all with PM approval gates at each step.

Phase 1 does not require screenshots and has no dependency on GitHub MCP.
Code reading is done directly from local repo paths configured by the PM.

---

### Core Features (Phase 1 — Intelligence Loop)

**1. KPI Signal Detection (Agent 10)**
Agent queries registered Domo datasets and surfaces meaningful metric
movements by market and platform. Weak signals are noted but do not
trigger a full loop. PM reviews the signal report and confirms which
movements to investigate before the loop continues.

**2. Feedback Triangulation (Agent 11)**
Agent queries Domo feedback datasets (app reviews, Love Meter, CS tickets,
search terms) and Jira-based UX research (UXR project, Observation type)
for qualitative signals corroborating or challenging the detected movement.
Writes findings and segment cuts for Agent 12 to consume. Memory-first:
findings store is checked before querying Domo.

**3. Journey Mapping + Code Reading (Agent 12)**
For each PM-confirmed hypothesis, Agent 12 maps the current FE+BE journey
for the relevant funnel scope before reading hypothesis-specific code.
Journey mapping identifies entry/exit points, branch conditions, platform
guards, and active feature flags — giving the agent structural context
before targeted reading begins.

After reading hypothesis-specific code, Agent 12 synthesises emergent
hypotheses: additional failure mechanisms found in branch conditions,
feature flags, fragility notes, or Agent 11 signals not covered by the
confirmed list. Emergent hypotheses are presented to the PM at a gate
before experiment design proceeds.

Each hypothesis produces an A/B test design: control, variant, segment
scope, SP estimate, success metric, and blast radius. Compound hypotheses
are atomically decomposed — one testable change per design.

A grep_anchor verification pass runs before writing outputs: every file
cited must have a specific identifier (function name, method signature,
constant) that was actually observed and can be re-confirmed with Grep.

**4. Scoring and Ranking (Agent 13)**
Experiments are scored on Confidence (from Agent 12 code evidence) ×
Impact (code path centrality + signal severity) × Scope (SP estimate,
inverted). PM sees a ranked table of sprint candidates, backlog candidates,
pending data items, and items needing engineering spike.

Optional enrichment: if Agent 20 (inspiration loop) has run within the
staleness window, its market context and PM odds are loaded and can
break ties at equal priority scores.

**5. Code Grounding Check (Agent 13 — hard gate)**
Before any Jira story is created, Agent 13 re-verifies every code claim
from Agent 12 against the read audit log and re-runs Grep for each
grep_anchor. Stories where code claims cannot be verified are hard-blocked
and routed to a needs-spike file. PM is informed of blocked stories before
the agent proceeds with verified ones.

**6. Jira Story Creation (Agent 13)**
For PM-approved experiments that pass the code grounding check, Agent 13
creates sprint-ready Jira stories under the configured epic. A dedup check
runs first: carry-forward hypotheses (seen in prior cycles) update an
existing open ticket via comment rather than creating a new one. New
hypotheses are checked by JQL for any manually created tickets covering
the same issue.

Compound hypotheses are split into atomic sub-stories with one SP estimate,
one Proposed Change, and one set of Acceptance Criteria each.

**7. Trend Escalation (Agent 15)**
After Agent 13, the trend agent tracks confidence and priority scores
across cycles. Hypotheses with high priority scores that remain unactioned
across ≥2 cycles accumulate priority debt and are escalated to PM via
a Confluence brief. No GMV assumptions.

**8. Baseline Logging**
At Jira story creation, the system records the specific metric, segment,
market, and baseline value at time of creation. Recovery is measured at
the same granularity — not at aggregate conversion rate level. Attribution
is credible only when the exact problematic metric recovers post-action
within 1 month of delivery.

---

### Out of Scope for Phase 1

| Feature | Rationale | Phase |
|---|---|---|
| Screenshot-based funnel monitoring | Phase 2 — growth-engineer orchestrator | Phase 2 |
| GitHub MCP effort estimation | Phase 2 — requires GitHub MCP integration | Phase 2 |
| Market intel agent (web + social scan) | Phase 2 — growth-engineer orchestrator | Phase 2 |
| Session vs. user view toggling (Marcus dashboard) | Built after PM loop is proven | Phase 3 |
| Multi-PM support | Pilot with one PM, one domain KPI | Phase 3 |
| High-complexity / architectural tickets | Out of scope by design — quick wins only | Never (by design) |

---

### Phase 2 Unlock Condition

Phase 2 (Action Layer — growth-engineer orchestrator) unlocks when:

| Signal | Threshold |
|---|---|
| Intelligence Loop cycles completed | ≥3 full loops |
| Hypotheses actioned per loop | ≥2/3 per loop |

Both conditions must be met. If after 5+ months 3 loops have not completed,
this is a signal the trigger mechanism needs fixing — not a reason to force
expansion to Phase 2.

---

### Future Vision

**Phase 2 — Action Layer: Growth Engineer Orchestrator**
Adds the screenshot-based funnel monitoring layer, web + social market intel
scan, GitHub MCP effort estimation, and the full growth-engineer workflow
(Discovery → Validation → Delivery). The PM drops screenshots in a watch
folder and triggers `/growth-engineer` rather than manually pulling Domo.
Agents 05–09 orchestrate the pipeline with HIL gates at every decision point.

**Phase 3 — Multi-PM Flywheel + Leadership Signal**
Expand the loop to other domain PMs and their KPIs. Build the Marcus view:
hypothesis pipeline, domain health, session vs. user view bridging. Feed
completed loops into monthly tech business meeting artefacts. The flywheel
becomes an organisational capability, not a single PM tool.

**Long-term — Regional Scale**
The loop model — evidence-grounded hypothesis → sprint action → targeted
metric recovery — becomes replicable across other Sephora markets and
product domains.

---

## Feedback Intelligence Layer

### Overview

A configurable, token-sustainable data intelligence capability embedded in
Step 3 (Triangulate) of the growth loop. The agent queries registered Domo
datasets on a weekly basis, extracts aggregated quant and qual signals, and
stores key findings in a memory store — so that when a hypothesis loop
triggers, pre-computed insights are immediately available for triangulation
without redundant querying.

### Registered Dataset Types

| Dataset Type | Signal Character |
|---|---|
| App store reviews | Qualitative (verbatim) + quantitative (rating, topic, volume) |
| Love Meter (NPS) | Quantitative (score trend) + qualitative (open text) |
| Domain KPI | Quantitative (metric values by market/platform) |
| Skincredible feedback | Qualitative (verbatim) — product/experience feedback |
| Customer service tickets | Qualitative (issue category, verbatim) + quantitative (volume) |

Dataset IDs are configured in a registry file — never hardcoded. New
datasets are added via config without changes to agent logic.

### Token Sustainability Model

- **Memory-first:** Before querying Domo, agent checks findings store for
  an existing result covering the requested dataset and time window. Only
  re-queries when findings are stale or absent.
- **Aggregation-first:** All queries run as SQL aggregations at the
  database layer. Raw row-level data is never passed to an LLM.
- **Verbatim sampling:** Qualitative text fields are sampled to a defined
  maximum of representative rows — not full dataset dumps.
- **Weekly refresh cadence:** Findings store updated weekly regardless of
  whether a hypothesis loop is active, so insights are pre-loaded and
  ready when a loop triggers.

### PII Policy

The following fields are classified as PII and are excluded at the SQL
SELECT layer. The agent never retrieves them, regardless of dataset schema:

| Field | Classification |
|---|---|
| `user_id` | PII — excluded |
| `account_number` | PII — excluded |
| `card_number` | PII — excluded |
| `payment_details` / transaction data | PII — excluded |
| `address` (billing, shipping, any) | PII — excluded |
| `password` / password hash | PII — excluded |
| `login` / username / email / phone | PII — excluded |
| Name | PII — excluded |

If a dataset schema cannot be verified as PII-safe before querying, the
agent halts and flags for human review. PII exclusion is enforced at
both the query layer and the output layer — no PII may appear in the
findings store, Confluence pages, or Jira tickets.

---

## Data Access Ground Rules

All agents accessing external data sources must comply with the following
governance rules without exception:

1. **Least Privilege** — Agents only access datasets explicitly registered
   in config. No ad-hoc dataset discovery or querying outside the approved
   list.

2. **Read-Only** — Agents may never write to, modify, or delete data in
   any source system. Query only.

3. **Aggregation-First** — Raw row-level data is never passed to an LLM.
   SQL aggregations run at the database layer first. Verbatim text sampled
   to a defined maximum.

4. **Scoped Date Windows** — Queries always include a date range filter.
   No unbounded SELECT * — agents query only the window relevant to the
   current cycle (e.g. rolling 90 days).

5. **Schema Verification Before Query** — Before querying a new dataset,
   the agent inspects its schema. If PII columns are detected, the query
   halts and flags for human review before proceeding.

6. **Memory-First / No Redundant Queries** — If a finding for a dataset
   and time window already exists in the findings store and is not stale,
   the agent uses it. No re-querying what has already been processed.

7. **No Raw Data in Outputs** — Findings store, Confluence pages, and
   Jira tickets contain only aggregated insights and anonymised verbatim.
   No raw records surfaced downstream.

8. **Human Approval for New Datasets** — Adding a new dataset ID to config
   requires explicit human confirmation before the agent queries it for the
   first time.

9. **Fail-Safe on Access Error** — If a dataset query fails (auth error,
   timeout, schema mismatch), the agent halts that data source gracefully,
   logs the failure, and continues with available sources — never silently
   skips or fabricates.

10. **Purpose Limitation** — Data accessed for hypothesis triangulation
    only. Agent outputs may not be repurposed for other uses (e.g.
    marketing, profiling) without a new approval gate.





## Target Users

### Primary Users

#### Priya — Platform PM, SEA Ecommerce

**Role & Context:**
Priya is a Platform PM responsible for the end-to-end ecommerce funnel across all SEA
markets (SG, MY, TH, AU, NZ, HK, ID) and platforms (app, web, mobile web). She owns
the domain KPI — conversion rate — and is accountable for understanding whether it is
growing or dropping, why, and what to do about it. She runs the full growth loop up to
twice a month, triggered by meaningful metric movement rather than a fixed calendar date.

**Problem Experience:**
Priya currently moves through a fragmented, manual process: she checks Domo for metric
movement, breaks it down by market and platform manually, correlates it with other funnel
metrics across spreadsheets, digs into the UX research Confluence space for qualitative
signals, and then tries to estimate effort by reading GitHub repos or asking engineers
informally. By the time she has a hypothesis ready, engineering grooming bandwidth is
gone and the insight stalls.

She navigates two lenses simultaneously — the **session view** (what leadership sees)
and the **user view** (what she trusts as the cleaner signal). Switching between them
is manual and adds cognitive load to every investigation.

**Motivations & Goals:**
- Know quickly when conversion rate moves, which market or platform is driving it, and why
- Build hypotheses grounded in evidence, not instinct, before raising them
- Get from alert to Jira ticket in a single guided flow without engineering dependency
- Run the full loop up to twice a month without it consuming her week

**Success Vision:**
Priya opens the tool, sees a conversion rate drop flagged with the right context, drills
into the market/platform breakdown, triangulates with user funnel KPIs, finds qualitative
evidence from research, gets an effort read from the codebase, estimates impact, and
creates a prioritised, ready-to-groom Jira ticket — all without leaving the flow.

---

### Secondary Users

#### Marcus — Head of Ecommerce

**Role & Context:**
Marcus leads ecommerce across SEA. He monitors the business from a **session-based
perspective** — session volumes, homepage-to-PDP rate, add-to-cart rate from a session
lens. He engages with PMs primarily on a firefighting basis: when a metric looks wrong,
he comes to Priya for answers.

**Problem Experience:**
The session view Marcus uses can abstract what is actually happening — painting a rosier
(or more alarming) picture than the user-level view Priya trusts. When Marcus arrives
with a concern, Priya must quickly translate between lenses and reconstruct the full
picture from scratch. There is no shared, current artefact to anchor the conversation.

**Motivations & Goals:**
- Understand at a glance which KPIs are healthy and which are at risk
- Have confidence that hypotheses in flight are evidence-based and prioritised
- Reduce time spent on reactive, unanchored conversations with PMs

**Success Vision:**
Marcus can see a current, structured view of the hypothesis pipeline and domain health
— bridging session view and user view — so firefighting conversations become briefings
rather than investigations.

---

#### Dev — Engineer / Scrum Master

**Role & Context:**
Dev is the engineering SM equivalent on Priya's squad. The system reads his team's
GitHub repos passively for effort signals. At the end of the growth loop, Dev is the
critical gatekeeper: he reviews the Jira ticket Priya has prepared and decides whether
it goes into the sprint.

**Motivations & Goals:**
- Receive well-formed, evidence-backed tickets that are easy to groom
- Avoid being pulled into half-formed investigations mid-sprint

**Success Vision:**
The ticket that lands in Dev's queue already has a clear problem statement, a scoped
solution hypothesis, a rough effort signal, and an estimated KPI impact — reducing
grooming time and increasing the chance of sprint inclusion.

---

### User Journey

#### The Growth Loop (Priya's primary journey)

**Cadence:** Signal-driven, up to twice per month. Monitoring runs continuously (weekly);
the full hypothesis-to-ticket loop triggers only when metric movement is strong enough
to warrant investigation. In low-signal periods, the system recommends skipping ticket
creation for that cycle. This aligns naturally with a two-week sprint rhythm — one loop
per sprint at most, producing one or a small set of prioritised, ready-to-groom tickets.

**1. Monitor — Signal Detection**
The system surfaces a conversion rate movement (drop or growth) with market and platform
breakdown already attached. Priya reviews the alert with context — no manual Domo
digging required. The system flags signal strength; weak signals are noted but do not
trigger a full loop.

**2. Zoom In — Anomaly Identification**
Priya drills into which specific markets and platforms (app / web / mobile web) are
driving the signal. She toggles between the session view (Marcus's lens) and the user
view (her primary lens) to confirm the signal is real and understand its character.

**3. Triangulate — Hypothesis Building**
The system correlates the primary KPI movement with other funnel KPIs. Priya refines
the hypothesis: what is the most likely root cause based on the combined metric picture?

**4. Validate — Qualitative Evidence**
The system searches the research Confluence space for qualitative signals — UX pulse
data, usability findings, customer verbatims — that corroborate or challenge the
hypothesis. Priya reviews and confirms the hypothesis is evidence-grounded before
proceeding.

**5. Estimate — Effort & Impact**
The system reads relevant GitHub repos to produce a rough effort estimate per hypothesis.
Priya estimates the expected KPI impact if the hypothesis is addressed and stacks the
ranked list by effort-to-impact ratio.

**6. Ship — Jira Ticket Creation**
Priya approves the top hypothesis and the system creates a scoped, ready-to-groom Jira
story. Dev reviews and brings it into the sprint.

**Aha Moment:** Priya completes her first full loop — from conversion rate alert to
sprint ticket — in a single guided session, without chasing engineers, analysts, or
Confluence manually.

---
