# /inspiration-loop — Inspiration Loop Orchestrator (Skill)

## What this skill does

Spawned by the Intelligence Loop after diagnosis is complete. Agent 20 (Inspiration Scout)
reads the diagnosis to understand what mechanism is broken, then scouts for prototype ideas
that could fix it by browsing current sephora.com UX and running a market scan.

The inspiration loop produces market context and PM-generated prototype ideas that feed
as alternative hypothesis candidates into Agent 13 (Prioritisation), where they are ranked
alongside diagnosis-derived hypotheses using the same C×I×S framework.

---

## Sequence

### Step 1 — Run Agent 20 after diagnosis exists

1. Read `.claude/agents/20-inspiration-scout/SKILL.md`
2. Execute the inspiration scout workflow:
   - Load diagnosis artifact to understand what's broken and why
   - Browse sephora.com in the relevant feature area to see current UX
   - Run scoped market scan to discover competitive solutions
   - Facilitate PM Gate 1: pre-mortem + prototype idea grounded in diagnosis context
   - Record bets to `outputs/inspiration/bet-log.json`
3. If PM does not confirm prototype idea and target metric, re-surface Gate 1 and wait

**Expected outputs:**
- `outputs/inspiration/bet-log.json` — appended with new bet entry
- `outputs/inspiration/cycle-state.json` — marked as `loop_completed: true`
- `outputs/inspiration/signal-brief.md` — overwritten with combined brief
- Confluence page (if enabled) — new child page under PI space

---

## Hard gates

- No PM-confirmed pre-mortem → do not advance
- No PM-confirmed prototype idea → do not advance
- No PM-confirmed target metric → do not advance

---

## Output contract

After Agent 20 completes (inspiration loop considered done):

Overwrite each run:
- `outputs/inspiration/signal-brief.md`
- `outputs/inspiration/cycle-state.json`

Append-only:
- `outputs/inspiration/bet-log.json` (one entry per inspiration loop run)

Confluence (if enabled):
- New page per run under PI space

---

## Integration with Intelligence Loop

```
Intelligence Loop:
  Step 1: Agent 10 (signal detection)
  Step 2: Agent 11+12 (diagnosis inputs)
  Step 3: Build diagnosis artifact
          ↓
  Step 4: Agent 20 (Inspiration Scout — reads diagnosis, produces bets)
          ↓
  Step 5: Agent 13 (Prioritisation — ranks diagnosis + bets together)
  Step 6: Agent 15 (Escalation)
```

Agent 13 receives:
- Diagnosis artifact (favored hypothesis + rivals from Agent 12)
- Bet-log from Agent 20 (PM prototype ideas + market context)

Both are evaluated using C×I×S (Confidence × Impact × Scope) and code-grounding rigor.

---

## Error handling

| Failure | Action |
|---|---|
| Diagnosis missing | Agent 20 halts; surface: run `/intelligence-loop` first |
| PM does not confirm Gate 1 (any field) | Re-surface Gate 1 prompts; wait for full confirmation |
| sephora.com inaccessible | Note in brief; proceed; do not fabricate |
| Web search no results | Note "No market signals found"; do not invent; proceed |
| bet-log.json corrupt | Recover: initialise with valid entries from backup or restart |
| Confluence write fails (401/403) | Surface to PM; instruct token rotation; halt until resolved |

---

## Configuration

```yaml
# config/atlassian.yml
inspiration_loop:
  signal_staleness_days: 7

teams:
  enabled: false
  notify_on:
    - inspiration_signal_ready
```

---

## Permissions

- Read: `outputs/diagnosis/diagnosis.md` and `diagnosis.json`
- Read: `outputs/signal-agent/signals.md` (optional context)
- Browse: `sephora.com` — visible UI only
- Web search: scoped to failure surface / mechanism
- Write: `outputs/inspiration/` (all files)
- Write: Confluence (new page per run under PI space, `page_id` from config)
- No Domo queries
- No Jira writes
- No source code inspection
