# Product Agents

This repository contains several agents, each with their own `skill.md` describing capabilities.

## Structure

- `.claude/` – contains onboarding information, permissions, and agent skills for Claude integration
  - `config.md` – edit this to onboard a new team or space
  - `settings.json` – permissions config
  - `skills/` – individual skill directories for each agent
    - `create-prd/` with `SKILL.md`
    - `user-stories/` with `SKILL.md`
    - `omni-monitor/` with `SKILL.md` (parallel)
    - `05-funnel-monitor/` with `SKILL.md` — ecommerce funnel metrics from Confluence
- `.mcp.json` – project-scope MCP config (git-ignored)
- `config/atlassian.yml` – configuration for connecting to Atlassian MCP (path, page id, space name).
- `agents/` – each subfolder represents an agent with a `skill.md` file.

## Adding an agent

1. Create a new folder under `agents/` (e.g. `agent3`).
2. Add a `skill.md` file with the agent's description and capabilities.
3. Update the configuration if needed.

## Configuration

The `config/atlassian.yml` file holds Atlassian details required by scripts or tooling.

Example content:

```yaml
mcp_path: "/path/to/mcp/project"
page_id: "1234567890"
space_name: "MYSPACE"
```
