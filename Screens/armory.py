from Objects import weapons
from CommonScripts import weaponType
weaponList = []


def armoryMainMenu():
    global weaponList
    print("\n")
    print("Welcome to the Armory!")
    weaponList = weaponType.weaponTypeMenu(weaponList)
    if weaponList == None:
        return
    # Begin Loop for Weapon Menu
    print("Here are all weapons for type. Select one for more info!")
    print("----------------------")
    flag = False
    while not flag:
        w = weaponType.selectWeaponMenu(weaponList)
        if w == 0:
            return
        wName = weaponList[w - 1]
        weapons.display(wName)
