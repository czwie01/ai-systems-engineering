import pytest

from ai_systems.experiments.evidence_contracts import (
    EvidenceCatalog,
    EvidenceFragment,
    EvidenceSelection,
    ProvenanceContext,
    RejectionReason,
)


def _catalog() -> EvidenceCatalog:
    return EvidenceCatalog(
        (
            EvidenceFragment("E17", ProvenanceContext("source-a", "version-1")),
            EvidenceFragment("E18", ProvenanceContext("source-a", "version-2")),
            EvidenceFragment("E19", ProvenanceContext("source-b", "version-1")),
        )
    )


def test_valid_coherent_evidence_is_accepted() -> None:
    selection = EvidenceSelection(
        ProvenanceContext("source-a", "version-1"),
        ("E17",),
    )

    result = _catalog().validate(selection)

    assert result.accepted is True
    assert result.known_evidence_ids is True
    assert result.provenance_compatible is True
    assert result.reason is None


def test_unknown_evidence_identity_is_rejected() -> None:
    selection = EvidenceSelection(
        ProvenanceContext("source-a", "version-1"),
        ("not-registered",),
    )

    result = _catalog().validate(selection)

    assert result.accepted is False
    assert result.known_evidence_ids is False
    assert result.provenance_compatible is None
    assert result.reason is RejectionReason.UNKNOWN_EVIDENCE
    assert result.rejected_evidence_id == "not-registered"


@pytest.mark.parametrize("incompatible_id", ["E18", "E19"])
def test_known_evidence_with_incompatible_provenance_is_rejected(
    incompatible_id: str,
) -> None:
    selection = EvidenceSelection(
        ProvenanceContext("source-a", "version-1"),
        ("E17", incompatible_id),
    )

    result = _catalog().validate(selection)

    assert result.accepted is False
    assert result.known_evidence_ids is True
    assert result.provenance_compatible is False
    assert result.reason is RejectionReason.INCOMPATIBLE_PROVENANCE
    assert result.rejected_evidence_id == incompatible_id


def test_identifier_only_control_accepts_invalid_relationship() -> None:
    selection = EvidenceSelection(
        ProvenanceContext("source-a", "version-1"),
        ("E17", "E18"),
    )
    catalog = _catalog()

    assert catalog.identifiers_exist(selection) is True
    assert catalog.validate(selection).accepted is False
