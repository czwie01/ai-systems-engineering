# Crash-boundary characterization

This optional characterization connects M3's provider-neutral observation model
to real workflow-runtime recovery behavior without making either framework a
dependency of the reusable experiment core.

## Matrix

Each framework runs four deterministic cases against a local SQLite sink:

| Case | Sink mode | Purpose |
| --- | --- | --- |
| crash before effect | naive | establish definite-no-effect and retry from the last checkpoint |
| crash after effect, before completion checkpoint | naive | expose duplicate external effects when replay is not idempotent |
| crash after effect, before completion checkpoint | idempotent | test the same replay with an application-owned idempotency boundary |
| crash after the effect's completion checkpoint | naive | establish that the completed effect step is not replayed |

The runner records one attempt before every effect execution. A hard process exit
with code 86 is injected exactly once per case. The next process inspects durable
framework state *before* recovery, maps the observation through M3, resumes, and
verifies the final sink.

## Roadmap ownership

This characterization deliberately does not collapse the existing milestones.

- M3 consumes the crash observation classification.
- M4 owns the guarantee that retries of an ambiguous logical operation do not
  duplicate application-visible effects under explicit idempotency assumptions.
- M5 owns the durable audit/provenance record of attempts, decisions, and effects.
- M7 owns committed-intent-to-dispatch durability.
- M6 remains out of scope.

A duplicated naive effect is evidence for M4, not a reason to enlarge M3.

## Temporal boundary

Temporal is not executed in this slice unless native characterization leaves a
residual semantic that a Temporal comparison could distinguish. Temporal's own
current documentation says Activities can execute more than once when a Worker
finishes an external side effect but fails before reporting completion, and
therefore recommends idempotent Activities/idempotency keys. That is the same
dangerous boundary being characterized here, so Temporal is not assumed to
remove external-effect ambiguity by itself.

## Execution

The pull-request workflow
`.github/workflows/failure-boundary-characterization.yml` installs exact
framework versions in isolated environments and runs each case across fresh
Python processes. The repository's default dependency set remains unchanged.
