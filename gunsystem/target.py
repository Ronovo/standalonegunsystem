from dataclasses import dataclass

SIZE_MODIFIERS = {"s": 1.10, "m": 1.0, "l": 0.90}


@dataclass
class Target:
    """Aim point for resolve_shot: distance in meters and size code s/m/l."""

    distance: int
    size: str = "m"

    def __post_init__(self) -> None:
        if self.size not in SIZE_MODIFIERS:
            raise ValueError(f"Unknown target size: {self.size!r} (expected one of {', '.join(SIZE_MODIFIERS)})")
