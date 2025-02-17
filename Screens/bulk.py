import hitCalculations
from CommonScripts import weaponType
from Presets import dummy_preset

weaponList = []
mode = 'Single Shot'
destroyedDummy = 0

def bulkShots():
    print("Bulk Report")

    # Ask for gun
    selectedWeapon = weaponType.getSelectedWeapon()
    if selectedWeapon is None:
        return

    results = getTotalMagazineCount(selectedWeapon)
    magazineCount = results[0]
    selectedWeapon = results[1]


    # Ask For Distance
    newDummy = dummy_preset.getNewDummy(False)

    reportArray = getReportArray(selectedWeapon, magazineCount, newDummy)

    for x in reportArray:
        print(x)
    print("\n")


def getTotalMagazineCount(selectedWeapon):
    maxAmmo = selectedWeapon.maxAmmo

    print("Your weapon currently has " + str(maxAmmo) + " bullets per magazine.")
    # Ask for number of shots/magazines
    answer = input("How many shots do you want to test?\n")
    if int(answer) < maxAmmo:
        extraBullets = int(answer)
    else:
        magazineCount = int(answer) // maxAmmo
        extraBullets = int(answer) % maxAmmo
    print("You have selected " + str(magazineCount) + " full magazines")
    if extraBullets > 0:
        magazineCount += 1
        print("You also have a non-full magazine with " + str(extraBullets) + " in it.")

    # Ammo Count
    if extraBullets > 0:
        selectedWeapon.currentAmmo = int(extraBullets)
    else:
        selectedWeapon.currentAmmo = selectedWeapon.maxAmmo

    results = [magazineCount,selectedWeapon]
    return results

def getReportArray(selectedWeapon, magazineCount, newDummy):
    n = 1
    reportArray = []

    while magazineCount > 0:
        magazineCount -= 1
        hits = 0
        misses = 0
        deadDummy = 0
        magDamage = 0
        magazineString = "Magazine " + str(n) + ": "
        while selectedWeapon.currentAmmo > 0:
            selectedWeapon.fireShot(False)
            result = hitCalculations.simpleHit(selectedWeapon, newDummy, False)
            if result == 1:
                hits += 1
                magDamage += selectedWeapon.damage
                newDummy.takeDamage(selectedWeapon.damage)
                if newDummy.health <= 0:
                    deadDummy += 1
                    newDummy.health = 200
            else:
                misses += 1

        if magazineCount > 0:
            selectedWeapon.reload()
        magazineString = (magazineString + str(hits) + " hits/ " + str(misses) + " misses/ "
                          + str(deadDummy) + " Dummies Destroyed/ " + str(magDamage) + " Damage Done")
        reportArray.append(magazineString)
        n += 1
    return reportArray