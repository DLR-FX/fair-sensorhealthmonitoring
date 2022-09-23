from auxiliaryParsing import pickleFunctions
import checkFunctions.sendMail as sendMail
from readFunctions import readSensorInformation as Rsi
class checkLogic():
    def __init__(self):
        #init all list and geht the pickle file with data to check
        self.fileToCheck = "C:/Users/vond_mr/Documents\InflightStreamingData/rawData.pickle"
        self.requiredParameterList = ["alt", "IR_FPACCEL"]
        self.warning = []
        self.layerOneWarning = []
        self.layerTwoWarning = []
        self.listKeys = []
        self.dictionary = []
        self.layerTwoList = []
        self.sensorReader = Rsi.ReadSensorInformation()
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
        #open the dictionary and save the keys (sensor names) as a list
        self.dictionary = pickleFunctions.loosen(self.fileToCheck)
        self.listKeys = list(self.dictionary.keys())

    def layerOneCheck(self):
        #check if each parameter in requiredlist is in the listKeys from the dictonary
        self.layerOneWarning = [parameter for parameter in self.requiredParameterList if parameter not in self.listKeys]

    def layerTwoCheck(self):
        self.createLayerTwoList()
        self.checkLayerTwoParameter()

    def checkLayerTwoParameter(self):
        self.checkNoise()
        self.checkValidValue()
        self.checkRange()

    def checkRange(self):
        #for each sensor in layerTwoList
        for parameter in self.layerTwoList:
            checkElement = self.dictionary[parameter][0][1]
            loopCount = 0
            lastid = -1
            #for each value in the in the value list form that sensor (checkLElement)
            for element in checkElement:
                #if the value is over the limit max or under the limit min and that value is not in any of the other value error list or in that list
                #append that sensor
                if element > self.sensorReader.limits[parameter]["limits"]["max"] or element < self.sensorReader.limits[parameter]["limits"]["min"]:
                    if parameter not in self.layerOneWarning and (parameter + " - WARNING: Layer Two Warning - Out of Range") not in self.layerTwoWarning\
                            and (element != checkElement[lastid]):
                        self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - Out of Range")
                        lastid = loopCount
                continue
            loopCount += 1


    def checkValidValue(self):
        #for each parameter in layerTwoList
        for parameter in self.layerTwoList:
            #get list of the element for that parameter
            checkElement = self.dictionary[parameter][0][1]
            loopCount = 0
            lastid = -1
            for element in checkElement:
                #if any value in checkElement hats one of the following values and that element is not in the waring list
                if element == 999 or element == 000 or str(element) == "nan" or element == None:
                    if parameter not in self.layerOneWarning and (parameter + " - WARNING: Layer Two Warning - No Valid Value") not in self.layerTwoWarning\
                            and element != checkElement[lastid]:
                        #append layerTwowraring list and add the loop count to print location of that Warning
                        self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - No Valid Value - ID: " + str(loopCount))
                        lastid = loopCount
                    continue
                loopCount += 1

    def checkNoise(self):
        #for each element in the layerTwoList
        for parameter in self.layerTwoList:
            #check if the parameter should have noise
            if self.sensorReader.limits[parameter]["extras"]["noise"] == True:
                #from the parameter get all elements
                checkElement = self.dictionary[parameter][0][1]
                loopCount = 0
                lastid = 0
                #for each element in the elment list
                for element in checkElement:
                    checkElementList = checkElement[loopCount:loopCount+250]
                    checkSum = 0
                    #sum up the element in the range of 250
                    for element in checkElementList:
                        checkSum += element
                    #calculate the middle value from that elements
                    checkSum = checkSum / 250
                    #if the elemnt has the same value as the checksum there is no noise in the sensor that means the next 250 values
                    #doesnt have overall the the value as the active element
                    if element == checkSum:
                        #if that element is not in the layerOneWaring and also not added into the layerTwo list and active element is not the
                        #checkElement[lastid] and the loop count is not 0
                        if parameter not in self.layerOneWarning \
                                and parameter + " - WARNING: Layer Two Warning - Noise Problem - ID: " + str(loopCount) not in self.layerTwoWarning \
                                and (element != checkElement[lastid] or loopCount == 0):
                            self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - Noise Problem - ID: " + str(loopCount))
                            lastid = loopCount
                    loopCount += 1
            else:
                continue

    def createLayerTwoList(self):
        #remove all elements form layerTwoList which had a Layer One Warning
        self.layerTwoList = self.requiredParameterList
        for parameter in self.layerOneWarning:
            self.layerTwoList.remove(parameter)

    def printWarning(self):
        #for each layer print the erroors
        for parameter in self.layerOneWarning:
            self.warning.append(parameter + " - WARNING: Layer One Warning - Parameter not Found")
        self.warning += self.layerTwoWarning
        for parameter in self.warning:
            print(parameter)
