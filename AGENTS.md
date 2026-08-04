# Part C Experimentation Framework

## Project Goal

This repository supports a dissertation Part C implementation for systematic
experimentation, hyperparameter optimisation, computational efficiency,
robustness, reproducibility, and talent-identification evidence for a TORCS
autonomous racing agent.

The project starts with a working dummy pipeline, then connects to live TORCS
through `scripts/run_torcs_live.py`.

## Important Commands

Set up the environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the dummy analysis pipeline:

```bash
source venv/bin/activate
python scripts/analyse_results.py
python scripts/run_experiment.py --config configs/baseline_config.yaml --dummy
```

Generate search configurations:

```bash
source venv/bin/activate
python scripts/grid_search.py
python scripts/random_search.py --trials 5
```

Run live TORCS after TORCS is open with `scr_server` active:

```bash
source venv/bin/activate
python scripts/run_torcs_live.py --config configs/baseline_config.yaml --port 3001 --runs 1
```

## TORCS/Wine Setup

TORCS is launched separately from:

```bash
~/Desktop/TORCS-Wine-Setup/Run_TORCS.command
```

Inside TORCS, start a practice/new race using the `scr_server` driver so the UDP
server listens on port `3001`.

## Key Files

- `agents/baseline_rule_agent.py`: baseline rule-based controller.
- `configs/baseline_config.yaml`: first controlled experiment configuration.
- `scripts/run_experiment.py`: dummy experiment runner.
- `scripts/run_torcs_live.py`: live TORCS experiment runner.
- `scripts/torcs_udp_client.py`: minimal SCR UDP client.
- `scripts/analyse_results.py`: analysis/scoring/charts.
- `data/run_log.csv`: per-run log.
- `data/telemetry_logs/`: per-run telemetry.
- `results/summary.csv`: current best/safest/efficient/balanced summary.
- `notes/experiment_diary.md`: dissertation experiment diary.

## Working Rules

- Preserve the CSV schema in `data/run_log.csv` unless explicitly changing the
  analysis pipeline too.
- Do not commit or edit `venv/`, `.matplotlib/`, or generated cache files.
- Keep dummy mode working when changing live TORCS logic.
- Prefer small, reproducible scripts over one-off notebook-only analysis.
- For dissertation evidence, log configuration, runtime, telemetry path,
  completion, lap time, crashes/off-track events, and decision latency.
- Keep generated charts in `results/charts/`.

## Next Implementation Step

The next practical task is to run `scripts/run_torcs_live.py` against a live
TORCS race, then tune the baseline controller using the recorded telemetry.

