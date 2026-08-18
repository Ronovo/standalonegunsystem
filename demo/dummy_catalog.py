from demo.dummy import Dummy, RANGES


def prompt_dummy_range(dummy: Dummy, debug: bool = False) -> None:
    while True:
        print("Please select distance for dummy")
        print("----------")
        print("1.) 50 Meters")
        print("2.) 100 Meters")
        print("3.) 150 Meters")
        print("4.) 200 Meters")
        print("5.) 300 Meters")
        print("6.) 400 Meters")
        print("7.) 500 Meters")
        print("8.) return \n")
        answer = input("Pick 1-8\n")
        try:
            choice = int(answer)
        except ValueError:
            print("Incorrect choice. Try again.")
            continue
        if 1 <= choice <= 7:
            dummy.distance = RANGES[choice - 1]
            if debug:
                print(f"Dummy has been set to range of {dummy.distance}")
            return
        if choice == 8:
            return
        print("Incorrect choice. Try again.")


def prompt_new_dummy(debug: bool = False) -> Dummy:
    print("Dummy Size:")
    print("s = small, m = medium, l = large")
    size = input("Select your Size of Dummy\n").lower()
    if size not in ("s", "m", "l"):
        print("Invalid Option, Dummy set to Medium")
        size = "m"
    dummy = Dummy(size)
    prompt_dummy_range(dummy, debug)
    return dummy
