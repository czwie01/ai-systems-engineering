from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    trace: list[str]
    attempt: int
    passed: bool
    intent_approved: bool
    promotion_approved: bool
    artifact: str
    output: str


def _append(state: State, event: str) -> list[str]:
    return [*state["trace"], event]


def _record_once(journal: Path, operation_id: str) -> None:
    existing = journal.read_text().splitlines() if journal.exists() else []
    if operation_id not in existing:
        journal.parent.mkdir(parents=True, exist_ok=True)
        with journal.open("a", encoding="utf-8") as handle:
            handle.write(operation_id + "\n")


def build_graph(journal: Path, checkpointer: SqliteSaver):
    def capture(state: State) -> dict[str, object]:
        return {"trace": _append(state, "capture")}

    def characterize(state: State) -> dict[str, object]:
        return {"trace": _append(state, "characterize")}

    def intent_gate(state: State) -> dict[str, object]:
        approved = bool(
            interrupt(
                {
                    "gate": "intent",
                    "question": "Approve the bounded artifact intent?",
                }
            )
        )
        return {
            "trace": _append(state, "intent-approved"),
            "intent_approved": approved,
        }

    def execute(state: State) -> dict[str, object]:
        operation_id = f"execute-{state['attempt']}"
        _record_once(journal, operation_id)
        return {
            "trace": _append(state, operation_id),
            "artifact": f"candidate-{state['attempt']}",
        }

    def observe(state: State) -> dict[str, object]:
        return {"trace": _append(state, f"observe-{state['attempt']}")}

    def falsify(state: State) -> dict[str, object]:
        passed = state["attempt"] >= 1
        label = "pass" if passed else "fail"
        return {
            "trace": _append(state, f"falsify-{state['attempt']}-{label}"),
            "passed": passed,
        }

    def route_after_falsify(state: State) -> str:
        return "promotion_gate" if state["passed"] else "repair"

    def repair(state: State) -> dict[str, object]:
        next_attempt = state["attempt"] + 1
        return {
            "trace": _append(state, f"repair-{next_attempt}"),
            "attempt": next_attempt,
        }

    def promotion_gate(state: State) -> dict[str, object]:
        approved = bool(
            interrupt(
                {
                    "gate": "promotion",
                    "question": "Promote the verified candidate?",
                    "artifact": state["artifact"],
                }
            )
        )
        return {
            "trace": _append(state, "promotion-approved"),
            "promotion_approved": approved,
        }

    def package(state: State) -> dict[str, object]:
        output = f"packaged:{state['artifact']}"
        return {
            "trace": _append(state, "package"),
            "output": output,
        }

    builder = StateGraph(State)
    builder.add_node("capture", capture)
    builder.add_node("characterize", characterize)
    builder.add_node("intent_gate", intent_gate)
    builder.add_node("execute", execute)
    builder.add_node("observe", observe)
    builder.add_node("falsify", falsify)
    builder.add_node("repair", repair)
    builder.add_node("promotion_gate", promotion_gate)
    builder.add_node("package", package)

    builder.add_edge(START, "capture")
    builder.add_edge("capture", "characterize")
    builder.add_edge("characterize", "intent_gate")
    builder.add_edge("intent_gate", "execute")
    builder.add_edge("execute", "observe")
    builder.add_edge("observe", "falsify")
    builder.add_conditional_edges(
        "falsify",
        route_after_falsify,
        {"repair": "repair", "promotion_gate": "promotion_gate"},
    )
    builder.add_edge("repair", "execute")
    builder.add_edge("promotion_gate", "package")
    builder.add_edge("package", END)
    return builder.compile(checkpointer=checkpointer)


def _initial_state() -> State:
    return {
        "trace": [],
        "attempt": 0,
        "passed": False,
        "intent_approved": False,
        "promotion_approved": False,
        "artifact": "",
        "output": "",
    }


def _assert_paused_on(graph, config: dict[str, object], gate: str) -> None:
    snapshot = graph.get_state(config)
    interrupts = [
        item.value
        for task in snapshot.tasks
        for item in task.interrupts
    ]
    assert any(
        isinstance(value, dict) and value.get("gate") == gate
        for value in interrupts
    ), (gate, interrupts)


def run_phase(root: Path, phase: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    database = root / "state.sqlite"
    journal = root / "side-effects.log"
    config = {"configurable": {"thread_id": "r2-artifact"}}

    if phase == "start":
        for path in (database, journal, root / "receipt.json"):
            if path.exists():
                path.unlink()

    with SqliteSaver.from_conn_string(str(database)) as checkpointer:
        graph = build_graph(journal, checkpointer)

        if phase == "start":
            graph.invoke(_initial_state(), config, durability="sync")
            _assert_paused_on(graph, config, "intent")
            return

        if phase == "resume-intent":
            graph.invoke(Command(resume=True), config, durability="sync")
            _assert_paused_on(graph, config, "promotion")
            state = graph.get_state(config).values
            assert state["attempt"] == 1
            assert state["passed"] is True
            return

        if phase == "resume-promotion":
            graph.invoke(Command(resume=True), config, durability="sync")
            snapshot = graph.get_state(config)
            assert snapshot.next == ()
            assert snapshot.values["output"] == "packaged:candidate-1"
            return

        if phase == "verify":
            snapshot = graph.get_state(config)
            state = snapshot.values
            operations = journal.read_text().splitlines()
            expected = ["execute-0", "execute-1"]
            assert operations == expected, operations
            assert len(operations) == len(set(operations))
            assert state["intent_approved"] is True
            assert state["promotion_approved"] is True
            assert state["attempt"] == 1
            assert state["passed"] is True
            assert state["output"] == "packaged:candidate-1"

            receipt = {
                "framework": "langgraph",
                "framework_version": importlib.metadata.version("langgraph"),
                "checkpoint_package_version": importlib.metadata.version(
                    "langgraph-checkpoint-sqlite"
                ),
                "state_store": "sqlite",
                "fresh_controller_boundaries": 2,
                "human_gates": ["intent", "promotion"],
                "bounded_repair_attempts": state["attempt"],
                "side_effect_operations": operations,
                "duplicate_side_effects": False,
                "final_output": state["output"],
                "final_trace": state["trace"],
                "observed_result": "pass",
            }
            receipt_path = root / "receipt.json"
            receipt_path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(receipt_path.read_text(), end="")
            return

    raise ValueError(f"unknown phase: {phase}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=["start", "resume-intent", "resume-promotion", "verify"],
    )
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    run_phase(args.root, args.phase)


if __name__ == "__main__":
    main()
