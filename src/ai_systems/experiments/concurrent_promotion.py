"""Concurrent shared-state promotion with generation fencing."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier


class PromotionState(StrEnum):
    """Authoritative states used by the bounded M6 experiment."""

    CANDIDATE = "candidate"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class PromotionDecision(StrEnum):
    """Outcome of one attempted authoritative transition."""

    APPLIED = "applied"
    STALE_GENERATION = "stale-generation"
    SOURCE_STATE_MISMATCH = "source-state-mismatch"


@dataclass(frozen=True, slots=True)
class AuthoritySnapshot:
    """Observed authoritative state carried by an actor."""

    state: PromotionState
    generation: int
    last_actor: str | None
    last_transition: str | None


@dataclass(frozen=True, slots=True)
class PromotionResult:
    """Result of one attempted promotion."""

    decision: PromotionDecision
    actor_id: str
    transition_id: str
    target_state: PromotionState
    observed_generation: int
    authoritative: AuthoritySnapshot


@dataclass(frozen=True, slots=True)
class CompetitionResult:
    """Observed outcome of two competing actors."""

    observations: tuple[AuthoritySnapshot, AuthoritySnapshot]
    results: tuple[PromotionResult, PromotionResult]
    final: AuthoritySnapshot


class PromotionStore:
    """Durable single-record authority with explicit generation fencing."""

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=5.0)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS authority (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    state TEXT NOT NULL,
                    generation INTEGER NOT NULL CHECK (generation >= 0),
                    last_actor TEXT,
                    last_transition TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO authority(
                    singleton,
                    state,
                    generation,
                    last_actor,
                    last_transition
                )
                VALUES (1, ?, 0, NULL, NULL)
                """,
                (PromotionState.CANDIDATE.value,),
            )

    def snapshot(self) -> AuthoritySnapshot:
        """Read the current authoritative state."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT state, generation, last_actor, last_transition
                FROM authority
                WHERE singleton = 1
                """
            ).fetchone()

        assert row is not None
        return AuthoritySnapshot(
            state=PromotionState(str(row[0])),
            generation=int(row[1]),
            last_actor=str(row[2]) if row[2] is not None else None,
            last_transition=str(row[3]) if row[3] is not None else None,
        )

    @staticmethod
    def _validate_promotion(
        observed: AuthoritySnapshot,
        target_state: PromotionState,
    ) -> None:
        if observed.state is not PromotionState.CANDIDATE:
            raise ValueError("promotion-source-must-be-candidate")
        if target_state not in {PromotionState.APPROVED, PromotionState.REJECTED}:
            raise ValueError("promotion-target-must-be-terminal")

    def naive_promote(
        self,
        observed: AuthoritySnapshot,
        *,
        actor_id: str,
        transition_id: str,
        target_state: PromotionState,
    ) -> PromotionResult:
        """Apply a stale actor decision without checking current authority."""

        self._validate_promotion(observed, target_state)

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE authority
                SET state = ?,
                    generation = generation + 1,
                    last_actor = ?,
                    last_transition = ?
                WHERE singleton = 1
                """,
                (target_state.value, actor_id, transition_id),
            )

        return PromotionResult(
            decision=PromotionDecision.APPLIED,
            actor_id=actor_id,
            transition_id=transition_id,
            target_state=target_state,
            observed_generation=observed.generation,
            authoritative=self.snapshot(),
        )

    def promote(
        self,
        observed: AuthoritySnapshot,
        *,
        actor_id: str,
        transition_id: str,
        target_state: PromotionState,
    ) -> PromotionResult:
        """Atomically promote only if source state and generation still match."""

        self._validate_promotion(observed, target_state)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE authority
                SET state = ?,
                    generation = generation + 1,
                    last_actor = ?,
                    last_transition = ?
                WHERE singleton = 1
                  AND state = ?
                  AND generation = ?
                """,
                (
                    target_state.value,
                    actor_id,
                    transition_id,
                    observed.state.value,
                    observed.generation,
                ),
            )

            row = connection.execute(
                """
                SELECT state, generation, last_actor, last_transition
                FROM authority
                WHERE singleton = 1
                """
            ).fetchone()
            assert row is not None
            authoritative = AuthoritySnapshot(
                state=PromotionState(str(row[0])),
                generation=int(row[1]),
                last_actor=str(row[2]) if row[2] is not None else None,
                last_transition=str(row[3]) if row[3] is not None else None,
            )

        if cursor.rowcount == 1:
            decision = PromotionDecision.APPLIED
        elif authoritative.generation != observed.generation:
            decision = PromotionDecision.STALE_GENERATION
        else:
            decision = PromotionDecision.SOURCE_STATE_MISMATCH

        return PromotionResult(
            decision=decision,
            actor_id=actor_id,
            transition_id=transition_id,
            target_state=target_state,
            observed_generation=observed.generation,
            authoritative=authoritative,
        )

    def promote_state_only(
        self,
        observed: AuthoritySnapshot,
        *,
        actor_id: str,
        transition_id: str,
        target_state: PromotionState,
    ) -> PromotionResult:
        """Weak control that checks source state but ignores generation."""

        self._validate_promotion(observed, target_state)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE authority
                SET state = ?,
                    generation = generation + 1,
                    last_actor = ?,
                    last_transition = ?
                WHERE singleton = 1
                  AND state = ?
                """,
                (
                    target_state.value,
                    actor_id,
                    transition_id,
                    observed.state.value,
                ),
            )

            row = connection.execute(
                """
                SELECT state, generation, last_actor, last_transition
                FROM authority
                WHERE singleton = 1
                """
            ).fetchone()
            assert row is not None
            authoritative = AuthoritySnapshot(
                state=PromotionState(str(row[0])),
                generation=int(row[1]),
                last_actor=str(row[2]) if row[2] is not None else None,
                last_transition=str(row[3]) if row[3] is not None else None,
            )

        decision = (
            PromotionDecision.APPLIED
            if cursor.rowcount == 1
            else PromotionDecision.SOURCE_STATE_MISMATCH
        )
        return PromotionResult(
            decision=decision,
            actor_id=actor_id,
            transition_id=transition_id,
            target_state=target_state,
            observed_generation=observed.generation,
            authoritative=authoritative,
        )

    def advance_for_characterization(
        self,
        target_state: PromotionState,
        *,
        actor_id: str,
        transition_id: str,
    ) -> AuthoritySnapshot:
        """Advance authority unconditionally to construct the ABA control."""

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE authority
                SET state = ?,
                    generation = generation + 1,
                    last_actor = ?,
                    last_transition = ?
                WHERE singleton = 1
                """,
                (target_state.value, actor_id, transition_id),
            )
        return self.snapshot()


def _compete(
    store: PromotionStore,
    *,
    protected: bool,
) -> CompetitionResult:
    barrier = Barrier(2)

    def actor(
        actor_id: str,
        transition_id: str,
        target_state: PromotionState,
    ) -> tuple[AuthoritySnapshot, PromotionResult]:
        observed = store.snapshot()
        barrier.wait(timeout=5.0)
        if protected:
            result = store.promote(
                observed,
                actor_id=actor_id,
                transition_id=transition_id,
                target_state=target_state,
            )
        else:
            result = store.naive_promote(
                observed,
                actor_id=actor_id,
                transition_id=transition_id,
                target_state=target_state,
            )
        return observed, result

    with ThreadPoolExecutor(max_workers=2) as executor:
        left = executor.submit(
            actor,
            "actor-a",
            "transition-a",
            PromotionState.APPROVED,
        )
        right = executor.submit(
            actor,
            "actor-b",
            "transition-b",
            PromotionState.REJECTED,
        )
        left_observation, left_result = left.result(timeout=10.0)
        right_observation, right_result = right.result(timeout=10.0)

    return CompetitionResult(
        observations=(left_observation, right_observation),
        results=(left_result, right_result),
        final=store.snapshot(),
    )


def compete_naively(path: Path) -> CompetitionResult:
    """Run the stale-write negative control."""

    return _compete(PromotionStore(path), protected=False)


def compete_with_generation_fence(path: Path) -> CompetitionResult:
    """Run two competing promotions against one observed generation."""

    return _compete(PromotionStore(path), protected=True)


def _assert_same_initial_observation(result: CompetitionResult) -> None:
    left, right = result.observations
    assert left.state is PromotionState.CANDIDATE
    assert right.state is PromotionState.CANDIDATE
    assert left.generation == 0
    assert right.generation == 0


def run_experiment() -> int:
    """Run failure-first concurrent-promotion and ABA controls."""

    with TemporaryDirectory() as directory:
        root = Path(directory)

        naive = compete_naively(root / "naive.sqlite")
        protected = compete_with_generation_fence(root / "protected.sqlite")
        reopened = PromotionStore(root / "protected.sqlite").snapshot()

        state_only_store = PromotionStore(root / "state-only-aba.sqlite")
        stale_state_only = state_only_store.snapshot()
        state_only_store.advance_for_characterization(
            PromotionState.REVIEW,
            actor_id="system",
            transition_id="cycle-away",
        )
        state_only_store.advance_for_characterization(
            PromotionState.CANDIDATE,
            actor_id="system",
            transition_id="cycle-back",
        )
        state_only_result = state_only_store.promote_state_only(
            stale_state_only,
            actor_id="stale-actor",
            transition_id="stale-state-only",
            target_state=PromotionState.APPROVED,
        )

        fenced_store = PromotionStore(root / "fenced-aba.sqlite")
        stale_fenced = fenced_store.snapshot()
        fenced_store.advance_for_characterization(
            PromotionState.REVIEW,
            actor_id="system",
            transition_id="cycle-away",
        )
        fenced_store.advance_for_characterization(
            PromotionState.CANDIDATE,
            actor_id="system",
            transition_id="cycle-back",
        )
        fenced_result = fenced_store.promote(
            stale_fenced,
            actor_id="stale-actor",
            transition_id="stale-fenced",
            target_state=PromotionState.APPROVED,
        )

    _assert_same_initial_observation(naive)
    _assert_same_initial_observation(protected)

    naive_decisions = tuple(result.decision for result in naive.results)
    protected_decisions = tuple(result.decision for result in protected.results)

    if (
        naive_decisions.count(PromotionDecision.APPLIED) != 2
        or naive.final.generation != 2
        or protected_decisions.count(PromotionDecision.APPLIED) != 1
        or protected_decisions.count(PromotionDecision.STALE_GENERATION) != 1
        or protected.final.generation != 1
        or reopened != protected.final
        or state_only_result.decision is not PromotionDecision.APPLIED
        or state_only_result.authoritative.generation != 3
        or fenced_result.decision is not PromotionDecision.STALE_GENERATION
        or fenced_result.authoritative.state is not PromotionState.CANDIDATE
        or fenced_result.authoritative.generation != 2
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    winner = next(
        result
        for result in protected.results
        if result.decision is PromotionDecision.APPLIED
    )
    loser = next(
        result
        for result in protected.results
        if result.decision is PromotionDecision.STALE_GENERATION
    )

    print("NAIVE STALE-WRITE CONTROL")
    print("both actors observed: candidate@0")
    print("actor-a target: approved")
    print("actor-b target: rejected")
    print("accepted transitions: 2")
    print(f"final generation: {naive.final.generation}")
    print("result: BOTH STALE DECISIONS WERE ACCEPTED")
    print()
    print("GENERATION-FENCED PROMOTION")
    print("both actors observed: candidate@0")
    print(f"winner: {winner.actor_id} -> {winner.target_state.value}")
    print(f"loser: {loser.actor_id} -> {loser.decision.value}")
    print(f"final generation: {protected.final.generation}")
    print("durability check: reopened state matches accepted state")
    print("result: EXACTLY ONE TRANSITION ACCEPTED")
    print()
    print("ABA / STATE-ONLY CONTROL")
    print("stale actor observed: candidate@0")
    print("authority cycled: candidate@0 -> review@1 -> candidate@2")
    print(f"state-only result: {state_only_result.decision.value}")
    print(f"generation-fenced result: {fenced_result.decision.value}")
    print("result: GENERATION DISTINGUISHED STALE AUTHORITY")
    print()
    print("GUARANTEE")
    print(
        "Given one authoritative record and an atomic compare-and-swap on its "
        "expected source state and monotonically increasing generation, at most "
        "one competing transition can be accepted from one observed generation."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish distributed consensus, fairness, lease semantics, "
        "multi-record transactions, dead-actor recovery, Git conflict prevention, "
        "or durable dispatch."
    )
    return 0
