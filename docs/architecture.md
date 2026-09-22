# Architecture

## Purpose

The repository separates evidence-producing experiments from reusable
primitives. Experiments investigate one difficult systems property at a time.
The library core receives a mechanism only after executable evidence justifies
its behavior and its boundary is provider- and framework-independent.

## Layers

1. **Public interface** — `ai-systems` makes registered experiments
   discoverable and dispatches available experiments with `run`.
2. **Experiment registry** — immutable metadata describes every known
   experiment and associates an available experiment with its runner without
   implying that execution establishes a broader guarantee.
3. **Executable experiments** — milestone code owns scenarios, probes, expected
   observations, and evidence. Planned experiments have no placeholder
   implementation directories.
4. **Synthesis / promotion boundary** — completed experiment guarantees are
   classified before any mechanism moves inward. Promotion requires an explicit
   destination, missing-evidence check, and real-consumer validation.
5. **Reusable core** — future capabilities may be promoted only when executable
   evidence plus consumer validation justify a small provider- and
   framework-independent mechanism.

Dependencies should point inward: experiments may use the reusable core, but
the core must not depend on experiment code or a specific AI provider.

## Operating constraints

- The default path is offline and deterministic.
- No baseline check requires credentials, a provider, a model, or a service.
- Synthetic or explicitly redistributable material is the only acceptable
  input to committed scenarios and fixtures.
- Metadata status is authoritative. A planned invariant is not a guarantee.

These boundaries are recorded in
[Decision 0001](decisions/0001-foundation-principles.md). The current
post-M7 promotion decisions are tracked in the
[M1–M7 synthesis and promotion map](m1-m7-synthesis-and-promotion-map.md).
