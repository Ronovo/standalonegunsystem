from CommonScripts import weaponType, hitCalculations
from Presets import dummy_preset, weapons_preset

weaponList = []
mode = 'Single Shot'
destroyedDummy = 0


def rangeMain():
    global mode
    global destroyedDummy
    print("Welcome to the Gun Range!")

    # Begin Loop for Weapon Menu
    selectedWeapon = weaponType.getSelectedWeapon()
    if selectedWeapon is None:
        return
    # Ammo Count
    selectedWeapon.currentAmmo = selectedWeapon.maxAmmo
    # Run Menu to set Initial Dummy Range
    # Create Target Dummy
    newDummy = dummy_preset.getNewDummy(True)

    while 1:
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
        match answer:
            case '1':
                newDummy = shootDummy(newDummy, selectedWeapon, mode)
            case '2':
                print('Current Fire Mode is ' + mode)
                mode = weaponType.setFireMode(selectedWeapon)
                print('New Fire Mode is ' + mode)
            case '3':
                newDummy.setDummyRange(True)
            case '4':
                print("Ammo before reload is : " + str(selectedWeapon.currentAmmo))
                selectedWeapon.reload()
                print("Current Ammo is : " + str(selectedWeapon.currentAmmo))
                print("Weapon is reloaded!")
            case '5':
                weapons_preset.rangeDisplay(selectedWeapon)
            case '6':
                selectedWeapon = weaponType.getSelectedWeapon()
            case '7':
                return
            case _:
                print("Incorrect choice. Try again.")
        if newDummy.health <= 0:
            print("Do you want to set up a new dummy at the same range?\n")
            restart = input("1 for yes. Anything to leave.\n")
            if restart == '1':
                newDummy = dummy_preset.getNewDummy(True)
                destroyedDummy += 1
                print('You have destroyed ' + str(destroyedDummy) + ' dummies.\n' )
            else:
                break

def shootDummy(newDummy, selectedWeapon, fireMode):
    triggerPulls = 1
    shots = 0
    if selectedWeapon.currentAmmo == 0:
        print("Out of Ammo! Try Reloading")
        return newDummy
    if mode == 'Fully Automatic':
        y = input("How many shots do you want to fire?\n")
        if int(y) > selectedWeapon.maxAmmo:
            triggerPulls = selectedWeapon.maxAmmo - selectedWeapon.currentAmmo
        else:
            triggerPulls = int(y)
    if mode == '3 Round Burst':
        triggerPulls = 3
    waitVariable = input("Press any key to shoot")
    while triggerPulls != 0:
        selectedWeapon.fireShot(True)
        triggerPulls -= 1
        if fireMode != "Fully Automatic":
            if fireMode == "3 Round Burst":
                if shots == 3:
                    shots = 0
            else:
                shots = 0
        shots += 1
        result = hitCalculations.calculateHit(selectedWeapon, newDummy, shots, True)
        if result[0] == 1:
            newDummy.takeDamage(result[1])
            print("Dummy health is now " + str(newDummy.health) + "\n")
        else:
            print("\n")
        if newDummy.health <= 0:
            print("Dummy destroyed!")
            break

    return newDummy

