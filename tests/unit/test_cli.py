import pytest

from ai_systems.cli.main import main
from ai_systems.experiments import EXPERIMENTS


def test_list_exposes_every_registered_experiment_truthfully(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["list"]) == 0

    output = capsys.readouterr().out
    for experiment in EXPERIMENTS:
        assert experiment.identifier in output
    assert output.count("planned") == len(EXPERIMENTS) - 2
    assert output.count("available") == 2


def test_explain_registered_experiment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["explain", "evidence-contracts"]) == 0

    output = capsys.readouterr().out
    assert "id: evidence-contracts" in output
    assert "engineering question:" in output
    assert "intended invariant:" in output
    assert "status: available" in output


def test_explain_unknown_experiment_fails_clearly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        main(["explain", "not-registered"])

    assert error.value.code != 0
    assert "unknown experiment: not-registered" in capsys.readouterr().err


def test_run_evidence_contracts_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "evidence-contracts"]) == 0

    output = capsys.readouterr().out
    assert "NAIVE CHECK" in output
    assert "provenance compatibility: NOT CHECKED" in output
    assert "CONTRACT CHECK" in output
    assert "result: REJECTED (incompatible-provenance)" in output
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_evaluation_oracle_integrity_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "evaluation-oracle-integrity"]) == 0

    output = capsys.readouterr().out
    assert "NAIVE EVALUATOR" in output
    assert "claim support requirements: NOT CHECKED" in output
    assert "INTEGRITY EVALUATOR" in output
    assert (
        "verdict: REJECTED "
        "(unsupported-requirement: supports-python-3.14)" in output
    )
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_planned_experiment_fails_clearly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        main(["run", "durable-dispatch"])

    assert error.value.code != 0
    assert (
        "experiment is not available to run: durable-dispatch (status: planned)"
        in capsys.readouterr().err
    )
