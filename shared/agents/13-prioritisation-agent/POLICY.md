# 13-prioritisation-agent — Policy

## Role in pipeline

Agent 13 of the Phase 1 Intelligence Loop. Runs after the shared diagnosis artifact has been built from Agent 11 and Agent 12 outputs.

Connects the cycle signal to each hypothesis and its experiment design. Ranks experiments so the PM can decide which to proceed with. Creates Jira stories for approved experiments and publishes a Confluence summary page with Jira links. Nothing goes to Jira or Confluence without PM approval at the gate.

```
outputs/signal-agent/pipeline-context.md     ──┐
outputs/diagnosis/diagnosis.json             ──┤
outputs/validation/experiment-designs.json   ──┤──▶  13-prioritisation-agent
outputs/prioritisation/ranked-hypotheses.json──┤         │
  (history — lineage)                          │         │
outputs/inspiration/bet-log.json  (optional) ──┘         │
  (Agent 20 — market context + PM odds)                   │
                                              *** PM GATE (approve experiments) ***
                                                          │
                              ┌───────────────────────────┼──────────────────────────┐
                              ↓                           ↓                          ↓
              Jira stories (one per              outputs/prioritisation/      Confluence page
              approved experiment)               ranked-hypotheses.json       PI space — ranked
              under epic_key                     (append)                     experiments + Jira links
                                                 ranked-hypotheses.md
                                                 (overwrite)
                                                 needs-spike.md (overwrite)
```

## Trigger

Spawned by `/intelligence-loop` after `outputs/diagnosis/diagnosis.json` has been built.
Standalone: "prioritise experiments", "rank hypotheses", "run prioritisation".

---

## Output Contract

### `outputs/prioritisation/ranked-hypotheses.json`
**Append-only** — one entry per cycle run. Never overwrite history.

```json
{
  "run_date": "YYYY-MM-DD",
  "cycle_signal": "description from pipeline-context.md",
  "pm_approved": true,
  "approved_ids": ["H1", "H4", "H2"],
  "confluence_page_id": "64768147490",
  "confluence_page_url": "https://sephora-asia.atlassian.net/spaces/PI/pages/...",
  "entries": [
    {
      "rank": 1,
      "failure_id": "H1",
      "description": "hypothesis description",
      "market": "AU",
      "signal_connected": "ATC rate -21% WoW AU",
      "experiment_summary": "one-line description of the A/B test",
      "sp_estimate": 2,
      "sprint_viable": true,
      "confidence_score": 3,
      "confidence_source": "Agent 12 — High",
      "impact_score": 3,
      "impact_source": "Agent 12 — High / hard block",
      "scope_score": 2,
      "scope_source": "Agent 12 — SP 2 / Moderate",
      "priority_score": 18.0,
      "jira_created": true,
      "jira_ticket": "BAAPP-463",
      "jira_url": "https://sephora-asia.atlassian.net/browse/BAAPP-463",
      "deployed_date": null,
      "post_deploy_metric_delta": null,
      "pending_data_validation": false,
      "needs_spike": false,
      "inspiration_market_context": null,
      "inspiration_pm_odds": null,
      "lineage": {
        "first_seen_date": "YYYY-MM-DD",
        "times_ranked": 1,
        "times_actioned": 1,
        "cycles_unactioned": 0
      }
    }
  ]
}
```

### `outputs/prioritisation/ranked-hypotheses.md`
**Overwrite** each run. Standardised signal→hypothesis→experiment table.

### `outputs/prioritisation/needs-spike.md`
**Overwrite** each run. Emergent hypotheses or entries where no experiment design exists.

### `outputs/jira-writer/created-tickets.md`
**Overwrite** each run. Log of all Jira stories created this cycle.

---

## Configuration

```yaml
# config/atlassian.yml
space_name: "PI"
page_id: "64742785027"          # parent for Confluence page creation

growth_agent:
  jira_project_key: "BAAPP"
  epic_key: "BAAPP-461"
  story_labels: ["growth-agent", "quick-win", "intelligence-loop"]
  backlog_label: "growth-backlog"
```

## Permissions

- Read: `outputs/signal-agent/pipeline-context.md`
- Read: `outputs/validation/experiment-designs.json`
- Read: `outputs/validation/read-audit.log` — **required for code grounding check; absence blocks all Jira creation**
- Read: `outputs/prioritisation/ranked-hypotheses.json` (history)
- Read: `outputs/inspiration/bet-log.json` — **optional enrichment from Agent 20; absence or staleness is non-blocking**
- Read: `config/atlassian.yml`, `config/atlassian.team.yml`, `config/atlassian.local.yml`
- Write: `outputs/prioritisation/ranked-hypotheses.json` (append-only)
- Write: `outputs/prioritisation/ranked-hypotheses.md` (overwrite)
- Write: `outputs/prioritisation/needs-spike.md` (overwrite)
- Write: `outputs/jira-writer/created-tickets.md` (overwrite)
- Write: Jira stories under configured `epic_key` — **only after PM approval**
- Write: Confluence page in configured `space_name` under `page_id` — **only after PM approval**
- No writes to any repo or memory file

## Error Handling

| Error | Action |
|---|---|
| `experiment-designs.json` missing | Halt — "Run Steps 1–2 of intelligence loop first" |
| `pipeline-context.md` missing | Halt — "Run Step 1 of intelligence loop first" |
| `read-audit.log` missing | Hard block all Jira creation — "Code review audit log missing. Cannot verify code grounding." Surface to PM; route all approved stories to needs-spike.md |
| All files for a story are unverified (not in audit log) | Hard block that story — route to needs-spike.md; surface to PM at Step 5a gate; do not create Jira story |
| All grep_anchors for a story fail re-verification | Hard block that story — route to needs-spike.md |
| Confidence = Low for an approved story | Hard block that story — route to needs-spike.md |
| Partially verified files | Proceed with verified files only in "Where in the code"; exclude unverified paths |
| Experiment has no signal connection | Note gap; include in ranked output with "signal not mapped" flag |
| Emergent hypothesis has no experiment design | Place in needs-spike.md with reason |
| Scores missing for an entry | Set confidence = Low, impact = Low; note "scores absent" |
| No history file | First run — initialise lineage from scratch |
| `bet-log.json` absent or stale | Skip Agent 20 enrichment silently |
| Agent 20 `target_metric` matches no hypothesis | Load enrichment but do not apply; note in ranked-hypotheses.md header |
| PM responds "skip jira" | Record prioritisation only; set `jira_created: false`; skip Steps 6–7 |
| Jira create returns 401 | Report credentials error; do not retry |
| Jira create returns 400 | Log error with response body; skip that story; continue with remaining |
| `priority` field in Jira additional_fields causes error | Remove `priority` from additional_fields — omit entirely |
| `parent.key` in Jira additional_fields causes error | Use `epicKey` field instead of `parent` |
| Confluence create fails | Log error; local outputs still written; note Confluence step failed in created-tickets.md |
| `create_jira_stories.py` exits 3 (input missing) | Halt Jira creation — surface missing file to PM |
| `create_jira_stories.py` exits 2 (config error) | Halt — check `config/atlassian.yml` project/epic keys |
| `raise_github_pr.py` exits 2 (no raise-PR comment) | Surface to PM: "No 'raise PR -> {repo}' comment found on ticket" |
| `raise_github_pr.py` exits 3 (unknown repo) | Surface to PM with list of known repos |
| GitHub MCP returns 403 | Surface to PM: "No write access to {repo} via configured MCP token." |
| GitHub branch already exists | Surface to PM: "Branch {branch} already exists. Delete it or use a different ticket." |
| All entries in needs-spike | Surface to PM: "No scoreable experiments this cycle." |
| `outputs/prioritisation/` missing | Create directory before writing |
| `outputs/jira-writer/` missing | Create directory before writing |

---

## Self-Anneal (run after every execution)

Append one entry to `outputs/prioritisation/run-log.json` (create with `[]` if absent):

```json
{
  "run_at": "YYYY-MM-DDTHH:MM",
  "outcome": "success | partial | failed",
  "failures": ["Step N: what broke and why"],
  "constraints_discovered": ["e.g. epicKey field causes 400 — use parent.key instead for project X"]
}
```

If `failures` or `constraints_discovered` is non-empty:
- Update PROCEDURE.md with the new constraint (Jira field validation, Confluence auth, config key)
- If a script broke: fix it, test it, record the fix in `failures`
- Do not discard errors silently — this directive must reflect what the system has learned
