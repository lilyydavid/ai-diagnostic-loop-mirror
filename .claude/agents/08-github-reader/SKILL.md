# /github-reader — Code Context Reader (Agent 8)

## Role in pipeline
Agent 8. Called by `/growth-engineer` in Week 3. Reads relevant GitHub repos to understand
the current code state for each validated hypothesis. Identifies specific files, functions,
and patterns that need changing, and assesses change complexity.

```
Reads:  outputs/validation/validated-hypotheses.md
        GitHub repos: sephora-asia org (via github MCP)
Writes: outputs/github-reader/code-context.md
```

## Trigger
Called by `/growth-engineer` automatically in Week 3.
Can also be run standalone: `/github-reader` or "read code for hypotheses", "find relevant code".

---

## Repo Map
From `config/atlassian.yml`:

**Always read (every run):**
- `sephora-asia/sea-web-app` — TypeScript frontend (web)
- `sephora-asia/web-ui` — JavaScript SSR / homepage UI
- `sephora-asia/luxola` — Ruby core ecommerce platform (cart, checkout, PDP)

**Conditional (only when hypothesis `code_area` matches):**
| code_area keyword | Repo |
|---|---|
| cart, add-to-cart, basket | `sea-cart-ms` |
| payment, checkout, order | `sea-payment-ms` |
| order, fulfilment | `sea-order-ms` |
| search, catalogue, PDP, product | `catalogue-service` |
| login, sign-in, auth, account | `sea-auth-ms` |
| promotion, voucher, reward, loyalty | `sea-promotion-ms` |

---

## Agent Steps

### Step 1 — Load validated hypotheses
Read `outputs/validation/validated-hypotheses.md`.
Extract all Sprint Candidates and Backlog Candidates.
For each hypothesis, note: `code_area`, `funnel_stage`, `proposed_fix`.

### Step 2 — Map hypotheses to repos
For each hypothesis:
1. Always include `sea-web-app`, `web-ui`, `luxola`
2. Check `code_area` keyword against repo map above — add conditional repos
3. Record the repo list for this hypothesis

### Step 3 — Search and read code (per hypothesis)

For each hypothesis, execute these searches in mapped repos:

**3a. Component/route discovery**
Search for files related to the funnel stage:
- Checkout: search `checkout`, `payment`, `order-summary`, `cart-review`
- Cart/ATC: search `cart`, `add-to-cart`, `basket`
- PDP: search `product-detail`, `pdp`, `product-page`
- Search: search `search-results`, `algolia`, `catalogue`
- Auth: search `login`, `sign-in`, `auth`

Use GitHub MCP search to find files, then read the most relevant 2–4 files per hypothesis.

**3b. Pattern extraction**
From the files read, extract:
- Component/class name and file path
- The specific function/method relevant to the hypothesis
- Current behaviour (what it does today)
- The line range or logic block that would need changing
- Any feature flags, A/B test wrappers, or config-driven behaviour
- Dependencies: what else calls this code

**3c. Complexity assessment**
For each proposed change, estimate story points:

| Change type | SP estimate |
|---|---|
| Copy/label change | 1 |
| Config value or feature flag | 1 |
| CSS/styling only | 1 |
| Single component logic change, no API change | 2 |
| UI change + API contract change | 3 |
| New service call or new API endpoint | > 3 (backlog) |
| Database schema change | > 3 (backlog) |
| Cross-service change (2+ microservices) | > 3 (backlog) |

If the code reading reveals that the proposed fix is more complex than initially assessed,
update the SP estimate and reclassify quick-win → backlog accordingly.

### Step 4 — Multi-step reasoning: change impact assessment

For each code finding, reason explicitly:

1. **Blast radius** — how many user flows / pages does this code affect?
2. **Test coverage** — are there existing tests for this code? (look for spec/ or __tests__ dirs)
3. **Recent changes** — has this file been modified recently? (indicates active development risk)
4. **Quick win viability** — can the proposed change be made in isolation, or does it pull in dependencies?
5. **Risk flag** — note any code patterns that suggest the change is riskier than estimated

### Step 5 — Write output
Write `outputs/github-reader/code-context.md`. Overwrite on each run.

---

## Output Contract

### `outputs/github-reader/code-context.md`
Overwrite on each run.

```markdown
# Code Context — {YYYY-MM-DD}
Repos scanned: {list}
Hypotheses processed: {N}

## H1 — {hypothesis title}
- Funnel stage: {stage}
- Repos read: {list}
- Classification: QUICK WIN (≤3 SP) | BACKLOG (>3 SP)
- Story points estimate: {N}

### Relevant files
| File | Repo | Lines | Component/Function | Purpose |
|---|---|---|---|---|
| `path/to/file.tsx` | sea-web-app | 142–198 | `CheckoutForm.handleSubmit` | Handles checkout form submit |

### Current behaviour
{description of what the code does today}

### Proposed change
{specific description of what needs to change}
- File: `path/to/file.tsx`
- Function: `CheckoutForm.handleSubmit` (line 162)
- Change: {exact description — e.g., "add retry logic after payment failure response code 402"}

### Risk flags
- {any flags from Step 4 reasoning}

### Test coverage
- Existing tests: {yes/no/partial} — `path/to/spec`

---

## H2 — {hypothesis title}
[same schema]

---

## Reclassified items
Hypotheses reclassified after code reading (quick-win → backlog):
| Hypothesis | Original SP | Revised SP | Reason |
|---|---|---|---|

## Search coverage log
| Repo | Files read | Search terms used |
|---|---|---|
```

---

## Configuration
```yaml
# config/atlassian.yml
github:
  org: "sephora-asia"
  always_read: [sea-web-app, web-ui, luxola]
  conditional:
    cart: "sea-cart-ms"
    payment: "sea-payment-ms"
    ...
```

## Permissions
- Read: `outputs/validation/validated-hypotheses.md`
- Read: `config/atlassian.yml`
- Read: GitHub repos in `sephora-asia` org (via `github` MCP, read-only)
- Write: `outputs/github-reader/code-context.md`

## Error Handling
- `validated-hypotheses.md` missing → halt: "Run /validate-hypotheses first"
- GitHub MCP returns 404 for repo → skip repo, note in search coverage log
- GitHub MCP returns 403 → note "Insufficient token scope" — do not retry
- File too large to read in full → read first 200 lines + last 50 lines, note truncation
- No relevant files found for hypothesis → note "No matching code found" — do not block Jira story creation; agent 9 will flag it
- Complexity assessment is ambiguous → default to higher SP estimate (conservative)
