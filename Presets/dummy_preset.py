from Objects.dummy import Dummy

small = Dummy(125, 0, 's')
medium = Dummy(200, 0, 'm')
large = Dummy(275, 0, 'l')

def getNewDummy(size):
    match size:
        case 's':
            newDummy = small
        case 'm':
            newDummy = medium
        case 'l':
            newDummy = large
        case _:
            newDummy = medium
    return newDummy