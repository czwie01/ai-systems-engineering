# Architecture

## Purpose

The repository separates evidence-producing experiments from reusable
primitives. Experiments investigate one difficult systems property at a time.
The library core receives a mechanism only after executable evidence justifies
its behavior and its boundary is provider- and framework-independent.

## Layers

1. **Public interface** — `ai-systems` makes registered experiments
   discoverable. M0 supports `list` and `explain`; a future `run` command can
   dispatch implemented experiments through the same registry boundary.
2. **Experiment registry** — immutable metadata describes every known
   experiment without implying implementation or success.
3. **Executable experiments** — future milestone code will own scenarios,
   probes, expected observations, and evidence. Planned experiments have no
   placeholder implementation directories.
4. **Reusable core** — future capabilities may be promoted only when an
   experiment establishes a useful guarantee under explicit assumptions.

Dependencies should point inward: experiments may use the reusable core, but
the core must not depend on experiment code or a specific AI provider.

## Operating constraints

- The default path is offline and deterministic.
- No baseline check requires credentials, a provider, a model, or a service.
- Synthetic or explicitly redistributable material is the only acceptable
  input to committed scenarios and fixtures.
- Metadata status is authoritative. A planned invariant is not a guarantee.

These boundaries are recorded in
[Decision 0001](decisions/0001-foundation-principles.md).
