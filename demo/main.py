from demo.screens import armory, balance, bulk, range as range_screen
from demo.ui import formatter


def run() -> None:
    formatter.clear()
    print("Welcome to Ronovo's Stand Alone Gun System\n")
    print("Designed to be plugged into text adventure games\n")
    wrong = False
    while True:
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
            case "1":
                armory.armory_main_menu()
            case "2":
                range_screen.range_main()
            case "3":
                bulk.bulk_shots()
            case "4":
                balance.balance_report()
            case "5":
                return
            case _:
                wrong = True
        formatter.clear()
