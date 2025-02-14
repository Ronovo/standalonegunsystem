import hitCalculations
from CommonScripts import weaponType
from Objects import weapons

weaponList = []
mode = 'Single Shot'
destroyedDummy = 0


def range():
    global mode
    global destroyedDummy
    print("Welcome to the Gun Range!")
    # Create Target Dummy
    dummy = {
        "health": 200,
        "distance": 50
    }

    # Begin Loop for Weapon Menu
    selectedWeapon = selectAWeapon()
    if selectedWeapon is None:
        return
    # Ammo Count
    selectedWeapon.currentAmmo = selectedWeapon.maxAmmo
    print("Ammo: " + str(selectedWeapon.currentAmmo) + "/" + str(selectedWeapon.maxAmmo))

    # Run Menu to set Initial Dummy Range
    dummy = setDummyRange(dummy)

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
                dummy = shootDummy(dummy, selectedWeapon)
            case '2':
                print('Current Fire Mode is ' + mode)
                setGlobalFireMode(selectedWeapon)
                print('New Fire Mode is ' + mode)
            case '3':
                dummy = setDummyRange(dummy)
            case '4':
                print("Ammo before reload is : " + str(selectedWeapon.currentAmmo))
                selectedWeapon.reload()
                print("Current Ammo is : " + str(selectedWeapon.currentAmmo))
                print("Weapon is reloaded")
            case '5':
                weapons.rangeDisplay(selectedWeapon)
            case '6':
                selectedWeapon = selectAWeapon()
            case '7':
                return
            case _:
                print("Incorrect choice. Try again.")
        if dummy['health'] <= 0:
            print("Do you want to set up a new dummy at the same range?\n")
            restart = input("1 for yes. Anything to leave.\n")
            if restart == '1':
                dummy['health'] = 200
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

def setDummyRange(dummy):
    dFlag = False
    dummyRange = 0
    while not dFlag:
        print("Please select distance for dummy")
        print("----------")
        print("1.) 50 Meters")
        print("2.) 100 Meters")
        print("3.) 150 Meters")
        print("4.) 200 Meters")
        print("5.) 300 Meters")
        print("6.) 400 Meters")
        print("7.) 500 Meters")
        print("8.) return \n")
        answer = input("Pick 1-8\n")
        numAnswer = int(answer)
        if 0 < numAnswer < 5:
            dummyRange = 50 * numAnswer
            dFlag = True
        elif 4 < numAnswer < 8:
            dFlag = True
            match numAnswer:
                case 5:
                    dummyRange = 300
                case 6:
                    dummyRange = 400
                case 7:
                    dummyRange = 500
        elif numAnswer == 8:
            quit()
        else:
            print("Incorrect choice. Try again.")
    dummy['distance'] = dummyRange
    print("Dummy has been set to range of " + str(dummy['distance']))
    return dummy

def shootDummy(dummy, selectedWeapon):
    triggerPulls = 1
    if selectedWeapon.currentAmmo == 0:
        print("Out of Ammo! Try Reloading")
        return dummy
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
        selectedWeapon.fireShot()
        triggerPulls -= 1
        result = hitCalculations.simpleHit(selectedWeapon, dummy)
        if result == 1:
            damage = selectedWeapon.damage
            dummy['health'] -= damage
            print("Dummy health is now " + str(dummy['health']) + "\n")
        else:
            print("\n")
        if dummy['health'] <= 0:
            print("Dummy destroyed!")
            break
    return dummy

def selectAWeapon():
    global mode
    global weaponList
    weaponList = weaponType.weaponTypeMenu(weaponList)
    if weaponList == []:
        return
    print("Here are all weapons for type. Select one for more info!")
    print("----------------------")
    w = weaponType.selectWeaponMenu(weaponList)
    if w != 0:
        wName = weaponList[w - 1]
        selectedWeapon = weapons.getWeaponByName(wName)
        print("Weapon Selected: " + selectedWeapon.name)
        selectedWeapon.reload()
        mode = 'Single Shot'
        return selectedWeapon

