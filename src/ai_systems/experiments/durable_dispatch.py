"""Durable dispatch through an atomic transactional outbox boundary."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_systems.experiments.ambiguous_completion import (
    EffectDecision,
    IdempotentEffectSink,
    LogicalOperation,
)


class DispatchStatus(StrEnum):
    """Durable dispatch lifecycle represented by the M7 experiment."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"


@dataclass(frozen=True, slots=True)
class DispatchIntent:
    """Immutable downstream work committed with authoritative state."""

    dispatch_id: str
    effect_name: str
    payload: str


@dataclass(frozen=True, slots=True)
class DispatchRecord:
    """Durable outbox record."""

    intent: DispatchIntent
    status: DispatchStatus
    effect_id: str | None


@dataclass(frozen=True, slots=True)
class AuthorityView:
    """Authoritative state whose transition requires downstream dispatch."""

    state: str
    generation: int


@dataclass(frozen=True, slots=True)
class DispatchAttempt:
    """Observed result of one relay attempt."""

    dispatch_id: str
    effect_decision: EffectDecision
    effect_id: str
    acknowledged: bool


class InjectedCrash(RuntimeError):
    """Synthetic process-loss boundary used by the experiment."""

    pass


class DispatchStore:
    """Durable authority plus transactional outbox in one SQLite database."""

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS authority (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    state TEXT NOT NULL,
                    generation INTEGER NOT NULL CHECK (generation >= 0)
                )
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO authority(singleton, state, generation)
                VALUES (1, 'candidate', 0)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    dispatch_id TEXT PRIMARY KEY,
                    effect_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    effect_id TEXT
                )
                """
            )

    def authority(self) -> AuthorityView:
        """Read the current authoritative state."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT state, generation
                FROM authority
                WHERE singleton = 1
                """
            ).fetchone()
        assert row is not None
        return AuthorityView(state=str(row[0]), generation=int(row[1]))

    def commit_authority_only(self) -> None:
        """Naive first half of a dual write."""

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE authority
                SET state = 'dispatch-required',
                    generation = generation + 1
                WHERE singleton = 1
                """
            )

    def insert_dispatch(self, intent: DispatchIntent) -> None:
        """Naive second half of a dual write."""

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO outbox(
                    dispatch_id,
                    effect_name,
                    payload,
                    status,
                    effect_id
                )
                VALUES (?, ?, ?, ?, NULL)
                """,
                (
                    intent.dispatch_id,
                    intent.effect_name,
                    intent.payload,
                    DispatchStatus.PENDING.value,
                ),
            )

    def commit_with_outbox(self, intent: DispatchIntent) -> None:
        """Atomically commit authoritative state plus durable dispatch intent."""

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE authority
                SET state = 'dispatch-required',
                    generation = generation + 1
                WHERE singleton = 1
                """
            )
            connection.execute(
                """
                INSERT INTO outbox(
                    dispatch_id,
                    effect_name,
                    payload,
                    status,
                    effect_id
                )
                VALUES (?, ?, ?, ?, NULL)
                """,
                (
                    intent.dispatch_id,
                    intent.effect_name,
                    intent.payload,
                    DispatchStatus.PENDING.value,
                ),
            )

    def pending(self) -> tuple[DispatchRecord, ...]:
        """Return retained unacknowledged work."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT dispatch_id, effect_name, payload, status, effect_id
                FROM outbox
                WHERE status = ?
                ORDER BY dispatch_id
                """,
                (DispatchStatus.PENDING.value,),
            ).fetchall()

        return tuple(
            DispatchRecord(
                intent=DispatchIntent(
                    dispatch_id=str(row[0]),
                    effect_name=str(row[1]),
                    payload=str(row[2]),
                ),
                status=DispatchStatus(str(row[3])),
                effect_id=str(row[4]) if row[4] is not None else None,
            )
            for row in rows
        )

    def record(self, dispatch_id: str) -> DispatchRecord | None:
        """Read one durable dispatch record."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT dispatch_id, effect_name, payload, status, effect_id
                FROM outbox
                WHERE dispatch_id = ?
                """,
                (dispatch_id,),
            ).fetchone()

        if row is None:
            return None
        return DispatchRecord(
            intent=DispatchIntent(
                dispatch_id=str(row[0]),
                effect_name=str(row[1]),
                payload=str(row[2]),
            ),
            status=DispatchStatus(str(row[3])),
            effect_id=str(row[4]) if row[4] is not None else None,
        )

    def acknowledge(self, dispatch_id: str, effect_id: str) -> None:
        """Acknowledge only after the external effect boundary reports success."""

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE outbox
                SET status = ?,
                    effect_id = ?
                WHERE dispatch_id = ?
                  AND status = ?
                """,
                (
                    DispatchStatus.ACKNOWLEDGED.value,
                    effect_id,
                    dispatch_id,
                    DispatchStatus.PENDING.value,
                ),
            )
        if cursor.rowcount != 1:
            raise ValueError("dispatch-not-pending")


def dispatch_one(
    store: DispatchStore,
    sink: IdempotentEffectSink,
    dispatch_id: str,
    *,
    crash_after_effect: bool = False,
) -> DispatchAttempt:
    """Relay one pending intent through the M4 idempotent effect boundary."""

    record = store.record(dispatch_id)
    if record is None or record.status is not DispatchStatus.PENDING:
        raise ValueError("dispatch-not-pending")

    effect = sink.apply(
        LogicalOperation(
            operation_id=record.intent.dispatch_id,
            effect_name=record.intent.effect_name,
            payload=record.intent.payload,
        )
    )

    if crash_after_effect:
        raise InjectedCrash("after-effect-before-dispatch-ack")

    store.acknowledge(dispatch_id, effect.effect_id)
    return DispatchAttempt(
        dispatch_id=dispatch_id,
        effect_decision=effect.decision,
        effect_id=effect.effect_id,
        acknowledged=True,
    )


def run_experiment() -> int:
    """Run naive loss, durable outbox, and effect-before-ack replay probes."""

    intent = DispatchIntent(
        dispatch_id="dispatch-001",
        effect_name="publish-artifact",
        payload="artifact-v1",
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)

        naive_path = root / "naive.sqlite"
        naive = DispatchStore(naive_path)
        naive.commit_authority_only()
        try:
            raise InjectedCrash("after-authority-before-dispatch-intent")
        except InjectedCrash:
            pass
        naive_reopened = DispatchStore(naive_path)
        naive_authority = naive_reopened.authority()
        naive_pending = naive_reopened.pending()

        protected_path = root / "protected.sqlite"
        protected = DispatchStore(protected_path)
        protected.commit_with_outbox(intent)
        try:
            raise InjectedCrash("after-atomic-commit-before-dispatch")
        except InjectedCrash:
            pass

        protected_reopened = DispatchStore(protected_path)
        protected_authority = protected_reopened.authority()
        protected_pending = protected_reopened.pending()
        protected_sink = IdempotentEffectSink(root / "protected-effects.sqlite")
        protected_attempt = dispatch_one(
            protected_reopened,
            protected_sink,
            intent.dispatch_id,
        )
        protected_record = protected_reopened.record(intent.dispatch_id)
        protected_effects = protected_sink.visible_effect_count()

        replay_intent = DispatchIntent(
            dispatch_id="dispatch-002",
            effect_name="publish-artifact",
            payload="artifact-v2",
        )
        replay_path = root / "replay.sqlite"
        replay_store = DispatchStore(replay_path)
        replay_store.commit_with_outbox(replay_intent)
        replay_sink_path = root / "replay-effects.sqlite"
        replay_sink = IdempotentEffectSink(replay_sink_path)

        crashed = False
        try:
            dispatch_one(
                replay_store,
                replay_sink,
                replay_intent.dispatch_id,
                crash_after_effect=True,
            )
        except InjectedCrash:
            crashed = True

        pending_after_effect_crash = DispatchStore(replay_path).pending()
        effects_after_crash = IdempotentEffectSink(
            replay_sink_path
        ).visible_effect_count()

        replay_reopened = DispatchStore(replay_path)
        sink_reopened = IdempotentEffectSink(replay_sink_path)
        replay_attempt = dispatch_one(
            replay_reopened,
            sink_reopened,
            replay_intent.dispatch_id,
        )
        replay_record = replay_reopened.record(replay_intent.dispatch_id)
        replay_effects = sink_reopened.visible_effect_count()

    if (
        naive_authority.state != "dispatch-required"
        or naive_authority.generation != 1
        or naive_pending != ()
        or protected_authority.state != "dispatch-required"
        or protected_authority.generation != 1
        or len(protected_pending) != 1
        or protected_pending[0].intent != intent
        or protected_attempt.effect_decision is not EffectDecision.APPLIED
        or protected_record is None
        or protected_record.status is not DispatchStatus.ACKNOWLEDGED
        or protected_effects != 1
        or not crashed
        or len(pending_after_effect_crash) != 1
        or pending_after_effect_crash[0].intent != replay_intent
        or effects_after_crash != 1
        or replay_attempt.effect_decision is not EffectDecision.REPLAYED
        or replay_record is None
        or replay_record.status is not DispatchStatus.ACKNOWLEDGED
        or replay_record.effect_id != replay_attempt.effect_id
        or replay_effects != 1
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    print("NAIVE DUAL-WRITE CONTROL")
    print("authoritative state committed: dispatch-required@1")
    print("process failed before durable dispatch intent was recorded")
    print(f"pending intents after reopen: {len(naive_pending)}")
    print("result: COMMITTED WORK REQUIREMENT LOST ITS DISPATCH")
    print()
    print("TRANSACTIONAL OUTBOX")
    print("authoritative state + dispatch intent committed atomically")
    print("process failed before dispatcher ran")
    print(f"pending intents after reopen: {len(protected_pending)}")
    print(f"dispatch result: {protected_attempt.effect_decision.value}")
    print(f"visible effects: {protected_effects}")
    print("result: COMMITTED DISPATCH INTENT SURVIVED RESTART")
    print()
    print("EFFECT-BEFORE-ACK REPLAY")
    print("first relay produced the external effect")
    print("process failed before outbox acknowledgement")
    print(f"pending intents after crash: {len(pending_after_effect_crash)}")
    print(f"visible effects after crash: {effects_after_crash}")
    print(f"retry effect decision: {replay_attempt.effect_decision.value}")
    print(f"visible effects after retry: {replay_effects}")
    print(f"final outbox status: {replay_record.status.value}")
    print("result: RETAINED INTENT REPLAYED AND ACKNOWLEDGED")
    print()
    print("GUARANTEE")
    print(
        "Given atomic commit of authoritative state plus durable dispatch intent, "
        "retention of unacknowledged intents, and eventual rescanning by a "
        "dispatcher, committed dispatch intent remains discoverable across process "
        "failure until acknowledgement."
    )
    print()
    print("COMPOSITION")
    print(
        "When dispatch itself completes ambiguously, M4-compatible stable operation "
        "identity and an idempotent effect boundary allow the retained intent to be "
        "replayed without adding another application-visible effect under M4's "
        "stated retention assumptions."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish exactly-once delivery or execution, progress if no "
        "dispatcher ever runs again, distributed consensus, cross-database atomicity, "
        "global ordering, poison-message handling, or a preferred workflow runtime."
    )
    return 0
