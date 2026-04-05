# /intelligence-loop — Intelligence Loop Orchestrator (Skill)

## What this skill does
Runs the full Phase 1 intelligence loop in the main conversation context.
It orchestrates Agent 10 for signal detection, Agent 11 and Agent 12 for diagnosis inputs,
materialises the shared diagnosis artifact, then runs Agent 20 (inspiration scout) to produce
PM-sourced prototype ideas, and finally Agent 13 and Agent 15 to prioritise both diagnosis-derived
and inspiration-sourced hypotheses.

The orchestrator must keep signal, diagnosis, hypothesis, and prioritisation distinct.
Do not skip PM gates. Do not collapse diagnosis directly into experiment design.

---

## Sequence

### Step 1 — Run Agent 10 and stop at PM gate
1. Read `.claude/agents/10-signal-agent/SKILL.md`
2. Execute the signal workflow exactly as defined there
3. Wait for explicit PM confirmation of the signal list
4. If the PM does not confirm signals, park the loop and stop

### Step 2 — Run Agent 11 and Agent 12 from the confirmed signal set
1. Read `.claude/agents/11-feedback-agent/SKILL.md`
2. Read `.claude/agents/12-validation-agent/SKILL.md`
3. Run both against the confirmed signal set from `outputs/signal-agent/pipeline-context.md`
4. Treat their outputs as diagnosis inputs, not as prioritisation-ready conclusions

Expected local outputs before diagnosis build:
- `outputs/feedback/findings.md`
- `outputs/validation/experiment-designs.json`
- `outputs/signal-agent/pipeline-context.md`

### Step 3 — Build the shared diagnosis artifact
1. Read `directives/assemble_diagnosis_input.md`
2. Run:

```bash
python3 execution/assemble_diagnosis_input.py \
   --pipeline outputs/signal-agent/pipeline-context.md \
   --findings outputs/feedback/findings.md \
   --experiments outputs/validation/experiment-designs.json \
   --output .tmp/diagnosis-input.json
```

3. Read `directives/build_diagnosis_artifact.md`
4. Run:

```bash
python3 execution/build_diagnosis_artifact.py \
  --input .tmp/diagnosis-input.json \
  --json-output outputs/diagnosis/diagnosis.json \
  --markdown-output outputs/diagnosis/diagnosis.md
```

5. If either assembly or diagnosis build fails, halt before Agent 20

### Step 4 — Run Agent 20 after diagnosis exists
1. Read `.claude/agents/20-inspiration-scout/SKILL.md`
2. **Agent 20 now reads the diagnosis artifact** as context for scouting
3. Execute the inspiration scout workflow:
   - Load diagnosis to understand what's broken
   - Browse sephora.com current UX state
   - Run scoped market scan
   - Facilitate PM Gate 1: pre-mortem + prototype idea based on diagnosis context
   - Record bets to `outputs/inspiration/bet-log.json`
4. If PM does not confirm prototype idea, re-surface Gate 1 and wait

Expected output:
- `outputs/inspiration/bet-log.json` (appended with new bets)
- `outputs/inspiration/cycle-state.json` (marked complete)

### Step 5 — Run Agent 13 only after diagnosis and bets exist
1. Read `.claude/agents/13-prioritisation-agent/SKILL.md`
2. Run prioritisation using:
   - `outputs/signal-agent/pipeline-context.md`
   - `outputs/diagnosis/diagnosis.json`
   - `outputs/validation/experiment-designs.json`
   - `outputs/inspiration/bet-log.json` (if it exists — new bets from Agent 20)
3. Agent 13 will rank both diagnosis-derived hypotheses and inspiration-sourced bets using C×I×S framework
4. Respect the PM approval gate before any Jira or Confluence write

### Step 6 — Run Agent 15 after prioritisation
1. Read `.claude/agents/15-trend-escalation-agent/SKILL.md`
2. Run trend and escalation only after Agent 13 completes successfully

---

## Hard gates

- No PM-confirmed signals → do not run Agents 11 or 12
- No diagnosis artifact → do not run Agent 20 or Agent 13
- No PM approval at prioritisation gate → do not create Jira stories

---

## Output contract

Overwrite each run:
- `outputs/signal-agent/signals.md`
- `outputs/signal-agent/pipeline-context.md`
- `outputs/diagnosis/diagnosis.json`
- `outputs/diagnosis/diagnosis.md`
- `outputs/validation/experiment-designs.json`
- `outputs/validation/experiment-designs.md`
- `outputs/prioritisation/ranked-hypotheses.md`
- `outputs/trend/signal-trend.json`
- `outputs/trend/trend-report.md`

Append-only:
- `outputs/feedback/findings-store.json`
- `outputs/prioritisation/ranked-hypotheses.json`

---

## Error handling

| Failure | Action |
|---|---|
| Agent 10 has no confirmed signals | Stop after PM gate; do not continue |
| Agent 11 missing evidence | Follow Agent 11 hard-stop rules; do not infer missing evidence |
| Agent 12 cannot localise mechanism | Surface uncertainty in diagnosis input; do not skip diagnosis |
| Diagnosis builder validation fails | Halt before Agent 13 and show the validation error |
| Agent 13 sees missing `diagnosis.json` | Halt and build diagnosis first |
