# AI Systems Engineering

> Executable experiments and reusable primitives for reliable AI-enabled
> software.

AI-enabled systems combine probabilistic components, external providers,
distributed effects, and incomplete evidence. That combination makes ordinary
questions—what happened, whether a result is correct, and whether an operation
is safe to retry—surprisingly difficult to answer.

**Current status: Foundation / M0.** This repository currently demonstrates a
small, offline project skeleton and truthful experiment discovery. The
reliability mechanisms described in the roadmap are planned; none is yet
implemented or established as a guarantee.

## Run it now

Prerequisites: [uv](https://docs.astral.sh/uv/) and a supported Python version
(3.13 or newer).

```console
git clone https://github.com/czwie01/ai-systems-engineering.git
cd ai-systems-engineering
uv sync
uv run ai-systems list
uv run ai-systems explain evidence-contracts
```

`list` reports all registered experiments and their honest lifecycle status.
`explain` exposes the engineering question, area, milestone, status, and
intended invariant for one registered experiment. Unknown identifiers fail
with a non-zero exit status.

## Architecture

- `src/ai_systems/experiments/` is the canonical experiment metadata registry.
- `src/ai_systems/cli/` exposes discovery now and leaves room for a later
  `run` command.
- `experiments/` will contain narrow executable experiments as milestones land.
- `docs/` defines architecture, evidence standards, and public project
  contracts.
- Only mechanisms justified by experiment evidence may be promoted into a
  provider- and framework-independent library core.

See [Architecture](docs/architecture.md) and the
[experiment model](docs/experiment-model.md) for the boundaries.

## Roadmap

| Milestone | Experiment | Area | Status |
| --- | --- | --- | --- |
| M1 | `evidence-contracts` | evidence | planned |
| M2 | `evaluation-oracle-integrity` | evaluation | planned |
| v0.1 | Evidence & Evaluation | release checkpoint | planned |
| M3 | `failure-semantics` | execution | planned |
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
will investigate; they are not current guarantees. M0 guarantees only that the
checked-in registry and CLI can be validated offline by the test suite.

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
```

To apply formatting locally, run `uv run ruff format .`. Development and CI are
offline after dependencies are installed; they require no AI provider,
credentials, network service, Docker daemon, or model download.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution contract.

## License

Licensed under the [MIT License](LICENSE).
