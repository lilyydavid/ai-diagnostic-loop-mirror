# /validate-hypotheses — Hypothesis Validation + Synthetic Research (Agent 7)

## Role in pipeline
Agent 7. Called by `/growth-engineer` in Week 2. Validates hypotheses from funnel-monitor
against existing Confluence user research. Runs synthetic user research to fill evidence gaps.
Scores and ranks hypotheses by confidence, impact, and implementation scope.

```
Reads:  outputs/funnel-monitor/validation-hypotheses.md
        outputs/funnel-monitor/pipeline-context.md
        outputs/market-intel/signals.md
        Confluence — user research pages (PI space)
Writes: outputs/validation/validated-hypotheses.md
```

## Trigger
Called by `/growth-engineer` automatically in Week 2.
Can also be run standalone: `/validate-hypotheses` or "validate hypotheses", "score hypotheses".

---

## User Personas (synthetic research base)
Three standing personas for Sephora SEA. Used in all synthetic research runs.

**Persona A — The Loyalist**
- Profile: Female, 28–35, Singapore or Malaysia, Sephora Beauty Pass member
- Device: iOS app (primary), web (occasional)
- Behaviour: Shops 2–3x/month, knows what she wants, uses saved addresses and stored payment
- Friction sensitivity: High for checkout changes, low for discovery friction

**Persona B — The Comparison Shopper**
- Profile: Female, 25–40, Malaysia or Thailand, non-member or Silver tier
- Device: Android app or mobile web
- Behaviour: Price-compares across Lazada/Shopee, visits Sephora for brand assurance
- Friction sensitivity: High for price/promo clarity, high for payment failure, will abandon for competitors

**Persona C — The Occasion Buyer**
- Profile: Female or male, 20–30, any SEA market, gift buyer or self-treat
- Device: Web (desktop or mobile)
- Behaviour: Infrequent visitor, large basket, easily confused by loyalty/checkout flow
- Friction sensitivity: Very high for address and checkout complexity, low trust with payment

---

## Agent Steps

### Step 1 — Load inputs
1. Read `outputs/funnel-monitor/validation-hypotheses.md` — load all hypotheses
2. Read `outputs/funnel-monitor/pipeline-context.md` — load metric context
3. Read `outputs/market-intel/signals.md` if it exists — load market signals
4. Record which files were loaded successfully

### Step 2 — Search Confluence for supporting research
Load research sources from `config/atlassian.yml` → `validation.research_sources`.
For each source, start from the configured `page_id` and search its descendants.
Do not search outside these configured sources — never hardcode space keys or page IDs.

For each hypothesis, use `confluence_search_terms` from the hypothesis schema.
Also search using: hypothesis funnel stage + "user research" + "usability" + "test".

Search strategy per source:
1. Fetch page descendants: `GET /wiki/rest/api/content/{page_id}/descendant/page?limit=50`
2. Full-text search within the space: CQL `space = "{space_key}" AND text ~ "{search_term}" AND ancestor = {page_id}`
3. Read matching pages and extract relevant findings

For each matching Confluence page:
- Read the page content
- Extract findings that confirm or contradict the hypothesis
- Note the research date (older than 18 months = reduced weight)
- Record: page title, key finding, direction (supports/contradicts/neutral), recency

Confidence from Confluence evidence:
- 2+ pages with recent (< 18 months) supporting evidence → **High**
- 1 page supporting, or older evidence → **Medium**
- No Confluence evidence found → **Low** → trigger synthetic research (Step 3)

### Step 3 — Synthetic research (for Low-confidence hypotheses)

For each hypothesis with Low Confluence confidence:

**3a. Persona journey simulation**
For each of the 3 personas (A, B, C), simulate their journey through the problematic flow:
- Entry point (how they arrive at the funnel stage)
- Navigational steps they take
- Point of friction: what specifically causes hesitation or abandonment
- Likely action: abandon, retry, seek help, switch to competitor
- What single change would most likely keep them in the funnel

Score each persona's friction severity: Critical (would abandon) / Moderate (would hesitate) / Minor (would proceed).
Record which personas are most affected.

**3b. A/B outcome modeling**
For the proposed fix in the hypothesis, estimate expected lift:
- Reference: industry benchmarks for similar funnel-stage changes
- Reference: metrics-history.json for Sephora baseline
- Model: if the fix is implemented, what % improvement in the target metric is plausible?
- Range estimate: conservative / expected / optimistic
- Example: "Reducing checkout steps: conservative +5%, expected +10%, optimistic +18% checkout CVR"

Document assumptions made. Flag if no reliable benchmark is available.

### Step 4 — Market signal correlation
For each hypothesis, check `outputs/market-intel/signals.md`:
- Does any headline signal corroborate this hypothesis? → boost confidence by one level
- Does any competitor activity directly explain the metric shift? → note as alternative cause
- Does social sentiment match the friction type in the hypothesis?

If market signal strongly corroborates → upgrade confidence by one level (Low→Medium, Medium→High).

### Step 5 — Multi-step reasoning: score and rank

For each hypothesis, apply structured scoring:

1. **Confidence score** (1–3): Low=1, Medium=2, High=3
2. **Funnel impact score** (1–3):
   - Drop in metric affects < 10% of sessions = 1
   - Affects 10–30% of sessions = 2
   - Affects > 30% of sessions or is a checkout/payment metric = 3
3. **Implementation scope** (inverted, 1–3):
   - > 3 story points (major change) = 1
   - 2–3 story points = 2
   - ≤ 1 story point (config, copy, minor UI) = 3
4. **Priority score** = Confidence × Impact × Scope (max 27)

Rank all hypotheses by priority score descending.
Top 3 = "Sprint candidates" (quick wins to act on in Week 3).
Remaining = "Backlog candidates".

Flag any hypothesis where Confidence = Low AND Impact = 3 → escalate for more research before acting.

### Step 6 — Write output
Write `outputs/validation/validated-hypotheses.md`. Overwrite on each run.

---

## Output Contract

### `outputs/validation/validated-hypotheses.md`
Overwrite on each run.

```markdown
# Validated Hypotheses — {YYYY-MM-DD}
Cycle week: {N} of 3
Inputs: funnel-hypotheses ({N} loaded), market-signals ({yes/no}), Confluence pages reviewed: {N}

## Sprint Candidates (top 3 — quick wins)
### H1 — {hypothesis title}
- Funnel stage: {stage}
- Metric affected: {metric name} ({current value} vs {benchmark/last week})
- Hypothesis: {statement}
- Evidence:
  - Confluence: {page title} — "{key finding}" ({date})
  - Market signal: {signal if any}
  - Synthetic: Persona {A/B/C} — {friction point} — severity: {Critical/Moderate/Minor}
- A/B model: conservative +{X}%, expected +{Y}%, optimistic +{Z}% on {metric}
- Confidence: {High/Medium/Low}
- Impact score: {1–3}
- Scope: {≤3 SP / >3 SP}
- Priority score: {N}/27
- Proposed fix: {specific change to make}
- code_area: {repo/component hint for Agent 8}
- output_type: {jira_story / overhead}

### H2 — ...
### H3 — ...

## Backlog Candidates
### H4 — {hypothesis title}
[same schema, abbreviated]

## Escalated (Low confidence, High impact — needs more research)
### H{N} — {title}
- Reason for escalation: {why}
- Recommended next step: {what research would resolve this}

## Synthetic Research Log
### Persona journey simulations run: {N}
### A/B models run: {N}

## Confluence Pages Reviewed
| Page | Space | Finding | Direction | Date |
|---|---|---|---|---|
| ... | ... | ... | supports/contradicts | ... |
```

---

## Configuration
```yaml
# config/atlassian.yml
validation:
  research_sources:
    - space_key: "SEA"
      page_id: "63975620619"
      label: "UX Research Repository"
# Add more sources in atlassian.team.yml or atlassian.local.yml — never hardcode.
```

## Permissions
- Read: `outputs/funnel-monitor/validation-hypotheses.md`
- Read: `outputs/funnel-monitor/pipeline-context.md`
- Read: `outputs/market-intel/signals.md`
- Read: all Confluence pages (search across all spaces)
- Write: `outputs/validation/validated-hypotheses.md`

## Error Handling
- `validation-hypotheses.md` missing → halt with message: "Run /funnel-monitor first"
- `signals.md` missing → proceed without market correlation, note in output
- Confluence search returns 0 pages → mark all hypotheses as Low confidence, proceed to synthetic
- Hypothesis has no `confluence_search_terms` → generate search terms from hypothesis text
- Synthetic research produces no actionable insight → note "Insufficient signal — keep in Backlog"
