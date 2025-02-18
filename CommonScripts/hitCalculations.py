import random


def roll(number):
    return random.randint(1, number)


# Base 100 Roll.
# Check Against Base Accuracy
# Factors:
# Distance, Dummy Size
def calculateHit(selectedWeapon, newDummy, debug):
    #Initial roll 1-100
    baseResult = roll(100)
    if debug:
        print("Base Roll = " + str(baseResult))
    #Initial Variables for Caluculation
    rangeM = int(selectedWeapon.rangeM)
    isSniper = False
    if selectedWeapon.weaponType.className == "Sniper":
        isSniper = True

    # Calculate : RANGE BONUS
    # Check Dummy Distance Against Range of Gun
    # Close Range Bonus
    # TODO : Refactor with new MaxRange Stat on weapon
    if newDummy.distance < rangeM:
        closeRange = rangeM - newDummy.distance
        y = closeRange // 50
        # This Check Makes Sure that Sniper at Max Range doesn't get insane bonus
        if isSniper and y > 3:
            y = 4
        for x in range(0, y):
            baseResult -= 5
    # Long Range Penalty
    elif newDummy.distance > rangeM:
        farRange = newDummy.distance - rangeM
        y = farRange // 50
        for x in range(0, y):
            baseResult += 10

    if debug:
        print("BaseResult w/ Range Modifier : " + str(baseResult))

    # Calculate : DUMMY SIZE BONUS
    # Check Dummy Size. Smaller the target, harder to hit, vice versa.
    size = newDummy.size
    match size:
        case 's':
            baseResult *= 1.08
            if debug:
                print(str(baseResult) + " after Dummy Size")
        case 'l':
            baseResult *= 0.92
            if debug:
                print(str(baseResult) + " after Dummy Size")

    # Calculate : Bullet Drop

    if baseResult <= selectedWeapon.baseAccuracy:
        if debug:
            print("Hit!")
        return 1
    else:
        if debug:
            print("Miss!")
        return 0