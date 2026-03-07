# MCP Configuration

## Atlassian

Credentials are loaded from `.mcp.json` (git-ignored). Set the write target in `config/atlassian.yml`:

```yaml
space_name: ""   # Confluence space key, e.g. "PROD"
page_id: ""      # Page ID from the Confluence URL
```

### Confluence Permissions

| Operation | Allowed |
|---|---|
| Read any page | Yes |
| Write to configured space / page | Yes |
| Write outside configured space / page | No |
| Create top-level spaces | No |

### Jira Permissions

| Operation | Allowed |
|---|---|
| Read issues | Yes |
| Create / update issues | Yes |
| Delete issues | No |

---

Rotate tokens: https://id.atlassian.com/manage-profile/security/api-tokens
