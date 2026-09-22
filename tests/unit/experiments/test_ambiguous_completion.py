import pytest

from ai_systems.experiments.ambiguous_completion import (
    IdempotentEffectBoundary,
    OperationRequest,
    RetryDisposition,
)


def request(
    operation_id: str = "op-1",
    intent: tuple[str, ...] = ("create-resource", "resource-a"),
) -> OperationRequest:
    return OperationRequest(operation_id=operation_id, intent=intent)


def test_retry_replays_prior_result_without_second_effect() -> None:
    boundary = IdempotentEffectBoundary()

    first_disposition, first_result = boundary.execute(request())
    retry_disposition, retry_result = boundary.execute(request())

    assert first_disposition is RetryDisposition.APPLIED
    assert retry_disposition is RetryDisposition.REPLAYED
    assert first_result == retry_result
    assert len(boundary.visible_effects) == 1


def test_same_operation_id_with_different_intent_is_rejected() -> None:
    boundary = IdempotentEffectBoundary()
    boundary.execute(request())

    with pytest.raises(ValueError, match="idempotency-conflict"):
        boundary.execute(request(intent=("create-resource", "resource-b")))

    assert len(boundary.visible_effects) == 1


def test_expired_idempotency_record_removes_at_most_one_guarantee() -> None:
    boundary = IdempotentEffectBoundary()
    original = request()

    boundary.execute(original)
    boundary.expire(original.operation_id)
    disposition, second_result = boundary.execute(original)

    assert disposition is RetryDisposition.APPLIED
    assert second_result.effect_id == "effect-2"
    assert len(boundary.visible_effects) == 2
