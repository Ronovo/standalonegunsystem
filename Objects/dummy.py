class Dummy:
    def __init__(self, health, distance, size):
        self.health = health
        self.distance = distance
        self.size = size

    def takeDamage(self, damage):
        self.health -= damage

    def setDummyRange(self, debug):
        dFlag = False
        dummyRange = 0
        while not dFlag:
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
            numAnswer = int(answer)
            if 0 < numAnswer < 5:
                dummyRange = 50 * numAnswer
                dFlag = True
            elif 4 < numAnswer < 8:
                dFlag = True
                match numAnswer:
                    case 5:
                        dummyRange = 300
                    case 6:
                        dummyRange = 400
                    case 7:
                        dummyRange = 500
            elif numAnswer == 8:
                quit()
            else:
                print("Incorrect choice. Try again.")
        self.distance = dummyRange
        if debug:
            print("Dummy has been set to range of " + str(dummyRange))

    def setDummyRangeBalanceReport(self, distance):
        self.distance = distance



