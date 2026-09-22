# Concurrent Promotion and Generation Fencing

## Engineering question

How can multiple actors that observed the same authoritative state attempt
conflicting promotions without both being accepted?

M3–M5 dealt with one logical operation and its retries/history. M6 introduces a
different failure mode: **two valid actors can independently make decisions from
the same stale observation of shared authoritative state**.

## Failure model

Two actors both read:

```text
state = candidate
generation = 0
```

Actor A decides to promote the candidate to `approved`. Actor B independently
decides to promote the same candidate to `rejected`.

If each actor later performs an unconditional write based only on its earlier
observation, both writes can report success. The later write overwrites the
earlier one even though both actors acted from the same generation.

Workspace isolation, separate worktrees, or separate valid mutation grants do
not solve this shared-authority problem by themselves.

## Invariant

> Given one authoritative record and an atomic compare-and-swap on its expected
> source state and monotonically increasing generation, at most one competing
> transition can be accepted from one observed generation.

## Scenario

The experiment has three controls.

### 1. Naive stale-write control

Two real Python threads synchronize after both have read `candidate@0`.
They then issue different unconditional promotions.

Both report `applied`, and the authoritative generation advances twice. The
final value hides the fact that two transitions from the same stale observation
were accepted.

### 2. Generation-fenced promotion

The same synchronized competition is repeated, but each actor submits the
source state and generation it actually observed.

The SQLite update is a single atomic compare-and-swap:

```sql
UPDATE authority
SET state = :target,
    generation = generation + 1
WHERE state = :observed_state
  AND generation = :observed_generation
```

Exactly one actor changes `candidate@0` to a terminal state at generation 1.
The other actor's predicate no longer matches and is classified
`stale-generation`.

Closing and reopening the store reconstructs the same accepted state.

### 3. ABA / state-only control

Generation matters even when the state value later looks unchanged.

A stale actor observes `candidate@0`. Authority then moves:

```text
candidate@0 -> review@1 -> candidate@2
```

A guard that checks only `state == candidate` accepts the stale actor because
the value has returned to the expected string.

The generation-fenced guard rejects the same stale observation because
generation 0 is no longer authoritative.

## Mechanism under test

The portable mechanism is **generation fencing / optimistic compare-and-swap**:

- one authoritative state record;
- one monotonic generation attached to that record;
- actors carry the generation they actually observed;
- acceptance atomically checks source state + generation;
- each accepted mutation increments generation;
- stale attempts are rejected rather than silently overwriting newer authority.

SQLite is only the deterministic experiment mechanism. The contract does not
require SQLite in production.

## Run it

```console
uv run ai-systems run concurrent-promotion
```

The experiment is offline, credential-free, provider-independent, and uses only
the Python standard library.

## Expected observation

The naive control accepts two transitions from the same observed generation.

The protected concurrent run accepts exactly one transition and classifies the
other as `stale-generation`.

The state-only ABA control accepts a stale actor after the state cycles back,
while generation fencing rejects it.

## Guarantee established

Given one authoritative record and atomic compare-and-swap on the expected
source state and monotonically increasing generation, at most one competing
transition can be accepted from one observed generation.

## What this does not prove

M6 does not establish:

- distributed consensus or linearizability across arbitrary systems;
- a fairness policy for which actor wins;
- leases, locks, heartbeats, or dead-actor recovery;
- multi-row or multi-repository atomic transactions;
- that an external provider supports equivalent compare-and-swap semantics;
- Git merge-conflict prevention;
- durable dispatch of accepted work (M7);
- that the Agentic Control Plane must own the authoritative record.

If multiple systems must agree on the same generation but no existing
authoritative store can atomically fence stale actors, that becomes evidence for
a stronger shared-authority component. This experiment does not assume that
component in advance.

## Reusable capability

The reusable candidate is the semantic contract:

```text
observed state + observed generation
          |
          v
atomic compare-and-swap
          |
    +-----+------+
    |            |
 accepted     stale-generation
```

Promotion into a reusable core primitive still requires downstream consumer
evidence beyond this experiment.

## Related decision

This experiment directly characterizes the shared-state distinction exposed by
concurrent agent work: workspace isolation prevents local overwrite, while
generation-fenced integration authority prevents two stale actors from both
successfully changing one authoritative record.

M7 remains separate: after one promotion has been accepted, M7 asks whether a
committed intent to perform downstream work can silently disappear before
dispatch.
