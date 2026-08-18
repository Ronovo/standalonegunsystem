from dataclasses import dataclass


@dataclass
class Target:
    """Aim point for resolve_shot: distance in meters and size code s/m/l."""

    distance: int
    size: str = "m"
