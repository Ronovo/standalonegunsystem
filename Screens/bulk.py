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
    fireMode = weaponType.setFireMode(selectedWeapon)
    exportReport(selectedWeapon,magazineCount,newDummy, fireMode)


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

def getReport(selectedWeapon, magazineCount, newDummy, fireMode):
    # Variables needed to build final report
    n = 1
    magazineArray = []
    totalHits = 0
    totalMisses = 0
    totalDamage = 0
    totalDummy = 0
    totalCrits = 0

    #Loop through Bullets Selected (Ammo in Gun + magazine Count)
    #Magazine Outer Loop - Total magazines
    while magazineCount > 0:
        magazineCount -= 1
        hits = 0
        misses = 0
        deadDummy = 0
        magDamage = 0
        crits = 0
        shots = 0
        magazineString = "Magazine " + str(n) + ": "
        #Magazine Inner Loop - Bullets in Gun
        while selectedWeapon.currentAmmo > 0:
            selectedWeapon.fireShot(False)
            #Keeps Single Shot Accurate.
            if fireMode != 'Single Shot':
                shots += 1
            result = hitCalculations.calculateHit(selectedWeapon, newDummy, shots, False)
            hit = result[0]
            damage = result[1]
            isCritical = result[2]
            if hit == 1:
                if isCritical:
                    crits += 1
                hits += 1
                magDamage += damage
                newDummy.takeDamage(damage)
                totalDamage += damage
                if newDummy.health <= 0:
                    deadDummy += 1
                    newDummy.health = 200
            else:
                misses += 1
        #Update Loop Variables after Weapon is Empty
        totalHits += hits
        totalMisses += misses
        totalDummy += deadDummy
        totalCrits += crits
        if magazineCount > 0:
            selectedWeapon.reload(True)
        magazineString = (magazineString + str(hits) + " Hits / " + str(misses) + " Misses / "
                          + str(deadDummy) + " Dummies Destroyed / " + str(magDamage) + " Damage Done")
        if crits > 0:
            magazineString = magazineString + "/ Critical Hits : " + str(crits)

        magazineArray.append(magazineString)
        n += 1

    #Build Total Array
    totalArray = [totalHits,totalMisses,totalDummy,totalDamage]

    #Build Final Report
    # 0. Magazine Array - List of Magazine Stats
    # 1. Total Array - List of Total Stats for report
    result = [magazineArray,totalArray]
    return result

def exportReport(selectedWeapon, magazineCount, newDummy, fireMode):
    # Result = [MagazineArray, TotalArray]
    # Each Array has Hits,Misses,Dummies Destroyed, and Damage, in order

    reportResult = getReport(selectedWeapon, magazineCount, newDummy, fireMode)

    # Print Report Per Magazine
    magazineArray = reportResult[0]
    print("Breakdown by Magazine")
    print("--------------------")
    for x in magazineArray:
        print(x)
    print("")
    # Get Total Variables
    totalArray = reportResult[1]
    totalHits = totalArray[0]
    totalMiss = totalArray[1]
    totalShots = totalHits + totalMiss
    totalDummy = totalArray[2]
    totalDamage = totalArray[3]

    # Calculate Accuracy
    accuracy = totalHits / totalShots
    accuracy *= 100
    accuracy = round(accuracy, 2)

    print("Totals for All Shots")
    print("--------------------")
    print(str(accuracy) + "% Accuracy / " + str(totalDummy) + " Dummies Destroyed / "
          + str(totalDamage) + " Damage Done")
    print("------------------------------------\n")