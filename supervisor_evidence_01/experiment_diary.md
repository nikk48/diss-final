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
