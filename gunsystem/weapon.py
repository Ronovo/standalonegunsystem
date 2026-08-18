from dataclasses import dataclass
from enum import Enum


class FireMode(Enum):
    SINGLE = "s"
    BURST = "3r"
    AUTO = "fa"

    @property
    def display_name(self) -> str:
        return {
            FireMode.SINGLE: "Single Shot",
            FireMode.BURST: "3 Round Burst",
            FireMode.AUTO: "Fully Automatic",
        }[self]

    @classmethod
    def from_display(cls, name: str) -> "FireMode":
        for mode in cls:
            if mode.display_name == name:
                return mode
        raise KeyError(f"Unknown fire mode: {name}")


class ReloadStyle(Enum):
    MAGAZINE = "magazine"
    SHELL = "shell"
    REVOLVER = "revolver"


@dataclass(frozen=True)
class WeaponType:
    class_name: str
    category: str


class Weapon:
    def __init__(
        self,
        name: str,
        max_ammo: int,
        damage: int,
        range_m: int,
        max_range: int,
        base_accuracy: int,
        weapon_type: WeaponType,
        fire_modes: tuple[FireMode, ...],
        reload_style: ReloadStyle = ReloadStyle.MAGAZINE,
    ):
        self.name = name
        self.max_ammo = max_ammo
        self.current_ammo = 0
        self.damage = damage
        self.range_m = range_m
        self.max_range = max_range
        self.base_accuracy = base_accuracy
        self.weapon_type = weapon_type
        self.fire_modes = fire_modes
        self.reload_style = reload_style

    def reload(self) -> None:
        self.current_ammo = self.max_ammo

    def load_round(self) -> bool:
        if self.current_ammo >= self.max_ammo:
            return False
        self.current_ammo += 1
        return True

    def unload(self) -> None:
        self.current_ammo = 0

    def fire_shot(self) -> bool:
        if self.current_ammo <= 0:
            return False
        self.current_ammo -= 1
        return True

    def copy(self) -> "Weapon":
        clone = Weapon(
            name=self.name,
            max_ammo=self.max_ammo,
            damage=self.damage,
            range_m=self.range_m,
            max_range=self.max_range,
            base_accuracy=self.base_accuracy,
            weapon_type=self.weapon_type,
            fire_modes=self.fire_modes,
            reload_style=self.reload_style,
        )
        clone.current_ammo = self.current_ammo
        return clone

    def fire_mode_names(self) -> str:
        return ", ".join(mode.display_name for mode in self.fire_modes)

    def describe(self, include_ammo: bool = False) -> str:
        lines = [
            f"Max Ammo: {self.max_ammo} | Damage: {self.damage}",
            f"Base Range(In Meters): {self.range_m} | Base Accuracy: {self.base_accuracy}",
            f"Max Range (In Meters): {self.max_range}",
            f"Class: {self.weapon_type.class_name} | Weapon Type: {self.weapon_type.category}",
            f"Fire Modes : {self.fire_mode_names()}",
        ]
        if include_ammo:
            lines.append(f"Current Ammo : {self.current_ammo}")
        return "\n".join(lines)
