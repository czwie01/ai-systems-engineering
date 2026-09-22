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
    assert output.count("planned") == 0
    assert output.count("available") == len(EXPERIMENTS)


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
    assert "verdict: REJECTED (unsupported-requirement: supports-python-3.14)" in output
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_failure_semantics_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "failure-semantics"]) == 0

    output = capsys.readouterr().out
    assert "RAW FAILURE CONTROL" in output
    assert "APPLICATION CLASSIFICATION" in output
    assert "ambiguous-completion" in output
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_ambiguous_completion_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "ambiguous-completion"]) == 0

    output = capsys.readouterr().out
    assert "AMBIGUOUS COMPLETION CONTROL" in output
    assert "result: DUPLICATED" in output
    assert "PROTECTED RETRY" in output
    assert "visible effects: 1" in output
    assert "idempotency-conflict" in output
    assert "RETENTION BOUNDARY" in output
    assert "AT-MOST-ONE GUARANTEE NO LONGER AVAILABLE" in output
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_operation_provenance_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "operation-provenance"]) == 0

    output = capsys.readouterr().out
    assert "FINAL-STATE-ONLY CONTROL" in output
    assert "HISTORIES COLLAPSED TO THE SAME FINAL SUMMARY" in output
    assert "PROVENANCE AUDIT" in output
    assert "RECOVERY PATH RETAINED" in output
    assert "missing-recovery-decision" in output
    assert "DURABILITY CHECK" in output
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_concurrent_promotion_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "concurrent-promotion"]) == 0

    output = capsys.readouterr().out
    assert "NAIVE STALE-WRITE CONTROL" in output
    assert "BOTH STALE DECISIONS WERE ACCEPTED" in output
    assert "GENERATION-FENCED PROMOTION" in output
    assert "EXACTLY ONE TRANSITION ACCEPTED" in output
    assert "stale-generation" in output
    assert "ABA / STATE-ONLY CONTROL" in output
    assert "GENERATION DISTINGUISHED STALE AUTHORITY" in output
    assert "GUARANTEE" in output
    assert "NON-GUARANTEE" in output


def test_run_durable_dispatch_succeeds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "durable-dispatch"]) == 0

    output = capsys.readouterr().out
    assert "NAIVE DUAL-WRITE CONTROL" in output
    assert "COMMITTED WORK REQUIREMENT LOST ITS DISPATCH" in output
    assert "TRANSACTIONAL OUTBOX" in output
    assert "COMMITTED DISPATCH INTENT SURVIVED RESTART" in output
    assert "EFFECT-BEFORE-ACK REPLAY" in output
    assert "RETAINED INTENT REPLAYED AND ACKNOWLEDGED" in output
    assert "GUARANTEE" in output
    assert "COMPOSITION" in output
    assert "NON-GUARANTEE" in output
