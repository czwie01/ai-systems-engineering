"""Canonical metadata for public experiments."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from ai_systems.experiments.ambiguous_completion import (
    run_experiment as run_ambiguous_completion,
)
from ai_systems.experiments.concurrent_promotion import (
    run_experiment as run_concurrent_promotion,
)
from ai_systems.experiments.evaluation_oracle_integrity import (
    run_experiment as run_evaluation_oracle_integrity,
)
from ai_systems.experiments.evidence_contracts import (
    run_experiment as run_evidence_contracts,
)
from ai_systems.experiments.failure_semantics import (
    run_experiment as run_failure_semantics,
)
from ai_systems.experiments.operation_provenance import (
    run_experiment as run_operation_provenance,
)


class ExperimentStatus(StrEnum):
    """Lifecycle states exposed by the public experiment registry."""

    PLANNED = "planned"
    AVAILABLE = "available"


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
    runner: Callable[[], int] | None = None


EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment(
        identifier="evidence-contracts",
        name="Evidence Contracts",
        milestone="M1",
        area="evidence",
        status=ExperimentStatus.AVAILABLE,
        engineering_question=(
            "How can downstream software reject evidence relationships that conflict "
            "with recorded identity and provenance?"
        ),
        intended_invariant=(
            "Under the declared identity/version model, an accepted evidence "
            "selection contains only known fragments whose recorded provenance "
            "equals the selection's declared provenance."
        ),
        runner=run_evidence_contracts,
    ),
    Experiment(
        identifier="evaluation-oracle-integrity",
        name="Evaluation Oracle Integrity",
        milestone="M2",
        area="evaluation",
        status=ExperimentStatus.AVAILABLE,
        engineering_question=(
            "How can an evaluator reject unsupported claims instead of passing on "
            "citation validity alone?"
        ),
        intended_invariant=(
            "Under the explicit atomic support model, a passing verdict requires "
            "every represented claim requirement to be included in the evaluator's "
            "checked evidence support."
        ),
        runner=run_evaluation_oracle_integrity,
    ),
    Experiment(
        identifier="failure-semantics",
        name="Provider-Neutral Failure Semantics",
        milestone="M3",
        area="execution",
        status=ExperimentStatus.AVAILABLE,
        engineering_question=(
            "How can provider failures map to stable application semantics?"
        ),
        intended_invariant=(
            "Equivalent failures have provider-independent classifications."
        ),
        runner=run_failure_semantics,
    ),
    Experiment(
        identifier="ambiguous-completion",
        name="Ambiguous Completion and Idempotency",
        milestone="M4",
        area="reliability",
        status=ExperimentStatus.AVAILABLE,
        engineering_question="How can a caller recover when completion is uncertain?",
        intended_invariant=(
            "While authoritative idempotency state remains retained, retries of one "
            "logical operation produce at most one application-visible effect under "
            "the experiment's stated assumptions."
        ),
        runner=run_ambiguous_completion,
    ),
    Experiment(
        identifier="operation-provenance",
        name="Operation Provenance",
        milestone="M5",
        area="observability",
        status=ExperimentStatus.AVAILABLE,
        engineering_question=(
            "How can an operation retain an auditable execution history?"
        ),
        intended_invariant=(
            "Each operation records the decisions and effects needed for audit."
        ),
        runner=run_operation_provenance,
    ),
    Experiment(
        identifier="concurrent-promotion",
        name="Concurrent Agent State Transitions",
        milestone="M6",
        area="coordination",
        status=ExperimentStatus.AVAILABLE,
        engineering_question="How can concurrent actors safely promote shared state?",
        intended_invariant=(
            "Given one authoritative record and atomic compare-and-swap on its "
            "observed source state and generation, at most one competing transition "
            "is accepted from one observed generation."
        ),
        runner=run_concurrent_promotion,
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

for _experiment in EXPERIMENTS:
    if (_experiment.status is ExperimentStatus.AVAILABLE) != (
        _experiment.runner is not None
    ):
        raise RuntimeError(
            f"experiment status and runner disagree: {_experiment.identifier}"
        )


def get_experiment(identifier: str) -> Experiment | None:
    """Return registered experiment metadata, if present."""

    return _EXPERIMENTS_BY_ID.get(identifier)
