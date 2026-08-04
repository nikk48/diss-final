"""CSV telemetry logger for one run at a time."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping


TELEMETRY_FIELDS = [
    "timestamp",
    "speed",
    "steering",
    "throttle",
    "brake",
    "track_position",
    "angle",
    "rpm",
    "gear",
    "track_sensor_center",
    "lap_time",
    "event",
]


class TelemetryLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=TELEMETRY_FIELDS)
        self._writer.writeheader()

    def log(self, row: Mapping[str, object]) -> None:
        clean = {field: row.get(field, "") for field in TELEMETRY_FIELDS}
        self._writer.writerow(clean)

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "TelemetryLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

