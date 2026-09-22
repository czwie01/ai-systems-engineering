from pathlib import Path

import pytest

from ai_systems.experiments.ambiguous_completion import (
    EffectDecision,
    IdempotencyConflict,
    IdempotentEffectSink,
    LogicalOperation,
    NaiveEffectSink,
    RejectionReason,
    operation_fingerprint,
)


def _operation(
    *,
    operation_id: str = "operation-001",
    payload: str = "artifact-v1",
) -> LogicalOperation:
    return LogicalOperation(
        operation_id=operation_id,
        effect_name="publish-artifact",
        payload=payload,
    )


def test_naive_retry_duplicates_visible_effect(tmp_path: Path) -> None:
    sink = NaiveEffectSink(tmp_path / "naive.sqlite")
    operation = _operation()

    sink.apply(operation)
    sink.apply(operation)

    assert sink.visible_effect_count() == 2


def test_stable_idempotency_key_survives_sink_reopen(tmp_path: Path) -> None:
    path = tmp_path / "protected.sqlite"
    operation = _operation()

    first = IdempotentEffectSink(path).apply(operation)
    replay = IdempotentEffectSink(path).apply(operation)

    assert first.decision is EffectDecision.APPLIED
    assert replay.decision is EffectDecision.REPLAYED
    assert replay.effect_id == first.effect_id
    assert IdempotentEffectSink(path).visible_effect_count() == 1


def test_same_id_with_different_content_is_rejected(tmp_path: Path) -> None:
    sink = IdempotentEffectSink(tmp_path / "protected.sqlite")
    sink.apply(_operation(payload="artifact-v1"))

    with pytest.raises(IdempotencyConflict) as error:
        sink.apply(_operation(payload="artifact-v2"))

    assert error.value.reason is RejectionReason.IDEMPOTENCY_CONFLICT
    assert sink.visible_effect_count() == 1


def test_new_id_is_a_new_logical_effect_even_for_same_content(tmp_path: Path) -> None:
    sink = IdempotentEffectSink(tmp_path / "protected.sqlite")

    first = sink.apply(_operation(operation_id="operation-001"))
    second = sink.apply(_operation(operation_id="operation-002"))

    assert first.decision is EffectDecision.APPLIED
    assert second.decision is EffectDecision.APPLIED
    assert sink.visible_effect_count() == 2


def test_operation_fingerprint_is_unambiguous_for_embedded_separators() -> None:
    left = LogicalOperation(
        operation_id="left",
        effect_name="a\0b",
        payload="c",
    )
    right = LogicalOperation(
        operation_id="right",
        effect_name="a",
        payload="b\0c",
    )

    assert operation_fingerprint(left) != operation_fingerprint(right)


def test_expired_idempotency_record_ends_at_most_one_guarantee(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retention.sqlite"
    operation = _operation()
    sink = IdempotentEffectSink(path)

    first = sink.apply(operation)
    sink.expire(operation.operation_id)
    retry = sink.apply(operation)

    assert first.decision is EffectDecision.APPLIED
    assert retry.decision is EffectDecision.APPLIED
    assert retry.effect_id != first.effect_id
    assert sink.visible_effect_count() == 2
