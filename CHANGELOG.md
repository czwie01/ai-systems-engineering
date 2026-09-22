# Changelog

## Unreleased

- M3 `failure-semantics` adds a provider- and framework-neutral classification
  for observable completion state: `definite-no-effect`,
  `ambiguous-completion`, and `completion-recorded`.
- The optional crash-boundary characterization connects that vocabulary to
  LangGraph and Microsoft Agent Framework without adding either framework to the
  default dependency set.
- M4 `ambiguous-completion` demonstrates the stable logical-operation identity
  and durable idempotency assumptions under which replay produces at most one
  application-visible effect, while rejecting conflicting id reuse.
- M5 `operation-provenance` demonstrates the minimal durable audit fields
  needed to distinguish a recovered retry from an otherwise identical final
  summary, including attempt identity, completion observations, recovery
  decisions, effect identity, and final disposition.
- M6 and M7 remain planned; M3–M5 do not claim exactly-once execution/delivery,
  tamper-proof provenance, concurrency safety, or durable dispatch.

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
