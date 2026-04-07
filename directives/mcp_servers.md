# MCP Servers

## Purpose
Reference for all MCP server connections — tool names, OAuth scopes, error handling, and selection rules.

## Servers

### mcp-atlassian (`uvx mcp-atlassian`)
- **Primary** for all Confluence reads/writes and Jira operations
- Auth: Basic (username + API token)
- Confluence writes: use `mcp__mcp-atlassian__confluence_update_page`
- Prefer `mcp__mcp-atlassian__*` for all Atlassian operations

### Atlassian (Rovo)
- OAuth-based — **search and fetch only**
- Has no Confluence write tool
- Use for CQL search when mcp-atlassian search is insufficient

### github (`npx @modelcontextprotocol/server-github`)
- Read access to configured org repos
- Token scopes: `audit_log, repo`
- Used by Agent 08 (github-reader) and Phase 2 action layer

### domo-mcp (`node dist/index.js`)
- `data` scope for datasets; `dashboard` scope for pages/cards
- **Critical:** Use `get-dashboard-signals` for page sources — NOT `get-page-cards` or `get-card` alone (those return metadata only, not live values)
- All sources must be registered in `config/domo.yml` before querying
- Server location: external to this repo

## Error handling

| Error | Action |
|---|---|
| 401 from Confluence/Jira | MCP server needs restart — token rotation requires server restart to pick up new credentials |
| 401 from Domo | Check client_credentials in `.mcp.json`; Domo tokens don't expire but may be revoked |
| Unregistered Domo source ID | Hard stop — surface to PM, do not query. Add to `config/domo.yml` first |

## Credentials
All in `.mcp.json` (git-ignored). To rotate Atlassian tokens: https://id.atlassian.com/manage-profile/security/api-tokens
