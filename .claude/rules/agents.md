---
description: Apply when adding a new agent, running a skill, or working inside the .claude/skills/ directory
---

# Agent Conventions

## Adding an agent

1. Create a new directory under `.claude/agents/` with a numeric prefix (e.g. `06-my-agent/`).
2. Add a `SKILL.md` file describing role, trigger, steps, output contract, permissions, and error handling.
3. Register the skill in `CLAUDE.md` agents table.

## Skill file structure

Each `SKILL.md` should include:

- **Role in pipeline** — position relative to other agents and data flow
- **Trigger** — slash command or natural language phrases that activate the skill
- **Agent Steps** — numbered, deterministic steps
- **Output Contract** — exact file paths, formats, and append vs overwrite behavior
- **Configuration** — relevant `config/` keys
- **Permissions** — what the agent may read and write
- **Error Handling** — explicit fallback for every failure mode

## Output files

All agent outputs go under `outputs/<agent-name>/`. Overwrite pipeline context files on each run. Never overwrite history/append-only files — only append.
