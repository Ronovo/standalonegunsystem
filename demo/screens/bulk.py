from gunsystem.simulation import MAX_BULK_SHOTS, plan_magazines, report_lines, run_bulk
from demo.ui import formatter
from demo.ui.dummies import prompt_new_dummy
from demo.ui.weapons import get_selected_weapon, set_fire_mode


def bulk_shots() -> None:
    print("Bulk Report")

    selected_weapon = get_selected_weapon()
    if selected_weapon is None:
        return

    total_shots = ask_total_shots(selected_weapon.max_ammo)
    formatter.clear()

    new_dummy = prompt_new_dummy(False)
    formatter.clear()
    fire_mode = set_fire_mode(selected_weapon) or selected_weapon.fire_modes[0]
    formatter.clear()
    print("\n".join(report_lines(run_bulk(selected_weapon, total_shots, new_dummy, fire_mode))))
    input("Press any key to return to Main Menu...")


def ask_total_shots(max_ammo: int) -> int:
    print(f"Your weapon currently has {max_ammo} bullets per magazine.")
    answer = input(f"How many shots do you want to test? (up to {MAX_BULK_SHOTS})\n")
    try:
        total_shots = int(answer)
    except ValueError:
        total_shots = 0

    magazine_count, first_mag = plan_magazines(max_ammo, total_shots)
    full_mags = magazine_count if first_mag == max_ammo else magazine_count - 1
    print(f"\nYou have selected {full_mags} full magazines")
    if first_mag != max_ammo:
        print(f"You also have a non-full magazine with {first_mag} in it.\n")
    return total_shots
