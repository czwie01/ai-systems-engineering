# R3 result — external-effect crash boundaries

- Date: 2026-09-21
- Issue: #11
- Stacked pull request: #12
- Characterization commit: `11aebe03470a2bae7f445d863e7095136bd9f1ea`
- Repository CI: run 35629282066 — success
- Failure-boundary characterization: run 35629282152 — success

## Observed matrix

The same four cases passed in LangGraph 1.2.11 and Microsoft Agent Framework
Core 1.19.0.

| Crash boundary | Sink policy | Class at crash | Completion recorded | Effect visible at crash | Effect executions after recovery | Visible effects after recovery |
| --- | --- | --- | --- | --- | ---: | ---: |
| before effect | naive | `definite-no-effect` | no | no | 2 | 1 |
| after effect, before checkpoint | naive | `ambiguous-completion` | no | yes | 2 | 2 |
| after effect, before checkpoint | idempotent | `ambiguous-completion` | no | yes | 2 | 1 |
| after effect completion checkpoint | naive | `completion-recorded` | yes | yes | 1 | 1 |

For LangGraph, the crash inspection exposed `effect` as the next node before the
completion checkpoint and `post_checkpoint` after it. For Microsoft Agent
Framework, the corresponding persisted checkpoint iteration counts were 1 and
2 in this fixture.

## Failure-first observation

The important negative control is the naive post-effect/pre-checkpoint case.

Both frameworks had already produced the externally visible effect when the
process terminated, but neither had durably recorded completion of the effect
step. Recovery therefore executed the effect step again. With the deliberately
naive sink, one logical operation produced two visible effects.

This is evidence that framework checkpoint/resume semantics alone do not provide
an exactly-once external-effect guarantee at this crash boundary.

## Application idempotency observation

The identical post-effect/pre-checkpoint case was repeated with a stable
operation id and an application-owned idempotency check at the sink.

Both frameworks still executed the effect step twice, but the sink admitted one
visible effect. In this single-actor local fixture, the idempotency boundary
converted replay into one application-visible effect.

This establishes only composition with the tested local sink. It does not yet
establish M4's general retry guarantee, atomicity under concurrency, or
idempotency support from arbitrary external providers.

## Roadmap interpretation

### M3 — failure-semantics

The framework observations map cleanly to M3's provider/framework-independent
classification:

- effect absent + completion absent -> `definite-no-effect`;
- effect visible + completion absent -> `ambiguous-completion`;
- effect visible + completion recorded -> `completion-recorded`.

M3 owns only this classification boundary.

### M4 — ambiguous-completion

R3 now provides a concrete failure-first input for M4:

`ambiguous-completion` plus blind replay duplicated the effect, while the same
replay plus a stable idempotency boundary did not.

M4 should therefore test the smallest portable contract for logical operation
identity, retry/reconciliation, and the assumptions under which at-most-one
application-visible effect can actually be claimed.

### M5 — operation-provenance

The fixture recorded operation attempts and visible effects, but that is not yet
a complete audit contract. M5 should decide the minimal durable record needed to
answer what was attempted, what was observed, which recovery decision was made,
and what effect identity resulted.

### M7 — durable-dispatch

R3 did not test whether committed dispatch intent can be silently lost before
any worker/runtime receives it. M7 remains separate and planned.

### M6 — concurrent-promotion

No shared promotion authority or competing actors were involved. R3 provides no
evidence for M6.

## Temporal decision

Do not add Temporal to this slice.

Current Temporal documentation describes Activities as retryable and documents
the same dangerous window: a Worker can complete an external side effect and
fail before the Temporal Service records completion, causing the Activity to be
retried. Temporal therefore recommends idempotent Activities and idempotency
keys for external side effects.

That means the residual semantic demonstrated here — ambiguity between an
external effect becoming visible and execution completion becoming durable — is
not removed merely by substituting Temporal for the two tested workflow
frameworks.

Temporal remains a legitimate later comparison for a different question, most
naturally M7 durable dispatch or a demonstrated need for distributed durable
workflow execution. It is not justified by R3 as a fix for external-effect
exactly-once semantics.

## Control Plane routing

Under the Control Plane requirement-admission test, this slice currently shows
an **execution-continuation** problem plus an **application operation identity**
requirement. It does not establish a need for `DURABLE_SHARED_AUTHORITY`.

Escalation to Control Plane shared authority would require later evidence that
multiple independent actors must agree on one authoritative operation state,
that provider/framework ownership plus thin composition is insufficient, and
that stale actors must be fenced.

## What R3 does not prove

R3 does not establish:

- exactly-once delivery or execution;
- correctness under concurrent callers;
- atomicity across an arbitrary external provider and local state;
- distributed recovery;
- complete operation provenance;
- durable dispatch;
- shared mutation authority;
- a preferred workflow framework.

The next milestone should consume the demonstrated
`ambiguous-completion` case rather than starting another general framework
benchmark.


## Normalized-head revalidation

After R2 PR #10 was accepted and squash-merged, this R3 branch was normalized to
one commit directly on top of the accepted R2 state. No executable or result
semantics changed during normalization.

Final pre-merge revalidation before this note:

- normalized characterization head: `4c7ad5fdf42e1c092562a71cde3431bb927e81a6`;
- repository CI: run `35718660844` — Python 3.13 and Python 3.14 both successful;
- failure-boundary characterization: run `35718660872` — all 8
  framework/scenario/mode jobs successful.

The earlier run ids above remain the original R3 evidence. This section binds the
same characterized tree, after stack normalization, to the current `develop`
lineage. The documentation-only commit containing this note must itself pass the
normal repository CI before merge.
