---
description: Apply when reading from or writing to Confluence or Jira via MCP
---

# Atlassian MCP Rules

## Configuration

Credentials are loaded from `.mcp.json` (git-ignored).
Write targets are set in `config/atlassian.yml`:

```yaml
space_name: ""   # Confluence space key, e.g. "PI"
page_id: ""      # Page ID from the Confluence URL
```

To rotate tokens: https://id.atlassian.com/manage-profile/security/api-tokens

## Confluence Permissions

| Operation | Allowed |
|---|---|
| Read any page | Yes |
| Write to configured space / page | Yes |
| Write outside configured space / page | No |
| Create top-level spaces | No |

## Jira Permissions

| Operation | Allowed |
|---|---|
| Read issues | Yes |
| Create / update issues | Yes |
| Delete issues | No |
