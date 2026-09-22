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
claim-support verdict. Post-v0.1 development adds M3, M4, and M5. M0 remains
the repository and discovery foundation.

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

M4 adds one demonstrated ambiguous-completion retry guarantee:

> Given a stable logical operation id, immutable operation content bound to that
> id, and a durable atomic idempotency record retained across the retry window
> that binds the operation to its visible effect identity, retries of the same
> logical operation produce at most one application-visible effect while that
> record is retained.

The executable evidence includes a failure-first naive control where retrying
one logical operation creates two visible effects, a protected retry after the
sink is reopened where the same stable id replays the same effect identity with
one visible effect, rejection of the same id with different content as
`idempotency-conflict`, a control showing that minting a new id makes the same
content a new logical effect, and a retention-boundary control where deleting
only the idempotency record leaves the original effect visible but allows the
same logical operation to create a second effect.

The guarantee depends on stable identity reuse plus a durable atomic
idempotency record retained for the complete retry window. Once that record is
expired or pruned, the demonstrated at-most-one guarantee no longer applies. It
does not establish exactly-once execution or delivery, arbitrary provider
idempotency, atomicity across an unrelated external provider and local database,
concurrent fencing, complete operation provenance, or durable dispatch.

M5 adds one demonstrated operation-provenance guarantee:

> Under the declared event model, a valid provenance journal preserves one
> operation's immutable intent identity, ordered attempts, completion
> observations, ambiguous-completion recovery decisions, observed effect
> identities, and final disposition well enough to distinguish a recovered
> retry from an otherwise identical direct-success final summary.

The executable evidence first proves that a final-state-only summary collapses a
direct success and an ambiguous-completion recovery into the same final result.
The protected journal retains the different attempt/mechanism/completion path,
rejects a removed recovery decision as `missing-recovery-decision`, rejects
invalid references and mixed intent, and reconstructs the same audit view after
the SQLite journal is reopened.

The guarantee assumes journal contents and recorded observations are correct
inputs. It does not establish cryptographic authenticity, tamper evidence,
external-effect truth, full distributed tracing, hidden reasoning capture,
concurrent fencing, or durable dispatch.

M6–M7 invariants remain planned targets, not demonstrated guarantees. Their
registry descriptions communicate intent and do not claim implementation.
