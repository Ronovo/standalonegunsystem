import random

def roll(number):
    return random.randint(1, number)


# Base 100 Roll.
# Check Against Base Accuracy
# Factors:
# Distance, Dummy Size
def calculateHit(selectedWeapon, newDummy, shots, debug):
    #Initial roll 1-100
    baseResult = roll(100)
    if debug:
        print("Base Roll = " + str(baseResult))

    #Initial Variables for Caluculation
    rangeM = int(selectedWeapon.rangeM)
    maxRangeM = int(selectedWeapon.maxRange)
    isSniper = False
    if selectedWeapon.weaponType.className == "Sniper":
        isSniper = True

    # Calculate : Bullet Dropoff
    # Check Dummy Distance Against Range of Gun
    # If Dummy is past max weapon range, the weapon's base result is set to 100
    # Otherwise, apply range modifier
    if newDummy.distance > maxRangeM :
        baseResult = 100
    else :
        baseResult = getDummyRangeModifier(newDummy, rangeM, isSniper, baseResult)
    if debug:
        print("BaseResult w/ Range Modifier : " + str(baseResult))

    # Calculate : DUMMY SIZE BONUS
    # Check Dummy Size. Smaller the target, harder to hit, vice versa.
    baseResult = getDummySizeModifier(newDummy, baseResult)
    if debug:
        print("BaseResult w/ Dummy Size : " + str(baseResult))

    # CALCULATE : Bullet Spray
    # 3 Round Burst = Minimal Penalty
    # Every Shot after 3, penalty goes up on a scale
    if 1 < shots < 4:
        baseResult = baseResult * 3
    elif 4 <= shots <= 7:
        baseResult = baseResult * 10
    elif 7 < shots <= 10:
        baseResult = baseResult * 25
    elif 10 < shots <= 30:
        baseResult = baseResult * 150
    elif 30 < shots <= 100:
        baseResult = baseResult * 300
    if (shots > 1 and debug):
        print("Base Result w/ Bullet Spray : " + str(baseResult))

    # Critical Chance Roll for Damage (1/200 chance)
    isCritical = False
    criticalChance = roll(200)
    if criticalChance == 1:
        isCritical = True

    # Final Calculation
    criticalHits = 0
    if 0 <= baseResult <= selectedWeapon.baseAccuracy:
        if newDummy.distance > maxRangeM:
            damage = 0
        else:
            damage = getDamage(newDummy,rangeM,selectedWeapon.damage)
            if isCritical:
                damageBonus = roll(100)
                if damageBonus > 20:
                    damage *= 3
                else:
                    damage *= 2
        if debug:
            print("Hit!")
            print("Damage dealt = " + str(damage))
        hit = 1
    else:
        if debug:
            print("Miss!")
        hit = 0
        damage = 0
    result = [hit, damage, isCritical]
    return result

def getDummyRangeModifier(newDummy, rangeM, isSniper, baseResult):
    # Close Range Bonus
    if newDummy.distance < rangeM:
        closeRange = rangeM - newDummy.distance
        y = closeRange // 50
        # This Check Makes Sure that Sniper at Max Range doesn't get insane bonus
        if isSniper and y > 3:
            y = 4
        for x in range(0, y):
            baseResult -= 5
            if baseResult < 0:
                # Stops the hit from being subtracted to a miss by bonus
                baseResult = 0

    # Long Range Penalty
    elif newDummy.distance > rangeM:
        farRange = newDummy.distance - rangeM
        y = farRange // 50
        for x in range(0, y):
            baseResult += 10
    return baseResult

def getDummySizeModifier(newDummy, baseResult):
    size = newDummy.size
    match size:
        case 's':
            baseResult *= 1.10
        case 'l':
            baseResult *= 0.90
    return baseResult

def getDamage(newDummy,rangeM, weaponDamage):
    damage = weaponDamage
    if newDummy.distance > rangeM:
        farRange = newDummy.distance - rangeM
        y = farRange // 50
        for x in range(0, y):
            damage -= 25
    return damage