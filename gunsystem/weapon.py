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


class ReloadStyle(Enum):
    MAGAZINE = "magazine"
    SHELL = "shell"
    REVOLVER = "revolver"

    @property
    def note(self) -> str:
        return {
            ReloadStyle.MAGAZINE: "Magazine fed: reloads in one go.",
            ReloadStyle.SHELL: "Tube fed: shells are loaded one at a time.",
            ReloadStyle.REVOLVER: "Revolver: empty the cylinder, then load rounds one at a time.",
        }[self]


class ReloadStep(Enum):
    EMPTY = "empty"
    MAGAZINE = "magazine"
    SHELL = "shell"
    ROUND = "round"

    @property
    def label(self) -> str:
        return {
            ReloadStep.EMPTY: "Empty cylinder",
            ReloadStep.MAGAZINE: "Reload magazine",
            ReloadStep.SHELL: "Load shell",
            ReloadStep.ROUND: "Load round",
        }[self]


LOADING_STEPS = {ReloadStyle.MAGAZINE: ReloadStep.MAGAZINE, ReloadStyle.SHELL: ReloadStep.SHELL,
                 ReloadStyle.REVOLVER: ReloadStep.ROUND}


@dataclass(frozen=True)
class WeaponType:
    class_name: str
    category: str
    # Added to the to-hit roll per 50m inside effective range; negative is a bonus.
    close_range_step: int = -5
    max_close_steps: int = 3
    # Scales how much a long string widens the spray; below 1 is easier to hold on target.
    spray_control: float = 1.0
    # Percent of hits that are critical.
    crit_chance: int = 2


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
        rpm: int,
        reload_seconds: float,
        reload_style: ReloadStyle = ReloadStyle.MAGAZINE,
        pellets: int = 1,
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
        self.rpm = rpm
        self.reload_seconds = reload_seconds
        self.reload_style = reload_style
        self.pellets = pellets

    @property
    def rounds_per_pull(self) -> int:
        """Rounds one second on the trigger fires on full auto."""
        return max(1, round(self.rpm / 60))

    @property
    def full_reload_seconds(self) -> float:
        if self.reload_style is ReloadStyle.MAGAZINE:
            return self.reload_seconds
        return self.reload_seconds * self.max_ammo

    @property
    def reload_label(self) -> str:
        if self.reload_style is ReloadStyle.MAGAZINE:
            return f"{self.reload_seconds:g} s"
        each = "shell" if self.reload_style is ReloadStyle.SHELL else "round"
        return f"{self.reload_seconds:g} s per {each} ({self.full_reload_seconds:g} s from empty)"

    def reload(self) -> None:
        self.current_ammo = self.max_ammo

    def load_round(self) -> bool:
        if self.current_ammo >= self.max_ammo:
            return False
        self.current_ammo += 1
        return True

    def unload(self) -> None:
        self.current_ammo = 0

    def next_reload_step(self, loading: bool = False) -> ReloadStep | None:
        """The next reload action: None when full, EMPTY when a revolver still holding rounds has to be emptied
        before loading. `loading` is True once a reload has started."""
        if self.current_ammo == self.max_ammo:
            return None
        if self.reload_style is ReloadStyle.REVOLVER and self.current_ammo > 0 and not loading:
            return ReloadStep.EMPTY
        return LOADING_STEPS[self.reload_style]

    def take_reload_step(self, step: ReloadStep) -> str:
        """Empties the cylinder, loads a whole magazine, or loads one shell or round. Returns what happened."""
        if step is ReloadStep.EMPTY:
            self.unload()
            return "Gun unloaded. Load rounds one at a time."
        if step is ReloadStep.MAGAZINE:
            self.reload()
            return "Weapon is reloaded!"
        self.load_round()
        noun = "shell" if step is ReloadStep.SHELL else "bullet"
        return f"One {noun} loaded. {self.max_ammo - self.current_ammo} remaining."

    def fire_shot(self) -> bool:
        if self.current_ammo <= 0:
            return False
        self.current_ammo -= 1
        return True

    def fire_mode_names(self) -> str:
        return ", ".join(mode.display_name for mode in self.fire_modes)

    def describe(self, include_ammo: bool = False) -> str:
        lines = [
            f"Max Ammo: {self.max_ammo} | Damage: {self.damage}",
            f"Base Range (In Meters): {self.range_m} | Base Accuracy: {self.base_accuracy}",
            f"Max Range (In Meters): {self.max_range}",
            f"Rate of Fire: {self.rpm} rpm | Reload: {self.reload_label}",
            f"Class: {self.weapon_type.class_name} | Weapon Type: {self.weapon_type.category}",
            f"Fire Modes : {self.fire_mode_names()}",
        ]
        if self.pellets > 1:
            lines.append(f"Pellets Per Shell: {self.pellets}")
        if include_ammo:
            lines.append(f"Current Ammo : {self.current_ammo}")
        return "\n".join(lines)
