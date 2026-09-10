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

## M0 position

M0 establishes repository structure, discovery metadata, and offline checks.
All M1–M7 invariants are planned targets, not demonstrated guarantees. Their
registry descriptions communicate intent and do not claim implementation.

## Illustrative planned example

The `ambiguous-completion` experiment plans to investigate whether retries can
avoid duplicate logical operations after uncertain completion. Any later
guarantee would need to identify assumptions such as identifier stability,
storage behavior, and the precise failure window. It would not automatically
prove exactly-once delivery or correctness under every infrastructure failure.

This example is illustrative only; the experiment is not implemented.
