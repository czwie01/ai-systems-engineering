# R2 — HITL orchestration restart characterization

Status: bounded characterization fixture for issue #9.

## Engineering question

Can two maintained permissive-open-source workflow frameworks express the same
explicit human-gated, bounded-repair control flow while surviving fresh
controller processes without silently duplicating side effects?

## Frameworks

- LangGraph 1.2.11 with `langgraph-checkpoint-sqlite` 3.1.1.
- Microsoft Agent Framework Core 1.19.0.

The Microsoft package is deliberately `agent-framework-core`, not Foundry,
Azure hosting, or any model-provider integration.

## Failure model

A workflow that appears resumable may still couple task state to one process,
lose pending human input, re-run non-idempotent work after resume, or make a
bounded repair loop depend on model-driven control.

## Scenario

Both runners implement the same deterministic semantic flow:

```text
CAPTURE
→ CHARACTERIZE
→ HUMAN INTENT GATE
→ EXECUTE attempt 0
→ OBSERVE
→ FALSIFY (forced failure)
→ REPAIR
→ EXECUTE attempt 1
→ OBSERVE
→ FALSIFY (pass)
→ HUMAN PROMOTION GATE
→ PACKAGE
```

The CI job runs each gate in a fresh Python process:

```text
start
process exits
resume-intent
process exits
resume-promotion
process exits
verify
```

No LLM, provider API, network service, credential, or hosted runtime participates
after dependencies are installed.

## Side-effect probe

`EXECUTE` writes an operation id to a local journal. The helper is explicitly
idempotent by operation id. The final receipt fails if an operation id appears
more than once or if the expected attempts are missing.

This does not claim the frameworks automatically make arbitrary side effects
idempotent. It characterizes whether an explicit idempotency boundary composes
cleanly with their resume semantics.

## Run

The pull-request-only workflow
`.github/workflows/orchestration-characterization.yml` installs exact framework
versions in isolated virtual environments and executes both runners.

Each job prints a JSON receipt. The receipt is characterization evidence only;
it does not select a framework or establish a reusable project guarantee.

## Non-guarantees

This fixture does not test model quality, agent delegation, hosted services,
distributed workers, production durability, MCP, OpenTelemetry exporters, or
multi-machine coordination. It does not establish that either framework is
preferred for the Agentic Engineering OS.
