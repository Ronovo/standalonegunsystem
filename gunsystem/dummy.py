from gunsystem import Target

SIZE_STATS = {
    "s": ("Small", 125),
    "m": ("Medium", 200),
    "l": ("Large", 275),
}

SIZE_LABELS = tuple(label for label, _ in SIZE_STATS.values())
RANGES = (50, 100, 150, 200, 300, 400, 500)


def size_code(value) -> str:
    """The code for a size given as a code or a label ("s" or "Small"), or "m" for anything else."""
    for code, (label, _) in SIZE_STATS.items():
        if value in (code, label):
            return code
    return "m"


def size_label(value) -> str:
    """The label for a size given as a code or a label, or "Medium" for anything else."""
    return SIZE_STATS[size_code(value)][0]


class Dummy(Target):
    def __init__(self, size: str = "m", distance: int = RANGES[0]):
        size = size_code(size)
        super().__init__(distance, size)
        label, health = SIZE_STATS[size]
        self.size_label = label
        self.max_health = health
        self.health = health

    def take_damage(self, damage: int) -> None:
        self.health -= damage

    def reset_health(self) -> None:
        self.health = self.max_health

    def is_destroyed(self) -> bool:
        return self.health <= 0

