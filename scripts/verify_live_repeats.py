"""Verify whether live repeat rows are backed by distinct telemetry files."""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN_LOG = ROOT / "data" / "run_log.csv"
RESULTS_DIR = ROOT / "results"
LIVE_FILE_OUTPUT = RESULTS_DIR / "live_repeat_telemetry_files.csv"
LIVE_SUMMARY_OUTPUT = RESULTS_DIR / "live_repeat_verification_summary.csv"
LIVE_MARKDOWN_OUTPUT = RESULTS_DIR / "live_repeat_verification.md"
LIVE_SOURCES = {
    "live",
    "grid_live",
    "optuna_live",
    "optuna_live_replay",
    "stress_live",
}


def resolve_path(raw_path: object) -> Path | None:
    if pd.isna(raw_path) or not str(raw_path).strip():
        return None

    path = Path(str(raw_path)).expanduser()
    if path.exists():
        return path

    fallback = ROOT / "data" / "telemetry_logs" / path.name
    if fallback.exists():
        return fallback
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def number(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def completed(row: pd.Series) -> bool:
    return number(row.get("completed_lap")) == 1.0 or number(row.get("completion_rate")) > 0.0


def live_rows(run_log: pd.DataFrame) -> pd.DataFrame:
    run_log["source"] = run_log["source"].fillna("").astype(str)
    run_log["best_lap_time"] = pd.to_numeric(run_log["best_lap_time"], errors="coerce")
    mask = (
        run_log["source"].isin(LIVE_SOURCES)
        & (run_log["best_lap_time"].fillna(0.0) > 0.0)
        & run_log.apply(completed, axis=1)
    )
    return run_log[mask].copy()


def telemetry_profile(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "telemetry_exists": False,
            "file_size_bytes": "",
            "file_mtime": "",
            "sha256": "",
            "telemetry_rows": "",
            "first_timestamp": "",
            "last_timestamp": "",
            "first_lap_time": "",
            "last_lap_time": "",
            "max_lap_time": "",
            "max_speed": "",
        }
    if not path.exists():
        return {
            "telemetry_exists": False,
            "file_size_bytes": "",
            "file_mtime": "",
            "sha256": "",
            "telemetry_rows": "",
            "first_timestamp": "",
            "last_timestamp": "",
            "first_lap_time": "",
            "last_lap_time": "",
            "max_lap_time": "",
            "max_speed": "",
        }

    stat = path.stat()
    profile: dict[str, Any] = {
        "telemetry_exists": True,
        "file_size_bytes": stat.st_size,
        "file_mtime": pd.Timestamp.fromtimestamp(stat.st_mtime).isoformat(),
        "sha256": sha256_file(path),
    }

    telemetry = pd.read_csv(path)
    profile["telemetry_rows"] = len(telemetry)
    profile["first_timestamp"] = (
        str(telemetry["timestamp"].dropna().iloc[0])
        if "timestamp" in telemetry.columns and not telemetry["timestamp"].dropna().empty
        else ""
    )
    profile["last_timestamp"] = (
        str(telemetry["timestamp"].dropna().iloc[-1])
        if "timestamp" in telemetry.columns and not telemetry["timestamp"].dropna().empty
        else ""
    )

    for column in ["lap_time", "speed"]:
        if column in telemetry.columns:
            telemetry[column] = pd.to_numeric(telemetry[column], errors="coerce")

    lap_times = telemetry["lap_time"].dropna() if "lap_time" in telemetry.columns else pd.Series(dtype=float)
    speeds = telemetry["speed"].dropna() if "speed" in telemetry.columns else pd.Series(dtype=float)
    profile["first_lap_time"] = float(lap_times.iloc[0]) if not lap_times.empty else ""
    profile["last_lap_time"] = float(lap_times.iloc[-1]) if not lap_times.empty else ""
    profile["max_lap_time"] = float(lap_times.max()) if not lap_times.empty else ""
    profile["max_speed"] = float(speeds.max()) if not speeds.empty else ""
    return profile


def build_file_rows(rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for _, row in rows.iterrows():
        path = resolve_path(row.get("telemetry_file"))
        profile = telemetry_profile(path)
        records.append(
            {
                "experiment_id": row.get("experiment_id", ""),
                "source": row.get("source", ""),
                "algorithm": row.get("algorithm", ""),
                "run_number": row.get("run_number", ""),
                "date_time": row.get("date_time", ""),
                "best_lap_time": row.get("best_lap_time", ""),
                "runtime_per_run_seconds": row.get("runtime_per_run_seconds", ""),
                "telemetry_file": str(path) if path else "",
                **profile,
            }
        )
    return pd.DataFrame(records)


def verdict_for(group: pd.DataFrame) -> str:
    expected = len(group)
    existing = int(group["telemetry_exists"].sum())
    unique_paths = group.loc[group["telemetry_exists"], "telemetry_file"].nunique()
    unique_hashes = group.loc[group["telemetry_exists"], "sha256"].nunique()
    unique_first_timestamps = group.loc[group["telemetry_exists"], "first_timestamp"].nunique()

    if existing < expected:
        return "not verified: one or more telemetry files are missing"
    if unique_paths < expected:
        return "not verified: repeated run rows point to the same telemetry path"
    if unique_hashes < expected:
        return "not verified: at least two telemetry files have identical content hashes"
    if unique_first_timestamps < expected:
        return "partially verified: files differ but internal start timestamps repeat"
    return "verified: distinct telemetry files with unique content hashes and timestamps"


def build_summary(file_rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for keys, group in file_rows.groupby(
        ["experiment_id", "source", "algorithm"],
        dropna=False,
    ):
        experiment_id, source, algorithm = keys
        lap_times = pd.to_numeric(group["best_lap_time"], errors="coerce").dropna()
        row_counts = pd.to_numeric(group["telemetry_rows"], errors="coerce").dropna()
        records.append(
            {
                "experiment_id": experiment_id,
                "source": source,
                "algorithm": algorithm,
                "run_rows": len(group),
                "telemetry_files_found": int(group["telemetry_exists"].sum()),
                "unique_telemetry_paths": group.loc[
                    group["telemetry_exists"], "telemetry_file"
                ].nunique(),
                "unique_sha256_hashes": group.loc[group["telemetry_exists"], "sha256"].nunique(),
                "unique_first_timestamps": group.loc[
                    group["telemetry_exists"], "first_timestamp"
                ].nunique(),
                "unique_last_timestamps": group.loc[
                    group["telemetry_exists"], "last_timestamp"
                ].nunique(),
                "mean_best_lap_time": lap_times.mean() if not lap_times.empty else "",
                "std_best_lap_time": lap_times.std(ddof=0) if len(lap_times) > 1 else 0.0,
                "min_telemetry_rows": int(row_counts.min()) if not row_counts.empty else "",
                "max_telemetry_rows": int(row_counts.max()) if not row_counts.empty else "",
                "verdict": verdict_for(group),
            }
        )
    return pd.DataFrame(records).sort_values(["source", "experiment_id", "algorithm"])


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[column]).replace("|", "\\|") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_markdown(summary: pd.DataFrame, file_rows: pd.DataFrame) -> None:
    repeated = summary[summary["run_rows"] >= 2].copy()
    content = [
        "# Live Repeat Telemetry Verification",
        "",
        f"Run log: `{RUN_LOG}`",
        "",
        "This check verifies whether live repeat rows are backed by distinct telemetry files. It checks file existence, unique paths, SHA-256 content hashes, internal telemetry timestamps, row counts, and lap-time values.",
        "",
        "## Group Verdicts",
        "",
        markdown_table(repeated),
        "",
        "## File-Level Evidence",
        "",
        markdown_table(
            file_rows[
                [
                    "experiment_id",
                    "source",
                    "run_number",
                    "date_time",
                    "best_lap_time",
                    "file_size_bytes",
                    "telemetry_rows",
                    "first_timestamp",
                    "last_timestamp",
                    "sha256",
                ]
            ]
        ),
        "",
    ]
    LIVE_MARKDOWN_OUTPUT.write_text("\n".join(content))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(RUN_LOG))
    args = parser.parse_args()

    run_log_path = Path(args.input).expanduser()
    if not run_log_path.is_absolute():
        run_log_path = (ROOT / run_log_path).resolve()
    if not run_log_path.exists():
        raise SystemExit(f"Run log not found: {run_log_path}")

    run_log = pd.read_csv(run_log_path)
    rows = live_rows(run_log)
    if rows.empty:
        raise SystemExit("No completed positive-lap live rows found to verify.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    file_rows = build_file_rows(rows)
    summary = build_summary(file_rows)
    file_rows.to_csv(LIVE_FILE_OUTPUT, index=False)
    summary.to_csv(LIVE_SUMMARY_OUTPUT, index=False)
    write_markdown(summary, file_rows)

    repeated = summary[summary["run_rows"] >= 2]
    print(f"Verified {len(file_rows)} completed positive-lap live row(s).")
    print(f"Repeated live groups: {len(repeated)}")
    print(f"File-level output: {LIVE_FILE_OUTPUT}")
    print(f"Summary output: {LIVE_SUMMARY_OUTPUT}")
    print(f"Markdown output: {LIVE_MARKDOWN_OUTPUT}")
    print("\nRepeated-group verdicts:")
    for _, row in repeated.iterrows():
        print(
            f"- {row['experiment_id']} ({row['source']}): {row['verdict']} "
            f"[rows={row['run_rows']}, unique_hashes={row['unique_sha256_hashes']}]"
        )


if __name__ == "__main__":
    main()
