from pathlib import Path

import pytest

from ai_systems.experiments.ambiguous_completion import (
    EffectDecision,
    IdempotentEffectSink,
)
from ai_systems.experiments.durable_dispatch import (
    DispatchIntent,
    DispatchStatus,
    DispatchStore,
    InjectedCrash,
    dispatch_one,
)


def _intent(dispatch_id: str = "dispatch-001") -> DispatchIntent:
    return DispatchIntent(
        dispatch_id=dispatch_id,
        effect_name="publish-artifact",
        payload="artifact-v1",
    )


def test_naive_dual_write_can_commit_state_without_dispatch(
    tmp_path: Path,
) -> None:
    path = tmp_path / "naive.sqlite"
    store = DispatchStore(path)

    store.commit_authority_only()

    reopened = DispatchStore(path)
    assert reopened.authority().state == "dispatch-required"
    assert reopened.authority().generation == 1
    assert reopened.pending() == ()


def test_transactional_outbox_survives_store_reopen(tmp_path: Path) -> None:
    path = tmp_path / "protected.sqlite"
    intent = _intent()
    DispatchStore(path).commit_with_outbox(intent)

    reopened = DispatchStore(path)

    assert reopened.authority().state == "dispatch-required"
    assert reopened.authority().generation == 1
    assert len(reopened.pending()) == 1
    assert reopened.pending()[0].intent == intent


def test_successful_dispatch_is_acknowledged(tmp_path: Path) -> None:
    store_path = tmp_path / "dispatch.sqlite"
    sink_path = tmp_path / "effects.sqlite"
    intent = _intent()
    store = DispatchStore(store_path)
    store.commit_with_outbox(intent)
    sink = IdempotentEffectSink(sink_path)

    attempt = dispatch_one(store, sink, intent.dispatch_id)
    record = store.record(intent.dispatch_id)

    assert attempt.effect_decision is EffectDecision.APPLIED
    assert record is not None
    assert record.status is DispatchStatus.ACKNOWLEDGED
    assert record.effect_id == attempt.effect_id
    assert sink.visible_effect_count() == 1


def test_effect_before_ack_stays_pending_and_replays_safely(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / "dispatch.sqlite"
    sink_path = tmp_path / "effects.sqlite"
    intent = _intent()
    store = DispatchStore(store_path)
    store.commit_with_outbox(intent)
    sink = IdempotentEffectSink(sink_path)

    with pytest.raises(InjectedCrash):
        dispatch_one(
            store,
            sink,
            intent.dispatch_id,
            crash_after_effect=True,
        )

    reopened_store = DispatchStore(store_path)
    reopened_sink = IdempotentEffectSink(sink_path)
    pending = reopened_store.pending()

    assert len(pending) == 1
    assert pending[0].intent == intent
    assert reopened_sink.visible_effect_count() == 1

    retry = dispatch_one(reopened_store, reopened_sink, intent.dispatch_id)
    record = reopened_store.record(intent.dispatch_id)

    assert retry.effect_decision is EffectDecision.REPLAYED
    assert record is not None
    assert record.status is DispatchStatus.ACKNOWLEDGED
    assert record.effect_id == retry.effect_id
    assert reopened_sink.visible_effect_count() == 1
