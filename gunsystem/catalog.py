from typing import NamedTuple

from gunsystem.weapon import FireMode, ReloadStyle, Weapon, WeaponType

S = FireMode.SINGLE
B = FireMode.BURST
A = FireMode.AUTO
MAG = ReloadStyle.MAGAZINE
SHELL = ReloadStyle.SHELL
REV = ReloadStyle.REVOLVER
PISTOL = WeaponType("Pistol", "Small Arms", spray_control=1.4, crit_chance=3)
SMG = WeaponType("SMG", "Small Arms", spray_control=1.2, crit_chance=1)
SHOTGUN = WeaponType("Shotgun", "Medium Arms", crit_chance=2)
ASSAULT = WeaponType("Assault", "Medium Arms", crit_chance=2)
SNIPER = WeaponType("Sniper", "Large Arms", close_range_step=5, max_close_steps=4, crit_chance=10)
LMG = WeaponType("LMG", "Large Arms", spray_control=0.8, crit_chance=1)


class Spec(NamedTuple):
    name: str
    max_ammo: int
    damage: int
    range_m: int
    max_range: int
    base_accuracy: int
    weapon_type: WeaponType
    fire_modes: tuple[FireMode, ...]
    reload_style: ReloadStyle
    rpm: int
    reload_seconds: float
    pellets: int = 1


_WEAPONS: tuple[Spec, ...] = (
    Spec("M1911", 7, 50, 100, 200, 80, PISTOL, (S,), MAG, 90, 2.0),
    Spec("USP .45", 12, 75, 100, 250, 75, PISTOL, (S,), MAG, 90, 2.0),
    Spec("M9", 15, 50, 150, 300, 70, PISTOL, (S,), MAG, 90, 2.0),
    Spec("Desert Eagle", 7, 100, 150, 300, 65, PISTOL, (S,), MAG, 60, 2.5),
    Spec("Glock 18", 18, 50, 150, 300, 75, PISTOL, (S, A), MAG, 1200, 2.0),
    Spec(".38 Special", 6, 50, 100, 200, 75, PISTOL, (S,), REV, 60, 0.8),
    Spec("44 Magnum", 6, 100, 150, 300, 85, PISTOL, (S,), REV, 50, 0.8),
    Spec("MP5", 30, 50, 200, 300, 80, SMG, (S, A), MAG, 800, 2.5),
    Spec("AK-47u", 30, 75, 200, 350, 75, SMG, (S, A), MAG, 700, 2.5),
    Spec("P90", 50, 75, 200, 250, 70, SMG, (S, A), MAG, 900, 3.0),
    Spec("Mini-Uzi", 32, 50, 100, 250, 60, SMG, (S, A), MAG, 950, 2.5),
    Spec("W1200", 7, 75, 100, 150, 90, SHOTGUN, (S,), SHELL, 40, 0.6, 8),
    Spec("M1014", 4, 100, 100, 150, 90, SHOTGUN, (S,), SHELL, 120, 0.6, 8),
    Spec("USAS-12", 10, 75, 100, 200, 90, SHOTGUN, (S, A), MAG, 300, 3.0, 8),
    Spec("Spas-12", 8, 100, 100, 200, 90, SHOTGUN, (S,), SHELL, 100, 0.6, 8),
    Spec("M16A4", 30, 75, 200, 450, 80, ASSAULT, (S, B, A), MAG, 800, 2.5),
    Spec("AK47", 30, 100, 200, 450, 80, ASSAULT, (S, B, A), MAG, 600, 2.5),
    Spec("G3", 20, 75, 300, 500, 80, ASSAULT, (S, B, A), MAG, 550, 3.0),
    Spec("G36", 30, 75, 300, 500, 75, ASSAULT, (S, B, A), MAG, 750, 2.5),
    Spec("FN FAL", 20, 100, 250, 500, 80, ASSAULT, (S, B, A), MAG, 650, 3.0),
    Spec("M40A3", 5, 100, 500, 500, 80, SNIPER, (S,), MAG, 20, 3.0),
    Spec("Dragunov", 20, 75, 500, 500, 80, SNIPER, (S,), MAG, 40, 3.0),
    Spec("Barrett .50Cal", 10, 200, 500, 500, 70, SNIPER, (S,), MAG, 30, 4.0),
    Spec("M249 SAW", 100, 75, 300, 500, 80, LMG, (S, A), MAG, 850, 6.0),
    Spec("M60E4", 100, 50, 250, 500, 70, LMG, (S, A), MAG, 550, 7.0),
    Spec("RPD", 100, 50, 350, 500, 70, LMG, (S, A), MAG, 650, 6.0),
)

_BY_NAME = {spec.name: spec for spec in _WEAPONS}


class Catalog:
    CATEGORIES = ("Small Arms", "Medium Arms", "Large Arms")

    @classmethod
    def create(cls, name: str) -> Weapon:
        spec = _BY_NAME.get(name)
        if spec is None:
            raise KeyError(f"Unknown weapon: {name}")
        return Weapon(**spec._asdict())

    @classmethod
    def names(cls, category: str | None = None) -> list[str]:
        return [spec.name for spec in _WEAPONS if category is None or spec.weapon_type.category == category]

    @classmethod
    def all(cls) -> list[Weapon]:
        return [cls.create(spec.name) for spec in _WEAPONS]

    @classmethod
    def by_class(cls, category: str | None = None) -> dict[str, list[Weapon]]:
        groups: dict[str, list[Weapon]] = {}
        for name in cls.names(category):
            weapon = cls.create(name)
            groups.setdefault(weapon.weapon_type.class_name, []).append(weapon)
        return groups
