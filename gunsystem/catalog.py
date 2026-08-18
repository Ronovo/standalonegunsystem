from gunsystem.weapon import FireMode, ReloadStyle, Weapon, WeaponType

S = FireMode.SINGLE
B = FireMode.BURST
A = FireMode.AUTO
MAG = ReloadStyle.MAGAZINE
SHELL = ReloadStyle.SHELL
REV = ReloadStyle.REVOLVER


def _type(class_name: str, category: str) -> WeaponType:
    return WeaponType(class_name=class_name, category=category)


# name, max_ammo, damage, range_m, max_range, accuracy, type, fire_modes, reload
_WEAPONS: tuple[tuple, ...] = (
    ("M1911", 7, 50, 100, 200, 80, _type("Pistol", "Small Arms"), (S,), MAG),
    ("USP .45", 12, 75, 100, 250, 75, _type("Pistol", "Small Arms"), (S,), MAG),
    ("M9", 15, 50, 150, 300, 70, _type("Pistol", "Small Arms"), (S,), MAG),
    ("Desert Eagle", 7, 100, 200, 300, 70, _type("Pistol", "Small Arms"), (S,), MAG),
    ("Glock 18", 18, 50, 150, 300, 75, _type("Pistol", "Small Arms"), (S, A), MAG),
    (".38 Special", 6, 50, 100, 200, 75, _type("Pistol", "Small Arms"), (S,), REV),
    ("44 Magnum", 6, 100, 150, 300, 85, _type("Pistol", "Small Arms"), (S,), REV),
    ("MP5", 30, 50, 200, 300, 80, _type("SMG", "Small Arms"), (S, A), MAG),
    ("AK-47u", 30, 75, 200, 350, 75, _type("SMG", "Small Arms"), (S, A), MAG),
    ("P90", 50, 75, 200, 250, 70, _type("SMG", "Small Arms"), (S, A), MAG),
    ("Mini-Uzi", 32, 50, 100, 250, 60, _type("SMG", "Small Arms"), (S, A), MAG),
    ("W1200", 7, 75, 50, 150, 90, _type("Shotgun", "Medium Arms"), (S,), SHELL),
    ("M1014", 4, 100, 50, 150, 90, _type("Shotgun", "Medium Arms"), (S,), SHELL),
    ("USAS-12", 10, 75, 100, 200, 90, _type("Shotgun", "Medium Arms"), (S, A), MAG),
    ("Spas-12", 8, 100, 100, 200, 90, _type("Shotgun", "Medium Arms"), (S,), SHELL),
    ("M16A4", 30, 75, 200, 450, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    ("AK47", 30, 100, 200, 450, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    ("G3", 20, 75, 300, 500, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    ("G36", 30, 100, 400, 500, 75, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    ("FN FAL", 20, 100, 250, 500, 80, _type("Assault", "Medium Arms"), (S, B, A), MAG),
    ("M40A3", 5, 100, 500, 500, 80, _type("Sniper", "Large Arms"), (S,), MAG),
    ("Dragunov", 20, 75, 500, 500, 80, _type("Sniper", "Large Arms"), (S,), MAG),
    ("Barrett .50Cal", 1, 200, 500, 500, 70, _type("Sniper", "Large Arms"), (S,), MAG),
    ("M249 SAW", 100, 75, 300, 500, 80, _type("LMG", "Large Arms"), (S, A), MAG),
    ("M60E4", 100, 50, 250, 500, 70, _type("LMG", "Large Arms"), (S, A), MAG),
    ("RPD", 100, 50, 350, 500, 70, _type("LMG", "Large Arms"), (S, A), MAG),
)


def _from_spec(spec: tuple) -> Weapon:
    name, max_ammo, damage, range_m, max_range, accuracy, weapon_type, fire_modes, reload_style = spec
    return Weapon(
        name=name,
        max_ammo=max_ammo,
        damage=damage,
        range_m=range_m,
        max_range=max_range,
        base_accuracy=accuracy,
        weapon_type=weapon_type,
        fire_modes=fire_modes,
        reload_style=reload_style,
    )


_BY_NAME = {spec[0]: spec for spec in _WEAPONS}


class Catalog:
    CATEGORIES = ("Small Arms", "Medium Arms", "Large Arms")

    @classmethod
    def create(cls, name: str) -> Weapon:
        spec = _BY_NAME.get(name)
        if spec is None:
            raise KeyError(f"Unknown weapon: {name}")
        return _from_spec(spec)

    @classmethod
    def names(cls) -> list[str]:
        return [spec[0] for spec in _WEAPONS]

    @classmethod
    def names_by_category(cls, category: str) -> list[str]:
        return [spec[0] for spec in _WEAPONS if spec[6].category == category]

    @classmethod
    def all(cls) -> list[Weapon]:
        return [_from_spec(spec) for spec in _WEAPONS]
