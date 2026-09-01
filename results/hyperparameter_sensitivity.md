# Hyperparameter Sensitivity

Source file: `/Users/thenotoriouscode/Desktop/gaurav-diss-final/data/run_log.csv`
Filter: mode=`live`, source=`all`, valid rows=`14`.

The associations below are directional signals only. They do not claim statistical significance because the number of live TORCS runs is small.

## Directional Associations

| hyperparameter | sample_size | spearman_rho | assessment |
| --- | --- | --- | --- |
| target_speed | 4 | 0.7746 | target_speed: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. |
| gentle_speed | 4 | -0.9487 | gentle_speed: higher values appear associated with better lap time in this limited sample; requires further testing. |
| brake_threshold | 4 | -0.9487 | brake_threshold: higher values appear associated with better lap time in this limited sample; requires further testing. |
| steer_gain | 4 | 0.2 | steer_gain: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. |

## Aggregated Experiments

| experiment_id | source | target_speed | gentle_speed | brake_threshold | steer_gain | mean_lap_time | best_lap_time | completion_rate | mean_runtime | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPTUNA_LIVE_001 | optuna_live | 77.491 | 49.261 | 0.646 | 1.039 | 195.526 | 195.526 | 1 | 12.3151 | Best aggregated lap time in the filtered sample. Associations are exploratory: target_speed: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. gentle_speed: higher values appear associated with better lap time in this limited sample; requires further testing. brake_threshold: higher values appear associated with better lap time in this limited sample; requires further testing. steer_gain: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. |
| EXP_001 | live | 80 | 45 | 0.6 | 1 | 196.466 | 195.766 | 1 | 87.1456 | Better-than-median lap time in the filtered sample. Associations are exploratory: target_speed: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. gentle_speed: higher values appear associated with better lap time in this limited sample; requires further testing. brake_threshold: higher values appear associated with better lap time in this limited sample; requires further testing. steer_gain: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. |
| GRID_040 | grid_live | 80 | 45 | 0.6 | 0.8 | 198.906 | 198.906 | 1 | 12.5123 | Slower-than-median lap time in the filtered sample. Associations are exploratory: target_speed: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. gentle_speed: higher values appear associated with better lap time in this limited sample; requires further testing. brake_threshold: higher values appear associated with better lap time in this limited sample; requires further testing. steer_gain: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. |
| GRID_030 | grid_live | 80 | 40 | 0.5 | 1.2 | 199.806 | 199.806 | 1 | 12.3935 | Slower-than-median lap time in the filtered sample. Associations are exploratory: target_speed: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. gentle_speed: higher values appear associated with better lap time in this limited sample; requires further testing. brake_threshold: higher values appear associated with better lap time in this limited sample; requires further testing. steer_gain: higher values appear associated with worse lap time, so lower values appear better in this limited sample; requires further testing. |
