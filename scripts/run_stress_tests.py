"""Run robustness stress tests in dummy or live TORCS mode."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_stress_configs import write_stress_configs  # noqa: E402
from scripts.run_experiment import append_run_log, load_config, run_dummy_once, summarise_rows  # noqa: E402
from scripts.run_torcs_live import run_live_once  # noqa: E402


def run_one_config(
    config_path: Path,
    mode: str,
    runs: int,
    host: str,
    port: int,
    sid: str,
    connect_attempts: int,
    socket_timeout: float,
    startup_timeout: float,
    max_missed_frames: int,
    max_steps: int,
    lap_distance: float,
) -> list[dict[str, Any]]:
    config = load_config(config_path)
    config["source"] = f"stress_{mode}"

    if mode == "dummy":
        rows = [
            run_dummy_once(config=config, config_path=config_path, run_number=run_number)
            for run_number in range(1, runs + 1)
        ]
    else:
        rows = [
            run_live_once(
                config=config,
                config_path=config_path,
                run_number=run_number,
                host=host,
                port=port,
                sid=sid,
                connect_attempts=connect_attempts,
                socket_timeout=socket_timeout,
                startup_timeout=startup_timeout,
                max_missed_frames=max_missed_frames,
                max_steps=max_steps,
                lap_distance=lap_distance,
            )
            for run_number in range(1, runs + 1)
        ]

    summary = summarise_rows(rows)
    for row in rows:
        row.update(summary)
        row["source"] = f"stress_{mode}"
        row["base_experiment_id"] = config.get("base_experiment_id", "")
        row["stress_type"] = config.get("stress_type", "")
        row["stress_parameter"] = config.get("stress_parameter", "")
        row["stress_value"] = config.get("stress_value", "")
        row["notes"] = (
            f"{mode} stress test; "
            f"base_experiment_id={config.get('base_experiment_id', '')}; "
            f"stress_type={config.get('stress_type', '')}; "
            f"stress_parameter={config.get('stress_parameter', '')}; "
            f"stress_value={config.get('stress_value', '')}"
        )
        append_run_log(row, ROOT / "data" / "run_log.csv")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dummy", "live"], required=True)
    parser.add_argument("--base-config", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--sid", default="SCR")
    parser.add_argument("--connect-attempts", type=int, default=60)
    parser.add_argument("--socket-timeout", type=float, default=2.0)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--max-missed-frames", type=int, default=60)
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--lap-distance", type=float, default=3608.45)
    parser.add_argument("--selected-only", nargs="*", default=None)
    args = parser.parse_args()

    base_config_path = (ROOT / args.base_config).resolve()
    generated_paths = write_stress_configs(
        base_config_path=base_config_path,
        mode=args.mode,
        selected_only=args.selected_only,
        output_dir=ROOT / "configs" / "generated_stress",
    )

    total_rows = 0
    for config_path in generated_paths:
        rows = run_one_config(
            config_path=config_path,
            mode=args.mode,
            runs=args.runs,
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
        total_rows += len(rows)
        config = load_config(config_path)
        print(
            f"{config['experiment_id']}: {len(rows)} {args.mode} run(s), "
            f"stress={config['stress_type']}"
        )

    print(
        f"Completed {total_rows} stress-test run(s) from "
        f"{len(generated_paths)} generated config(s)."
    )


if __name__ == "__main__":
    main()
