"""Provider- and framework-neutral failure semantic classification."""

from dataclasses import dataclass
from enum import StrEnum


class CompletionClass(StrEnum):
    """Stable application-level completion classifications."""

    DEFINITE_NO_EFFECT = "definite-no-effect"
    AMBIGUOUS_COMPLETION = "ambiguous-completion"
    COMPLETION_RECORDED = "completion-recorded"


@dataclass(frozen=True, slots=True)
class FailureObservation:
    """Observable facts available after one execution failure boundary."""

    source: str
    raw_failure: str
    effect_visible: bool
    completion_recorded: bool


def classify_completion(observation: FailureObservation) -> CompletionClass:
    """Map observable completion facts to a stable application classification."""

    if observation.completion_recorded and not observation.effect_visible:
        raise ValueError("completion cannot be recorded while the effect is absent")

    if not observation.effect_visible:
        return CompletionClass.DEFINITE_NO_EFFECT

    if not observation.completion_recorded:
        return CompletionClass.AMBIGUOUS_COMPLETION

    return CompletionClass.COMPLETION_RECORDED


def raw_failure_code(observation: FailureObservation) -> str:
    """Expose the provider/framework-specific failure label as a weak control."""

    return observation.raw_failure


def run_experiment() -> int:
    """Run a synthetic failure-first classification probe."""

    provider_a = (
        FailureObservation(
            source="provider-a",
            raw_failure="worker-process-exit",
            effect_visible=False,
            completion_recorded=False,
        ),
        FailureObservation(
            source="provider-a",
            raw_failure="worker-process-exit-after-effect",
            effect_visible=True,
            completion_recorded=False,
        ),
        FailureObservation(
            source="provider-a",
            raw_failure="post-checkpoint-controller-exit",
            effect_visible=True,
            completion_recorded=True,
        ),
    )
    provider_b = (
        FailureObservation(
            source="provider-b",
            raw_failure="executor-terminated",
            effect_visible=False,
            completion_recorded=False,
        ),
        FailureObservation(
            source="provider-b",
            raw_failure="executor-terminated-after-effect",
            effect_visible=True,
            completion_recorded=False,
        ),
        FailureObservation(
            source="provider-b",
            raw_failure="continuation-interrupted",
            effect_visible=True,
            completion_recorded=True,
        ),
    )

    raw_pairs = tuple(
        (raw_failure_code(left), raw_failure_code(right))
        for left, right in zip(provider_a, provider_b, strict=True)
    )
    classified_pairs = tuple(
        (classify_completion(left), classify_completion(right))
        for left, right in zip(provider_a, provider_b, strict=True)
    )

    expected = (
        CompletionClass.DEFINITE_NO_EFFECT,
        CompletionClass.AMBIGUOUS_COMPLETION,
        CompletionClass.COMPLETION_RECORDED,
    )

    if (
        any(left == right for left, right in raw_pairs)
        or tuple(left for left, _ in classified_pairs) != expected
        or any(left is not right for left, right in classified_pairs)
    ):
        print("UNEXPECTED OBSERVATION: experiment assertions did not hold")
        return 1

    print("RAW FAILURE CONTROL")
    for index, (left, right) in enumerate(raw_pairs, start=1):
        print(f"scenario {index}: provider-a={left}; provider-b={right}")
    print("result: provider/framework-specific labels disagree")
    print()
    print("APPLICATION CLASSIFICATION")
    for index, (left, right) in enumerate(classified_pairs, start=1):
        print(f"scenario {index}: provider-a={left.value}; provider-b={right.value}")
    print("result: equivalent observable states map to the same classification")
    print()
    print("GUARANTEE")
    print(
        "Under the declared observation model, failures with equivalent effect "
        "visibility and completion-recording facts receive the same "
        "provider- and framework-independent completion classification."
    )
    print()
    print("NON-GUARANTEE")
    print(
        "This does not establish exactly-once effects, safe retries, durable "
        "dispatch, source-of-truth correctness, or that the required observations "
        "are always available from an execution framework."
    )
    return 0
