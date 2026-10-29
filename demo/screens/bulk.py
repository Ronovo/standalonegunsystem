from gunsystem import Weapon

from demo.dummy_catalog import prompt_new_dummy
from gunsystem.simulation import plan_magazines, report_lines, run_magazines
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
    print("\n".join(report_lines(run_magazines(selected_weapon, magazine_count, new_dummy, fire_mode))))
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
