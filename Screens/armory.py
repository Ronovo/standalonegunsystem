from Objects import weapons
from CommonScripts import weaponType
from Presets import weapons_preset


def armoryMainMenu():
    print("\n")
    print("Welcome to the Armory!")
    weaponList = weaponType.weaponTypeMenu()
    if len(weaponList) == 0:
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
        weapons_preset.display(wName)
