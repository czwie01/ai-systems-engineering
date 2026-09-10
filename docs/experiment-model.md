# Experiment model

Every implemented experiment must use the following public structure. Sections
must contain concrete, falsifiable statements; a heading may not be omitted
because evidence is inconvenient or inconclusive.

```markdown
# <Experiment name>

## Engineering question
## Failure model
## Invariant
## Scenario
## Mechanism under test
## Run it
## Expected observation
## Guarantee established
## What this does not prove
## Reusable capability
## Related decision
```

The registry may describe a planned engineering question and intended
invariant before implementation. The remaining sections belong with executable
experiment evidence and must not be fabricated in advance.

An experiment should be small enough that a reader can connect the failure
model, mechanism, probe, and observation without relying on a provider's
undocumented behavior. If the observation does not support the invariant, the
result must remain visible and no reusable capability may be claimed from it.
