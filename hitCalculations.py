import random
import json
from tkinter import END


def roll(number):
    return random.randint(1, number)


# Base 100 Roll.
# Check Against Base Accuracy
# Factors:
# Distance
def simpleHit(selectedWeapon, dummy):
    #Initial roll 1-100
    baseResult = roll(100)
    print("Base Roll = " + str(baseResult))
    #Initial Variables for Caluculation
    distance = int(dummy["distance"])
    rangeM = int(selectedWeapon.rangeM)
    isSniper = False
    if selectedWeapon.weaponType.className == "Sniper":
        isSniper = True

    # Close Range Bonus
    if distance < rangeM:
        closeRange = rangeM - distance
        y = closeRange // 50
        # This Check Makes Sure that Sniper at Max Range doesn't get insane bonus
        if isSniper and y > 3:
            y = 4
        for x in range(0, y):
            baseResult -= 5
        #print("Base Result w/ Close Range Bonus = " + str(baseResult))
    # Long Range Penalty
    elif distance > rangeM:
        farRange = distance - rangeM
        y = farRange // 50
        for x in range(0, y):
            baseResult += 10
        #print("Base Result w/ Long Range Penalty = " + str(baseResult))

    #print("Your weapons base accuracy is " + str(selectedWeapon.baseAccuracy) + " at " + str(selectedWeapon.rangeM) + "M")
    if baseResult <= selectedWeapon.baseAccuracy:
        print("Hit!")
        return 1
    else:
        print("Miss!")
        return 0