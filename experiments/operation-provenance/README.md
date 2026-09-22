# Operation Provenance

## Engineering question

How can one logical operation retain enough durable, provider-independent
history to explain what was intended, attempted, observed, retried, and finally
accepted?

M3 classifies the completion state. M4 establishes the stable operation identity
and idempotency assumptions that make an ambiguous retry safe. M5 asks a
different question: **can an auditor reconstruct the recovery path later?**

## Failure-first control

A final-state-only record can say:

```text
operation-001
status = succeeded
effect = effect-001
```

That looks adequate until two materially different histories end in exactly that
same state:

```text
History A:
attempt-1 -> completion-recorded -> succeeded

History B:
attempt-1 -> effect observed -> ambiguous-completion
          -> explicit retry decision
attempt-2 -> same effect observed -> completion-recorded -> succeeded
```

The experiment first proves that the final summaries are equal. The summary
therefore cannot explain whether recovery happened, why it happened, or which
mechanisms were involved.

## Provenance contract

The smallest tested event vocabulary records:

- one operation registration with stable operation id, effect kind, and immutable
  intent fingerprint;
- ordered attempt starts with attempt id and execution mechanism;
- observed external effect identities;
- one completion observation for every started attempt;
- an explicit recovery decision for every ambiguous completion;
- one final disposition and, for success, an observed authoritative effect id.

The journal deliberately records **observable facts and explicit decisions**.
It does not require private model reasoning, chain-of-thought, provider-internal
checkpoint blobs, or full prompts/transcripts.

## Deterministic validation

A history is rejected when, among other things:

- event sequence numbers are not contiguous;
- operation ids or intent fingerprints are mixed;
- an event references an unknown attempt;
- an attempt lacks a completion observation;
- an ambiguous completion lacks an explicit recovery decision;
- final success references an effect that was never observed.

The experiment includes a negative control that removes the retry decision from
the ambiguous history and receives
`missing-recovery-decision`.

## Durability fixture

The synthetic `ProvenanceJournal` stores events in SQLite, closes, reopens, and
reconstructs the same audit view.

SQLite is only the experiment mechanism. The demonstrated contract is the event
content and validation semantics, not a requirement that production users adopt
SQLite.

## Run it

```console
uv run ai-systems run operation-provenance
```

The experiment is deterministic, offline, provider-free, and uses only the
Python standard library.

## Demonstrated guarantee

Under the declared event model, a valid provenance journal preserves one
operation's immutable intent identity, ordered attempts, completion
observations, ambiguous-completion recovery decisions, observed effect
identities, and final disposition well enough to distinguish a recovered retry
from an otherwise identical direct-success final summary.

## What this does not prove

M5 does not establish:

- cryptographic authenticity or tamper evidence;
- that an external effect observation is truthful or complete;
- full distributed tracing;
- prompt/model transcript retention requirements;
- hidden reasoning capture;
- concurrency control or stale-actor fencing (M6);
- committed-intent delivery or durable dispatch (M7);
- a universal event-sourcing architecture;
- that the Control Plane must own this journal.

A production owner can map these semantic fields onto an existing workflow
history, provider receipt, database, event log, or other evidence store if that
surface satisfies the contract.

## Roadmap handoff

After M5, the Reliable AI Execution sequence has three complementary primitives:

```text
M3: classify what completion state was observed
M4: make ambiguous retry safe under explicit idempotency assumptions
M5: retain enough durable provenance to explain the attempts and recovery
```

M6 then changes the problem from one logical operation to competing actors over
shared authoritative state. M7 separately asks whether committed operation
intent can disappear before dispatch.
