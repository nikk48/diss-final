"""Generate dissertation-ready Part C visuals.

The figures created here are static, reproducible evidence artefacts for the
Part C experimentation framework. Part B evidence is treated only as an
imported comparator and is never blended silently with Part C live, dummy, or
stress evidence.
"""

from __future__ import annotations

import csv
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import pandas as pd  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = RESULTS_DIR / "dissertation_visuals"

SOURCE_ORDER = [
    "dummy",
    "grid_dummy",
    "optuna_dummy",
    "optuna_dummy_replay",
    "live",
    "grid_live",
    "optuna_live",
    "optuna_live_replay",
    "stress_dummy",
    "stress_live",
    "partb_imported",
]
SOURCE_COLORS = {
    "dummy": "#737373",
    "grid_dummy": "#A3A3A3",
    "optuna_dummy": "#525252",
    "optuna_dummy_replay": "#78716C",
    "live": "#2563EB",
    "grid_live": "#0F766E",
    "optuna_live": "#B45309",
    "optuna_live_replay": "#EA580C",
    "stress_dummy": "#7C3AED",
    "stress_live": "#DC2626",
    "partb_imported": "#BE185D",
}
NEUTRAL = "#374151"
GRID = "#E5E7EB"


@dataclass
class FigureRecord:
    figure_id: str
    title: str
    png_path: Path
    svg_path: Path
    caption: str
    data_sources: str
    notes: str


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "best_lap_time" not in df.columns:
        return df.copy()
    out = numeric(df, ["best_lap_time", "completion_rate", "completed_lap"])
    completed = pd.Series([True] * len(out), index=out.index)
    if "completed_lap" in out.columns:
        completed = completed & (out["completed_lap"].fillna(0) == 1)
    elif "completion_rate" in out.columns:
        completed = completed & (out["completion_rate"].fillna(0) > 0)
    return out[(out["best_lap_time"].fillna(0) > 0) & completed].copy()


def source_color(source: object) -> str:
    return SOURCE_COLORS.get(str(source), "#4B5563")


def method_label(row: pd.Series) -> str:
    experiment = str(row.get("experiment_id", ""))
    source = str(row.get("source", ""))
    method = str(row.get("method", row.get("algorithm", "")))
    return f"{experiment}\n{source}\n{method}"


def style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")
    ax.tick_params(colors=NEUTRAL, labelsize=9)
    ax.title.set_color("#111827")
    ax.xaxis.label.set_color(NEUTRAL)
    ax.yaxis.label.set_color(NEUTRAL)


def save_figure(
    fig: plt.Figure,
    figure_id: str,
    title: str,
    caption: str,
    data_sources: str,
    records: list[FigureRecord],
    notes: str = "",
) -> None:
    png_path = OUTPUT_DIR / f"{figure_id}.png"
    svg_path = OUTPUT_DIR / f"{figure_id}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    records.append(
        FigureRecord(
            figure_id=figure_id,
            title=title,
            png_path=png_path,
            svg_path=svg_path,
            caption=caption,
            data_sources=data_sources,
            notes=notes,
        )
    )


def draw_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    face: str = "#F9FAFB",
    edge: str = "#9CA3AF",
    fontsize: int = 9,
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.2,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        "\n".join(textwrap.wrap(text, width=22)),
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#111827",
    )


def draw_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.2,
        color="#6B7280",
        shrinkA=7,
        shrinkB=7,
    )
    ax.add_patch(arrow)


def framework_diagram(records: list[FigureRecord]) -> None:
    figure_id = "fig_01_part_c_framework"
    title = "Part C Experimentation Framework"
    fig, ax = plt.subplots(figsize=(12.5, 5.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(1.4, 6.3)
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=18)

    boxes = [
        ((0.6, 4.7), "Configuration files\nYAML hyperparameters"),
        ((3.4, 4.7), "Experiment runner\nrepeatable run control"),
        ((6.2, 4.7), "TORCS live or\ndummy simulator"),
        ((9.0, 4.7), "Telemetry logs\nper-run CSV files"),
        ((9.0, 2.3), "run_log.csv\ncentral evidence log"),
        ((6.2, 2.3), "Analysis scripts\nsummary + scoring"),
        ((3.4, 2.3), "Tables and charts\ndissertation outputs"),
        ((0.6, 2.3), "Reproducibility and\ntalent-evidence outputs"),
    ]
    for index, (xy, label) in enumerate(boxes):
        fill = "#EFF6FF" if index in {1, 2, 5} else "#F9FAFB"
        draw_box(ax, xy, 2.0, 1.0, label, face=fill)

    for left, right in [(0, 1), (1, 2), (2, 3)]:
        draw_arrow(
            ax,
            (boxes[left][0][0] + 2.0, boxes[left][0][1] + 0.5),
            (boxes[right][0][0], boxes[right][0][1] + 0.5),
        )
    draw_arrow(ax, (10.0, 4.7), (10.0, 3.3))
    for left, right in [(4, 5), (5, 6), (6, 7)]:
        draw_arrow(
            ax,
            (boxes[left][0][0], boxes[left][0][1] + 0.5),
            (boxes[right][0][0] + 2.0, boxes[right][0][1] + 0.5),
        )

    caption = (
        "Figure 1. Overview of the Part C contribution: controlled configuration "
        "files drive repeatable TORCS or dummy experiments, which produce telemetry, "
        "run logs, analysis tables and reproducibility evidence."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "Repository structure, data/run_log.csv, analysis scripts",
        records,
    )


def evidence_source_map(records: list[FigureRecord]) -> None:
    figure_id = "fig_02_evidence_source_map"
    title = "Evidence Source Separation Map"
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=18)

    streams = [
        ("Dummy validation evidence", "validates pipeline only", "#F3F4F6", "summary_dummy.csv", 5.7),
        ("Live TORCS Part C evidence", "supports Part C live performance", "#EFF6FF", "summary_live.csv", 4.2),
        ("Stress-test evidence", "supports robustness exploration", "#F5F3FF", "summary_stress.csv", 2.7),
        ("Imported Part B comparator evidence", "comparator artefact only", "#FDF2F8", "summary_partb.csv", 1.2),
    ]
    for name, role, fill, summary, y in streams:
        draw_box(ax, (0.5, y), 2.25, 0.82, f"{name}\n{role}", face=fill, fontsize=8)
        draw_box(ax, (4.0, y), 1.8, 0.82, summary, face="white", fontsize=8)
        draw_arrow(ax, (2.75, y + 0.41), (4.0, y + 0.41))
        draw_arrow(ax, (5.8, y + 0.41), (7.1, 3.45))

    draw_box(
        ax,
        (7.1, 2.95),
        2.25,
        1.0,
        "comparison_summary.csv\nclear source labels retained",
        face="#ECFDF5",
        edge="#34D399",
    )

    caption = (
        "Figure 2. Evidence streams are separated before comparison: dummy rows "
        "validate the pipeline, live TORCS rows support Part C performance claims, "
        "stress rows support robustness exploration, and Part B rows are imported "
        "comparator artefacts only."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/summary_dummy.csv, results/summary_live.csv, results/summary_stress.csv, results/summary_partb.csv, results/comparison_summary.csv",
        records,
    )


def live_performance(summary_live: pd.DataFrame, records: list[FigureRecord]) -> None:
    df = valid_rows(summary_live)
    if df.empty:
        return
    allowed_sources = {"live", "grid_live", "optuna_live", "optuna_live_replay", "stress_live"}
    df = df[df["source"].isin(allowed_sources)].copy()
    if df.empty:
        return

    method = df["method"].astype(str) if "method" in df.columns else df["algorithm"].astype(str)
    include = (
        (
            (df["experiment_id"].astype(str) == "EXP_001")
            & (df["source"].astype(str) == "live")
            & (method == "rule_based")
        )
        | df["experiment_id"].astype(str).isin({"GRID_030", "GRID_040", "OPTUNA_LIVE_001"})
        | df["source"].astype(str).isin({"optuna_live_replay", "stress_live"})
    )
    df = df[include].copy()
    if df.empty:
        return

    df = numeric(df, ["mean_lap_time", "best_lap_time", "completion_rate"]).sort_values(
        "mean_lap_time"
    )
    figure_id = "fig_03_live_lap_time_comparison"
    title = "Verified live TORCS mean lap time by configuration"
    labels = [method_label(row) for _, row in df.iterrows()]
    colors = [source_color(row.get("source")) for _, row in df.iterrows()]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    bars = ax.barh(labels, df["mean_lap_time"], color=colors, edgecolor="#1F2937", linewidth=0.6)
    ax.invert_yaxis()
    ax.set_xlabel("Mean lap time (seconds, lower is better)")
    ax.set_ylabel("Part C live evidence group")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    for bar, value in zip(bars, df["mean_lap_time"]):
        ax.text(
            value + 0.35,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}s",
            va="center",
            ha="left",
            fontsize=8.5,
            color=NEUTRAL,
        )
    ax.text(
        0,
        -0.12,
        "Invalid zero-lap rows excluded. Part B comparator is not included in this live-only figure.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#6B7280",
    )

    caption = (
        "Lower lap time is better. This figure compares only Part C live TORCS "
        "configurations, excluding dummy validation and imported Part B evidence."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/summary_live.csv",
        records,
        "Uses valid completed live rows only; excludes Part B imported comparator evidence.",
    )


def comparison_by_source(comparison: pd.DataFrame, records: list[FigureRecord]) -> None:
    df = valid_rows(comparison)
    if df.empty:
        return
    df = numeric(df, ["mean_lap_time", "best_lap_time"])
    focus_sources = ["dummy", "grid_live", "live", "optuna_live", "stress_dummy", "partb_imported"]
    df = df[df["source"].isin(focus_sources)].copy()
    if df.empty:
        return
    df = df.drop_duplicates(subset=["experiment_id", "source", "method", "mean_lap_time"])
    df["label"] = df.apply(method_label, axis=1)
    df = df.sort_values(["source", "mean_lap_time"])

    figure_id = "fig_04_cross_source_comparison"
    title = "Cross-Source Comparison With Evidence Labels"
    fig, ax = plt.subplots(figsize=(11, 7.2))
    y = range(len(df))
    ax.barh(
        y,
        df["mean_lap_time"],
        color=[source_color(s) for s in df["source"]],
        edgecolor="#1F2937",
        linewidth=0.5,
    )
    ax.set_yticks(list(y), df["label"])
    ax.invert_yaxis()
    ax.set_xlabel("Mean lap time (seconds, lower is better)")
    ax.set_ylabel("Evidence group")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    for ypos, value in zip(y, df["mean_lap_time"]):
        ax.text(value + 1.0, ypos, f"{value:.1f}s", va="center", fontsize=8.5, color=NEUTRAL)
    ax.text(
        0,
        -0.1,
        "This is a labelled comparison, not a claim that dummy, live, stress and imported Part B evidence are equivalent.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#6B7280",
    )

    caption = (
        "Figure 4. Cross-source comparison with source labels retained. Part B PPO "
        "appears only as imported comparator evidence, while Part C claims rely on "
        "the live, grid, Optuna, dummy-validation and stress-test streams."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/comparison_summary.csv",
        records,
        "Sources are labelled explicitly to avoid mixing evidence types.",
    )


def robustness_visual(robustness: pd.DataFrame, records: list[FigureRecord]) -> None:
    if robustness.empty:
        return
    df = robustness.copy()
    if "valid_runs" in df.columns:
        df = df[pd.to_numeric(df["valid_runs"], errors="coerce").fillna(0) > 0]
    if "best_lap_time" in df.columns:
        df = df[pd.to_numeric(df["best_lap_time"], errors="coerce").fillna(0) > 0]
    live_sources = {"live", "grid_live", "optuna_live", "optuna_live_replay", "stress_live"}
    df = df[df["source"].isin(live_sources)].copy()
    if df.empty:
        return
    df = numeric(df, ["std_lap_time", "completion_rate", "valid_runs"]).sort_values(
        ["completion_rate", "std_lap_time"], ascending=[False, True]
    )
    labels = [method_label(row) for _, row in df.iterrows()]

    figure_id = "fig_05_live_robustness"
    title = "Live Robustness Evidence"
    fig, ax1 = plt.subplots(figsize=(10.5, 5.8))
    x = list(range(len(df)))
    ax1.bar(
        x,
        df["std_lap_time"].fillna(0),
        color=[source_color(s) for s in df["source"]],
        edgecolor="#1F2937",
        linewidth=0.5,
    )
    ax1.set_ylabel("Lap-time standard deviation (seconds)")
    ax1.set_xticks(x, labels, rotation=0)
    ax1.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax1)
    ax1.grid(axis="y", color=GRID, linewidth=0.8)
    ax1.grid(axis="x", visible=False)

    ax2 = ax1.twinx()
    ax2.plot(x, df["completion_rate"], color="#111827", marker="o", linewidth=1.5, label="Completion rate")
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("Completion rate")
    ax2.tick_params(colors=NEUTRAL, labelsize=9)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color("#D1D5DB")
    for xpos, rate in zip(x, df["completion_rate"]):
        ax2.text(xpos, min(rate + 0.035, 1.04), f"{rate:.0%}", ha="center", fontsize=8)

    fig.tight_layout()
    caption = (
        "Figure 5. Robustness view for live Part C evidence: lower lap-time spread "
        "and high completion rate indicate more repeatable behaviour in the limited "
        "live sample."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/robustness_summary.csv",
        records,
        "Uses live-source rows with positive lap-time evidence.",
    )


def efficiency_visual(efficiency: pd.DataFrame, records: list[FigureRecord]) -> None:
    if efficiency.empty:
        return
    df = efficiency.copy()
    if "best_lap_time" in df.columns:
        df = df[pd.to_numeric(df["best_lap_time"], errors="coerce").fillna(0) > 0]
    live_sources = {"live", "grid_live", "optuna_live", "optuna_live_replay"}
    df = df[df["source"].isin(live_sources)].copy()
    if df.empty:
        return
    df = numeric(
        df,
        [
            "mean_runtime_per_run_seconds",
            "mean_decision_latency_ms",
            "best_lap_time",
            "valid_run_percentage",
        ],
    )
    df = df.sort_values("mean_runtime_per_run_seconds")

    figure_id = "fig_06_live_computational_efficiency"
    title = "Live Computational Efficiency"
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.scatter(
        df["mean_runtime_per_run_seconds"],
        df["mean_decision_latency_ms"],
        s=110,
        c=[source_color(s) for s in df["source"]],
        edgecolors="#111827",
        linewidths=0.8,
    )
    for _, row in df.iterrows():
        ax.annotate(
            str(row["experiment_id"]),
            (row["mean_runtime_per_run_seconds"], row["mean_decision_latency_ms"]),
            xytext=(6, 5),
            textcoords="offset points",
            fontsize=8.5,
            color=NEUTRAL,
        )
    ax.set_xlabel("Mean runtime per run (seconds)")
    ax.set_ylabel("Mean decision latency (milliseconds)")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    ax.grid(True, color=GRID, linewidth=0.8)

    caption = (
        "Figure 6. Computational-efficiency evidence for live Part C methods, "
        "showing runtime and decision latency without mixing dummy or imported "
        "Part B rows."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/computational_efficiency_summary.csv",
        records,
        "Live Part C methods only.",
    )


def sensitivity_visual(sensitivity: pd.DataFrame, records: list[FigureRecord]) -> None:
    df = valid_rows(sensitivity)
    if df.empty:
        return
    params = ["target_speed", "gentle_speed", "brake_threshold", "steer_gain"]
    available = [p for p in params if p in df.columns]
    if not available:
        return
    df = numeric(df, available + ["mean_lap_time"])
    df = df[df["source"].isin(["live", "grid_live", "optuna_live", "optuna_live_replay"])].copy()
    if len(df) < 2:
        return

    figure_id = "fig_07_hyperparameter_sensitivity"
    title = "Hyperparameter Sensitivity Signals"
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    axes = axes.ravel()
    for ax, param in zip(axes, available):
        plot_df = df[[param, "mean_lap_time", "source", "experiment_id"]].dropna()
        if plot_df.empty:
            ax.axis("off")
            continue
        ax.scatter(
            plot_df[param],
            plot_df["mean_lap_time"],
            s=80,
            c=[source_color(s) for s in plot_df["source"]],
            edgecolors="#111827",
            linewidths=0.6,
        )
        for _, row in plot_df.iterrows():
            ax.annotate(
                str(row["experiment_id"]),
                (row[param], row["mean_lap_time"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7.5,
                color=NEUTRAL,
            )
        ax.set_title(param.replace("_", " "), fontsize=11, fontweight="bold")
        ax.set_xlabel(param.replace("_", " "))
        ax.set_ylabel("Mean lap time (s)")
        style_axis(ax)
        ax.grid(True, color=GRID, linewidth=0.8)
    for ax in axes[len(available) :]:
        ax.axis("off")
    fig.suptitle(title, fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.text(
        0.02,
        0.01,
        "Exploratory visual only: small live sample, no statistical-significance claim.",
        fontsize=8.5,
        color="#6B7280",
    )

    caption = (
        "Figure 7. Exploratory sensitivity signals linking selected hyperparameters "
        "to mean lap time. The small live sample supports cautious discussion only "
        "and requires further testing before strong claims."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/hyperparameter_sensitivity.csv",
        records,
        "Cautious exploratory figure; no statistical-significance claim.",
    )


def choose_telemetry_rows(run_log: pd.DataFrame) -> pd.DataFrame:
    if run_log.empty or "telemetry_file" not in run_log.columns:
        return pd.DataFrame()
    df = valid_rows(run_log)
    if df.empty:
        return df
    df = df[df["source"].isin(["live", "grid_live", "optuna_live", "optuna_live_replay"])].copy()
    if df.empty:
        return df
    selected = []
    for source in ["live", "grid_live", "optuna_live"]:
        source_df = df[df["source"] == source].copy()
        if source_df.empty:
            continue
        source_df = numeric(source_df, ["best_lap_time"])
        selected.append(source_df.sort_values("best_lap_time").head(1))
    if not selected:
        return pd.DataFrame()
    return pd.concat(selected, ignore_index=True)


def read_telemetry(path_value: object) -> pd.DataFrame:
    path = resolve_telemetry_path(path_value)
    if path is None:
        return pd.DataFrame()
    df = read_csv_if_exists(path)
    return numeric(df, ["lap_time", "speed", "throttle", "brake"])


def resolve_telemetry_path(path_value: object) -> Path | None:
    if not isinstance(path_value, str) or not path_value:
        return None
    path = Path(path_value)
    repo_local = ROOT / "data" / "telemetry_logs" / path.name
    if repo_local.exists():
        return repo_local
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists() or path.stat().st_size == 0:
        return None
    return path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def telemetry_profile(run_log: pd.DataFrame, records: list[FigureRecord]) -> None:
    selected = choose_telemetry_rows(run_log)
    if selected.empty:
        return

    figure_id = "fig_08_live_telemetry_speed_profiles"
    title = "Live Telemetry Speed Profiles"
    fig, ax = plt.subplots(figsize=(11, 6))
    plotted = 0
    sources: list[str] = []
    for _, row in selected.iterrows():
        telemetry_path = resolve_telemetry_path(row.get("telemetry_file"))
        telemetry = read_telemetry(row.get("telemetry_file"))
        if telemetry.empty or "lap_time" not in telemetry.columns or "speed" not in telemetry.columns:
            continue
        telemetry = telemetry[(telemetry["lap_time"] >= 0) & (telemetry["speed"].notna())].copy()
        if telemetry.empty:
            continue
        if len(telemetry) > 900:
            telemetry = telemetry.iloc[:: max(1, math.floor(len(telemetry) / 900))]
        label = f"{row.get('experiment_id')} ({row.get('source')})"
        ax.plot(
            telemetry["lap_time"],
            telemetry["speed"],
            label=label,
            color=source_color(row.get("source")),
            linewidth=1.8,
        )
        plotted += 1
        if telemetry_path is not None:
            sources.append(display_path(telemetry_path))
    if plotted == 0:
        plt.close(fig)
        return
    ax.set_xlabel("Lap time (seconds)")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.legend(frameon=False, fontsize=8.5, loc="best")
    ax.text(
        0,
        -0.12,
        "Telemetry traces show controller behaviour during valid live TORCS runs.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#6B7280",
    )

    caption = (
        "Figure 8. Speed profiles from representative valid live telemetry files, "
        "showing how the Part C controller behaves over a lap."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "; ".join(sources),
        records,
        "Uses representative valid live telemetry files referenced in data/run_log.csv.",
    )


def write_captions(records: list[FigureRecord]) -> None:
    path = OUTPUT_DIR / "figure_captions.md"
    lines = ["# Dissertation Visual Captions", ""]
    for record in records:
        lines.extend(
            [
                f"## {record.figure_id}",
                "",
                record.caption,
                "",
                f"- PNG: `{record.png_path.relative_to(ROOT)}`",
                f"- SVG: `{record.svg_path.relative_to(ROOT)}`",
                f"- Data source(s): {record.data_sources}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(records: list[FigureRecord]) -> None:
    path = OUTPUT_DIR / "visual_manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "figure_id",
                "title",
                "png_path",
                "svg_path",
                "caption",
                "data_sources",
                "notes",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "figure_id": record.figure_id,
                    "title": record.title,
                    "png_path": str(record.png_path.relative_to(ROOT)),
                    "svg_path": str(record.svg_path.relative_to(ROOT)),
                    "caption": record.caption,
                    "data_sources": record.data_sources,
                    "notes": record.notes,
                }
            )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records: list[FigureRecord] = []

    run_log = read_csv_if_exists(DATA_DIR / "run_log.csv")
    summary_live = read_csv_if_exists(RESULTS_DIR / "summary_live.csv")
    comparison = read_csv_if_exists(RESULTS_DIR / "comparison_summary.csv")
    robustness = read_csv_if_exists(RESULTS_DIR / "robustness_summary.csv")
    efficiency = read_csv_if_exists(RESULTS_DIR / "computational_efficiency_summary.csv")
    sensitivity = read_csv_if_exists(RESULTS_DIR / "hyperparameter_sensitivity.csv")

    framework_diagram(records)
    evidence_source_map(records)
    live_performance(summary_live, records)
    comparison_by_source(comparison, records)
    robustness_visual(robustness, records)
    efficiency_visual(efficiency, records)
    sensitivity_visual(sensitivity, records)
    telemetry_profile(run_log, records)

    write_captions(records)
    write_manifest(records)

    print(f"Generated {len(records)} dissertation visual(s).")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Captions: {OUTPUT_DIR / 'figure_captions.md'}")
    print(f"Manifest: {OUTPUT_DIR / 'visual_manifest.csv'}")


if __name__ == "__main__":
    main()
