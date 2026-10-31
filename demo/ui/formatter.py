import os

from gunsystem.util import to_int


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def choose(options: list[str], back: str | None = None, invalid: str = "Incorrect choice. Try again.",
           retry: bool = True) -> int | None:
    """Prints a numbered menu and returns the 0-based pick. Returns None for the back option, or for a bad answer
    when retry is off."""
    while True:
        for index, option in enumerate(options, start=1):
            print(f"{index}.) {option}")
        last = len(options) + (1 if back else 0)
        if back:
            print(f"{last}.) {back}")
        choice = to_int(input(f"Pick 1-{last}\n"), 0)
        if 1 <= choice <= len(options):
            return choice - 1
        if back and choice == last:
            return None
        print(invalid)
        if not retry:
            return None
