"""Provider-neutral idempotency semantics for ambiguous completion retries."""

from dataclasses import dataclass
from enum import StrEnum


class RetryDisposition(StrEnum):
    """How an idempotency boundary handled one request."""

    APPLIED = "applied"
    REPLAYED = "replayed"


@dataclass(frozen=True, slots=True)
class OperationRequest:
    """One logical operation with caller-provided identity and immutable intent."""

    operation_id: str
    intent: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Stable result associated with one logical operation."""

    operation_id: str
    intent: tuple[str, ...]
    effect_id: str


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """Authoritative binding between operation identity, intent, and result."""

    intent: tuple[str, ...]
    result: OperationResult


class IdempotentEffectBoundary:
    """Atomic idempotency model for one application-visible effect boundary."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._effects: list[OperationResult] = []

    @property
    def visible_effects(self) -> tuple[OperationResult, ...]:
        """Return application-visible effects in creation order."""

        return tuple(self._effects)

    def execute(
        self,
        request: OperationRequest,
    ) -> tuple[RetryDisposition, OperationResult]:
        """Apply or replay one logical operation under the experiment model."""

        existing = self._records.get(request.operation_id)
        if existing is not None:
            if existing.intent != request.intent:
                raise ValueError("idempotency-conflict")
            return RetryDisposition.REPLAYED, existing.result

        effect_id = f"effect-{len(self._effects) + 1}"
        result = OperationResult(
            operation_id=request.operation_id,
            intent=request.intent,
            effect_id=effect_id,
        )

        # The experiment treats the effect and idempotency record as one atomic
        # boundary. There is deliberately no modeled crash point between them.
        self._effects.append(result)
        self._records[request.operation_id] = IdempotencyRecord(
            intent=request.intent,
            result=result,
        )
        return RetryDisposition.APPLIED, result

    def expire(self, operation_id: str) -> None:
        """Remove retained idempotency knowledge for one logical operation."""

        self._records.pop(operation_id, None)


def _naive_retry_effect_count(request: OperationRequest) -> int:
    effects = [request.intent]
    effects.append(request.intent)
    return len(effects)


def run_experiment() -> int:
    """Run failure-first idempotency controls for ambiguous completion."""

    request = OperationRequest(
        operation_id="op-1",
        intent=("create-resource", "resource-a"),
    )

    naive_effects = _naive_retry_effect_count(request)
    if naive_effects != 2:
        print("UNEXPECTED OBSERVATION: naive retry control did not duplicate")
        return 1

    boundary = IdempotentEffectBoundary()
    first_disposition, first_result = boundary.execute(request)
    retry_disposition, retry_result = boundary.execute(request)

    if (
        first_disposition is not RetryDisposition.APPLIED
        or retry_disposition is not RetryDisposition.REPLAYED
        or first_result != retry_result
        or len(boundary.visible_effects) != 1
    ):
        print("UNEXPECTED OBSERVATION: idempotent retry contract did not hold")
        return 1

    conflict = OperationRequest(
        operation_id=request.operation_id,
        intent=("create-resource", "resource-b"),
    )
    try:
        boundary.execute(conflict)
    except ValueError as error:
        if str(error) != "idempotency-conflict":
            raise
    else:
        print("UNEXPECTED OBSERVATION: conflicting intent was accepted")
        return 1

    if len(boundary.visible_effects) != 1:
        print("UNEXPECTED OBSERVATION: conflict created an effect")
        return 1

    boundary.expire(request.operation_id)
    post_expiry_disposition, _ = boundary.execute(request)
    if (
        post_expiry_disposition is not RetryDisposition.APPLIED
        or len(boundary.visible_effects) != 2
    ):
        print("UNEXPECTED OBSERVATION: retention control did not expose the boundary")
        return 1

    print("NAIVE RETRY CONTROL")
    print(f"visible effects after ambiguous retry: {naive_effects}")
    print("result: duplicate effect observed")
    print()

    print("IDEMPOTENCY CONTRACT")
    print(f"first request: {first_disposition.value}")
    print(f"retry: {retry_disposition.value}")
    print(f"stable result: {first_result.effect_id}")
    print("visible effects before expiry: 1")
    print("result: retry reused the prior logical operation")
    print()

    print("INTENT CONFLICT")
    print("result: REJECTED (idempotency-conflict)")
    print()

    print("RETENTION CONTROL")
    print("idempotency record expired")
    print("retry after expiry: applied")
    print("visible effects after expiry: 2")
    print("result: at-most-one guarantee no longer available")
    print()

    print("GUARANTEE")
    print(
        "Given stable operation identity and intent, retained authoritative "
        "idempotency state, and the experiment's atomic effect/record boundary, "
        "serial retries of one logical operation produce at most one "
        "application-visible effect."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish exactly-once delivery or execution, safety after "
        "idempotency-state expiry, concurrent-caller correctness, atomicity across "
        "arbitrary third-party systems, durable dispatch, complete operation "
        "provenance, or shared multi-actor authority."
    )
    return 0
