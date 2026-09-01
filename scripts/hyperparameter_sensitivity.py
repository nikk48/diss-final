"""Summarise Part C hyperparameter sensitivity from run_log.csv.

This script is deliberately cautious: it reports whether higher or lower
hyperparameter values appear associated with lap time in the filtered sample,
but it does not claim statistical significance.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.result_utils import DUMMY_SOURCES, LIVE_SOURCES, infer_source  # noqa: E402


RUN_LOG = ROOT / "data" / "run_log.csv"
RESULTS_DIR = ROOT / "results"
OUTPUT_CSV = RESULTS_DIR / "hyperparameter_sensitivity.csv"
OUTPUT_MD = RESULTS_DIR / "hyperparameter_sensitivity.md"
HYPERPARAMETERS = [
    "target_speed",
    "gentle_speed",
    "brake_threshold",
    "steer_gain",
]
NUMERIC_COLUMNS = [
    "best_lap_time",
    "average_lap_time",
    "completed_lap",
    "completion_rate",
    "runtime_per_run_seconds",
    "decision_latency_ms",
    "crash_count",
    "off_track_count",
    *HYPERPARAMETERS,
]
LEGACY_COLUMNS = {
    "corner_speed": "gentle_speed",
    "braking_threshold": "brake_threshold",
    "steering_gain": "steer_gain",
}
MODE_SOURCES = {
    "dummy": DUMMY_SOURCES,
    "live": LIVE_SOURCES,
    "all": DUMMY_SOURCES | LIVE_SOURCES,
}
SOURCE_CHOICES = ["all", *sorted(DUMMY_SOURCES | LIVE_SOURCES)]


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def read_run_log(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"Run log is missing or empty: {path}")

    df = pd.read_csv(path).rename(columns=LEGACY_COLUMNS)
    for column in ["experiment_id", "source", "algorithm", "track"]:
        if column not in df.columns:
            df[column] = ""
    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            df[column] = 0.0
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["source"] = df.apply(infer_source, axis=1)
    df["average_lap_time"] = df["average_lap_time"].fillna(df["best_lap_time"])
    return df


def filter_rows(df: pd.DataFrame, mode: str, source: str) -> pd.DataFrame:
    filtered = df[df["source"].isin(MODE_SOURCES[mode])].copy()
    if source != "all":
        filtered = filtered[filtered["source"] == source].copy()

    valid = (filtered["best_lap_time"] > 0) & (
        (filtered["completed_lap"].fillna(0) == 1)
        | (filtered["completion_rate"].fillna(0) > 0)
    )
    return filtered[valid].copy()


def aggregate_experiments(df: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "experiment_id",
        "source",
        "target_speed",
        "gentle_speed",
        "brake_threshold",
        "steer_gain",
    ]
    aggregated = (
        df.groupby(group_columns, dropna=False, as_index=False)
        .agg(
            mean_lap_time=("average_lap_time", "mean"),
            best_lap_time=("best_lap_time", "min"),
            std_lap_time=("average_lap_time", lambda values: values.std(ddof=0)),
            completion_rate=("completion_rate", "mean"),
            mean_runtime=("runtime_per_run_seconds", "mean"),
            mean_decision_latency=("decision_latency_ms", "mean"),
            crash_count=("crash_count", "sum"),
            off_track_count=("off_track_count", "sum"),
            valid_runs=("experiment_id", "size"),
        )
        .sort_values(["mean_lap_time", "best_lap_time", "experiment_id"], na_position="last")
        .reset_index(drop=True)
    )
    aggregated["rank"] = range(1, len(aggregated) + 1)
    return aggregated


def association_sentence(aggregated: pd.DataFrame, parameter: str) -> dict[str, object]:
    sample = aggregated[[parameter, "mean_lap_time"]].dropna().copy()
    sample = sample[sample[parameter].map(math.isfinite)]
    sample = sample[sample["mean_lap_time"].map(math.isfinite)]
    unique_values = sample[parameter].nunique()

    if len(sample) < 3 or unique_values < 2:
        return {
            "hyperparameter": parameter,
            "sample_size": len(sample),
            "spearman_rho": "",
            "assessment": (
                f"{parameter}: too little variation in this limited sample to infer a "
                "direction; requires further testing."
            ),
        }

    rho = sample[parameter].rank().corr(sample["mean_lap_time"].rank())
    if pd.isna(rho):
        assessment = (
            f"{parameter}: no clear directional association in this limited sample; "
            "requires further testing."
        )
    elif rho >= 0.15:
        assessment = (
            f"{parameter}: higher values appear associated with worse lap time, so "
            "lower values appear better in this limited sample; requires further testing."
        )
    elif rho <= -0.15:
        assessment = (
            f"{parameter}: higher values appear associated with better lap time in this "
            "limited sample; requires further testing."
        )
    else:
        assessment = (
            f"{parameter}: no clear directional association with lap time in this "
            "limited sample; requires further testing."
        )

    return {
        "hyperparameter": parameter,
        "sample_size": len(sample),
        "spearman_rho": round(float(rho), 4) if not pd.isna(rho) else "",
        "assessment": assessment,
    }


def add_interpretations(
    aggregated: pd.DataFrame,
    association_rows: list[dict[str, object]],
) -> pd.DataFrame:
    result = aggregated.copy()
    association_summary = " ".join(str(row["assessment"]) for row in association_rows)
    median_lap = result["mean_lap_time"].median()

    interpretations: list[str] = []
    for _, row in result.iterrows():
        if row["rank"] == 1:
            position = "Best aggregated lap time in the filtered sample."
        elif row["mean_lap_time"] <= median_lap:
            position = "Better-than-median lap time in the filtered sample."
        else:
            position = "Slower-than-median lap time in the filtered sample."
        interpretations.append(
            f"{position} Associations are exploratory: {association_summary}"
        )

    result["interpretation"] = interpretations
    return result


def format_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def markdown_table(rows: Iterable[dict[str, object]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        cells = [format_value(row.get(column, "")).replace("|", "\\|") for column in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_markdown(
    path: Path,
    mode: str,
    source: str,
    row_count: int,
    aggregated: pd.DataFrame,
    association_rows: list[dict[str, object]],
) -> None:
    association_columns = ["hyperparameter", "sample_size", "spearman_rho", "assessment"]
    table_columns = [
        "experiment_id",
        "source",
        "target_speed",
        "gentle_speed",
        "brake_threshold",
        "steer_gain",
        "mean_lap_time",
        "best_lap_time",
        "completion_rate",
        "mean_runtime",
        "interpretation",
    ]
    content = [
        "# Hyperparameter Sensitivity",
        "",
        f"Source file: `{RUN_LOG}`",
        f"Filter: mode=`{mode}`, source=`{source}`, valid rows=`{row_count}`.",
        "",
        "The associations below are directional signals only. They do not claim statistical significance because the number of live TORCS runs is small.",
        "",
        "## Directional Associations",
        "",
        markdown_table(association_rows, association_columns),
        "",
        "## Aggregated Experiments",
        "",
        markdown_table(aggregated[table_columns].to_dict("records"), table_columns),
        "",
    ]
    path.write_text("\n".join(content))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(RUN_LOG))
    parser.add_argument("--mode", choices=["live", "dummy", "all"], default="live")
    parser.add_argument("--source", choices=SOURCE_CHOICES, default="all")
    args = parser.parse_args()

    run_log_path = resolve_path(args.input)
    df = read_run_log(run_log_path)
    valid = filter_rows(df, args.mode, args.source)
    if valid.empty:
        raise SystemExit(
            "No valid rows matched the requested filters. "
            "Try --mode all --source all, or check that live runs completed a lap."
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    aggregated = aggregate_experiments(valid)
    association_rows = [
        association_sentence(aggregated, parameter) for parameter in HYPERPARAMETERS
    ]
    output = add_interpretations(aggregated, association_rows)

    output_columns = [
        "experiment_id",
        "source",
        "target_speed",
        "gentle_speed",
        "brake_threshold",
        "steer_gain",
        "mean_lap_time",
        "best_lap_time",
        "std_lap_time",
        "completion_rate",
        "mean_runtime",
        "mean_decision_latency",
        "crash_count",
        "off_track_count",
        "valid_runs",
        "interpretation",
    ]
    output[output_columns].to_csv(OUTPUT_CSV, index=False)
    write_markdown(
        path=OUTPUT_MD,
        mode=args.mode,
        source=args.source,
        row_count=len(valid),
        aggregated=output,
        association_rows=association_rows,
    )

    print(f"Analysed {len(valid)} valid row(s) from {run_log_path}")
    print(f"Aggregated {len(output)} experiment configuration(s)")
    print(f"CSV written: {OUTPUT_CSV}")
    print(f"Markdown written: {OUTPUT_MD}")
    print("\nDirectional association summary:")
    for row in association_rows:
        print(f"- {row['assessment']}")


if __name__ == "__main__":
    main()
