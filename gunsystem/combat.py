from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from gunsystem.target import COVER, MOVING_PENALTY, SIZES, Target
from gunsystem.weapon import FireMode, Weapon, WeaponType

_RNG = random.Random()
BAND_M = 50
MIN_DAMAGE = 25
# A to-hit roll at or under NATURAL_HIT always lands and one at or over NATURAL_MISS never does.
NATURAL_HIT = 2
NATURAL_MISS = 99
# Percent of the base damage a hit does, rolled per hit.
DAMAGE_SPREAD = (85, 115)
CRIT_ROLL = 1000
# (shots in the string above which it applies, roll multiplier), widest spray first.
SPRAY_TIERS = ((30, 10), (10, 5), (7, 2), (3, 1.5), (1, 1.2))


@dataclass(frozen=True)
class ShotResult:
    hit: bool
    damage: int
    critical: bool
    remaining_ammo: int
    fired: bool
    pellets_hit: int = 0


def bands(meters: int) -> int:
    """Whole 50 m bands in a distance; none for a negative one."""
    return max(0, meters) // BAND_M


def apply_spray(base_result: float, shots_in_string: int, control: float = 1.0) -> float:
    for above, multiplier in SPRAY_TIERS:
        if shots_in_string > above:
            return base_result * (1 + (multiplier - 1) * control)
    return base_result


def apply_size_modifier(size: str, base_result: float) -> float:
    return base_result * SIZES[size].to_hit


def apply_range_modifier(distance: int, range_m: int, weapon_type: WeaponType, base_result: float) -> float:
    if distance < range_m:
        steps = min(bands(range_m - distance), weapon_type.max_close_steps)
        return base_result + weapon_type.close_range_step * steps
    return base_result + 10 * bands(distance - range_m)


def apply_cover_modifier(target: Target, base_result: float) -> float:
    return base_result + COVER[target.cover] + (MOVING_PENALTY if target.moving else 0)


def compute_damage(distance: int, range_m: int, max_range: int, weapon_damage: int) -> int:
    """Full damage out to range_m, then a straight line down to MIN_DAMAGE at max_range, in 50 m bands."""
    total = bands(max_range - range_m)
    if total == 0:
        return weapon_damage
    far = min(bands(distance - range_m), total)
    floor = min(MIN_DAMAGE, weapon_damage)
    return round(weapon_damage - (weapon_damage - floor) * far / total)


def advance_string(fire_mode: FireMode, shots_in_string: int) -> int:
    if fire_mode is FireMode.SINGLE:
        return 1
    if fire_mode is FireMode.BURST:
        return 1 if shots_in_string >= 3 else shots_in_string + 1
    return shots_in_string + 1


def lands(roll: int, weapon: Weapon, target: Target, shots_in_string: int = 1) -> bool:
    """Whether a to-hit roll of 1-100 lands once spray, size, range and cover have moved it."""
    if roll <= NATURAL_HIT:
        return True
    if roll >= NATURAL_MISS:
        return False
    result = apply_spray(float(roll), shots_in_string, weapon.weapon_type.spray_control)
    result = apply_size_modifier(target.size, result)
    result = apply_range_modifier(target.distance, weapon.range_m, weapon.weapon_type, result)
    result = apply_cover_modifier(target, result)
    return result <= weapon.base_accuracy


def hit_chance(weapon: Weapon, target: Target, shots_in_string: int = 1) -> float:
    """The chance (0-1) that a shot lands, worked out from the same modifiers resolve_shot rolls against. A
    shotgun shot lands when any of its pellets does."""
    if target.distance > weapon.max_range:
        return 0.0
    per_pellet = sum(lands(roll, weapon, target, shots_in_string) for roll in range(1, 101)) / 100
    return 1 - (1 - per_pellet) ** weapon.pellets


def resolve_shot(
    weapon: Weapon,
    target: Target,
    shots_in_string: int = 1,
    rng: Optional[random.Random] = None,
) -> ShotResult:
    """Fire one round if ammo remains. Out of max range is a miss. A shotgun does the share of its damage that
    its pellets land."""
    rng = rng or _RNG
    if not weapon.fire_shot():
        return _miss(weapon, fired=False)
    if target.distance > weapon.max_range:
        return _miss(weapon)

    pellets_hit = sum(lands(rng.randint(1, 100), weapon, target, shots_in_string) for _ in range(weapon.pellets))
    if pellets_hit == 0:
        return _miss(weapon)

    damage = compute_damage(target.distance, weapon.range_m, weapon.max_range, weapon.damage)
    damage = round(damage * pellets_hit / weapon.pellets * rng.randint(*DAMAGE_SPREAD) / 100)
    critical = rng.randint(1, CRIT_ROLL) <= weapon.weapon_type.crit_chance * (CRIT_ROLL // 100)
    if critical:
        damage *= 3 if rng.randint(1, 100) > 20 else 2
    return ShotResult(
        hit=True, damage=damage, critical=critical, remaining_ammo=weapon.current_ammo, fired=True,
        pellets_hit=pellets_hit,
    )


def _miss(weapon: Weapon, fired: bool = True) -> ShotResult:
    return ShotResult(hit=False, damage=0, critical=False, remaining_ammo=weapon.current_ammo, fired=fired)
