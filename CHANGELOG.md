# Changelog

## Unreleased

- M3 `failure-semantics` adds a provider- and framework-neutral classification
  for observable completion state: `definite-no-effect`,
  `ambiguous-completion`, and `completion-recorded`.
- The optional crash-boundary characterization connects that vocabulary to
  LangGraph and Microsoft Agent Framework without adding either framework to the
  default dependency set.
- M4 `ambiguous-completion` demonstrates the stable logical-operation identity
  and durable atomic idempotency assumptions under which replay produces at most
  one application-visible effect while the idempotency record is retained,
  rejects conflicting id reuse, and explicitly demonstrates that pruning the
  record ends that guarantee.
- M5 `operation-provenance` demonstrates the minimal durable audit fields
  needed to distinguish a recovered retry from an otherwise identical final
  summary, including attempt identity, completion observations, recovery
  decisions, effect identity, and final disposition.
- M6 `concurrent-promotion` demonstrates that an atomic generation-fenced
  compare-and-swap accepts at most one competing transition from one observed
  generation, while the naive stale-write and ABA controls expose why state
  values alone are insufficient.
- M7 `durable-dispatch` demonstrates a transactional-outbox-style durable
  handoff: authoritative state plus dispatch intent survive process failure when
  committed atomically, while effect-before-ack replay composes with M4
  idempotency.
- The planned M1–M7 experiment sequence is now executable. Promotion into a
  reusable core and production runtime selection remain separate decisions;
  M3–M7 still do not claim exactly-once delivery/execution, distributed
  consensus, cross-database atomicity, or bounded liveness.

## v0.1.0 — Evidence & Evaluation

The first public reference boundary of AI Systems Engineering.

This release contains two independently executable experiments:

- M1 `evidence-contracts`
  Demonstrates that valid evidence identity is not sufficient for provenance
  compatibility.
- M2 `evaluation-oracle-integrity`
  Demonstrates that valid citations are not sufficient for claim support.
  Under the explicit atomic support model, every represented requirement must
  be supported before a passing verdict.

Demonstrated guarantees are intentionally narrow and executable.

This release does not establish:

- arbitrary natural-language entailment;
- factual truth of source material;
- retrieval quality or completeness;
- evidence authenticity;
- general LLM-as-judge reliability;
- production-ready provenance or evaluation infrastructure;
- a stable public library API;
- M3–M7 reliability, concurrency, or dispatch properties.

M3–M7 remain planned.

This is an Alpha reference boundary and is not published to PyPI.
