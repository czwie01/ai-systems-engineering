# Changelog

## v0.1.0 — Evidence & Evaluation

The first public reference boundary. It contains two independently executable
experiments and does not publish a shared library API, a PyPI package, or a
1.x compatibility promise.

### Added

- `evidence-contracts` (M1): deterministic provenance compatibility checks.
- `evaluation-oracle-integrity` (M2): explicit atomic claim-support checks.
- Discovery CLI: `ai-systems list`, `explain`, and `run`.

### Demonstrated guarantees

- M1: known evidence identity is not sufficient for provenance compatibility.
  An accepted selection contains only known fragments whose recorded
  document/version provenance equals the declared provenance.
- M2: valid evidence relationships are not sufficient for claim support.
  Under the explicit atomic support model, a passing verdict checks every
  represented requirement and finds each one in recorded evidence support.

### Explicit non-guarantees

- arbitrary natural-language entailment;
- factual truth of source material;
- retrieval quality or completeness;
- evidence authenticity or universal provenance infrastructure;
- general LLM-as-judge reliability, model alignment, or hallucination
  detection;
- production-ready evaluation or provenance systems;
- a stable public library API;
- M3–M7 reliability, concurrency, or dispatch properties.
