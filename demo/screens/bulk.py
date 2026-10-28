from gunsystem import FireMode, Weapon

from demo.dummy import Dummy
from demo.dummy_catalog import prompt_new_dummy
from demo.simulation import MagazineResult, combine, plan_magazines, run_magazines
from demo.ui import formatter
from demo.ui.weapons import get_selected_weapon, set_fire_mode


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
        total_shots = 0

    magazine_count, first_mag = plan_magazines(max_ammo, total_shots)
    full_mags = magazine_count if first_mag == max_ammo else magazine_count - 1
    print("\nYou have selected " + str(full_mags) + " full magazines")
    if first_mag != max_ammo:
        print("You also have a non-full magazine with " + str(first_mag) + " in it.\n")

    selected_weapon.current_ammo = first_mag
    return magazine_count, selected_weapon


def export_report(
    selected_weapon: Weapon,
    magazine_count: int,
    new_dummy: Dummy,
    fire_mode: FireMode,
) -> None:
    print_report(run_magazines(selected_weapon, magazine_count, new_dummy, fire_mode))


def print_report(magazines: list[MagazineResult]) -> None:
    print("Breakdown by Magazine")
    print("--------------------")
    for n, magazine in enumerate(magazines, start=1):
        line = (
            f"Magazine {n}: {magazine.hits} Hits / {magazine.misses} Misses / "
            f"{magazine.destroyed} Dummies Destroyed / {magazine.damage} Damage Done"
        )
        if magazine.crits > 0:
            line += f"/ Critical Hits : {magazine.crits}"
        print(line)
    print("")

    totals = combine(magazines)
    print("Totals for All Shots")
    print("--------------------")
    print(f"{totals.accuracy}% Accuracy / {totals.destroyed} Dummies Destroyed / {totals.damage} Damage Done")
    print("------------------------------------\n")
