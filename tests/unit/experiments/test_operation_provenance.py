from dataclasses import replace
from pathlib import Path

import pytest

from ai_systems.experiments.ambiguous_completion import LogicalOperation
from ai_systems.experiments.operation_provenance import (
    EventType,
    ProvenanceEvent,
    ProvenanceJournal,
    ProvenanceValidationError,
    RecoveryDecision,
    RejectionReason,
    direct_success_history,
    final_summary,
    recovered_history,
    validate_history,
)


def _operation() -> LogicalOperation:
    return LogicalOperation(
        operation_id="operation-001",
        effect_name="publish-artifact",
        payload="artifact-v1",
    )


def _renumber(
    events: tuple[ProvenanceEvent, ...],
) -> tuple[ProvenanceEvent, ...]:
    return tuple(
        replace(event, sequence=index) for index, event in enumerate(events, start=1)
    )


def test_final_summary_collapses_materially_different_histories() -> None:
    operation = _operation()
    direct = direct_success_history(operation)
    recovered = recovered_history(operation)

    assert final_summary(direct) == final_summary(recovered)
    assert validate_history(direct).attempt_ids == ("attempt-1",)
    assert validate_history(recovered).attempt_ids == ("attempt-1", "attempt-2")


def test_recovered_history_retains_retry_decision_and_effect_identity() -> None:
    audit = validate_history(recovered_history(_operation()))

    assert audit.recovery_decisions == (RecoveryDecision.RETRY,)
    assert audit.observed_effect_ids == ("effect-001", "effect-001")
    assert audit.mechanisms == ("provider-a", "provider-b")


def test_missing_recovery_decision_is_rejected() -> None:
    events = recovered_history(_operation())
    incomplete = _renumber(
        tuple(
            event
            for event in events
            if event.event_type is not EventType.RECOVERY_DECIDED
        )
    )

    with pytest.raises(ProvenanceValidationError) as error:
        validate_history(incomplete)

    assert error.value.reason is RejectionReason.MISSING_RECOVERY_DECISION


def test_duplicate_recovery_decision_is_rejected() -> None:
    events = list(recovered_history(_operation()))
    recovery = events[4]
    events.insert(5, replace(recovery, sequence=6))
    events = list(_renumber(tuple(events)))

    with pytest.raises(ProvenanceValidationError) as error:
        validate_history(tuple(events))

    assert error.value.reason is RejectionReason.DUPLICATE_RECOVERY_DECISION


def test_unknown_attempt_reference_is_rejected() -> None:
    events = list(recovered_history(_operation()))
    effect = events[2]
    events[2] = replace(effect, attempt_id="missing-attempt")

    with pytest.raises(ProvenanceValidationError) as error:
        validate_history(tuple(events))

    assert error.value.reason is RejectionReason.UNKNOWN_ATTEMPT


def test_mixed_intent_is_rejected() -> None:
    events = list(recovered_history(_operation()))
    events[3] = replace(events[3], intent_fingerprint="different")

    with pytest.raises(ProvenanceValidationError) as error:
        validate_history(tuple(events))

    assert error.value.reason is RejectionReason.MIXED_INTENT


def test_success_cannot_finalize_an_unobserved_effect() -> None:
    events = list(recovered_history(_operation()))
    events[-1] = replace(events[-1], effect_id="effect-never-observed")

    with pytest.raises(ProvenanceValidationError) as error:
        validate_history(tuple(events))

    assert error.value.reason is RejectionReason.UNOBSERVED_FINAL_EFFECT


def test_journal_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "provenance.sqlite"
    expected = recovered_history(_operation())

    journal = ProvenanceJournal(path)
    for event in expected:
        journal.append(event)

    reopened = ProvenanceJournal(path)

    assert reopened.read() == expected
    assert validate_history(reopened.read()) == validate_history(expected)
