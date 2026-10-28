from demo.dummy import SIZE_STATS, Dummy, RANGES


def prompt_dummy_range(dummy: Dummy, debug: bool = False) -> None:
    back = len(RANGES) + 1
    while True:
        print("Please select distance for dummy")
        print("----------")
        for index, distance in enumerate(RANGES, start=1):
            print(f"{index}.) {distance} Meters")
        print(f"{back}.) return \n")
        answer = input(f"Pick 1-{back}\n")
        try:
            choice = int(answer)
        except ValueError:
            print("Incorrect choice. Try again.")
            continue
        if 1 <= choice <= len(RANGES):
            dummy.distance = RANGES[choice - 1]
            if debug:
                print(f"Dummy has been set to range of {dummy.distance}")
            return
        if choice == back:
            return
        print("Incorrect choice. Try again.")


def prompt_new_dummy(debug: bool = False, distance: int | None = None) -> Dummy:
    print("Dummy Size:")
    print("s = small, m = medium, l = large")
    size = input("Select your Size of Dummy\n").lower()
    if size not in SIZE_STATS:
        print("Invalid Option, Dummy set to Medium")
    if distance is not None:
        return Dummy(size, distance)
    dummy = Dummy(size)
    prompt_dummy_range(dummy, debug)
    return dummy
