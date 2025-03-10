from CommonScripts import formatter
from Screens import armory
from Screens import range
from Screens import bulk
from Screens import balance

formatter.clear()
print("Welcome to Ronovo's Stand Alone Gun System\n")
print("Designed to be plugged into text adventure games\n")
wrong = False
while 1:
    if wrong:
        print("Incorrect choice. Try again.\n")
        wrong = False
    print("MAIN MENU")
    print("----------")
    print("1.) Armory - View Weapons In Detail")
    print("2.) Range - Select Gun and try it on range")
    print("3.) Bulk Fire Report")
    print("4.) Run a Balance Report")
    print("5.) Quit\n")
    answer = input("Pick 1-5\n")
    formatter.clear()
    match answer:
        case '1':
            armory.armoryMainMenu()
        case '2':
            range.rangeMain()
        case '3':
            bulk.bulkShots()
        case '4':
            balance.balanceReport()
        case '5':
            quit()
        case _:
            wrong = True
    formatter.clear()
