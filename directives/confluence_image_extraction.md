# Confluence Image Extraction

## Purpose
Download and assess Confluence page attachments for metric extraction.

## Script
Manual — no execution script yet. Steps performed by Agent 05 (funnel-monitor).

## Steps
1. Download attachments via `/wiki/rest/api/content/{pageId}/child/attachment?limit=50&expand=version`
2. Filter to only attachments where `version.when` starts with current month (`YYYY-MM`)
3. Download with `curl -L` to follow redirects
4. Assess confidence per attachment:
   - **High** = value + label + date range all readable
   - **Medium** = value readable
   - **Low** = skip

## Edge cases
- Attachments from prior months are excluded (stale screenshots)
- If no current-month attachments found, note absence and continue without image data
- Redirects are common — always use `-L` flag
