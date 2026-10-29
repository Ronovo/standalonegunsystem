from typing import NamedTuple

from gunsystem.weapon import FireMode, ReloadStyle, Weapon, WeaponType

S = FireMode.SINGLE
B = FireMode.BURST
A = FireMode.AUTO
MAG = ReloadStyle.MAGAZINE
SHELL = ReloadStyle.SHELL
REV = ReloadStyle.REVOLVER
SNIPER = WeaponType(class_name="Sniper", category="Large Arms", close_range_step=5, max_close_steps=4)


def _type(class_name: str, category: str) -> WeaponType:
    return WeaponType(class_name=class_name, category=category)


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


_WEAPONS: tuple[Spec, ...] = (
    Spec("M1911", 7, 50, 100, 200, 80, _type("Pistol", "Small Arms"), (S,), MAG),
    Spec("USP .45", 12, 75, 100, 250, 75, _type("Pistol", "Small Arms"), (S,), MAG),
    Spec("M9", 15, 50, 150, 300, 70, _type("Pistol", "Small Arms"), (S,), MAG),
    Spec("Desert Eagle", 7, 100, 200, 300, 70, _type("Pistol", "Small Arms"), (S,), MAG),
    Spec("Glock 18", 18, 50, 150, 300, 75, _type("Pistol", "Small Arms"), (S, A), MAG),
    Spec(".38 Special", 6, 50, 100, 200, 75, _type("Pistol", "Small Arms"), (S,), REV),
    Spec("44 Magnum", 6, 100, 150, 300, 85, _type("Pistol", "Small Arms"), (S,), REV),
    Spec("MP5", 30, 50, 200, 300, 80, _type("SMG", "Small Arms"), (S, A), MAG),
    Spec("AK-47u", 30, 75, 200, 350, 75, _type("SMG", "Small Arms"), (S, A), MAG),
    Spec("P90", 50, 75, 200, 250, 70, _type("SMG", "Small Arms"), (S, A), MAG),
    Spec("Mini-Uzi", 32, 50, 100, 250, 60, _type("SMG", "Small Arms"), (S, A), MAG),
    Spec("W1200", 7, 75, 50, 150, 90, _type("Shotgun", "Medium Arms"), (S,), SHELL),
    Spec("M1014", 4, 100, 50, 150, 90, _type("Shotgun", "Medium Arms"), (S,), SHELL),
    Spec("USAS-12", 10, 75, 100, 200, 90, _type("Shotgun", "Medium Arms"), (S, A), MAG),
    Spec("Spas-12", 8, 100, 100, 200, 90, _type("Shotgun", "Medium Arms"), (S,), SHELL),
    Spec("M16A4", 30, 75, 200, 450, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    Spec("AK47", 30, 100, 200, 450, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    Spec("G3", 20, 75, 300, 500, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    Spec("G36", 30, 100, 400, 500, 75, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    Spec("FN FAL", 20, 100, 250, 500, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    Spec("M40A3", 5, 100, 500, 500, 80, SNIPER, (S,), MAG),
    Spec("Dragunov", 20, 75, 500, 500, 80, SNIPER, (S,), MAG),
    Spec("Barrett .50Cal", 1, 200, 500, 500, 70, SNIPER, (S,), MAG),
    Spec("M249 SAW", 100, 75, 300, 500, 80, _type("LMG", "Large Arms"), (S, A), MAG),
    Spec("M60E4", 100, 50, 250, 500, 70, _type("LMG", "Large Arms"), (S, A), MAG),
    Spec("RPD", 100, 50, 350, 500, 70, _type("LMG", "Large Arms"), (S, A), MAG),
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
