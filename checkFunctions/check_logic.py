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
    compare_reference_to_signal, normalize_unit, baro_to_gnss, ellipsoid_to_orthometric, gnss_speed
import numpy as np
from check_config import check_config

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

    def reset_parameter_shm(self, id):
        # find all parameters from collection
        parameters = self.instance.search({"parent": id, "is_basis_series":False})

        # get parameters that contain SHM usertags
        parameters_filtered = [parameter for parameter in parameters
                               if parameter["user_tags"].get("SHM") is not None]

        # pop SHM usertags
        for parameter in parameters_filtered:
            parameter["user_tags"].pop("SHM")
            # reapply parameters that had SHM user_tags
            self.instance.update(parameter["id"], {"user_tags":parameter["user_tags"]})

    def update_shm_usertags(self, id, shm_dict):
        """
        receive
        -collection, series or project id
        -dictionary containing elements of Sensor Health Monitoring JSON-dict
        :param cleanup: If true reset SHM dict to wipe previous clutter
        :type cleanup: Bool
        :param id:
        :type id:
        :param shm_dict:
        :type shm_dict:
        :return:
        :rtype:
        """
        flight_list = self.instance.search({"id": id})
        # update SHM dict and to allow multiple partial updates for SHM dict
        if flight_list[0]["user_tags"].get("SHM") is None:
            flight_list[0]["user_tags"].update({"SHM": shm_dict})
        else:
            flight_list[0]["user_tags"]["SHM"].update(shm_dict)

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

    def check_stash_data(self, collection_id, instance="dev"):
        """
        :param collection: collection name
        :return:
        :rtype:
        """
        # load from external file

        check_config_2 = check_config["level 2"]
        check_config_3 = check_config["level 3"]
        # get stash Collection name
        self.instance = Client.from_instance_name(instance)
        self.collection_id = collection_id
        # get parameter list from stash
        flight_list = self.instance.search({"id": collection_id})
        # get parameter reference list from imcexp
        if flight_list[0]["user_tags"]["registration"] == "D-BDLR":
            config = config_from_istar_flight(flight_list[0]["name"])
        else:
            print("unknown aircraft")
            return 0
        self.name_aircraft = flight_list[0]["user_tags"]["registration"]


        # cleanup shm user_tags in series from previous iterations
        self.reset_parameter_shm(collection_id)

        missing_parameters, flight_parameters = self.layer_one_from_stash(collection_id, config.keys())
        self.update_shm_usertags(collection_id, {"missing parameters": missing_parameters})
        print("level 1 check complete")

        if True:
            level_2_notes = self.layer_two_from_stash(collection_id, config, check_config_2)
            self.update_shm_usertags(collection_id, {"single sensor behaviour": level_2_notes})
            print("level 2 check complete")

        # TODO: Level 3 only with parameters that are not wonky
        self.level_3(flight_parameters, config, check_config_3)
        print("upload complete")

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

    def level_3(self, parameter_list, config, check_config):
        # TODO: create routine for each parameter tag
        # decide between direct/indirect parameters

        # ALTITUDES
        ##start with barometrics
        # get parameter names that have references:
        taglist = ["barometric altitude", "pressure altitude", "static pressure", "ellipsoid altitude",
                   "orthometric altitude"]
        correlation_dict = {}
        # collect tags from config and stash. used in download step of recursive processing
        for parameter_key, parameter_value in config.items():
            if parameter_value.get("tag") is not None:
                # add new tags to dictionary
                if correlation_dict.get(parameter_value.get("tag")) is None:
                    correlation_dict[parameter_value.get("tag")] = {}
                # add parameters to correlation dictionary
                correlation_dict[parameter_value.get("tag")].update({parameter_key: parameter_value})

        self.tag_lookup = correlation_dict
        self.flight_parameters = parameter_list

        self.check_lvl3(check_config, parameter_list)

        print(time.ctime() + "\tLevel 3 completed")

    def check_lvl3(self, check_config, parameter_list):
        """
        this is the top level function that does generally the same as parse_lvl3_config() but lacks utility since it only
        treats the top level parameters
        :param check_config:
        :type check_config:
        :param parameter_list:
        :type parameter_list:
        :return:
        :rtype:
        """
        # put weighting for hierarchical order.
        df_select = pd.DataFrame()
        compact_config = self.compact_config(self.name_aircraft, check_config)

        for component_name, subcomponent in check_config["components"].items():
            df_select[component_name], data_dict = self.parse_lvl3_config(subcomponent, component_name)

            for parameter, value in data_dict.items():
                # compare and upload info to sensor user_tags SHM
                report = compare_reference_to_signal(df_select[component_name], value["data"])

                # upload and sort
                report["suspicious values"] = self.pandas_to_list(report["suspicious values"])
                report["tag"] = value["tag"]
                self.update_shm_usertags(parameter_list[parameter], report)

                # add tags to components. add property tab first to allow cleaner interface lol
                if compact_config[component_name].get("properties") is None:
                    compact_config[component_name]["properties"] = {}
                if compact_config[component_name]["properties"].get("tags") is None:
                    compact_config[component_name]["properties"]["tags"] = {}
                if value["tag"] not in compact_config[component_name]["properties"]["tags"]:
                    compact_config[component_name]["properties"]["tags"].update({value["tag"]:[parameter]})
                else:
                    compact_config[component_name]["properties"]["tags"][value["tag"]].append(parameter)

            compact_config[component_name]["properties"]["checking_range"] = report.get("checking_range")


        for column in df_select.columns:
            select_series = df_select[column].resample("5S").ffill()
            compact_config[column]["properties"]["data"] = [(select_series.index.asi8 * 1e-9).tolist(), select_series.values.tolist()]

            # also upload to collection user_tags. This contains check_config as well as fused parameters
        self.update_shm_usertags(self.collection_id, {"level 3": compact_config})

    def compact_config(self, name, check_config):
        config_dict = {}
        if check_config.get("components") is not None:
            for key, value in check_config["components"].items():
                config_dict.update({key: self.compact_config(key, value)})
        else:
            # add tags from tag lookup
            for parameter in self.tag_lookup[name]:
                config_dict.update({parameter: {}})
        return config_dict

    def parse_lvl3_config(self, component, name):
        """
        receives a number of components in the shape of a dictionary as well as a name for the config

        :param component:
        :type component:
        :param name:
        :type name:
        :return: pandas series using given function. Only use pandas dataframe at top level
        :rtype:
        """
        # put weighting for hierarchical order.
        data_dict = {}
        fusing_df = pd.DataFrame()

        # data acquisition step
        if component.get("components") is None:
            temp_dict = self.get_vars_from_tag(name, component)
            data_dict.update(temp_dict)
            for key in temp_dict.keys():
                fusing_df[key] = temp_dict[key]["data"]
        else:
            for component_name, subcomponent in component["components"].items():
                fusing_df[component_name], misc = self.parse_lvl3_config(subcomponent, component_name)
                data_dict.update(misc)

        # data processing step
        if component.get("function") is not None:
            # put all items through data processing step so that all parameters get transformed by the same metric?
            # needs work regarding feasibility of implementing dynamic big functions with multiple dynamic inputs. idk how?
            pass

        if component.get("mergefunction") is None or component.get("components") is None:
            # default mode
            fused_parameter = fuse_redundant_sensors(fusing_df)
        else:
            # else get specified function
            fused_parameter = component["mergefunction"](fusing_df)

        return fused_parameter, data_dict

    def get_vars_from_tag(self, tag, component) -> dict:
        """
        receives a tag with which it downloads tagged sensors, processes them and returns a dataframe
        :param tag:
        :type tag:
        :param component:
        :type component:
        :return:
        :rtype:
        """
        sampling_rate = 1
        # dataframe to collect component in
        data_dict = {}
        # get variable via stash using the tag to find all parameters that are associated with it.
        paramdict = self.tag_lookup.get(tag)
        if paramdict is None:
            parameters = []
        else:
            parameters = paramdict.keys()

        for parameter in parameters:
            print("downloading: " + parameter)
            series = self.download_series(self.flight_parameters[parameter], convert_to_SI=True)

            # if tag contains a reference value --> collect reference value
            if component.get("reference_value"):
                if self.tag_lookup[tag][parameter].get("reference") is None:
                    raise Exception("Parameter does not contain reference in config excel: " + parameter)
                reference_series = self.download_series(
                    self.flight_parameters[self.tag_lookup[tag][parameter]["reference"]],
                    convert_to_SI=True)
                temp_df = data_dict_to_dataframe(
                    {"series": [series, "series"], "reference": [reference_series, "reference"]}, sampling_rate)
            else:
                temp_df = data_dict_to_dataframe(
                    {"series": [series, "series"]}, sampling_rate)

            data_dict[parameter] = {}
            # check for transformation function
            if component.get("function") is not None and component.get("reference_value") is not None:
                data_dict[parameter]["data"] = component["function"](temp_df["series"], temp_df["reference"])
            elif component.get("function") is not None and component.get("reference_value") is None:
                data_dict[parameter]["data"] = component["function"](temp_df["series"])
            else:
                data_dict[parameter]["data"] = temp_df["series"]
            data_dict[parameter]["tag"] = tag
        return data_dict
