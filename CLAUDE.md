# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PM diagnostic tool with 2 complementary loops for SEA ecommerce PMs across all KPIs and markets (SG, MY, AU, NZ, PH, HK, TH, ID):

**Intelligence Loop (Phase 1 — active):** 4-step diagnostic loop.
1. **Signal** — query configured Domo KPI datasets; surface which metrics moved, where, by how much
2. **Diagnose** — two parallel sub-steps: (2a) Domo feedback datasets for corroborating voice-of-customer evidence; (2b) independent code review to localise the failure and map mechanisms
3. **Hypothesise** — convert the favored diagnosis into rival-tested, falsifiable hypotheses and A/B experiment designs
4. **Prioritise** — score and rank experiments by confidence × impact × scope; PM approves which advance

**Inspiration Loop (active — parallel to Phase 1):** PM-triggered ideation loop that produces prototype bets.
1. **Scout** — load Agent 10 signals (what's broken) + browse SEA frontends (what we have today) + scoped market scan (what's possible)
2. **Gate 1** — PM confirms pre-mortem scenario and prototype idea; bet recorded with target metric and odds
3. **Classify** — bet classified by type (pain / shine / pain+shine); drives downstream loop investment
4. Downstream: prototype builder → launch validator → fit tracker (agents 22–24, in design)

Both loops feed Agent 13: the Intelligence Loop provides a diagnosis artifact plus code-grounded experiment designs; the Inspiration Loop provides market context and PM odds as optional enrichment for scoring and tiebreaking.

Every gate is human-approved. Domo evidence absence is a hard stop — the system halts and asks, it does not infer. Phase 2 adds the action layer (GitHub effort estimation + Jira story creation) once Phase 1 is proven.

## Operating Model

This repo uses a 3-layer architecture that separates concerns to maximise reliability. LLMs are probabilistic; business logic is deterministic. This system fixes that mismatch.

### 3-Layer Architecture

**Layer 1 — Directive (What to do)**
SOPs written in Markdown, living in `directives/` and agent `SKILL.md` files. Define goals, inputs, tools/scripts to use, outputs, and edge cases. Natural language instructions, like you'd give a mid-level employee.

**Layer 2 — Orchestration (Decision making)**
This is Claude. Job: intelligent routing. Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings. Claude is the glue between intent and execution — don't try to do the work manually, read the directive and run the right script.

**Layer 3 — Execution (Doing the work)**
Deterministic scripts in `execution/` (Python) and `scripts/` (Node). Handle API calls, data processing, file operations. Reliable, testable, fast. Use scripts instead of manual work.

**Why this works:** if Claude does everything itself, errors compound. 90% accuracy per step = 59% success over 5 steps. Push complexity into deterministic code so Claude can focus on decision-making.

### Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per the relevant directive. Only create new scripts if none exist.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits — check with user first)
- Update the directive with what you learned (API limits, timing, edge cases)

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations — update the directive. Don't create or overwrite directives without asking unless explicitly told to.

**4. Optimise for context window**
- Apply `directives/context_window_budget.md` on all multi-step runs
- Load minimum scope first (directive + script + active outputs), then expand only when blocked
- Prefer deterministic summarisation in `execution/` over long narrative reasoning
- Avoid replaying unchanged history; reference prior artifacts and record only deltas

### Self-annealing loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test the tool, make sure it works
4. Update directive to include the new flow
5. System is now stronger

### File Organisation

**Deliverables vs Intermediates:**
- **Deliverables**: Confluence pages, Google Sheets/Slides, or other cloud outputs the user can access
- **Intermediates**: Temporary files needed during processing

**Directory structure:**
- `.tmp/` — All intermediate files (scraped data, temp exports). Never commit, always regenerated.
- `execution/` — Python scripts (deterministic tools)
- `directives/` — SOPs in Markdown (the instruction set)
- `scripts/` — Node.js scripts (e.g. Puppeteer capture)
- `.env` — Environment variables and API keys (git-ignored)
- `outputs/` — Agent-generated files (operational data)

**Key principle:** Local files are only for processing. Deliverables live in cloud services (Confluence, Google Sheets, etc.) where the user can access them. Everything in `.tmp/` can be deleted and regenerated.

### Cloud Webhooks (Modal)

Supports event-driven execution via Modal webhooks. Each webhook maps to exactly one directive with scoped tool access.

When adding a webhook:
1. Read `directives/add_webhook.md` for complete instructions
2. Create the directive file in `directives/`
3. Add entry to `execution/webhooks.json`
4. Deploy: `modal deploy execution/modal_webhook.py`
5. Test the endpoint

Key files: `execution/webhooks.json`, `execution/modal_webhook.py`, `directives/add_webhook.md`

### Model preference

Use the latest Claude model optimised for reasoning and coding. Currently `claude-opus-4-6`. Update this note when a newer reasoning-optimised model supersedes it.

## Architecture

Full architecture with diagrams, state/persistence model, config registry, and architectural decisions: `_bmad-output/planning-artifacts/architecture.md`

### Active loops

| Loop | Trigger | Agents | Status |
|---|---|---|---|
| Intelligence Loop | `/intelligence-loop` | 10 → 11+12 → diagnosis artifact → 20 (inspiration scout reads diagnosis) → bets → 13 → 15 (PM gates at each step) | Active |
| Inspiration Loop | `/inspiration-loop` | Spawned by intelligence loop after diagnosis; Agent 20 scouts prototype ideas grounded in diagnosis context | Active (Agent 20 live) |
| Action Layer | `/growth-engineer` | 05 → 06 → 07 → 08 → 09 (gates at each week) | Not yet active |
| Weekly Refresh | `/weekly-refresh` | 14 | Active (background) |

## Available Agents

Agent locations are governed by `config/agents.yml` (the registry). Resolve all agent paths from there — never hardcode paths in skills or directives.

**Shared agents** (`shared/agents/`) — used by more than one project:

| Agent | Trigger | Consumed by | Description |
|---|---|---|---|
| `13-prioritisation-agent` | spawned by loop | intelligence-loop, inspiration-loop | C×I×S scoring; code grounding; Jira; lineage; uses `score_hypotheses.py`, `verify_code_grounding.py`, `resolve_config.py` |
| `14-weekly-refresh` | `/weekly-refresh` | intelligence-loop | Background findings store refresh |

**Intelligence Loop** (`projects/intelligence-loop/agents/`):

| Agent | Trigger | Description |
|---|---|---|
| `10-signal-agent` | `/intelligence-loop` | KPI signal from Domo; PM gate. Hidden: `/sharpen` |
| `11-feedback-agent` | spawned by loop | Domo feedback triangulation; contributes evidence to diagnosis artifact; uses `check_findings_cache.py` |
| `12-validation-agent` | spawned by loop | Local codebase survey; localises mechanism; derives hypotheses and A/B designs; uses `score_hypotheses.py`, `index_repos.py` |
| `15-trend-escalation-agent` | spawned after 13 | Priority debt + escalation; uses `calculate_priority_debt.py` |

**Inspiration Loop** (`projects/inspiration-loop/agents/`):

| Agent | Trigger | Description |
|---|---|---|
| `20-inspiration-scout` | `/inspiration-loop` | Signal + frontend browse + market scan; PM Gate 1; produces bet-log for intelligence loop input; uses `check_signals_staleness.py` |

**Action Layer** (`projects/action-layer/agents/`) — not yet active:

| Agent | Trigger | Description |
|---|---|---|
| `05-funnel-monitor` | `/funnel-monitor` | Weekly ecommerce funnel report (Thu→Wed) |
| `06-market-intel` | `/market-intel` | SEA web + social scanner |
| `07-validation` | `/validate-hypotheses` | Confluence research + synthetic user modeling; uses `score_hypotheses.py` |
| `08-github-reader` | `/github-reader` | Code context per hypothesis; uses `index_repos.py` |
| `09-jira-writer` | `/jira-writer` | Jira story creation; uses `resolve_config.py` |

## Skills (orchestrators)

Skills are **Layer 1 directives** that live in `.claude/skills/`. They define which agents to spawn, in what order, with what gates. Skills delegate to agents; agents delegate to `execution/` scripts. This table is a registry — orchestration logic lives in each skill file.

```
Skill (Layer 1 — directive)  → which agents, what order, what gates
  Agent (Layer 1 — directive)  → what steps, what MCP calls, what scripts
    Script (Layer 3 — execution) → deterministic computation
```

| Skill | Trigger | Spawns |
|---|---|---|
| `intelligence-loop` | `/intelligence-loop` | 10 → 11+12 → 13 → 15 with PM gates |
| `inspiration-loop` | `/inspiration-loop` | 20 → 21 with PM Gate 1 |
| `growth-engineer` | `/growth-engineer` | 05 → (records bets → fed to intelligence loop)ith gates |
| `puppeteer` | `/puppeteer` | Runs `scripts/domo-capture.js` — automates Domo screenshot capture |

## Key Files & References

- `.mcp.json` — MCP credentials (git-ignored). See `directives/mcp_servers.md` for tool selection, scopes, and error handling.
- `config/agents.yml` — Agent registry. Maps agent IDs to paths; governs shared vs project scope. Resolve all agent paths from here.
- `config/atlassian.yml` — Atlassian defaults. Config layers resolved by `execution/resolve_config.py` — see `directives/resolve_config.md`.
- `config/domo.yml` — Domo registry, signal thresholds, PII exclusion list.
- `.claude/rules/` — Auto-loaded per context: `atlassian` (permissions), `agents` (conventions + overwrite/append list), `workspace-setup` (onboarding).
- `outputs/<agent-name>/` — Agent-generated files.
- `outputs/diagnosis/` — Shared diagnosis artifact between diagnosis and prioritisation stages.
- `directives/` — SOPs for all execution scripts and operational procedures.
- `execution/` — Deterministic Python scripts (Layer 3).
- `scripts/` — Node.js scripts (Puppeteer, etc.).

## Agent Cognition Model

**Context:** This directive governs the cognitive framework and optimization parameters for all agents within the diagnostic Orchestration and Execution layers.

**Objective:** To prevent agents from collapsing the distance between observation and explanation. Agents must optimize for disciplined causal interpretation, prioritizing the discovery of *latent conditions* over the patching of *active failures*.

---

### 1. Core Reasoning Constraints
All agents in this repository must apply the following logical constraints when processing data, generating hypotheses, or recommending actions.

### 1.1. Separate Observation from Interpretation
* **Rule:** Agents must strictly isolate raw signals from causal narratives. 
* **Enforcement:** "Adoption is down" is an observation. "Visibility is weak" is an interpretation. Agents must never treat an interpretation as a factual prior. 

### 1.2. Reject Proximate-Cause Fixation
* **Rule:** Agents must not assume the nearest visible bottleneck is the root cause. 
* **Enforcement:** If a metric drops at a specific UI step (the active failure), the agent must query upstream constraints (the latent conditions)—such as mental model mismatches, workflow design, policy ambiguity, or incentive structures—that made the failure likely.

### 1.3. Ban "Human Error" as a Terminal Diagnosis
* **Rule:** "User confusion" or "operator mistake" are labels, not explanations. 
* **Enforcement:** If an agent reaches a conclusion of human error, it must forcefully continue inquiry to explain *what system conditions made that mistake easy, likely, or hard to detect*.

---

### 2. Optimization Mandates for Hypothesis Generation
When the agent train is tasked with explaining a product symptom or metric anomaly, it must optimize its output according to the following rules:

* **Require Cross-Class Rival Explanations:** Agents must generate competing hypotheses that span different conceptual layers. Explanations must not all come from the same domain (e.g., all UI tweaks). They must span categories such as: Visibility, Value Ambiguity, Trust, Setup Effort, Segment Mismatch, and Organizational/Architecture Constraints.
* **Diagnosis Before Hypothesis:** Agents must first localise the failure, define affected segments, and articulate rival diagnoses before proposing a specific hypothesis or experiment.
* **Test for Counterfactual Strength:** An agent should only elevate a hypothesis if it passes the counterfactual test: *If this latent condition were different, would the outcome have materially changed?*
* **Test for Recurrence Leverage:** Agents must prioritize solutions that break the chain of failure systemically, rather than merely patching the local instance.

---

### 3. The "Six Question" Output Gate
No matter the specific tasks of the individual agents in the train, the final orchestrated output/recommendation provided to the user MUST explicitly resolve these six questions. **Enforced by Agent 13 (Prioritisation).** The Orchestrator agent must block final output until these are satisfied:

1. **The Observation:** What is the precise, uninterpreted data/trace?
2. **The Rivalry:** What are the top three rival explanations (spanning different causal classes)?
3. **The Counterfactual:** Which explanation has the strongest counterfactual impact?
4. **The Leverage:** Which explanation offers the most recurrence leverage (systemic fix vs. local patch)?
5. **The Falsification:** What specific evidence or metric trace would falsify our favored explanation?
6. **The Experiment Constraint:** (If proposing an experiment) How does the proposed experiment specifically discriminate *between* the rival explanations, rather than just testing a single solution?
