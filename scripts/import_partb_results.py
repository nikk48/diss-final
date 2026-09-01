"""Import Part B PPO evaluation artefacts into Part C result files.

Part C does not train or claim ownership of the PPO model. This script only
converts Part B summaries and telemetry into the Part C evidence schema so the
same analysis scripts can compare baseline, tuned, Optuna, and imported PPO
results fairly.
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_experiment import RUN_LOG_FIELDS, append_run_log  # noqa: E402


DEFAULT_SOURCE = Path("/Users/thenotoriouscode/Desktop/eva-optimised")
PARTB_RESULTS = ROOT / "data" / "partb_results.csv"
PARTB_DATA_DIR = ROOT / "data" / "part_b_imports"
TELEMETRY_DIR = ROOT / "data" / "telemetry_logs"
RUN_LOG = ROOT / "data" / "run_log.csv"
TOP_LEVEL_EXPERIMENT_ID = "PARTB_IMPORTED_3LAPS_NORMAL"
ARCHIVE_EXPERIMENT_ID = "PARTB_PPO_OPTIMIZED"
PARTB_FIELDS = [
    "experiment_id",
    "source",
    "agent_version",
    "policy_version",
    "state_version",
    "reward_version",
    "algorithm",
    "track",
    "run_number",
    "seed",
    "best_lap_time",
    "average_lap_time",
    "completion_rate",
    "crash_count",
    "off_track_count",
    "damage",
    "lap_time_variance",
    "runtime_per_run_seconds",
    "decision_latency_ms",
    "memory_usage",
    "telemetry_file",
    "notes",
]


def parse_lap_times(value: object) -> list[float]:
    if pd.isna(value):
        return []
    return [
        float(part.strip())
        for part in str(value).replace(",", ";").split(";")
        if part.strip()
    ]


def numeric(value: object, default: float = 0.0) -> float:
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(converted):
        return default
    return float(converted)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return path.with_name(f"{path.stem}_{stamp}{path.suffix}")


def copy_file(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and filecmp.cmp(source, destination, shallow=False):
        return destination
    destination = unique_path(destination)
    shutil.copy2(source, destination)
    return destination


def extract_zip_member(archive: zipfile.ZipFile, member: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination
    with archive.open(member) as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    return destination


def telemetry_stats(path: Path | None) -> dict[str, float]:
    if path is None or not path.exists() or path.stat().st_size == 0:
        return {
            "target_speed": 0.0,
            "crash_count": 0.0,
            "off_track_count": 0.0,
            "max_damage": 0.0,
        }

    df = pd.read_csv(path)
    stats = {
        "target_speed": 0.0,
        "crash_count": 0.0,
        "off_track_count": 0.0,
        "max_damage": 0.0,
    }
    if "target_speed" in df.columns:
        stats["target_speed"] = numeric(df["target_speed"].mean())
    elif "base_target_speed" in df.columns:
        stats["target_speed"] = numeric(df["base_target_speed"].mean())

    if "trackPos" in df.columns:
        track_pos = pd.to_numeric(df["trackPos"], errors="coerce").fillna(0.0)
        stats["off_track_count"] = float((track_pos.abs() > 1.0).sum())

    if "damage" in df.columns:
        damage = pd.to_numeric(df["damage"], errors="coerce").fillna(0.0)
        stats["max_damage"] = float(damage.max())
        stats["crash_count"] = float((damage.diff().fillna(0.0) > 0.0).sum())

    return stats


def text_value(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    if pd.isna(value):
        return ""
    return str(value).strip()


def telemetry_columns(path: Path | None) -> set[str]:
    if path is None or not path.exists() or path.stat().st_size == 0:
        return set()
    try:
        return set(pd.read_csv(path, nrows=0).columns)
    except pd.errors.EmptyDataError:
        return set()


def infer_partb_algorithm(summary_row: pd.Series, telemetry_path: Path | None) -> tuple[str, str]:
    controller = text_value(summary_row, "controller")
    checkpoint = text_value(summary_row, "checkpoint")
    telemetry_csv = text_value(summary_row, "telemetry_csv")
    self_reported_text = " ".join([controller, checkpoint, telemetry_csv]).lower()

    if "ppo" in self_reported_text:
        evidence = (
            f"Algorithm label sourced from Part B summary controller={controller!r}."
            if controller
            else "Algorithm label sourced from Part B summary checkpoint/telemetry metadata."
        )
        return "PPO-based optimised policy", evidence

    columns = telemetry_columns(telemetry_path)
    residual_columns = {"rl_target_active", "policy_inference", "residual"}
    if residual_columns.issubset(columns):
        return (
            "Part B imported residual policy",
            (
                "PPO is not self-reported in the source summary for this row; "
                "algorithm type is recorded conservatively from telemetry columns "
                "rl_target_active, policy_inference, and residual."
            ),
        )

    return (
        "Part B imported policy",
        "Algorithm type is not self-reported by the source summary or telemetry.",
    )


def build_common_values(
    *,
    experiment_id: str,
    run_number: int,
    summary_row: pd.Series,
    telemetry_path: Path | None,
    algorithm: str,
    notes: str,
) -> dict[str, Any]:
    lap_times = parse_lap_times(summary_row.get("lap_times_seconds"))
    best_lap_time = numeric(
        summary_row.get("best_lap_time"),
        min(lap_times) if lap_times else 0.0,
    )
    average_lap_time = numeric(
        summary_row.get("mean_flying_lap_time"),
        sum(lap_times) / len(lap_times) if lap_times else best_lap_time,
    )
    completed_laps = int(numeric(summary_row.get("completed_laps"), 0.0))
    lap_completed = int(numeric(summary_row.get("lap_completed"), completed_laps > 0))
    max_damage = numeric(summary_row.get("max_damage"), 0.0)
    elapsed_seconds = numeric(
        summary_row.get("elapsed_seconds"),
        sum(lap_times) if lap_times else numeric(summary_row.get("last_curLapTime")),
    )
    stats = telemetry_stats(telemetry_path)
    damage = max(max_damage, stats["max_damage"])
    crash_count = int(stats["crash_count"] or (1 if damage > 0 else 0))
    off_track_count = int(stats["off_track_count"])
    lap_variance = numeric(summary_row.get("std_flying_lap_time"), 0.0) ** 2
    controller = text_value(summary_row, "controller")

    return {
        "experiment_id": experiment_id,
        "source": "partb_imported",
        "agent_version": controller or "part_b_visual_eval_agent",
        "policy_version": "optimized_v6_student32",
        "state_version": "part_b_autoencoder_29_to_8",
        "reward_version": "part_b_longitudinal_reward_v6",
        "algorithm": algorithm,
        "track": "corkscrew",
        "run_number": run_number,
        "seed": "",
        "target_speed": round(stats["target_speed"], 3),
        "best_lap_time": round(best_lap_time, 3),
        "average_lap_time": round(average_lap_time, 3),
        "completed_lap": lap_completed,
        "completion_rate": 1.0 if completed_laps > 0 or lap_completed else 0.0,
        "crash_count": crash_count,
        "off_track_count": off_track_count,
        "damage": round(damage, 6),
        "lap_time_variance": round(lap_variance, 6),
        "training_time_seconds": 0.0,
        "runtime_per_run_seconds": round(elapsed_seconds, 4),
        "decision_latency_ms": round(
            numeric(summary_row.get("mean_policy_decision_ms"), 0.0),
            5,
        ),
        "cpu_usage": round(
            numeric(summary_row.get("process_cpu_total_seconds"), 0.0)
            / elapsed_seconds
            * 100.0,
            2,
        )
        if elapsed_seconds > 0
        else "",
        "memory_usage": round(numeric(summary_row.get("peak_rss_mb"), 0.0), 2),
        "telemetry_file": str(telemetry_path) if telemetry_path else "",
        "notes": notes,
    }


def run_log_row(common: dict[str, Any], summary_path: Path) -> dict[str, Any]:
    row = {field: "" for field in RUN_LOG_FIELDS}
    row.update(common)
    row["date_time"] = datetime.now(timezone.utc).isoformat()
    row["steer_gain"] = ""
    row["centering_gain"] = ""
    row["brake_threshold"] = ""
    row["gentle_speed"] = ""
    row["sharp_speed"] = ""
    row["straight_speed"] = ""
    row["acceleration_limit"] = ""
    row["braking_intensity"] = ""
    row["config_path"] = str(summary_path)
    return row


def partb_result_row(common: dict[str, Any]) -> dict[str, Any]:
    return {field: common.get(field, "") for field in PARTB_FIELDS}


def existing_keys(path: Path) -> set[tuple[str, str, int]]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    df = pd.read_csv(path)
    if df.empty:
        return set()
    keys = set()
    for _, row in df.iterrows():
        try:
            run_number = int(row.get("run_number", 0))
        except (TypeError, ValueError):
            run_number = 0
        keys.add((str(row.get("experiment_id")), str(row.get("algorithm")), run_number))
    return keys


def import_top_level(source: Path) -> list[tuple[dict[str, Any], Path]]:
    summary = source / "eval_laps3_normal_visual_summary.csv"
    telemetry = source / "eval_laps3_normal_telemetry.csv"
    if not summary.exists():
        return []

    imported_summary = copy_file(
        summary,
        PARTB_DATA_DIR / "eval_laps3_normal_visual_summary.csv",
    )
    imported_telemetry = (
        copy_file(telemetry, TELEMETRY_DIR / f"{TOP_LEVEL_EXPERIMENT_ID}_telemetry.csv")
        if telemetry.exists()
        else None
    )

    df = pd.read_csv(imported_summary)
    rows = []
    for index, row in df.iterrows():
        algorithm, algorithm_evidence = infer_partb_algorithm(row, imported_telemetry)
        common = build_common_values(
            experiment_id=TOP_LEVEL_EXPERIMENT_ID,
            run_number=index + 1,
            summary_row=row,
            telemetry_path=imported_telemetry,
            algorithm=algorithm,
            notes=(
                "Imported Part B visual evaluation; model developed by Part B and "
                f"evaluated within Part C framework. {algorithm_evidence}"
            ),
        )
        rows.append((common, imported_summary))
    return rows


def eval_run_number(name: str, fallback: int) -> int:
    match = re.search(r"eval(\d+)", name)
    return int(match.group(1)) if match else fallback


def import_zip_package(source: Path) -> list[tuple[dict[str, Any], Path]]:
    rows: list[tuple[dict[str, Any], Path]] = []
    zip_paths = sorted(source.glob("*.zip"))
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path) as archive:
            members = archive.namelist()
            summary_members = [
                member
                for member in members
                if member.endswith("_summary.csv")
                and "distillation_metrics" not in member
            ]
            for fallback, summary_member in enumerate(summary_members, start=1):
                summary_name = Path(summary_member).name
                summary_dest = extract_zip_member(
                    archive,
                    summary_member,
                    PARTB_DATA_DIR / summary_name,
                )

                telemetry_member = summary_member.replace("_summary.csv", "_telemetry.csv")
                telemetry_dest = None
                if telemetry_member in members:
                    telemetry_dest = extract_zip_member(
                        archive,
                        telemetry_member,
                        TELEMETRY_DIR / Path(telemetry_member).name,
                    )

                df = pd.read_csv(summary_dest)
                for _, row in df.iterrows():
                    algorithm, algorithm_evidence = infer_partb_algorithm(
                        row,
                        telemetry_dest,
                    )
                    common = build_common_values(
                        experiment_id=ARCHIVE_EXPERIMENT_ID,
                        run_number=eval_run_number(summary_name, fallback),
                        summary_row=row,
                        telemetry_path=telemetry_dest,
                        algorithm=algorithm,
                        notes=(
                            "Imported Part B PPO evaluation from archive; model "
                            "developed by Part B and evaluated within Part C framework. "
                            f"{algorithm_evidence}"
                        ),
                    )
                    rows.append((common, summary_dest))
    return rows


def write_partb_results(rows: list[dict[str, Any]]) -> None:
    PARTB_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=PARTB_FIELDS).to_csv(PARTB_RESULTS, index=False)


def write_import_manifest(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=RUN_LOG_FIELDS).to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Append rows even if experiment_id/algorithm/run_number already exists.",
    )
    parser.add_argument(
        "--append-run-log",
        action="store_true",
        help="Also append imported Part B rows to data/run_log.csv.",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Part B source folder does not exist: {source}")

    imported = import_top_level(source) + import_zip_package(source)
    if not imported:
        raise SystemExit(f"No Part B summary files found in {source}")

    partb_rows = [partb_result_row(common) for common, _ in imported]
    run_log_rows = [run_log_row(common, summary_path) for common, summary_path in imported]
    write_partb_results(partb_rows)
    write_import_manifest(run_log_rows, PARTB_DATA_DIR / "part_b_import_manifest.csv")

    appended = 0
    skipped = 0
    if args.append_run_log:
        seen = existing_keys(RUN_LOG)
        for row in run_log_rows:
            key = (row["experiment_id"], row["algorithm"], int(row["run_number"]))
            if key in seen and not args.allow_duplicates:
                skipped += 1
                continue
            append_run_log(row, RUN_LOG)
            seen.add(key)
            appended += 1

    print(f"Imported source: {source}")
    print(f"Rows discovered: {len(imported)}")
    print(f"Rows written to partb_results.csv: {len(partb_rows)}")
    print(f"Rows appended to run_log.csv: {appended}")
    print(f"Duplicate rows skipped: {skipped}")
    print(f"Part B results: {PARTB_RESULTS}")
    print(f"Import manifest: {PARTB_DATA_DIR / 'part_b_import_manifest.csv'}")


if __name__ == "__main__":
    main()
