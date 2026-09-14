"""Executable evidence identity and provenance compatibility experiment."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ProvenanceContext:
    """Identity of one immutable version of a source document."""

    document_id: str
    version_id: str


@dataclass(frozen=True, slots=True)
class EvidenceFragment:
    """An immutable evidence identity with recorded provenance."""

    identifier: str
    provenance: ProvenanceContext


@dataclass(frozen=True, slots=True)
class EvidenceSelection:
    """A candidate selection and the provenance it declares."""

    declared_provenance: ProvenanceContext
    evidence_ids: tuple[str, ...]


class RejectionReason(StrEnum):
    """Deterministic evidence contract rejection categories."""

    UNKNOWN_EVIDENCE = "unknown-evidence"
    INCOMPATIBLE_PROVENANCE = "incompatible-provenance"


@dataclass(frozen=True, slots=True)
class ContractResult:
    """Outcome of enforcing the evidence selection contract."""

    accepted: bool
    known_evidence_ids: bool
    provenance_compatible: bool | None
    reason: RejectionReason | None
    rejected_evidence_id: str | None


class EvidenceCatalog:
    """Immutable lookup state required to validate evidence selections."""

    __slots__ = ("_fragments",)

    def __init__(self, fragments: Iterable[EvidenceFragment]) -> None:
        index: dict[str, EvidenceFragment] = {}
        for fragment in fragments:
            if fragment.identifier in index:
                raise ValueError(
                    f"duplicate evidence identifier: {fragment.identifier}"
                )
            index[fragment.identifier] = fragment
        self._fragments: Mapping[str, EvidenceFragment] = MappingProxyType(index)

    def identifiers_exist(self, selection: EvidenceSelection) -> bool:
        """Apply the intentionally weak identifier-only control."""

        return all(
            identifier in self._fragments for identifier in selection.evidence_ids
        )

    def validate(self, selection: EvidenceSelection) -> ContractResult:
        """Require known identities and exact declared provenance compatibility."""

        for identifier in selection.evidence_ids:
            if identifier not in self._fragments:
                return ContractResult(
                    accepted=False,
                    known_evidence_ids=False,
                    provenance_compatible=None,
                    reason=RejectionReason.UNKNOWN_EVIDENCE,
                    rejected_evidence_id=identifier,
                )

        for identifier in selection.evidence_ids:
            fragment = self._fragments[identifier]
            if fragment.provenance != selection.declared_provenance:
                return ContractResult(
                    accepted=False,
                    known_evidence_ids=True,
                    provenance_compatible=False,
                    reason=RejectionReason.INCOMPATIBLE_PROVENANCE,
                    rejected_evidence_id=identifier,
                )

        return ContractResult(
            accepted=True,
            known_evidence_ids=True,
            provenance_compatible=True,
            reason=None,
            rejected_evidence_id=None,
        )


def run_experiment() -> int:
    """Run and present the synthetic failure-first evidence probe."""

    version_1 = ProvenanceContext("synthetic-source", "version-1")
    version_2 = ProvenanceContext("synthetic-source", "version-2")
    catalog = EvidenceCatalog(
        (
            EvidenceFragment("E17", version_1),
            EvidenceFragment("E18", version_2),
        )
    )
    coherent_selection = EvidenceSelection(version_1, ("E17",))
    incompatible_selection = EvidenceSelection(version_1, ("E17", "E18"))

    coherent_result = catalog.validate(coherent_selection)
    naive_accepts = catalog.identifiers_exist(incompatible_selection)
    contract_result = catalog.validate(incompatible_selection)

    if (
        not coherent_result.accepted
        or not naive_accepts
        or contract_result.accepted
        or contract_result.reason is not RejectionReason.INCOMPATIBLE_PROVENANCE
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    print("VALID CONTROL")
    print("declared provenance: synthetic-source/version-1")
    print("selected evidence: E17")
    print("contract result: ACCEPTED")
    print()
    print("INVALID RELATIONSHIP")
    print("declared provenance: synthetic-source/version-1")
    print("selected evidence: E17 (version-1), E18 (version-2)")
    print()
    print("NAIVE CHECK")
    print("known evidence IDs: PASS")
    print("provenance compatibility: NOT CHECKED")
    print("result: ACCEPTED")
    print()
    print("CONTRACT CHECK")
    print("known evidence IDs: PASS")
    print("provenance compatibility: FAIL (E18 belongs to version-2)")
    print("result: REJECTED (incompatible-provenance)")
    print()
    print("GUARANTEE")
    print(
        "Under the declared identity/version model, an accepted evidence selection "
        "contains only known fragments whose recorded provenance equals the "
        "selection's declared provenance."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish factual correctness, claim support, retrieval "
        "completeness, or evidence authenticity."
    )
    return 0
