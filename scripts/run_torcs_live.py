"""Run the Part C baseline agent against live TORCS.

Usage:
1. Start TORCS through Wine.
2. Open a practice/new race with the SCR/server driver active.
3. Run this script from the Part_C_Experimentation virtual environment.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.baseline_rule_agent import build_agent  # noqa: E402
from scripts.result_utils import source_for_run, telemetry_path  # noqa: E402
from scripts.run_experiment import append_run_log, load_config, summarise_rows  # noqa: E402
from scripts.telemetry_logger import TelemetryLogger  # noqa: E402
from scripts.torcs_udp_client import TorcsUdpClient  # noqa: E402


GEAR_SPEEDS = [0, 50, 80, 120, 150, 200]


def shift_gear(speed: float) -> int:
    gear = 1
    for index, threshold in enumerate(GEAR_SPEEDS):
        if speed > threshold:
            gear = index + 1
    return min(gear, 6)


def torcs_state_to_agent_state(server_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "speed": server_state.get("speedX", 0.0),
        "angle": server_state.get("angle", 0.0),
        "track_position": server_state.get("trackPos", 0.0),
        "track": server_state.get("track", [200.0] * 19),
        "rpm": server_state.get("rpm", 0.0),
        "gear": server_state.get("gear", 1),
    }


def run_live_once(
    config: dict[str, Any],
    config_path: Path,
    run_number: int,
    host: str,
    port: int,
    sid: str,
    connect_attempts: int,
    socket_timeout: float,
    startup_timeout: float,
    max_missed_frames: int,
    max_steps: int,
    lap_distance: float,
) -> dict[str, Any]:
    hyperparameters = config["hyperparameters"]
    agent = build_agent(hyperparameters)
    algorithm = config.get("algorithm", "rule_based")
    source = source_for_run(algorithm, live=True)
    run_telemetry_path = telemetry_path(
        ROOT,
        config["experiment_id"],
        source,
        run_number,
    )

    process = psutil.Process()
    cpu_start = psutil.cpu_percent(interval=None)
    start_time = time.perf_counter()
    decision_latencies: list[float] = []
    lap_times: list[float] = []
    speeds: list[float] = []
    crash_count = 0
    off_track_count = 0
    completed_lap = False
    previous_damage = 0.0
    current_lap_time = 0.0

    client = TorcsUdpClient(
        host=host,
        port=port,
        sid=sid,
        timeout=socket_timeout,
        connect_attempts=connect_attempts,
    )
    try:
        with TelemetryLogger(run_telemetry_path) as telemetry:
            step = 0
            missed_frames = 0
            startup_deadline = time.perf_counter() + startup_timeout
            while step < max_steps:
                if not client.get_servers_input():
                    if not speeds and time.perf_counter() < startup_deadline:
                        client.respond_to_server()
                        print("Waiting for first TORCS telemetry frame...")
                        continue
                    missed_frames += 1
                    if missed_frames < max_missed_frames:
                        continue
                    print(
                        "No TORCS telemetry received after "
                        f"{missed_frames} missed frame checks; stopping live run."
                    )
                    break
                missed_frames = 0

                server_state = client.S.d
                agent_state = torcs_state_to_agent_state(server_state)
                before_decision = time.perf_counter()
                action = agent.act(agent_state)
                decision_latencies.append((time.perf_counter() - before_decision) * 1000)

                speed = float(server_state.get("speedX", 0.0))
                track_pos = float(server_state.get("trackPos", 0.0))
                damage = float(server_state.get("damage", 0.0))
                current_lap_time = float(server_state.get("curLapTime", 0.0))
                dist_raced = float(server_state.get("distRaced", 0.0))
                track = server_state.get("track", [0.0] * 19)
                center_sensor = track[9] if isinstance(track, list) and len(track) > 9 else ""
                event = "step"

                if abs(track_pos) > 1.0:
                    off_track_count += 1
                    event = "off_track"
                if damage > previous_damage:
                    crash_count += 1
                    event = "damage"
                previous_damage = damage
                speeds.append(speed)
                if current_lap_time > 0:
                    lap_times.append(current_lap_time)

                client.R.d["steer"] = action["steer"]
                client.R.d["accel"] = action["accel"]
                client.R.d["brake"] = action["brake"]
                client.R.d["gear"] = shift_gear(speed)
                client.respond_to_server()

                telemetry.log(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "speed": round(speed, 3),
                        "steering": round(action["steer"], 4),
                        "throttle": round(action["accel"], 4),
                        "brake": round(action["brake"], 4),
                        "track_position": round(track_pos, 4),
                        "angle": round(float(server_state.get("angle", 0.0)), 4),
                        "rpm": server_state.get("rpm", ""),
                        "gear": client.R.d["gear"],
                        "track_sensor_center": center_sensor,
                        "lap_time": round(current_lap_time, 4),
                        "event": event,
                    }
                )

                if dist_raced >= lap_distance:
                    completed_lap = True
                    print(f"Lap distance reached at step {step}: {dist_raced:.2f} m")
                    break
                if dist_raced > 10 and speed < 1.0 and step > 100:
                    print("Car appears stopped after race start; ending run.")
                    break
                step += 1
    finally:
        client.shutdown()

    runtime = time.perf_counter() - start_time
    cpu_end = psutil.cpu_percent(interval=None)
    memory_mb = process.memory_info().rss / (1024 * 1024)
    best_lap_time = current_lap_time if current_lap_time > 0 else 0.0

    return {
        "experiment_id": config["experiment_id"],
        "date_time": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "track": config["track"],
        "agent_version": config["agent_version"],
        "state_version": config["state_version"],
        "policy_version": config["policy_version"],
        "reward_version": config["reward_version"],
        "algorithm": algorithm,
        "run_number": run_number,
        "seed": int(config.get("seed", 42)) + run_number,
        "target_speed": hyperparameters["target_speed"],
        "steer_gain": hyperparameters["steer_gain"],
        "centering_gain": hyperparameters["centering_gain"],
        "brake_threshold": hyperparameters["brake_threshold"],
        "gentle_speed": hyperparameters["gentle_speed"],
        "sharp_speed": hyperparameters["sharp_speed"],
        "straight_speed": hyperparameters["straight_speed"],
        "acceleration_limit": hyperparameters["acceleration_limit"],
        "braking_intensity": hyperparameters["braking_intensity"],
        "best_lap_time": round(best_lap_time, 3),
        "average_lap_time": round(best_lap_time, 3),
        "completed_lap": int(completed_lap),
        "completion_rate": 1.0 if completed_lap else 0.0,
        "crash_count": crash_count,
        "off_track_count": off_track_count,
        "lap_time_variance": 0.0,
        "training_time_seconds": 0.0,
        "runtime_per_run_seconds": round(runtime, 4),
        "decision_latency_ms": round(statistics.mean(decision_latencies), 5)
        if decision_latencies
        else 0.0,
        "cpu_usage": round((cpu_start + cpu_end) / 2.0, 2),
        "memory_usage": round(memory_mb, 2),
        "config_path": str(config_path),
        "telemetry_file": str(run_telemetry_path),
        "notes": "live TORCS run",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline_config.yaml")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--sid", default="SCR")
    parser.add_argument("--connect-attempts", type=int, default=30)
    parser.add_argument("--socket-timeout", type=float, default=2.0)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--max-missed-frames", type=int, default=25)
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--lap-distance", type=float, default=3608.45)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument(
        "--run-start",
        type=int,
        default=1,
        help="First run number to log; useful when repeating live runs one race at a time.",
    )
    args = parser.parse_args()

    config_path = (ROOT / args.config).resolve()
    config = load_config(config_path)

    rows = [
        run_live_once(
            config=config,
            config_path=config_path,
            run_number=run_number,
            host=args.host,
            port=args.port,
            sid=args.sid,
            connect_attempts=args.connect_attempts,
            socket_timeout=args.socket_timeout,
            startup_timeout=args.startup_timeout,
            max_missed_frames=args.max_missed_frames,
            max_steps=args.max_steps,
            lap_distance=args.lap_distance,
        )
        for run_number in range(args.run_start, args.run_start + args.runs)
    ]

    summary = summarise_rows(rows)
    for row in rows:
        row.update(summary)
        append_run_log(row, ROOT / "data" / "run_log.csv")

    print(f"Completed {len(rows)} live TORCS run(s) for {config['experiment_id']}")
    print(f"Best lap time: {summary['best_lap_time']:.3f}")
    print(f"Average lap time: {summary['average_lap_time']:.3f}")
    print(f"Completion rate: {summary['completion_rate']:.2f}")


if __name__ == "__main__":
    main()
