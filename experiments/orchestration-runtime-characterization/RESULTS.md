# R2 result — HITL orchestration restart characterization

- Date: 2026-09-21
- Fixture: issue #9
- Pull request: #10
- Evidence: GitHub Actions run 35608029019
- Repository CI: GitHub Actions run 35608028997

## Observed result

Both framework realizations completed the same deterministic fixture successfully.

| Observation | LangGraph 1.2.11 | Microsoft Agent Framework Core 1.19.0 |
| --- | --- | --- |
| Local durable store used | SQLite checkpointer 3.1.1 | FileCheckpointStorage |
| Fresh controller boundaries crossed | 2 | 2 |
| Human gates resumed after restart | intent, promotion | intent, promotion |
| Forced first attempt failed | yes | yes |
| Bounded repair executed | exactly once | exactly once |
| Second attempt passed | yes | yes |
| Final output | `packaged:candidate-1` | `packaged:candidate-1` |
| Side-effect operation ids | `execute-0`, `execute-1` | `execute-0`, `execute-1` |
| Duplicate operation ids | none | none |

The common trace was:

```text
capture
characterize
intent-approved
execute-0
observe-0
falsify-0-fail
repair-1
execute-1
observe-1
falsify-1-pass
promotion-approved
package
```

## What the fixture established

### LangGraph

The fixture used framework-native graph state, conditional routing, `interrupt()`,
`Command(resume=...)`, and a SQLite checkpointer. A new Python process could
reconstruct the thread, observe the pending gate, resume it, traverse the bounded
repair branch, pause at the second gate, and later finish.

### Microsoft Agent Framework

The fixture installed only `agent-framework-core`. It did not install or invoke
Foundry, Azure hosting, a model provider, or a hosted workflow service.

The fixture used `WorkflowBuilder`, custom `Executor` nodes,
`request_info` / `response_handler`, targeted message routing, and
`FileCheckpointStorage`. A new Python process could reconstruct the workflow
from a checkpoint, answer the persisted pending request, execute the repair path,
pause at the second request, and later finish.

## Lock-in characterization

The result does not support treating vendor ownership as equivalent to proprietary
lock-in.

Both tested frameworks are open-source realizations, but both create ordinary
framework coupling:

- the graph/executor APIs are framework-specific;
- resume/checkpoint representations are framework-specific;
- pending-request representation and continuation mechanics are framework-specific;
- migrating a live checkpoint from one framework to the other was not attempted
  and is not assumed possible.

The portable boundary in this fixture is therefore the **application semantic
contract**, not the framework checkpoint:

```text
intent
artifact state
acceptance facts
human decisions
operation ids
promotion decision
```

Those concepts can remain application-owned while a framework-specific checkpoint
is treated as execution continuation state.

The fixture observed no Azure/Foundry service requirement for Microsoft Agent
Framework Core and no LangSmith/LangGraph hosted-service requirement for
LangGraph. It did not characterize optional hosted products.

## Side-effect qualification

The runners supplied their own operation-id journal. Passing this fixture proves
that an explicit idempotency boundary composes with both tested resume mechanisms.

It does **not** prove either framework automatically makes arbitrary external side
effects exactly-once or idempotent.

## Framework-selection implication

This slice produces no overall framework selection.

For the tested capability only, both candidates remain viable. A later decision
should therefore discriminate on properties that this fixture did not test, such
as:

- framework-state portability and upgrade behavior;
- subworkflow composition under real consumer structure;
- MCP capability integration;
- OpenTelemetry and execution-receipt mapping;
- distributed/durable execution beyond a single machine;
- behavior when a crash occurs inside a side-effecting node rather than at a
  human gate.

## Next smallest slice

Do not broaden into a feature-count benchmark.

The next useful slice is a durability-boundary characterization: inject process
failure immediately before and after one externally visible operation, then
compare the native framework recovery semantics with an explicit durable
execution substrate only if the native result leaves a material gap.

No reusable core, Control Plane runtime, framework preference, or new repository
is justified by R2 alone.
