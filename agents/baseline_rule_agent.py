"""Simple baseline rule-based TORCS agent.

The agent is intentionally small and deterministic. It gives Part C an early
baseline before the final state, policy, or reward modules are ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class AgentParameters:
    target_speed: float = 80.0
    steer_gain: float = 1.0
    centering_gain: float = 0.5
    brake_threshold: float = 0.6
    gentle_speed: float = 45.0
    sharp_speed: float = 35.0
    straight_speed: float = 95.0
    acceleration_limit: float = 0.8
    braking_intensity: float = 0.25


class BaselineRuleAgent:
    """Rule-based controller returning steer, accel, and brake actions."""

    def __init__(self, parameters: AgentParameters):
        self.parameters = parameters

    def act(self, state: Mapping[str, object]) -> dict[str, float]:
        speed = float(state.get("speed", state.get("speedX", 0.0)))
        angle = float(state.get("angle", 0.0))
        track_pos = float(state.get("track_position", state.get("trackPos", 0.0)))
        track = state.get("track", [200.0] * 19)
        track_sensors = [float(value) for value in track]  # type: ignore[arg-type]

        steer = self._steer(angle, track_pos, track_sensors)
        corner_detected = self._is_corner(track_sensors, speed)
        safe_speed = self._safe_speed(track_sensors)

        target_speed = self.parameters.target_speed
        if self._is_straight(track_sensors, speed):
            target_speed = self.parameters.straight_speed
        if corner_detected:
            target_speed = min(target_speed, safe_speed)

        accel = self._accel(speed, target_speed, steer)
        brake = self._brake(speed, angle, track_sensors, target_speed)

        if brake > 0:
            accel = 0.0

        return {
            "steer": max(-1.0, min(1.0, steer)),
            "accel": max(0.0, min(1.0, accel)),
            "brake": max(0.0, min(1.0, brake)),
        }

    def _steer(self, angle: float, track_pos: float, track: Sequence[float]) -> float:
        steer = (angle * self.parameters.steer_gain) - (
            track_pos * self.parameters.centering_gain
        )

        left_avg = sum(track[:9]) / max(1, len(track[:9]))
        right_avg = sum(track[10:]) / max(1, len(track[10:]))
        sensor_bias = right_avg - left_avg

        if self._is_corner(track, speed=0.0):
            if sensor_bias < 0:
                steer += 0.20
            elif sensor_bias > 0:
                steer -= 0.20

        return steer

    def _accel(self, speed: float, target_speed: float, steer: float) -> float:
        steering_penalty = abs(steer) * 12.0
        if speed < target_speed - steering_penalty:
            return self.parameters.acceleration_limit
        return 0.15

    def _brake(
        self,
        speed: float,
        angle: float,
        track: Sequence[float],
        target_speed: float,
    ) -> float:
        brake = 0.0
        if abs(angle) > self.parameters.brake_threshold:
            brake = self.parameters.braking_intensity

        forward_distance = max(track[7:12]) if len(track) >= 12 else 200.0
        if forward_distance < speed * 0.60 or speed > target_speed + 12:
            brake += 0.15

        return brake

    def _is_corner(self, track: Sequence[float], speed: float) -> bool:
        if len(track) < 10:
            return False
        side_min = min(min(track[:9]), min(track[10:]))
        forward = track[9]
        return side_min < 5.0 or forward < max(45.0, speed * 0.65)

    def _safe_speed(self, track: Sequence[float]) -> float:
        forward_distance = max(track[8:11]) if len(track) >= 11 else 200.0
        if forward_distance < 60.0:
            return self.parameters.sharp_speed
        return self.parameters.gentle_speed

    def _is_straight(self, track: Sequence[float], speed: float) -> bool:
        if len(track) < 10:
            return False
        return track[9] > 120.0 and speed >= self.parameters.target_speed - 5.0


def build_agent(hyperparameters: Mapping[str, object]) -> BaselineRuleAgent:
    values = {
        field: float(hyperparameters.get(field, getattr(AgentParameters(), field)))
        for field in AgentParameters.__dataclass_fields__
    }
    return BaselineRuleAgent(AgentParameters(**values))

