# Importing This Project Into IBM Bob

## Option 1: Open the Folder Directly

1. Open IBM Bob.
2. Choose `File > Open Folder`.
3. Select:

   ```text
   ~/Desktop/Part_C_Experimentation
   ```

4. Trust the folder if Bob asks.
5. Open Bob chat and ask:

   ```text
   Explain this project and how to run the dummy and live TORCS experiments.
   ```

## Option 2: Use the Zip Archive

If you need to upload/import a compressed project, use:

```text
~/Desktop/Part_C_Experimentation_for_Bob.zip
```

The zip excludes `venv`, `.git`, `.matplotlib`, and cache files.

## Good First Prompt In Bob

```text
Read AGENTS.md and README.md. Then explain the project structure, how the dummy
pipeline works, and the exact steps to connect run_torcs_live.py with TORCS.
Do not change files yet.
```

## Good Implementation Prompt In Bob

```text
Improve the live TORCS experiment runner so it logs average speed, max speed,
damage, distance raced, and failure reason while preserving the existing
run_log.csv schema or updating the analysis scripts consistently.
```

