"""Replay the best Optuna configuration for repeated dummy or live runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_experiment import append_run_log, load_config, run_dummy_once, summarise_rows  # noqa: E402
from scripts.run_torcs_live import run_live_once  # noqa: E402


RUN_LOG = ROOT / "data" / "run_log.csv"
RESULTS_DIR = ROOT / "results"
OPTUNA_CONFIG_DIR = ROOT / "configs" / "generated_optuna"
DEFAULT_BEST_CONFIG = RESULTS_DIR / "optuna_best_config.yaml"
OPTUNA_TRIALS = RESULTS_DIR / "optuna_trials.csv"
REPLAY_CONFIG = OPTUNA_CONFIG_DIR / "OPTUNA_BEST_REPLAY.yaml"


def resolve_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def replay_source(mode: str) -> str:
    return "optuna_live_replay" if mode == "live" else "optuna_dummy_replay"


def source_best_config(explicit_path: str | None) -> Path:
    if explicit_path:
        path = resolve_path(explicit_path)
        if not path.exists():
            raise SystemExit(f"Requested best config does not exist: {path}")
        return path

    if DEFAULT_BEST_CONFIG.exists():
        return DEFAULT_BEST_CONFIG

    if OPTUNA_TRIALS.exists() and OPTUNA_TRIALS.stat().st_size > 0:
        trials = pd.read_csv(OPTUNA_TRIALS)
        if "objective_score" in trials.columns and "config_path" in trials.columns:
            trials = trials.sort_values("objective_score")
            for raw_path in trials["config_path"].dropna():
                path = resolve_path(str(raw_path))
                if path.exists():
                    return path

    generated = sorted(
        OPTUNA_CONFIG_DIR.glob("OPTUNA_*.yaml"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    generated = [path for path in generated if path.name != REPLAY_CONFIG.name]
    if generated:
        return generated[0]

    raise SystemExit(
        "No Optuna best config found. Run scripts/optuna_tuning.py first, "
        "or pass --best-config path/to/config.yaml."
    )


def build_replay_config(best_config: dict[str, Any], mode: str) -> dict[str, Any]:
    base_experiment_id = str(best_config.get("experiment_id", "UNKNOWN_OPTUNA_TRIAL"))
    replay_config = dict(best_config)
    replay_config["experiment_id"] = "OPTUNA_BEST_REPLAY"
    replay_config["base_experiment_id"] = base_experiment_id
    replay_config["source"] = replay_source(mode)
    replay_config["algorithm"] = "optuna_replay"
    replay_config["hyperparameters"] = dict(best_config["hyperparameters"])
    return replay_config


def save_replay_config(config: dict[str, Any]) -> Path:
    OPTUNA_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with REPLAY_CONFIG.open("w") as file:
        yaml.safe_dump(config, file, sort_keys=False)
    return REPLAY_CONFIG


def run_replay_rows(
    config: dict[str, Any],
    config_path: Path,
    mode: str,
    runs: int,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    if mode == "dummy":
        return [
            run_dummy_once(config=config, config_path=config_path, run_number=run_number)
            for run_number in range(1, runs + 1)
        ]

    return [
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
        for run_number in range(1, runs + 1)
    ]


def append_replay_rows(
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    mode: str,
) -> dict[str, float]:
    summary = summarise_rows(rows)
    source = replay_source(mode)
    for row in rows:
        row.update(summary)
        row["source"] = source
        row["base_experiment_id"] = config.get("base_experiment_id", "")
        row["notes"] = "Repeated replay of best Optuna configuration"
        append_run_log(row, RUN_LOG)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dummy", "live"], default="dummy")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--best-config", default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--sid", default="SCR")
    parser.add_argument("--connect-attempts", type=int, default=60)
    parser.add_argument("--socket-timeout", type=float, default=2.0)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--max-missed-frames", type=int, default=60)
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--lap-distance", type=float, default=3608.45)
    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")

    best_config_path = source_best_config(args.best_config)
    best_config = load_config(best_config_path)
    if "hyperparameters" not in best_config:
        raise SystemExit(f"Best config has no hyperparameters section: {best_config_path}")

    replay_config = build_replay_config(best_config, args.mode)
    replay_config_path = save_replay_config(replay_config)

    rows = run_replay_rows(
        config=replay_config,
        config_path=replay_config_path,
        mode=args.mode,
        runs=args.runs,
        args=args,
    )
    summary = append_replay_rows(rows, replay_config, args.mode)

    print(f"Best Optuna source config: {best_config_path}")
    print(f"Replay config written: {replay_config_path}")
    print(f"Completed {len(rows)} {args.mode} replay run(s) for OPTUNA_BEST_REPLAY")
    print(f"Source label: {replay_source(args.mode)}")
    print(f"Base experiment: {replay_config['base_experiment_id']}")
    print(f"Best lap time: {summary['best_lap_time']:.3f}")
    print(f"Average lap time: {summary['average_lap_time']:.3f}")
    print(f"Completion rate: {summary['completion_rate']:.2f}")


if __name__ == "__main__":
    main()
