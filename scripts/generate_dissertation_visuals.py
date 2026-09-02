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


def improvement_vs_baseline(summary_live: pd.DataFrame, records: list[FigureRecord]) -> None:
    df = valid_rows(summary_live)
    if df.empty:
        return
    df = numeric(df, ["mean_lap_time", "best_lap_time", "completion_rate"])
    if "method" in df.columns:
        df["method_text"] = df["method"].astype(str)
    elif "algorithm" in df.columns:
        df["method_text"] = df["algorithm"].astype(str)
    else:
        df["method_text"] = ""

    baseline = df[
        (df["experiment_id"].astype(str) == "EXP_001")
        & (df["source"].astype(str) == "live")
        & (df["method_text"] == "rule_based")
    ].copy()
    if baseline.empty:
        return
    baseline_mean = float(baseline.iloc[0]["mean_lap_time"])

    requested_ids = {"GRID_030", "GRID_040", "OPTUNA_LIVE_001"}
    include = (
        df["experiment_id"].astype(str).isin(requested_ids)
        | (df["source"].astype(str) == "optuna_live_replay")
    )
    df = df[include].copy()
    if df.empty:
        return

    df["improvement_seconds"] = baseline_mean - df["mean_lap_time"]
    df["label"] = df.apply(method_label, axis=1)
    df = df.sort_values("improvement_seconds", ascending=False)

    figure_id = "fig_04_improvement_vs_baseline"
    title = "Live performance improvement versus verified baseline"
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    y = list(range(len(df)))
    colors = ["#B45309" if value >= 0 else "#9CA3AF" for value in df["improvement_seconds"]]
    bars = ax.barh(y, df["improvement_seconds"], color=colors, edgecolor="#1F2937", linewidth=0.6)
    ax.axvline(0, color="#111827", linewidth=1.1)
    ax.set_yticks(y, df["label"])
    ax.invert_yaxis()
    ax.set_xlabel("Improvement versus baseline (seconds)")
    ax.set_ylabel("Live Part C configuration")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    x_values = df["improvement_seconds"].fillna(0)
    padding = max(0.6, (x_values.max() - x_values.min()) * 0.12)
    ax.set_xlim(x_values.min() - padding, x_values.max() + padding)
    for bar, value in zip(bars, df["improvement_seconds"]):
        ha = "left" if value >= 0 else "right"
        offset = 0.08 if value >= 0 else -0.08
        ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:+.3f}s",
            va="center",
            ha=ha,
            fontsize=8.5,
            color=NEUTRAL,
        )
    ax.text(
        0,
        -0.13,
        "Positive values are faster than the verified EXP_001 live rule-based baseline; negative values are slower.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#6B7280",
    )

    caption = (
        "Figure 4. Improvement is calculated as verified baseline mean lap time "
        "minus experiment mean lap time. Positive values indicate faster live "
        "TORCS performance than the EXP_001 rule-based baseline."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/summary_live.csv",
        records,
        "Live Part C configurations only; excludes dummy validation and imported Part B comparator evidence.",
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
    crash_column = "crash_count" if "crash_count" in df.columns else "total_crashes"
    off_track_column = (
        "off_track_count" if "off_track_count" in df.columns else "total_off_track_events"
    )
    df = numeric(
        df,
        ["completion_rate", "valid_runs", crash_column, off_track_column],
    ).sort_values(["source", "experiment_id"])
    labels = [method_label(row) for _, row in df.iterrows()]

    figure_id = "fig_05_robustness_reproducibility_summary"
    title = "Robustness evidence from repeated live TORCS runs"
    metrics = [
        ("valid_runs", "Valid runs", "runs", None),
        ("completion_rate_percent", "Completion rate", "%", 100),
        (crash_column, "Crash count", "count", None),
        (off_track_column, "Off-track count", "count", None),
    ]
    df["completion_rate_percent"] = df["completion_rate"].fillna(0) * 100

    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), sharey=True)
    axes = axes.flatten()
    y = list(range(len(df)))
    colors = [source_color(source) for source in df["source"]]

    for index, (column, panel_title, unit, fixed_max) in enumerate(metrics):
        ax = axes[index]
        values = df[column].fillna(0)
        ax.barh(y, values, color=colors, edgecolor="#1F2937", linewidth=0.5)
        ax.set_title(panel_title, fontsize=11.5, fontweight="bold", color="#111827")
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        style_axis(ax)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.grid(axis="y", visible=False)
        limit = fixed_max if fixed_max is not None else max(float(values.max()) * 1.25, 1.0)
        ax.set_xlim(0, limit)
        ax.set_xlabel(unit)
        if index % 2 == 1:
            ax.tick_params(axis="y", labelleft=False)
        for ypos, value in zip(y, values):
            label = f"{value:.0f}%" if unit == "%" else f"{value:.0f}"
            offset = limit * 0.025
            ax.text(
                min(float(value) + offset, limit * 0.98),
                ypos,
                label,
                va="center",
                ha="left",
                fontsize=8.5,
                color=NEUTRAL,
            )

    fig.suptitle(title, fontsize=15, fontweight="bold", color="#111827", y=0.98)
    fig.text(
        0.5,
        0.015,
        "Completion rate is shown as a percentage; other panels are run/event counts. Invalid zero-lap rows are excluded.",
        ha="center",
        fontsize=8.5,
        color="#6B7280",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    caption = (
        "Repeated runs under identical conditions support reproducibility. Broader "
        "robustness requires stress tests or varied conditions."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/robustness_summary.csv",
        records,
        "Uses live Part C rows with positive lap-time evidence; completion rate shown as percentage.",
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
    if "algorithm" in df.columns:
        df["method_text"] = df["algorithm"].astype(str)
    else:
        df["method_text"] = ""
    requested_ids = {"GRID_030", "GRID_040", "OPTUNA_LIVE_001"}
    include = (
        (
            (df["experiment_id"].astype(str) == "EXP_001")
            & (df["source"].astype(str) == "live")
            & (df["method_text"] == "rule_based")
        )
        | df["experiment_id"].astype(str).isin(requested_ids)
        | (df["source"].astype(str) == "optuna_live_replay")
    )
    df = df[include].copy()
    if df.empty:
        return
    df = numeric(
        df,
        [
            "mean_runtime_per_run_seconds",
            "mean_decision_latency_ms",
            "mean_cpu_usage",
            "mean_memory_usage",
            "best_lap_time",
            "valid_run_percentage",
        ],
    )
    df = df.sort_values("mean_runtime_per_run_seconds")

    figure_id = "fig_06_live_computational_efficiency"
    title = "Computational-efficiency indicators for live Part C experiments"
    metrics = [
        ("mean_runtime_per_run_seconds", "Runtime per run", "seconds"),
        ("mean_decision_latency_ms", "Decision latency", "milliseconds"),
        ("mean_cpu_usage", "CPU usage", "%"),
        ("mean_memory_usage", "Memory usage", "%"),
    ]
    metrics = [(column, panel_title, unit) for column, panel_title, unit in metrics if column in df.columns]
    if not metrics:
        return

    labels = [method_label(row) for _, row in df.iterrows()]
    colors = [source_color(source) for source in df["source"]]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.4), sharey=True)
    axes = axes.flatten()
    y = list(range(len(df)))

    for index, ax in enumerate(axes):
        if index >= len(metrics):
            ax.axis("off")
            continue
        column, panel_title, unit = metrics[index]
        values = df[column].fillna(0)
        ax.barh(y, values, color=colors, edgecolor="#1F2937", linewidth=0.5)
        ax.set_title(panel_title, fontsize=11.5, fontweight="bold", color="#111827")
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        style_axis(ax)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.grid(axis="y", visible=False)
        limit = max(float(values.max()) * 1.22, 0.01)
        ax.set_xlim(0, limit)
        ax.set_xlabel(unit)
        if index % 2 == 1:
            ax.tick_params(axis="y", labelleft=False)
        for ypos, value in zip(y, values):
            if unit == "seconds":
                label = f"{value:.3f}s"
            elif unit == "milliseconds":
                label = f"{value:.4f} ms"
            else:
                label = f"{value:.1f}%"
            ax.text(
                min(float(value) + limit * 0.025, limit * 0.98),
                ypos,
                label,
                va="center",
                ha="left",
                fontsize=8.5,
                color=NEUTRAL,
            )

    fig.suptitle(title, fontsize=15, fontweight="bold", color="#111827", y=0.98)
    fig.text(
        0.5,
        0.015,
        "Live Part C rows only. Dummy and imported Part B runtime evidence are excluded from this figure.",
        ha="center",
        fontsize=8.5,
        color="#6B7280",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))

    caption = (
        "Figure 6. Computational-efficiency indicators for live Part C experiments, "
        "comparing the verified rule-based baseline, grid-search configurations, "
        "and Optuna live configuration without mixing dummy or imported Part B runtime evidence."
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
    param_specs = [
        ("fig_07a_target_speed_sensitivity", "Figure 7a", "target_speed", "Target speed"),
        ("fig_07b_gentle_speed_sensitivity", "Figure 7b", "gentle_speed", "Gentle speed"),
        ("fig_07c_brake_threshold_sensitivity", "Figure 7c", "brake_threshold", "Brake threshold"),
        ("fig_07d_steer_gain_sensitivity", "Figure 7d", "steer_gain", "Steer gain"),
    ]
    available = [param for _, _, param, _ in param_specs if param in df.columns]
    if not available or "mean_lap_time" not in df.columns:
        return
    df = numeric(df, available + ["mean_lap_time"])
    live_sources = {"live", "grid_live", "optuna_live", "optuna_live_replay", "stress_live"}
    df = df[df["source"].isin(live_sources)].copy()
    if len(df) < 2:
        return

    for figure_id, figure_label, param, param_label in param_specs:
        if param not in df.columns:
            continue
        plot_df = df[[param, "mean_lap_time", "source", "experiment_id"]].dropna()
        if plot_df.empty:
            continue
        title = f"{param_label} sensitivity versus mean lap time"
        fig, ax = plt.subplots(figsize=(8.2, 5.6))
        ax.scatter(
            plot_df[param],
            plot_df["mean_lap_time"],
            s=95,
            c=[source_color(s) for s in plot_df["source"]],
            edgecolors="#111827",
            linewidths=0.7,
        )
        for _, row in plot_df.iterrows():
            ax.annotate(
                str(row["experiment_id"]),
                (row[param], row["mean_lap_time"]),
                xytext=(6, 5),
                textcoords="offset points",
                fontsize=8,
                color=NEUTRAL,
            )
        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel(param_label)
        ax.set_ylabel("Mean lap time (seconds, lower is better)")
        style_axis(ax)
        ax.grid(True, color=GRID, linewidth=0.8)

        x_values = plot_df[param]
        y_values = plot_df["mean_lap_time"]
        if x_values.nunique() == 1:
            pad = max(abs(float(x_values.iloc[0])) * 0.04, 0.1)
            ax.set_xlim(float(x_values.iloc[0]) - pad, float(x_values.iloc[0]) + pad)
        if y_values.nunique() == 1:
            pad = max(abs(float(y_values.iloc[0])) * 0.01, 0.5)
            ax.set_ylim(float(y_values.iloc[0]) - pad, float(y_values.iloc[0]) + pad)
        ax.text(
            0,
            -0.16,
            "This is an exploratory sensitivity visual based on a small live sample and should not be interpreted as statistical proof.",
            transform=ax.transAxes,
            fontsize=8.5,
            color="#6B7280",
        )
        fig.tight_layout()

        caption = (
            f"{figure_label}. {param_label} plotted against mean lap time for live Part C "
            "experiments. This is an exploratory sensitivity visual based on a "
            "small live sample and should not be interpreted as statistical proof."
        )
        save_figure(
            fig,
            figure_id,
            title,
            caption,
            "results/hyperparameter_sensitivity.csv",
            records,
            "Live Part C rows only; exploratory visual with no statistical-significance claim.",
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
    telemetry_columns = [
        "lap_time",
        "speed",
        "steering",
        "steer",
        "throttle",
        "accel",
        "brake",
        "distance",
        "dist_from_start",
        "distFromStart",
    ]
    return numeric(df, telemetry_columns)


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


def choose_baseline_and_optuna_telemetry(run_log: pd.DataFrame) -> dict[str, pd.Series]:
    if run_log.empty or "telemetry_file" not in run_log.columns:
        return {}
    df = valid_rows(run_log)
    if df.empty:
        return {}
    df = df.copy()
    for column in ["experiment_id", "source", "algorithm"]:
        if column not in df.columns:
            df[column] = ""
    df = df[df["telemetry_file"].apply(lambda value: resolve_telemetry_path(value) is not None)]
    if df.empty:
        return {}

    baseline = df[
        (df["experiment_id"].astype(str) == "EXP_001")
        & (df["source"].astype(str) == "live")
        & (df["algorithm"].astype(str) == "rule_based")
    ].copy()
    optuna = df[
        (df["experiment_id"].astype(str) == "OPTUNA_LIVE_001")
        & (df["source"].astype(str) == "optuna_live")
    ].copy()
    selected: dict[str, pd.Series] = {}
    if not baseline.empty:
        selected["Verified baseline EXP_001"] = baseline.sort_values("telemetry_file").iloc[0]
    if not optuna.empty:
        selected["Optuna OPTUNA_LIVE_001"] = optuna.sort_values("telemetry_file").iloc[0]
    return selected


def prepare_profile_telemetry(row: pd.Series) -> tuple[pd.DataFrame, str]:
    telemetry = read_telemetry(row.get("telemetry_file"))
    if telemetry.empty:
        return telemetry, "Simulation step"
    if "lap_time" in telemetry.columns:
        telemetry = telemetry[(telemetry["lap_time"].fillna(-1) >= 0)].copy()
    if telemetry.empty:
        return telemetry, "Simulation step"

    distance_candidates = ["distance", "dist_from_start", "distFromStart"]
    x_column = next(
        (column for column in distance_candidates if column in telemetry.columns and telemetry[column].notna().any()),
        None,
    )
    if x_column is None:
        telemetry = telemetry.reset_index(drop=True)
        telemetry["simulation_step"] = telemetry.index + 1
        x_column = "simulation_step"
        x_label = "Simulation step"
    else:
        x_label = "Distance"

    if len(telemetry) > 900:
        telemetry = telemetry.iloc[:: max(1, math.floor(len(telemetry) / 900))].copy()
    return telemetry, x_label


def plot_baseline_optuna_profile(
    rows: dict[str, pd.Series],
    figure_id: str,
    title: str,
    y_columns: list[tuple[str, str, str]],
    y_label: str,
    records: list[FigureRecord],
) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    plotted = 0
    sources: list[str] = []
    x_label = "Simulation step"
    base_colors = {
        "Verified baseline EXP_001": "#2563EB",
        "Optuna OPTUNA_LIVE_001": "#B45309",
    }

    for row_label, row in rows.items():
        telemetry_path = resolve_telemetry_path(row.get("telemetry_file"))
        telemetry, x_label = prepare_profile_telemetry(row)
        if telemetry.empty:
            continue
        x_column = "simulation_step"
        if x_label == "Distance":
            x_column = next(
                column
                for column in ["distance", "dist_from_start", "distFromStart"]
                if column in telemetry.columns and telemetry[column].notna().any()
            )
        for column, suffix, linestyle in y_columns:
            if column not in telemetry.columns or telemetry[column].dropna().empty:
                continue
            ax.plot(
                telemetry[x_column],
                telemetry[column],
                label=f"{row_label} {suffix}".strip(),
                color=base_colors.get(row_label, NEUTRAL),
                linestyle=linestyle,
                linewidth=1.6,
            )
            plotted += 1
        if telemetry_path is not None:
            sources.append(display_path(telemetry_path))

    if plotted == 0:
        plt.close(fig)
        return
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    ax.grid(True, color=GRID, linewidth=0.8)
    if len(y_columns) > 1:
        ax.legend(frameon=False, fontsize=8.2, loc="center left", bbox_to_anchor=(1.01, 0.5))
    else:
        ax.legend(frameon=False, fontsize=8.2, loc="best")
    ax.text(
        0,
        -0.13,
        "These plots show how the driving behaviour differs over the lap, not just the final lap time.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#6B7280",
    )
    fig.tight_layout()

    caption = (
        "These plots show how the driving behaviour differs over the lap, not just "
        "the final lap time."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "; ".join(sources),
        records,
        "Uses one verified baseline live telemetry file and one verified Optuna live telemetry file referenced in data/run_log.csv.",
    )


def baseline_vs_optuna_telemetry(run_log: pd.DataFrame, records: list[FigureRecord]) -> None:
    rows = choose_baseline_and_optuna_telemetry(run_log)
    if len(rows) < 2:
        return
    plot_baseline_optuna_profile(
        rows,
        "fig_09a_speed_profile_baseline_vs_optuna",
        "Speed profile: verified baseline versus Optuna",
        [("speed", "", "-")],
        "Speed (km/h)",
        records,
    )
    steering_column = "steering"
    sample_telemetry = read_telemetry(next(iter(rows.values())).get("telemetry_file"))
    if steering_column not in sample_telemetry.columns and "steer" in sample_telemetry.columns:
        steering_column = "steer"
    plot_baseline_optuna_profile(
        rows,
        "fig_09b_steering_profile_baseline_vs_optuna",
        "Steering profile: verified baseline versus Optuna",
        [(steering_column, "", "-")],
        "Steering command",
        records,
    )
    throttle_column = "throttle"
    if throttle_column not in sample_telemetry.columns and "accel" in sample_telemetry.columns:
        throttle_column = "accel"
    plot_baseline_optuna_profile(
        rows,
        "fig_09c_throttle_brake_profile_baseline_vs_optuna",
        "Throttle and brake profile: verified baseline versus Optuna",
        [(throttle_column, "throttle", "-"), ("brake", "brake", "--")],
        "Control command value",
        records,
    )


def optuna_trial_history(optuna_trials: pd.DataFrame, records: list[FigureRecord]) -> None:
    if optuna_trials.empty or "trial" not in optuna_trials.columns:
        return
    score_column = None
    score_label = None
    for candidate, label in [
        ("objective_score", "Objective score (lower is better)"),
        ("balanced_score", "Balanced objective score (lower is better)"),
        ("mean_lap_time", "Mean lap time (seconds, lower is better)"),
        ("average_lap_time", "Mean lap time (seconds, lower is better)"),
    ]:
        if candidate in optuna_trials.columns:
            score_column = candidate
            score_label = label
            break
    if score_column is None or score_label is None:
        return

    df = numeric(optuna_trials, ["trial", score_column]).dropna(subset=["trial", score_column])
    if df.empty:
        return
    df = df.sort_values("trial")
    best = df.loc[df[score_column].idxmin()]

    figure_id = "fig_08_optuna_trial_history"
    title = "Optuna search progress"
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.plot(
        df["trial"],
        df[score_column],
        color="#B45309",
        linewidth=1.8,
        marker="o",
        markersize=6,
        markeredgecolor="#111827",
    )
    ax.scatter(
        [best["trial"]],
        [best[score_column]],
        s=150,
        color="#2563EB",
        edgecolor="#111827",
        linewidth=0.8,
        zorder=4,
        label="Best trial",
    )
    best_label = f"Best trial {int(best['trial'])}: {best[score_column]:.3f}"
    ax.annotate(
        best_label,
        (best["trial"], best[score_column]),
        xytext=(8, 12),
        textcoords="offset points",
        fontsize=9,
        color=NEUTRAL,
        arrowprops={"arrowstyle": "->", "color": "#6B7280", "linewidth": 0.8},
    )
    ax.set_xlabel("Trial number")
    ax.set_ylabel(score_label)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    style_axis(ax)
    ax.grid(True, color=GRID, linewidth=0.8)
    if len(df) == 1:
        trial = float(df["trial"].iloc[0])
        score = float(df[score_column].iloc[0])
        ax.set_xlim(trial - 0.5, trial + 0.5)
        ax.set_ylim(score * 0.995, score * 1.005)
        ax.text(
            0,
            -0.14,
            "Only one Optuna trial is currently recorded; add more trials for a clearer search-progress curve.",
            transform=ax.transAxes,
            fontsize=8.5,
            color="#6B7280",
        )
    ax.legend(frameon=False, loc="best", fontsize=8.5)

    caption = (
        "Optuna was used as an automated hyperparameter optimisation extension. "
        "Lower objective score indicates better balance of lap time, completion "
        "and penalty metrics."
    )
    save_figure(
        fig,
        figure_id,
        title,
        caption,
        "results/optuna_trials.csv",
        records,
        f"Y-axis uses {score_column}; best trial is the lowest available value.",
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
    robustness = read_csv_if_exists(RESULTS_DIR / "robustness_summary.csv")
    efficiency = read_csv_if_exists(RESULTS_DIR / "computational_efficiency_summary.csv")
    sensitivity = read_csv_if_exists(RESULTS_DIR / "hyperparameter_sensitivity.csv")
    optuna_trials = read_csv_if_exists(RESULTS_DIR / "optuna_trials.csv")

    framework_diagram(records)
    evidence_source_map(records)
    live_performance(summary_live, records)
    improvement_vs_baseline(summary_live, records)
    robustness_visual(robustness, records)
    efficiency_visual(efficiency, records)
    sensitivity_visual(sensitivity, records)
    optuna_trial_history(optuna_trials, records)
    baseline_vs_optuna_telemetry(run_log, records)

    write_captions(records)
    write_manifest(records)

    print(f"Generated {len(records)} dissertation visual(s).")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Captions: {OUTPUT_DIR / 'figure_captions.md'}")
    print(f"Manifest: {OUTPUT_DIR / 'visual_manifest.csv'}")


if __name__ == "__main__":
    main()
