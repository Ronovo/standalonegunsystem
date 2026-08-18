from demo.ui import formatter
from demo.ui.weapons import print_armory_display, select_weapon_menu, weapon_type_menu


def armory_main_menu() -> None:
    print("Welcome to the Armory!")
    weapon_list = weapon_type_menu()
    if not weapon_list:
        return
    while True:
        formatter.clear()
        print("Weapons List")
        print("----------------------")
        choice = select_weapon_menu(weapon_list)
        if choice == 0:
            return
        print_armory_display(weapon_list[choice - 1])
