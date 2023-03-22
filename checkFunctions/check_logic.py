import pandas as pd

from auxiliaryParsing import pickleFunctions
import checkFunctions.sendMail as sendMail
from readFunctions import readSensorInformation as Rsi
from auxiliaryParsing.busDefinitions import labels_inetx
from Parsing.parseFunctions import get_variables_from_database, find_string_list_in_string_list, get_mean_noise, \
    timestamp_from_utc, utc_from_timestamp, data_dict_to_dataframe
from stashclient.client import Client
from readFunctions.readSensorInformation import config_from_istar_flight
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

ft2m = 0.3048
m2ft = 1 / (ft2m)


class check_logic():
    def __init__(self, data=None, stash_check=False, instance="dev"):
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
            self.check_stash_data(data, instance)
        else:
            self.run_functions()

    def run_functions(self):
        self.get_required_parameters()
        self.layer_one_check()
        self.layer_two_check()
        self.print_warning()
        self.mailClient.set_mail_content(self.warning)
        # self.mailClient.sendMail()

    def pandas_from_stash(self, id):
        """

        :param id: stash data series id
        :type id: str
        :return: Pandas shape series
        :rtype: pandas.series
        """
        series_connector_id = self.instance.search({"id": id})[0]["series_connector_id"]
        time_id = self.instance.search({"series_connector_id": series_connector_id, "is_basis_series": True})[0]["id"]
        time_series = self.instance.data(time_id)
        data_series = self.instance.data(id)
        series = pd.Series(index=pd.to_datetime(time_series, unit="s"), data=data_series)
        return series

    def pandas_to_list(self, series):
        # datetime to str
        series.index = [utc_from_timestamp(single_time) for single_time in series.index.asi8 * 1e-9]
        # return as dictionary
        return series.to_dict()

    def check_stash_data(self, collection_id, instance="dev"):
        """
        :param collection: collection name
        :return:
        :rtype:
        """
        # get stash Collection name
        self.instance = Client.from_instance_name(instance)
        # get parameter list from stash
        flight_list = self.instance.search({"id": collection_id})
        # get parameter reference list from imcexp
        if flight_list[0]["user_tags"]["registration"] == "D-BDLR":
            config = config_from_istar_flight(flight_list[0]["name"])
        else:
            print("unknown aircraft")
            return

        missing_parameters, flight_parameters = self.layer_one_from_stash(collection_id, config.keys())
        print("level 1 check complete")
        # level_2_notes = self.layer_two_from_stash(collection_id, config)
        level_2_notes = {}
        print("level 2 check complete")
        # collect gps altitudes and calculate differences.

        # TODO: Level 3
        # download imar vs ascb gps and compare
        ascb = "ASCB_GPS_Gps1aGps429_gps50msec429_altitude_o"
        imar = "IMAR_GNSS_Altitude"
        imar = "IMAR_INS_Altitude"
        # download
        ascb_data = self.download_series(flight_parameters[ascb])
        imar_data = self.download_series(flight_parameters[imar])
        # resample to 1 Hz
        df = data_dict_to_dataframe({ascb: [ascb_data, ascb], imar: [imar_data, imar]}, 1)
        df[ascb] = df[ascb] * ft2m
        alt_diff = "altitude difference"
        df[alt_diff] = df[ascb] - df[imar]

        fig, ax1 = plt.subplots()

        color = 'tab:red'
        ax1.set_ylabel("Difference of ASCB to IMAR [m]", color=color)
        ax1.plot(df[alt_diff], color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

        color = 'tab:blue'
        ax2.set_ylabel("ASCB-GPS Altitude [m]", color=color)  # we already handled the x-label with ax1
        ax2.plot(df[ascb], color=color)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.plot(df[imar])
        plt.title("Difference of Gps Altitude")
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.show()

        # TODO: find a measure to autamatically generate thresholds

        # differences: mean has to be zero. Interesting spots: outside stdev

        # upload to stash. append to user_tags:SHM
        shm_dict = {"SHM": {"missing parameters": missing_parameters,
                            "single sensor behaviour": level_2_notes}}
        flight_list[0]["user_tags"].update(shm_dict)
        self.instance.update(flight_list[0]["id"], {"user_tags": flight_list[0]["user_tags"]})
        print("upload complete")

    def download_series(self, id):
        """
        attribute id is the stash id for a parameter series so that
        is_basis_series = False
        :param id:
        :type id:
        :return:
        :rtype:
        """
        properties = self.instance.search({"id": id})[0]
        if properties["is_basis_series"] == False:
            properties_time_series = self.instance.search({"series_connector_id": properties["series_connector_id"],
                                                           "is_basis_series": True})[0]
            time_data = self.instance.data(properties_time_series["id"])
            parameter_data = self.instance.data(id)

            return [time_data, parameter_data]
        else:
            raise Exception("Wrong input type for download_series in check_logic.py: is_basis_series must be False")

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

    def layer_one_from_stash(self, flight_id, config_parameters):
        """

        :param flight_id: stash hexadecimal identifier
        :type flight_id: str
        :param config_parameters: list of parameters that are in config
        :type config_parameters: list
        :return: list of parameters that are in config but not in stash
        :rtype: list
        """
        # level 1, get parameter names from stash
        parameter_list = self.instance.search(
            {"parent": flight_id, "type": "series", "is_basis_series": False})

        # this has to be used to program out martins parameter abbreviations
        parameter_names = {}
        for parameter in parameter_list:
            if "user_tags" in parameter and "Name" in parameter.get("user_tags"):
                parameter_names.update({parameter.get('user_tags')["Name"]["value"]:
                                            parameter['id']})
            else:
                print("No user tag \"name\" for parameter: " + parameter.get("name"))
                parameter_names.update({parameter.get("name"): ["id"]})

        # use "any" logic if it doesn't match to anything
        missing_parameters = [param for param in config_parameters
                              if not any(stash_param in param for stash_param in parameter_names.keys())]
        return missing_parameters, parameter_names

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

    def update_notes(self, notes, check_series, min_range, max_range, warning_string, parameter_name):
        """
        cleanup function. Checks whether values are in range and updates the notes section of SHM to display any
        anomalies
        :param notes:
        :type notes:
        :param check_series:
        :type check_series:
        :param min_range:
        :type min_range:
        :param max_range:
        :type max_range:
        :param warning_string:
        :type warning_string:
        :param parameter_name:
        :type parameter_name:
        :return:
        :rtype:
        """
        values_exceeded = check_series[~check_series.between(min_range, max_range)]
        if len(values_exceeded) > 0:
            notes[warning_string].update({parameter_name: {
                "occurences": self.pandas_to_list(values_exceeded),
                "range": {"min": min_range, "max": max_range}}})

    def layer_two_from_stash(self, collection_id, config):
        # parameter id under usertags->name->value
        # LEVEL 2
        parameter_list = self.instance.search(
            {"parent": collection_id, "type": "series", "is_basis_series": False})
        # check definition
        checks = {"physical": {"error_tag": "physical values out of range",
                               "min": "physical range min",
                               "max": "physical range max"},
                  "amplitude": {"error_tag": "amplitude out of range",
                                "min": "amplitude min",
                                "max": "amplitude max"}}
        notes = {value["error_tag"]: {} for value in checks.values()}
        column_names = []
        for value in checks.values():
            column_names.extend([value.get("min"), value.get("max")])

        progress_bar = tqdm(parameter_list)
        for parameter in progress_bar:
            parameter_name = parameter["user_tags"]["Name"]["value"]
            parameter_config = config[parameter_name]
            progress_bar.set_description("Processing %s" % parameter_name)
            # check if any of the given checks for min and max are within the parameter config
            if any(level_2_check in list(parameter_config.keys()) for level_2_check in column_names):
                # download parameter data into pandas series
                series = self.pandas_from_stash(parameter["id"])
                for check in checks.values():
                    range = [parameter_config.get(check["min"]), parameter_config.get(check["max"])]
                    if any(range):
                        self.update_notes(notes, series, range[0], range[1], check["error_tag"], parameter_name)
                """
                # check range
                min_range, max_range = parameter_config.get("physical range min"), \
                                       parameter_config.get("physical range max")
                if max_range is not None and min_range is not None:
                    self.update_notes(notes, series, min_range, max_range,
                                      "Physical Values out of Range", parameter_name)
                # check noise and get list with time, where values were exceeded
                min_amplitude, max_amplitude = parameter_config.get("amplitude min"), \
                                               parameter_config.get("amplitude max")
                if min_amplitude is not None and max_amplitude is not None:
                    mean_noise = get_mean_noise(series)[0]
                    self.update_notes(notes, mean_noise, min_amplitude, max_amplitude,
                                      "Amplitude out of range", parameter_name)
                """
        return notes

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
