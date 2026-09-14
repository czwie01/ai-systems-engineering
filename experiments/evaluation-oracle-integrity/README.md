# Evaluation Oracle Integrity

## Engineering question

How can an evaluator reject unsupported claims instead of producing a passing
verdict merely because referenced evidence is valid?

## Failure model

A weak evaluator treats a valid evidence relationship as sufficient for a
passing claim-support verdict. It checks that cited evidence is known and
provenance-compatible, but does not check every support obligation represented
by the claim. The verdict therefore claims more than the evaluator established.

## Invariant

Under the experiment's explicit atomic support model, a passing verdict
requires every represented claim requirement to be included in the evaluator's
checked evidence support.

## Scenario

The synthetic evidence fragment `E21` has already passed the M1 identity and
provenance contract. Its explicit support annotation contains one proposition:

> The system supports Python 3.13.

The supported control claims only Python 3.13 support. The failure-first
candidate claims support for both Python 3.13 and Python 3.14 while citing the
same valid fragment.

## Mechanism under test

The claim is decomposed into explicit atomic support requirements. Validated
evidence records the requirement identities it supports. The integrity
evaluator checks every represented requirement against the combined explicit
support records and includes all checked and unsupported requirement identities
in its verdict.

The deliberately weak control checks only that the claim has requirements and
validated evidence is present. M1 validity is an input assumption; M2 neither
repeats nor broadens the M1 guard.

## Run it

```console
uv run ai-systems run evaluation-oracle-integrity
```

The probe is deterministic, synthetic, and offline.

## Expected observation

The complete Python 3.13 control passes. For the partially unsupported
candidate, the weak evaluator observes valid evidence and passes without
checking claim support. The integrity evaluator checks both atomic requirements
and deterministically rejects `supports-python-3.14` as
`unsupported-requirement`.

Repeated evaluation of the same inputs produces an equal verdict and the same
ordered rejection details.

## Guarantee established

Given:

- evidence relationships that have already passed M1;
- a complete and correct decomposition of the claim into atomic requirement
  identities; and
- correct explicit support annotations on the evidence;

an M2 passing verdict cannot omit a represented claim requirement from its
support check, and every represented requirement is present in the checked
evidence support.

The executable evidence includes a fully supported control, a weak-evaluator
false positive, deterministic rejection of the same partially unsupported
claim, and stable rejection details.

## What this does not prove

This experiment does not establish:

- universal natural-language entailment;
- factual truth of source material;
- evidence completeness or retrieval quality;
- evidence authenticity or correctness of upstream provenance;
- correctness of claim decomposition or support annotations;
- general LLM-as-judge reliability or model alignment;
- universal hallucination detection.

The experiment proves coverage within an explicit support model, not arbitrary
semantic understanding.

## Reusable capability

No reusable primitive promoted. M1 and M2 expose related but distinct
boundaries: evidence relationship validity and claim-support coverage. v0.1.0
does not treat either experiment-local API as a stable shared boundary.

## Related decision

[Decision 0001: Foundation principles](../../docs/decisions/0001-foundation-principles.md)
requires executable evidence before promotion into a reusable primitive. M2
follows that decision and introduces no new durable architectural choice.
