import pytest

from ai_systems.experiments.failure_semantics import (
    CompletionClass,
    FailureObservation,
    classify_completion,
)


@pytest.mark.parametrize(
    ("effect_visible", "completion_recorded", "expected"),
    [
        (False, False, CompletionClass.DEFINITE_NO_EFFECT),
        (True, False, CompletionClass.AMBIGUOUS_COMPLETION),
        (True, True, CompletionClass.COMPLETION_RECORDED),
    ],
)
def test_completion_classification(
    effect_visible: bool,
    completion_recorded: bool,
    expected: CompletionClass,
) -> None:
    observation = FailureObservation(
        source="synthetic",
        raw_failure="raw-provider-label",
        effect_visible=effect_visible,
        completion_recorded=completion_recorded,
    )

    assert classify_completion(observation) is expected


def test_equivalent_observations_ignore_provider_failure_labels() -> None:
    left = FailureObservation(
        source="provider-a",
        raw_failure="worker-exited",
        effect_visible=True,
        completion_recorded=False,
    )
    right = FailureObservation(
        source="provider-b",
        raw_failure="executor-terminated",
        effect_visible=True,
        completion_recorded=False,
    )

    assert classify_completion(left) is CompletionClass.AMBIGUOUS_COMPLETION
    assert classify_completion(right) is CompletionClass.AMBIGUOUS_COMPLETION


def test_inconsistent_completion_observation_is_rejected() -> None:
    observation = FailureObservation(
        source="synthetic",
        raw_failure="impossible-under-model",
        effect_visible=False,
        completion_recorded=True,
    )

    with pytest.raises(
        ValueError,
        match="completion cannot be recorded while the effect is absent",
    ):
        classify_completion(observation)
