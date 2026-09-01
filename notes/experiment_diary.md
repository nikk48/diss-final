# Experiment Diary

## 2026-08-03

Date: 2026-08-03

What I tried:
- Created the Part C experimentation framework scaffold.
- Added dummy data, baseline configuration, result analysis, telemetry logging,
  and experiment runner scripts.

Why I tried it:
- To make progress on Part C before depending on a fully stable TORCS loop.

What worked:
- Project structure and starter files were created.

What did not work:
- Not tested with live TORCS yet.

Error encountered:
- None yet.

Change made:
- Established controlled logs and dummy analysis pipeline.

Next step:
- Run the dummy analysis, then connect `scripts/run_experiment.py` to live TORCS.

## 2026-08-05

Date: 2026-08-05

What I tried:
- I ran the dummy baseline experiment and then tested multiple grid-search
  configurations.

Why I tried it:
- To check whether the Part C experimentation framework can compare different
  agent configurations before live TORCS integration.

What worked:
- The scripts generated experiment configurations, ran dummy experiments,
  produced telemetry logs, and appended results to `run_log.csv`.
- The analysis script now reads `data/run_log.csv`, aggregates repeated runs,
  filters invalid zero-lap rows by default, and regenerates result summaries and
  charts.

What did not work / risk:
- The current dummy simulator does not prove real TORCS performance. It only
  validates the pipeline.
- Live TORCS integration remains a technical risk when the simulator connects
  but does not immediately advance the telemetry loop.

Change made:
- I standardised hyperparameter names around the actual agent fields:
  `target_speed`, `gentle_speed`, `brake_threshold`, and `steer_gain`.
- I prepared the framework for controlled live TORCS testing by keeping the same
  config, telemetry, and run-log structure across dummy and live runs.

Next step:
- Connect the same experiment runner to live TORCS and run one baseline
  configuration for 1-3 real runs.

## 2026-08-31

Date: 2026-08-31

What I tried:
- Imported the Part B `eva-optimised` code/results/telemetry folder into the
  Part C experimentation framework.

Why I tried it:
- To replace dummy-only evidence with real optimized PPO evaluation outputs and
  allow Part C analysis to compare baseline, live TORCS, grid-search, and Part B
  results using one shared run-log schema.

What worked:
- `scripts/import_part_b_results.py` converted Part B summary files into
  `data/run_log.csv`.
- Part B telemetry and summary files were copied into the Part C project.
- `scripts/analyse_results.py --input data/run_log.csv` included Part B results
  and identified the optimized PPO model as the best lap-time experiment.

What did not work / risk:
- Some Part B hyperparameter fields such as `steer_gain` and
  `brake_threshold` are not directly available because the imported model is a
  learned PPO controller rather than the Part C rule-based baseline.

Change made:
- Added a reusable Part B import bridge and regenerated analysis outputs from
  the combined run log.

Next step:
- Use the imported Part B results as the real-data input for Part C comparison
  and continue live TORCS validation with repeat baseline runs.

## 2026-08-31 Part C Evidence Cleanup

Date: 2026-08-31

What I tried:
- Applied the Part C implementation brief for dissertation-ready evidence.
- Added controlled result-source labels for dummy, grid dummy, Optuna dummy,
  live TORCS, live grid/Optuna and imported Part B evidence.
- Imported Part B PPO summaries into a dedicated `data/partb_results.csv`.
- Ran dummy Optuna validation with 10 trials and 3 runs per trial.
- Regenerated analysis outputs for dummy, live, Part B and combined views.

Why I tried it:
- To stop dummy validation rows being mixed with live TORCS or imported Part B
  evidence.
- To support the research question with reproducible performance, robustness,
  computational-efficiency and comparison outputs.

What worked:
- `scripts/analyse_results.py --mode dummy/live/partb/all` now works.
- `data/run_log.csv` now includes a controlled `source` column.
- `data/partb_results.csv` contains 4 imported Part B PPO evaluation rows.
- Legacy Part B rows were preserved in
  `data/part_b_imports/run_log_partb_legacy_rows.csv` and removed from the
  active Part C `data/run_log.csv`.
- `results/robustness_summary.csv`,
  `results/computational_efficiency_summary.csv` and
  `results/comparison_summary.csv` were generated.
- `results/charts/` now contains the required dissertation chart files.
- `scripts/optuna_tuning.py --mode dummy --trials 10 --runs 3 --profile coreSmall`
  completed successfully and selected `OPTUNA_DUMMY_008` as the best dummy
  trial by balanced objective score.

What did not work / risk:
- Live TORCS baseline still needs more clean repeated runs. The current live
  analysis has valid lap rows but also excludes earlier zero-lap connection
  attempts.
- Dummy runtime values are much smaller than live or Part B runtime values, so
  computational-efficiency claims must be made within the same source mode or
  clearly labelled as combined pipeline validation.

Change made:
- Added source/mode handling, overwrite-safe telemetry filenames, Part B import
  separation, robustness summaries, computational-efficiency summaries,
  comparison tables, required charts and a working dummy Optuna tuning loop.

Next step:
- Run 3 clean live baseline laps and 3-run live tests for selected grid configs
  such as `GRID_030` and `GRID_040`, then rerun
  `python scripts/analyse_results.py --mode live` and
  `python scripts/analyse_results.py --mode all`.

## 2026-08-31 Live Grid and Optuna Evidence

Date: 2026-08-31

What I tried:
- Ran selected grid-search configurations through real TORCS using the SCR UDP
  server.
- Ran one Optuna live trial as a smoke test of real simulator optimisation.
- Re-imported Part B evidence with conservative algorithm provenance labels.

Why I tried it:
- To add real `grid_live` and `optuna_live` rows for Part C instead of relying
  only on dummy validation.
- To show that systematic experimentation and hyperparameter optimisation can
  be executed against live TORCS telemetry.

What worked:
- `GRID_030` completed a live TORCS lap in 199.806 seconds.
- `GRID_040` completed a live TORCS lap in 198.906 seconds.
- `OPTUNA_LIVE_001` completed a live TORCS lap in 195.526 seconds with sampled
  parameters: target speed 77.491, gentle speed 49.261, brake threshold 0.646,
  steer gain 1.039.
- Live analysis now includes 2 `grid_live` rows and 1 `optuna_live` row.
- Combined analysis was regenerated after the live runs.

What did not work / risk:
- This is still a small live sample. Strong robustness claims need repeated
  runs per configuration.
- Dummy, live and imported Part B timings should be discussed as separate
  evidence modes unless hardware/runtime conditions are normalised.

Change made:
- Corrected source inference so explicit valid labels such as `optuna_live` are
  preserved.
- Corrected the existing `OPTUNA_LIVE_001` row in `data/run_log.csv`.
- Regenerated live and combined analysis outputs.

Next step:
- Repeat the best live candidates for at least 3 runs each, then use
  `results/robustness_summary.csv` for the dissertation robustness discussion.

## 2026-09-01 Live Robustness Repeats

Date: 2026-09-01

What I tried:
- Repeated the selected live TORCS baseline, grid-search and Optuna
  configurations until each main Part C candidate had 3 completed live runs.

Why I tried it:
- To support Part C claims about robustness and reproducibility using repeated
  simulator evidence rather than single-run results.

What worked:
- `EXP_001` baseline `rule_based` now has 3 completed live runs with mean lap
  time 196.726 seconds.
- `GRID_030` now has 3 completed live runs with mean lap time 199.806 seconds.
- `GRID_040` now has 3 completed live runs with mean lap time 198.906 seconds.
- `OPTUNA_LIVE_001` now has 3 completed live runs with mean lap time 195.526
  seconds.
- Regenerated live and combined analysis outputs.
- Created `results/dissertation_robustness_evidence.csv` for dissertation
  planning and ChatGPT handoff.

What did not work / risk:
- The repeated live runs are deterministic in this TORCS setup, so lap-time
  variance is near zero. This supports reproducibility, but broader robustness
  claims would require additional seeds, tracks, or perturbations.

Change made:
- Added `--run-start` to `scripts/run_torcs_live.py` so repeated live runs can
  be logged with correct run numbers.
- Refreshed `results/dissertation_chatgpt_key_results.csv` and
  `results/dissertation_chatgpt_next_steps_input.csv`.

Next step:
- Use the robustness table to write the Part C results section: baseline vs
  grid vs Optuna, then discuss Part B imported PPO as a comparator with
  provenance caveats.
