# /puppeteer — Domo Dashboard Screenshot Capture (Skill)

## What this skill does
Uses Puppeteer to automate Domo dashboard screenshot capture.
Replaces the manual "drop screenshot in `.claude/tmp-screenshots/funnel-weekly/`" step required by Phase 2 (`/growth-engineer`).

Trigger: `/puppeteer` or "capture domo screenshots" or "take funnel screenshots"

---

## Prerequisites

| Requirement | Detail |
|---|---|
| Puppeteer installed | `npm install` in repo root (already in `package.json`) |
| Env vars set | `DOMO_HOST`, `DOMO_USERNAME`, `DOMO_PASSWORD` |
| Pages registered | Target pages must have `approved: true` in `config/domo.yml → kpi_pages` |

---

## Steps

### Step 1 — Resolve credentials
Check for `DOMO_USERNAME` and `DOMO_PASSWORD` env vars.
If absent, ask the PM: "Please provide your Domo username and password (used only for this session)."
Never hardcode or log credentials.

### Step 2 — Confirm pages to capture
Read `config/domo.yml → kpi_pages`. List all pages where `approved: true`.
Show the PM: page name, page ID, and target URL (`https://<host>/page/<id>`).
Ask: "Capture all of the above, or a specific page? (reply with a page ID or 'all')"

### Step 3 — Run the capture script
Execute via Bash:

```bash
DOMO_HOST=<host> \
DOMO_USERNAME=<username> \
DOMO_PASSWORD=<password> \
node scripts/domo-capture.js [pageId]
```

- Omit `[pageId]` to capture all approved pages.
- Pass a specific page ID to capture one page only.
- Screenshots are saved to `.claude/tmp-screenshots/funnel-weekly/<pageId>-<YYYY-MM-DD>.png`.

### Step 4 — Report results
After the script exits, list saved screenshot paths.
If any page failed (non-zero exit or `ERROR` in output), surface the error and ask PM how to proceed.

### Step 5 — Offer to continue to growth-engineer
If screenshots were saved successfully, ask:
"Screenshots captured. Run `/growth-engineer` now to process them?"

---

## Configuration

Pages are registered in `config/domo.yml`:

```yaml
kpi_pages:
  - id: "391829894"
    name: "Squad KPIs"
    url: "https://sephora-sg.domo.com/page/391829894"
    approved: true
```

To add a new page: add the entry, set `approved: true`, commit. Then re-run `/puppeteer`.

---

## Error handling

| Error | Action |
|---|---|
| Login fails (URL still contains `/auth`) | Surface error, ask PM to verify credentials |
| Page not found (404 / redirect) | Log warning, skip page, continue with remaining pages |
| Card selector timeout | Log warning, capture full-page screenshot anyway |
| Script exits non-zero | Show full error output, do not invoke `/growth-engineer` |
| Missing env var | Ask PM for the value before running |

---

## Output contract

| Path | Behaviour |
|---|---|
| `.claude/tmp-screenshots/funnel-weekly/<pageId>-<YYYY-MM-DD>.png` | Overwrite if same date; new file each day |

Screenshots here are automatically picked up by `/growth-engineer` on the same session.
