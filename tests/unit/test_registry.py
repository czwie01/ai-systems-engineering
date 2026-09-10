from ai_systems.experiments import EXPERIMENTS, ExperimentStatus

EXPECTED_IDS = (
    "evidence-contracts",
    "evaluation-oracle-integrity",
    "failure-semantics",
    "ambiguous-completion",
    "operation-provenance",
    "concurrent-promotion",
    "durable-dispatch",
)


def test_registry_contains_exactly_the_planned_experiments() -> None:
    assert tuple(experiment.identifier for experiment in EXPERIMENTS) == EXPECTED_IDS


def test_experiment_identifiers_are_unique() -> None:
    identifiers = [experiment.identifier for experiment in EXPERIMENTS]
    assert len(identifiers) == len(set(identifiers))


def test_only_evidence_contracts_is_available() -> None:
    statuses = {
        experiment.identifier: experiment.status for experiment in EXPERIMENTS
    }

    assert statuses["evidence-contracts"] is ExperimentStatus.AVAILABLE
    assert all(
        status is ExperimentStatus.PLANNED
        for identifier, status in statuses.items()
        if identifier != "evidence-contracts"
    )


def test_available_status_matches_executable_runner() -> None:
    for experiment in EXPERIMENTS:
        assert (experiment.status is ExperimentStatus.AVAILABLE) is (
            experiment.runner is not None
        )
