"""Shared helpers for result source labels and telemetry file names."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


DUMMY_SOURCES = {
    "dummy",
    "grid_dummy",
    "optuna_dummy",
    "optuna_dummy_replay",
    "stress_dummy",
}
LIVE_SOURCES = {
    "live",
    "grid_live",
    "optuna_live",
    "optuna_live_replay",
    "stress_live",
}
PARTB_SOURCES = {"partb_imported", "imported_partb"}
VALID_SOURCES = DUMMY_SOURCES | LIVE_SOURCES | PARTB_SOURCES


def clean_token(value: object) -> str:
    token = str(value).strip()
    token = re.sub(r"[^A-Za-z0-9_.-]+", "_", token)
    return token.strip("_") or "unknown"


def infer_source(row: Mapping[str, object]) -> str:
    """Infer a controlled source label for old rows that lack one."""

    explicit = str(row.get("source", "") or "").strip()
    algorithm = str(row.get("algorithm", "") or "").lower()
    notes = str(row.get("notes", "") or "").lower()
    experiment_id = str(row.get("experiment_id", "") or "").lower()

    if explicit in VALID_SOURCES:
        return explicit

    if "part_b" in algorithm or "part b" in notes or "partb" in experiment_id:
        return "partb_imported"

    if "dummy" in notes or "replace simulator with live torcs later" in notes:
        if "grid" in experiment_id or "grid" in algorithm:
            return "grid_dummy"
        if "optuna" in algorithm or "optuna" in experiment_id:
            return "optuna_dummy"
        return "dummy"

    if "torcs_live" in algorithm or notes.startswith("live torcs run"):
        if "grid" in experiment_id or "grid" in algorithm:
            return "grid_live"
        if "optuna" in algorithm or "optuna" in experiment_id:
            return "optuna_live"
        return "live"
    if "grid" in algorithm or experiment_id.startswith("grid_"):
        return "grid_dummy"
    if "optuna" in algorithm or experiment_id.startswith("optuna_"):
        return "optuna_dummy"
    return "dummy"


def source_for_run(algorithm: object, live: bool) -> str:
    algorithm_name = str(algorithm or "").lower()
    if "replay" in algorithm_name and "optuna" in algorithm_name:
        return "optuna_live_replay" if live else "optuna_dummy_replay"
    if "stress" in algorithm_name:
        return "stress_live" if live else "stress_dummy"
    if "grid" in algorithm_name:
        return "grid_live" if live else "grid_dummy"
    if "optuna" in algorithm_name:
        return "optuna_live" if live else "optuna_dummy"
    return "live" if live else "dummy"


def timestamp_label(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.strftime("%Y%m%d_%H%M%S_%f")


def telemetry_path(
    root: Path,
    experiment_id: object,
    source: object,
    run_number: object,
    now: datetime | None = None,
) -> Path:
    """Create a telemetry path that will not overwrite an earlier run."""

    telemetry_dir = root / "data" / "telemetry_logs"
    base_name = (
        f"{clean_token(experiment_id)}_"
        f"{clean_token(source)}_"
        f"run_{clean_token(run_number)}_"
        f"{timestamp_label(now)}"
    )
    path = telemetry_dir / f"{base_name}.csv"
    suffix = 1
    while path.exists():
        path = telemetry_dir / f"{base_name}_{suffix}.csv"
        suffix += 1
    return path
