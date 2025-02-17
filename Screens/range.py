import hitCalculations
from CommonScripts import weaponType
from Objects import weapons
from Objects.dummy import Dummy

weaponList = []
mode = 'Single Shot'
destroyedDummy = 0


def range():
    global mode
    global destroyedDummy
    print("Welcome to the Gun Range!")

    # Create Target Dummy
    newDummy = Dummy(200,0)

    # Begin Loop for Weapon Menu
    selectedWeapon = weaponType.getSelectedWeapon()

    if selectedWeapon is None:
        return
    # Ammo Count
    selectedWeapon.currentAmmo = selectedWeapon.maxAmmo
    print("Ammo: " + str(selectedWeapon.currentAmmo) + "/" + str(selectedWeapon.maxAmmo))

    # Run Menu to set Initial Dummy Range
    newDummy.setDummyRange(True)

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
                newDummy = shootDummy(newDummy, selectedWeapon)
            case '2':
                print('Current Fire Mode is ' + mode)
                setGlobalFireMode(selectedWeapon)
                print('New Fire Mode is ' + mode)
            case '3':
                newDummy.setDummyRange(True)
            case '4':
                print("Ammo before reload is : " + str(selectedWeapon.currentAmmo))
                selectedWeapon.reload()
                print("Current Ammo is : " + str(selectedWeapon.currentAmmo))
                print("Weapon is reloaded!")
            case '5':
                weapons.rangeDisplay(selectedWeapon)
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
                newDummy.health = 200
                destroyedDummy += 1
                print('You have destroyed ' + str(destroyedDummy) + ' dummies.\n' )
            else:
                break


def setGlobalFireMode(selectedWeapon):
    n = 1
    for x in selectedWeapon.fireMode:
        fireModeValue = weapons.returnFireMode(x)
        print(str(n) + '.) ' + fireModeValue)
        n += 1
    endIndex = n - 1
    print(str(n) + '.) Return to Shooting Menu')
    fireModeAnswer = input("Pick 1 - " + str(n) + '\n')
    intFM = int(fireModeAnswer)
    if intFM == n:
        return
    if intFM > 0 and intFM < (endIndex + 1):
        i = intFM - 1
        modeabbr = selectedWeapon.fireMode[i]
        # sets Global Fire Mode
        global mode
        mode = weapons.returnFireMode(modeabbr)
        return
    else:
        print("Invalid Selection; Fire Mode not set")
        return

def shootDummy(newDummy, selectedWeapon):
    triggerPulls = 1
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
        result = hitCalculations.simpleHit(selectedWeapon, newDummy.distance, True)
        if result == 1:
            newDummy.takeDamage(selectedWeapon.damage)
            print("Dummy health is now " + str(newDummy.health) + "\n")
        else:
            print("\n")
        if newDummy.health <= 0:
            print("Dummy destroyed!")
            break
    return newDummy

