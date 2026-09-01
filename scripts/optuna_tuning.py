"""Run small Optuna tuning experiments for the Part C framework."""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_experiment import (  # noqa: E402
    append_run_log,
    load_config,
    run_dummy_once,
    summarise_rows,
)


BASE_CONFIG = ROOT / "configs" / "baseline_config.yaml"
SEARCH_SPACE = ROOT / "configs" / "search_space.yaml"
RUN_LOG = ROOT / "data" / "run_log.csv"
RESULTS_DIR = ROOT / "results"
TRIAL_CONFIG_DIR = ROOT / "configs" / "generated_optuna"


def objective_score(
    lap_time: float,
    completion_rate: float,
    crash_count: float,
    off_track_count: float,
    runtime_seconds: float,
) -> float:
    return (
        lap_time
        + (1.0 - completion_rate) * 40.0
        + crash_count * 12.0
        + off_track_count * 3.0
        + runtime_seconds * 0.05
    )


def profile_ranges(search_space: dict[str, Any], profile: str) -> dict[str, tuple[float, float]]:
    ranges = search_space.get("random_search_ranges", {})
    selected = {
        "target_speed": tuple(ranges.get("target_speed", [70, 100])),
        "gentle_speed": tuple(ranges.get("gentle_speed", [30, 55])),
        "brake_threshold": tuple(ranges.get("brake_threshold", [0.4, 0.8])),
        "steer_gain": tuple(ranges.get("steer_gain", [0.8, 1.3])),
    }
    if profile.lower() in {"core", "coresmall", "core_small"}:
        selected["target_speed"] = (70.0, 90.0)
        selected["gentle_speed"] = (35.0, 50.0)
        selected["brake_threshold"] = (0.5, 0.7)
        selected["steer_gain"] = (0.8, 1.2)
    return {key: (float(value[0]), float(value[1])) for key, value in selected.items()}


def build_trial_config(
    base: dict[str, Any],
    trial_number: int,
    params: dict[str, float],
    mode: str,
    seed: int,
) -> dict[str, Any]:
    config = dict(base)
    config["experiment_id"] = f"OPTUNA_{mode.upper()}_{trial_number:03d}"
    config["algorithm"] = "optuna"
    config["seed"] = seed + trial_number * 100
    config["hyperparameters"] = dict(base["hyperparameters"])
    config["hyperparameters"].update(
        {
            "target_speed": round(params["target_speed"], 3),
            "gentle_speed": round(params["gentle_speed"], 3),
            "sharp_speed": round(max(25.0, params["gentle_speed"] - 10.0), 3),
            "straight_speed": round(params["target_speed"] + 15.0, 3),
            "brake_threshold": round(params["brake_threshold"], 3),
            "steer_gain": round(params["steer_gain"], 3),
        }
    )
    return config


def save_trial_config(config: dict[str, Any]) -> Path:
    TRIAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = TRIAL_CONFIG_DIR / f"{config['experiment_id']}.yaml"
    with path.open("w") as file:
        yaml.safe_dump(config, file, sort_keys=False)
    return path


def run_rows(
    config: dict[str, Any],
    config_path: Path,
    mode: str,
    runs: int,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    if mode == "dummy":
        return [
            run_dummy_once(config, config_path, run_number)
            for run_number in range(1, runs + 1)
        ]

    from scripts.run_torcs_live import run_live_once  # noqa: WPS433

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


def append_rows_with_summary(
    rows: list[dict[str, Any]],
    trial_number: int,
    mode: str,
) -> dict[str, float]:
    summary = summarise_rows(rows)
    for row in rows:
        row.update(summary)
        row["notes"] = f"optuna {mode} trial {trial_number}; {row.get('notes', '')}"
        append_run_log(row, RUN_LOG)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dummy", "live"], default="dummy")
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--profile", default="core")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--config", default=str(BASE_CONFIG))
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--sid", default="SCR")
    parser.add_argument("--connect-attempts", type=int, default=30)
    parser.add_argument("--socket-timeout", type=float, default=2.0)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--max-missed-frames", type=int, default=25)
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--lap-distance", type=float, default=3608.45)
    args = parser.parse_args()

    try:
        import optuna
    except ImportError as exc:
        raise SystemExit(
            "Optuna is not installed. Run: pip install -r requirements.txt"
        ) from exc

    base_path = Path(args.config).expanduser()
    if not base_path.is_absolute():
        base_path = (ROOT / base_path).resolve()
    base = load_config(base_path)
    with SEARCH_SPACE.open() as file:
        search_space = yaml.safe_load(file)
    ranges = profile_ranges(search_space, args.profile)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    trial_records: list[dict[str, Any]] = []
    sampler = optuna.samplers.TPESampler(seed=args.seed)
    study = optuna.create_study(direction="minimize", sampler=sampler)

    def objective(trial: Any) -> float:
        params = {
            "target_speed": trial.suggest_float("target_speed", *ranges["target_speed"]),
            "gentle_speed": trial.suggest_float("gentle_speed", *ranges["gentle_speed"]),
            "brake_threshold": trial.suggest_float(
                "brake_threshold",
                *ranges["brake_threshold"],
            ),
            "steer_gain": trial.suggest_float("steer_gain", *ranges["steer_gain"]),
        }
        trial_number = trial.number + 1
        config = build_trial_config(base, trial_number, params, args.mode, args.seed)
        config_path = save_trial_config(config)
        rows = run_rows(config, config_path, args.mode, args.runs, args)
        summary = append_rows_with_summary(rows, trial_number, args.mode)
        score = objective_score(
            lap_time=float(summary["average_lap_time"]),
            completion_rate=float(summary["completion_rate"]),
            crash_count=statistics.mean(float(row["crash_count"]) for row in rows),
            off_track_count=statistics.mean(float(row["off_track_count"]) for row in rows),
            runtime_seconds=statistics.mean(
                float(row["runtime_per_run_seconds"]) for row in rows
            ),
        )
        trial_records.append(
            {
                "trial": trial_number,
                "mode": args.mode,
                "profile": args.profile,
                "experiment_id": config["experiment_id"],
                "target_speed": config["hyperparameters"]["target_speed"],
                "gentle_speed": config["hyperparameters"]["gentle_speed"],
                "brake_threshold": config["hyperparameters"]["brake_threshold"],
                "steer_gain": config["hyperparameters"]["steer_gain"],
                "runs": args.runs,
                "best_lap_time": summary["best_lap_time"],
                "average_lap_time": summary["average_lap_time"],
                "completion_rate": summary["completion_rate"],
                "objective_score": score,
                "config_path": str(config_path),
            }
        )
        return score

    study.optimize(objective, n_trials=args.trials)

    trials = pd.DataFrame(trial_records).sort_values("objective_score")
    trials.to_csv(RESULTS_DIR / "optuna_trials.csv", index=False)

    best_config_path = Path(trials.iloc[0]["config_path"])
    best_config = load_config(best_config_path)
    with (RESULTS_DIR / "optuna_best_config.yaml").open("w") as file:
        yaml.safe_dump(best_config, file, sort_keys=False)

    print(f"Completed {args.trials} Optuna {args.mode} trial(s).")
    print(f"Best experiment: {trials.iloc[0]['experiment_id']}")
    print(f"Best objective score: {trials.iloc[0]['objective_score']:.3f}")
    print(f"Trials output: {RESULTS_DIR / 'optuna_trials.csv'}")
    print(f"Best config output: {RESULTS_DIR / 'optuna_best_config.yaml'}")


if __name__ == "__main__":
    main()
