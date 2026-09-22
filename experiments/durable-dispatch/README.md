# Durable Dispatch

## Engineering question

How can committed authoritative intent remain durably discoverable for
dispatch across process failure without requiring the original request process
to survive?

## Failure model

A process changes authoritative state and then separately publishes downstream
work:

```text
commit state
   |
   X crash
   |
publish/queue work
```

If the state commit and the dispatch write are independent, the state change
can survive while the work notification disappears. The authoritative system
then says work is required, but no dispatcher can discover what to do.

This is the dual-write failure addressed by the transactional outbox pattern.

## Invariant

> Given atomic commit of authoritative state plus durable dispatch intent,
> retention of unacknowledged intents, and eventual rescanning by a dispatcher,
> committed dispatch intent remains discoverable across process failure until
> acknowledgement.

M7 deliberately says **discoverable until acknowledged**, not exactly-once
delivery.

## Scenario

The experiment has three phases.

### 1. Naive dual-write loss

The authoritative SQLite row is changed to `dispatch-required@1` and committed.
The synthetic process then fails before the separate dispatch record is
inserted.

After reopening the durable store:

- authoritative state says downstream work is required;
- the outbox contains zero pending intents.

The work requirement survived, but its dispatch did not.

### 2. Transactional outbox survival

The protected path writes both facts in one SQLite transaction:

```text
authoritative state = dispatch-required
+
dispatch-001 = pending
```

The process then fails immediately after commit and before any dispatcher runs.

After reopening the database, the pending dispatch record is still present and
can be relayed. This removes the state-write / dispatch-write loss window inside
the declared single durable authority boundary.

### 3. Effect-before-ack replay

An outbox relay has another crash window:

```text
pending outbox
    |
external effect succeeds
    |
    X crash
    |
mark outbox acknowledged
```

The outbox row must remain pending until acknowledgement. After restart, it is
therefore replayed.

M7 composes with M4 for that replay: the dispatch id is reused as the logical
operation id at the idempotent effect boundary. The first relay creates one
visible effect; the retry resolves as `replayed`, creates no second visible
effect, and then acknowledges the outbox row.

## Mechanism under test

The provider-independent mechanism is a transactional outbox boundary:

- authoritative state and dispatch intent share one atomic durable commit;
- dispatch intent has stable immutable identity/content;
- unacknowledged intents are retained and queryable;
- acknowledgement happens only after the effect boundary reports success;
- a dispatcher can rescan pending records after process restart;
- effect-before-ack replay uses the M4 idempotency contract.

SQLite is only the deterministic experiment realization. Production systems
may realize the same semantics using a relational outbox table, transactional
change feed, workflow history, or another mechanism that can establish the same
observable guarantees.

## Run it

```console
uv run ai-systems run durable-dispatch
```

The experiment is offline, credential-free, provider-independent, and uses only
the Python standard library plus the already-demonstrated M4 primitive.

## Expected observation

The naive dual-write control reopens with committed authoritative state but no
pending dispatch.

The transactional-outbox path reopens with the committed pending intent, which
is then dispatched and acknowledged.

In the effect-before-ack path, one visible effect exists while the outbox row
remains pending after the simulated crash. Retry reuses the same operation id,
produces no additional visible effect under M4's assumptions, and acknowledges
the retained row.

## Guarantee established

Given atomic commit of authoritative state plus durable dispatch intent,
retention of unacknowledged intents, and eventual rescanning by a dispatcher,
committed dispatch intent remains discoverable across process failure until it
is acknowledged.

When dispatch completion itself is ambiguous, M4's separately demonstrated
stable-id/idempotent-effect assumptions can be composed with M7 so replay does
not add another application-visible effect while the M4 idempotency record is
retained.

## What this does not prove

M7 does not establish:

- exactly-once delivery or exactly-once execution;
- progress if no dispatcher ever runs again;
- a liveness bound or dispatch deadline;
- global ordering or fairness across many intents;
- poison-message retry/dead-letter policy;
- distributed consensus;
- an atomic transaction across unrelated databases/services;
- that every queue/workflow provider has equivalent semantics;
- that Temporal, a broker, CDC, or a custom outbox is the preferred runtime;
- that the Agentic Control Plane must own the dispatch authority.

The single-store atomicity assumption matters. If authoritative state lives in
one system and the dispatch/workflow start lives in another, the dual-write
problem reappears unless a higher-level mechanism changes the ownership
boundary or provides an equivalent durable handoff.

## Reusable capability

The reusable candidate is the semantic handoff:

```text
authoritative transition
        +
durable dispatch intent
        |
   one atomic commit
        |
        v
pending / discoverable
        |
  dispatcher rescan
        |
        v
external effect
        |
 acknowledge only after success
```

This is a semantic contract, not a requirement to build a bespoke queue.

## Related decision

M7 closes the planned M1–M7 experiment sequence. It composes with:

- M3 to classify uncertain effect completion;
- M4 to replay ambiguous dispatch safely under explicit idempotency/retention
  assumptions;
- M5 to retain attempts, observations, and recovery decisions;
- M6 when committing dispatch intent follows a generation-fenced authoritative
  promotion.

After M7, the next step is not an automatic M8. The repository should synthesize
which semantics are genuinely reusable, validate them in real consumers, and
characterize existing maintained runtimes such as Temporal against the
demonstrated contracts before deciding whether any new runtime component is
needed.
