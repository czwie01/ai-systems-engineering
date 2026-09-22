"""Ambiguous-completion recovery through stable logical operation identity."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory


class EffectDecision(StrEnum):
    """Result of submitting one logical operation to the protected sink."""

    APPLIED = "applied"
    REPLAYED = "replayed"


class RejectionReason(StrEnum):
    """Deterministic M4 rejection categories."""

    IDEMPOTENCY_CONFLICT = "idempotency-conflict"


@dataclass(frozen=True, slots=True)
class LogicalOperation:
    """Stable identity plus immutable content for one logical external effect."""

    operation_id: str
    effect_name: str
    payload: str


@dataclass(frozen=True, slots=True)
class EffectResult:
    """Outcome of one protected effect submission."""

    decision: EffectDecision
    operation_id: str
    effect_id: str


class IdempotencyConflict(ValueError):
    """Raised when one logical operation id is reused for different content."""

    def __init__(self, operation_id: str) -> None:
        self.operation_id = operation_id
        self.reason = RejectionReason.IDEMPOTENCY_CONFLICT
        super().__init__(
            f"{self.reason.value}: operation id {operation_id!r} "
            "is already bound to different content"
        )


def operation_fingerprint(operation: LogicalOperation) -> str:
    """Return a stable fingerprint for the immutable operation content."""

    material = json.dumps(
        [operation.effect_name, operation.payload],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(material).hexdigest()


class NaiveEffectSink:
    """Synthetic sink that applies every attempt as a new visible effect."""

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS effects (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                )
                """
            )

    def apply(self, operation: LogicalOperation) -> None:
        """Apply every attempt without deduplication."""

        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                INSERT INTO effects(operation_id, fingerprint)
                VALUES (?, ?)
                """,
                (operation.operation_id, operation_fingerprint(operation)),
            )

    def visible_effect_count(self) -> int:
        """Return the number of visible effects in the synthetic sink."""

        with sqlite3.connect(self._path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM effects").fetchone()
        assert row is not None
        return int(row[0])


class IdempotentEffectSink:
    """Synthetic durable sink with retained idempotency knowledge."""

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS effects (
                    effect_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_records (
                    operation_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    effect_sequence INTEGER NOT NULL
                )
                """
            )

    def apply(self, operation: LogicalOperation) -> EffectResult:
        """Apply once, replay a retained result, or reject conflicting id reuse."""

        fingerprint = operation_fingerprint(operation)

        with sqlite3.connect(self._path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT fingerprint, effect_sequence
                FROM idempotency_records
                WHERE operation_id = ?
                """,
                (operation.operation_id,),
            ).fetchone()

            if row is None:
                cursor = connection.execute(
                    """
                    INSERT INTO effects(operation_id, fingerprint)
                    VALUES (?, ?)
                    """,
                    (operation.operation_id, fingerprint),
                )
                effect_sequence = cursor.lastrowid
                assert effect_sequence is not None
                connection.execute(
                    """
                    INSERT INTO idempotency_records(
                        operation_id,
                        fingerprint,
                        effect_sequence
                    )
                    VALUES (?, ?, ?)
                    """,
                    (operation.operation_id, fingerprint, effect_sequence),
                )
                return EffectResult(
                    decision=EffectDecision.APPLIED,
                    operation_id=operation.operation_id,
                    effect_id=f"effect-{effect_sequence}",
                )

            recorded_fingerprint = str(row[0])
            if recorded_fingerprint != fingerprint:
                raise IdempotencyConflict(operation.operation_id)

            effect_sequence = int(row[1])
            return EffectResult(
                decision=EffectDecision.REPLAYED,
                operation_id=operation.operation_id,
                effect_id=f"effect-{effect_sequence}",
            )

    def expire(self, operation_id: str) -> None:
        """Remove idempotency knowledge without removing the visible effect."""

        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                DELETE FROM idempotency_records
                WHERE operation_id = ?
                """,
                (operation_id,),
            )

    def visible_effect_count(self) -> int:
        """Return the number of application-visible effects admitted by the sink."""

        with sqlite3.connect(self._path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM effects").fetchone()
        assert row is not None
        return int(row[0])


def run_experiment() -> int:
    """Run the failure-first ambiguous-completion idempotency probe."""

    operation = LogicalOperation(
        operation_id="operation-001",
        effect_name="publish-artifact",
        payload="artifact-v1",
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)

        naive = NaiveEffectSink(root / "naive.sqlite")
        naive.apply(operation)
        naive.apply(operation)
        naive_count = naive.visible_effect_count()

        protected = IdempotentEffectSink(root / "protected.sqlite")
        first = protected.apply(operation)

        # Re-open the durable sink before the retry to model lost controller state.
        protected = IdempotentEffectSink(root / "protected.sqlite")
        replay = protected.apply(operation)
        protected_count = protected.visible_effect_count()

        conflicting_operation = LogicalOperation(
            operation_id=operation.operation_id,
            effect_name=operation.effect_name,
            payload="artifact-v2",
        )
        conflict_reason: RejectionReason | None = None
        try:
            protected.apply(conflicting_operation)
        except IdempotencyConflict as error:
            conflict_reason = error.reason

        new_identity = LogicalOperation(
            operation_id="operation-002",
            effect_name=operation.effect_name,
            payload=operation.payload,
        )
        new_identity_result = protected.apply(new_identity)
        count_after_new_identity = protected.visible_effect_count()

        retention = IdempotentEffectSink(root / "retention.sqlite")
        retained_first = retention.apply(operation)
        retention.expire(operation.operation_id)
        after_expiry = retention.apply(operation)
        retention_count = retention.visible_effect_count()

    if (
        naive_count != 2
        or first.decision is not EffectDecision.APPLIED
        or replay.decision is not EffectDecision.REPLAYED
        or replay.effect_id != first.effect_id
        or protected_count != 1
        or conflict_reason is not RejectionReason.IDEMPOTENCY_CONFLICT
        or new_identity_result.decision is not EffectDecision.APPLIED
        or count_after_new_identity != 2
        or retained_first.decision is not EffectDecision.APPLIED
        or after_expiry.decision is not EffectDecision.APPLIED
        or retained_first.effect_id == after_expiry.effect_id
        or retention_count != 2
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    print("AMBIGUOUS COMPLETION CONTROL")
    print("same logical operation submitted twice")
    print(f"visible effects without idempotency: {naive_count}")
    print("result: DUPLICATED")
    print()
    print("PROTECTED RETRY")
    print(f"first attempt: {first.decision.value} ({first.effect_id})")
    print("sink reopened before retry")
    print(f"retry with same operation id: {replay.decision.value} ({replay.effect_id})")
    print(f"visible effects: {protected_count}")
    print("result: ONE APPLICATION-VISIBLE EFFECT")
    print()
    print("IDENTITY CONFLICT")
    print("same operation id + different immutable content")
    print(f"result: REJECTED ({RejectionReason.IDEMPOTENCY_CONFLICT.value})")
    print()
    print("STABLE ID ASSUMPTION")
    print("same content + new operation id")
    print(f"result: {new_identity_result.decision.value}")
    print(f"visible effects after new identity: {count_after_new_identity}")
    print()
    print("RETENTION BOUNDARY")
    print("first logical effect remains visible")
    print("idempotency record expired")
    print(f"retry after expiry: {after_expiry.decision.value} ({after_expiry.effect_id})")
    print(f"visible effects after expiry: {retention_count}")
    print("result: AT-MOST-ONE GUARANTEE NO LONGER AVAILABLE")
    print()
    print("GUARANTEE")
    print(
        "Given a stable logical operation id, immutable content bound to that id, "
        "and a durable atomic idempotency record retained across the retry window, "
        "retries of the same logical operation produce at most one "
        "application-visible effect."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish safety after idempotency-record expiry, exactly-once "
        "execution or delivery, arbitrary provider idempotency, concurrent fencing, "
        "complete operation provenance, or durable dispatch."
    )
    return 0
