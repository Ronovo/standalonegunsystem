from gunsystem import Target

SIZE_STATS = {
    "s": ("Small", 125),
    "m": ("Medium", 200),
    "l": ("Large", 275),
}

SIZE_LABELS = tuple(label for label, _ in SIZE_STATS.values())
SIZE_CODES = {label: code for code, (label, _) in SIZE_STATS.items()}
RANGES = (50, 100, 150, 200, 300, 400, 500)


class Dummy(Target):
    def __init__(self, size: str = "m", distance: int = RANGES[0]):
        if size not in SIZE_STATS:
            size = "m"
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


def create_dummy(size_label: str, distance: int = RANGES[0]) -> Dummy:
    return Dummy(SIZE_CODES.get(size_label, "m"), distance)
