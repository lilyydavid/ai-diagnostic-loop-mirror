Read `.claude/agents/10-signal-agent/SKILL.md` and execute the signal agent workflow.

1. Load `config/domo.yml` — read all approved KPI sources and query windows.
2. If the PM provided a dashboard URL (e.g. `https://sephora-sg.domo.com/page/391829894`): extract the page ID and check it against `config/domo.yml → kpi_pages`. If registered, use `get-dashboard-signals` with that page ID. If not registered, tell the PM to add it to `config/domo.yml` first.
3. For all page sources: use `get-dashboard-signals` — NOT `get-page-cards` or `get-card` alone. Those tools return card metadata only, not live metric values.
4. Follow the agent steps precisely — query sources, apply signal threshold, flag suspicious metrics, surface signal report to PM.
5. Wait for PM gate before proceeding. Do not auto-advance to Step 2.
6. If PM types `/sharpen` after the gate, execute the first-principles sharpening workflow from the SKILL.md.
