from Objects import weapons
from Objects.weapons import Preset, WeaponType
from CommonScripts import weaponType
# REMEMBER TO ADD TO WEAPON LIST IN METHOD getWeaponList() if you create it here
# Pistols
# Skill Order = N MA CA D R BA WT
m1911 = Preset("M1911", 7, 0, 50, 100, 80, WeaponType("Pistol", "Small Arms"),fireMode=['s'])  # 20%
usp45 = Preset("USP .45", 12, 0, 75, 100, 75, WeaponType("Pistol", "Small Arms"),fireMode=['s'])  # 15%
m9 = Preset("M9", 15, 0, 50, 150, 70, WeaponType("Pistol", "Small Arms"),fireMode=['s'])  # 15%
deserteagle = Preset("Desert Eagle", 7, 0, 100, 200, 60, WeaponType("Pistol", "Small Arms"),fireMode=['s'])  # 10%

# SMG
# Skill Order = N MA CA D R BA WT
mp5 = Preset("MP5", 30, 0, 50, 300, 40, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])  # 12 %
ak47u = Preset("AK-47u", 30, 0, 75, 250, 40, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])  # 10 %
p90 = Preset("P90", 50, 0, 25, 350, 30, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])  # 12 %
miniuzi = Preset("Mini-Uzi", 32, 0, 50, 200, 35, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])  # 15 %

# Shotguns
# Skill Order = N MA CA D R BA WT
w1200 = Preset("W1200", 7, 0, 75, 50, 90, WeaponType("Shotgun", "Medium Arms"),fireMode=['s'])  # 12%
m1014 = Preset("M1014", 4, 0, 100, 50, 90, WeaponType("Shotgun", "Medium Arms"),fireMode=['s'])  # 10%

# Assault Rifles
# Skill Order = N MA CA D R BA WT
m16a4 = Preset("M16A4", 30, 0, 70, 400, 60, WeaponType("Assault", "Medium Arms"),fireMode=['s','3r','fa'])  # 14%
ak47 = Preset("AK47", 30, 0, 100, 300, 60, WeaponType("Assault", "Medium Arms"),fireMode=['s','3r','fa'])  # 8%
g3 = Preset("G3", 20, 0, 50, 500, 60, WeaponType("Assault", "Medium Arms"),fireMode=['s','3r','fa'])  # 8%

# Sniper(High Skill Cap, more power, high accurary
# Skill Order = N MA CA D R BA WT
m40a3 = Preset("M40A3", 5, 0, 100, 500, 80, WeaponType("Sniper", "Large Arms"),fireMode=['s'])  # 5%
dragunov = Preset("Dragunov", 20, 0, 75, 500, 80, WeaponType("Sniper", "Large Arms"),fireMode=['s'])  # 3%
b50cal = Preset("Barrett .50Cal", 1, 0, 200, 500, 70, WeaponType("Sniper", "Large Arms"),fireMode=['s'])  # 1%

# LMG
# Skill Order = N MA CA D R BA WT
m249 = Preset("M249 SAW", 100, 0, 30, 300, 50, WeaponType("LMG", "Large Arms"),fireMode=['s','fa'])  # 5%
m60e4 = Preset("M60E4", 100, 0, 75, 300, 35, WeaponType("LMG", "Large Arms"),fireMode=['s','fa'])  # 3%
rpd = Preset("RPD", 100, 0, 50, 300, 45, WeaponType("LMG", "Large Arms"),fireMode=['s','fa'])


def getWeaponList():
    weaponList = [m1911, usp45, m9, deserteagle, mp5, ak47u, p90, miniuzi, w1200, m1014,
                  m16a4, ak47, g3, m40a3, dragunov, b50cal, m249, m60e4, rpd]
    return weaponList


def getWeaponListByWeaponType(wType):
    weapons = getWeaponList()
    sendlist = []
    for x in weapons:
        y = x.weaponType.type
        if y == wType:
            sendlist.append(x)
    return sendlist

def getWeaponByName(name):
    weapons = getWeaponList()
    for x in weapons:
        y = x.name
        if y == name:
            return x

def returnFireMode(x):
    match x:
        case 's':
            return 'Single Shot'
        case '3r':
            return '3 Round Burst'
        case 'fa':
            return 'Fully Automatic'


def buildFireModeString(selected):
    fireModeString = ''
    endIndex = len(selected.fireMode) - 1
    for x in selected.fireMode:
        fireModeValue = returnFireMode(x)
        fireModeString += fireModeValue
        if selected.fireMode.index(x) != endIndex:
            fireModeString += ', '
    return fireModeString


def display(name):
    selected = getWeaponByName(name)
    print("\nYou have selected " + selected.name)
    print("Max Ammo: " + str(selected.maxAmmo) + " | " + "Damage: " + str(selected.damage))
    print("Range(In Meters): " + str(selected.rangeM) + " | " + "Base Accuracy: " + str(selected.baseAccuracy))
    weaponType = selected.weaponType
    print("Class: " + str(weaponType.className) + " | " + "Weapon Type: " + str(weaponType.type) + "\n")
    fireModeString = buildFireModeString(selected)
    print("Fire Modes : " + fireModeString)
    input("Press any key to return to weapon select\n")

def rangeDisplay(weapon):
    print("\nYour current weapon is " + weapon.name)
    print("Max Ammo: " + str(weapon.maxAmmo) + " | " + "Damage: " + str(weapon.damage))
    print("Range(In Meters): " + str(weapon.rangeM) + " | " + "Base Accuracy: " + str(weapon.baseAccuracy))
    weaponType = weapon.weaponType
    print("Class: " + str(weaponType.className) + " | " + "Weapon Type: " + str(weaponType.type) + "\n")
    print("Current Ammo : " + str(weapon.currentAmmo))
    input("Press any key to return to Shooting Menu\n")