from auxiliaryParsing import pickleFunctions
import checkFunctions.sendMail as sendMail
from readFunctions import readSensorInformation as Rsi
from auxiliaryParsing.busDefinitions import labels_inetx
from Parsing.parseFunctions import get_variables_from_database, find_string_list_in_string_list
from stashclient.client import Client
from readFunctions.readSensorInformation import config_from_istar_flight


class check_logic():
    def __init__(self, data=None, stash_check=False):
        self.warning = []
        self.layerOneWarning = []
        self.layerTwoWarning = []
        self.data_parameters = []
        self.layerTwoList = []
        self.data = data
        self.sensorReader = Rsi.ReadSensorInformation()
        self.mailClient = sendMail.MailClient()
        # functionality
        if stash_check:
            self.check_stash_data(data)
        else:
            self.run_functions()

    def run_functions(self):
        self.get_required_parameters()
        self.layer_one_check()
        self.layer_two_check()
        self.print_warning()
        self.mailClient.set_mail_content(self.warning)
        # self.mailClient.sendMail()

    def check_stash_data(self, collection: str):
        """
        :param collection: collection name
        :return:
        :rtype:
        """
        # get stash Collection name
        self.instance = Client.from_instance_name("dev")
        # TODO: get parameter list from stash
        project_id = self.instance.search({"name": "FX ISTAR", "type": "project"})[0]["id"]
        flight_list = self.instance.search({"parent": project_id, "name": collection, "type": "collection"})
        # TODO: get parameter reference list from imcexp
        if flight_list[0]["user_tags"]["registration"] == "D-BDLR":
            config = config_from_istar_flight(flight_list[0]["name"])
        else:
            print("unknown aircraft")
        # level 1, get parameter names from stash
        parameter_list = self.instance.search(
            {"parent": flight_list[0]["id"], "type": "series", "is_basis_series": False})
        parameters = [parameter.get('user_tags')["Name"]["value"] for parameter in parameter_list if
                      "user_tags" in parameter and "Name" in parameter.get("user_tags")]
        # this has to be used to program out martins parameter abbreviations
        parameters.extend([parameter.get("name") for parameter in parameter_list
                           if "user_tags" in parameter or "Name" in parameter.get("user_tags")])
        # use "any" logic if it doesn't match to anything
        missing_parameters = [param for param in config.keys()
                              if not any(stash_param in param for stash_param in parameters)]
        # upload to stash. append to user_tags shm flag of flight
        flight_list[0]["user_tags"].update({"shm": {"missing_parameters": missing_parameters}})
        self.instance.update(flight_list[0]["id"], {"user_tags": flight_list[0]["user_tags"]})

        # parameter real name below usertags->name->value
        # TODO: level 2

    def get_parameter_from_stash(self):
        pass

    def get_required_parameters(self):
        # get required parameter list from config file
        self.requiredParameterList = get_variables_from_database(labels_inetx)
        self.data_parameters = list(self.data.keys())

    def set_limits(self):
        pass

    """
    ██╗░░░░░███████╗██╗░░░██╗███████╗██╗░░░░░  ░░███╗░░
    ██║░░░░░██╔════╝██║░░░██║██╔════╝██║░░░░░  ░████║░░
    ██║░░░░░█████╗░░╚██╗░██╔╝█████╗░░██║░░░░░  ██╔██║░░
    ██║░░░░░██╔══╝░░░╚████╔╝░██╔══╝░░██║░░░░░  ╚═╝██║░░
    ███████╗███████╗░░╚██╔╝░░███████╗███████╗  ███████╗
    ╚══════╝╚══════╝░░░╚═╝░░░╚══════╝╚══════╝  ╚══════╝    
    """

    def layer_one_check(self):
        # check if each parameter in requiredlist is in the listKeys from the dictonary
        self.layerOneWarning = [parameter for parameter in self.requiredParameterList if
                                parameter not in self.data_parameters]

    """
    ██╗░░░░░███████╗██╗░░░██╗███████╗██╗░░░░░  ██████╗░
    ██║░░░░░██╔════╝██║░░░██║██╔════╝██║░░░░░  ╚════██╗
    ██║░░░░░█████╗░░╚██╗░██╔╝█████╗░░██║░░░░░  ░░███╔═╝
    ██║░░░░░██╔══╝░░░╚████╔╝░██╔══╝░░██║░░░░░  ██╔══╝░░
    ███████╗███████╗░░╚██╔╝░░███████╗███████╗  ███████╗
    ╚══════╝╚══════╝░░░╚═╝░░░╚══════╝╚══════╝  ╚══════╝
    """

    def layer_two_check(self):
        self.create_layer_two_list()
        self.check_layer_two_parameter()

    def check_layer_two_parameter(self):
        self.check_noise()
        self.check_valid_value()
        self.check_range()

    def check_range(self):
        # for each sensor in layerTwoList
        for parameter in self.layerTwoList:
            checkElement = self.data[parameter][0][1]
            loopCount = 0
            lastid = -1
            # for each value in the in the value list form that sensor (checkElement)
            for value in checkElement:
                # if the value is over the limit max or under the limit min and that value is not in any of the other value error list or in that list
                # append that sensor
                # TODO: good idea to log the value just once but perhaps a good addition to add the time at which it happened
                if self.parameter_in_range(parameter, value):
                    if parameter not in self.layerOneWarning and (
                            parameter + " - WARNING: Layer Two Warning - Out of Range") not in self.layerTwoWarning \
                            and (value != checkElement[lastid]):
                        self.layerTwoWarning.append(parameter + " - WARNING: Layer Two Warning - Out of Range")
                        lastid = loopCount
                continue
            loopCount += 1

    def check_valid_value(self):
        # for each parameter in layerTwoList
        for parameter in self.layerTwoList:
            # get list of the element for that parameter
            checkElement = self.data[parameter][0][1]
            loopCount = 0
            lastid = -1
            for value in checkElement:
                # if any value in checkElement has one of the following values and that value is not in the warning list
                if value == 999 or value == 000 or str(value) == "nan" or value == None:
                    if parameter not in self.layerOneWarning and (
                            parameter + " - WARNING: Layer Two Warning - No Valid Value") not in self.layerTwoWarning \
                            and value != checkElement[lastid]:
                        # append layerTwowraring list and add the loop count to print location of that Warning
                        self.layerTwoWarning.append(
                            parameter + " - WARNING: Layer Two Warning - No Valid Value - ID: " + str(loopCount))
                        lastid = loopCount
                    continue
                loopCount += 1

    def parameter_in_range(self, name, value):
        if self.sensorReader.limits.get(name) is not None:
            return value > self.sensorReader.limits[name]["limits"]["max"] or value < \
                   self.sensorReader.limits[name]["limits"]["min"]
        else:
            return True

    def parameter_has_noise(self, name):
        if self.sensorReader.limits.get(name) is not None:
            return self.sensorReader.limits[name]["extras"]["noise"]
        else:
            return False

    def check_noise(self):
        # TODO: whats the algorithm here?
        # for each element in the layerTwoList
        for parameter in self.layerTwoList:
            # check if the parameter should have noise
            if self.parameter_has_noise(parameter):
                # from the parameter get all elements
                checkElement = self.data[parameter][0][1]
                loopCount = 0
                lastid = 0
                # for each element in the element list
                for element in checkElement:
                    checkElementList = checkElement[loopCount:loopCount + 250]
                    checkSum = 0
                    # sum up the element in the range of 250
                    for element in checkElementList:
                        checkSum += element
                    # calculate the middle value from that elements
                    checkSum = checkSum / 250
                    # if the elemnt has the same value as the checksum there is no noise in the sensor that means the next 250 values
                    # doesnt have overall the the value as the active element
                    if element == checkSum:
                        # if that element is not in the layerOneWaring and also not added into the layerTwo list and active element is not the
                        # checkElement[lastid] and the loop count is not 0
                        if parameter not in self.layerOneWarning \
                                and parameter + " - WARNING: Layer Two Warning - Noise Problem - ID: " + str(
                            loopCount) not in self.layerTwoWarning \
                                and (element != checkElement[lastid] or loopCount == 0):
                            self.layerTwoWarning.append(
                                parameter + " - WARNING: Layer Two Warning - Noise Problem - ID: " + str(loopCount))
                            lastid = loopCount
                    loopCount += 1
            else:
                continue

    def create_layer_two_list(self):
        # remove all elements form layerTwoList which had a Layer One Warning
        self.layerTwoList = list(self.requiredParameterList.keys())
        for parameter in self.layerOneWarning:
            self.layerTwoList.remove(parameter)

    def print_warning(self):
        # for each layer print the erroors
        for parameter in self.layerOneWarning:
            self.warning.append(parameter + " - WARNING: Layer One Warning - Parameter not Found")
        self.warning += self.layerTwoWarning
        for parameter in self.warning:
            print(parameter)
