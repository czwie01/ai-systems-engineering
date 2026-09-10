# Decision 0001: Foundation principles

- **Status:** accepted
- **Scope:** M0

## Context

A long-lived reference repository can become misleading if exploratory history,
provider-specific behavior, and reusable mechanisms share the same boundary.
Public development also makes privacy review a design concern rather than a
final publication step.

## Decision

1. The repository is a distilled engineering reference, not a diary or a
   collection of disconnected tutorials.
2. Reusable core capabilities remain independent of AI providers and
   orchestration frameworks.
3. The default development and experiment path is offline and deterministic.
4. Executable experiment evidence must justify promotion of a mechanism into a
   reusable primitive.
5. Repository content is public by construction, including development history
   and automation output.

## Consequences

- Planned experiments are represented by metadata, not placeholder
  implementations or simulated results.
- Provider adapters, if later required by an experiment, remain outside the
  reusable core boundary.
- External services and credentials cannot become baseline requirements.
- Every guarantee must name its assumptions, evidence, and non-guarantees.
- Contributors must complete the publication checklist before sharing work.

These principles may be revised by a later engineering decision when executable
evidence demonstrates that a boundary no longer serves the mission.
