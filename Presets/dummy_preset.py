from Objects.dummy import Dummy

small = Dummy(125, 0, 's')
medium = Dummy(200, 0, 'm')
large = Dummy(275, 0, 'l')

def getNewDummy(debug):
    print("Dummy Size:")
    print("s = small, m = medium, l = large")
    size = input("Select your Size of Dummy\n")
    size = str.lower(size)
    match size:
        case 's':
            newDummy = small
        case 'm':
            newDummy = medium
        case 'l':
            newDummy = large
        case _:
            print("Invalid Option, Dummy set to Medium")
            newDummy = medium
    newDummy.setDummyRange(debug)
    return newDummy