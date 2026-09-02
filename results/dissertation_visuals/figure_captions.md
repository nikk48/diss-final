# Dissertation Visual Captions

## fig_01_part_c_framework

Figure 1. Overview of the Part C contribution: controlled configuration files drive repeatable TORCS or dummy experiments, which produce telemetry, run logs, analysis tables and reproducibility evidence.

- PNG: `results/dissertation_visuals/fig_01_part_c_framework.png`
- SVG: `results/dissertation_visuals/fig_01_part_c_framework.svg`
- Data source(s): Repository structure, data/run_log.csv, analysis scripts

## fig_02_evidence_source_map

Figure 2. Evidence streams are separated before comparison: dummy rows validate the pipeline, live TORCS rows support Part C performance claims, stress rows support robustness exploration, and Part B rows are imported comparator artefacts only.

- PNG: `results/dissertation_visuals/fig_02_evidence_source_map.png`
- SVG: `results/dissertation_visuals/fig_02_evidence_source_map.svg`
- Data source(s): results/summary_dummy.csv, results/summary_live.csv, results/summary_stress.csv, results/summary_partb.csv, results/comparison_summary.csv

## fig_03_live_lap_time_comparison

Lower lap time is better. This figure compares only Part C live TORCS configurations, excluding dummy validation and imported Part B evidence.

- PNG: `results/dissertation_visuals/fig_03_live_lap_time_comparison.png`
- SVG: `results/dissertation_visuals/fig_03_live_lap_time_comparison.svg`
- Data source(s): results/summary_live.csv

## fig_04_improvement_vs_baseline

Figure 4. Improvement is calculated as verified baseline mean lap time minus experiment mean lap time. Positive values indicate faster live TORCS performance than the EXP_001 rule-based baseline.

- PNG: `results/dissertation_visuals/fig_04_improvement_vs_baseline.png`
- SVG: `results/dissertation_visuals/fig_04_improvement_vs_baseline.svg`
- Data source(s): results/summary_live.csv

## fig_05_robustness_reproducibility_summary

Repeated runs under identical conditions support reproducibility. Broader robustness requires stress tests or varied conditions.

- PNG: `results/dissertation_visuals/fig_05_robustness_reproducibility_summary.png`
- SVG: `results/dissertation_visuals/fig_05_robustness_reproducibility_summary.svg`
- Data source(s): results/robustness_summary.csv

## fig_06_live_computational_efficiency

Figure 6. Computational-efficiency indicators for live Part C experiments, comparing the verified rule-based baseline, grid-search configurations, and Optuna live configuration without mixing dummy or imported Part B runtime evidence.

- PNG: `results/dissertation_visuals/fig_06_live_computational_efficiency.png`
- SVG: `results/dissertation_visuals/fig_06_live_computational_efficiency.svg`
- Data source(s): results/computational_efficiency_summary.csv

## fig_07a_target_speed_sensitivity

Figure 7a. Target speed plotted against mean lap time for live Part C experiments. This is an exploratory sensitivity visual based on a small live sample and should not be interpreted as statistical proof.

- PNG: `results/dissertation_visuals/fig_07a_target_speed_sensitivity.png`
- SVG: `results/dissertation_visuals/fig_07a_target_speed_sensitivity.svg`
- Data source(s): results/hyperparameter_sensitivity.csv

## fig_07b_gentle_speed_sensitivity

Figure 7b. Gentle speed plotted against mean lap time for live Part C experiments. This is an exploratory sensitivity visual based on a small live sample and should not be interpreted as statistical proof.

- PNG: `results/dissertation_visuals/fig_07b_gentle_speed_sensitivity.png`
- SVG: `results/dissertation_visuals/fig_07b_gentle_speed_sensitivity.svg`
- Data source(s): results/hyperparameter_sensitivity.csv

## fig_07c_brake_threshold_sensitivity

Figure 7c. Brake threshold plotted against mean lap time for live Part C experiments. This is an exploratory sensitivity visual based on a small live sample and should not be interpreted as statistical proof.

- PNG: `results/dissertation_visuals/fig_07c_brake_threshold_sensitivity.png`
- SVG: `results/dissertation_visuals/fig_07c_brake_threshold_sensitivity.svg`
- Data source(s): results/hyperparameter_sensitivity.csv

## fig_07d_steer_gain_sensitivity

Figure 7d. Steer gain plotted against mean lap time for live Part C experiments. This is an exploratory sensitivity visual based on a small live sample and should not be interpreted as statistical proof.

- PNG: `results/dissertation_visuals/fig_07d_steer_gain_sensitivity.png`
- SVG: `results/dissertation_visuals/fig_07d_steer_gain_sensitivity.svg`
- Data source(s): results/hyperparameter_sensitivity.csv

## fig_08_optuna_trial_history

Optuna was used as an automated hyperparameter optimisation extension. Lower objective score indicates better balance of lap time, completion and penalty metrics.

- PNG: `results/dissertation_visuals/fig_08_optuna_trial_history.png`
- SVG: `results/dissertation_visuals/fig_08_optuna_trial_history.svg`
- Data source(s): results/optuna_trials.csv

## fig_09a_speed_profile_baseline_vs_optuna

These plots show how the driving behaviour differs over the lap, not just the final lap time.

- PNG: `results/dissertation_visuals/fig_09a_speed_profile_baseline_vs_optuna.png`
- SVG: `results/dissertation_visuals/fig_09a_speed_profile_baseline_vs_optuna.svg`
- Data source(s): data/telemetry_logs/EXP_001_live_run_1_20260831_181130_629284.csv; data/telemetry_logs/OPTUNA_LIVE_001_optuna_live_run_1_20260831_190722_745120.csv

## fig_09b_steering_profile_baseline_vs_optuna

These plots show how the driving behaviour differs over the lap, not just the final lap time.

- PNG: `results/dissertation_visuals/fig_09b_steering_profile_baseline_vs_optuna.png`
- SVG: `results/dissertation_visuals/fig_09b_steering_profile_baseline_vs_optuna.svg`
- Data source(s): data/telemetry_logs/EXP_001_live_run_1_20260831_181130_629284.csv; data/telemetry_logs/OPTUNA_LIVE_001_optuna_live_run_1_20260831_190722_745120.csv

## fig_09c_throttle_brake_profile_baseline_vs_optuna

These plots show how the driving behaviour differs over the lap, not just the final lap time.

- PNG: `results/dissertation_visuals/fig_09c_throttle_brake_profile_baseline_vs_optuna.png`
- SVG: `results/dissertation_visuals/fig_09c_throttle_brake_profile_baseline_vs_optuna.svg`
- Data source(s): data/telemetry_logs/EXP_001_live_run_1_20260831_181130_629284.csv; data/telemetry_logs/OPTUNA_LIVE_001_optuna_live_run_1_20260831_190722_745120.csv

## fig_10_racing_line_or_track_position_map

Figure 10. Telemetry does not include x/y position coordinates, so this is a track-position profile rather than a real racing-line map.

- PNG: `results/dissertation_visuals/fig_10_racing_line_or_track_position_map.png`
- SVG: `results/dissertation_visuals/fig_10_racing_line_or_track_position_map.svg`
- Data source(s): data/telemetry_logs/EXP_001_live_run_1_20260831_181130_629284.csv; data/telemetry_logs/OPTUNA_LIVE_001_optuna_live_run_1_20260831_190722_745120.csv

## fig_11_dummy_to_live_transfer_gap

Configurations favoured by dummy validation did not transfer to better live TORCS performance. The dummy panel is pipeline-validation evidence, while the live panel shows Part C simulator evidence for the same named configurations.

- PNG: `results/dissertation_visuals/fig_11_dummy_to_live_transfer_gap.png`
- SVG: `results/dissertation_visuals/fig_11_dummy_to_live_transfer_gap.svg`
- Data source(s): results/summary_dummy.csv; results/summary_live.csv
