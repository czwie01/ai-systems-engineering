import pytest

from ai_systems.cli.main import main
from ai_systems.experiments import EXPERIMENTS


def test_list_exposes_every_planned_experiment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["list"]) == 0

    output = capsys.readouterr().out
    for experiment in EXPERIMENTS:
        assert experiment.identifier in output
    assert output.count("planned") == len(EXPERIMENTS)


def test_explain_registered_experiment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["explain", "evidence-contracts"]) == 0

    output = capsys.readouterr().out
    assert "id: evidence-contracts" in output
    assert "engineering question:" in output
    assert "intended invariant:" in output
    assert "status: planned" in output


def test_explain_unknown_experiment_fails_clearly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        main(["explain", "not-registered"])

    assert error.value.code != 0
    assert "unknown experiment: not-registered" in capsys.readouterr().err
