"""Run a configured experiment.

The current implementation supports a deterministic dummy mode. The function
names are structured so the dummy simulator can later be replaced with live
TORCS calls while keeping the same logging format.
"""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.baseline_rule_agent import build_agent  # noqa: E402
from scripts.telemetry_logger import TelemetryLogger  # noqa: E402


RUN_LOG_FIELDS = [
    "experiment_id",
    "date_time",
    "track",
    "agent_version",
    "state_version",
    "policy_version",
    "reward_version",
    "algorithm",
    "run_number",
    "seed",
    "target_speed",
    "steer_gain",
    "centering_gain",
    "brake_threshold",
    "gentle_speed",
    "sharp_speed",
    "straight_speed",
    "acceleration_limit",
    "braking_intensity",
    "best_lap_time",
    "average_lap_time",
    "completed_lap",
    "completion_rate",
    "crash_count",
    "off_track_count",
    "lap_time_variance",
    "training_time_seconds",
    "runtime_per_run_seconds",
    "decision_latency_ms",
    "cpu_usage",
    "memory_usage",
    "config_path",
    "telemetry_file",
    "notes",
]


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as file:
        return yaml.safe_load(file)


def append_run_log(row: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RUN_LOG_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RUN_LOG_FIELDS})


def dummy_track_state(step: int, rng: random.Random) -> dict[str, Any]:
    straight = 180.0 - (step % 60)
    corner_pressure = 35.0 + (step % 25)
    track = [
        corner_pressure + rng.uniform(-5, 5),
        45 + rng.uniform(-5, 5),
        60 + rng.uniform(-5, 5),
        80 + rng.uniform(-5, 5),
        100 + rng.uniform(-5, 5),
        120 + rng.uniform(-5, 5),
        140 + rng.uniform(-5, 5),
        160 + rng.uniform(-5, 5),
        170 + rng.uniform(-5, 5),
        straight + rng.uniform(-8, 8),
        170 + rng.uniform(-5, 5),
        160 + rng.uniform(-5, 5),
        140 + rng.uniform(-5, 5),
        120 + rng.uniform(-5, 5),
        100 + rng.uniform(-5, 5),
        80 + rng.uniform(-5, 5),
        60 + rng.uniform(-5, 5),
        45 + rng.uniform(-5, 5),
        corner_pressure + rng.uniform(-5, 5),
    ]
    return {
        "speed": 60.0 + rng.uniform(-6, 10),
        "angle": rng.uniform(-0.08, 0.08),
        "track_position": rng.uniform(-0.35, 0.35),
        "track": track,
        "rpm": 4500 + rng.randint(-500, 700),
        "gear": 3,
    }


def run_dummy_once(
    config: dict[str, Any],
    config_path: Path,
    run_number: int,
) -> dict[str, Any]:
    seed = int(config.get("seed", 42)) + run_number
    rng = random.Random(seed)
    hyperparameters = config["hyperparameters"]
    agent = build_agent(hyperparameters)

    telemetry_path = (
        ROOT
        / "data"
        / "telemetry_logs"
        / f"{config['experiment_id']}_run_{run_number}.csv"
    )

    decision_latencies: list[float] = []
    speeds: list[float] = []
    crash_count = 0
    off_track_count = 0
    start_time = time.perf_counter()
    process = psutil.Process()
    cpu_start = psutil.cpu_percent(interval=None)

    with TelemetryLogger(telemetry_path) as telemetry:
        for step in range(120):
            state = dummy_track_state(step, rng)
            before_decision = time.perf_counter()
            action = agent.act(state)
            decision_latencies.append((time.perf_counter() - before_decision) * 1000)

            speed = float(state["speed"])
            speeds.append(speed)
            if abs(float(state["track_position"])) > 1.0:
                off_track_count += 1
            if action["brake"] > 0.35 and speed > hyperparameters["target_speed"] + 20:
                crash_count += 1

            telemetry.log(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "speed": round(speed, 3),
                    "steering": round(action["steer"], 4),
                    "throttle": round(action["accel"], 4),
                    "brake": round(action["brake"], 4),
                    "track_position": round(float(state["track_position"]), 4),
                    "angle": round(float(state["angle"]), 4),
                    "rpm": state["rpm"],
                    "gear": state["gear"],
                    "track_sensor_center": round(float(state["track"][9]), 3),
                    "lap_time": "",
                    "event": "dummy_step",
                }
            )

    runtime = time.perf_counter() - start_time
    cpu_end = psutil.cpu_percent(interval=None)
    memory_mb = process.memory_info().rss / (1024 * 1024)

    target_speed = float(hyperparameters["target_speed"])
    speed_bonus = max(0.0, target_speed - 70.0) * 0.45
    safety_penalty = crash_count * 8.0 + off_track_count * 2.0
    lap_time = 165.0 - speed_bonus + safety_penalty + rng.uniform(-4.0, 4.0)
    completed_lap = crash_count < 3

    return {
        "experiment_id": config["experiment_id"],
        "date_time": datetime.now(timezone.utc).isoformat(),
        "track": config["track"],
        "agent_version": config["agent_version"],
        "state_version": config["state_version"],
        "policy_version": config["policy_version"],
        "reward_version": config["reward_version"],
        "algorithm": config["algorithm"],
        "run_number": run_number,
        "seed": seed,
        "target_speed": hyperparameters["target_speed"],
        "steer_gain": hyperparameters["steer_gain"],
        "centering_gain": hyperparameters["centering_gain"],
        "brake_threshold": hyperparameters["brake_threshold"],
        "gentle_speed": hyperparameters["gentle_speed"],
        "sharp_speed": hyperparameters["sharp_speed"],
        "straight_speed": hyperparameters["straight_speed"],
        "acceleration_limit": hyperparameters["acceleration_limit"],
        "braking_intensity": hyperparameters["braking_intensity"],
        "best_lap_time": round(lap_time, 3),
        "average_lap_time": round(lap_time, 3),
        "completed_lap": int(completed_lap),
        "completion_rate": 1.0 if completed_lap else 0.0,
        "crash_count": crash_count,
        "off_track_count": off_track_count,
        "lap_time_variance": 0.0,
        "training_time_seconds": 0.0,
        "runtime_per_run_seconds": round(runtime, 4),
        "decision_latency_ms": round(statistics.mean(decision_latencies), 5),
        "cpu_usage": round((cpu_start + cpu_end) / 2.0, 2),
        "memory_usage": round(memory_mb, 2),
        "config_path": str(config_path),
        "telemetry_file": str(telemetry_path),
        "notes": "dummy run; replace simulator with live TORCS later",
    }


def summarise_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    lap_times = [float(row["average_lap_time"]) for row in rows]
    return {
        "best_lap_time": min(lap_times),
        "average_lap_time": statistics.mean(lap_times),
        "completion_rate": statistics.mean(float(row["completion_rate"]) for row in rows),
        "lap_time_variance": statistics.pvariance(lap_times) if len(lap_times) > 1 else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline_config.yaml")
    parser.add_argument("--dummy", action="store_true", help="Run dummy simulator mode")
    args = parser.parse_args()

    config_path = (ROOT / args.config).resolve()
    config = load_config(config_path)

    if not args.dummy:
        raise SystemExit(
            "Live TORCS mode is not connected yet. Use --dummy first, then replace "
            "run_dummy_once() with the real TORCS loop."
        )

    rows = [
        run_dummy_once(config, config_path, run_number)
        for run_number in range(1, int(config.get("num_runs", 1)) + 1)
    ]
    summary = summarise_rows(rows)
    for row in rows:
        row.update(summary)
        append_run_log(row, ROOT / "data" / "run_log.csv")

    print(f"Completed {len(rows)} dummy runs for {config['experiment_id']}")
    print(f"Best lap time: {summary['best_lap_time']:.3f}")
    print(f"Average lap time: {summary['average_lap_time']:.3f}")
    print(f"Completion rate: {summary['completion_rate']:.2f}")
    print(f"Lap-time variance: {summary['lap_time_variance']:.3f}")


if __name__ == "__main__":
    main()

