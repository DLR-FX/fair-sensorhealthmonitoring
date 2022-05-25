from auxiliaryParsing import pickleFunctions
import checkFunctions.sendMail as sendMail
class checkLogic():
    def __init__(self):
        self.fileToCheck = "C:/Users/vond_mr/Documents\InflightStreamingData/rawData.pickle"
        self.requiredParameterList = ["alt", "AD_BCALT1"]
        self.warning = []
        self.layerOneWarning = []
        self.layerTwoWarning = []
        self.listKeys = []
        self.dictionary = []
        self.layerTwoList = []
        self.limits = {"AD_BCALT1": {
            "extras": {
                "noise": False
            },
            "limits": {
                "max": 10000000,
                "min": -10
                }
            }
        }
        self.mailClient = sendMail.MailClient()
        self.runFunctions()

    def set_requiredParameterList(self):
        pass

    def set_limits(self):
        pass

    def runFunctions(self):
        self.fillParameterList()
        self.layerOneCheck()
        self.layerTwoCheck()
        self.printWarning()
        self.mailClient.setMailContent(self.warning)
        #self.mailClient.sendMail()

    def fillParameterList(self):
        self.dictionary = pickleFunctions.loosen(self.fileToCheck)
        self.listKeys = list(self.dictionary.keys())

    def layerOneCheck(self):
        self.layerOneWarning = [parameter for parameter in self.requiredParameterList if parameter not in self.listKeys]

    def layerTwoCheck(self):
        self.createLayerTwoList()
        self.checkLayerTwoParameter()

    def checkLayerTwoParameter(self):
        self.checkNoise()
        self.checkValidValue()
        self.checkRange()

    def checkRange(self):
        for parameter in self.layerTwoList:
            checkElement = self.dictionary[parameter][0][1]
            loopCount = 0
            lastid = -1
            for element in checkElement:
                if element > self.limits[parameter]["limits"]["max"] or element < self.limits[parameter]["limits"]["min"]:
                    if parameter not in self.layerOneWarning and (parameter + " - WARNING: Layer Two Warning - Out of Range") not in self.layerTwoWarning\
                            and element != checkElement[lastid]:
                        self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - Out of Range")
                        lastid = loopCount
                continue
            loopCount += 1


    def checkValidValue(self):
        for parameter in self.layerTwoList:
            checkElement = self.dictionary[parameter][0][1]
            loopCount = 0
            lastid = -1
            for element in checkElement:
                if element == 999 or element == 000 or str(element) == "nan" or element == None:
                    if parameter not in self.layerOneWarning and (parameter + " - WARNING: Layer Two Warning - No Valid Value") not in self.layerTwoWarning\
                            and element != checkElement[lastid]:
                        self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - No Valid Value")
                        lastid = loopCount
                    continue
                loopCount += 1

    def checkNoise(self):
        for parameter in self.layerTwoList:
            if self.limits[parameter]["extras"]["noise"] == True:
                checkElement = self.dictionary[parameter][0][1]
                loopCount = 0
                lastid = 0
                for element in checkElement:
                    if loopCount+5 < len(checkElement) and element == checkElement[loopCount+5]:
                        if parameter not in self.layerOneWarning \
                                and parameter + " - WARNING: Layer Two Warning - Noise Problem - ID: " + str(loopCount) not in self.layerTwoWarning \
                                and element != checkElement[lastid]:
                            self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - Noise Problem - ID: " + str(loopCount))
                            lastid = loopCount
                    loopCount += 1
            else:
                continue

    def createLayerTwoList(self):
        self.layerTwoList = self.requiredParameterList
        for parameter in self.layerOneWarning:
            self.layerTwoList.remove(parameter)

    def printWarning(self):
        for parameter in self.layerOneWarning:
            self.warning.append(parameter + " - WARNING: Layer One Warning - Parameter not Found")
        self.warning += self.layerTwoWarning
        for parameter in self.warning:
            print(parameter)
