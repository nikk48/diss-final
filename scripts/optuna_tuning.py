"""Optional Optuna scaffold.

Use this only after TORCS execution is stable. For now this creates an objective
shape that can call `run_experiment.py` later.
"""

from __future__ import annotations


def objective_score(
    lap_time: float,
    crash_count: int,
    off_track_count: int,
    runtime_seconds: float,
) -> float:
    return (
        lap_time
        + crash_count * 12.0
        + off_track_count * 3.0
        + runtime_seconds * 0.05
    )


def main() -> None:
    print("Optuna scaffold ready.")
    print("Connect this to live TORCS after grid/random search are stable.")
    print(
        "Objective: minimise lap_time + crash_penalty + offtrack_penalty "
        "+ runtime_penalty."
    )


if __name__ == "__main__":
    main()

