# Contributing

Contributions should advance the mission: executable experiments and reusable
primitives for reliable AI-enabled software.

## Before proposing a change

1. Read the [architecture](docs/architecture.md), [experiment
   model](docs/experiment-model.md), and [publication
   policy](docs/publication-policy.md).
2. Keep an experiment narrow, executable, and explicit about its failure model.
3. Keep reusable capabilities independent of providers and frameworks.
4. Complete the publication policy's pre-publication checklist.

Do not submit private or production-derived material, credentials, raw AI
transcripts, or claims unsupported by checked-in evidence.

## Local validation

Install [uv](https://docs.astral.sh/uv/), then run:

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
uv run ai-systems run ambiguous-completion
uv run ai-systems run operation-provenance
```

Tests and examples must be deterministic and must not require credentials,
external services, paid APIs, model downloads, or a Docker daemon.

## Change design

- Add registry metadata only for an intentional milestone.
- Use the documented experiment headings for an implementation.
- State assumptions and non-guarantees as carefully as guarantees.
- Add an engineering decision only for a durable architectural choice.
- Prefer the standard library; each dependency must provide clear value.

Use concise, public-safe commit messages. A pull request should explain the
engineering question, evidence added, and any guarantee affected.
