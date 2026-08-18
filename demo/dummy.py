SIZE_STATS = {
    "s": ("Small", 125),
    "m": ("Medium", 200),
    "l": ("Large", 275),
}

SIZE_LABELS = ("Small", "Medium", "Large")
SIZE_CODES = {"Small": "s", "Medium": "m", "Large": "l"}
RANGES = (50, 100, 150, 200, 300, 400, 500)


class Dummy:
    def __init__(self, size: str = "m", distance: int = 0):
        if size not in SIZE_STATS:
            size = "m"
        label, health = SIZE_STATS[size]
        self.size = size
        self.size_label = label
        self.max_health = health
        self.health = health
        self.distance = distance

    def take_damage(self, damage: int) -> None:
        self.health -= damage

    def reset_health(self) -> None:
        self.health = self.max_health

    def is_destroyed(self) -> bool:
        return self.health <= 0


def create_dummy(size_label: str, distance: int = 0) -> Dummy:
    return Dummy(SIZE_CODES.get(size_label, "m"), distance)
