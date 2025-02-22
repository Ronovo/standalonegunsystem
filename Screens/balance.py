from CommonScripts import weaponType, hitCalculations
from Screens import bulk
from Presets import dummy_preset, weapons_preset
import sys
import os

def balanceReport():
    print("You are about to run a balance report. This will fire 3 magazines for:")
    print("-All Weapons")
    print("-All Dummies")
    print("-All Ranges")
    answer = input("Press any key to continue or 1 to stop\n")
    try:
        answer = int(answer)
        if int(answer) == 1:
            return
    except ValueError:
        pass

    currentPath = os.getcwd()
    path = currentPath + "/Balance Reports"

    if not os.path.exists(path):
        os.makedirs(path)

    # Get Weapon List
    weaponsList = weapons_preset.getWeaponList()

    # WeaponList Loop
    for selectedWeapon in weaponsList:
        #Create Weapon Type Subdirectory if it doesn't exist
        weaponTypePath = path + "/" + selectedWeapon.weaponType.className
        if not os.path.exists(weaponTypePath):
            os.makedirs(weaponTypePath)

        weaponPath = weaponTypePath + "/" + selectedWeapon.name
        if not os.path.exists(weaponPath):
            os.makedirs(weaponPath)

        #Load the selected weapon
        selectedWeapon.reload(True)
        if len(selectedWeapon.fireMode) > 1:
            for x in selectedWeapon.fireMode:
                fireModeValue = weapons_preset.returnFireMode(x)
                shootDummyBySize(selectedWeapon,weaponTypePath,fireModeValue)
        else:
            fireModeValue = weapons_preset.returnFireMode(selectedWeapon.fireMode[0])
            shootDummyBySize(selectedWeapon, weaponTypePath, fireModeValue)




    #Reset Output to Console After we are done writing
    sys.stdout = sys.__stdout__

def runCalculationsOnDummy(newDummy, selectedWeapon, fireMode):
    ranges = dummy_preset.getRanges()
    for nextRange in ranges:
        print("Results for " + str(nextRange) + "M")
        print("------------------------------------\n")
        newDummy.setDummyRangeBalanceReport(nextRange)
        bulk.exportReport(selectedWeapon,3,newDummy,fireMode)
        selectedWeapon.reload(True)

def shootDummyBySize(selectedWeapon, weaponTypePath, fireModeValue):
    # Dummy Type Loop
    sizeList = dummy_preset.getSizes()
    for dummySize in sizeList:
        fireModePath = weaponTypePath + "/" + selectedWeapon.name + "/" + dummySize + "/"
        if not os.path.exists(fireModePath):
            os.makedirs(fireModePath)

        filename = fireModeValue + ".txt"
        sys.stdout = open(os.path.join(fireModePath, filename), 'w')
        match dummySize:
            case 'Small':
                newDummy = dummy_preset.getNewDummyBalanceReport('Small')
            case 'Medium':
                newDummy = dummy_preset.getNewDummyBalanceReport('Medium')
            case 'Large':
                localSizeDummy = 'large'
                newDummy = dummy_preset.getNewDummyBalanceReport('Large')
            case _:
                newDummy = dummy_preset.getNewDummyBalanceReport('Medium')
        print("Balance Report for " + selectedWeapon.name)
        print("------------------------------------\n")
        runCalculationsOnDummy(newDummy, selectedWeapon, fireModeValue)

