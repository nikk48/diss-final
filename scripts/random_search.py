"""Create random-search experiment configurations."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = ROOT / "configs" / "baseline_config.yaml"
OUTPUT_DIR = ROOT / "configs" / "generated_random"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    with BASE_CONFIG.open() as file:
        base = yaml.safe_load(file)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for index in range(1, args.trials + 1):
        target_speed = round(rng.uniform(70, 100), 3)
        gentle_speed = round(rng.uniform(35, 55), 3)
        config = dict(base)
        config["experiment_id"] = f"RAND_{index:03d}"
        config["algorithm"] = "random_search"
        config["seed"] = args.seed + index
        config["hyperparameters"] = dict(base["hyperparameters"])
        config["hyperparameters"].update(
            {
                "target_speed": target_speed,
                "gentle_speed": gentle_speed,
                "sharp_speed": round(max(25, gentle_speed - rng.uniform(8, 16)), 3),
                "straight_speed": round(target_speed + rng.uniform(10, 25), 3),
                "brake_threshold": round(rng.uniform(0.4, 0.8), 3),
                "steer_gain": round(rng.uniform(0.8, 1.3), 3),
            }
        )
        output_path = OUTPUT_DIR / f"{config['experiment_id']}.yaml"
        with output_path.open("w") as file:
            yaml.safe_dump(config, file, sort_keys=False)

    print(f"Created {args.trials} random-search configs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

