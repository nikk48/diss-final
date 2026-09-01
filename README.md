# TORCS AI Racing Experimentation Framework

This repository supports the Part C dissertation question:

> How can systematic experimentation and hyperparameter optimisation improve
> the computational efficiency, robustness and reproducibility of an autonomous
> racing agent while supporting talent identification through evidence of
> applied AI skills?

Part C contributes the experimentation, logging, analysis and comparison
framework. The PPO model was developed in Part B and is imported here only as
an evaluated policy artefact.

## Project Structure

```text
Part_C_Experimentation/
  agents/                 Rule-based baseline agent
  configs/                Baseline, search-space and generated YAML configs
  data/run_log.csv        Part C dummy/live run log
  data/partb_results.csv  Imported Part B PPO results
  data/telemetry_logs/    Per-run telemetry CSV files
  notes/                  Experiment diary and methodology notes
  results/                Scored outputs, summaries and charts
  scripts/                Experiment, import, analysis and tuning scripts
```

## Setup

```bash
cd ~/Desktop/Part_C_Experimentation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Source Labels

Every result row has a controlled `source` value:

- `dummy`: baseline dummy validation
- `grid_dummy`: grid-search dummy validation
- `optuna_dummy`: Optuna dummy validation
- `live`: live TORCS baseline/control evidence
- `grid_live`: live TORCS grid-search evidence
- `optuna_live`: live TORCS Optuna evidence
- `partb_imported`: imported Part B PPO policy evidence

Dummy rows prove that the pipeline works. They should not be cited as final
live simulator performance.

## Dummy Baseline

```bash
source venv/bin/activate
python scripts/run_experiment.py --config configs/baseline_config.yaml --dummy
```

This appends dummy rows to `data/run_log.csv` and writes timestamped telemetry
files in `data/telemetry_logs/`.

## Grid Search

Generate grid configs:

```bash
python scripts/grid_search.py
```

Run selected dummy configs:

```bash
python scripts/run_experiment.py --config configs/generated_grid/GRID_030.yaml --dummy
python scripts/run_experiment.py --config configs/generated_grid/GRID_040.yaml --dummy
```

## Import Part B PPO Results

```bash
python scripts/import_partb_results.py --source ~/Desktop/eva-optimised
```

This writes `data/partb_results.csv` and refreshes
`data/part_b_imports/part_b_import_manifest.csv`. Use
`--append-run-log` only if you intentionally want imported Part B rows copied
into `data/run_log.csv` for legacy workflows.

Earlier Part B rows that had already been appended to `data/run_log.csv` were
preserved in `data/part_b_imports/run_log_partb_legacy_rows.csv` and removed
from the active Part C run log.

## Analyse Results

Run each view separately:

```bash
python scripts/analyse_results.py --mode dummy
python scripts/analyse_results.py --mode live
python scripts/analyse_results.py --mode partb
python scripts/analyse_results.py --mode all
```

Generated outputs include:

- `results/dummy_scored_experiments.csv`
- `results/live_scored_experiments.csv`
- `results/partb_scored_experiments.csv`
- `results/combined_scored_experiments.csv`
- `results/summary_live.csv`
- `results/summary_all.csv`
- `results/robustness_summary.csv`
- `results/computational_efficiency_summary.csv`
- `results/comparison_summary.csv`

Required charts are saved in `results/charts/`:

- `best_lap_time_by_configuration.png`
- `average_lap_time_with_variance.png`
- `completion_rate_by_configuration.png`
- `crash_offtrack_damage_comparison.png`
- `runtime_or_decision_latency_comparison.png`
- `balanced_score_by_configuration.png`

## Optuna

Validate Optuna in dummy mode first:

```bash
python scripts/optuna_tuning.py --mode dummy --trials 10 --runs 3 --profile coreSmall
```

Outputs:

- `results/optuna_trials.csv`
- `results/optuna_best_config.yaml`
- `configs/generated_optuna/OPTUNA_DUMMY_*.yaml`
- appended `optuna_dummy` rows in `data/run_log.csv`

The objective balances lap time, completion rate, crashes, off-track events and
runtime. Do not use live Optuna until TORCS baseline live runs are stable.

## Live TORCS Runs

Start TORCS through Wine:

```bash
cd ~/Desktop/TORCS-Wine-Setup
./Run_TORCS.command
```

Inside TORCS, open Practice/New Race with the SCR/server driver active on UDP
port `3001`. Then use a second Terminal:

```bash
cd ~/Desktop/Part_C_Experimentation
source venv/bin/activate
python scripts/run_torcs_live.py --config configs/baseline_config.yaml --port 3001 --runs 3
```

Selected live grid tests:

```bash
python scripts/run_torcs_live.py --config configs/generated_grid/GRID_030.yaml --port 3001 --runs 3
python scripts/run_torcs_live.py --config configs/generated_grid/GRID_040.yaml --port 3001 --runs 3
```

Small live Optuna test only after TORCS is stable:

```bash
python scripts/optuna_tuning.py --mode live --trials 3 --runs 1 --profile core --port 3001
```

## Current Evidence Snapshot

After the latest analysis:

- live baseline best lap: `195.766s` from valid live TORCS rows
- imported Part B PPO best lap: `106.892s`
- Part B PPO completion rate: `1.00`
- live analysis excluded three zero-lap connection attempts
- dummy Optuna validation best trial: `OPTUNA_DUMMY_008`

Correct dissertation wording:

> The PPO model was developed in Part B and imported into Part C as an
> evaluated policy artefact. Part C contributes the systematic experimentation
> framework used to standardise, compare, analyse and interpret baseline,
> tuned, Optuna and Part B PPO results using common performance, robustness,
> reproducibility and computational-efficiency metrics.
