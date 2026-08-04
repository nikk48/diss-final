"""Minimal TORCS SCR UDP client.

This avoids the old gym-torcs client's Linux-specific relaunch behaviour. Start
TORCS separately through Wine, open a race with the SCR/server driver, then run
the live experiment script.
"""

from __future__ import annotations

import socket
import sys
from dataclasses import dataclass, field
from typing import Any


DATA_SIZE = 2**17
SENSOR_ANGLES = "-45 -19 -12 -7 -4 -2.5 -1.7 -1 -.5 0 .5 1 1.7 2.5 4 7 12 19 45"


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def destringify(values: list[str] | str) -> Any:
    if not values:
        return values
    if isinstance(values, str):
        try:
            return float(values)
        except ValueError:
            return values
    if len(values) == 1:
        return destringify(values[0])
    return [destringify(value) for value in values]


@dataclass
class ServerState:
    d: dict[str, Any] = field(default_factory=dict)
    raw: str = ""

    def parse_server_str(self, server_string: str) -> None:
        self.raw = server_string.strip()
        payload = self.raw[:-1].strip().lstrip("(").rstrip(")")
        for item in payload.split(")("):
            parts = item.split(" ")
            self.d[parts[0]] = destringify(parts[1:])


@dataclass
class DriverAction:
    d: dict[str, Any] = field(
        default_factory=lambda: {
            "accel": 0.2,
            "brake": 0.0,
            "clutch": 0.0,
            "gear": 1,
            "steer": 0.0,
            "focus": [-90, -45, 0, 45, 90],
            "meta": 0,
        }
    )

    def clip_to_limits(self) -> None:
        self.d["steer"] = clip(float(self.d["steer"]), -1.0, 1.0)
        self.d["brake"] = clip(float(self.d["brake"]), 0.0, 1.0)
        self.d["accel"] = clip(float(self.d["accel"]), 0.0, 1.0)
        self.d["clutch"] = clip(float(self.d["clutch"]), 0.0, 1.0)
        if self.d["gear"] not in [-1, 0, 1, 2, 3, 4, 5, 6]:
            self.d["gear"] = 0
        if self.d["meta"] not in [0, 1, False, True]:
            self.d["meta"] = 0

    def __repr__(self) -> str:
        self.clip_to_limits()
        output = ""
        for key, value in self.d.items():
            output += f"({key} "
            if isinstance(value, list):
                output += " ".join(str(item) for item in value)
            else:
                output += f"{float(value):.3f}"
            output += ")"
        return output


class TorcsUdpClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3001,
        sid: str = "SCR",
        timeout: float = 1.0,
        connect_attempts: int = 30,
    ):
        self.host = host
        self.port = port
        self.sid = sid
        self.timeout = timeout
        self.connect_attempts = connect_attempts
        self.S = ServerState()
        self.R = DriverAction()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.timeout)
        self._connect()

    def _connect(self) -> None:
        init_message = f"{self.sid}(init {SENSOR_ANGLES})".encode()
        for attempt in range(1, self.connect_attempts + 1):
            self.socket.sendto(init_message, (self.host, self.port))
            try:
                packet, _ = self.socket.recvfrom(DATA_SIZE)
            except socket.timeout:
                print(
                    f"Waiting for TORCS UDP server on {self.host}:{self.port} "
                    f"with id {self.sid!r} "
                    f"({attempt}/{self.connect_attempts})"
                )
                continue

            text = packet.decode("utf-8", errors="replace")
            if "***identified***" in text:
                print(f"Connected to TORCS UDP server on {self.host}:{self.port}")
                return

        self.shutdown()
        raise TimeoutError(
            f"Could not connect to TORCS on {self.host}:{self.port}. "
            "Start TORCS, open Practice/New Race with only scr_server 1 selected, "
            "then rerun. If TORCS already accepted an older Python process, "
            "quit the race and start a fresh New Race."
        )

    def get_servers_input(self) -> bool:
        while True:
            try:
                packet, _ = self.socket.recvfrom(DATA_SIZE)
            except socket.timeout:
                return False

            text = packet.decode("utf-8", errors="replace")
            if "***identified***" in text:
                continue
            if "***shutdown***" in text or "***restart***" in text:
                return False
            if text:
                self.S.parse_server_str(text)
                return True

    def respond_to_server(self) -> None:
        message = repr(self.R).encode()
        self.socket.sendto(message, (self.host, self.port))

    def shutdown(self) -> None:
        if self.socket:
            self.socket.close()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3001
    client = TorcsUdpClient(port=port)
    client.shutdown()


if __name__ == "__main__":
    main()
