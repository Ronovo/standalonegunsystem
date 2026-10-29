from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from gunsystem.target import SIZE_MODIFIERS, Target
from gunsystem.weapon import FireMode, Weapon, WeaponType

_RNG = random.Random()


@dataclass(frozen=True)
class ShotResult:
    hit: bool
    damage: int
    critical: bool
    remaining_ammo: int
    fired: bool


def apply_range_modifier(
    distance: int, range_m: int, weapon_type: WeaponType, base_result: float
) -> float:
    if distance < range_m:
        close_range = range_m - distance
        steps = min(close_range // 50, weapon_type.max_close_steps)
        base_result += weapon_type.close_range_step * steps
        if base_result < 0:
            base_result = 0
    else:
        base_result += 10 * far_range_steps(distance, range_m)
    return base_result


def apply_size_modifier(size: str, base_result: float) -> float:
    return base_result * SIZE_MODIFIERS[size]


def apply_spray(base_result: float, shots_in_string: int) -> float:
    if 1 < shots_in_string < 4:
        return base_result * 1.2
    if 4 <= shots_in_string <= 7:
        return base_result * 1.5
    if 7 < shots_in_string <= 10:
        return base_result * 2
    if 10 < shots_in_string <= 30:
        return base_result * 5
    if shots_in_string > 30:
        return base_result * 10
    return base_result


def far_range_steps(distance: int, range_m: int) -> int:
    """Whole 50 m bands past the weapon's effective range."""
    return max(0, distance - range_m) // 50


def compute_damage(distance: int, range_m: int, weapon_damage: int) -> int:
    return max(0, weapon_damage - 25 * far_range_steps(distance, range_m))


def advance_string(fire_mode: FireMode, shots_in_string: int) -> int:
    if fire_mode is FireMode.SINGLE:
        return 1
    if fire_mode is FireMode.BURST:
        return 1 if shots_in_string >= 3 else shots_in_string + 1
    return shots_in_string + 1


def resolve_shot(
    weapon: Weapon,
    target: Target,
    shots_in_string: int = 1,
    rng: Optional[random.Random] = None,
) -> ShotResult:
    """Fire one round if ammo remains. Out of max range or zero damage after falloff is a miss."""
    rng = rng or _RNG
    if not weapon.fire_shot():
        return _miss(weapon, fired=False)

    if target.distance > weapon.max_range:
        return _miss(weapon)

    # Spray scales the raw roll before the range modifier clamps at 0.
    base_result = apply_spray(float(rng.randint(1, 100)), shots_in_string)
    base_result = apply_range_modifier(target.distance, weapon.range_m, weapon.weapon_type, base_result)
    base_result = apply_size_modifier(target.size, base_result)
    if base_result > weapon.base_accuracy:
        return _miss(weapon)

    damage = compute_damage(target.distance, weapon.range_m, weapon.damage)
    if damage == 0:
        return _miss(weapon)

    critical = rng.randint(1, 200) == 1
    if critical:
        if rng.randint(1, 100) > 20:
            damage *= 3
        else:
            damage *= 2
    return ShotResult(hit=True, damage=damage, critical=critical, remaining_ammo=weapon.current_ammo, fired=True)


def _miss(weapon: Weapon, fired: bool = True) -> ShotResult:
    return ShotResult(hit=False, damage=0, critical=False, remaining_ammo=weapon.current_ammo, fired=fired)
