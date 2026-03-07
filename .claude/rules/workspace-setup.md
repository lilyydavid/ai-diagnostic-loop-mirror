---
description: Apply when onboarding a new team, configuring a new Atlassian space, or setting up permissions
---

# Workspace Setup

## Onboarding a new team or space

1. Add team members to `.claude/settings.json` under `permissions.admins` or `permissions.users`.
2. Fill out `.mcp.json` with project-scope MCP credentials (keep git-ignored).
3. Set the Atlassian targets in `config/atlassian.yml`:
   - `space_name` — Confluence space key
   - `page_id` — Confluence page ID the agent may write to
4. If adding a new agent, create a skill directory under `.claude/skills/` and update `CLAUDE.md`.
