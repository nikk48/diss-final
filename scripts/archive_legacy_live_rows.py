"""Archive legacy EXP_001 torcs_live rows from the main run log."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_LOG = ROOT / "data" / "run_log.csv"
ARCHIVE = ROOT / "data" / "archived_legacy_live_rows.csv"


def is_legacy_exp001_torcs_live(row: dict[str, str]) -> bool:
    return (
        row.get("experiment_id", "").strip() == "EXP_001"
        and row.get("algorithm", "").strip() == "torcs_live"
    )


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("experiment_id", ""),
        row.get("date_time", ""),
        row.get("algorithm", ""),
        row.get("telemetry_file", ""),
    )


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    fieldnames, rows = read_csv(RUN_LOG)
    legacy_rows = [row for row in rows if is_legacy_exp001_torcs_live(row)]
    retained_rows = [row for row in rows if not is_legacy_exp001_torcs_live(row)]

    if ARCHIVE.exists() and ARCHIVE.stat().st_size > 0:
        archive_fields, archived_rows = read_csv(ARCHIVE)
        if archive_fields != fieldnames:
            raise SystemExit(
                f"Archive schema does not match run log schema: {ARCHIVE}"
            )
    else:
        archived_rows = []

    archived_keys = {row_key(row) for row in archived_rows}
    new_archive_rows = [
        row for row in legacy_rows if row_key(row) not in archived_keys
    ]
    write_csv(ARCHIVE, fieldnames, [*archived_rows, *new_archive_rows])
    write_csv(RUN_LOG, fieldnames, retained_rows)

    print(f"Archived {len(new_archive_rows)} legacy row(s) to {ARCHIVE}")
    print(f"Removed {len(legacy_rows)} legacy row(s) from {RUN_LOG}")
    print(f"Remaining run_log rows: {len(retained_rows)}")


if __name__ == "__main__":
    main()
