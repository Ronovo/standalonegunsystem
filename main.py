from Screens import armory
from Screens import range
from Screens import bulk

print("Welcome to Ronovo's Stand Alone Gun System")
print("Designed to be plugged into text adventure games")
print("\n")
while 1:
    print("MAIN MENU")
    print("----------")
    print("1.) Armory - View Weapons In Detail")
    print("2.) Range - Select Gun and try it on range")
    print("3.) Bulk Fire Report")
    print("4.) Quit\n")
    answer = input("Pick 1-4\n")
    match answer:
        case '1':
            armory.armoryMainMenu()
        case '2':
            range.rangeMain()
        case '3':
            bulk.bulkShots()
        case '4':
            quit()
        case _:
            print("Incorrect choice. Try again.")
