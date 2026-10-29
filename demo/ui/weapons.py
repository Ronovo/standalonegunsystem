from gunsystem import Catalog, FireMode, ReloadStyle, Weapon

from demo.ui import formatter


def weapon_type_menu() -> list[str]:
    print("Please select a weapon type:")
    print("----------------------")
    choice = formatter.choose(list(Catalog.CATEGORIES), invalid="Incorrect choice. Returning to Menu", retry=False)
    return [] if choice is None else Catalog.names_by_category(Catalog.CATEGORIES[choice])


def select_weapon_menu(weapon_list: list[str]) -> int | None:
    return formatter.choose(weapon_list, back="Return to Main Menu", invalid="Please enter a valid number")


def get_selected_weapon() -> Weapon | None:
    weapon_list = weapon_type_menu()
    if not weapon_list:
        return None
    formatter.clear()
    print("Weapons List")
    print("----------------------")
    choice = select_weapon_menu(weapon_list)
    if choice is None:
        formatter.clear()
        return None
    weapon = Catalog.create(weapon_list[choice])
    weapon.reload()
    return weapon


def set_fire_mode(selected_weapon: Weapon) -> FireMode | None:
    modes = selected_weapon.fire_modes
    choice = formatter.choose([mode.display_name for mode in modes], back="Return to Shooting Menu",
                              invalid="Invalid Selection; Fire Mode not set", retry=False)
    return None if choice is None else modes[choice]


def interactive_reload(weapon: Weapon) -> bool:
    step = weapon.next_reload_step()
    if step is None:
        print("Ammo already full. No need to reload")
        return False
    if weapon.reload_style is ReloadStyle.SHELL:
        print("Non-Automatic Shotguns need to be manually loaded.")
        print("--------------------------------------------------")
    elif weapon.reload_style is ReloadStyle.REVOLVER:
        print("Revolvers unload when reloaded and must be manually loaded")
        print("----------------------------------------------------------")
    noun = "shell" if weapon.reload_style is ReloadStyle.SHELL else "bullet"
    while step is not None:
        if step in (ReloadStyle.SHELL, ReloadStyle.REVOLVER):
            input(f"Press any button to load a {noun}")
        weapon.take_reload_step(step)
        if step == "empty":
            print("Gun unloaded")
        elif step is not ReloadStyle.MAGAZINE:
            print(f"One {noun} loaded. {weapon.max_ammo - weapon.current_ammo} remaining")
        step = weapon.next_reload_step(loading=True)
    return True


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
