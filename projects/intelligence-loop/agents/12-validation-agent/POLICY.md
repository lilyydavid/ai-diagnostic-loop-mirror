# 12-validation-agent — Policy

## Role in pipeline

Agent 12 of the Phase 1 Intelligence Loop. Runs in parallel with Agent 11 after the Agent 10 PM gate.

For each PM-confirmed hypothesis, maps the current FE/BE journey for the relevant funnel
scope, then reads targeted code to understand the specific implementation. Proposes A/B
test designs per hypothesis, scoped to PM-approved segments where applicable.

Outputs feed Agent 13 directly and also feed the shared diagnosis artifact used before prioritisation.

**Local file system only. No Confluence, no Jira, no GitHub MCP, no Domo.**

```
outputs/signal-agent/pipeline-context.md       ──┐
outputs/feedback/findings.md                   ──┤
outputs/feedback/segment-cuts.md               ──┤──▶  *** PM GATE (repo + funnel scope) ***
config/repos.yml  (repo metadata)              ──┤         ↓
config/repos.local.yml  (local paths)          ──┘  12-validation-agent
                                                          ↓
                                              outputs/diagnosis/diagnosis.json
                                              outputs/validation/experiment-designs.json
                                              outputs/validation/experiment-designs.md
                                              outputs/validation/read-audit.log
```

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
          {
            "path": "src/components/AddToCart.tsx",
            "function": "handleAddToCart",
            "lines": "42-89",
            "grep_anchor": "handleAddToCart"
          }
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

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/validation/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. grep_anchor 'handleAddToCart' not found — function renamed to 'onAddToCart'"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update PROCEDURE.md with the new constraint (repo structure change, anchor naming convention, path mismatch)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
