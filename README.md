# Part C Experimentation Framework

This project is a practical implementation scaffold for the Part C dissertation work:
systematic experimentation, hyperparameter optimisation, computational efficiency,
robustness, reproducibility, and talent-identification evidence for a TORCS
autonomous racing agent.

The framework starts with dummy data so the analysis pipeline can be tested
before TORCS is fully connected. Later, `scripts/run_experiment.py` can be
extended to call the real TORCS client and agent loop.

## Structure

```text
Part_C_Experimentation/
  agents/                 Rule-based and future learned agents
  configs/                YAML experiment configuration files
  data/                   Raw run logs, dummy data, telemetry logs
  data/telemetry_logs/    Per-run telemetry CSV files
  logs/                   Runtime logs
  notebooks/              Jupyter notebooks
  notes/                  Experiment diary and methodology notes
  results/                Summaries and generated charts
  results/charts/         Analysis charts
  scripts/                Experiment, analysis, and tuning scripts
```

## First Setup

```bash
cd ~/Desktop/Part_C_Experimentation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## First Dummy Test

```bash
source venv/bin/activate
python scripts/analyse_results.py
python scripts/run_experiment.py --config configs/baseline_config.yaml --dummy
```

Expected outputs:

- `results/summary.csv`
- `results/scored_experiments.csv`
- charts in `results/charts/`
- appended rows in `data/run_log.csv`
- telemetry files in `data/telemetry_logs/`

## Practical Implementation Path

1. Validate the dummy pipeline.
2. Run the baseline dummy experiment.
3. Replace dummy values in `run_experiment.py` with real TORCS telemetry.
4. Run small real experiments, for example one configuration with three runs.
5. Add grid search, then random search.
6. Add Optuna only when TORCS execution is stable.
7. Repeat best configurations for robustness testing.
8. Use outputs from `results/` in the dissertation.

## Running With Live TORCS

Start TORCS first:

```bash
cd ~/Desktop/TORCS-Wine-Setup
./Run_TORCS.command
```

Inside TORCS, open a practice/new race using the SCR/server driver so the UDP
server listens on port `3001`.

Then, in a second Terminal:

```bash
cd ~/Desktop/Part_C_Experimentation
source venv/bin/activate
python scripts/run_torcs_live.py --config configs/baseline_config.yaml --port 3001 --runs 1
```

Live outputs are appended to:

- `data/run_log.csv`
- `data/telemetry_logs/<experiment>_live_run_<n>.csv`

