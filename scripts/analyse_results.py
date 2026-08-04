"""Analyse dummy or real experiment results.

The first goal is to prove the analysis pipeline before relying on TORCS. The
same scoring idea can later be applied to real experiment summaries.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "dummy_experiments.csv"
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"


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
    df = pd.read_csv(DATA_PATH)
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
    print(f"\nSaved outputs to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()

