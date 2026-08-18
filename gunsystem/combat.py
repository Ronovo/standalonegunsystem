from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from gunsystem.target import Target
from gunsystem.weapon import FireMode, Weapon


@dataclass(frozen=True)
class ShotResult:
    hit: bool
    damage: int
    critical: bool
    remaining_ammo: int


def apply_range_modifier(distance: int, range_m: int, is_sniper: bool, base_result: float) -> float:
    if distance < range_m:
        close_range = range_m - distance
        steps = close_range // 50
        if is_sniper and steps > 3:
            steps = 4
        base_result -= 5 * steps
        if base_result < 0:
            base_result = 0
    elif distance > range_m:
        far_range = distance - range_m
        steps = far_range // 50
        base_result += 10 * steps
    return base_result


def apply_size_modifier(size: str, base_result: float) -> float:
    if size == "s":
        return base_result * 1.10
    if size == "l":
        return base_result * 0.90
    return base_result


def apply_spray(base_result: float, shots_in_string: int) -> float:
    if 1 < shots_in_string < 4:
        return base_result * 1.2
    if 4 <= shots_in_string <= 7:
        return base_result * 1.5
    if 7 < shots_in_string <= 10:
        return base_result * 2
    if 10 < shots_in_string <= 30:
        return base_result * 5
    if 30 < shots_in_string <= 100:
        return base_result * 10
    return base_result


def compute_damage(distance: int, range_m: int, weapon_damage: int) -> int:
    damage = weapon_damage
    if distance > range_m:
        far_range = distance - range_m
        steps = far_range // 50
        damage -= 25 * steps
    return max(0, damage)


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
    """Fire one round if ammo remains. Out of max range is always a miss."""
    rng = rng or random.Random()
    if not weapon.fire_shot():
        return ShotResult(hit=False, damage=0, critical=False, remaining_ammo=weapon.current_ammo)

    if target.distance > weapon.max_range:
        return ShotResult(hit=False, damage=0, critical=False, remaining_ammo=weapon.current_ammo)

    base_result = float(rng.randint(1, 100))
    is_sniper = weapon.weapon_type.class_name == "Sniper"
    base_result = apply_range_modifier(target.distance, weapon.range_m, is_sniper, base_result)
    base_result = apply_size_modifier(target.size, base_result)
    base_result = apply_spray(base_result, shots_in_string)

    if 0 <= base_result <= weapon.base_accuracy:
        damage = compute_damage(target.distance, weapon.range_m, weapon.damage)
        critical = rng.randint(1, 200) == 1
        if critical:
            if rng.randint(1, 100) > 20:
                damage *= 3
            else:
                damage *= 2
        return ShotResult(hit=True, damage=damage, critical=critical, remaining_ammo=weapon.current_ammo)

    return ShotResult(hit=False, damage=0, critical=False, remaining_ammo=weapon.current_ammo)
