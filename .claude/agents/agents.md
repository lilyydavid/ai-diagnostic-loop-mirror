# Agent Catalog

Quick-reference for all registered agents. Source of truth for paths: `config/agents.yml`.
Full instructions: each agent's `SKILL.md` → `PROCEDURE.md`.

## Intelligence Loop (`/intelligence-loop`)

| ID | Name | Path | Outputs | Status |
|---|---|---|---|---|
| 10 | signal-agent | `projects/intelligence-loop/agents/10-signal-agent/` | `outputs/signal-agent/` | Active |
| 11 | feedback-agent | `projects/intelligence-loop/agents/11-feedback-agent/` | `outputs/feedback/` | Active |
| 12 | validation-agent | `projects/intelligence-loop/agents/12-validation-agent/` | `outputs/validation/` | Active |
| 15 | trend-escalation-agent | `projects/intelligence-loop/agents/15-trend-escalation-agent/` | `outputs/trend/` | Active |

## Inspiration Loop (`/inspiration-loop`)

| ID | Name | Path | Outputs | Status |
|---|---|---|---|---|
| 20 | inspiration-scout | `projects/inspiration-loop/agents/20-inspiration-scout/` | `outputs/inspiration/` | Active |

## Shared (used by multiple loops)

| ID | Name | Path | Outputs | Status |
|---|---|---|---|---|
| 13 | prioritisation-agent | `shared/agents/13-prioritisation-agent/` | `outputs/prioritisation/` | Active |
| 14 | weekly-refresh | `shared/agents/14-weekly-refresh/` | `outputs/trend/` | Scaffolded |

## Action Layer (not yet active — `/growth-engineer`)

| ID | Name | Path | Outputs |
|---|---|---|---|
| 05 | funnel-monitor | `projects/action-layer/agents/05-funnel-monitor/` | `outputs/funnel-monitor/` |
| 06 | market-intel | `projects/action-layer/agents/06-market-intel/` | `outputs/market-intel/` |
| 07 | validation | `projects/action-layer/agents/07-validation/` | `outputs/validation/` |
| 08 | github-reader | `projects/action-layer/agents/08-github-reader/` | — |
| 09 | jira-writer | `projects/action-layer/agents/09-jira-writer/` | `outputs/jira-writer/` |

## Pipeline flow

```
Intelligence Loop:  10 → (11 ∥ 12) → diagnosis artifact → 13 → 15
Inspiration Loop:   20 → Gate 1 (PM) → bet-log → feeds 13
Action Layer:       05 → 06 → 07 → 08 → 09  [not active]
```

## Key rules

- Gates are human-approved — never skip
- Domo evidence absence is a hard stop — halt and ask, do not infer
- **Overwrite each run:** `pipeline-context.md`, `signals.md`, `diagnosis.md`, `ranked-hypotheses.md`, `experiment-designs.json`, `cycle-state.json`
- **Append only — never overwrite:** `metrics-history.json`, `findings-store.json`, `ranked-hypotheses.json`, `bet-log.json`
- Diagnose before hypothesise — `directives/diagnosis_before_experimentation.md`
- Score hypotheses via `execution/score_hypotheses.py`; code grounding via `execution/verify_code_grounding.py`
