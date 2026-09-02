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

## fig_05_live_robustness

Figure 5. Robustness view for live Part C evidence: lower lap-time spread and high completion rate indicate more repeatable behaviour in the limited live sample.

- PNG: `results/dissertation_visuals/fig_05_live_robustness.png`
- SVG: `results/dissertation_visuals/fig_05_live_robustness.svg`
- Data source(s): results/robustness_summary.csv

## fig_06_live_computational_efficiency

Figure 6. Computational-efficiency evidence for live Part C methods, showing runtime and decision latency without mixing dummy or imported Part B rows.

- PNG: `results/dissertation_visuals/fig_06_live_computational_efficiency.png`
- SVG: `results/dissertation_visuals/fig_06_live_computational_efficiency.svg`
- Data source(s): results/computational_efficiency_summary.csv

## fig_07_hyperparameter_sensitivity

Figure 7. Exploratory sensitivity signals linking selected hyperparameters to mean lap time. The small live sample supports cautious discussion only and requires further testing before strong claims.

- PNG: `results/dissertation_visuals/fig_07_hyperparameter_sensitivity.png`
- SVG: `results/dissertation_visuals/fig_07_hyperparameter_sensitivity.svg`
- Data source(s): results/hyperparameter_sensitivity.csv

## fig_08_live_telemetry_speed_profiles

Figure 8. Speed profiles from representative valid live telemetry files, showing how the Part C controller behaves over a lap.

- PNG: `results/dissertation_visuals/fig_08_live_telemetry_speed_profiles.png`
- SVG: `results/dissertation_visuals/fig_08_live_telemetry_speed_profiles.svg`
- Data source(s): data/telemetry_logs/EXP_001_live_run_1_20260831_181130_629284.csv; data/telemetry_logs/GRID_040_grid_live_run_1_20260831_190630_762814.csv; data/telemetry_logs/OPTUNA_LIVE_001_optuna_live_run_1_20260831_190722_745120.csv
