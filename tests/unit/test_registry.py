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


def test_every_registered_experiment_is_planned() -> None:
    assert {experiment.status for experiment in EXPERIMENTS} == {
        ExperimentStatus.PLANNED
    }
