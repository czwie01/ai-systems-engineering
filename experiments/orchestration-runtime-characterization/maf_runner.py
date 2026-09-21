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
    handler,
    response_handler,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
)


JOURNAL: Path


def _load(message: str) -> dict[str, Any]:
    value = json.loads(message)
    if not isinstance(value, dict):
        raise TypeError("state must decode to an object")
    return value


def _dump(state: dict[str, Any]) -> str:
    return json.dumps(state, sort_keys=True)


def _trace(state: dict[str, Any], event: str) -> None:
    state["trace"].append(event)


def _record_once(operation_id: str) -> None:
    existing = JOURNAL.read_text().splitlines() if JOURNAL.exists() else []
    if operation_id not in existing:
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        with JOURNAL.open("a", encoding="utf-8") as handle:
            handle.write(operation_id + "\n")


class Capture(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = _load(message)
        _trace(state, "capture")
        await ctx.send_message(_dump(state))


class Characterize(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = _load(message)
        _trace(state, "characterize")
        await ctx.send_message(_dump(state))


class IntentGate(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext) -> None:
        await ctx.request_info(
            request_data=message,
            response_type=str,
            request_id="intent",
        )

    @response_handler
    async def resume(
        self,
        original_request: str,
        response: str,
        ctx: WorkflowContext[str],
    ) -> None:
        assert response == "approve"
        state = _load(original_request)
        state["intent_approved"] = True
        _trace(state, "intent-approved")
        await ctx.send_message(_dump(state), target_id="execute")


class Execute(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = _load(message)
        operation_id = f"execute-{state['attempt']}"
        _record_once(operation_id)
        state["artifact"] = f"candidate-{state['attempt']}"
        _trace(state, operation_id)
        await ctx.send_message(_dump(state))


class Observe(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = _load(message)
        _trace(state, f"observe-{state['attempt']}")
        await ctx.send_message(_dump(state))


class Falsify(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = _load(message)
        passed = state["attempt"] >= 1
        state["passed"] = passed
        label = "pass" if passed else "fail"
        _trace(state, f"falsify-{state['attempt']}-{label}")
        target = "promotion" if passed else "repair"
        await ctx.send_message(_dump(state), target_id=target)


class Repair(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[str]) -> None:
        state = _load(message)
        state["attempt"] += 1
        _trace(state, f"repair-{state['attempt']}")
        await ctx.send_message(_dump(state), target_id="execute")


class PromotionGate(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext) -> None:
        await ctx.request_info(
            request_data=message,
            response_type=str,
            request_id="promotion",
        )

    @response_handler
    async def resume(
        self,
        original_request: str,
        response: str,
        ctx: WorkflowContext[str],
    ) -> None:
        assert response == "approve"
        state = _load(original_request)
        state["promotion_approved"] = True
        _trace(state, "promotion-approved")
        await ctx.send_message(_dump(state), target_id="package")


class Package(Executor):
    @handler
    async def run(self, message: str, ctx: WorkflowContext[Any, str]) -> None:
        state = _load(message)
        state["output"] = f"packaged:{state['artifact']}"
        _trace(state, "package")
        await ctx.yield_output(_dump(state))


def build_workflow(storage: FileCheckpointStorage) -> Workflow:
    capture = Capture(id="capture")
    characterize = Characterize(id="characterize")
    intent = IntentGate(id="intent")
    execute = Execute(id="execute")
    observe = Observe(id="observe")
    falsify = Falsify(id="falsify")
    repair = Repair(id="repair")
    promotion = PromotionGate(id="promotion")
    package = Package(id="package")

    return (
        WorkflowBuilder(
            name="r2-artifact",
            start_executor=capture,
            checkpoint_storage=storage,
            output_from=[package],
            max_iterations=20,
        )
        .add_edge(capture, characterize)
        .add_edge(characterize, intent)
        .add_edge(intent, execute)
        .add_edge(execute, observe)
        .add_edge(observe, falsify)
        .add_edge(falsify, repair)
        .add_edge(falsify, promotion)
        .add_edge(repair, execute)
        .add_edge(promotion, package)
        .build()
    )


def _initial_state() -> dict[str, Any]:
    return {
        "trace": [],
        "attempt": 0,
        "passed": False,
        "intent_approved": False,
        "promotion_approved": False,
        "artifact": "",
        "output": "",
    }


async def _latest_checkpoint(storage: FileCheckpointStorage) -> str:
    checkpoints = await storage.list_checkpoints(workflow_name="r2-artifact")
    assert checkpoints
    return sorted(checkpoints, key=lambda item: item.timestamp)[-1].checkpoint_id


async def _run_until_pause(
    workflow: Workflow,
    *,
    message: str | None = None,
    checkpoint_id: str | None = None,
    responses: dict[str, str] | None = None,
) -> tuple[str | None, str | None]:
    request_id: str | None = None
    output: str | None = None

    kwargs: dict[str, Any] = {"stream": True}
    if message is not None:
        kwargs["message"] = message
    if checkpoint_id is not None:
        kwargs["checkpoint_id"] = checkpoint_id
    if responses is not None:
        kwargs["responses"] = responses

    async for event in workflow.run(**kwargs):
        if event.type == "request_info":
            request_id = event.request_id
        elif event.type == "output":
            output = event.data

    return request_id, output


async def run_phase(root: Path, phase: str) -> None:
    global JOURNAL

    root.mkdir(parents=True, exist_ok=True)
    storage_root = root / "checkpoints"
    JOURNAL = root / "side-effects.log"
    pause_file = root / "pause.json"
    final_file = root / "final.json"
    receipt_file = root / "receipt.json"

    if phase == "start":
        if root.exists():
            for path in root.glob("*"):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    for child in path.glob("*"):
                        child.unlink()
                    path.rmdir()
        root.mkdir(parents=True, exist_ok=True)

    storage = FileCheckpointStorage(storage_path=storage_root)
    workflow = build_workflow(storage)

    if phase == "start":
        request_id, output = await _run_until_pause(
            workflow,
            message=_dump(_initial_state()),
        )
        assert request_id is not None
        assert output is None
        checkpoint_id = await _latest_checkpoint(storage)
        pause_file.write_text(
            json.dumps(
                {"checkpoint_id": checkpoint_id, "request_id": request_id},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return

    if phase == "resume-intent":
        pause = json.loads(pause_file.read_text())
        request_id, output = await _run_until_pause(
            workflow,
            checkpoint_id=pause["checkpoint_id"],
            responses={pause["request_id"]: "approve"},
        )
        assert request_id is not None
        assert output is None
        checkpoint_id = await _latest_checkpoint(storage)
        pause_file.write_text(
            json.dumps(
                {"checkpoint_id": checkpoint_id, "request_id": request_id},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return

    if phase == "resume-promotion":
        pause = json.loads(pause_file.read_text())
        request_id, output = await _run_until_pause(
            workflow,
            checkpoint_id=pause["checkpoint_id"],
            responses={pause["request_id"]: "approve"},
        )
        assert request_id is None
        assert output is not None
        final_file.write_text(output + "\n", encoding="utf-8")
        return

    if phase == "verify":
        state = _load(final_file.read_text())
        operations = JOURNAL.read_text().splitlines()
        expected = ["execute-0", "execute-1"]
        assert operations == expected, operations
        assert len(operations) == len(set(operations))
        assert state["intent_approved"] is True
        assert state["promotion_approved"] is True
        assert state["attempt"] == 1
        assert state["passed"] is True
        assert state["output"] == "packaged:candidate-1"

        receipt = {
            "framework": "microsoft-agent-framework-core",
            "framework_version": importlib.metadata.version("agent-framework-core"),
            "state_store": "file-checkpoint-storage",
            "fresh_controller_boundaries": 2,
            "human_gates": ["intent", "promotion"],
            "bounded_repair_attempts": state["attempt"],
            "side_effect_operations": operations,
            "duplicate_side_effects": False,
            "final_output": state["output"],
            "final_trace": state["trace"],
            "observed_result": "pass",
        }
        receipt_file.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(receipt_file.read_text(), end="")
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
    asyncio.run(run_phase(args.root, args.phase))


if __name__ == "__main__":
    main()
