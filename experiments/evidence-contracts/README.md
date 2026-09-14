# Evidence Contracts

## Engineering question

How can downstream AI-enabled software refer to evidence while preserving
enough identity and provenance information to reject invalid evidence
relationships deterministically?

## Failure model

An identifier-only validator confirms that every selected evidence ID exists
but never compares each fragment's recorded provenance with the provenance
declared by the candidate selection. Known fragments from different source
versions can therefore be accepted as one coherent set.

## Invariant

Under the declared identity/version model, an accepted evidence selection
contains only known fragments whose recorded provenance equals the selection's
declared provenance.

## Scenario

A synthetic catalog contains:

- `E17`, attributed to `synthetic-source/version-1`;
- `E18`, attributed to `synthetic-source/version-2`.

The invalid candidate declares `synthetic-source/version-1` and selects both
fragments. Both IDs exist, but `E18` conflicts with the declared version. A
coherent control selects only `E17`.

## Mechanism under test

The contract guard checks at the downstream acceptance boundary:

1. every selected identity resolves exactly once in the immutable catalog;
2. every resolved fragment's recorded document and version identity exactly
   equal the candidate's declared provenance.

The naïve control performs only the first check. Contract rejection uses stable
reason categories for unknown identity and incompatible provenance.

## Run it

```console
uv run ai-systems run evidence-contracts
```

The probe is deterministic, synthetic, and offline.

## Expected observation

The coherent control is accepted. For the invalid candidate, the naïve check
passes both known IDs and accepts the relationship. The contract check finds
that `E18` belongs to `version-2` and rejects the same relationship as
`incompatible-provenance`.

## Guarantee established

Given a catalog with unique immutable evidence identities and correct recorded
document/version attribution, any selection accepted by this guard contains
only known fragments whose recorded provenance equals the selection's declared
provenance.

Evidence consists of executable probes and tests for coherent acceptance,
unknown-identity rejection, document/version incompatibility rejection, and
the identifier-only control's blind spot.

## What this does not prove

This experiment does not establish:

- factual correctness of source content;
- whether evidence supports a generated claim;
- retrieval completeness;
- authenticity or absence of malicious fabrication;
- correctness of provenance recorded before validation;
- coverage of every possible provenance relationship.

Claim support is a separate concern demonstrated by
`evaluation-oracle-integrity`; this experiment does not establish it.

## Reusable capability

No primitive is promoted into a shared library in M1. The experiment-local
catalog and guard demonstrate provider-independent semantics, but v0.1.0 still
does not treat this API as a durable shared boundary. Later experiments may
justify extracting the identity/provenance guard without its scenario or
presentation code.

## Related decision

[Decision 0001: Foundation principles](../../docs/decisions/0001-foundation-principles.md)
requires executable evidence before promoting a mechanism and keeps the default
path provider-independent, offline, and deterministic. M1 follows that
decision and creates no new architectural decision.
