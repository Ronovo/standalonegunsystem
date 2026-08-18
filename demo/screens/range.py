from gunsystem import FireMode, Weapon, advance_string, resolve_shot

from demo.dummy import Dummy
from demo.dummy_catalog import prompt_dummy_range, prompt_new_dummy
from demo.ui import formatter
from demo.ui.weapons import get_selected_weapon, interactive_reload, print_range_display, set_fire_mode

destroyed_dummy = 0


def range_main() -> None:
    global destroyed_dummy
    print("Welcome to the Gun Range!")

    selected_weapon = get_selected_weapon()
    if selected_weapon is None:
        return
    formatter.clear()
    selected_weapon.reload()
    fire_mode = selected_weapon.fire_modes[0]
    new_dummy = prompt_new_dummy(True)
    formatter.clear()
    while True:
        print("SHOOTING MENU")
        print("----------")
        print("1.) Fire a Shot")
        print("2.) Change Fire Mode")
        print("3.) Reset Dummy Range")
        print("4.) Reload")
        print("5.) Get Current Weapon Info")
        print("6.) Switch Weapons")
        print("7.) Quit to Main Menu\n")
        answer = input("Pick 1-7\n")
        formatter.clear()
        match answer:
            case "1":
                new_dummy = shoot_dummy(new_dummy, selected_weapon, fire_mode)
            case "2":
                print("Current Fire Mode is " + fire_mode.display_name)
                new_mode = set_fire_mode(selected_weapon)
                if new_mode is not None:
                    fire_mode = new_mode
                print("New Fire Mode is " + fire_mode.display_name)
            case "3":
                prompt_dummy_range(new_dummy, True)
            case "4":
                print("Ammo before reload is : " + str(selected_weapon.current_ammo))
                interactive_reload(selected_weapon)
                print("Current Ammo is : " + str(selected_weapon.current_ammo))
                print("Weapon is reloaded!")
            case "5":
                print_range_display(selected_weapon)
            case "6":
                switched = get_selected_weapon()
                if switched is not None:
                    selected_weapon = switched
                    fire_mode = selected_weapon.fire_modes[0]
            case "7":
                return
            case _:
                print("Incorrect choice. Try again.")
        input("Press any key to continue...")
        formatter.clear()
        if new_dummy.is_destroyed():
            print("DUMMY DESTROYED!")
            destroyed_dummy += 1
            print("You have destroyed " + str(destroyed_dummy) + " dummies.\n")
            print("Do you want to set up a new dummy at the same range?\n")
            restart = input("1 for yes. Anything to leave.\n")
            formatter.clear()
            if restart == "1":
                previous_range = new_dummy.distance
                new_dummy = prompt_new_dummy(True)
                if new_dummy.distance == 0:
                    new_dummy.distance = previous_range
            else:
                break


def _shots_to_fire(weapon: Weapon, fire_mode: FireMode) -> int:
    if weapon.current_ammo <= 0:
        return 0
    if fire_mode is FireMode.AUTO:
        raw = input("How many shots do you want to fire?\n")
        try:
            requested = int(raw)
        except ValueError:
            requested = 1
        if requested < 1:
            requested = 1
        return min(requested, weapon.current_ammo)
    if fire_mode is FireMode.BURST:
        return min(3, weapon.current_ammo)
    return 1


def shoot_dummy(new_dummy: Dummy, selected_weapon: Weapon, fire_mode: FireMode) -> Dummy:
    if selected_weapon.current_ammo == 0:
        print("Out of Ammo! Try Reloading")
        return new_dummy

    trigger_pulls = _shots_to_fire(selected_weapon, fire_mode)
    input("Press any key to shoot")
    shots_in_string = 0
    while trigger_pulls > 0:
        if selected_weapon.current_ammo <= 0:
            print("Out of Ammo! Try Reloading")
            break
        trigger_pulls -= 1
        shots_in_string = advance_string(fire_mode, shots_in_string)
        result = resolve_shot(selected_weapon, new_dummy, shots_in_string)
        print("Your weapon now has " + str(result.remaining_ammo) + " bullets.")
        if result.hit:
            print("Hit!")
            if result.critical:
                print("Critical hit!")
            print("Damage dealt = " + str(result.damage))
            new_dummy.take_damage(result.damage)
            print("Dummy health is now " + str(new_dummy.health) + "\n")
        else:
            print("Miss!\n")
        if new_dummy.is_destroyed():
            print("Dummy destroyed!")
            break

    return new_dummy
