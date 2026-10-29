from gunsystem.dummy import RANGES, Dummy
from gunsystem.target import SIZES
from demo.ui import formatter


def prompt_dummy_range(dummy: Dummy, debug: bool = False) -> None:
    print("Please select distance for dummy")
    print("----------")
    choice = formatter.choose([f"{distance} Meters" for distance in RANGES], back="return")
    if choice is not None:
        dummy.distance = RANGES[choice]
        if debug:
            print(f"Dummy has been set to range of {dummy.distance}")


def prompt_new_dummy(debug: bool = False, distance: int | None = None) -> Dummy:
    print("Dummy Size:")
    print(", ".join(f"{code} = {size.label.lower()}" for code, size in SIZES.items()))
    size = input("Select your Size of Dummy\n").lower()
    if size not in SIZES:
        print("Invalid Option, Dummy set to Medium")
        size = "m"
    if distance is not None:
        return Dummy(size, distance)
    dummy = Dummy(size)
    prompt_dummy_range(dummy, debug)
    return dummy
