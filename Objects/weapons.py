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
        self.currentAmmo = self.maxAmmo

    def fireShot(self, debug):
        self.currentAmmo -= 1
        if debug:
            print("Your weapon now has " + str(self.currentAmmo) + " bullets.")

class WeaponType:
    def __init__(self, className, type):
        self.className = className
        self.type = type
