# Ambiguous Completion and Idempotency

## Engineering question

How can a caller recover when an external effect may already have happened but
execution completion was not durably recorded?

M3 gives this state the provider/framework-independent name
`ambiguous-completion`. R3 then demonstrated the failure concretely: both
tested workflow frameworks replayed an operation after a crash in this window,
and a naive sink produced a duplicate visible effect.

## Failure model

A caller submits one logical operation.

The external effect becomes visible, but the controller/runtime fails before it
can durably record successful completion. On recovery, the operation may be
retried.

Without a stable logical identity and an idempotent effect boundary, that replay
can create a second visible effect.

## Invariant

Given:

1. one stable logical operation id reused across attempts;
2. immutable operation content bound to that id;
3. a durable sink that atomically enforces uniqueness by that operation id;

retries of the same logical operation produce **at most one
application-visible effect**.

## Failure-first control

The experiment first submits the same operation twice to a deliberately naive
SQLite sink.

Because every attempt is accepted independently, two visible effects are
recorded.

That control is required evidence: simply showing that a protected sink produces
one row would not establish that the guard is doing useful work.

## Protected mechanism

The protected synthetic sink persists:

```text
operation_id -> immutable operation fingerprint
```

The operation id is a primary key. The immutable content fingerprint is derived
from structured serialization of the effect name and payload, rather than an
ambiguous delimiter-joined string.

On submission:

- unseen id + content -> `applied`;
- same id + same content -> `replayed` with no new visible effect;
- same id + different content -> reject `idempotency-conflict`.

The experiment reopens the SQLite sink before the retry so the result does not
depend on controller-process memory.

A separate negative control submits the same content with a **new operation id**.
That is correctly treated as a new logical effect. This demonstrates that
idempotency depends on stable operation identity, not content coincidence.

## Run it

```console
uv run ai-systems run ambiguous-completion
```

The experiment is deterministic, offline, provider-free, and uses only the
Python standard library.

## Demonstrated guarantee

Under the explicit assumptions above, retries of one logical operation produce
at most one application-visible effect.

This is an **at-most-one-visible-effect** guarantee for the protected synthetic
sink. It is not an exactly-once execution or delivery claim.

## What this does not prove

M4 does not establish:

- that an arbitrary provider accepts or correctly implements idempotency keys;
- that a local idempotency record can be made atomic with an unrelated external
  service;
- exactly-once execution or delivery;
- correctness under concurrent competing callers or stale actors (M6);
- complete attempt/effect/recovery audit history (M5);
- that committed operation intent is eventually dispatched (M7).

If a real provider has no idempotency key and no authoritative lookup by logical
operation identity, `ambiguous-completion` may require reconciliation or human
escalation rather than blind retry.

## Why Temporal is not part of M4

Temporal solves a different layer: durable workflow continuation, timers,
retries, and recovery after worker/process failure.

It does not remove the external atomicity gap tested here. Temporal's own
Activity guidance describes an at-least-once execution model where a Worker may
finish an external side effect and fail before the Temporal Service records
completion, after which the Activity is retried. Temporal therefore still
requires idempotent external effects/idempotency keys.

M4 isolates the contract that remains necessary underneath either LangGraph,
Microsoft Agent Framework, Temporal, or a custom caller.

Temporal becomes decision-relevant later if the unresolved problem is durable
dispatch, long-lived distributed execution, or reliable coordination rather
than duplicate suppression at the external-effect boundary.

## Roadmap handoff

- M3 tells us **what state we are in**: `ambiguous-completion`.
- M4 establishes **what makes retry safe under explicit assumptions**.
- M5 next asks **what durable evidence must be retained to explain attempts,
  recovery decisions, and effects**.
- M7 later asks **whether committed intent can disappear before dispatch**.
