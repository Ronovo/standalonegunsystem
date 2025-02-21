class Preset:
    def __init__(self, name, maxAmmo, currentAmmo, damage, rangeM, maxRange, baseAccuracy, weaponType, fireMode):
        self.name = name
        self.maxAmmo = maxAmmo
        self.currentAmmo = currentAmmo
        self.damage = damage
        self.rangeM = rangeM
        self.maxRange = maxRange
        self.baseAccuracy = baseAccuracy
        self.weaponType = weaponType
        self.fireMode = fireMode

    def reload(self):
        #Load by cartridge except for Automatic Shotguns
        if self.currentAmmo == self.maxAmmo:
            print("Ammo already full. No need to reload")
            return

        #Shotgun Manual Reload check
        if self.weaponType.className == "Shotgun" and self.name != "USAS-12":
            print("Non-Automatic Shotguns need to be manually loaded.")
            print("--------------------------------------------------")
            shells = self.maxAmmo - self.currentAmmo
            while shells != 0:
                input("Press any button to load a shell")
                shells -= 1
                self.currentAmmo += 1
                print("One shell loaded. " + str(shells) + " remaining")
        #Revolver reload logic
        if self.name == "44 Magnum" or self.name == ".38 Special":
            print("Revolvers unload when reloaded and must be manually loaded")
            print("----------------------------------------------------------")
            if self.currentAmmo != 0:
                self.currentAmmo = 0
                print("Gun unloaded")
            bullets = self.maxAmmo
            while bullets != 0:
                input("Press any button to load a bullet.")
                self.currentAmmo += 1
                bullets -= 1
                print("One bullet loaded. " + str(bullets) + " remaining")
        #Load by Magazine
        else:
            self.currentAmmo = self.maxAmmo

    def fireShot(self, debug):
        self.currentAmmo -= 1
        if debug:
            print("Your weapon now has " + str(self.currentAmmo) + " bullets.")

class WeaponType:
    def __init__(self, className, type):
        self.className = className
        self.type = type
