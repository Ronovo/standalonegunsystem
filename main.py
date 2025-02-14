from Screens import armory
from Screens import range

print("Welcome to Ronovo's Stand Alone Gun System")
print("Designed to be plugged into text adventure games")
print("\n")
while 1:
    print("MAIN MENU")
    print("----------")
    print("1.) Armory - View Weapons In Detail")
    print("2.) Range - Select Gun and try it on range")
    print("3.) Quit\n")
    answer = input("Pick 1-3\n")
    match answer:
        case '1':
            armory.armoryMainMenu()
        case '2':
            range.range()
        case '3':
            quit()
        case _:
            print("Incorrect choice. Try again.")
