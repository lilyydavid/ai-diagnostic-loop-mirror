# Market Intel Signals
week: 2026-W09
generated: 2026-03-06
for: Growth Engineer W1 2026-03

Sources scanned: Confluence internal research (Competitive Research + Synthesis, Stackable Promotions spec, payment architecture docs, address/checkout specs, C&C specs, loyalty docs). Open-web scan (Reddit, TikTok, competitor sites) not completed this run.

Signals scored ≥3 only. Scale: 1=noise, 5=high-impact confirmed signal.

---

## Internal Product Signals (Confluence)

### S1 — App Cart→Checkout CTR (15.29%) nearly half of web (29.20%), declining faster YoY
Score: 5 | Stage: Cart → Checkout | Source: Domo screenshots (W09)

App cart→checkout CTR is 15.29% (YoY -13.03%) vs web 29.20% (YoY -9.23%). Combined 17.25% (YoY -18.66%). The gap and rate of decline on app is the primary driver of the combined decline. Stackable promotions have NOT yet gone to production — the decline predates any promotion change and is concentrated on app. Possible causes: payment method unavailability on app, guest checkout flow on app, app-specific UX friction, or lower purchase intent in app sessions vs web.

**Implication for H1 (revised):** Hypothesis reframed. The cart→checkout drop is an app-channel-specific issue, not a promotions issue. W2 should isolate: (a) payment method availability on app vs web, (b) guest vs signed-in CTR split on app, (c) app checkout UX step-level funnel in Domo.

---

### S2 — C&C exclusion banner (SE-4032) shown for eligible carts
Score: 5 | Stage: Fulfilment / C&C | Source: Internal spec/bug (SE-4032)

A C&C exclusion banner is persistently displayed to users even when their cart is eligible for click-and-collect. This directly suppresses C&C order selection and explains the 10-week declining trend (8.47%→7.51%). The bug/spec issue has a ticket reference (SE-4032).

**Implication for H4:** Confidence upgrades to HIGH. The C&C decline is a product bug (false exclusion banner), not a demand or in-store experience issue. This changes H4 from a "investigate cause" spike to a "fix a known bug" story — potentially ≤3 SP.

---

### S3 — Payment retry architecture: 3.5–24h expiry window
Score: 4 | Stage: Payment | Source: Internal payment architecture docs

Payment session expiry occurs 3.5–24h after failure depending on payment method, before a retry is technically possible. The current architecture routes failed-payment users back to checkout without a retry nudge. Retry attempts create duplicate order risk without proper idempotency handling. This explains the ~70% non-retry rate and adds complexity to H2.

**Implication for H2:** The retry nudge (push within 1hr) is feasible for payment methods with >3.5h expiry windows, but not for short-expiry methods. W2 validation should identify payment method breakdown of the 11.09% failures to confirm scope. The 1-hr push may need to be method-conditional.

---

### S4 — Sign-in rate -7.1% YoY reduces address pre-fill and payment tokenisation
Score: 4 | Stage: Auth → Checkout | Source: Pipeline context (sign-in rate metric) + checkout spec

Declining sign-in rate (43.1% combined, -7.1% YoY) reduces the proportion of users with tokenised payment and pre-filled shipping addresses. This compounds both H2 (payment failure — unrecognised cards more likely to fail) and H3 (address completion — guest users must manually enter all 5 required fields).

**Implication for H2/H3:** Guest checkout users face higher payment failure rates AND higher address drop-off. H3 may be best scoped as "reduce friction for guest address entry" rather than just "fix postcode lookup."

---

### S5 — Strict address validation: 5 required fields, no partial save
Score: 3 | Stage: Checkout | Source: Internal address/checkout spec

Address form requires 5 fields with strict validation and no partial save capability. Users who exit mid-completion lose all progress. No autofill from sign-in data for guest users. Corroborates H3 but does not isolate whether postcode lookup or the full form length is the dominant drop-off point.

**Implication for H3:** Root cause could be form length + no partial save (addressable with field reduction or autosave), not specifically postcode API. W2 should pull step-level Domo funnel to confirm.

---

## Competitor / Market Signals

### S6 — Shopee AI/AR suite: 2.7× conversion, 40% cart uplift (SEA, live Aug 2025)
Score: 5 | Stage: Discovery | Source: Competitive Research + Synthesis (Confluence)

Shopee's AI recommendation and AR try-on suite is live across SEA markets (SG, MY, TH, ID, PH) since Aug 2025. Reported metrics: 2.7× conversion lift for AR-engaged sessions, 40% cart size uplift. This sets a new SEA benchmark for AI-assisted discovery. Sephora's Skincredible is the closest equivalent but is in-store only with limited online handoff.

**Implication:** Not a W2 hypothesis, but strong strategic context. If Skincredible online sessions (H5) confirm 2× CVR, this validates prioritising Skincredible scale as a competitive response to Shopee's AR suite.

---

### S7 — Lazada Lazzie AI agent: 30%+ conversion lift (live SG/MY/TH/ID/PH)
Score: 4 | Stage: Discovery | Source: Competitive Research + Synthesis (Confluence)

Lazada's Lazzie AI shopping agent is live across all SEA markets with reported 30%+ conversion lift for agent-assisted sessions. Natural language product discovery, comparison, and checkout guidance. Sephora has no equivalent online AI shopping assistant.

**Implication:** Competitive pressure on discovery CVR. Context for market intel — not actionable in this sprint cycle (scope too large) but relevant for quarterly roadmap.

---

### S8 — Agentic commerce live: OpenAI (Feb 2026), Google (Jan 2026)
Score: 3 | Stage: Strategic | Source: Competitive Research + Synthesis (Confluence)

OpenAI and Google have launched agentic commerce capabilities (Feb and Jan 2026 respectively). SEA adoption timeline unclear. Early movers (Shopee, Lazada) already building AI shopping infrastructure.

**Implication:** Strategic horizon signal. Not actionable in this cycle. Monitor quarterly.

---

### S9 — O2O benchmark: 54% of shoppers use mobile in-store
Score: 3 | Stage: Discovery / O2O | Source: Competitive Research + Synthesis (Confluence)

54% of SEA shoppers actively use mobile while in-store. Sephora's Skincredible and C&C are both positioned for O2O but under-instrumented (limited online tracking of in-store mobile sessions). Corroborates both H4 (C&C) and H5 (Skincredible online handoff).

**Implication:** Strengthens the case for instrumenting Skincredible online sessions (H5) and for fixing C&C false exclusion banner (H4/S2).

---

## Summary — Hypothesis Impact

| Hypothesis | Signal | Change |
|---|---|---|
| H1 Cart→Checkout friction (app-channel) | S1: App CTR 15.29% vs web 29.20%, declining faster | Confidence: HIGH — app-specific, stackable promos not yet in prod |
| H2 Payment failure recovery | S3: 3.5-24h expiry window limits retry scope | Confidence: HIGH, scope narrowed |
| H3 Address completion friction | S4: Guest user compound issue; S5: 5-field strict form | Confidence: HIGH, root cause broadened |
| H4 C&C decline | S2: SE-4032 false exclusion banner confirmed | Confidence: MED-LOW → **HIGH, likely ≤3 SP fix** |
| H5 Skincredible CVR | S6/S9: Competitive context strengthens strategic case | Not in W2 scope but elevated strategically |
