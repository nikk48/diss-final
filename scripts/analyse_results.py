"""Analyse Part C dummy, live, and imported Part B TORCS evidence."""

from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "part_c_matplotlib"),
)
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "part_c_cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.result_utils import (  # noqa: E402
    DUMMY_SOURCES,
    LIVE_SOURCES,
    PARTB_SOURCES,
    infer_source,
)


RUN_LOG = ROOT / "data" / "run_log.csv"
PARTB_RESULTS = ROOT / "data" / "partb_results.csv"
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"
LEGACY_COLUMN_NAMES = {
    "corner_speed": "gentle_speed",
    "braking_threshold": "brake_threshold",
    "steering_gain": "steer_gain",
    "max_damage": "damage",
}
NUMERIC_COLUMNS = [
    "best_lap_time",
    "average_lap_time",
    "completed_lap",
    "completion_rate",
    "crash_count",
    "off_track_count",
    "damage",
    "lap_time_variance",
    "runtime_per_run_seconds",
    "decision_latency_ms",
    "cpu_usage",
    "memory_usage",
]
MODE_SOURCES = {
    "dummy": DUMMY_SOURCES,
    "live": LIVE_SOURCES,
    "partb": PARTB_SOURCES,
    "stress": {"stress_dummy", "stress_live"},
}
SCORED_OUTPUTS = {
    "dummy": "dummy_scored_experiments.csv",
    "live": "live_scored_experiments.csv",
    "partb": "partb_scored_experiments.csv",
    "stress": "stress_scored_experiments.csv",
    "all": "combined_scored_experiments.csv",
}
SUMMARY_OUTPUTS = {
    "dummy": "summary_dummy.csv",
    "live": "summary_live.csv",
    "partb": "summary_partb.csv",
    "stress": "summary_stress.csv",
    "all": "summary_all.csv",
}
SOURCE_COLORS = {
    "dummy": "#6B7280",
    "grid_dummy": "#9CA3AF",
    "optuna_dummy": "#4B5563",
    "optuna_dummy_replay": "#52525B",
    "stress_dummy": "#7C3AED",
    "live": "#2563EB",
    "grid_live": "#0F766E",
    "optuna_live": "#B45309",
    "optuna_live_replay": "#EA580C",
    "stress_live": "#DC2626",
    "partb_imported": "#BE185D",
}


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def min_max(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").fillna(0.0)
    span = series.max() - series.min()
    if span == 0:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - series.min()) / span


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    standardised = df.rename(columns=LEGACY_COLUMN_NAMES).copy()

    if "best_lap_time" not in standardised.columns and "average_lap_time" in standardised.columns:
        standardised["best_lap_time"] = standardised["average_lap_time"]
    if "average_lap_time" not in standardised.columns and "best_lap_time" in standardised.columns:
        standardised["average_lap_time"] = standardised["best_lap_time"]

    for column in NUMERIC_COLUMNS:
        if column not in standardised.columns:
            standardised[column] = 0.0
        standardised[column] = pd.to_numeric(standardised[column], errors="coerce")

    for column in [
        "experiment_id",
        "source",
        "algorithm",
        "track",
        "notes",
        "base_experiment_id",
        "stress_type",
        "stress_parameter",
        "stress_value",
        "agent_version",
        "state_version",
        "policy_version",
        "reward_version",
        "telemetry_file",
    ]:
        if column not in standardised.columns:
            standardised[column] = ""

    standardised["source"] = standardised.apply(infer_source, axis=1)
    standardised["algorithm"] = standardised["algorithm"].replace("", "unknown")
    standardised["track"] = standardised["track"].replace("", "unknown")
    return standardised


def read_results(path: Path, *, required: bool) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        if required:
            raise SystemExit(f"Required input file is missing or empty: {path}")
        return pd.DataFrame()
    return standardise_columns(pd.read_csv(path))


def valid_lap_mask(df: pd.DataFrame) -> pd.Series:
    return df["best_lap_time"].fillna(0.0) > 0.0


def completed_lap_mask(df: pd.DataFrame) -> pd.Series:
    return valid_lap_mask(df) & (
        (df["completed_lap"].fillna(0.0) == 1.0)
        | (df["completion_rate"].fillna(0.0) > 0.0)
    )


def dummy_mode_mask(df: pd.DataFrame) -> pd.Series:
    return df["source"].astype(str).str.lower().str.contains("dummy", na=False)


def live_mode_mask(df: pd.DataFrame) -> pd.Series:
    return df["source"].astype(str).str.lower().str.contains("live", na=False)


def partb_mode_mask(df: pd.DataFrame) -> pd.Series:
    source = df["source"].astype(str).str.lower()
    return (
        source.str.contains("partb", na=False)
        | source.str.contains("part_b", na=False)
        | source.str.contains("imported_partb", na=False)
    )


def stress_mode_mask(df: pd.DataFrame) -> pd.Series:
    return df["source"].astype(str).str.lower().isin({"stress_live", "stress_dummy"})


def mode_row_mask(df: pd.DataFrame, mode: str) -> pd.Series:
    if mode == "dummy":
        return dummy_mode_mask(df)
    if mode == "live":
        return live_mode_mask(df)
    if mode == "partb":
        return partb_mode_mask(df)
    if mode == "stress":
        return stress_mode_mask(df)
    if mode == "all":
        return pd.Series([True] * len(df), index=df.index)
    raise ValueError(f"Unsupported mode: {mode}")


def select_mode_rows(
    mode: str,
    run_log_path: Path,
    partb_path: Path,
) -> tuple[pd.DataFrame, list[Path]]:
    inputs: list[Path] = []

    if mode == "partb":
        partb = read_results(partb_path, required=True)
        inputs.append(partb_path)
        return partb[partb["source"].isin(PARTB_SOURCES)].copy(), inputs

    run_log = read_results(run_log_path, required=True)
    inputs.append(run_log_path)

    if mode in MODE_SOURCES:
        return run_log[mode_row_mask(run_log, mode)].copy(), inputs

    part_c_rows = run_log[~run_log["source"].isin(PARTB_SOURCES)].copy()
    partb = read_results(partb_path, required=False)
    if not partb.empty:
        inputs.append(partb_path)
        partb = partb[partb["source"].isin(PARTB_SOURCES)].copy()
    return pd.concat([part_c_rows, partb], ignore_index=True), inputs


def aggregate_experiments(df: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        column
        for column in [
            "source",
            "experiment_id",
            "algorithm",
            "track",
            "target_speed",
            "gentle_speed",
            "brake_threshold",
            "steer_gain",
        ]
        if column in df.columns
    ]

    if "experiment_id" not in group_columns:
        return df.copy()

    return (
        df.groupby(group_columns, dropna=False, as_index=False)
        .agg(
            best_lap_time=("best_lap_time", "min"),
            average_lap_time=("average_lap_time", "mean"),
            completion_rate=("completion_rate", "mean"),
            crash_count=("crash_count", "mean"),
            off_track_count=("off_track_count", "mean"),
            damage=("damage", "max"),
            lap_time_variance=("lap_time_variance", "mean"),
            runtime_per_run_seconds=("runtime_per_run_seconds", "mean"),
            decision_latency_ms=("decision_latency_ms", "mean"),
            cpu_usage=("cpu_usage", "mean"),
            memory_usage=("memory_usage", "mean"),
        )
        .copy()
    )


def add_balanced_score(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()
    scored["lap_time_score"] = min_max(scored["average_lap_time"])
    scored["crash_score"] = min_max(scored["crash_count"])
    scored["off_track_score"] = min_max(scored["off_track_count"])
    scored["damage_score"] = min_max(scored["damage"])
    scored["runtime_score"] = min_max(scored["runtime_per_run_seconds"])
    scored["completion_penalty"] = 1.0 - scored["completion_rate"].fillna(0.0)

    scored["balanced_score"] = (
        scored["lap_time_score"] * 0.40
        + scored["completion_penalty"] * 0.25
        + scored["crash_score"] * 0.12
        + scored["off_track_score"] * 0.08
        + scored["damage_score"] * 0.05
        + scored["runtime_score"] * 0.10
    )
    return scored.sort_values("balanced_score", ascending=True)


def first_row(scored: pd.DataFrame, sort_by: list[str], ascending: list[bool]) -> pd.Series:
    return scored.sort_values(sort_by, ascending=ascending).iloc[0]


def summary_record(category: str, row: pd.Series) -> dict[str, object]:
    return {
        "category": category,
        "source": row.get("source", ""),
        "experiment_id": row.get("experiment_id", ""),
        "algorithm": row.get("algorithm", ""),
        "best_lap_time": row.get("best_lap_time", ""),
        "average_lap_time": row.get("average_lap_time", ""),
        "completion_rate": row.get("completion_rate", ""),
        "balanced_score": row.get("balanced_score", ""),
    }


def save_selection_summary(scored: pd.DataFrame, mode: str) -> pd.DataFrame:
    rows = [
        summary_record(
            "best_lap_time",
            first_row(scored, ["best_lap_time"], [True]),
        ),
        summary_record(
            "safest",
            first_row(
                scored,
                ["crash_count", "off_track_count", "damage", "completion_rate"],
                [True, True, True, False],
            ),
        ),
        summary_record(
            "most_efficient",
            first_row(scored, ["runtime_per_run_seconds"], [True]),
        ),
        summary_record("balanced_best", scored.iloc[0]),
    ]
    summary = pd.DataFrame(rows)
    summary.to_csv(RESULTS_DIR / SUMMARY_OUTPUTS[mode], index=False)
    summary.to_csv(RESULTS_DIR / "summary.csv", index=False)
    return summary


def method_label(values: Iterable[object]) -> str:
    labels: list[str] = []
    for value in values:
        label = str(value or "").strip()
        if label and label not in labels:
            labels.append(label)
    return "; ".join(labels[:3]) or "unknown"


def dissertation_summary_columns() -> list[str]:
    return [
        "experiment_id",
        "source",
        "method",
        "valid_runs",
        "completed_runs",
        "completion_rate",
        "best_lap_time",
        "mean_lap_time",
        "std_lap_time",
        "lap_time_variance",
        "crash_count",
        "off_track_count",
        "mean_runtime_per_run_seconds",
        "mean_decision_latency_ms",
        "mean_cpu_usage",
        "mean_memory_usage",
        "improvement_vs_baseline_seconds",
        "improvement_vs_baseline_percent",
        "rank_by_mean_lap",
        "rank_by_balanced_score",
    ]


def load_combined_results(run_log_path: Path, partb_path: Path) -> tuple[pd.DataFrame, list[Path]]:
    run_log = read_results(run_log_path, required=True)
    inputs = [run_log_path]
    partb = read_results(partb_path, required=False)
    if not partb.empty:
        inputs.append(partb_path)
        return pd.concat([run_log, partb], ignore_index=True), inputs
    return run_log, inputs


def add_dissertation_ranks(summary: pd.DataFrame, baseline_id: str) -> pd.DataFrame:
    if summary.empty:
        return summary

    ranked = summary.copy()
    mean_lap = pd.to_numeric(ranked["mean_lap_time"], errors="coerce")
    lap_time_score = pd.Series([1.0] * len(ranked), index=ranked.index)
    lap_mask = mean_lap.notna()
    if lap_mask.any():
        lap_time_score.loc[lap_mask] = min_max(mean_lap.loc[lap_mask])
    ranked["lap_time_score"] = lap_time_score
    ranked["completion_penalty"] = 1.0 - ranked["completion_rate"].fillna(0.0)
    ranked["crash_score"] = min_max(ranked["crash_count"])
    ranked["off_track_score"] = min_max(ranked["off_track_count"])
    ranked["runtime_score"] = min_max(ranked["mean_runtime_per_run_seconds"])
    ranked["balanced_score"] = (
        ranked["lap_time_score"] * 0.40
        + ranked["completion_penalty"] * 0.25
        + ranked["crash_score"] * 0.12
        + ranked["off_track_score"] * 0.08
        + ranked["runtime_score"] * 0.10
    )

    baseline_rows = ranked[ranked["experiment_id"] == baseline_id].copy()
    baseline_mean = (
        float(baseline_rows.dropna(subset=["mean_lap_time"]).sort_values("mean_lap_time").iloc[0]["mean_lap_time"])
        if not baseline_rows.empty
        and not baseline_rows.dropna(subset=["mean_lap_time"]).empty
        else float("nan")
    )
    ranked["improvement_vs_baseline_seconds"] = (
        baseline_mean - pd.to_numeric(ranked["mean_lap_time"], errors="coerce")
    )
    ranked["improvement_vs_baseline_percent"] = (
        ranked["improvement_vs_baseline_seconds"] / baseline_mean * 100.0
        if baseline_mean and not math.isnan(baseline_mean)
        else float("nan")
    )
    ranked["rank_by_mean_lap"] = (
        ranked["mean_lap_time"].rank(method="min", ascending=True).astype("Int64")
    )
    ranked["rank_by_balanced_score"] = (
        ranked["balanced_score"].rank(method="min", ascending=True).astype("Int64")
    )
    return ranked.sort_values(
        ["rank_by_balanced_score", "rank_by_mean_lap", "experiment_id"],
        na_position="last",
    )


def create_dissertation_summary(
    df: pd.DataFrame,
    mode: str,
    baseline_id: str,
    include_invalid: bool,
) -> pd.DataFrame:
    selected = df[mode_row_mask(df, mode)].copy()
    if not include_invalid:
        selected = selected[valid_lap_mask(selected)].copy()
    if selected.empty:
        return pd.DataFrame(columns=dissertation_summary_columns())

    rows: list[dict[str, object]] = []
    for keys, group in selected.groupby(["experiment_id", "source"], dropna=False):
        experiment_id, source = keys
        completed = group[completed_lap_mask(group)].copy()
        lap_group = completed.copy()
        lap_times = lap_group["average_lap_time"].dropna()
        best_times = lap_group["best_lap_time"].dropna()
        variance = lap_times.var(ddof=0) if len(lap_times) > 1 else 0.0
        rows.append(
            {
                "experiment_id": experiment_id,
                "source": source,
                "method": method_label(group["algorithm"]),
                "valid_runs": int(valid_lap_mask(group).sum()),
                "completed_runs": int(len(completed)),
                "completion_rate": float(group["completion_rate"].mean()),
                "best_lap_time": float(best_times.min()) if not best_times.empty else float("nan"),
                "mean_lap_time": float(lap_times.mean()) if not lap_times.empty else float("nan"),
                "std_lap_time": math.sqrt(max(float(variance), 0.0)),
                "lap_time_variance": float(variance),
                "crash_count": float(group["crash_count"].sum()),
                "off_track_count": float(group["off_track_count"].sum()),
                "mean_runtime_per_run_seconds": float(
                    group["runtime_per_run_seconds"].mean()
                ),
                "mean_decision_latency_ms": float(group["decision_latency_ms"].mean()),
                "mean_cpu_usage": float(group["cpu_usage"].mean()),
                "mean_memory_usage": float(group["memory_usage"].mean()),
            }
        )

    summary = pd.DataFrame(rows)
    ranked = add_dissertation_ranks(summary, baseline_id)
    return ranked[dissertation_summary_columns()]


def write_dissertation_summaries(
    df: pd.DataFrame,
    baseline_id: str,
    include_invalid: bool,
) -> dict[str, pd.DataFrame]:
    summaries: dict[str, pd.DataFrame] = {}
    for mode in ["dummy", "live", "partb", "stress"]:
        summary = create_dissertation_summary(df, mode, baseline_id, include_invalid)
        summary.to_csv(RESULTS_DIR / SUMMARY_OUTPUTS[mode], index=False)
        summaries[mode] = summary

    comparison = pd.concat(
        [
            summary.assign(evidence_mode=mode)
            for mode, summary in summaries.items()
            if not summary.empty
        ],
        ignore_index=True,
    ) if any(not summary.empty for summary in summaries.values()) else pd.DataFrame()
    if not comparison.empty:
        comparison = comparison[
            ["evidence_mode", *dissertation_summary_columns()]
        ].sort_values(["evidence_mode", "rank_by_balanced_score", "rank_by_mean_lap"])
    comparison.to_csv(RESULTS_DIR / "comparison_summary.csv", index=False)

    summaries["all"] = comparison
    live_key_results = summaries["live"].copy()
    live_key_results.to_csv(RESULTS_DIR / "dissertation_key_results.csv", index=False)
    return summaries


def grouped_notes(values: Iterable[object]) -> str:
    notes = []
    for value in values:
        note = str(value or "").strip()
        if note and note not in notes:
            notes.append(note)
    return " | ".join(notes[:3])


def create_robustness_summary(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    group_columns = ["source", "experiment_id", "algorithm", "track"]
    for keys, group in raw.groupby(group_columns, dropna=False):
        source, experiment_id, algorithm, track = keys
        valid = group[completed_lap_mask(group)].copy()
        lap_times = valid["average_lap_time"].dropna()
        best_times = valid["best_lap_time"].dropna()
        direct_std = lap_times.std(ddof=0) if len(lap_times) > 1 else 0.0
        stored_variance = group["lap_time_variance"].dropna()
        stored_std = (
            math.sqrt(max(float(stored_variance.mean()), 0.0))
            if not stored_variance.empty
            else 0.0
        )
        rows.append(
            {
                "source": source,
                "experiment_id": experiment_id,
                "algorithm": algorithm,
                "track": track,
                "number_of_rows": len(group),
                "valid_runs": len(valid),
                "completion_rate": group["completion_rate"].mean(),
                "best_lap_time": best_times.min() if not best_times.empty else "",
                "mean_lap_time": lap_times.mean() if not lap_times.empty else "",
                "std_lap_time": direct_std if direct_std > 0 else stored_std,
                "lap_time_range": (
                    lap_times.max() - lap_times.min() if len(lap_times) > 1 else 0.0
                ),
                "total_crashes": group["crash_count"].sum(),
                "total_off_track_events": group["off_track_count"].sum(),
                "max_damage": group["damage"].max(),
                "notes": grouped_notes(group["notes"]),
            }
        )

    robustness = pd.DataFrame(rows)
    if not robustness.empty:
        robustness = robustness.sort_values(
            ["source", "best_lap_time", "experiment_id"],
            na_position="last",
        )
    robustness.to_csv(RESULTS_DIR / "robustness_summary.csv", index=False)
    return robustness


def create_efficiency_summary(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    group_columns = ["source", "experiment_id", "algorithm"]
    for keys, group in raw.groupby(group_columns, dropna=False):
        source, experiment_id, algorithm = keys
        valid = group[completed_lap_mask(group)].copy()
        best_lap_time = valid["best_lap_time"].min() if not valid.empty else 0.0
        metric_group = valid if not valid.empty else group
        mean_runtime = metric_group["runtime_per_run_seconds"].mean()
        performance_per_runtime = (
            (1.0 / best_lap_time) / mean_runtime
            if best_lap_time > 0 and mean_runtime > 0
            else 0.0
        )
        rows.append(
            {
                "source": source,
                "experiment_id": experiment_id,
                "algorithm": algorithm,
                "number_of_trials_or_runs": len(group),
                "mean_runtime_per_run_seconds": mean_runtime,
                "mean_decision_latency_ms": metric_group["decision_latency_ms"].mean(),
                "median_decision_latency_ms": metric_group["decision_latency_ms"].median(),
                "mean_cpu_usage": metric_group["cpu_usage"].mean(),
                "mean_memory_usage": metric_group["memory_usage"].mean(),
                "valid_run_percentage": len(valid) / len(group) * 100.0,
                "best_lap_time": best_lap_time if best_lap_time > 0 else "",
                "performance_per_runtime": performance_per_runtime,
            }
        )

    efficiency = pd.DataFrame(rows)
    if not efficiency.empty:
        efficiency = efficiency.sort_values(
            ["source", "best_lap_time", "experiment_id"],
            na_position="last",
        )
    efficiency.to_csv(RESULTS_DIR / "computational_efficiency_summary.csv", index=False)
    return efficiency


def interpretation_for(source: str, algorithm: str) -> str:
    if source == "partb_imported":
        return (
            "Imported Part B PPO policy artefact; Part C evaluates it using the "
            "same comparison metrics."
        )
    if source == "live":
        return "Live TORCS baseline/control evidence."
    if source == "grid_live":
        return "Live TORCS grid-search configuration evidence."
    if source == "optuna_live":
        return "Live TORCS Optuna-tuned configuration evidence."
    if source == "optuna_live_replay":
        return "Live TORCS repeated replay evidence for the best Optuna configuration."
    if source == "stress_live":
        return "Live TORCS robustness stress-test evidence."
    if source == "stress_dummy":
        return "Dummy robustness stress-test pipeline validation."
    if source == "grid_dummy":
        return "Dummy grid-search pipeline validation; not final live evidence."
    if source == "optuna_dummy":
        return "Dummy Optuna validation; not final live evidence."
    if source == "optuna_dummy_replay":
        return "Dummy replay validation for the best Optuna configuration."
    if "random" in str(algorithm).lower():
        return "Dummy random-search pipeline validation."
    return "Dummy baseline pipeline validation; not final live evidence."


def create_comparison_summary(
    scored: pd.DataFrame,
    robustness: pd.DataFrame,
    efficiency: pd.DataFrame,
) -> pd.DataFrame:
    robust_lookup = robustness.set_index(["source", "experiment_id", "algorithm", "track"])
    efficiency_lookup = efficiency.set_index(["source", "experiment_id", "algorithm"])
    rows: list[dict[str, object]] = []
    for _, row in scored.sort_values("balanced_score").iterrows():
        robust_key = (
            row["source"],
            row["experiment_id"],
            row["algorithm"],
            row["track"],
        )
        efficiency_key = (row["source"], row["experiment_id"], row["algorithm"])
        robust = robust_lookup.loc[robust_key] if robust_key in robust_lookup.index else {}
        efficient = (
            efficiency_lookup.loc[efficiency_key]
            if efficiency_key in efficiency_lookup.index
            else {}
        )
        std_lap = robust.get("std_lap_time", "") if hasattr(robust, "get") else ""
        mean_runtime = (
            efficient.get("mean_runtime_per_run_seconds", "")
            if hasattr(efficient, "get")
            else ""
        )
        mean_latency = (
            efficient.get("mean_decision_latency_ms", "")
            if hasattr(efficient, "get")
            else ""
        )
        rows.append(
            {
                "Configuration": row["experiment_id"],
                "Source": row["source"],
                "Algorithm": row["algorithm"],
                "Best lap time": row["best_lap_time"],
                "Average lap time": row["average_lap_time"],
                "Completion rate": row["completion_rate"],
                "Crash/off-track/damage": (
                    f"{row['crash_count']:.0f}/"
                    f"{row['off_track_count']:.0f}/"
                    f"{row['damage']:.3f}"
                ),
                "Lap-time standard deviation": std_lap,
                "Runtime/decision latency": (
                    f"{float(mean_runtime):.4f}s / {float(mean_latency):.5f}ms"
                    if mean_runtime != "" and mean_latency != ""
                    else ""
                ),
                "Interpretation": interpretation_for(row["source"], row["algorithm"]),
            }
        )

    comparison = pd.DataFrame(rows)
    comparison.to_csv(RESULTS_DIR / "comparison_summary.csv", index=False)
    return comparison


def display_label(row: pd.Series) -> str:
    return f"{row['experiment_id']} ({row['source']})"


def title_prefix(mode: str) -> str:
    return {
        "dummy": "Dummy Pipeline Validation",
        "live": "Live TORCS Evidence",
        "partb": "Part B Imported PPO Evidence",
        "stress": "Stress-Test Evidence",
        "all": "Combined Evidence",
    }[mode]


def chart_subset(df: pd.DataFrame, sort_column: str, ascending: bool, limit: int = 20) -> pd.DataFrame:
    subset = df.sort_values(sort_column, ascending=ascending).head(limit).copy()
    subset["label"] = subset.apply(display_label, axis=1)
    return subset


def barh_chart(
    df: pd.DataFrame,
    value_column: str,
    title: str,
    xlabel: str,
    filename: str,
    *,
    ascending: bool = True,
) -> None:
    if df.empty:
        return
    data = chart_subset(df, value_column, ascending)
    data = data.sort_values(value_column, ascending=False)
    height = max(5.0, 0.38 * len(data) + 1.8)
    fig, ax = plt.subplots(figsize=(11, height))
    colors = [SOURCE_COLORS.get(source, "#374151") for source in data["source"]]
    ax.barh(data["label"], data[value_column], color=colors)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / filename, dpi=170)
    plt.close(fig)


def average_lap_variance_chart(robustness: pd.DataFrame, mode: str) -> None:
    if robustness.empty or "mean_lap_time" not in robustness.columns:
        return
    data = robustness[robustness["valid_runs"] > 0].copy()
    if data.empty:
        return
    data = data.sort_values("mean_lap_time").head(20)
    data["label"] = data["experiment_id"] + " (" + data["source"] + ")"
    data = data.sort_values("mean_lap_time", ascending=False)
    height = max(5.0, 0.38 * len(data) + 1.8)
    fig, ax = plt.subplots(figsize=(11, height))
    colors = [SOURCE_COLORS.get(source, "#374151") for source in data["source"]]
    ax.barh(
        data["label"],
        data["mean_lap_time"],
        xerr=data["std_lap_time"],
        color=colors,
        ecolor="#111827",
        capsize=3,
    )
    ax.set_title(f"{title_prefix(mode)}: Average Lap Time With Variance")
    ax.set_xlabel("Average lap time (seconds), error bar = standard deviation")
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "average_lap_time_with_variance.png", dpi=170)
    plt.close(fig)


def crash_damage_chart(robustness: pd.DataFrame, mode: str) -> None:
    if robustness.empty:
        return
    data = robustness.copy()
    data["safety_total"] = (
        data["total_crashes"].fillna(0)
        + data["total_off_track_events"].fillna(0)
        + data["max_damage"].fillna(0)
    )
    data = data.sort_values("safety_total").head(20)
    data["label"] = data["experiment_id"] + " (" + data["source"] + ")"
    data = data.sort_values("safety_total", ascending=False)
    height = max(5.0, 0.38 * len(data) + 1.8)
    fig, ax = plt.subplots(figsize=(11, height))
    ax.barh(data["label"], data["total_crashes"], color="#B45309", label="Crashes")
    ax.barh(
        data["label"],
        data["total_off_track_events"],
        left=data["total_crashes"],
        color="#2563EB",
        label="Off-track events",
    )
    left = data["total_crashes"] + data["total_off_track_events"]
    ax.barh(
        data["label"],
        data["max_damage"],
        left=left,
        color="#BE185D",
        label="Damage",
    )
    ax.set_title(f"{title_prefix(mode)}: Crash, Off-Track, and Damage Comparison")
    ax.set_xlabel("Count or damage value")
    ax.legend(loc="lower right")
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "crash_offtrack_damage_comparison.png", dpi=170)
    plt.close(fig)


def runtime_latency_chart(efficiency: pd.DataFrame, mode: str) -> None:
    if efficiency.empty:
        return
    data = efficiency.sort_values("mean_runtime_per_run_seconds").head(20).copy()
    data["label"] = data["experiment_id"] + " (" + data["source"] + ")"
    data = data.sort_values("mean_runtime_per_run_seconds", ascending=False)
    height = max(5.0, 0.38 * len(data) + 1.8)
    fig, axes = plt.subplots(1, 2, figsize=(14, height), sharey=True)
    axes[0].barh(data["label"], data["mean_runtime_per_run_seconds"], color="#2563EB")
    axes[0].set_xlabel("Runtime per run (seconds)")
    axes[0].grid(axis="x", color="#E5E7EB", linewidth=0.8)
    axes[1].barh(data["label"], data["mean_decision_latency_ms"], color="#0F766E")
    axes[1].set_xlabel("Decision latency (ms)")
    axes[1].grid(axis="x", color="#E5E7EB", linewidth=0.8)
    fig.suptitle(f"{title_prefix(mode)}: Runtime and Decision Latency")
    for ax in axes:
        ax.set_axisbelow(True)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "runtime_or_decision_latency_comparison.png", dpi=170)
    plt.close(fig)


def make_charts(
    scored: pd.DataFrame,
    robustness: pd.DataFrame,
    efficiency: pd.DataFrame,
    mode: str,
) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "font.size": 10,
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": "#111827",
            "xtick.color": "#374151",
            "ytick.color": "#374151",
            "text.color": "#111827",
        }
    )

    barh_chart(
        scored,
        "best_lap_time",
        f"{title_prefix(mode)}: Best Lap Time by Configuration",
        "Best lap time (seconds)",
        "best_lap_time_by_configuration.png",
        ascending=True,
    )
    average_lap_variance_chart(robustness, mode)
    barh_chart(
        scored,
        "completion_rate",
        f"{title_prefix(mode)}: Completion Rate by Configuration",
        "Completion rate",
        "completion_rate_by_configuration.png",
        ascending=False,
    )
    crash_damage_chart(robustness, mode)
    runtime_latency_chart(efficiency, mode)
    barh_chart(
        scored,
        "balanced_score",
        f"{title_prefix(mode)}: Balanced Score by Configuration",
        "Balanced score (lower is better)",
        "balanced_score_by_configuration.png",
        ascending=True,
    )


def print_highlights(scored: pd.DataFrame) -> None:
    print("Best lap time experiment:")
    print(first_row(scored, ["best_lap_time"], [True]).to_string())
    print("\nSafest experiment:")
    print(
        first_row(
            scored,
            ["crash_count", "off_track_count", "damage", "completion_rate"],
            [True, True, True, False],
        ).to_string()
    )
    print("\nMost efficient experiment:")
    print(first_row(scored, ["runtime_per_run_seconds"], [True]).to_string())
    print("\nBalanced best configuration:")
    print(scored.iloc[0].to_string())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["dummy", "live", "partb", "stress", "all"],
        default="live",
        help="Choose which evidence source to highlight. All summary files are regenerated.",
    )
    parser.add_argument("--input", default=str(RUN_LOG))
    parser.add_argument("--partb-input", default=str(PARTB_RESULTS))
    parser.add_argument(
        "--baseline",
        default="EXP_001",
        help="Baseline experiment_id for improvement calculations.",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include rows with zero or blank lap times in scoring.",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    run_log_path = resolve_path(args.input)
    partb_path = resolve_path(args.partb_input)
    combined_raw, inputs = load_combined_results(run_log_path, partb_path)
    raw = combined_raw[mode_row_mask(combined_raw, args.mode)].copy()
    rows_loaded = len(raw)
    invalid_rows = int((~valid_lap_mask(raw)).sum()) if not raw.empty else 0
    incomplete_rows = int((valid_lap_mask(raw) & ~completed_lap_mask(raw)).sum()) if not raw.empty else 0

    if raw.empty:
        raise SystemExit(f"No experiment rows found for mode '{args.mode}'.")

    scoring_rows = raw.copy() if args.include_invalid else raw[completed_lap_mask(raw)].copy()
    if scoring_rows.empty:
        raise SystemExit(
            f"No valid non-zero lap-time rows found for mode '{args.mode}'."
        )

    aggregated = aggregate_experiments(scoring_rows)
    scored = add_balanced_score(aggregated)
    scored_path = RESULTS_DIR / SCORED_OUTPUTS[args.mode]
    scored.to_csv(scored_path, index=False)
    scored.to_csv(RESULTS_DIR / "scored_experiments.csv", index=False)

    dissertation_summaries = write_dissertation_summaries(
        combined_raw,
        baseline_id=args.baseline,
        include_invalid=args.include_invalid,
    )
    summary = dissertation_summaries[args.mode]
    robustness = create_robustness_summary(
        combined_raw if args.mode == "all" else raw,
    )
    efficiency = create_efficiency_summary(
        combined_raw if args.mode == "all" else raw,
    )
    comparison = dissertation_summaries["all"]
    make_charts(scored, robustness, efficiency, args.mode)

    print_highlights(scored)
    print("\nAnalysis details:")
    print(f"Mode: {args.mode}")
    print(f"Analysed input(s): {', '.join(str(path) for path in inputs)}")
    print(f"Rows loaded for mode: {rows_loaded}")
    print(f"Invalid rows excluded from scoring: {0 if args.include_invalid else invalid_rows}")
    print(
        "Incomplete rows excluded from scoring: "
        f"{0 if args.include_invalid else incomplete_rows}"
    )
    print(f"Baseline experiment: {args.baseline}")
    print(f"Scored output: {scored_path}")
    for mode in ["live", "dummy", "partb", "stress"]:
        print(f"{mode} summary: {RESULTS_DIR / SUMMARY_OUTPUTS[mode]}")
    print(f"Robustness summary: {RESULTS_DIR / 'robustness_summary.csv'}")
    print(
        "Computational efficiency summary: "
        f"{RESULTS_DIR / 'computational_efficiency_summary.csv'}"
    )
    print(f"Comparison summary: {RESULTS_DIR / 'comparison_summary.csv'}")
    print(f"Dissertation key results: {RESULTS_DIR / 'dissertation_key_results.csv'}")
    print(f"Chart directory: {CHARTS_DIR}")
    print(f"Summary rows written: {len(summary)}")
    print(f"Comparison rows written: {len(comparison)}")


if __name__ == "__main__":
    main()
