"""Canonical metadata for public experiments."""

from dataclasses import dataclass
from enum import StrEnum


class ExperimentStatus(StrEnum):
    """Lifecycle states exposed by the public experiment registry."""

    PLANNED = "planned"


@dataclass(frozen=True, slots=True)
class Experiment:
    """Discoverable metadata for an engineering experiment."""

    identifier: str
    name: str
    milestone: str
    area: str
    status: ExperimentStatus
    engineering_question: str
    intended_invariant: str


EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment(
        identifier="evidence-contracts",
        name="Evidence Contracts",
        milestone="M1",
        area="evidence",
        status=ExperimentStatus.PLANNED,
        engineering_question="How can evidence remain attributable and verifiable?",
        intended_invariant="Accepted evidence preserves its declared provenance.",
    ),
    Experiment(
        identifier="evaluation-oracle-integrity",
        name="Evaluation Oracle Integrity",
        milestone="M2",
        area="evaluation",
        status=ExperimentStatus.PLANNED,
        engineering_question=(
            "How can an evaluation oracle avoid judging its own output?"
        ),
        intended_invariant=(
            "Evaluation evidence is independent of the subject under evaluation."
        ),
    ),
    Experiment(
        identifier="failure-semantics",
        name="Provider-Neutral Failure Semantics",
        milestone="M3",
        area="execution",
        status=ExperimentStatus.PLANNED,
        engineering_question=(
            "How can provider failures map to stable application semantics?"
        ),
        intended_invariant=(
            "Equivalent failures have provider-independent classifications."
        ),
    ),
    Experiment(
        identifier="ambiguous-completion",
        name="Ambiguous Completion and Idempotency",
        milestone="M4",
        area="reliability",
        status=ExperimentStatus.PLANNED,
        engineering_question="How can a caller recover when completion is uncertain?",
        intended_invariant="Retries do not duplicate a logically completed operation.",
    ),
    Experiment(
        identifier="operation-provenance",
        name="Operation Provenance",
        milestone="M5",
        area="observability",
        status=ExperimentStatus.PLANNED,
        engineering_question=(
            "How can an operation retain an auditable execution history?"
        ),
        intended_invariant=(
            "Each operation records the decisions and effects needed for audit."
        ),
    ),
    Experiment(
        identifier="concurrent-promotion",
        name="Concurrent Agent State Transitions",
        milestone="M6",
        area="coordination",
        status=ExperimentStatus.PLANNED,
        engineering_question="How can concurrent actors safely promote shared state?",
        intended_invariant="At most one valid transition wins from a given state.",
    ),
    Experiment(
        identifier="durable-dispatch",
        name="Durable Dispatch",
        milestone="M7",
        area="reliability",
        status=ExperimentStatus.PLANNED,
        engineering_question=(
            "How can committed intent reliably produce an external effect?"
        ),
        intended_invariant="Committed dispatch intent is not silently lost.",
    ),
)

_EXPERIMENTS_BY_ID = {experiment.identifier: experiment for experiment in EXPERIMENTS}

if len(_EXPERIMENTS_BY_ID) != len(EXPERIMENTS):
    raise RuntimeError("experiment identifiers must be unique")


def get_experiment(identifier: str) -> Experiment | None:
    """Return registered experiment metadata, if present."""

    return _EXPERIMENTS_BY_ID.get(identifier)
