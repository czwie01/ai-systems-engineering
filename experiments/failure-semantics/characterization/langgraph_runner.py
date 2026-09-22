from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from typing import TypedDict

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
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    scenario: str
    mode: str
    output: str


def build_graph(
    *,
    root: Path,
    sink: Path,
    checkpointer: SqliteSaver,
):
    def prepare(_state: State) -> dict[str, str]:
        return {}

    def effect(state: State) -> dict[str, str]:
        scenario = Scenario(state["scenario"])
        mode = EffectMode(state["mode"])

        record_attempt(sink)
        if scenario is Scenario.BEFORE_EFFECT:
            crash_once(root, "before-effect")

        apply_effect(sink, mode)
        if scenario is Scenario.AFTER_EFFECT_BEFORE_CHECKPOINT:
            crash_once(root, "after-effect")

        return {}

    def post_checkpoint(state: State) -> dict[str, str]:
        if Scenario(state["scenario"]) is Scenario.AFTER_CHECKPOINT:
            crash_once(root, "after-checkpoint")
        return {}

    def finish(_state: State) -> dict[str, str]:
        return {"output": "done"}

    builder = StateGraph(State)
    builder.add_node("prepare", prepare)
    builder.add_node("effect", effect)
    builder.add_node("post_checkpoint", post_checkpoint)
    builder.add_node("finish", finish)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "effect")
    builder.add_edge("effect", "post_checkpoint")
    builder.add_edge("post_checkpoint", "finish")
    builder.add_edge("finish", END)
    return builder.compile(checkpointer=checkpointer)


def _config() -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": "failure-boundary"}}


def run_phase(
    *,
    root: Path,
    phase: str,
    scenario: Scenario,
    mode: EffectMode,
) -> None:
    sink = root / "sink.sqlite"
    database = root / "langgraph.sqlite"
    observation_path = root / "observation.json"

    if phase == "start":
        reset_case(root)

    root.mkdir(parents=True, exist_ok=True)

    with SqliteSaver.from_conn_string(str(database)) as checkpointer:
        graph = build_graph(root=root, sink=sink, checkpointer=checkpointer)
        config = _config()

        if phase == "start":
            graph.invoke(
                {
                    "scenario": scenario.value,
                    "mode": mode.value,
                    "output": "",
                },
                config,
                durability="sync",
            )
            raise AssertionError("failure injection did not terminate the process")

        if phase == "inspect":
            snapshot = graph.get_state(config)
            next_nodes = tuple(snapshot.next)
            _attempts, effect_count = sink_counts(sink)
            completion_recorded = "effect" not in next_nodes
            observation = observe_failure(
                framework="langgraph",
                scenario=scenario,
                mode=mode,
                effect_visible=effect_count > 0,
                completion_recorded=completion_recorded,
                framework_detail={"next_nodes": list(next_nodes)},
            )
            write_observation(observation_path, observation)
            return

        if phase == "resume":
            graph.invoke(None, config, durability="sync")
            snapshot = graph.get_state(config)
            assert snapshot.next == ()
            assert snapshot.values["output"] == "done"
            return

        if phase == "verify":
            observation = read_observation(observation_path)
            attempts, effects = sink_counts(sink)
            expected_attempts, expected_effects = expected_counts(scenario, mode)
            snapshot = graph.get_state(config)

            assert observation.completion_class == expected_class(scenario).value
            assert attempts == expected_attempts
            assert effects == expected_effects
            assert snapshot.values["output"] == "done"

            receipt = {
                "framework": "langgraph",
                "framework_version": importlib.metadata.version("langgraph"),
                "checkpoint_package_version": importlib.metadata.version(
                    "langgraph-checkpoint-sqlite"
                ),
                "scenario": scenario.value,
                "mode": mode.value,
                "completion_class_at_crash": observation.completion_class,
                "effect_visible_at_crash": observation.effect_visible,
                "completion_recorded_at_crash": observation.completion_recorded,
                "framework_detail": observation.framework_detail,
                "operation_attempts": attempts,
                "visible_effects": effects,
                "duplicate_effect": effects > 1,
                "final_output": snapshot.values["output"],
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
    run_phase(
        root=args.root,
        phase=args.phase,
        scenario=args.scenario,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
