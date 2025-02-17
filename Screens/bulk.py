from CommonScripts import weaponType, hitCalculations
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

    #Result = [MagazineArray, TotalArray]
    #Each Array has Hits,Misses,Dummies Destroyed, and Damage, in order
    reportResult = getReport(selectedWeapon, magazineCount, newDummy)

    #Print Report Per Magazine
    magazineArray = reportResult[0]
    print("Breakdown by Magazine")
    print("--------------------")
    for x in magazineArray:
        print(x)
    print("")
    #Get Total Variables
    totalArray = reportResult[1]
    totalHits = totalArray[0]
    totalMiss = totalArray[1]
    totalShots = totalHits + totalMiss
    totalDummy = totalArray[2]
    totalDamage = totalArray[3]

    #Calculate Accuracy
    accuracy = totalHits / totalShots
    accuracy *= 100
    accuracy = round(accuracy, 2)

    print("Totals for All Shots")
    print("--------------------")
    print(str(accuracy) + "% Accuracy / " + str(totalDummy) + " Dummies Destroyed / "
          + str(totalDamage) + " Damage Done")
    print("")


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
    print("\nYou have selected " + str(magazineCount) + " full magazines")
    if extraBullets > 0:
        magazineCount += 1
        print("You also have a non-full magazine with " + str(extraBullets) + " in it.\n")

    # Ammo Count
    if extraBullets > 0:
        selectedWeapon.currentAmmo = int(extraBullets)
    else:
        selectedWeapon.currentAmmo = selectedWeapon.maxAmmo

    results = [magazineCount,selectedWeapon]
    return results

def getReport(selectedWeapon, magazineCount, newDummy):
    # Variables needed to build final report
    n = 1
    magazineArray = []
    totalHits = 0
    totalMisses = 0
    totalDamage = 0
    totalDummy = 0

    #Loop through Bullets Selected (Ammo in Gun + magazine Count)
    #Magazine Outer Loop - Total magazines
    while magazineCount > 0:
        magazineCount -= 1
        hits = 0
        misses = 0
        deadDummy = 0
        magDamage = 0
        magazineString = "Magazine " + str(n) + ": "
        #Magazine Inner Loop - Bullets in Gun
        while selectedWeapon.currentAmmo > 0:
            selectedWeapon.fireShot(False)
            result = hitCalculations.simpleHit(selectedWeapon, newDummy, False)
            if result == 1:
                hits += 1
                magDamage += selectedWeapon.damage
                newDummy.takeDamage(selectedWeapon.damage)
                totalDamage += selectedWeapon.damage
                if newDummy.health <= 0:
                    deadDummy += 1
                    newDummy.health = 200
            else:
                misses += 1
        #Update Loop Variables after Weapon is Empty
        totalHits += hits
        totalMisses += misses
        totalDummy += deadDummy
        if magazineCount > 0:
            selectedWeapon.reload()
        magazineString = (magazineString + str(hits) + " Hits / " + str(misses) + " Misses / "
                          + str(deadDummy) + " Dummies Destroyed / " + str(magDamage) + " Damage Done")
        magazineArray.append(magazineString)
        n += 1

    #Build Total Array
    totalArray = [totalHits,totalMisses,totalDummy,totalDamage]

    #Build Final Report
    # 0. Magazine Array - List of Magazine Stats
    # 1. Total Array - List of Total Stats for report
    result = [magazineArray,totalArray]
    return result