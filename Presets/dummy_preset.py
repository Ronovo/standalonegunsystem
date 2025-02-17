from Objects.dummy import Dummy

small = Dummy(125, 0, 's')
medium = Dummy(200, 0, 'm')
large = Dummy(275, 0, 'l')

sizes = ['Small','Medium','Large']
ranges = [50,100,150,200,300,400,500]

def getSizes():
    return sizes

def getRanges():
    return ranges


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

def getNewDummyBalanceReport(size):
    match size:
        case 'Small':
            newDummy = small
        case 'Medium':
            newDummy = medium
        case 'Large':
            newDummy = large
        case _:
            newDummy = medium
    return newDummy