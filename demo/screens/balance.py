import os
import sys
from pathlib import Path

from gunsystem import Catalog, FireMode, Weapon

from demo.dummy import SIZE_LABELS, Dummy, create_dummy
from demo.dummy_catalog import RANGES
from demo.screens import bulk


def balance_report() -> None:
    print("You are about to run a balance report. This will fire 3 magazines for:")
    print("-All Weapons")
    print("-All Dummies")
    print("-All Ranges")
    answer = input("Press any key to continue or 1 to stop\n")
    try:
        if int(answer) == 1:
            return
    except ValueError:
        pass

    path = Path.cwd() / "Balance Reports"
    path.mkdir(exist_ok=True)

    for selected_weapon in Catalog.all():
        weapon_type_path = path / selected_weapon.weapon_type.class_name
        weapon_type_path.mkdir(exist_ok=True)
        weapon_path = weapon_type_path / selected_weapon.name
        weapon_path.mkdir(exist_ok=True)

        selected_weapon.reload()
        for fire_mode in selected_weapon.fire_modes:
            shoot_dummy_by_size(selected_weapon, weapon_type_path, fire_mode)

    sys.stdout = sys.__stdout__
    print("Report finished. You can find it in the repo's Balance Report Directory.")
    input("Press any key to return to Main Menu...")


def run_calculations_on_dummy(new_dummy: Dummy, selected_weapon: Weapon, fire_mode: FireMode) -> None:
    for next_range in RANGES:
        print("Results for " + str(next_range) + "M")
        print("------------------------------------\n")
        new_dummy.distance = next_range
        bulk.export_report(selected_weapon, 3, new_dummy, fire_mode)
        selected_weapon.reload()


def shoot_dummy_by_size(selected_weapon: Weapon, weapon_type_path: Path, fire_mode: FireMode) -> None:
    for dummy_size in SIZE_LABELS:
        fire_mode_path = weapon_type_path / selected_weapon.name / dummy_size
        fire_mode_path.mkdir(parents=True, exist_ok=True)

        filename = fire_mode.display_name + ".txt"
        sys.stdout = open(os.path.join(fire_mode_path, filename), "w", encoding="utf-8")
        new_dummy = create_dummy(dummy_size)
        print("Balance Report for " + selected_weapon.name)
        print("------------------------------------\n")
        run_calculations_on_dummy(new_dummy, selected_weapon, fire_mode)
