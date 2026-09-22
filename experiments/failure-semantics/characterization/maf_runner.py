from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
from pathlib import Path
from typing import Any

from agent_framework import (
    Executor,
    FileCheckpointStorage,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from common import (
    EffectMode,
    Scenario,
    apply_effect,
    crash_once,
    expected_class,
    expected_counts,
    observe_failure,
    read_observation,
    record_attempt,
    reset_case,
    sink_counts,
    write_observation,
)


class Prepare(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        await ctx.send_message(message)


class Effect(Executor):
    def __init__(self, *, root: Path, sink: Path) -> None:
        super().__init__(id="effect")
        self._root = root
        self._sink = sink

    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = json.loads(message)
        scenario = Scenario(state["scenario"])
        mode = EffectMode(state["mode"])

        record_attempt(self._sink)
        if scenario is Scenario.BEFORE_EFFECT:
            crash_once(self._root, "before-effect")

        apply_effect(self._sink, mode)
        if scenario is Scenario.AFTER_EFFECT_BEFORE_CHECKPOINT:
            crash_once(self._root, "after-effect")

        await ctx.send_message(message)


class PostCheckpoint(Executor):
    def __init__(self, *, root: Path) -> None:
        super().__init__(id="post_checkpoint")
        self._root = root

    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = json.loads(message)
        if Scenario(state["scenario"]) is Scenario.AFTER_CHECKPOINT:
            crash_once(self._root, "after-checkpoint")
        await ctx.send_message(message)


class Finish(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[Any, str]) -> None:
        state = json.loads(message)
        state["output"] = "done"
        await ctx.yield_output(json.dumps(state, sort_keys=True))


def build_workflow(
    *,
    root: Path,
    sink: Path,
    storage: FileCheckpointStorage,
) -> Workflow:
    prepare = Prepare(id="prepare")
    effect = Effect(root=root, sink=sink)
    post_checkpoint = PostCheckpoint(root=root)
    finish = Finish(id="finish")

    return (
        WorkflowBuilder(
            name="failure-boundary",
            start_executor=prepare,
            checkpoint_storage=storage,
            output_from=[finish],
            max_iterations=10,
        )
        .add_edge(prepare, effect)
        .add_edge(effect, post_checkpoint)
        .add_edge(post_checkpoint, finish)
        .build()
    )


async def _latest_checkpoint(
    storage: FileCheckpointStorage,
):
    checkpoints = await storage.list_checkpoints(workflow_name="failure-boundary")
    assert checkpoints
    return sorted(checkpoints, key=lambda item: item.timestamp)[-1]


async def _run_to_output(
    workflow: Workflow,
    *,
    message: str | None = None,
    checkpoint_id: str | None = None,
) -> str | None:
    kwargs: dict[str, Any] = {"stream": True}
    if message is not None:
        kwargs["message"] = message
    if checkpoint_id is not None:
        kwargs["checkpoint_id"] = checkpoint_id

    output: str | None = None
    async for event in workflow.run(**kwargs):
        if event.type == "output":
            output = event.data
    return output


async def run_phase(
    *,
    root: Path,
    phase: str,
    scenario: Scenario,
    mode: EffectMode,
) -> None:
    if phase == "start":
        reset_case(root)

    root.mkdir(parents=True, exist_ok=True)
    sink = root / "sink.sqlite"
    observation_path = root / "observation.json"
    final_path = root / "final.json"
    storage = FileCheckpointStorage(storage_path=root / "checkpoints")
    workflow = build_workflow(root=root, sink=sink, storage=storage)

    if phase == "start":
        message = json.dumps(
            {"scenario": scenario.value, "mode": mode.value, "output": ""},
            sort_keys=True,
        )
        await _run_to_output(workflow, message=message)
        raise AssertionError("failure injection did not terminate the process")

    if phase == "inspect":
        latest = await _latest_checkpoint(storage)
        _attempts, effect_count = sink_counts(sink)
        completion_recorded = latest.iteration_count >= 2
        observation = observe_failure(
            framework="microsoft-agent-framework-core",
            scenario=scenario,
            mode=mode,
            effect_visible=effect_count > 0,
            completion_recorded=completion_recorded,
            framework_detail={
                "checkpoint_id": latest.checkpoint_id,
                "iteration_count": latest.iteration_count,
            },
        )
        write_observation(observation_path, observation)
        return

    if phase == "resume":
        latest = await _latest_checkpoint(storage)
        output = await _run_to_output(
            workflow,
            checkpoint_id=latest.checkpoint_id,
        )
        assert output is not None
        final_path.write_text(output + "\n", encoding="utf-8")
        return

    if phase == "verify":
        observation = read_observation(observation_path)
        attempts, effects = sink_counts(sink)
        expected_attempts, expected_effects = expected_counts(scenario, mode)
        state = json.loads(final_path.read_text())

        assert observation.completion_class == expected_class(scenario).value
        assert attempts == expected_attempts
        assert effects == expected_effects
        assert state["output"] == "done"

        receipt = {
            "framework": "microsoft-agent-framework-core",
            "framework_version": importlib.metadata.version("agent-framework-core"),
            "scenario": scenario.value,
            "mode": mode.value,
            "completion_class_at_crash": observation.completion_class,
            "effect_visible_at_crash": observation.effect_visible,
            "completion_recorded_at_crash": observation.completion_recorded,
            "framework_detail": observation.framework_detail,
            "operation_attempts": attempts,
            "visible_effects": effects,
            "duplicate_effect": effects > 1,
            "final_output": state["output"],
            "observed_result": "pass",
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return

    raise ValueError(f"unknown phase: {phase}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["start", "inspect", "resume", "verify"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--scenario", type=Scenario, required=True)
    parser.add_argument("--mode", type=EffectMode, required=True)
    args = parser.parse_args()
    asyncio.run(
        run_phase(
            root=args.root,
            phase=args.phase,
            scenario=args.scenario,
            mode=args.mode,
        )
    )


if __name__ == "__main__":
    main()
