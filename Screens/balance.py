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

        #Load the selected weapon
        selectedWeapon.reload()


        filename = selectedWeapon.name + '.txt'
        sys.stdout = open(os.path.join(weaponTypePath, filename), 'w')
        print("Balance Report for " + selectedWeapon.name)
        print("------------------------------------\n")
        #Dummy Type Loop
        sizeList = dummy_preset.getSizes()
        for dummySize in sizeList:
            print("Results for " + dummySize + " Dummy")
            print("------------------------------------\n")
            match dummySize:
                case 'Small':
                    newDummy = dummy_preset.getNewDummyBalanceReport('Small')
                case 'Medium':
                    newDummy = dummy_preset.getNewDummyBalanceReport('Medium')
                case 'Large':
                    newDummy = dummy_preset.getNewDummyBalanceReport('Large')
            runCalculationsOnDummy(newDummy, selectedWeapon)



    #Reset Output to Console After we are done writing
    sys.stdout = sys.__stdout__

def runCalculationsOnDummy(newDummy, selectedWeapon):
    ranges = dummy_preset.getRanges()
    for nextRange in ranges:
        print("Results for " + str(nextRange) + "M")
        print("------------------------------------\n")
        newDummy.setDummyRangeBalanceReport(nextRange)
        bulk.exportReport(selectedWeapon,3,newDummy)
        selectedWeapon.reload()

