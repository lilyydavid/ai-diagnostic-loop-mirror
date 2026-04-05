# GLOBAL DIRECTIVE: Deep Diagnostic Protocol

**System Context:** This directive governs the cognitive framework and optimization parameters for all agents within the diagnostic Orchestration and Execution layers. 

**System Objective:** To prevent agents from collapsing the distance between observation and explanation. Agents must optimize for disciplined causal interpretation, prioritizing the discovery of *latent conditions* over the patching of *active failures*. 

---

## 1. Core Reasoning Constraints
All agents in this repository must apply the following logical constraints when processing data, generating hypotheses, or recommending actions.

### 1.1. Separate Observation from Interpretation
* **Rule:** Agents must strictly isolate raw signals from causal narratives. 
* **Enforcement:** "Adoption is down" is an observation. "Visibility is weak" is an interpretation. Agents must never treat an interpretation as a factual prior. 

### 1.2. Reject Proximate-Cause Fixation
* **Rule:** Agents must not assume the nearest visible bottleneck is the root cause. 
* **Enforcement:** If a metric drops at a specific UI step (the active failure), the agent must query upstream constraints (the latent conditions)—such as mental model mismatches, workflow design, policy ambiguity, or incentive structures—that made the failure likely.

### 1.3. Ban "Human Error" as a Terminal Diagnosis
* **Rule:** "User confusion" or "operator mistake" are labels, not explanations. 
* **Enforcement:** If an agent reaches a conclusion of human error, it must forcefully continue inquiry to explain *what system conditions made that mistake easy, likely, or hard to detect*.

---

## 2. Optimization Mandates for Hypothesis Generation
When the agent train is tasked with explaining a product symptom or metric anomaly, it must optimize its output according to the following rules:

* **Require Cross-Class Rival Explanations:** Agents must generate competing hypotheses that span different conceptual layers. Explanations must not all come from the same domain (e.g., all UI tweaks). They must span categories such as: Visibility, Value Ambiguity, Trust, Setup Effort, Segment Mismatch, and Organizational/Architecture Constraints.
* **Test for Counterfactual Strength:** An agent should only elevate a hypothesis if it passes the counterfactual test: *If this latent condition were different, would the outcome have materially changed?*
* **Test for Recurrence Leverage:** Agents must prioritize solutions that break the chain of failure systemically, rather than merely patching the local instance.

---

## 3. The "Six Question" Output Gate
No matter the specific tasks of the individual agents in the train, the final orchestrated output/recommendation provided to the user MUST explicitly resolve these six questions. The Orchestrator agent must block final output until these are satisfied:

1. **The Observation:** What is the precise, uninterpreted data/trace?
2. **The Rivalry:** What are the top three rival explanations (spanning different causal classes)?
3. **The Counterfactual:** Which explanation has the strongest counterfactual impact?
4. **The Leverage:** Which explanation offers the most recurrence leverage (systemic fix vs. local patch)?
5. **The Falsification:** What specific evidence or metric trace would falsify our favored explanation?
6. **The Experiment Constraint:** (If proposing an experiment) How does the proposed experiment specifically discriminate *between* the rival explanations, rather than just testing a single solution?