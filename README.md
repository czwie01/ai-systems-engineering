# AI Systems Engineering

> Executable experiments and reusable primitives for reliable AI-enabled
> software.

AI-enabled systems combine probabilistic components, external providers,
distributed effects, and incomplete evidence. That combination makes ordinary
questions—what happened, whether a result is correct, and whether an operation
is safe to retry—surprisingly difficult to answer.

**Current status: post-v0.1 development.** v0.1.0 — Evidence & Evaluation
remains the latest release checkpoint. Development now includes M3
`failure-semantics`, a provider- and framework-neutral completion
classification experiment. M4–M7 remain planned. This project is still an Alpha
reference boundary, not a production-ready library or a 1.x compatibility
promise.

## Run it now

Prerequisites: [uv](https://docs.astral.sh/uv/) and a supported Python version
(3.13 or newer).

```console
git clone https://github.com/czwie01/ai-systems-engineering.git
cd ai-systems-engineering
uv sync
uv run ai-systems list
uv run ai-systems explain evidence-contracts
uv run ai-systems run evidence-contracts
uv run ai-systems explain evaluation-oracle-integrity
uv run ai-systems run evaluation-oracle-integrity
uv run ai-systems explain failure-semantics
uv run ai-systems run failure-semantics
```

`list` reports all registered experiments and their honest lifecycle status.
`explain` exposes the engineering question, area, milestone, status, and
intended invariant for one registered experiment. Unknown identifiers fail
with a non-zero exit status. `run` executes only experiments marked
`available`.

## What's in v0.1.0

This is the first public reference boundary. Demonstrated guarantees are
intentionally narrow and executable.

- M1 `evidence-contracts` — valid evidence identity is not sufficient for
  provenance compatibility.
- M2 `evaluation-oracle-integrity` — valid citations are not sufficient for
  claim support. Under the explicit atomic support model, every represented
  requirement must be supported before a passing verdict.

Read them in that order. A valid evidence relationship is not a supported
generated claim. The current development branch additionally contains M3
`failure-semantics`; that experiment is not part of the v0.1.0 release
checkpoint. M4–M7 remain planned. This Alpha boundary is not a stable public
library API and is not published to PyPI. See [CHANGELOG.md](CHANGELOG.md) for
the release record.

## Architecture

- `src/ai_systems/experiments/` is the canonical experiment metadata registry.
- `src/ai_systems/cli/` exposes discovery and registered experiment execution.
- `experiments/` documents narrow executable experiments as milestones land.
- `docs/` defines architecture, evidence standards, and public project
  contracts.
- Only mechanisms justified by experiment evidence may be promoted into a
  provider- and framework-independent library core.

See [Architecture](docs/architecture.md) and the
[experiment model](docs/experiment-model.md) for the boundaries.

## Roadmap

| Milestone | Experiment | Area | Status |
| --- | --- | --- | --- |
| M1 | `evidence-contracts` | evidence | available |
| M2 | `evaluation-oracle-integrity` | evaluation | available |
| v0.1 | Evidence & Evaluation | release checkpoint | v0.1.0 |
| M3 | `failure-semantics` | execution | available |
| M4 | `ambiguous-completion` | reliability | planned |
| M5 | `operation-provenance` | observability | planned |
| v0.2 | Reliable AI Execution | release checkpoint | planned |
| M6 | `concurrent-promotion` | coordination | planned |
| M7 | `durable-dispatch` | reliability | planned |
| v0.3 | Safe Agentic State Changes | release checkpoint | planned |

A roadmap entry is not evidence that its invariant holds.

## Guarantees and non-guarantees

Every completed experiment must state its demonstrated guarantee, assumptions,
evidence, and non-guarantees. Planned invariants express what an experiment
will investigate; they are not current guarantees. v0.1.0 contains the M1 identity/provenance compatibility guarantee and the M2
explicit claim-support coverage guarantee. Post-v0.1 development adds the M3
completion-classification guarantee under its explicit observation assumptions.
It does not claim a stable public API or production readiness.

Read the full [guarantee model](docs/guarantees.md).

## Public by construction

Every repository surface—including Git history, fixtures, pull request text,
and CI output—is treated as public. Contributions must use synthetic or
explicitly redistributable material and must not contain credentials, private
AI transcripts, production logs, or employer/customer material. See the
[publication policy](docs/publication-policy.md) before contributing.

## Development

```console
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run ai-systems list
uv run ai-systems run evidence-contracts
uv run ai-systems run evaluation-oracle-integrity
uv run ai-systems run failure-semantics
```

To apply formatting locally, run `uv run ruff format .`. Development and CI are
offline after dependencies are installed; they require no AI provider,
credentials, network service, Docker daemon, or model download.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution contract.

## License

Licensed under the [MIT License](LICENSE).
