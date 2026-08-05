"""Analyse dummy or real experiment results.

The first goal is to prove the analysis pipeline before relying on TORCS. The
same scoring idea can later be applied to real experiment summaries.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "run_log.csv"
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"
LEGACY_COLUMN_NAMES = {
    "corner_speed": "gentle_speed",
    "braking_threshold": "brake_threshold",
    "steering_gain": "steer_gain",
}
METRIC_COLUMNS = [
    "average_lap_time",
    "completion_rate",
    "crash_count",
    "off_track_count",
    "runtime_per_run_seconds",
]


def min_max(series: pd.Series) -> pd.Series:
    span = series.max() - series.min()
    if span == 0:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - series.min()) / span


def add_balanced_score(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()
    scored["lap_time_score"] = min_max(scored["average_lap_time"])
    scored["crash_score"] = min_max(scored["crash_count"])
    scored["off_track_score"] = min_max(scored["off_track_count"])
    scored["runtime_score"] = min_max(scored["runtime_per_run_seconds"])
    scored["completion_penalty"] = 1.0 - scored["completion_rate"]

    scored["balanced_score"] = (
        scored["lap_time_score"] * 0.40
        + scored["completion_penalty"] * 0.25
        + scored["crash_score"] * 0.15
        + scored["off_track_score"] * 0.10
        + scored["runtime_score"] * 0.10
    )
    return scored.sort_values("balanced_score", ascending=True)


def load_results(path: Path, include_invalid: bool = False) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns=LEGACY_COLUMN_NAMES)

    if "average_lap_time" not in df.columns and "best_lap_time" in df.columns:
        df["average_lap_time"] = df["best_lap_time"]

    missing = [column for column in METRIC_COLUMNS if column not in df.columns]
    if missing:
        raise SystemExit(
            f"{path} is missing required analysis column(s): {', '.join(missing)}"
        )

    for column in METRIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if not include_invalid:
        before = len(df)
        df = df[df["average_lap_time"] > 0].copy()
        excluded = before - len(df)
        if excluded:
            print(f"Excluded {excluded} invalid row(s) with zero or blank lap time.")

    if df.empty:
        raise SystemExit(f"No valid experiment rows found in {path}")

    return aggregate_experiments(df)


def aggregate_experiments(df: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        column
        for column in [
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
        return df

    aggregated = (
        df.groupby(group_columns, dropna=False, as_index=False)
        .agg(
            average_lap_time=("average_lap_time", "mean"),
            completion_rate=("completion_rate", "mean"),
            crash_count=("crash_count", "mean"),
            off_track_count=("off_track_count", "mean"),
            runtime_per_run_seconds=("runtime_per_run_seconds", "mean"),
        )
        .copy()
    )
    return aggregated


def save_summary(scored: pd.DataFrame) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    scored.to_csv(RESULTS_DIR / "scored_experiments.csv", index=False)

    rows = [
        {
            "category": "best_lap_time",
            "experiment_id": scored.sort_values("average_lap_time").iloc[0][
                "experiment_id"
            ],
        },
        {
            "category": "safest",
            "experiment_id": scored.sort_values(
                ["crash_count", "off_track_count", "completion_rate"],
                ascending=[True, True, False],
            ).iloc[0]["experiment_id"],
        },
        {
            "category": "most_efficient",
            "experiment_id": scored.sort_values("runtime_per_run_seconds").iloc[0][
                "experiment_id"
            ],
        },
        {
            "category": "balanced_best",
            "experiment_id": scored.iloc[0]["experiment_id"],
        },
    ]
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "summary.csv", index=False)


def make_charts(scored: pd.DataFrame) -> None:
    ordered = scored.sort_values("experiment_id")

    chart_specs = [
        ("average_lap_time", "Average Lap Time by Experiment", "Lap time"),
        ("completion_rate", "Completion Rate by Experiment", "Completion rate"),
        ("crash_count", "Crash Count by Experiment", "Crashes"),
        ("balanced_score", "Balanced Score by Experiment", "Balanced score"),
    ]

    for column, title, ylabel in chart_specs:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(ordered["experiment_id"], ordered[column])
        ax.set_title(title)
        ax.set_xlabel("Experiment")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        fig.savefig(CHARTS_DIR / f"{column}.png", dpi=160)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(scored["runtime_per_run_seconds"], scored["average_lap_time"])
    for _, row in scored.iterrows():
        ax.annotate(
            row["experiment_id"],
            (row["runtime_per_run_seconds"], row["average_lap_time"]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )
    ax.set_title("Runtime vs Average Lap Time")
    ax.set_xlabel("Runtime per run (seconds)")
    ax.set_ylabel("Average lap time")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "runtime_vs_lap_time.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA_PATH))
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include rows with zero or blank lap times in scoring.",
    )
    args = parser.parse_args()

    input_path = (ROOT / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input)
    df = load_results(input_path, include_invalid=args.include_invalid)
    scored = add_balanced_score(df)
    save_summary(scored)
    make_charts(scored)

    print("Best lap time experiment:")
    print(scored.sort_values("average_lap_time").iloc[0].to_string())
    print("\nSafest experiment:")
    print(
        scored.sort_values(
            ["crash_count", "off_track_count", "completion_rate"],
            ascending=[True, True, False],
        )
        .iloc[0]
        .to_string()
    )
    print("\nMost efficient experiment:")
    print(scored.sort_values("runtime_per_run_seconds").iloc[0].to_string())
    print("\nBalanced best configuration:")
    print(scored.iloc[0].to_string())
    print(f"\nAnalysed input: {input_path}")
    print(f"Saved outputs to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
