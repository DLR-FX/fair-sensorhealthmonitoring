import time

from Parsing import parseIMCEXP as Rsi
import pandas as pd
import checkFunctions.sendMail as sendMail
from config.dcode_busDefinitions import labels_inetx
from Parsing.parseFunctions import get_variables_from_database, utc_from_timestamp, data_dict_to_dataframe, \
    get_mean_noise
from stashclient.client import Client
from Parsing.parseIMCEXP import config_from_istar_flight
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from checkFunctions.level3 import altitude_from_pressure, short_time_statistics, fuse_redundant_sensors, \
    compare_reference_to_signal, normalize_unit
import numpy as np
from check_config import level2_checks

ft2m = 0.3048
m2ft = 1 / (ft2m)
inHg2hPa = 33.8639


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
        # load from external file
        check_config = level2_checks
        # get stash Collection name
        self.instance = Client.from_instance_name(instance)
        # get parameter list from stash
        flight_list = self.instance.search({"id": collection_id})
        # get parameter reference list from imcexp
        if flight_list[0]["user_tags"]["registration"] == "D-BDLR":
            config = config_from_istar_flight(flight_list[0]["name"])
        else:
            print("unknown aircraft")
            return 0

        missing_parameters, flight_parameters = self.layer_one_from_stash(collection_id, config.keys())
        print("level 1 check complete")
        level_2_notes = self.layer_two_from_stash(collection_id, config, check_config)
        print("level 2 check complete")
        # upload to stash. append to user_tags:SHM
        shm_dict = {"missing parameters": missing_parameters,
                    "single sensor behaviour": level_2_notes}
        self.update_shm_usertags(collection_id, shm_dict)
        # TODO: Level 3 only with parameters that are not wonky
        self.level_3(flight_parameters, config)

        """
        # compare Covariance/Correlation of fused and actual signal
        # download imar vs ascb gps and compare
        parameter_down = {
            "baro": "ASCB_ADS_Ads1ADA_airData50msec_baroAltitude1_o",
            "p_static": "ASCB_ADS_Ads1ADA_airData50msec_staticPressure_o",
            "p_ref": "ASCB_ADS_Ads1ADA_airData50msec_mbBaroCorrection1_o",
            "baro_uncorr": "ASCB_ADS_Ads1ADA_airData50msec_pressureAltitude_o",
            "p_static_nose": "NOSE_StaticPressure"
        }
        parameter_two = {
            "pressure_alt": "ASCB_ADS_Ads1ADA_airData50msec_pressureAltitude_o",
            "baro_alt": "ASCB_ADS_Ads1ADA_airData50msec_baroAltitude1_o",
            "static pressure": "ASCB_ADS_Ads1ADA_airData50msec_staticPressure_o",
            "baro_ref": "ASCB_ADS_Ads1ADA_airData50msec_mbBaroCorrection1_o",
            "gps": "ASCB_GPS_Gps1aGps429_gps50msec429_altitude_o",
            "cas": "ASCB_ADS_Ads1ADA_airData50msec_calibratedAirspeed_o"
        }

        parameter_data = {}
        for key, value in parameter_down.items():
            parameter_data.update({key: [self.download_series(flight_parameters[value]), key]})
        # resample and into dataframe
        df = data_dict_to_dataframe(parameter_data, 25)
        """
        print("upload complete")

    def update_shm_usertags(self, id, shm_dict):
        """
        receive
        -collection, series or project id
        -dictionary containing elements of Sensor Health Monitoring JSON-dict
        :param id:
        :type id:
        :param shm_dict:
        :type shm_dict:
        :return:
        :rtype:
        """
        flight_list = self.instance.search({"id": id})
        flight_list[0]["user_tags"].update({"SHM": shm_dict})
        self.instance.update(id, {"user_tags": flight_list[0]["user_tags"]})

    def download_series(self, id, convert_to_SI=False):
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
            time_data = self.instance.data(properties_time_series["id"], "list")
            parameter_data = self.instance.data(id, "list")

            if convert_to_SI:
                parameter_data, si_unit = normalize_unit(parameter_data, properties["unit"])

            return [time_data, list(parameter_data)]
        else:
            raise Exception("Wrong input type for download_series in check_logic.py: is_basis_series must be False")

    def download_series_si(self, id):
        """
        download series and convert to si unit

        :param id:
        :type id:
        :return:
        :rtype:
        """

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
                parameter_names.update({parameter.get('user_tags')["Name"]: parameter['id']})
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

    def layer_two_from_stash(self, collection_id, config, check_config):
        """

        :param collection_id: stash hex-id of flight/collection
        :type collection_id:
        :param config: merged config (imcexp+excel) for all parameters
        :type config:
        :param check_config: config dictionary for checks that are about to be performed
        :type check_config:
        :return: dictionary format containing fault report
        :rtype:
        """
        # parameter id under usertags->name->value
        # LEVEL 2
        parameter_list = self.instance.search(
            {"parent": collection_id, "type": "series", "is_basis_series": False})

        notes = {value["error_tag"]: {} for value in check_config.values()}
        # transform into column names
        column_names = []
        for value in check_config.values():
            column_names.extend([value.get("min"), value.get("max")])

        progress_bar = tqdm(parameter_list)
        for parameter in progress_bar:
            parameter_name = parameter["user_tags"]["Name"]
            parameter_config = config[parameter_name]
            progress_bar.set_description("Processing %s" % parameter_name)
            # check if any of the given checks for min and max are within the parameter config
            if any(level_2_check in list(parameter_config.keys()) for level_2_check in column_names):
                # download parameter data into pandas series
                series = self.pandas_from_stash(parameter["id"])
                for check in check_config.values():
                    limits = [parameter_config.get(check["min"]), parameter_config.get(check["max"])]
                    if any(limits):  # if parameter limits are defined in config file
                        if check.get("function") is not None:
                            check_series = check.get("function")(series)
                        else:
                            check_series = series
                        values_exceeded = check_series[~check_series.between(limits[0], limits[1])]
                        if len(values_exceeded) > 0:  # if any occurences have been found
                            notes[check["error_tag"]].update({parameter_name: {
                                "occurences": self.pandas_to_list(values_exceeded),
                                "limits": {"min": limits[0], "max": limits[1]}}})

        return notes

    """
    ██╗░░░░░███████╗██╗░░░██╗███████╗██╗░░░░░  ██████╗░
    ██║░░░░░██╔════╝██║░░░██║██╔════╝██║░░░░░  ╚════██╗
    ██║░░░░░█████╗░░╚██╗░██╔╝█████╗░░██║░░░░░  ░█████╔╝
    ██║░░░░░██╔══╝░░░╚████╔╝░██╔══╝░░██║░░░░░  ░╚═══██╗
    ███████╗███████╗░░╚██╔╝░░███████╗███████╗  ██████╔╝
    ╚══════╝╚══════╝░░░╚═╝░░░╚══════╝╚══════╝  ╚═════╝░
    """

    def level_3(self, parameter_list, config):
        # TODO: create routine for each parameter tag
        # decide between direct/indirect parameters

        # ALTITUDES
        ##start with barometrics
        # get parameter names that have references:
        taglist = ["barometric altitude", "pressure altitude", "static pressure", "ellipsoid altitude",
                   "orthometric altitude"]
        correlation_dict = {}
        # collect tags from config and stash
        for parameter_key, parameter_value in config.items():
            if parameter_value.get("tag") is not None:
                # add new tags to dictionary
                if correlation_dict.get(parameter_value.get("tag")) is None:
                    correlation_dict[parameter_value.get("tag")] = {}
                # add parameters to correlation dictionary
                correlation_dict[parameter_value.get("tag")].update({parameter_key: parameter_value})

        # get altitudes that are tagged with "barometric altitude"
        # dont get altitudes that are tagged with "pressure altitude". seem useless and redundant with barometric altitude
        # "static pressure" needs "reference altitude" parameter name directly within its metadata

        correlations_config = {
            "altitudes": {"static pressure": {"function": altitude_from_pressure, "reference_value": True},
                          "barometric altitude": {"reference_value": True},
                          "pressure altitude": {"reference_value": False},
                          "orthometric altitude":{}}}


        # iterate through values representing the same feature
        for principal_feature in correlations_config.keys():
            df_same_parameters = pd.DataFrame() #pf-principal feature
            # operate on each different subtag of a feature
            for tag in correlations_config[principal_feature].keys():
                # for each parameter that is tagged with the same value
                for parameter in correlation_dict[tag].keys():
                    series = self.download_series(parameter_list[parameter], convert_to_SI=True)
                    # if tag contains a reference value --> collect reference value
                    if correlations_config[principal_feature][tag].get("reference_value"):
                        reference_series = self.download_series(
                            parameter_list[config[parameter]["reference"]],
                            convert_to_SI=True)
                        df = data_dict_to_dataframe(
                            {"series": [series, "series"], "reference": [reference_series, "reference"]}, 25)
                    else:
                        df = data_dict_to_dataframe(
                            {"series": [series, "series"]}, 25)
                    if correlations_config[principal_feature][tag].get("function") is not None:
                        df_same_parameters[parameter] = correlations_config[principal_feature][tag]["function"](df["series"], df["reference"])
                    else:
                        df_same_parameters[parameter] = df["series"]
            # fuse all sensor of the same feature/principal feature
            fused = fuse_redundant_sensors(df_same_parameters)
            for parameter in list(df_same_parameters.columns):
                # compare and upload info to sensor user_tags SHM
                report = compare_reference_to_signal(fused, df_same_parameters[parameter])
                # upload
                report["suspicious values"] = self.pandas_to_list(report["suspicious values"])
                self.update_shm_usertags(parameter_list[parameter], report)


        print(time.ctime() + "\tLevel 3 completed")
