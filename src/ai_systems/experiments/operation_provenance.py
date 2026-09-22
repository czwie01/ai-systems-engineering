"""Durable provider-independent provenance for one logical operation."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_systems.experiments.ambiguous_completion import (
    LogicalOperation,
    operation_fingerprint,
)
from ai_systems.experiments.failure_semantics import CompletionClass


class EventType(StrEnum):
    """Stable M5 provenance event categories."""

    OPERATION_REGISTERED = "operation-registered"
    ATTEMPT_STARTED = "attempt-started"
    EFFECT_OBSERVED = "effect-observed"
    COMPLETION_OBSERVED = "completion-observed"
    RECOVERY_DECIDED = "recovery-decided"
    OPERATION_FINALIZED = "operation-finalized"


class RecoveryDecision(StrEnum):
    """Explicit recovery choices after ambiguous completion."""

    RETRY = "retry"
    RECONCILE = "reconcile"
    ESCALATE = "escalate"


class FinalDisposition(StrEnum):
    """Final operation dispositions represented by this experiment."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ESCALATED = "escalated"


class RejectionReason(StrEnum):
    """Deterministic M5 provenance validation failures."""

    NON_CONTIGUOUS_SEQUENCE = "non-contiguous-sequence"
    MIXED_OPERATION_IDENTITY = "mixed-operation-identity"
    MIXED_INTENT = "mixed-intent"
    INVALID_REGISTRATION = "invalid-registration"
    UNKNOWN_ATTEMPT = "unknown-attempt"
    DUPLICATE_ATTEMPT = "duplicate-attempt"
    MISSING_COMPLETION = "missing-completion"
    DUPLICATE_COMPLETION = "duplicate-completion"
    MISSING_RECOVERY_DECISION = "missing-recovery-decision"
    INVALID_RECOVERY_DECISION = "invalid-recovery-decision"
    DUPLICATE_RECOVERY_DECISION = "duplicate-recovery-decision"
    INVALID_FINALIZATION = "invalid-finalization"
    UNOBSERVED_FINAL_EFFECT = "unobserved-final-effect"


@dataclass(frozen=True, slots=True)
class ProvenanceEvent:
    """One durable observable or explicit decision in an operation history."""

    sequence: int
    event_type: EventType
    operation_id: str
    intent_fingerprint: str
    effect_name: str
    attempt_id: str | None = None
    mechanism: str | None = None
    completion_class: CompletionClass | None = None
    effect_id: str | None = None
    recovery_decision: RecoveryDecision | None = None
    final_disposition: FinalDisposition | None = None


@dataclass(frozen=True, slots=True)
class AuditView:
    """Minimal reconstructed audit view for one logical operation."""

    operation_id: str
    intent_fingerprint: str
    effect_name: str
    attempt_ids: tuple[str, ...]
    mechanisms: tuple[str, ...]
    completion_classes: tuple[CompletionClass, ...]
    recovery_decisions: tuple[RecoveryDecision, ...]
    observed_effect_ids: tuple[str, ...]
    final_disposition: FinalDisposition
    final_effect_id: str | None


@dataclass(frozen=True, slots=True)
class FinalSummary:
    """Deliberately lossy final-state-only projection."""

    operation_id: str
    final_disposition: FinalDisposition
    final_effect_id: str | None


class ProvenanceValidationError(ValueError):
    """Raised when one operation history violates the M5 contract."""

    def __init__(self, reason: RejectionReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


class ProvenanceJournal:
    """Small durable append/read store for operation provenance events."""

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provenance_events (
                    sequence INTEGER PRIMARY KEY,
                    event_json TEXT NOT NULL
                )
                """
            )

    def append(self, event: ProvenanceEvent) -> None:
        """Append one event at its explicit sequence number."""

        payload = {
            "sequence": event.sequence,
            "event_type": event.event_type.value,
            "operation_id": event.operation_id,
            "intent_fingerprint": event.intent_fingerprint,
            "effect_name": event.effect_name,
            "attempt_id": event.attempt_id,
            "mechanism": event.mechanism,
            "completion_class": (
                event.completion_class.value if event.completion_class else None
            ),
            "effect_id": event.effect_id,
            "recovery_decision": (
                event.recovery_decision.value if event.recovery_decision else None
            ),
            "final_disposition": (
                event.final_disposition.value if event.final_disposition else None
            ),
        }
        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                INSERT INTO provenance_events(sequence, event_json)
                VALUES (?, ?)
                """,
                (event.sequence, json.dumps(payload, sort_keys=True)),
            )

    def read(self) -> tuple[ProvenanceEvent, ...]:
        """Read the durable history in sequence order."""

        with sqlite3.connect(self._path) as connection:
            rows = connection.execute(
                """
                SELECT event_json
                FROM provenance_events
                ORDER BY sequence
                """
            ).fetchall()

        events: list[ProvenanceEvent] = []
        for (payload,) in rows:
            value = json.loads(str(payload))
            events.append(
                ProvenanceEvent(
                    sequence=int(value["sequence"]),
                    event_type=EventType(value["event_type"]),
                    operation_id=str(value["operation_id"]),
                    intent_fingerprint=str(value["intent_fingerprint"]),
                    effect_name=str(value["effect_name"]),
                    attempt_id=value["attempt_id"],
                    mechanism=value["mechanism"],
                    completion_class=(
                        CompletionClass(value["completion_class"])
                        if value["completion_class"]
                        else None
                    ),
                    effect_id=value["effect_id"],
                    recovery_decision=(
                        RecoveryDecision(value["recovery_decision"])
                        if value["recovery_decision"]
                        else None
                    ),
                    final_disposition=(
                        FinalDisposition(value["final_disposition"])
                        if value["final_disposition"]
                        else None
                    ),
                )
            )
        return tuple(events)


def _registration_event(
    operation: LogicalOperation,
    *,
    sequence: int = 1,
) -> ProvenanceEvent:
    return ProvenanceEvent(
        sequence=sequence,
        event_type=EventType.OPERATION_REGISTERED,
        operation_id=operation.operation_id,
        intent_fingerprint=operation_fingerprint(operation),
        effect_name=operation.effect_name,
    )


def validate_history(events: tuple[ProvenanceEvent, ...]) -> AuditView:
    """Validate one durable history and reconstruct its audit view."""

    if not events or tuple(event.sequence for event in events) != tuple(
        range(1, len(events) + 1)
    ):
        raise ProvenanceValidationError(RejectionReason.NON_CONTIGUOUS_SEQUENCE)

    operation_ids = {event.operation_id for event in events}
    if len(operation_ids) != 1:
        raise ProvenanceValidationError(RejectionReason.MIXED_OPERATION_IDENTITY)

    intent_keys = {(event.intent_fingerprint, event.effect_name) for event in events}
    if len(intent_keys) != 1:
        raise ProvenanceValidationError(RejectionReason.MIXED_INTENT)

    first = events[0]
    if (
        first.event_type is not EventType.OPERATION_REGISTERED
        or first.attempt_id is not None
        or first.mechanism is not None
        or first.completion_class is not None
        or first.effect_id is not None
        or first.recovery_decision is not None
        or first.final_disposition is not None
    ):
        raise ProvenanceValidationError(RejectionReason.INVALID_REGISTRATION)

    started_attempts: dict[str, str] = {}
    completion_by_attempt: dict[str, CompletionClass] = {}
    recovery_by_attempt: dict[str, RecoveryDecision] = {}
    observed_effect_ids: list[str] = []
    final_events: list[ProvenanceEvent] = []

    for event in events[1:]:
        if event.event_type is EventType.ATTEMPT_STARTED:
            if event.attempt_id is None or event.mechanism is None:
                raise ProvenanceValidationError(RejectionReason.UNKNOWN_ATTEMPT)
            if event.attempt_id in started_attempts:
                raise ProvenanceValidationError(RejectionReason.DUPLICATE_ATTEMPT)
            started_attempts[event.attempt_id] = event.mechanism
            continue

        if event.attempt_id is not None and event.attempt_id not in started_attempts:
            raise ProvenanceValidationError(RejectionReason.UNKNOWN_ATTEMPT)

        if event.event_type is EventType.EFFECT_OBSERVED:
            if event.attempt_id is None or event.effect_id is None:
                raise ProvenanceValidationError(RejectionReason.UNKNOWN_ATTEMPT)
            observed_effect_ids.append(event.effect_id)
            continue

        if event.event_type is EventType.COMPLETION_OBSERVED:
            if event.attempt_id is None or event.completion_class is None:
                raise ProvenanceValidationError(RejectionReason.UNKNOWN_ATTEMPT)
            if event.attempt_id in completion_by_attempt:
                raise ProvenanceValidationError(RejectionReason.DUPLICATE_COMPLETION)
            completion_by_attempt[event.attempt_id] = event.completion_class
            continue

        if event.event_type is EventType.RECOVERY_DECIDED:
            if event.attempt_id is None or event.recovery_decision is None:
                raise ProvenanceValidationError(
                    RejectionReason.INVALID_RECOVERY_DECISION
                )
            if (
                completion_by_attempt.get(event.attempt_id)
                is not CompletionClass.AMBIGUOUS_COMPLETION
            ):
                raise ProvenanceValidationError(
                    RejectionReason.INVALID_RECOVERY_DECISION
                )
            if event.attempt_id in recovery_by_attempt:
                raise ProvenanceValidationError(
                    RejectionReason.DUPLICATE_RECOVERY_DECISION
                )
            recovery_by_attempt[event.attempt_id] = event.recovery_decision
            continue

        if event.event_type is EventType.OPERATION_FINALIZED:
            final_events.append(event)
            continue

    if set(started_attempts) != set(completion_by_attempt):
        raise ProvenanceValidationError(RejectionReason.MISSING_COMPLETION)

    for attempt_id, completion in completion_by_attempt.items():
        if (
            completion is CompletionClass.AMBIGUOUS_COMPLETION
            and attempt_id not in recovery_by_attempt
        ):
            raise ProvenanceValidationError(RejectionReason.MISSING_RECOVERY_DECISION)

    if len(final_events) != 1 or final_events[0] is not events[-1]:
        raise ProvenanceValidationError(RejectionReason.INVALID_FINALIZATION)

    final = final_events[0]
    if final.final_disposition is None or final.attempt_id is not None:
        raise ProvenanceValidationError(RejectionReason.INVALID_FINALIZATION)

    if final.final_disposition is FinalDisposition.SUCCEEDED and (
        final.effect_id is None or final.effect_id not in observed_effect_ids
    ):
        raise ProvenanceValidationError(RejectionReason.UNOBSERVED_FINAL_EFFECT)

    return AuditView(
        operation_id=first.operation_id,
        intent_fingerprint=first.intent_fingerprint,
        effect_name=first.effect_name,
        attempt_ids=tuple(started_attempts),
        mechanisms=tuple(started_attempts.values()),
        completion_classes=tuple(completion_by_attempt.values()),
        recovery_decisions=tuple(recovery_by_attempt.values()),
        observed_effect_ids=tuple(observed_effect_ids),
        final_disposition=final.final_disposition,
        final_effect_id=final.effect_id,
    )


def final_summary(events: tuple[ProvenanceEvent, ...]) -> FinalSummary:
    """Return a deliberately lossy projection of only the final operation state."""

    final = next(
        event
        for event in reversed(events)
        if event.event_type is EventType.OPERATION_FINALIZED
    )
    if final.final_disposition is None:
        raise ProvenanceValidationError(RejectionReason.INVALID_FINALIZATION)

    return FinalSummary(
        operation_id=final.operation_id,
        final_disposition=final.final_disposition,
        final_effect_id=final.effect_id,
    )


def direct_success_history(operation: LogicalOperation) -> tuple[ProvenanceEvent, ...]:
    """One-attempt success with the same final state as the retry history."""

    fingerprint = operation_fingerprint(operation)
    return (
        _registration_event(operation),
        ProvenanceEvent(
            2,
            EventType.ATTEMPT_STARTED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            mechanism="provider-a",
        ),
        ProvenanceEvent(
            3,
            EventType.EFFECT_OBSERVED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            effect_id="effect-001",
        ),
        ProvenanceEvent(
            4,
            EventType.COMPLETION_OBSERVED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            completion_class=CompletionClass.COMPLETION_RECORDED,
        ),
        ProvenanceEvent(
            5,
            EventType.OPERATION_FINALIZED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            effect_id="effect-001",
            final_disposition=FinalDisposition.SUCCEEDED,
        ),
    )


def recovered_history(operation: LogicalOperation) -> tuple[ProvenanceEvent, ...]:
    """Ambiguous first attempt followed by an explicit retry and success."""

    fingerprint = operation_fingerprint(operation)
    return (
        _registration_event(operation),
        ProvenanceEvent(
            2,
            EventType.ATTEMPT_STARTED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            mechanism="provider-a",
        ),
        ProvenanceEvent(
            3,
            EventType.EFFECT_OBSERVED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            effect_id="effect-001",
        ),
        ProvenanceEvent(
            4,
            EventType.COMPLETION_OBSERVED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            completion_class=CompletionClass.AMBIGUOUS_COMPLETION,
        ),
        ProvenanceEvent(
            5,
            EventType.RECOVERY_DECIDED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-1",
            recovery_decision=RecoveryDecision.RETRY,
        ),
        ProvenanceEvent(
            6,
            EventType.ATTEMPT_STARTED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-2",
            mechanism="provider-b",
        ),
        ProvenanceEvent(
            7,
            EventType.EFFECT_OBSERVED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-2",
            effect_id="effect-001",
        ),
        ProvenanceEvent(
            8,
            EventType.COMPLETION_OBSERVED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            attempt_id="attempt-2",
            completion_class=CompletionClass.COMPLETION_RECORDED,
        ),
        ProvenanceEvent(
            9,
            EventType.OPERATION_FINALIZED,
            operation.operation_id,
            fingerprint,
            operation.effect_name,
            effect_id="effect-001",
            final_disposition=FinalDisposition.SUCCEEDED,
        ),
    )


def run_experiment() -> int:
    """Run the failure-first operation-provenance probe."""

    operation = LogicalOperation(
        operation_id="operation-001",
        effect_name="publish-artifact",
        payload="artifact-v1",
    )
    direct = direct_success_history(operation)
    recovered = recovered_history(operation)

    direct_summary = final_summary(direct)
    recovered_summary = final_summary(recovered)
    direct_audit = validate_history(direct)
    recovered_audit = validate_history(recovered)

    incomplete = tuple(
        event
        for event in recovered
        if event.event_type is not EventType.RECOVERY_DECIDED
    )
    incomplete = tuple(
        replace(event, sequence=index)
        for index, event in enumerate(incomplete, start=1)
    )

    rejection: RejectionReason | None = None
    try:
        validate_history(incomplete)
    except ProvenanceValidationError as error:
        rejection = error.reason

    with TemporaryDirectory() as directory:
        path = Path(directory) / "provenance.sqlite"
        journal = ProvenanceJournal(path)
        for event in recovered:
            journal.append(event)

        reopened = ProvenanceJournal(path)
        durable_audit = validate_history(reopened.read())

    if (
        direct_summary != recovered_summary
        or direct_audit.attempt_ids == recovered_audit.attempt_ids
        or recovered_audit.attempt_ids != ("attempt-1", "attempt-2")
        or recovered_audit.recovery_decisions != (RecoveryDecision.RETRY,)
        or recovered_audit.observed_effect_ids != ("effect-001", "effect-001")
        or rejection is not RejectionReason.MISSING_RECOVERY_DECISION
        or durable_audit != recovered_audit
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    print("FINAL-STATE-ONLY CONTROL")
    print("direct-success summary:", direct_summary)
    print("recovered-retry summary:", recovered_summary)
    print("result: HISTORIES COLLAPSED TO THE SAME FINAL SUMMARY")
    print()
    print("PROVENANCE AUDIT")
    print(f"attempts: {', '.join(recovered_audit.attempt_ids)}")
    print(f"mechanisms: {', '.join(recovered_audit.mechanisms)}")
    print(
        "completion classes:",
        ", ".join(item.value for item in recovered_audit.completion_classes),
    )
    print(
        "recovery decisions:",
        ", ".join(item.value for item in recovered_audit.recovery_decisions),
    )
    print(
        "observed effects:",
        ", ".join(recovered_audit.observed_effect_ids),
    )
    print(f"final disposition: {recovered_audit.final_disposition.value}")
    print("result: RECOVERY PATH RETAINED")
    print()
    print("INCOMPLETE HISTORY")
    print("ambiguous completion with recovery decision removed")
    print(f"result: REJECTED ({RejectionReason.MISSING_RECOVERY_DECISION.value})")
    print()
    print("DURABILITY CHECK")
    print("journal reopened from SQLite")
    print("result: AUDIT VIEW PRESERVED")
    print()
    print("GUARANTEE")
    print(
        "Under the declared event model, a valid provenance journal preserves one "
        "operation's immutable intent identity, ordered attempts, completion "
        "observations, ambiguous-completion recovery decisions, observed effect "
        "identities, and final disposition well enough to distinguish a recovered "
        "retry from an otherwise identical direct-success final summary."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish tamper evidence, hidden reasoning capture, "
        "distributed consistency, complete tracing, concurrent fencing, or durable "
        "dispatch."
    )
    return 0
