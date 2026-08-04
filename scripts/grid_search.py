"""Create simple grid-search experiment configurations."""

from __future__ import annotations

import itertools
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = ROOT / "configs" / "baseline_config.yaml"
OUTPUT_DIR = ROOT / "configs" / "generated_grid"


def main() -> None:
    with BASE_CONFIG.open() as file:
        base = yaml.safe_load(file)

    target_speeds = [70, 80, 90]
    gentle_speeds = [40, 45, 50]
    brake_thresholds = [0.5, 0.6, 0.7]
    steer_gains = [0.8, 1.0, 1.2]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for count, values in enumerate(
        itertools.product(target_speeds, gentle_speeds, brake_thresholds, steer_gains),
        start=1,
    ):
        target_speed, gentle_speed, brake_threshold, steer_gain = values
        config = dict(base)
        config["experiment_id"] = f"GRID_{count:03d}"
        config["algorithm"] = "grid_search"
        config["hyperparameters"] = dict(base["hyperparameters"])
        config["hyperparameters"].update(
            {
                "target_speed": target_speed,
                "gentle_speed": gentle_speed,
                "sharp_speed": max(25, gentle_speed - 10),
                "straight_speed": target_speed + 15,
                "brake_threshold": brake_threshold,
                "steer_gain": steer_gain,
            }
        )
        output_path = OUTPUT_DIR / f"{config['experiment_id']}.yaml"
        with output_path.open("w") as file:
            yaml.safe_dump(config, file, sort_keys=False)

    print(f"Created {count} grid-search configs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

