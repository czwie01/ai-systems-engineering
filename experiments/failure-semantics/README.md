# Provider-Neutral Failure Semantics

## Engineering question

How can provider or framework failures map to stable application semantics without
making vendor-specific exception names or checkpoint representations part of the
application contract?

## Failure model

Two execution systems can report different raw failures for the same observable
state around an external effect. If application behavior branches on those raw
labels, equivalent failures can produce different recovery decisions.

The experiment intentionally separates:

- raw provider/framework failure labels;
- whether the external effect is observably visible;
- whether successful completion is durably recorded by the execution mechanism.

## Invariant

Under the declared observation model, failures with equivalent effect visibility
and completion-recording facts receive the same provider- and framework-independent
completion classification.

## Scenario

Three synthetic observation classes are represented twice with deliberately
different raw provider labels:

1. effect absent and completion not recorded;
2. effect visible and completion not recorded;
3. effect visible and completion recorded.

The weak control compares raw failure labels. The contract classifier ignores
those labels and maps the observable facts to:

- `definite-no-effect`;
- `ambiguous-completion`;
- `completion-recorded`.

A fourth state — completion recorded while the effect is absent — is rejected as
inconsistent under this experiment's assumptions.

## Mechanism under test

`FailureObservation` is an application-owned observation record.
`classify_completion()` maps it to the `CompletionClass` enum.

The classifier contains no LangGraph, Microsoft Agent Framework, Temporal, model
provider, cloud, or transport dependency.

## Run it

```console
uv run ai-systems run failure-semantics
```

The default experiment remains offline and deterministic.

The framework crash-boundary characterization under `characterization/` is
additional evidence that asks whether real execution runtimes expose observations
that can be mapped into this model. Those optional characterization dependencies
are not part of the library core.

## Expected observation

The raw labels disagree between the two synthetic providers while each pair of
equivalent observable states receives the same application classification.

## Guarantee established

Given correct and authoritative values for `effect_visible` and
`completion_recorded`, the classifier returns the same completion class for
equivalent observations regardless of the provider/framework-specific failure
label.

## What this does not prove

This experiment does not establish:

- exactly-once external effects;
- safe retry or reconciliation behavior;
- durable dispatch;
- correctness or availability of the external-effect observation;
- correctness or availability of framework checkpoint state;
- operation provenance completeness;
- multi-actor coordination or fencing.

In particular, `ambiguous-completion` names the state that M4 must address. It
does not solve that state.

## Reusable capability

The reusable candidate is a small provider-independent completion-classification
primitive and its observation vocabulary.

Promotion beyond the experiment remains contingent on downstream evidence that
the vocabulary is useful across genuinely different consumers.

## Related decision

This experiment consumes the bounded orchestration characterization from issue
#11 only as framework evidence. It preserves the existing roadmap boundary:

- M3 owns failure classification;
- M4 owns idempotency/reconciliation for ambiguous completion;
- M5 owns auditable operation history;
- M7 owns durable dispatch;
- M6 remains unrelated to this single-operation failure boundary.
