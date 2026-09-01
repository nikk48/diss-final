# Live Repeat Telemetry Verification

Run log: `/Users/thenotoriouscode/Desktop/gaurav-diss-final/data/run_log.csv`

This check verifies whether live repeat rows are backed by distinct telemetry files. It checks file existence, unique paths, SHA-256 content hashes, internal telemetry timestamps, row counts, and lap-time values.

## Group Verdicts

| experiment_id | source | algorithm | run_rows | telemetry_files_found | unique_telemetry_paths | unique_sha256_hashes | unique_first_timestamps | unique_last_timestamps | mean_best_lap_time | std_best_lap_time | min_telemetry_rows | max_telemetry_rows | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GRID_030 | grid_live | grid_search | 3 | 3 | 3 | 3 | 3 | 3 | 199.806 | 0.0 | 9648 | 9648 | verified: distinct telemetry files with unique content hashes and timestamps |
| GRID_040 | grid_live | grid_search | 3 | 3 | 3 | 3 | 3 | 3 | 198.90600000000003 | 2.842170943040401e-14 | 9603 | 9603 | verified: distinct telemetry files with unique content hashes and timestamps |
| EXP_001 | live | rule_based | 3 | 3 | 3 | 3 | 3 | 3 | 196.726 | 0.0 | 9494 | 9494 | verified: distinct telemetry files with unique content hashes and timestamps |
| EXP_001 | live | torcs_live | 2 | 2 | 1 | 1 | 1 | 1 | 196.076 | 0.3100000000000023 | 9477 | 9477 | not verified: repeated run rows point to the same telemetry path |
| OPTUNA_LIVE_001 | optuna_live | optuna | 3 | 3 | 3 | 3 | 3 | 3 | 195.52599999999998 | 2.842170943040401e-14 | 9434 | 9434 | verified: distinct telemetry files with unique content hashes and timestamps |

## File-Level Evidence

| experiment_id | source | run_number | date_time | best_lap_time | file_size_bytes | telemetry_rows | first_timestamp | last_timestamp | sha256 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP_001 | live | 1 | 2026-08-04T01:05:05.903207+00:00 | 195.766 | 963148 | 9477 | 2026-08-12T12:56:23.585261+00:00 | 2026-08-12T12:59:40.953022+00:00 | fe1b1db9f0f4a7108b09a6e879128b01872f5f1ed836275c1844989f23103d17 |
| EXP_001 | live | 1 | 2026-08-12T12:59:40.953902+00:00 | 196.386 | 963148 | 9477 | 2026-08-12T12:56:23.585261+00:00 | 2026-08-12T12:59:40.953022+00:00 | fe1b1db9f0f4a7108b09a6e879128b01872f5f1ed836275c1844989f23103d17 |
| EXP_001 | live | 1 | 2026-08-31T18:11:43.113201+00:00 | 196.726 | 964351 | 9494 | 2026-08-31T18:11:30.681096+00:00 | 2026-08-31T18:11:43.111675+00:00 | 0a20c68328ae1f2a3ada456e274f2108736b925b21c3540c3a9c5288f5f0f1ad |
| EXP_001 | live | 1 | 2026-08-31T18:37:48.526131+00:00 | 196.726 | 964351 | 9494 | 2026-08-31T18:37:35.503222+00:00 | 2026-08-31T18:37:48.525884+00:00 | 204a36c4b8355567b60620c3949d7a06717c3d306d29c02cad1118fbd9f31bad |
| GRID_030 | grid_live | 1 | 2026-08-31T19:05:52.748559+00:00 | 199.806 | 979765 | 9648 | 2026-08-31T19:05:40.049664+00:00 | 2026-08-31T19:05:52.748304+00:00 | 99179e3b87e355720cc95e73eb8f5e65e32c498a24d3020007299030d6dba464 |
| GRID_040 | grid_live | 1 | 2026-08-31T19:06:43.706850+00:00 | 198.906 | 975672 | 9603 | 2026-08-31T19:06:30.816199+00:00 | 2026-08-31T19:06:43.706572+00:00 | 13174a0c4f5459030c0082fd6c76de5ccad4d02df3d2075288979c9c8d90c7b6 |
| OPTUNA_LIVE_001 | optuna_live | 1 | 2026-08-31T19:07:35.613334+00:00 | 195.526 | 958102 | 9434 | 2026-08-31T19:07:22.799735+00:00 | 2026-08-31T19:07:35.613070+00:00 | 54df51ca8dfa55d99ba0b70dc9b021d623c938f9cc24c0065109f163fc790964 |
| EXP_001 | live | 3 | 2026-09-01T13:13:02.610746+00:00 | 196.726 | 964351 | 9494 | 2026-09-01T13:12:50.846693+00:00 | 2026-09-01T13:13:02.610520+00:00 | be81d34663192e2bac6bac18ba658fe6897b817eb6696e4ba7c8b4b0564f0c4d |
| GRID_030 | grid_live | 2 | 2026-09-01T13:13:17.869810+00:00 | 199.806 | 979765 | 9648 | 2026-09-01T13:13:05.766004+00:00 | 2026-09-01T13:13:17.869576+00:00 | 97274b0afb93fdbb15d3caff7893b144618d7b2984637befba47c66a6a536d39 |
| GRID_030 | grid_live | 3 | 2026-09-01T13:13:33.249063+00:00 | 199.806 | 979765 | 9648 | 2026-09-01T13:13:21.025388+00:00 | 2026-09-01T13:13:33.248812+00:00 | f6a93f35c29030bb0421b681771ad7fa827a2a6fc76ebbde660cf7fdf0ab2875 |
| GRID_040 | grid_live | 2 | 2026-09-01T13:13:48.739145+00:00 | 198.906 | 975672 | 9603 | 2026-09-01T13:13:36.402103+00:00 | 2026-09-01T13:13:48.738710+00:00 | b1953dea53b23833e902b4aa81496874c001d4469225e2644a582d1df61ee1bc |
| GRID_040 | grid_live | 3 | 2026-09-01T13:14:04.047416+00:00 | 198.906 | 975672 | 9603 | 2026-09-01T13:13:51.895923+00:00 | 2026-09-01T13:14:04.047231+00:00 | ce8dab3a7140d6d4da2616fe1fa7ceb013c03d2eefdfedef246829d6789b125a |
| OPTUNA_LIVE_001 | optuna_live | 2 | 2026-09-01T13:14:19.218374+00:00 | 195.526 | 958102 | 9434 | 2026-09-01T13:14:07.211411+00:00 | 2026-09-01T13:14:19.218210+00:00 | a312623145d57d9a1a0128199c46716947fccc07c901514303b41d2f3d18c3f5 |
| OPTUNA_LIVE_001 | optuna_live | 3 | 2026-09-01T13:14:34.339409+00:00 | 195.526 | 958102 | 9434 | 2026-09-01T13:14:22.372255+00:00 | 2026-09-01T13:14:34.339182+00:00 | 34b87287d58731be016f72f0e76245625bccdd6ec0430151176f059aa721b97a |
