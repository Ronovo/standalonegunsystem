from gunsystem import Catalog, FireMode, ReloadStyle, Weapon

from demo.ui import formatter


def weapon_type_menu() -> list[str]:
    print("Please select a weapon type:")
    print("----------------------")
    for index, category in enumerate(Catalog.CATEGORIES, start=1):
        print(f"{index}.) {category}")
    answer = input("Pick 1-3\n")
    try:
        choice = int(answer)
    except ValueError:
        print("Incorrect choice. Returning to Menu")
        return []
    if not 1 <= choice <= 3:
        print("Incorrect choice. Returning to Menu")
        return []
    return Catalog.names_by_category(Catalog.CATEGORIES[choice - 1])


def select_weapon_menu(weapon_list: list[str]) -> int:
    while True:
        for index, name in enumerate(weapon_list, start=1):
            print(f"{index}.) {name}")
        back = len(weapon_list) + 1
        print(f"{back}.) Return to Main Menu")
        answer = input(f"Pick 1-{back}\n")
        if answer == str(back):
            return 0
        try:
            choice = int(answer)
        except ValueError:
            print("Please enter a valid number")
            continue
        if 1 <= choice <= len(weapon_list):
            return choice
        print("Please enter a valid number")


def get_selected_weapon() -> Weapon | None:
    weapon_list = weapon_type_menu()
    if not weapon_list:
        return None
    formatter.clear()
    print("Weapons List")
    print("----------------------")
    choice = select_weapon_menu(weapon_list)
    if choice == 0:
        formatter.clear()
        return None
    weapon = Catalog.create(weapon_list[choice - 1])
    weapon.reload()
    return weapon


def set_fire_mode(selected_weapon: Weapon) -> FireMode | None:
    modes = selected_weapon.fire_modes
    for index, mode in enumerate(modes, start=1):
        print(f"{index}.) {mode.display_name}")
    back = len(modes) + 1
    print(f"{back}.) Return to Shooting Menu")
    answer = input(f"Pick 1 - {back}\n")
    try:
        choice = int(answer)
    except ValueError:
        print("Invalid Selection; Fire Mode not set")
        return None
    if choice == back:
        return None
    if 1 <= choice <= len(modes):
        return modes[choice - 1]
    print("Invalid Selection; Fire Mode not set")
    return None


def interactive_reload(weapon: Weapon) -> None:
    if weapon.current_ammo == weapon.max_ammo:
        print("Ammo already full. No need to reload")
        return

    if weapon.reload_style is ReloadStyle.SHELL:
        print("Non-Automatic Shotguns need to be manually loaded.")
        print("--------------------------------------------------")
        remaining = weapon.max_ammo - weapon.current_ammo
        while remaining != 0:
            input("Press any button to load a shell")
            weapon.load_round()
            remaining -= 1
            print(f"One shell loaded. {remaining} remaining")
        return

    if weapon.reload_style is ReloadStyle.REVOLVER:
        print("Revolvers unload when reloaded and must be manually loaded")
        print("----------------------------------------------------------")
        if weapon.current_ammo != 0:
            weapon.unload()
            print("Gun unloaded")
        remaining = weapon.max_ammo
        while remaining != 0:
            input("Press any button to load a bullet.")
            weapon.load_round()
            remaining -= 1
            print(f"One bullet loaded. {remaining} remaining")
        return

    weapon.reload()


def print_armory_display(weapon_name: str) -> None:
    selected = Catalog.create(weapon_name)
    print(f"\nYou have selected {selected.name}")
    print(selected.describe())
    print("")
    input("Press any key to return to weapon select\n")


def print_range_display(weapon: Weapon) -> None:
    print(f"\nYour current weapon is {weapon.name}")
    print(weapon.describe(include_ammo=True))
    print("")
    input("Press any key to return to Shooting Menu\n")
