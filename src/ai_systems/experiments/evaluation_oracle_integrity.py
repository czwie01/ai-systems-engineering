"""Executable evaluation oracle integrity experiment."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class SupportRequirement:
    """One atomic support obligation represented by a claim."""

    identifier: str
    statement: str


@dataclass(frozen=True, slots=True)
class Claim:
    """A synthetic claim decomposed into explicit support requirements."""

    statement: str
    requirements: tuple[SupportRequirement, ...]


@dataclass(frozen=True, slots=True)
class ValidatedEvidenceFragment:
    """Evidence whose identity and provenance are assumed to have passed M1."""

    identifier: str
    supported_requirement_ids: frozenset[str]


class RejectionReason(StrEnum):
    """Deterministic evaluation rejection categories."""

    UNSUPPORTED_REQUIREMENT = "unsupported-requirement"


@dataclass(frozen=True, slots=True)
class EvaluationVerdict:
    """Result of checking every explicit claim support requirement."""

    passed: bool
    checked_requirement_ids: tuple[str, ...]
    unsupported_requirement_ids: tuple[str, ...]
    reason: RejectionReason | None


def relationship_only_accepts(
    claim: Claim,
    evidence: tuple[ValidatedEvidenceFragment, ...],
) -> bool:
    """Apply the deliberately weak control that never checks claim support."""

    return bool(claim.requirements and evidence)


def evaluate_claim_support(
    claim: Claim,
    evidence: tuple[ValidatedEvidenceFragment, ...],
) -> EvaluationVerdict:
    """Check every represented requirement against explicit evidence support."""

    supported_requirement_ids = {
        requirement_id
        for fragment in evidence
        for requirement_id in fragment.supported_requirement_ids
    }
    checked_requirement_ids = tuple(
        requirement.identifier for requirement in claim.requirements
    )
    unsupported_requirement_ids = tuple(
        requirement.identifier
        for requirement in claim.requirements
        if requirement.identifier not in supported_requirement_ids
    )

    if unsupported_requirement_ids:
        return EvaluationVerdict(
            passed=False,
            checked_requirement_ids=checked_requirement_ids,
            unsupported_requirement_ids=unsupported_requirement_ids,
            reason=RejectionReason.UNSUPPORTED_REQUIREMENT,
        )

    return EvaluationVerdict(
        passed=True,
        checked_requirement_ids=checked_requirement_ids,
        unsupported_requirement_ids=(),
        reason=None,
    )


def run_experiment() -> int:
    """Run and present the synthetic failure-first evaluation probe."""

    supports_python_313 = SupportRequirement(
        "supports-python-3.13",
        "The system supports Python 3.13.",
    )
    supports_python_314 = SupportRequirement(
        "supports-python-3.14",
        "The system supports Python 3.14.",
    )
    evidence = (
        ValidatedEvidenceFragment(
            "E21",
            frozenset({supports_python_313.identifier}),
        ),
    )
    supported_claim = Claim(
        "The system supports Python 3.13.",
        (supports_python_313,),
    )
    partially_unsupported_claim = Claim(
        "The system supports Python 3.13 and Python 3.14.",
        (supports_python_313, supports_python_314),
    )

    supported_verdict = evaluate_claim_support(supported_claim, evidence)
    naive_accepts = relationship_only_accepts(partially_unsupported_claim, evidence)
    protected_verdict = evaluate_claim_support(partially_unsupported_claim, evidence)

    if (
        not supported_verdict.passed
        or not naive_accepts
        or protected_verdict.passed
        or protected_verdict.reason is not RejectionReason.UNSUPPORTED_REQUIREMENT
        or protected_verdict.unsupported_requirement_ids != ("supports-python-3.14",)
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    print("SUPPORTED CONTROL")
    print("claim: The system supports Python 3.13.")
    print("evidence: E21 (identity and provenance valid)")
    print("support requirement: Python 3.13 = PASS")
    print("verdict: PASS")
    print()
    print("PARTIALLY UNSUPPORTED CLAIM")
    print("claim: The system supports Python 3.13 and Python 3.14.")
    print("evidence: E21 supports only Python 3.13")
    print()
    print("NAIVE EVALUATOR")
    print("evidence identity: PASS")
    print("provenance compatibility: PASS")
    print("claim support requirements: NOT CHECKED")
    print("verdict: PASS")
    print()
    print("INTEGRITY EVALUATOR")
    print("support requirement: Python 3.13 = PASS")
    print("support requirement: Python 3.14 = FAIL")
    print("verdict: REJECTED (unsupported-requirement: supports-python-3.14)")
    print()
    print("GUARANTEE")
    print(
        "Under the explicit atomic support model, a passing verdict requires every "
        "represented claim requirement to be included in the evaluator's checked "
        "evidence support."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish arbitrary natural-language entailment, source "
        "truth, retrieval completeness, or general evaluator reliability."
    )
    return 0
