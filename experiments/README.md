# Experiments

This directory contains executable, milestone-scoped investigations of
difficult AI systems properties.

An implemented experiment must follow the
[experiment model](../docs/experiment-model.md), run without hidden inputs, and
state its evidence, assumptions, guarantee, and non-guarantees. Failed or
inconclusive observations remain valid evidence and must not be rewritten as
success.

v0.1.0 contains `evidence-contracts` (M1) and `evaluation-oracle-integrity`
(M2). The other five registered experiments remain `planned`; use
`uv run ai-systems list` to inspect their current status.
