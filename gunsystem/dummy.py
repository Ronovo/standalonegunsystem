from gunsystem.target import SIZES, Target

RANGES = (50, 100, 150, 200, 300, 400, 500)


def size_code(value) -> str:
    """value when it is a size code, else "m"."""
    return value if value in SIZES else "m"


class Dummy(Target):
    def __init__(self, size: str = "m", distance: int = RANGES[0]):
        super().__init__(distance, size)
        self.max_health = self.health = SIZES[size].health

    @property
    def size_label(self) -> str:
        return SIZES[self.size].label

    def take_damage(self, damage: int) -> None:
        self.health -= damage

    def reset_health(self) -> None:
        self.health = self.max_health

    def is_destroyed(self) -> bool:
        return self.health <= 0
