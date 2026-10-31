from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from gunsystem import Catalog, FireMode, ShotResult, Weapon, advance_string, resolve_shot
from gunsystem.dummy import RANGES, Dummy
from gunsystem.target import SIZES

MAGAZINES_PER_RANGE = 15
MAX_BULK_SHOTS = 1000
REPORT_DIR = Path("Balance Reports")
RULE = "-" * 36


@dataclass
class MagazineResult:
    hits: int = 0
    misses: int = 0
    destroyed: int = 0
    damage: int = 0
    crits: int = 0

    @property
    def shots(self) -> int:
        return self.hits + self.misses

    @property
    def accuracy(self) -> float:
        return round(self.hits / self.shots * 100, 2) if self.shots else 0.0


def combine(magazines: list[MagazineResult]) -> MagazineResult:
    return MagazineResult(
        hits=sum(m.hits for m in magazines),
        misses=sum(m.misses for m in magazines),
        destroyed=sum(m.destroyed for m in magazines),
        damage=sum(m.damage for m in magazines),
        crits=sum(m.crits for m in magazines),
    )


def report_lines(magazines: list[MagazineResult]) -> list[str]:
    lines = ["Breakdown by Magazine", "--------------------"]
    for n, magazine in enumerate(magazines, start=1):
        line = (
            f"Magazine {n}: {magazine.hits} Hits / {magazine.misses} Misses / "
            f"{magazine.destroyed} Dummies Destroyed / {magazine.damage} Damage Done"
        )
        if magazine.crits > 0:
            line += f" / Critical Hits: {magazine.crits}"
        lines.append(line)
    totals = combine(magazines)
    return lines + [
        "",
        "Totals for All Shots",
        "--------------------",
        f"{totals.accuracy}% Accuracy / {totals.destroyed} Dummies Destroyed / {totals.damage} Damage Done",
        RULE,
        "",
    ]


def write_report(
    weapon: Weapon,
    fire_mode: FireMode,
    size: str,
    ranges: list[tuple[int, list[MagazineResult]]],
) -> None:
    report_dir = REPORT_DIR / weapon.weapon_type.class_name / weapon.name / SIZES[size].label
    report_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"Balance Report for {weapon.name}", RULE, ""]
    for distance, magazines in ranges:
        lines += [f"Results for {distance}M", RULE, "", *report_lines(magazines)]
    (report_dir / (fire_mode.display_name + ".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")


def plan_magazines(max_ammo: int, total_shots: int) -> tuple[int, int]:
    """Return (magazine_count, ammo_in_first_magazine). Fewer than 1 shot means one full magazine, and more than
    MAX_BULK_SHOTS means MAX_BULK_SHOTS."""
    if total_shots < 1:
        total_shots = max_ammo
    total_shots = min(total_shots, MAX_BULK_SHOTS)
    if total_shots < max_ammo:
        return 1, total_shots
    magazine_count = total_shots // max_ammo
    extra = total_shots % max_ammo
    if extra > 0:
        return magazine_count + 1, extra
    return magazine_count, max_ammo


def run_magazines(weapon: Weapon, magazine_count: int, dummy: Dummy, fire_mode: FireMode) -> list[MagazineResult]:
    """Empty the current magazine, then reload and empty until magazine_count magazines are fired. Each trigger
    pull starts a new string, as on the range."""
    dummy.reset_health()
    magazines = []
    for n in range(magazine_count):
        if n > 0:
            weapon.reload()
        magazine = MagazineResult()
        while weapon.current_ammo > 0:
            for result, _ in pull_trigger(weapon, dummy, fire_mode, weapon.rounds_per_pull):
                if result.hit:
                    magazine.hits += 1
                    magazine.crits += result.critical
                    magazine.damage += result.damage
                else:
                    magazine.misses += 1
            if dummy.is_destroyed():
                magazine.destroyed += 1
                dummy.reset_health()
        magazines.append(magazine)
    return magazines


def run_bulk(weapon: Weapon, total_shots: int, dummy: Dummy, fire_mode: FireMode) -> list[MagazineResult]:
    magazine_count, first_magazine = plan_magazines(weapon.max_ammo, total_shots)
    weapon.current_ammo = first_magazine
    return run_magazines(weapon, magazine_count, dummy, fire_mode)


def shots_for_trigger(weapon: Weapon, fire_mode: FireMode, requested: int = 1) -> int:
    if fire_mode is FireMode.AUTO:
        return min(max(requested, 1), weapon.current_ammo)
    if fire_mode is FireMode.BURST:
        return min(3, weapon.current_ammo)
    return min(1, weapon.current_ammo)


def pull_trigger(
    weapon: Weapon, dummy: Dummy, fire_mode: FireMode, requested: int = 1
) -> list[tuple[ShotResult, int]]:
    """Fire one trigger pull at the dummy. Returns each shot with the dummy's health after it."""
    shots = []
    shots_in_string = 0
    for _ in range(shots_for_trigger(weapon, fire_mode, requested)):
        shots_in_string = advance_string(fire_mode, shots_in_string)
        result = resolve_shot(weapon, dummy, shots_in_string)
        if result.hit:
            dummy.take_damage(result.damage)
        shots.append((result, dummy.health))
        if dummy.is_destroyed():
            break
    return shots


def balance_runs(
    magazines_per_range: int = MAGAZINES_PER_RANGE,
) -> Iterator[tuple[Weapon, FireMode, str, list[tuple[int, list[MagazineResult]]]]]:
    for weapon in Catalog.all():
        weapon.reload()
        for fire_mode in weapon.fire_modes:
            for size in SIZES:
                dummy = Dummy(size)
                ranges = []
                for distance in RANGES:
                    dummy.distance = distance
                    ranges.append((distance, run_magazines(weapon, magazines_per_range, dummy, fire_mode)))
                    weapon.reload()
                yield weapon, fire_mode, size, ranges
