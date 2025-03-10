from Objects import weapons
from CommonScripts import weaponType, formatter
from Presets import weapons_preset

## TODO Add WeaponType Submenu to Armory
def armoryMainMenu():
    print("Welcome to the Armory!")
    weaponList = weaponType.weaponTypeMenu()
    if len(weaponList) == 0:
        return
    # Begin Loop for Weapon Menu
    flag = False
    while not flag:
        formatter.clear()
        print("Weapons List")
        print("----------------------")
        w = weaponType.selectWeaponMenu(weaponList)
        if w == 0:
            return
        wName = weaponList[w - 1]
        weapons_preset.armoryDisplay(wName)
