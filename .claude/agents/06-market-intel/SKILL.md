# /market-intel — SEA Market Intelligence Scanner (Agent 6)

## Role in pipeline
Standalone signal-gathering agent. Called by `/growth-engineer` in Week 1 of each cycle.
Scans the open web and social channels for SEA ecommerce signals relevant to Sephora's
funnel performance, competitor activity, and consumer sentiment. Output consumed by
Agent 7 (validation) when scoring hypothesis confidence.

```
Agent 6: market-intel  →  outputs/market-intel/
         └── signals.md   → read by Agent 7 (validation) + Agent 10 (growth-engineer)
```

## Trigger
Called by `/growth-engineer` automatically. Can also be run standalone:
User runs `/market-intel` or asks to "scan market", "check competitor activity", "SEA ecommerce signals".

---

## Agent Steps

### Step 1 — Load funnel context
Read `outputs/funnel-monitor/pipeline-context.md` if it exists.
Extract: which funnel stages are underperforming, active hypotheses, current weak metrics.
This focuses the search — prioritise signals related to underperforming stages.

If `pipeline-context.md` does not exist, run with broad ecommerce scope.

### Step 2 — Brand sentiment scan
Run targeted web searches for Sephora SEA consumer sentiment.
Search queries to run (execute all, synthesise results):

```
"Sephora Singapore" OR "Sephora Malaysia" OR "Sephora Thailand" review complaint 2025 OR 2026
Sephora SEA app checkout problems site:reddit.com
Sephora SEA loyalty rewards issues site:reddit.com OR site:facebook.com
"Sephora" "Singapore" OR "Malaysia" beauty forum complaint OR issue
Sephora SEA Google Play Store OR App Store reviews recent
```

Extract: recurring complaints, praised features, checkout/payment mentions, app experience signals.
Note recency of each signal (within 30 days = high relevance, 31–90 days = medium, older = low).

### Step 3 — Competitor activity scan
Search for competitor moves that may explain shifts in Sephora's traffic or conversion.

Competitors to scan (from `config/atlassian.yml` market_intel.competitors):
Watsons, Guardian, LOOKFANTASTIC, Lazada Beauty, Shopee Beauty, Sasa

Queries per competitor:
```
"{competitor}" Singapore OR Malaysia promotion sale 2026
"{competitor}" app launch OR feature OR redesign SEA
"{competitor}" beauty skincare loyalty rewards SEA
```

Extract: active promotions, new features, pricing moves, loyalty program changes.
Flag anything that could divert Sephora traffic or shift AOV benchmarks.

### Step 4 — SEA ecommerce trend scan
Search for broader category trends relevant to beauty ecommerce.

```
SEA beauty ecommerce conversion rate 2025 OR 2026
Southeast Asia skincare online shopping trends
beauty checkout abandonment Southeast Asia
mobile commerce beauty SEA 2026
```

Extract: industry benchmarks, consumer behaviour shifts, payment/checkout trends.

### Step 5 — Social channel scan
Search beauty-specific social communities in SEA.

Platforms: Reddit (r/beauty, r/AsianBeauty, r/Singapore, r/malaysia), Facebook beauty groups,
TikTok mentions (search via web), YouTube reviews.

```
Sephora Singapore site:reddit.com OR "r/singapore" OR "r/malaysia"
Sephora SEA haul OR review OR checkout site:tiktok.com
"Sephora" "Malaysia" OR "Singapore" Facebook group complaint 2026
```

Extract: viral posts, trending complaints, positive word-of-mouth, unboxing/haul sentiment.

### Step 6 — Multi-step reasoning: signal scoring

For each signal found, apply structured reasoning before including in output:

1. **Relevance** — does it map to a known weak funnel stage? (High/Medium/Low)
2. **Recency** — within 30 days? 31–90 days? Older?
3. **Corroboration** — does the same signal appear in multiple sources?
4. **Directionality** — does it support or contradict current funnel hypotheses?
5. **Competitor threat** — does it indicate a competitive move that explains metric shifts?

Score each signal 1–5. Include only signals scoring ≥ 3.
Flag the top 3 "headline signals" for the growth engineer.

### Step 7 — Write output
Write `outputs/market-intel/signals.md`. Overwrite on each run.

---

## Output Contract

### `outputs/market-intel/signals.md`
Overwrite on each run.

```markdown
# Market Intelligence — {YYYY-MM-DD}
Generated: {timestamp}
Funnel context loaded: {yes/no}

## Headline Signals (top 3)
1. {signal} — Source: {url/platform} — Relevance: {High/Med/Low} — Funnel stage: {stage}
2. ...
3. ...

## Brand Sentiment
### Positive signals
- {signal} (source, recency)

### Friction / Complaints
- {signal} (source, recency)

## Competitor Activity
### {Competitor name}
- {activity} (source, recency, threat level: High/Med/Low)

## SEA Ecommerce Trends
- {trend} (source, relevance to Sephora funnel)

## Social Channels
- {signal} (platform, recency, volume indicator: viral/moderate/isolated)

## Signal Scoring Log
| Signal | Sources | Recency | Funnel Stage | Score | Included |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | yes/no |

## Search Coverage
Queries run: {N}
Sources reviewed: {N}
Date range: last 90 days prioritised
```

---

## Configuration
```yaml
# config/atlassian.yml
market_intel:
  brand: "Sephora"
  region: "Southeast Asia"
  markets: [Singapore, Malaysia, Thailand, Indonesia, Philippines]
  competitors: [Watsons, Guardian, LOOKFANTASTIC, Lazada Beauty, Shopee Beauty, Sasa]
```

## Permissions
- Read: `outputs/funnel-monitor/pipeline-context.md`
- Read: `config/atlassian.yml`
- Write: `outputs/market-intel/signals.md`
- Web search: unrestricted (public web only)

## Error Handling
- `pipeline-context.md` missing → proceed with broad scope, note in output
- Search returns no results for a query → skip silently, note in Search Coverage log
- All searches return < 5 signals → flag "Low signal run" in output header, do not suppress output
- Rate limiting on search → space queries, do not retry more than twice per query
