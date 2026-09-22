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

v0.1.0 — Evidence & Evaluation contains the M1 and M2 guarantees below. They
are complementary: a valid evidence relationship is not a passing
claim-support verdict. Post-v0.1 development adds M3. M0 remains the repository
and discovery foundation.

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

M3 adds one demonstrated failure-classification guarantee:

> Given correct and authoritative values for external-effect visibility and
> completion recording, failures with equivalent values receive the same
> provider- and framework-independent completion classification regardless of
> their raw provider/framework failure labels.

The executable evidence contains three equivalent observation pairs with
deliberately different raw labels: no visible effect, visible effect without
recorded completion, and visible effect with recorded completion. The classifier
maps them respectively to `definite-no-effect`, `ambiguous-completion`, and
`completion-recorded`. It also rejects the inconsistent observation
"completion recorded while effect absent" under the experiment model.

This guarantee assumes the two observation facts are correct, authoritative, and
sufficient for the declared model. It does not establish exactly-once effects,
safe retries, reconciliation, durable dispatch, operation-provenance
completeness, distributed authority, or that every runtime exposes those facts.

M4–M7 invariants remain planned targets, not demonstrated guarantees. Their
registry descriptions communicate intent and do not claim implementation.

## Illustrative planned example

The `ambiguous-completion` experiment plans to investigate whether retries can
avoid duplicate logical operations after uncertain completion. Any later
guarantee would need to identify assumptions such as identifier stability,
storage behavior, and the precise failure window. It would not automatically
prove exactly-once delivery or correctness under every infrastructure failure.

This example is illustrative only; the experiment is not implemented.
