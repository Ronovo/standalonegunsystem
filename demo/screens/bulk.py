from gunsystem import FireMode, Weapon, advance_string, resolve_shot

from demo.dummy import Dummy
from demo.dummy_catalog import prompt_new_dummy
from demo.ui import formatter
from demo.ui.weapons import get_selected_weapon, set_fire_mode


def plan_magazines(max_ammo: int, total_shots: int) -> tuple[int, int]:
    """Return (magazine_count, ammo_in_first_magazine)."""
    if total_shots <= 0:
        return 0, 0
    if total_shots < max_ammo:
        return 1, total_shots
    magazine_count = total_shots // max_ammo
    extra = total_shots % max_ammo
    if extra > 0:
        return magazine_count + 1, extra
    return magazine_count, max_ammo


def bulk_shots() -> None:
    print("Bulk Report")

    selected_weapon = get_selected_weapon()
    if selected_weapon is None:
        return

    magazine_count, selected_weapon = get_total_magazine_count(selected_weapon)
    formatter.clear()

    new_dummy = prompt_new_dummy(False)
    formatter.clear()
    fire_mode = set_fire_mode(selected_weapon)
    if fire_mode is None:
        fire_mode = selected_weapon.fire_modes[0]
    formatter.clear()
    export_report(selected_weapon, magazine_count, new_dummy, fire_mode)
    input("Press any key to return to Main Menu...")


def get_total_magazine_count(selected_weapon: Weapon) -> tuple[int, Weapon]:
    max_ammo = selected_weapon.max_ammo

    print("Your weapon currently has " + str(max_ammo) + " bullets per magazine.")
    answer = input("How many shots do you want to test?\n")
    try:
        total_shots = int(answer)
    except ValueError:
        total_shots = max_ammo

    magazine_count, first_mag = plan_magazines(max_ammo, total_shots)
    full_mags = magazine_count if first_mag == max_ammo else magazine_count - 1
    print("\nYou have selected " + str(full_mags) + " full magazines")
    if first_mag != max_ammo and first_mag > 0:
        print("You also have a non-full magazine with " + str(first_mag) + " in it.\n")

    selected_weapon.current_ammo = first_mag
    return magazine_count, selected_weapon


def get_report(
    selected_weapon: Weapon,
    magazine_count: int,
    new_dummy: Dummy,
    fire_mode: FireMode,
) -> tuple[list[str], list[int]]:
    n = 1
    magazine_array = []
    total_hits = 0
    total_misses = 0
    total_damage = 0
    total_dummy = 0
    new_dummy.reset_health()

    while magazine_count > 0:
        magazine_count -= 1
        hits = 0
        misses = 0
        dead_dummy = 0
        mag_damage = 0
        crits = 0
        shots_in_string = 0
        magazine_string = "Magazine " + str(n) + ": "
        while selected_weapon.current_ammo > 0:
            shots_in_string = advance_string(fire_mode, shots_in_string)
            result = resolve_shot(selected_weapon, new_dummy, shots_in_string)
            if result.hit:
                if result.critical:
                    crits += 1
                hits += 1
                mag_damage += result.damage
                new_dummy.take_damage(result.damage)
                total_damage += result.damage
                if new_dummy.is_destroyed():
                    dead_dummy += 1
                    new_dummy.reset_health()
            else:
                misses += 1
        total_hits += hits
        total_misses += misses
        total_dummy += dead_dummy
        if magazine_count > 0:
            selected_weapon.reload()
        magazine_string = (
            magazine_string
            + str(hits)
            + " Hits / "
            + str(misses)
            + " Misses / "
            + str(dead_dummy)
            + " Dummies Destroyed / "
            + str(mag_damage)
            + " Damage Done"
        )
        if crits > 0:
            magazine_string = magazine_string + "/ Critical Hits : " + str(crits)

        magazine_array.append(magazine_string)
        n += 1

    total_array = [total_hits, total_misses, total_dummy, total_damage]
    return magazine_array, total_array


def export_report(
    selected_weapon: Weapon,
    magazine_count: int,
    new_dummy: Dummy,
    fire_mode: FireMode,
) -> None:
    report_result = get_report(selected_weapon, magazine_count, new_dummy, fire_mode)

    magazine_array = report_result[0]
    print("Breakdown by Magazine")
    print("--------------------")
    for line in magazine_array:
        print(line)
    print("")
    total_array = report_result[1]
    total_hits = total_array[0]
    total_miss = total_array[1]
    total_shots = total_hits + total_miss
    total_dummy = total_array[2]
    total_damage = total_array[3]

    if total_shots == 0:
        accuracy = 0.0
    else:
        accuracy = round((total_hits / total_shots) * 100, 2)

    print("Totals for All Shots")
    print("--------------------")
    print(
        str(accuracy)
        + "% Accuracy / "
        + str(total_dummy)
        + " Dummies Destroyed / "
        + str(total_damage)
        + " Damage Done"
    )
    print("------------------------------------\n")
