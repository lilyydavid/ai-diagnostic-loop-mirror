# 12-validation-agent — Journey Mapping + Experiment Design (Step 2b)

## Role in pipeline

Agent 12 of the Phase 1 Intelligence Loop. Runs after Agent 11.

For each PM-confirmed hypothesis, maps the current FE/BE journey for the relevant funnel
scope, then reads targeted code to understand the specific implementation. Proposes A/B
test designs per hypothesis, scoped to PM-approved segments where applicable.

Outputs feed Agent 13 directly.

**Local file system only. No Confluence, no Jira, no GitHub MCP, no Domo.**

```
outputs/signal-agent/pipeline-context.md       ──┐
outputs/feedback/findings.md                   ──┤
outputs/feedback/segment-cuts.md               ──┤──▶  *** PM GATE (repo + funnel scope) ***
config/repos.yml  (repo metadata)              ──┤         ↓
config/repos.local.yml  (local paths)          ──┘  12-validation-agent
                                                          ↓
                                              outputs/validation/experiment-designs.json
                                              outputs/validation/experiment-designs.md
                                              outputs/validation/read-audit.log
```

---

## Trigger

Spawned by `/intelligence-loop` after Agent 11 completes.
Standalone: "survey codebase", "design experiments", "run validation agent".

---

## Security Rules

These rules apply at all times. No exceptions.

- **Never write raw code** to any output file. Write descriptions of behaviour only.
- **File paths and function names** may appear in outputs as references — no file contents.
- **No secrets, keys, tokens, or config values** read from repos may appear in any output.
- **No stack traces or error strings** from source files in outputs.
- **Outputs are local only** — `outputs/validation/` never goes to Confluence or Jira.
- **Memory prohibition** — Agent 12 must never write code patterns, implementations,
  file paths, or any code-derived content to memory files. Code evolves; cached code
  insights create false confidence. Only scored outputs (not evidence) may be referenced
  in future cycles.

---

## Agent Steps

### Step 1 — Load inputs

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

### Step 2 — PM gate: repo + funnel scope selection

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

### Step 3 — Journey mapping (per approved funnel scope)

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

### Step 4 — Hypothesis-targeted code reading (per hypothesis)

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

### Step 4e — Emergent hypothesis synthesis

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

---

### Step 5 — A/B test design (per hypothesis)

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

---

### Step 6 — Score for Agent 13

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

### Step 7 — Write outputs and read audit

Write all outputs. Then write the read audit log.

---

## Output Contract

### `outputs/validation/experiment-designs.json`
**Overwrite** each run.

```json
{
  "generated_at": "YYYY-MM-DD",
  "cycle_signal": "description of primary signal",
  "funnel_scope": "ATC flow",
  "repos_surveyed": ["sea-cart-ms", "sea-web-app"],
  "segments_applied": ["platform: iOS", "promo_active: true"],
  "entries": [
    {
      "id": 1,
      "description": "hypothesis description",
      "market": "AU",
      "funnel_stage": "ATC",
      "segment_scope": "iOS users with active promo",
      "code_evidence": {
        "repo": "sea-cart-ms",
        "files": [
          { "path": "src/components/AddToCart.tsx", "function": "handleAddToCart", "lines": "42-89" }
        ],
        "current_behaviour": "description of what the code does today — no raw code",
        "existing_experiment": "flag name or null",
        "fragility_notes": "any TODOs, error gaps, or churn noted — no raw code"
      },
      "ab_test": {
        "control": "current behaviour description",
        "variant": "proposed change description",
        "segment_rollout": "iOS users only via platform feature flag",
        "test_type": "FE feature flag",
        "success_metric": "ATC rate",
        "minimum_detectable_effect": "5%",
        "files_affected": ["src/components/AddToCart.tsx"],
        "sp_estimate": 2,
        "sprint_viable": true,
        "risk": "blast radius description",
        "rollback": "rollback method"
      },
      "confidence": "Medium",
      "confidence_reason": "one-line explanation",
      "impact": "High",
      "impact_reason": "one-line explanation",
      "scope": "Moderate",
      "scope_score": 2
    }
  ],
  "summary": {
    "total_entries": 0,
    "sprint_viable": 0,
    "backlog_only": 0,
    "existing_experiment_conflict": 0,
    "segment_scoped": 0
  }
}
```

### `outputs/validation/experiment-designs.md`
**Overwrite** each run.

```markdown
# Experiment Designs — {YYYY-MM-DD}
Cycle signal: {primary signal}
Funnel scope: {scope} | Repos: {list} | Segments applied: {list or none}
Hypotheses: {N} | Sprint viable: {N} | Backlog: {N}

---

## Journey Map — {funnel scope}

[FE] {step description}
[BE] {step description}
[FE] {step description}
...

Branch conditions observed: {list}
Existing experiment flags in scope: {list or none}

---

## H{id} — {description} ({market})

**Segment scope:** {all users | iOS only | promo users | ...}

**Code evidence**
- Repo: {name} | Files: {path + function}
- Current behaviour: {description — no raw code}
- Existing experiment: {flag or none}
- Fragility notes: {or none}

**A/B Test Design**
- Control: {current behaviour}
- Variant: {proposed change}
- Segment rollout: {scope of variant}
- Test type: {type}
- Success metric: {metric} | MDE: {N}%
- Files: {paths + functions}
- SP: {N} | Sprint viable: yes/no
- Risk: {blast radius}
- Rollback: {method}

**Agent 13 scores**
- Confidence: {High/Medium/Low} — {reason}
- Impact: {High/Medium/Low} — {reason}
- Scope: {Tight/Moderate/Complex} (SP {N})

---

*Generated by 12-validation-agent | {date}*
```

### `outputs/validation/read-audit.log`
**Overwrite** each run. Session record only — not a history file.

```
Date: YYYY-MM-DD
Repos accessed:
  - sea-cart-ms ({local_path})
  - sea-web-app ({local_path})

Files read:
  - sea-cart-ms: src/components/AddToCart.tsx
  - sea-cart-ms: src/services/CartService.ts
  - sea-web-app: pages/pdp/[id].tsx

Search terms used:
  - addToCart, handleAdd, CartService, featureFlag, experiment

Total files read: {N}
```

---

## Configuration

```yaml
# config/repos.yml — committed, no paths
repos:
  - name: "sea-web-app"
    type: "frontend"
    keywords: ["ATC", "PDP", "search", "checkout"]
  - name: "sea-cart-ms"
    type: "backend"
    keywords: ["ATC", "cart", "basket"]
  - name: "sea-payment-ms"
    type: "backend"
    keywords: ["checkout", "payment", "promo", "voucher"]
  - name: "sea-auth-ms"
    type: "backend"
    keywords: ["sign-in", "auth", "login", "OTP", "session"]
  - name: "sea-promotion-ms"
    type: "backend"
    keywords: ["loyalty", "points", "rewards", "promo"]
  - name: "catalogue-service"
    type: "backend"
    keywords: ["PDP", "product", "catalogue", "stock", "search"]
  - name: "luxola"
    type: "backend"
    keywords: ["checkout", "payment", "order"]

# config/repos.local.yml — git-ignored, personal paths only
repos:
  sea-web-app: "/Users/yourname/dev/sea-web-app"
  sea-cart-ms: "/Users/yourname/dev/sea-cart-ms"
```

---

## Permissions

- Read: `outputs/signal-agent/pipeline-context.md`
- Read: `outputs/feedback/findings.md`
- Read: `outputs/feedback/segment-cuts.md`
- Read: `config/repos.yml`
- Read: `config/repos.local.yml`
- Read: local repo file system (paths from `repos.local.yml`) — Read/Grep/Glob only, no writes to repo
- Write: `outputs/validation/experiment-designs.json` (overwrite)
- Write: `outputs/validation/experiment-designs.md` (overwrite)
- Write: `outputs/validation/read-audit.log` (overwrite)
- **No writes to**: Jira, Confluence, Domo, any repo, any memory file

---

## Error Handling

| Error | Action |
|---|---|
| `pipeline-context.md` missing | Halt — "Run /intelligence-loop Step 1 first" |
| `findings.md` missing | Note absence; continue with pipeline-context only |
| `segment-cuts.md` missing | Note absence; proceed without segment lens |
| Repo missing from `repos.local.yml` | Surface at gate: "No local path for {repo}. Add to repos.local.yml." — skip repo, continue |
| Repo path not found on disk | Surface to PM: "{repo} not found at {path}. Has it been cloned?" — skip, continue |
| No relevant files found for hypothesis | Set confidence = Low; note "No matching code found"; still produce experiment design from hypothesis description |
| Journey map produces no clear flow | Note "Flow structure unclear"; proceed to hypothesis-targeted reading without map context |
| Existing experiment in same area | Flag prominently — note flag name, overlap, and whether it blocks or enables the new test |
| SP > 3 | Classify backlog; note why; still produce experiment design |
| All hypotheses SP > 3 | Surface to PM: "No sprint-viable experiments found. All designs are backlog candidates." |
| `outputs/validation/` missing | Create directory before writing |
