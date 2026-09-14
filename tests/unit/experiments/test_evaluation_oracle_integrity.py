from ai_systems.experiments.evaluation_oracle_integrity import (
    Claim,
    RejectionReason,
    SupportRequirement,
    ValidatedEvidenceFragment,
    evaluate_claim_support,
    relationship_only_accepts,
)

PYTHON_313 = SupportRequirement(
    "supports-python-3.13",
    "The system supports Python 3.13.",
)
PYTHON_314 = SupportRequirement(
    "supports-python-3.14",
    "The system supports Python 3.14.",
)
VALID_EVIDENCE = (
    ValidatedEvidenceFragment(
        "E21",
        frozenset({PYTHON_313.identifier}),
    ),
)


def test_fully_supported_claim_is_accepted() -> None:
    claim = Claim(
        "The system supports Python 3.13.",
        (PYTHON_313,),
    )

    verdict = evaluate_claim_support(claim, VALID_EVIDENCE)

    assert verdict.passed is True
    assert verdict.checked_requirement_ids == ("supports-python-3.13",)
    assert verdict.unsupported_requirement_ids == ()
    assert verdict.reason is None


def test_partially_unsupported_claim_is_rejected() -> None:
    claim = Claim(
        "The system supports Python 3.13 and Python 3.14.",
        (PYTHON_313, PYTHON_314),
    )

    verdict = evaluate_claim_support(claim, VALID_EVIDENCE)

    assert verdict.passed is False
    assert verdict.checked_requirement_ids == (
        "supports-python-3.13",
        "supports-python-3.14",
    )
    assert verdict.unsupported_requirement_ids == ("supports-python-3.14",)
    assert verdict.reason is RejectionReason.UNSUPPORTED_REQUIREMENT


def test_relationship_only_control_falsely_accepts_unsupported_claim() -> None:
    claim = Claim(
        "The system supports Python 3.13 and Python 3.14.",
        (PYTHON_313, PYTHON_314),
    )

    assert relationship_only_accepts(claim, VALID_EVIDENCE) is True
    assert evaluate_claim_support(claim, VALID_EVIDENCE).passed is False


def test_rejection_is_deterministic_for_identical_inputs() -> None:
    claim = Claim(
        "The system supports Python 3.13 and Python 3.14.",
        (PYTHON_313, PYTHON_314),
    )

    first_verdict = evaluate_claim_support(claim, VALID_EVIDENCE)
    second_verdict = evaluate_claim_support(claim, VALID_EVIDENCE)

    assert first_verdict == second_verdict
    assert first_verdict.reason is RejectionReason.UNSUPPORTED_REQUIREMENT
    assert first_verdict.unsupported_requirement_ids == ("supports-python-3.14",)
