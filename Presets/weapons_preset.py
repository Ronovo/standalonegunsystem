from Objects.weapons import Preset, WeaponType

# REMEMBER TO ADD TO WEAPON LIST IN METHOD getWeaponList() if you create it here
# Pistols
m1911 = Preset("M1911", 7, 0, 50, 100, 200,80, WeaponType("Pistol", "Small Arms"),fireMode=['s'])
usp45 = Preset("USP .45", 12, 0, 75, 100, 250,75, WeaponType("Pistol", "Small Arms"),fireMode=['s'])
m9 = Preset("M9", 15, 0, 50, 150, 300, 70, WeaponType("Pistol", "Small Arms"),fireMode=['s'])
deserteagle = Preset("Desert Eagle", 7, 0, 100, 200, 300, 70, WeaponType("Pistol", "Small Arms"),fireMode=['s'])
glock18 = Preset("Glock 18", 18,0,50,150, 300, 75, WeaponType("Pistol", "Small Arms"),fireMode=['s','fa'] )
special38 = Preset(".38 Special", 6,0,50,100,200,75, WeaponType("Pistol","Small Arms"),fireMode=['s'])
magnum44 = Preset("44 Magnum",6,0,100,150,300, 85, WeaponType("Pistol", "Small Arms"),fireMode=['s'])

# SMG
mp5 = Preset("MP5", 30, 0, 50, 200, 300, 80, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])
ak47u = Preset("AK-47u", 30, 0, 75, 200, 350, 75, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])
p90 = Preset("P90", 50, 0, 75, 200, 250, 70, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])
miniuzi = Preset("Mini-Uzi", 32, 0, 50, 100, 250, 60, WeaponType("SMG", "Small Arms"),fireMode=['s','fa'])

# Shotguns
w1200 = Preset("W1200", 7, 0, 75, 50, 150,90, WeaponType("Shotgun", "Medium Arms"),fireMode=['s'])
m1014 = Preset("M1014", 4, 0, 100, 50,150, 90, WeaponType("Shotgun", "Medium Arms"),fireMode=['s'])
usas12 = Preset("USAS-12", 10, 0, 75, 100, 200,90, WeaponType("Shotgun", "Medium Arms"),fireMode=['s','fa'])
spas12 = Preset("Spas-12", 8,0,100, 100, 200, 90, WeaponType("Shotgun", "Medium Arms"),fireMode=['s'])
# Assault Rifles
m16a4 = Preset("M16A4", 30, 0, 75, 200, 450,80, WeaponType("Assault", "Medium Arms"),fireMode=['s','3r','fa'])
ak47 = Preset("AK47", 30, 0, 100, 200, 450,80, WeaponType("Assault", "Medium Arms"),fireMode=['s','3r','fa'])
g3 = Preset("G3", 20, 0, 75, 300, 500,80, WeaponType("Assault", "Medium Arms"),fireMode=['s','3r','fa'])
g36 = Preset("G36",30,0,100,400,500, 75, WeaponType("Assault","Medium Arms"),fireMode=['s','3r','fa'])
fnfal = Preset("FN FAL", 20, 0, 100, 250,500, 80, WeaponType("Assault", "Medium Arms"), fireMode=['s','3r','fa'])

# Sniper(High Skill Cap, more power, high accurary
m40a3 = Preset("M40A3", 5, 0, 100, 500, 500,80, WeaponType("Sniper", "Large Arms"),fireMode=['s'])
dragunov = Preset("Dragunov", 20, 0, 75, 500, 500,80, WeaponType("Sniper", "Large Arms"),fireMode=['s'])
b50cal = Preset("Barrett .50Cal", 1, 0, 200, 500, 500,70, WeaponType("Sniper", "Large Arms"),fireMode=['s'])

# LMG
m249 = Preset("M249 SAW", 100, 0, 75, 300, 500,80, WeaponType("LMG", "Large Arms"),fireMode=['s','fa'])
m60e4 = Preset("M60E4", 100, 0, 50, 250, 500,70, WeaponType("LMG", "Large Arms"),fireMode=['s','fa'])
rpd = Preset("RPD", 100, 0, 50, 350, 500,70, WeaponType("LMG", "Large Arms"),fireMode=['s','fa'])


def getWeaponList():
    weaponList = [m1911, usp45, m9, deserteagle, glock18, special38, magnum44,
                  mp5, ak47u, p90, miniuzi,
                  w1200, m1014, usas12,spas12,
                  m16a4, ak47, g3, g36, fnfal,
                  m40a3, dragunov, b50cal,
                  m249, m60e4, rpd]
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

def armoryDisplay(weaponName):
    selected = getWeaponByName(weaponName)
    print("\nYou have selected " + selected.name)
    display(selected)
    print("")
    input("Press any key to return to weapon select\n")

def rangeDisplay(weapon):
    print("\nYour current weapon is " + weapon.name)
    display(weapon)
    print("Current Ammo : " + str(weapon.currentAmmo) + "\n")
    input("Press any key to return to Shooting Menu\n")

def display(selectedWeapon):
    print("Max Ammo: " + str(selectedWeapon.maxAmmo) + " | " + "Damage: " + str(selectedWeapon.damage))
    print("Base Range(In Meters): " + str(selectedWeapon.rangeM) + " | " + "Base Accuracy: " + str(selectedWeapon.baseAccuracy))
    print("Max Range (In Meters): " + str(selectedWeapon.maxRange))
    weaponType = selectedWeapon.weaponType
    print("Class: " + str(weaponType.className) + " | " + "Weapon Type: " + str(weaponType.type))
    fireModeString = buildFireModeString(selectedWeapon)
    print("Fire Modes : " + fireModeString)