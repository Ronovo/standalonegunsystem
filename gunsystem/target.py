from dataclasses import dataclass


@dataclass(frozen=True)
class Size:
    label: str
    to_hit: float  # Multiplies the to-hit roll, so above 1 is harder to hit
    health: int  # A dummy's health
    height: int  # A dummy's drawn height in pixels at the nearest range


SIZES = {
    "s": Size("Small", 1.10, 125, 110),
    "m": Size("Medium", 1.0, 200, 150),
    "l": Size("Large", 0.90, 275, 190),
}


@dataclass
class Target:
    """Aim point for resolve_shot: distance in meters and a size code from SIZES."""

    distance: int
    size: str = "m"

    def __post_init__(self) -> None:
        if self.size not in SIZES:
            raise ValueError(f"Unknown target size: {self.size!r} (expected one of {', '.join(SIZES)})")
