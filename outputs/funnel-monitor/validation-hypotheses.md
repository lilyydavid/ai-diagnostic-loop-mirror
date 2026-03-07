# Validation Hypotheses
week: 2026-W09
generated: 2026-03-05
for: Agent 2 (validation), Agent 3 (github-reader)

---

## H1 — Cart-to-checkout drop caused by stackable promotions launch
hypothesis: The cart-to-checkout CTR decline (-18.66% YoY) is caused by the stackable promotions feature launched in Jan 2026 introducing friction or confusion on the cart page, not by seasonality or pricing changes.
priority: high
product_area: cart
output_type: jira_story

source_metric:
  name: Cart to Checkout CTR (Combined)
  value: 17.09%
  yoy: -18.66%
  risk_id: R2

validation_criteria:
  confirms: CTR decline began within 2 weeks of stackable promotions launch date; decline is larger for sessions with active promotions applied vs no promotions; session replay shows users reading promotion text then abandoning
  denies: Decline pre-dates the launch; decline is uniform across sessions regardless of promotion state; A/B holdback group (no stackable promos) shows same decline

confluence_search_terms: [stackable promotions, cart discount, cart page, promotion confusion, ATC rate]
confluence_pages_to_check: [63635128321, 64699236362]
confluence_pages_already_scanned: [63001919747, 64699236362, 64742948865, 63708168503]

code_area:
  service: cart-service / checkout-bff
  component: CartPage, DiscountEngine, PromotionBanner
  look_for: Changes merged Jan 2026 to cart page rendering or discount display logic; any changes to how stackable promotions are surfaced to the user; feature flags controlling promotion UI

suggested_jira_fields:
  type: Spike
  priority: P1
  labels: [ecommerce, cart, checkout, promotions]
  acceptance_criteria_hint: Identify the specific UX change or promotion mechanic that correlates with the CTR drop. Output: root cause confirmed or ruled out, with data. Next step is either a UX fix story or a revert.

---

## H2 — Payment failure recovery gap
hypothesis: Users who fail payment and receive a retry nudge within 1 hr will convert at >30%, making an automated retry flow a high-ROI intervention.
priority: high
product_area: payment
output_type: jira_story

source_metric:
  name: Payment Failure Rate
  value: 11.09%
  yoy: not available
  risk_id: R3

validation_criteria:
  confirms: Comparable retry nudge experiments in similar markets show >20% recovery rate; session data shows failed-payment users return to checkout within 24 hrs at a non-trivial rate when reminded; CRM has the technical capability to send a push within 1 hr of payment event
  denies: Failed-payment users have no return behaviour within 7 days even without nudge; payment failures are concentrated in specific payment methods that don't support retry (e.g. bank transfer timeout); retry rate is already >30% without intervention

confluence_search_terms: [payment failure, payment retry, checkout recovery, CRM push, abandoned checkout]
confluence_pages_to_check: []
confluence_pages_already_scanned: [63001919747, 64742948865]

code_area:
  service: checkout-bff / payment-service / CRM integration
  component: PaymentResultHandler, OrderConfirmationService, BrazeEventEmitter
  look_for: Does a payment failure event currently fire to Braze or CRM? Is there existing retry logic? What payment methods account for the 11.09% failure rate?

suggested_jira_fields:
  type: Story
  priority: P1
  labels: [ecommerce, payment, CRM, recovery]
  acceptance_criteria_hint: User receives push + email within 1 hr of payment failure with direct link back to checkout. A/B tested. Success metric: payment recovery rate >20% in treatment group.

---

## H3 — Address completion friction at postcode lookup
hypothesis: The address completion drop-off (58.63%) is primarily caused by friction at the postcode/address lookup step, not at sign-in, and can be reduced by simplifying that specific step.
priority: high
product_area: checkout
output_type: jira_story

source_metric:
  name: Address Completion Rate
  value: 58.63%
  yoy: not available
  risk_id: R3

validation_criteria:
  confirms: Step-level funnel in Domo shows a larger drop at postcode/address step than at sign-in; session replay shows users stopping at address lookup, re-entering, or giving up; error rate on address lookup API is elevated
  denies: Drop is primarily at the sign-in step; address lookup success rate is >95%; drop is uniform across all steps with no single dominant exit point

confluence_search_terms: [address completion, shipping address, postcode lookup, checkout friction, sign in checkout]
confluence_pages_to_check: []
confluence_pages_already_scanned: [63001919747, 64742948865]

code_area:
  service: checkout-bff / address-service
  component: ShippingAddressForm, PostcodeLookup, AddressAutocomplete
  look_for: Address lookup API error rates; recent changes to the address form; whether postcode lookup uses a third-party API (e.g. Google Places) with potential reliability issues; any A/B tests active on the address step

suggested_jira_fields:
  type: Spike
  priority: P1
  labels: [ecommerce, checkout, address, UX]
  acceptance_criteria_hint: Identify the dominant drop-off step in address completion funnel. If postcode lookup, output is a UX improvement story. If sign-in, output is a guest checkout story.

---

## H4 — C&C decline driven by in-store experience, not demand
hypothesis: The 10-week C&C decline (8.47% → 7.51% of ecomm orders) reflects degradation in the in-store collection experience (wait times, slot availability, fulfilment errors) rather than reduced customer intent.
priority: medium
product_area: fulfilment
output_type: jira_story

source_metric:
  name: C&C Orders as % of Ecomm
  value: 7.51%
  yoy: declining trend (Week 1 8.47% → Week 10 7.51%)
  risk_id: R5

validation_criteria:
  confirms: C&C slot fill rate has increased (slots filling up, limiting choice); collection SLA breach rate has increased; customer survey data shows satisfaction with C&C experience declining; store team reports on fulfilment issues
  denies: C&C slot availability is stable; customer satisfaction with collection is unchanged; decline is explained by store count or catchment changes

confluence_search_terms: [click and collect, C&C, collection experience, slot availability, fulfilment SLA]
confluence_pages_to_check: []
confluence_pages_already_scanned: [64742948865]

code_area:
  service: fulfilment-service / store-inventory
  component: ClickAndCollectSlotSelector, CollectionAvailabilityChecker
  look_for: Recent changes to slot availability logic; whether slot availability data is real-time or cached; any known issues with C&C fulfilment in specific markets

suggested_jira_fields:
  type: Spike
  priority: P2
  labels: [fulfilment, C&C, store, retail-ops]
  acceptance_criteria_hint: Confirm whether decline is demand-side or experience-side. If experience: surface specific failure point to store ops team. If demand: investigate whether promotion changes reduced C&C attractiveness.

---

## H5 — Skincredible sessions convert at 2× vs non-Skincredible
hypothesis: App sessions that include a Skincredible interaction convert at 2× the rate of non-Skincredible sessions and drive materially higher AOV, making Skincredible-to-PDP the highest-leverage discovery flow to scale.
priority: medium
product_area: discovery
output_type: jira_story

source_metric:
  name: Skincredible AOV (in-store omni)
  value: ~€122.4 vs baseline €69
  yoy: not available
  risk_id: none (opportunity signal)

validation_criteria:
  confirms: Domo segment of sessions with Skincredible touch shows CVR >2× non-Skincredible; AOV for Skincredible-influenced sessions is materially higher online (not just in-store); funnel from Skincredible scan → PDP → ATC → purchase shows low drop-off
  denies: The €122.4 AOV is an in-store artefact (high-value customers who scan in-store would have high AOV anyway); online Skincredible sessions do not show elevated CVR; sample size of Skincredible online sessions is too small to be meaningful

confluence_search_terms: [Skincredible, skin scan, PDP conversion, beauty scan, scan to cart]
confluence_pages_to_check: [64212336699]
confluence_pages_already_scanned: [64212336699, 64742948865]

code_area:
  service: skincredible-service / product-recommendation
  component: SkincredibleResultsPDP, SkinScanRecommendationEngine
  look_for: How Skincredible results link to PDPs; whether Skincredible interactions fire an ATC or CVR tracking event; whether there is an existing A/B test framework for Skincredible placement

suggested_jira_fields:
  type: Story
  priority: P2
  labels: [discovery, skincredible, PDP, conversion, app]
  acceptance_criteria_hint: Instrument Skincredible-influenced sessions in Domo to measure CVR and AOV vs control. If hypothesis confirmed: write a story to expand Skincredible placement to more PDP surfaces and trigger in-store → app push for non-converters.
