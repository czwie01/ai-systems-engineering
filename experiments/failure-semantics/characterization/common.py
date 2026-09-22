# ruff: noqa: I001
from __future__ import annotations

import json
import os
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from ai_systems.experiments.failure_semantics import (
    CompletionClass,
    FailureObservation,
    classify_completion,
)


CRASH_EXIT_CODE = 86
OPERATION_ID = "external-effect-001"


class Scenario(StrEnum):
    BEFORE_EFFECT = "before-effect"
    AFTER_EFFECT_BEFORE_CHECKPOINT = "after-effect-before-checkpoint"
    AFTER_CHECKPOINT = "after-checkpoint"


class EffectMode(StrEnum):
    NAIVE = "naive"
    IDEMPOTENT = "idempotent"


@dataclass(frozen=True, slots=True)
class CrashObservation:
    framework: str
    scenario: str
    mode: str
    effect_visible: bool
    completion_recorded: bool
    completion_class: str
    framework_detail: dict[str, object]


def reset_case(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)


def initialize_sink(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL
            )
            """
        )


def record_attempt(path: Path) -> None:
    initialize_sink(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO attempts(operation_id) VALUES (?)",
            (OPERATION_ID,),
        )


def apply_effect(path: Path, mode: EffectMode) -> None:
    initialize_sink(path)
    with sqlite3.connect(path) as connection:
        if mode is EffectMode.IDEMPOTENT:
            existing = connection.execute(
                "SELECT COUNT(*) FROM effects WHERE operation_id = ?",
                (OPERATION_ID,),
            ).fetchone()
            assert existing is not None
            if int(existing[0]) > 0:
                return

        connection.execute(
            "INSERT INTO effects(operation_id) VALUES (?)",
            (OPERATION_ID,),
        )


def sink_counts(path: Path) -> tuple[int, int]:
    initialize_sink(path)
    with sqlite3.connect(path) as connection:
        attempts_row = connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE operation_id = ?",
            (OPERATION_ID,),
        ).fetchone()
        effects_row = connection.execute(
            "SELECT COUNT(*) FROM effects WHERE operation_id = ?",
            (OPERATION_ID,),
        ).fetchone()
    assert attempts_row is not None
    assert effects_row is not None
    return int(attempts_row[0]), int(effects_row[0])


def crash_once(root: Path, label: str) -> None:
    marker = root / f"crashed-{label}"
    if marker.exists():
        return
    marker.write_text("armed\n", encoding="utf-8")
    os._exit(CRASH_EXIT_CODE)


def observe_failure(
    *,
    framework: str,
    scenario: Scenario,
    mode: EffectMode,
    effect_visible: bool,
    completion_recorded: bool,
    framework_detail: dict[str, object],
) -> CrashObservation:
    classification = classify_completion(
        FailureObservation(
            source=framework,
            raw_failure=f"process-exit-{scenario.value}",
            effect_visible=effect_visible,
            completion_recorded=completion_recorded,
        )
    )
    return CrashObservation(
        framework=framework,
        scenario=scenario.value,
        mode=mode.value,
        effect_visible=effect_visible,
        completion_recorded=completion_recorded,
        completion_class=classification.value,
        framework_detail=framework_detail,
    )


def write_observation(path: Path, observation: CrashObservation) -> None:
    path.write_text(
        json.dumps(asdict(observation), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_observation(path: Path) -> CrashObservation:
    value = json.loads(path.read_text())
    return CrashObservation(**value)


def expected_class(scenario: Scenario) -> CompletionClass:
    if scenario is Scenario.BEFORE_EFFECT:
        return CompletionClass.DEFINITE_NO_EFFECT
    if scenario is Scenario.AFTER_EFFECT_BEFORE_CHECKPOINT:
        return CompletionClass.AMBIGUOUS_COMPLETION
    return CompletionClass.COMPLETION_RECORDED


def expected_counts(scenario: Scenario, mode: EffectMode) -> tuple[int, int]:
    attempts = 1 if scenario is Scenario.AFTER_CHECKPOINT else 2
    effects = 1
    if scenario is Scenario.AFTER_EFFECT_BEFORE_CHECKPOINT and mode is EffectMode.NAIVE:
        effects = 2
    return attempts, effects
