from gunsystem.simulation import MAGAZINES_PER_RANGE, balance_runs, write_report


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

