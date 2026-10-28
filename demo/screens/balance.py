from contextlib import redirect_stdout
from pathlib import Path

from gunsystem import FireMode, Weapon

from demo.screens.bulk import print_report
from demo.simulation import MAGAZINES_PER_RANGE, MagazineResult, balance_runs

REPORT_DIR = Path("Balance Reports")


def balance_report() -> None:
    print(f"You are about to run a balance report. This will fire {MAGAZINES_PER_RANGE} magazines for:")
    print("-All Weapons")
    print("-All Dummies")
    print("-All Ranges")
    answer = input("Press any key to continue or 1 to stop\n")
    try:
        if int(answer) == 1:
            return
    except ValueError:
        pass

    for run in balance_runs():
        write_report(*run)

    print("Report finished. You can find it in the repo's Balance Report Directory.")
    input("Press any key to return to Main Menu...")


def write_report(
    weapon: Weapon,
    fire_mode: FireMode,
    size_label: str,
    ranges: list[tuple[int, list[MagazineResult]]],
) -> None:
    report_dir = REPORT_DIR / weapon.weapon_type.class_name / weapon.name / size_label
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / (fire_mode.display_name + ".txt")
    with open(report_path, "w", encoding="utf-8") as report, redirect_stdout(report):
        print("Balance Report for " + weapon.name)
        print("------------------------------------\n")
        for distance, magazines in ranges:
            print("Results for " + str(distance) + "M")
            print("------------------------------------\n")
            print_report(magazines)
