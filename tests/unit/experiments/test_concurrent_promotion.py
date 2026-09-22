from pathlib import Path

from ai_systems.experiments.concurrent_promotion import (
    PromotionDecision,
    PromotionState,
    PromotionStore,
    compete_naively,
    compete_with_generation_fence,
)


def test_naive_concurrent_stale_writes_are_both_accepted(tmp_path: Path) -> None:
    result = compete_naively(tmp_path / "naive.sqlite")

    assert all(snapshot.generation == 0 for snapshot in result.observations)
    assert all(
        snapshot.state is PromotionState.CANDIDATE
        for snapshot in result.observations
    )
    assert [item.decision for item in result.results].count(
        PromotionDecision.APPLIED
    ) == 2
    assert result.final.generation == 2


def test_generation_fence_accepts_exactly_one_competing_transition(
    tmp_path: Path,
) -> None:
    path = tmp_path / "protected.sqlite"
    result = compete_with_generation_fence(path)

    decisions = [item.decision for item in result.results]
    assert decisions.count(PromotionDecision.APPLIED) == 1
    assert decisions.count(PromotionDecision.STALE_GENERATION) == 1
    assert result.final.generation == 1
    assert result.final.state in {
        PromotionState.APPROVED,
        PromotionState.REJECTED,
    }
    assert PromotionStore(path).snapshot() == result.final


def test_state_only_guard_accepts_stale_actor_after_aba_cycle(tmp_path: Path) -> None:
    store = PromotionStore(tmp_path / "state-only.sqlite")
    stale = store.snapshot()

    store.advance_for_characterization(
        PromotionState.REVIEW,
        actor_id="system",
        transition_id="away",
    )
    store.advance_for_characterization(
        PromotionState.CANDIDATE,
        actor_id="system",
        transition_id="back",
    )

    result = store.promote_state_only(
        stale,
        actor_id="stale-actor",
        transition_id="stale",
        target_state=PromotionState.APPROVED,
    )

    assert result.decision is PromotionDecision.APPLIED
    assert result.authoritative.generation == 3


def test_generation_fence_rejects_stale_actor_after_aba_cycle(
    tmp_path: Path,
) -> None:
    store = PromotionStore(tmp_path / "protected-aba.sqlite")
    stale = store.snapshot()

    store.advance_for_characterization(
        PromotionState.REVIEW,
        actor_id="system",
        transition_id="away",
    )
    store.advance_for_characterization(
        PromotionState.CANDIDATE,
        actor_id="system",
        transition_id="back",
    )

    result = store.promote(
        stale,
        actor_id="stale-actor",
        transition_id="stale",
        target_state=PromotionState.APPROVED,
    )

    assert result.decision is PromotionDecision.STALE_GENERATION
    assert result.authoritative.state is PromotionState.CANDIDATE
    assert result.authoritative.generation == 2
