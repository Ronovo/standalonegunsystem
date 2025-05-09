from CommonScripts import formatter
from Presets import weapons_preset

weaponTypes = ['Small Arms', 'Medium Arms', 'Large Arms']

def weaponTypeMenu():
    weaponList = []
    print("Please select a weapon type:")
    print("----------------------")
    print("1.) " + weaponTypes[0])
    print("2.) " + weaponTypes[1])
    print("3.) " + weaponTypes[2])
    answer = input("Pick 1-3\n")
    wType = ''
    if 0 < int(answer) < 4:
        weaponTypesIndex = int(answer) - 1
        wType = weaponTypes[weaponTypesIndex]
    else:
        print("Incorrect choice. Returning to Menu")

    # Get Weapon List
    if wType != '':
        newlist = weapons_preset.getWeaponListByWeaponType(wType)
        if len(newlist) != 0:
            for x in newlist:
                weaponList.append(x.name)
    return weaponList

def getSelectedWeapon():
    weaponList = weaponTypeMenu()
    if weaponList == []:
        return
    formatter.clear()
    print("Weapons List")
    print("----------------------")
    w = selectWeaponMenu(weaponList)
    if w != 0:
        wName = weaponList[w - 1]
        selectedWeapon = weapons_preset.getWeaponByName(wName)
        selectedWeapon.reload(False)
        return selectedWeapon
    formatter.clear()

def selectWeaponMenu(weaponList):
    wFlag = True
    while wFlag:
        # Menu Counter
        n = 1
        for x in weaponList:
            print(str(n) + ".) " + x)
            n += 1
        print(str(n) + ".) Return to Main Menu")
        answer = input("Pick 1-" + str(n) + "\n")
        if answer == str(n):
            w = 0
            wFlag = False
        else:
            try:
                w = int(answer)
                wFlag = False
            except ValueError:
                print("Please enter a valid number")
    return w

def setFireMode(selectedWeapon):
    n = 1
    for x in selectedWeapon.fireMode:
        fireModeValue = weapons_preset.returnFireMode(x)
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
        mode = weapons_preset.returnFireMode(modeabbr)
        return mode
    else:
        print("Invalid Selection; Fire Mode not set")
        return
