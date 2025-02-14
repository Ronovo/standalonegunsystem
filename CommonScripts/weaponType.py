from Objects import weapons
choices = ['Small Arms', 'Medium Arms', 'Large Arms']

#TODO Add Return to Weapon Type Menu When in that sub menu
def weaponTypeMenu(weaponList):
    print("Please select a weapon type:")
    print("----------------------")
    print("1.) " + choices[0])
    print("2.) " + choices[1])
    print("3.) " + choices[2])
    answer = input("Pick 1-3\n")
    print("\n")
    wType = ''
    if 0 < int(answer) < 4:
        weaponList = []
        choiceIndex = int(answer) - 1
        wType = choices[choiceIndex]
    else:
        print("Incorrect choice. Returning to Menu")

    # Get Weapon List
    if wType != '':
        newlist = weapons.getWeaponListByWeaponType(wType)
        if len(newlist) != 0:
            for x in newlist:
                weaponList.append(x.name)
    return weaponList

def selectWeaponMenu(weaponList):
    wFlag = True
    while wFlag:
        # Menu Counter
        n = 1
        for x in weaponList:
            print(str(n) + ".) " + x)
            n += 1
        print(str(n) + ".) Return to Main Menu")
        answer = input("Pick 1-" + str(n) + "\n")
        print("\n")
        if answer == str(n):
            w = 0
            wFlag = False
        else:
            try:
                w = int(answer)
                wFlag = False
            except ValueError:
                print("Please enter a valid number")
    return w
