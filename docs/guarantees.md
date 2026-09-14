# Guarantees and non-guarantees

An experiment is useful only when its claim is narrower than its evidence. Each
completed experiment must distinguish four elements:

1. **Demonstrated guarantee** — the property established by the executable
   experiment.
2. **Assumptions** — environmental, data, timing, failure-model, and mechanism
   conditions required for that property to hold.
3. **Non-guarantees** — nearby properties that the evidence does not establish.
4. **Evidence** — repeatable observations, assertions, and artifacts that
   support the claim.

The expected observation alone is not a guarantee. A passing scenario supports
only the stated invariant under the experiment's stated assumptions. Results
must not be generalized to providers, workloads, or failure modes that were not
tested.

## Current guarantees

M0 establishes repository structure, discovery metadata, and offline checks.
M1 adds one demonstrated evidence relationship guarantee:

> Given a catalog with unique immutable evidence identities and correct
> recorded document/version attribution, an evidence selection accepted by the
> M1 guard contains only known fragments whose recorded provenance equals the
> selection's declared provenance.

The executable evidence includes a coherent control, unknown-identity
rejection, incompatible document/version rejection, and a failure-first control
showing that identifier existence alone accepts the invalid relationship.

The guarantee assumes that catalog identity and recorded attribution are
authoritative inputs. It does not establish source truth, claim support,
retrieval completeness, evidence authenticity, upstream attribution
correctness, or a universal provenance model.

M2 adds one demonstrated evaluation-oracle guarantee:

> Given M1-valid evidence relationships, complete and correct atomic claim
> requirements, and correct explicit evidence support annotations, an M2
> passing verdict checks every represented requirement and finds each one in
> the checked evidence support.

The executable evidence includes a fully supported control, a false positive
from the relationship-only evaluator, and deterministic
`unsupported-requirement` rejection of the same partially unsupported claim.
The verdict records every checked requirement and stable rejection details.

This guarantee covers explicit support-requirement coverage. It does not
establish arbitrary natural-language entailment, source truth, evidence or
retrieval completeness, authenticity, upstream provenance correctness,
annotation correctness, general evaluator reliability, model alignment, or
universal hallucination detection.

M1 relationship validity is necessary input to M2, but it is not sufficient for
a passing M2 claim-support verdict.

M3–M7 invariants remain planned targets, not demonstrated guarantees. Their
registry descriptions communicate intent and do not claim implementation.

## Illustrative planned example

The `ambiguous-completion` experiment plans to investigate whether retries can
avoid duplicate logical operations after uncertain completion. Any later
guarantee would need to identify assumptions such as identifier stability,
storage behavior, and the precise failure window. It would not automatically
prove exactly-once delivery or correctness under every infrastructure failure.

This example is illustrative only; the experiment is not implemented.
