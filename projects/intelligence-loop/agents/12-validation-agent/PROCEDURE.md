# 12-validation-agent — Procedure

Step-by-step execution. Resume from the labelled step when continuing a parked run.
Context: read POLICY.md for output contracts, permissions, security rules, and error handling.

---

## Step 0 — Validate input freshness

Before loading any inputs, check that upstream outputs are current:

```bash
python execution/check_input_staleness.py \
  --file outputs/signal-agent/pipeline-context.md \
  --threshold-days 3
```

Read the JSON output:
- If `stale: true`: surface to PM — "pipeline-context.md is {age_days} days old (last updated: {last_modified}). Proceed with stale inputs, or re-run Agent 10 first?" — halt until PM responds.
- If `reason: file_not_found`: halt — "Run /intelligence-loop Step 1 first".
- If `stale: false`: proceed.

---

## Step 1 — Load inputs

1. Read `outputs/signal-agent/pipeline-context.md` — load confirmed hypothesis list
2. Read `outputs/feedback/findings.md` if present — load Agent 11 qualitative context
3. Read `outputs/feedback/segment-cuts.md` if present — load PM-approved segment cuts
4. Read `config/repos.yml` — load repo metadata (names, types, keywords)
5. Read `config/repos.local.yml` — load local paths for each repo

If `pipeline-context.md` missing → halt: "Run /intelligence-loop Step 1 first"
If `findings.md` missing → note absence, continue with pipeline-context only
If `segment-cuts.md` missing → note absence, proceed without segment lens
If a repo's `local_path` is not in `repos.local.yml` → surface to PM at gate, do not block

For each hypothesis extract:
- `id`, `description`, `market`, `funnel_stage` (ATC / checkout / session / engagement)
- Any platform, version, or component noted in Agent 11 findings
- PM-approved segment cuts (e.g. platform: iOS, promo_active: true, tier: Gold)

---

## Step 2 — PM gate: repo + funnel scope selection

Present the following to the PM. **Do not read any files before PM responds.**

```
*** AGENT 12 — SCOPE GATE ***

Hypotheses loaded: {N}
Agent 11 segment cuts: {list or "none provided"}

Based on hypothesis types, suggested repos are:

  H{id} "{description}" → {suggested repo(s)}
  H{id} "{description}" → {suggested repo(s)}

Please confirm or override:
  1. Which repo(s) to survey? (name them, or say "use suggestions")
  2. Which funnel scope? (e.g. "ATC flow", "checkout", "sign-in", "PDP")

*** END GATE ***
```

Wait for PM response. Record: approved repo list, approved funnel scope.

**Repo suggestion keyword map** (for suggestions only — PM decides):

| Hypothesis keyword            | Suggested repo(s)                    |
|-------------------------------|--------------------------------------|
| ATC, add-to-cart, cart        | `sea-cart-ms`, `sea-web-app`         |
| checkout, payment, promo      | `sea-payment-ms`, `luxola`           |
| sign-in, auth, login, session | `sea-auth-ms`                        |
| PDP, product, catalogue       | `catalogue-service`, `sea-web-app`   |
| search                        | `catalogue-service`                  |
| loyalty, points, rewards      | `sea-promotion-ms`                   |

---

## Step 3 — Journey mapping (per approved funnel scope)

Before reading hypothesis-specific code, map the current FE+BE journey for the PM's
approved funnel scope. This is a structural survey — fast, broad, not deep.

**3a — Locate entry and exit points of the flow**
Use Glob and Grep to find route definitions, page components, and controller/service
entry points for the funnel scope. Aim for 5–8 key files that define the flow skeleton.

**3b — Trace the journey**
For each key file found, read enough to understand:
- What triggers this step (user action or system event)
- What the component/service does
- What it calls next (API call, state update, next route)
- Any branch conditions (platform check, auth state, feature flag)

**3c — Output journey map**
Produce a plain-text step-by-step flow:

```
[FE] User taps ATC button → handleAddToCart() called
[FE] → validate stock state → if OOS: show modal, halt
[FE] → POST /api/cart/add → sea-cart-ms CartController.add()
[BE] → check promo eligibility → PromotionService.applyAutoPromo()
[BE] → update cart state → return cart summary
[FE] → update cart icon count → navigate to cart or show toast
```

Note any observed branch conditions, platform guards, or feature flags at each step.
This map is written to `experiment-designs.md` as a header section and informs all
hypothesis-targeted reading in Step 4.

---

## Step 4 — Hypothesis-targeted code reading (per hypothesis)

Using the journey map from Step 3 as context, read targeted code for each hypothesis.

**4a — Locate the relevant step in the journey**
Identify which step(s) in the journey map the hypothesis implicates. Focus reading there.

**4b — Understand current implementation**
From the files at that step, extract (as descriptions — no raw code):
- Component/class name and file path
- Function or logic block relevant to the hypothesis
- Current behaviour — what it does today, step by step
- Any feature flags, A/B wrappers, or config-driven behaviour present
- Any TODOs, error handling gaps, or recent churn in the area

**4c — Apply segment lens**
If PM-approved segment cuts exist, check for segment-specific branches:
- `platform: iOS` → look for iOS version checks, platform conditionals
- `promo_active` → look for promo code application paths, discount logic
- `tier: Gold/Black` → look for loyalty tier branches

Note whether the failure path is segment-specific or affects all users.
This directly informs Impact scoring and variant scope in Step 5.

**4d — Check for existing experiments**
Search for: `featureFlag`, `experiment`, `variant`, `abTest`, `toggle`, `isEnabled`
If found: note flag name, what it controls, overlap with hypothesis.
An active flag in the same area may block or accelerate the new experiment.

---

## Step 4e — Emergent hypothesis synthesis

After completing code reading for all confirmed hypotheses, review everything observed
and generate additional hypotheses that were NOT in the original list from Agents 10/11.

This step is mandatory. Do not skip even if the confirmed hypothesis list appears complete.

**Sources to scan:**

1. **Journey map branch conditions** (Step 3) — every `if`, platform guard, feature flag,
   or config-driven branch is a potential failure point. Ask: "if this condition is
   wrong, stale, or misconfigured, what breaks?"

2. **Feature flags and A/B wrappers found in code** (Step 4d) — any active flag in the
   funnel path could be suppressing or inflating the metric. Each flag is a hypothesis:
   "active experiment in this path is masking the real signal."

3. **Fragility notes** (Step 4b) — TODOs, missing retry logic, double guards, stale
   cache reads, layout flash on reuse — these are candidate failure mechanisms. If you
   noted it as fragile, ask whether it could be failing right now.

4. **Agent 11 signals not yet mapped** — re-read `findings.md`. For every qualitative
   signal or UX observation not already covered by a confirmed hypothesis, ask whether
   code evidence from Steps 3–4 now provides a mechanism for it.

5. **Metric breadth check** — if the cycle signal is broad (multiple markets, multiple
   platforms), and all confirmed hypotheses are narrow (single market or single version),
   flag the gap explicitly: "confirmed hypotheses explain {X} markets; signal spans {Y}
   markets — missing mechanism for the remainder."

**For each emergent hypothesis found:**

Assign a temporary ID (H{n} continuing from confirmed list). Write a one-paragraph
description covering:
- What the mechanism is (what the code does that could cause the drop)
- What segment it affects (all users vs narrow)
- Why it wasn't in the original hypothesis list (not surfaced by Domo signal, or signal
  too broad to isolate)
- What evidence would confirm or reject it (Domo query, log pattern, flag audit)

**PM gate for emergent hypotheses:**

Present emergent hypotheses to PM before designing experiments:

```
*** AGENT 12 — EMERGENT HYPOTHESES ***

While mapping the {funnel scope} journey, {N} additional failure mechanisms were found
that were not in the original hypothesis list:

  H{n}: {one-line description} — source: {journey map / feature flag / fragility note / Agent 11 signal}
  H{n}: {one-line description} — source: {journey map / feature flag / fragility note / Agent 11 signal}

Suggested action per hypothesis:
  H{n}: design experiment — code mechanism confirmed
  H{n}: Domo validation first — mechanism plausible but needs data
  H{n}: flag to BI/Eng — data gap, not testable without pipeline fix

Proceed with experiment design for confirmed + approved emergent hypotheses?
(Respond: "yes all", "yes except H{n}", or list which to defer)

*** END GATE ***
```

Wait for PM response. Add approved emergent hypotheses to the working hypothesis list.
Proceed to Step 5 with the full combined list.

Before Step 5 completes, contribute diagnosis-layer outputs for orchestration:
- localise the failure surface in code terms
- identify at least 3 rival diagnoses spanning different causal classes where possible
- attach code evidence to each rival diagnosis as support / contradict / unresolved
- name the favored diagnosis and what code evidence would falsify it

---

## Step 5 — A/B test design (per hypothesis)

Choose FE or backend based on where the failure lives. Explain the choice in one line.

One primary design. Add secondary only if primary implementation risk is High.

Where segment cuts apply, specify whether the variant targets all users or a segment
rollout (e.g. "variant applies to iOS users only, controlled by platform feature flag").

**A/B test brief:**

```
Hypothesis: {what we believe is causing the metric drop}
Segment scope: {all users | iOS only | promo users | Gold/Black tier | ...}
Control: {current behaviour — cite file path + function name, no code}
Variant: {proposed change — specific, not generic}
Test type: FE component swap | FE feature flag | backend feature flag | backend logic branch
Success metric: {primary KPI} — MDE: {N}%
Files affected: {file path(s) + function name(s)}
SP estimate: {N}
Risk: {blast radius — how many flows / segments pass through this code}
Rollback: {how to revert}
Existing experiment flag: {flag name or "none"}
```

**Complexity rubric:**

| Change type                              | SP  |
|------------------------------------------|-----|
| Feature flag toggle / config value       | 1   |
| Copy or label change                     | 1   |
| Single component logic, no API change    | 2   |
| UI change + API contract change          | 3   |
| New service call or new endpoint         | >3  |
| Cross-service change (2+ microservices)  | >3  |

SP > 3 → classify backlog; note why quick-win not viable; still produce design for planning.

**Atomic scope rule:** Each A/B test design describes exactly one testable change. If the fix naturally spans multiple components (e.g. monitoring job + CRM journeys + CS tooling), split into one design per component and assign sub-IDs continuing from the hypothesis ID (H-D → H-D1, H-D2, H-D3). Describe the dependency relationship: "H-D1 is a prerequisite for H-D2" or "H-D1 and H-D2 are independent." Never write a single `variant` description that covers multiple independent deliverables.

**Cross-service coverage caveat:** If a hypothesis implicates a cross-service boundary but only one service was surveyed this cycle, set `confidence = Medium` at most regardless of what the surveyed code shows. State the gap explicitly in `confidence_reason`: "Only {surveyed_service} read this cycle; {unsurveyed_service} not surveyed — root cause may be upstream or downstream." This prevents mis-attribution when the real failure is in an unsurveyed service.

**Luxola-specific rule:** For the `luxola` repo (Rails monolith), cite method-level references only — use `def method_name` as the `grep_anchor`. Do not cite line numbers for luxola files; they are unreliable given file size and edit frequency. If a specific constant, error class name, or feature flag string was observed, add it as a secondary `grep_anchor` in a separate entry.

---

## Step 6 — Score for Agent 13

For each hypothesis, assign scores based on code and segment evidence:

**Confidence** (code confirms the hypothesis mechanism):
- `High` — code directly shows the failure (broken flag, null gap, hardcoded OOS, segment branch confirmed)
- `Medium` — code shows related fragility or recent churn in the area
- `Low` — no clear code evidence; hypothesis plausible but unsupported

**Impact** (centrality of affected code path + segment reach):
- `High` — core funnel path, all or majority of sessions; or segment-confirmed with large segment share
- `Medium` — conditional path (iOS only, promo users only, specific tier)
- `Low` — edge case, non-critical path, or very narrow segment

**Scope** (from SP estimate):
- SP 1 → `Tight` → score 3
- SP 2–3 → `Moderate` → score 2
- SP >3 → `Complex` → score 1

---

## Step 7 — Write outputs and read audit

Before writing outputs, verify each `grep_anchor` you assigned in Step 5:
- Run Grep for the anchor string in the file you cited
- If found → anchor is valid, write as-is
- If not found → remove or correct the anchor; downgrade `confidence` to Low for that entry

Then write all outputs (see POLICY.md for schemas), followed by the read audit log.

**grep_anchor rules:**
- Every `code_evidence.files` entry must include a `grep_anchor`: a specific identifier you observed in that file — function name, method signature, constant, error class, or feature flag string
- If you cannot name a specific identifier that you actually saw in the file, do not include the file in `code_evidence.files` — omit it and note the gap in `fragility_notes`
- For luxola files: use method-level anchors only (`def method_name`). Do not rely on line numbers for luxola — they are unreliable given file size and edit frequency
- `grep_anchor` is used by Agent 13 to re-verify claims before any Jira story is written
