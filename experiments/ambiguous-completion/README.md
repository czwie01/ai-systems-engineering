# Ambiguous Completion and Idempotency

## Engineering question

How can a caller safely retry one logical operation after completion is
ambiguous without silently creating a second application-visible effect?

## Failure model

M3 demonstrated a concrete crash boundary where an external effect is already
visible but execution completion is not durably recorded. Recovery can replay
the logical operation. Blind replay duplicated the effect in both characterized
workflow frameworks.

The M4 failure is therefore not "the framework crashed." It is:

```text
one logical operation
-> effect becomes visible
-> completion remains ambiguous
-> caller/runtime retries
-> second visible effect may occur
```

## Invariant

Given:

- a stable caller-provided operation id;
- a stable, complete immutable representation of the operation's intent;
- authoritative idempotency state retained across the retry window; and
- an atomic boundary that records the idempotency result together with the
  application-visible effect;

serial retries of one logical operation produce at most one
application-visible effect.

## Scenario

The experiment runs four controls:

1. **Naive retry** — the same logical request is applied twice after ambiguous
   completion; two visible effects are observed.
2. **Idempotent retry** — the same operation id and same intent are submitted
   twice; the second call replays the first result and one visible effect exists.
3. **Intent mismatch** — the same operation id is reused with different intent;
   the request is rejected as `idempotency-conflict`.
4. **Retention expiry** — the idempotency record is deliberately forgotten and
   the same request is submitted again; a second visible effect appears.

## Mechanism under test

`IdempotentEffectBoundary` is a deliberately small deterministic model.

It stores an authoritative binding:

```text
operation id -> immutable intent + prior result/effect identity
```

The model treats checking the idempotency record, applying the visible effect,
and storing the result as one atomic boundary. There is intentionally no crash
point inside that boundary.

This assumption is central. AWS's idempotent API guidance likewise notes that
the idempotency token and related mutation need an atomic/ACID boundary for a
strong at-most-once contract. AWS also recommends caller-provided request
identifiers and rejects the same identifier with different request intent.
Stripe similarly replays stored results for the same key, rejects changed
parameters, and documents that pruning the key ends the original deduplication
history.

Primary references:

- https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
- https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_prevent_interaction_failure_idempotent.html
- https://docs.stripe.com/api/idempotent_requests

These references motivate the experiment shape; they are not evidence that an
arbitrary provider implements this contract.

## Run it

```console
uv run ai-systems run ambiguous-completion
```

The default experiment is offline, deterministic, credential-free, and uses no
third-party dependency.

## Expected observation

The naive control produces two effects.

Under retained idempotency state, the first request is `applied`, the retry is
`replayed`, both calls return the same logical result, and only one visible
effect exists.

Reusing the operation id for different intent is rejected.

After explicit expiry of the idempotency record, retrying creates another
effect, showing that retention is part of the guarantee rather than an
implementation detail.

## Guarantee established

> Given stable operation identity and intent, retained authoritative
> idempotency state, and the experiment's atomic effect/record boundary, serial
> retries of one logical operation produce at most one application-visible
> effect.

## What this does not prove

The experiment does not establish:

- exactly-once delivery or exactly-once execution;
- safety once the idempotency record expires or is lost;
- correctness under concurrent racing callers;
- atomicity across an arbitrary third-party system and separate local state;
- provider-native idempotency behavior;
- durable dispatch;
- complete operation provenance;
- multi-actor shared authority or fencing.

The experiment models an atomic idempotency boundary; it does not solve how to
build that atomicity across systems that do not expose such a primitive.

## Reusable capability

The candidate reusable semantic is the small contract:

```text
stable operation id
+ stable complete intent
+ retained authoritative idempotency record
+ atomic effect/result binding
+ conflict on same id / different intent
```

The experiment does not yet justify promoting an implementation into the
reusable core. Downstream consumer evidence is still required.

## Related decision

M4 consumes M3's `ambiguous-completion` classification and establishes the
retry contract under a stronger explicit idempotency assumption.

M5 remains responsible for complete auditable operation history. M7 remains
responsible for durable dispatch. M6 remains responsible for concurrent shared
state promotion. This experiment creates no Control Plane requirement by
itself.
