# /growth-engineer — Autonomous Growth Engineer (Skill)

## What this skill does
Orchestrates the 3-week growth improvement cycle. Runs in the main conversation context,
spawning sub-agents (05–09) as needed. Manages cycle state across weeks with explicit
human validation gates between each week. Reports progress inline.

Drop a Domo screenshot into `inputs/screenshots/` before each run.
The skill detects which week of the cycle you're in and runs the appropriate steps.

Schedule: Weekly (every Thursday). Cycle resets on the 1st of each calendar month.

---

## Teams Notifications

If `teams.enabled: true` in config, post to Teams at each gate. Approval still happens in Claude Code.

| Event | Teams message | Action required |
|---|---|---|
| Gate 1 (end W1) | Hypothesis summary + Confluence link | Reply "approved" or "H1, H2 only" in Claude Code |
| Gate 2 (end W2) | Sprint Candidates ranked table + Confluence link | Reply "approved" or modify in Claude Code |
| W3 close | Jira ticket links + cycle summary | No action needed |

**Sending a Teams notification (via Teams Workflows webhook):**
Read `webhook_url` from resolved config (`atlassian.local.yml` → `atlassian.team.yml` → `atlassian.yml`).
If `teams.enabled` is false or `webhook_url` is empty → skip silently, do not error.

Teams Workflows webhooks require Adaptive Card format. Post via `curl`:
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST "{webhook_url}" \
  -H "Content-Type: application/json" \
  -d '{...adaptive card payload below...}'
```
Capture HTTP status code. If non-2xx → log "Teams notification failed (HTTP {status})" in cycle log, continue.

---

## Outputs per week

| Week | Confluence (`64742948865`) | Local files | Jira | Teams |
|---|---|---|---|---|
| Discovery | Funnel report + "Hypotheses Under Review" section | pipeline-context.md, validation-hypotheses.md, signals.md | — | Gate 1 notification |
| Validation | Same page: "Hypotheses Under Review" → "Validated Hypotheses" section | validated-hypotheses.md | — | Gate 2 notification |
| Delivery | Same page: "Validated Hypotheses" → "Sprint Actions" section (Jira links) | code-context.md, created-tickets.md | Quick-win + backlog stories under BAAPP-461 |

---

## Human Validation Gates

**Gate 1 (end of Discovery → before Validation):**
Agent prints hypothesis summary to chat and updates Confluence.
Human reviews the "Hypotheses Under Review" section on the Confluence page.
Human runs `/growth-engineer` again (with next week's screenshot) to start Validation.
At the START of Validation, agent re-presents the hypotheses and asks:
> "These are the Discovery hypotheses. Which should proceed to validation? Reply with hypothesis numbers to keep (e.g. 'H1, H2, H3') or 'all'."
Human confirms. Agent records approved list in `cycle-state.json` and proceeds.

**Gate 2 (end of Validation → before Delivery):**
Agent presents validated + ranked hypotheses with scores in chat.
Agent asks:
> "These are the Sprint Candidates ranked by priority. Confirm to create Jira tickets, or reply with changes (e.g. 'remove H2, keep H1 and H3', or 'move H1 to backlog')."
Human confirms or modifies. Agent records approved Sprint Candidates in `cycle-state.json`.
Human drops next screenshot. Runs `/growth-engineer` to start Delivery.

**No gate after Delivery** — cycle closes, summary posted to chat and Confluence.

---

## Confluence Page Structure

The same page (`64742948865`) is updated each week. Sections evolve:

```
Discovery write:
  1. Situation
  2. Action Impact (from prior cycle)
  3. Team Actions
  4. Risk Register
  5. Weekly Scorecard
  6. Monthly Sessions Trend
  7. [NEW] Hypotheses Under Review   ← growth engineer adds this
  8. Data Quality Notes
  Footer

Validation update (replace section 7):
  7. Validated Hypotheses             ← replaces "Under Review"
     - Sprint Candidates (top 3, ranked)
     - Backlog Candidates
     - Escalated (low confidence / high impact)

Delivery update (replace section 7):
  7. Sprint Actions                   ← replaces "Validated Hypotheses"
     - Quick-win tickets: {BAAPP-N links}
     - Backlog tickets: {BAAPP-N links}
     - Cycle summary ticket: {BAAPP-N link}
```

---

## Sub-agents spawned (in `.claude/agents/`)
| Week | Sub-agents called |
|---|---|
| Discovery | `05-funnel-monitor`, `06-market-intel` |
| Validation | `05-funnel-monitor`, `07-validation` |
| Delivery | `05-funnel-monitor`, `08-github-reader`, `09-jira-writer` |

---

## Cycle State Schema

`outputs/growth-engineer/cycle-state.json` — overwrite each week:

```json
{
  "cycle_month": "YYYY-MM",
  "current_phase": "discovery",
  "discovery_completed": null,
  "discovery_hypotheses_count": 0,
  "approved_hypotheses": [],
  "validation_completed": null,
  "validation_count": 0,
  "sprint_candidates": [],
  "backlog_candidates": [],
  "delivery_completed": null,
  "tickets_created": []
}
```

`approved_hypotheses` — set at Gate 1 confirmation (list of hypothesis titles).
`sprint_candidates` — set at Gate 2 confirmation.
`backlog_candidates` — set at Gate 2 confirmation.

**Phase resolution rules:**
- File missing → start Discovery, create state file
- `cycle_month` ≠ current month → reset to Discovery for new month
- `discovery_completed` null → run Discovery
- `discovery_completed` set AND `approved_hypotheses` empty → re-present Gate 1, await approval
- `approved_hypotheses` set AND `validation_completed` null → run Validation
- `validation_completed` set AND `sprint_candidates` empty → re-present Gate 2, await approval
- `sprint_candidates` set AND `delivery_completed` null → run Delivery
- All three completed → report done

---

## Multi-Step Reasoning Protocol

Apply at every major decision point. Document in `outputs/growth-engineer/cycle-log.md`.

```
REASON(decision_point):
  1. ENUMERATE   — list all candidates without filtering
  2. EVIDENCE    — for each: supporting evidence, contradicting evidence, source strength
  3. IMPACT      — funnel stage affected, % users impacted, metric delta magnitude
  4. SCOPE       — quick win (≤3 SP) or backlog (>3 SP)?
  5. CONTRADICT  — does market intel conflict with Confluence research? resolve explicitly
  6. RANK        — priority score = confidence × impact × scope
  7. SELECT      — name top candidates with one-line justification each
  8. CONFIDENCE  — state overall confidence (High/Medium/Low) and why
```

---

## Discovery — Signal Collection

### Step 1 — Detect and read screenshot
Scan `inputs/screenshots/` for image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`).
If none found → **halt**: "No screenshot found in `inputs/screenshots/`. Drop your Domo screenshot there and re-run."

Read each image visually. Extract KPI cards, funnel charts, weekly bars.
Record metrics with confidence (High/Medium/Low — per `05-funnel-monitor` rules).

### Step 2 — Spawn funnel-monitor agent
Invoke `05-funnel-monitor` as a sub-agent. Pass screenshot context.
Agent runs full sequence → writes pipeline outputs → updates Confluence sections 1–6, 8.

### Step 3 — Spawn market-intel agent
Invoke `06-market-intel` as a sub-agent.
Focuses on funnel stages flagged as weak in Step 2.

### Step 4 — REASON(): initial hypothesis triage
Apply REASON() to hypotheses from `outputs/funnel-monitor/validation-hypotheses.md`.
Select 3–5 hypotheses worth deep-validating in Validation.

Triage criteria:
- Prioritise where market signals corroborate funnel signal
- Exclude suspicious metrics
- Prefer checkout, payment, cart (highest revenue impact)
- Flag one wildcard (lower confidence, high potential if validated)

Write reasoning to `outputs/growth-engineer/cycle-log.md`.

### Step 5 — Update Confluence: add "Hypotheses Under Review" section
Append to page `64742948865` (after Team Actions, before Data Quality Notes):

```
## Hypotheses Under Review — {date}
Review these before the next run. Hypotheses will be validated in Validation.

| # | Hypothesis | Funnel Stage | Metric | Signal Strength | Recommended |
|---|---|---|---|---|---|
| H1 | ... | Checkout | cart→checkout CTR | High — market signal corroborates | ✓ Proceed |
| H2 | ... | Auth | sign-in rate | Medium | ✓ Proceed |
| H3 | ... | PDP | search CVR | Medium | ✓ Proceed |
| H4 | ... | Payment | failure rate | Low | ⚠ Wildcard |

_Run `/growth-engineer` with next week's screenshot to confirm selection and begin Validation._
```

### Step 6 — Post Teams notification (Gate 1)
If `teams.enabled` is true, post Adaptive Card to `teams.webhook_url`:

```json
{
  "type": "message",
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.2",
      "body": [
        {
          "type": "TextBlock",
          "size": "Large",
          "weight": "Bolder",
          "text": "📊 Growth Cycle {YYYY-MM} — Discovery Complete"
        },
        {
          "type": "TextBlock",
          "text": "**Funnel signal:** {one-sentence dominant signal}",
          "wrap": true
        },
        {
          "type": "TextBlock",
          "text": "**Top risks this week:**",
          "weight": "Bolder"
        },
        {
          "type": "FactSet",
          "facts": [
            { "title": "R1 — {funnel stage}", "value": "{risk description} · Severity: High" },
            { "title": "R2 — {funnel stage}", "value": "{risk description} · Severity: High" },
            { "title": "R3 — {funnel stage}", "value": "{risk description} · Severity: Medium" }
          ]
        },
        {
          "type": "TextBlock",
          "text": "Review on Confluence, then open Claude Code and run `/growth-engineer` to confirm selection and begin Validation.",
          "wrap": true,
          "color": "Accent"
        }
      ],
      "actions": [
        {
          "type": "Action.OpenUrl",
          "title": "Review Hypotheses on Confluence",
          "url": "https://sephora-asia.atlassian.net/wiki/pages/64742948865"
        }
      ]
    }
  }]
}
```

### Step 7 — Delete screenshot and update state
Delete all images from `inputs/screenshots/`.
Write `cycle-state.json`: `discovery_completed: {today}`, `discovery_hypotheses_count: N`.
Do NOT set `approved_hypotheses` yet — that is set at Gate 1.

### Discovery output to chat
```
Discovery complete — {date}

Funnel signal: {one sentence}
Metrics extracted: {N} | Suspicious excluded: {N}
Hypotheses generated: {N} | Market signals: {N}

Proposed for Validation:
  H1 — {title} ({funnel stage}, confidence: High)
  H2 — {title} ({funnel stage}, confidence: Medium)
  H3 — {title} ({funnel stage}, confidence: Medium)
  H4 — {title} ({funnel stage}, confidence: Low — wildcard)

Confluence updated: {page URL}

--- GATE 1 ---
Review the "Hypotheses Under Review" section on Confluence.
Drop next week's screenshot into inputs/screenshots/ and run /growth-engineer.
You will be asked to confirm which hypotheses to take into Validation.
```

---

## Validation

### Step 1 — Gate 1: confirm hypotheses
Present Discovery hypotheses from `cycle-state.json` (or re-read from `validation-hypotheses.md`):

```
Gate 1 — Hypothesis confirmation

Discovery proposed:
  H1 — {title} | Stage: {stage} | Confidence: High
  H2 — {title} | Stage: {stage} | Confidence: Medium
  H3 — {title} | Stage: {stage} | Confidence: Medium
  H4 — {title} | Stage: {stage} | Confidence: Low (wildcard)

Which hypotheses should proceed to validation?
Reply: "all" | hypothesis numbers e.g. "H1, H2, H3" | "H1, H2, H3 — remove H4"
```

**Wait for human response.** Do not proceed until confirmed.
Record approved list in `cycle-state.json` → `approved_hypotheses`.

### Step 2 — Detect screenshot
Same as Discovery Step 1. If no screenshot → halt with message.

### Step 3 — Spawn funnel-monitor agent (update run)
Re-run `05-funnel-monitor`. Action Impact section tracks whether Discovery signals persisted.
Updates Confluence sections 1–6, 8. Updates `pipeline-context.md` + `validation-hypotheses.md`.

### Step 4 — Spawn validation agent
Invoke `07-validation` as a sub-agent.
Scope: approved hypotheses from `approved_hypotheses` only.

### Step 5 — REASON(): validation review
Apply REASON() to `outputs/validation/validated-hypotheses.md`.

Ask explicitly:
- Did Validation funnel data move in the predicted direction for each hypothesis?
- Did any hypothesis lose support (metric recovered → deprioritise)?
- Are Sprint Candidates genuinely ≤3 SP based on validation output?

Revise ranking, document in cycle log.

### Step 6 — Update Confluence: replace with "Validated Hypotheses" section
Replace the "Hypotheses Under Review" section on page `64742948865` with:

```
## Validated Hypotheses — {date}

### Sprint Candidates (quick wins — ≤3 SP)
| # | Hypothesis | Stage | Confidence | Priority Score | SP Est. |
|---|---|---|---|---|---|
| H1 | ... | Checkout | High | 18/27 | 2 |
| H2 | ... | Auth | Medium | 12/27 | 3 |

### Backlog Candidates (>3 SP — for monthly product review)
| # | Hypothesis | Stage | Confidence | SP Est. |
|---|---|---|---|---|

_Pending sprint candidate approval. Run `/growth-engineer` with Delivery screenshot to confirm and create tickets._
```

### Step 7 — Post Teams notification (Gate 2) + delete screenshot
If `teams.enabled` is true, post Adaptive Card to `teams.webhook_url`:

```json
{
  "type": "message",
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.2",
      "body": [
        {
          "type": "TextBlock",
          "size": "Large",
          "weight": "Bolder",
          "text": "✅ Growth Cycle {YYYY-MM} — Validation Complete"
        },
        {
          "type": "TextBlock",
          "text": "**Risk register — validated this week:**",
          "weight": "Bolder"
        },
        {
          "type": "FactSet",
          "facts": [
            { "title": "R1 — {funnel stage}", "value": "{risk description} · Status: Confirmed · Priority: {score}/27" },
            { "title": "R2 — {funnel stage}", "value": "{risk description} · Status: Confirmed · Priority: {score}/27" }
          ]
        },
        {
          "type": "TextBlock",
          "text": "**Backlog candidates ({N} items)** queued for monthly product review.",
          "wrap": true
        },
        {
          "type": "TextBlock",
          "text": "Open Claude Code and run `/growth-engineer` to approve Sprint Candidates and begin Delivery (Jira ticket creation).",
          "wrap": true,
          "color": "Accent"
        }
      ],
      "actions": [
        {
          "type": "Action.OpenUrl",
          "title": "View Validated Hypotheses on Confluence",
          "url": "https://sephora-asia.atlassian.net/wiki/pages/64742948865"
        }
      ]
    }
  }]
}
```

Delete screenshot.
Write `cycle-state.json`: `validation_completed: {today}`, `validation_count: N`.

### Validation output to chat
```
Validation complete — {date}

Validated: {N} hypotheses
Confluence updated with ranked results: {page URL}

--- GATE 2 ---
Sprint Candidates (proposed for Jira quick-win stories):
  H1 — {title} | Confidence: High | Priority: 18/27 | ~2 SP
  H2 — {title} | Confidence: Medium | Priority: 12/27 | ~3 SP

Backlog Candidates (proposed for monthly review):
  H3 — {title} | Confidence: Medium | ~5 SP
  H4 — {title} | Confidence: Low | ~8 SP

Confirm Sprint Candidates and/or modify before Delivery creates Jira tickets.
Reply: "approved" | or specify changes e.g. "move H2 to backlog, keep H1"
```

**Wait for human response.** Do not proceed to Delivery until Gate 2 is confirmed.
Record in `cycle-state.json` → `sprint_candidates` and `backlog_candidates`.

---

## Delivery — Action

### Step 1 — Re-confirm Gate 2 selection
Print the approved Sprint Candidates and Backlog Candidates from `cycle-state.json`.
Ask: "Confirmed — creating Jira tickets for: {list}. Proceed? (yes / make changes)"
Wait for final confirmation.

### Step 2 — Detect screenshot
Same as Discovery Step 1. If no screenshot → halt with message.

### Step 3 — Spawn funnel-monitor agent (final update)
Re-run `05-funnel-monitor`. Action Impact tracks Discovery + Validation signal persistence.

### Step 4 — Spawn github-reader agent
Invoke `08-github-reader` as a sub-agent.
Scope: `sprint_candidates` only.

### Step 5 — REASON(): final action selection
Apply REASON() before ticket creation.

- After code reading, is each Sprint Candidate still ≤3 SP? Reclassify if not.
- Does the code context reveal risk not visible from data alone?
- Are acceptance criteria achievable in a single PR?

If any Sprint Candidate is reclassified to backlog → notify human before proceeding:
> "H{N} was reclassified to backlog after code reading ({reason}, estimated {SP} SP). Proceed with remaining {N} quick wins?"
Wait for confirmation.

### Step 6 — Spawn jira-writer agent
Invoke `09-jira-writer` as a sub-agent.
Passes `sprint_candidates` and `backlog_candidates`.

### Step 7 — Update Confluence: replace with "Sprint Actions" section
Replace the "Validated Hypotheses" section with:

```
## Sprint Actions — {date}

### Quick-win stories (sprint)
- [{BAAPP-N}] {summary} — {SP} SP
- [{BAAPP-N}] {summary} — {SP} SP

### Backlog stories (monthly product review)
- [{BAAPP-N}] {summary}

### Cycle summary
[{BAAPP-N}] [Growth] Cycle {YYYY-MM} W3 — Sprint Actions
```

### Step 8 — Post Teams notification (Delivery close) + delete screenshot
If `teams.enabled` is true, post Adaptive Card to `teams.webhook_url`:

```json
{
  "type": "message",
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
      "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
      "type": "AdaptiveCard",
      "version": "1.2",
      "body": [
        {
          "type": "TextBlock",
          "size": "Large",
          "weight": "Bolder",
          "text": "🎯 Growth Cycle {YYYY-MM} — Closed"
        },
        {
          "type": "TextBlock",
          "text": "**Risk register — addressed this cycle:**",
          "weight": "Bolder"
        },
        {
          "type": "FactSet",
          "facts": [
            { "title": "R1 — {funnel stage}", "value": "{risk description} → {BAAPP-N} · {SP} SP" },
            { "title": "R2 — {funnel stage}", "value": "{risk description} → {BAAPP-N} · {SP} SP" }
          ]
        },
        {
          "type": "TextBlock",
          "text": "**Backlog ({N} items)** queued for product review.",
          "wrap": true
        },
        {
          "type": "TextBlock",
          "text": "Next cycle starts {first Thursday of next month}.",
          "isSubtle": true
        }
      ],
      "actions": [
        {
          "type": "Action.OpenUrl",
          "title": "View Sprint Actions on Confluence",
          "url": "https://sephora-asia.atlassian.net/wiki/pages/64742948865"
        },
        {
          "type": "Action.OpenUrl",
          "title": "View Epic in Jira",
          "url": "https://sephora-asia.atlassian.net/browse/BAAPP-461"
        }
      ]
    }
  }]
}
```

Delete screenshot.
Write `cycle-state.json`: `delivery_completed: {today}`, `tickets_created: [...]`.

### Delivery output to chat
```
Growth cycle {YYYY-MM} closed — {date}

Quick-win stories created ({N}):
  {BAAPP-N} — {summary} ({SP} SP)

Backlog stories created ({N}):
  {BAAPP-N} — {summary}

Cycle summary: {BAAPP-N}
Confluence updated: {page URL}

Next cycle starts {first Thursday of next month}.
Drop a screenshot then and run /growth-engineer.
```

---

## Output Contract

### `outputs/growth-engineer/cycle-state.json` — overwrite each week (schema above)
### `outputs/growth-engineer/cycle-log.md` — **append only**, never overwrite

Sub-agent outputs:
- `outputs/funnel-monitor/` — overwrite per run
- `outputs/funnel-monitor/memory/metrics-history.json` — append only
- `outputs/market-intel/signals.md` — overwrite Discovery
- `outputs/validation/validated-hypotheses.md` — overwrite Validation
- `outputs/github-reader/code-context.md` — overwrite Delivery
- `outputs/jira-writer/created-tickets.md` — overwrite Delivery

---

## Configuration
Reads from `config/atlassian.yml` → `config/atlassian.team.yml` → `config/atlassian.local.yml`.
Keys used: `growth_agent.screenshot_watch_folder`, `growth_agent.epic_key`, `funnel_monitor_page_id`, `github.org`.

## Permissions
- Read + delete: `inputs/screenshots/`
- Read/write: `outputs/growth-engineer/`
- Write: Confluence page `64742948865` (sections only — does not overwrite full page)
- Spawn: agents 05, 06, 07, 08, 09

## Error Handling
- No screenshot → halt with message, do not proceed
- Gate response is ambiguous → ask for clarification, do not assume approval
- `cycle-state.json` corrupt → reset to Discovery, log reset
- Sub-agent fails → halt, report which agent and its error message
- Sprint Candidate reclassified in W3 → notify human, await confirmation before ticket creation
- All weeks completed → "Cycle {YYYY-MM} complete. Next cycle starts {date}."
- Out-of-order run (Delivery before Validation approved) → refuse, show current state and what's needed
