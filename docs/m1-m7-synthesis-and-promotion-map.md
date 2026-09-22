# M1–M7 Synthesis and Promotion Map

- Status: PROPOSED
- Date: 2026-09-22
- Source: executable M1–M7 experiments and `docs/guarantees.md`
- Decision scope: what the completed experiment sequence justifies next
- Non-decision: no runtime, framework, Control Plane, or reusable API is selected here

## Why this synthesis exists

M1–M7 are now executable, but experiment completion is not the same thing as
promotion into a reusable library or production architecture.

This document separates four questions that are easy to collapse:

1. **What was demonstrated?** — owned by the experiment and its evidence.
2. **What semantic is portable?** — a candidate conclusion from the evidence.
3. **Where should that semantic live?** — an ownership decision.
4. **Which mechanism should realize it?** — a later native/wrap/compose/build
   decision.

The repository should not create M8 merely because M7 is complete.

## Promotion vocabulary

- **CORE_CANDIDATE** — a small provider/framework-neutral mechanism may belong
  in the future reusable `ai_systems` core after real-consumer validation.
- **CONTRACT_CANDIDATE** — the reusable value is primarily an observable
  semantic obligation; the mechanism belongs at a workflow/runtime/consumer
  boundary.
- **COMPOSE_EXISTING** — the semantic is established, but maintained
  infrastructure or an existing systems pattern should be characterized before
  custom implementation.
- **KEEP_EXPERIMENT** — the evidence is useful, but the current abstraction is
  not yet justified as a reusable mechanism or contract.
- **CONSUMER_LOCAL** — the policy/meaning is domain-owned and should not be
  centralized.

A disposition is a next-decision category, not a maturity score.

## Promotion map

| Milestone | Demonstrated semantic | Primary disposition | Candidate destination | Evidence still required before promotion |
| --- | --- | --- | --- | --- |
| M1 `evidence-contracts` | Accepted selections contain only known evidence whose recorded provenance matches the declared selection provenance under the experiment identity model. | **CORE_CANDIDATE** | future `ai_systems` evidence primitive; consumers may compose it | At least two independent consumers with different evidence catalogs; show that one small identity/provenance interface is sufficient without importing consumer policy. |
| M2 `evaluation-oracle-integrity` | Under explicit atomic support annotations, a passing verdict checks every represented requirement and finds support for each one. | **KEEP_EXPERIMENT** | evaluation consumers first; possible future core helper | Real evaluation consumers must show that the atomic requirement/support representation survives non-synthetic claims. No promotion from this experiment to a general entailment/hallucination evaluator is justified. |
| M3 `failure-semantics` | Equivalent effect-visibility/completion observations map to the same provider/framework-independent completion class. | **CORE_CANDIDATE** | future `ai_systems` execution primitive | One or more real provider/effect adapters must demonstrate that the required observations can be obtained authoritatively; unknown observation must remain explicit rather than guessed. |
| M4 `ambiguous-completion` | Stable logical operation identity plus immutable content and retained atomic idempotency state gives at-most-one application-visible effect across retry while that record is retained. | **CONTRACT_CANDIDATE** | effect-boundary/runtime contract; small identifiers/types may later be core | Validate at least one real provider with native idempotency and one boundary that requires wrapping/composition. Record retention semantics explicitly. |
| M5 `operation-provenance` | A minimal durable history can distinguish recovered retry from direct success and retain attempts, observations, recovery decisions, effect identity, and final disposition. | **CONTRACT_CANDIDATE** | audit/evidence contract; map onto existing workflow history, telemetry, or consumer storage | Exercise in at least two different runtimes/consumers; prove the fields can map to existing maintained observability/workflow surfaces without creating a duplicate event store. |
| M6 `concurrent-promotion` | Atomic compare-and-swap on source state plus monotonic generation accepts at most one competing transition from one observed generation and rejects ABA-stale actors. | **CONTRACT_CANDIDATE** | portable authority semantics; likely Workflow Kit consumer, with runtime realization in an existing authoritative store or admitted Control Plane state | Real multi-actor consumer evidence; characterize the authoritative store's conditional-write/fencing semantics; do not infer a Control Plane requirement until the admission test is satisfied. |
| M7 `durable-dispatch` | Atomic authority+intent commit plus retained pending intent and eventual rescan prevents committed dispatch intent from silently disappearing before acknowledgement. | **COMPOSE_EXISTING** | transactional outbox/CDC/durable workflow runtime; Control Plane only if a consumer requires shared durable dispatch authority | Characterize maintained mechanisms against the contract, including Temporal and database/broker compositions; test effect-before-ack replay together with M4. No custom queue is justified by M7 alone. |

## What should actually become reusable code now?

Nothing is automatically promoted by this document.

The strongest current code candidates are **M1** and **M3** because their
mechanisms are small, deterministic, provider-neutral, and do not themselves
own consumer policy. Even they should remain candidates until real consumers
demonstrate that their interfaces are not artifacts of the synthetic fixtures.

M4–M7 are more valuable today as **contracts and composition tests** than as a
new framework:

- M4's correctness boundary lives where the real effect is deduplicated.
- M5 should map onto an existing durable history/telemetry surface where
  possible.
- M6 requires one real authoritative compare-and-swap surface, not a bespoke
  lock service by default.
- M7 is the established dual-write/outbox family of problems; the experiment
  demonstrates the semantic boundary, not a reason to build another queue.

M2 remains deliberately conservative because its explicit atomic support model
is much narrower than general natural-language evaluation.

## Dependency structure

The completed sequence is not one linear framework:

```text
M1 evidence relationship
  └─> M2 claim-support coverage

M3 completion classification
  └─> M4 ambiguous retry contract
        └─> M5 durable execution provenance

M6 generation-fenced shared-state mutation
  └─> may produce authoritative work intent
        └─> M7 durable dispatch

M7 effect-before-ack replay
  └─> composes M4 idempotency
        └─> may be explained by M5 provenance
```

This structure matters for runtime selection: a runtime can satisfy some rows
natively and still require composition for others.

## Post-M7 roadmap

### S0 — Synthesis and promotion map

This document.

Exit:
- every M1–M7 result has a bounded disposition;
- no experiment result is silently treated as production architecture;
- downstream evidence gaps are named.

### S1 — Real-consumer validation

Run selected contracts against at least three genuinely different consumers.

Required diversity:
- one creative/artifact-production workflow;
- one asset/data pipeline or external-effect workflow;
- one non-creative engineering/agent execution workflow.

For each consumer:
- identify which M1–M7 semantics are actually load-bearing;
- map consumer authority and provider/runtime mechanisms;
- record where the generic model fits without translation;
- record where policy remains consumer-local;
- record any unobservable or contradictory assumption.

Exit:
- at least two consumers support each proposed portable contract before it is
  promoted inward;
- consumer-specific vocabulary is not copied into the core.

### S2 — Maintained-runtime conformance

Characterize maintained open-source/native mechanisms **per capability**, not
as one framework ranking.

Initial maintained OSS candidates:
- LangGraph for explicit graph state, checkpoint/resume, interrupts, and
  agent-oriented orchestration;
- Temporal for durable long-running execution, retries, timers, and worker
  recovery;
- ordinary database conditional writes/outbox/CDC where they satisfy M6/M7 more
  directly than an agent framework.

Decision vocabulary:
`NATIVE / WRAP / COMPOSE / BUILD / DEFER`.

At minimum characterize:
- M3 observation availability;
- M4 logical-operation/idempotency support and retention semantics;
- M5 exportable durable provenance/history;
- M6 conditional-write/fencing ownership;
- M7 durable intent-to-execution handoff and effect-before-ack behavior;
- human approval/resume where a consumer requires it.

Exit:
- no `BUILD` without a named residual semantic gap after native/wrap/compose
  alternatives;
- runtime selection remains separable from semantic ownership.

### S3 — Route and promote

Route only validated results:

- tiny provider-neutral mechanisms -> `ai-systems-engineering` reusable core;
- portable workflow/authority semantics -> Workflow Kit under its own promotion
  gate;
- reusable procedures -> Skills Library;
- external capability facts -> Engineering Radar;
- admitted shared durable runtime state -> Control Plane;
- creative/product/domain policy -> consumer repository.

A public experiment may stay an experiment indefinitely; promotion is not a
required terminal state.

### S4 — Release checkpoints

Treat releases and reusable-API promotion as separate axes.

**v0.2 — Reliable AI Execution**
- publication boundary for M3–M5 plus the synthesis;
- may ship with zero newly promoted stable library API;
- must preserve the Alpha/non-production caveat.

**v0.3 — Safe Agentic State Changes**
- publication boundary for M6–M7 plus consumer/runtime validation evidence;
- must distinguish demonstrated semantics from whichever runtime realizations
  are selected later.

### S5 — Residual gaps only

Create a new experiment only when a real consumer or runtime characterization
produces a named unproven invariant.

Examples of legitimate future triggers:
- a required provider cannot expose the observations M3 needs;
- two independent authority stores must be coordinated and M6's single-record
  assumption is insufficient;
- a production dispatch surface cannot compose M4+M7 safely;
- provenance authenticity/tamper evidence becomes a real requirement.

"Seven milestones are complete" is not a trigger for M8.

## Runtime-selection implication

The experiment sequence now supplies a **conformance target** rather than an
argument for a particular SDK.

A maintained runtime is useful when it eliminates custom responsibility while
still satisfying the relevant semantic contract. A framework's own status or
completion signal is evidence about that framework; it is not automatically the
consumer's completion authority.

This keeps the project compatible with an OSS-first strategy while avoiding a
different kind of lock-in: rebuilding standard durable-execution, outbox,
checkpointing, or conditional-write machinery inside a bespoke agent framework.

## Immediate next tasks

1. Validate this promotion map against real consumers.
2. Characterize maintained runtimes against M3–M7 at capability level.
3. Route the supported portable semantics to their canonical owners.
4. Prepare v0.2 as a publication checkpoint once the synthesis is accepted.
5. Do not add M8 until S1/S2 exposes a concrete residual invariant.
