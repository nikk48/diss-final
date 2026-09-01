"""Generate controlled robustness stress-test configurations.

The generated configs are small one-parameter perturbations of an existing
baseline, grid, or Optuna configuration. They are intended for Part C
robustness evidence: the original configuration is the control, and each
stress config changes exactly one hyperparameter.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "configs" / "generated_stress"

STRESS_TESTS: dict[str, tuple[str, str, float]] = {
    "target_speed_plus_5_percent": ("target_speed", "percent", 1.05),
    "target_speed_minus_5_percent": ("target_speed", "percent", 0.95),
    "gentle_speed_plus_5_percent": ("gentle_speed", "percent", 1.05),
    "gentle_speed_minus_5_percent": ("gentle_speed", "percent", 0.95),
    "brake_threshold_plus_0_05": ("brake_threshold", "delta", 0.05),
    "brake_threshold_minus_0_05": ("brake_threshold", "delta", -0.05),
    "steer_gain_plus_0_05": ("steer_gain", "delta", 0.05),
    "steer_gain_minus_0_05": ("steer_gain", "delta", -0.05),
}
STRESS_ORDER = list(STRESS_TESTS)


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Config is not a YAML mapping: {path}")
    if "hyperparameters" not in config or not isinstance(config["hyperparameters"], dict):
        raise ValueError(f"Config has no hyperparameters mapping: {path}")
    return config


def stress_source(mode: str) -> str:
    if mode not in {"dummy", "live"}:
        raise ValueError("mode must be either dummy or live")
    return f"stress_{mode}"


def apply_stress_value(current_value: Any, operation: str, amount: float) -> float:
    value = float(current_value)
    if operation == "percent":
        stressed = value * amount
    elif operation == "delta":
        stressed = value + amount
    else:
        raise ValueError(f"Unsupported stress operation: {operation}")
    return round(stressed, 3)


def clamp_hyperparameter(parameter: str, value: float) -> float:
    if parameter == "brake_threshold":
        return min(1.0, max(0.0, value))
    if parameter in {"target_speed", "gentle_speed"}:
        return max(1.0, value)
    if parameter == "steer_gain":
        return max(0.0, value)
    return value


def generate_config(
    base_config: dict[str, Any],
    base_config_path: Path,
    stress_type: str,
    index: int,
    mode: str,
) -> dict[str, Any]:
    parameter, operation, amount = STRESS_TESTS[stress_type]
    hyperparameters = base_config["hyperparameters"]
    if parameter not in hyperparameters:
        raise KeyError(f"{parameter} is missing from {base_config_path}")

    config = copy.deepcopy(base_config)
    base_experiment_id = str(base_config["experiment_id"])
    stress_value = clamp_hyperparameter(
        parameter,
        apply_stress_value(hyperparameters[parameter], operation, amount),
    )

    config["experiment_id"] = f"{base_experiment_id}_STRESS_{index:03d}"
    config["base_experiment_id"] = base_experiment_id
    config["source"] = stress_source(mode)
    config["stress_type"] = stress_type
    config["stress_parameter"] = parameter
    config["stress_value"] = stress_value
    config["algorithm"] = f"{base_config.get('algorithm', 'rule_based')}_stress"
    config["num_runs"] = int(config.get("num_runs", 1))
    config["hyperparameters"] = copy.deepcopy(hyperparameters)
    config["hyperparameters"][parameter] = stress_value

    if parameter == "target_speed":
        config["hyperparameters"]["straight_speed"] = round(stress_value + 15.0, 3)
    elif parameter == "gentle_speed":
        config["hyperparameters"]["sharp_speed"] = round(max(25.0, stress_value - 10.0), 3)

    return config


def selected_stress_types(values: list[str] | None) -> list[str]:
    if not values:
        return list(STRESS_TESTS)
    unknown = [value for value in values if value not in STRESS_TESTS]
    if unknown:
        available = ", ".join(STRESS_TESTS)
        raise ValueError(f"Unknown stress type(s): {', '.join(unknown)}. Available: {available}")
    return values


def write_stress_configs(
    base_config_path: Path,
    mode: str,
    selected_only: list[str] | None,
    output_dir: Path,
) -> list[Path]:
    base_config = load_config(base_config_path)
    stress_types = selected_stress_types(selected_only)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_paths: list[Path] = []
    for stress_type in stress_types:
        index = STRESS_ORDER.index(stress_type) + 1
        config = generate_config(base_config, base_config_path, stress_type, index, mode)
        output_path = output_dir / f"{config['experiment_id']}.yaml"
        with output_path.open("w") as file:
            yaml.safe_dump(config, file, sort_keys=False)
        generated_paths.append(output_path)
    return generated_paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", default="configs/baseline_config.yaml")
    parser.add_argument("--mode", choices=["dummy", "live"], default="dummy")
    parser.add_argument("--output-dir", default="configs/generated_stress")
    parser.add_argument("--selected-only", nargs="*", default=None)
    args = parser.parse_args()

    base_config_path = (ROOT / args.base_config).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    try:
        generated_paths = write_stress_configs(
            base_config_path=base_config_path,
            mode=args.mode,
            selected_only=args.selected_only,
            output_dir=output_dir,
        )
    except (KeyError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"Created {len(generated_paths)} stress config(s) in {output_dir}")
    for path in generated_paths:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
