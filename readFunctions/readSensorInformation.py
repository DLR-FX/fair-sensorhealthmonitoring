import io
import os

import pandas as pd
import subprocess
import xmltodict
import auxiliaryParsing.readConfigXml as read_config_xml
import re
import warnings

correlation_types = {
    "3": "int",  # "status_1_int",  #:['1', '17', '3', '5', '2', '64', '4', '8']
    "5": "float",  # "float",
    "19": "int",  # "status_2_int",  #: ['16384', '0', '4278190080', '1', '20480']
    "20": "int",  # "status_3_bit",  #: ['1', '513']
    "30": "str"  # "str"
}
correlation_prop_id = {
    "1001": "ename",
    "1004": "edescription",
    "1013": "eunit",
    "1055": "esampling",
    "1058": "eserial number",
    "1064": "erelative path",
    "1080": "eabsolute path",
}


class ReadSensorInformation():
    def __init__(self):
        self.limits = {"IR_FPACCEL": {
            "extras": {
                "noise": True
            },
            "limits": {
                "max": 10000000,
                "min": -10
            }
        }
        }

    def fillDataDict(self):
        pass


def read_imcexp(path):
    ## read imcexp and extract all parameter names that are used and displayed
    # use command line tool and 7zip to read imcexp file to standard command line output which gets read into this script right here
    cmd = [r"C:\Program Files\7-Zip\7z", "x", path, "-so", "imc.Studio.PlugIns.DevSetup.imcDevices2x.XML", "-r"]
    sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    xml_file = sp.stdout.readlines()[-1].decode("utf-8")
    xml_dict = xmltodict.parse(xml_file)
    # unpack @Data tags
    for element in xml_dict["imcDev2xDocument"]["DataPoolSetupInfo"]:
        element.update(xmltodict.parse(element["@Data"]))

    imcexp = sort_imcexp_data(xml_dict)
    return imcexp


def imcexp_output_paths(imcexp, desired_prop_id="1064"):
    """
    :param imcexp:
    :type imcexp:
    :param prop_id:
    1001: Parameter name
    1004: parameter description
    1013: unit
    1055: sampling rate
    1058: Serial number
    1064: relative path
    1080: absolute path

    7:exFormat

    Datatypes:
    3: statusbits?:['1', '17', '3', '5', '2', '64', '4', '8']
    5: floats
    19: status ints?: ['16384', '0', '4278190080', '1', '20480']
    20: statusbits?: ['1', '513']
    30:str

    :type prop_id: str
    :return:
    :rtype:
    """
    # list values for prop id 1064 for output paths
    output_paths = []
    for element in imcexp["imcDev2xDocument"]["DataPoolSetupInfo"]:
        for parameter in element["TreeItemTable"]["TI"]:
            properties = parameter["PC"].get("Prop")
            if properties is not None:
                for prop in properties:
                    prop_id = prop.get("@ID")
                    if prop_id == desired_prop_id:
                        output_paths.append(prop.get("@Val"))

    return output_paths


def type_cast_prop(input, type):
    if "float" == correlation_types[type]:
        return float(input)
    elif "int" == correlation_types[type]:
        return int(input)
    elif "str" == correlation_types[type]:
        return str(input)
    else:
        print("type_cast_prop(): invalid input")


def assign_prop_id_values(imcexp):
    corr_dict = correlation_prop_id
    # use correlation_prop_id that is defined at the beginning of the script to correlate prop_ids to actual values
    config_out = {key: {corr_dict.get(subkey): subvalue
                        for subkey, subvalue in value.items()
                        if corr_dict.get(subkey) is not None}
                  for key, value in imcexp.items()}
    return config_out


def sort_imcexp_data(xml_dict):
    """
    please clean up!
    converts convoluted imcexp-dict into hopefully clean dictionary with correlated property_ids
    :param xml_dict:
    :type xml_dict:
    :return:
    :rtype:
    """
    imcexp_1 = []
    # append treeitemtables
    for tree_item_table in xml_dict["imcDev2xDocument"]["DataPoolSetupInfo"]:
        imcexp_1.extend(tree_item_table["TreeItemTable"]["TI"])

    # unzip elements up to PC prop
    imcexp_2 = [element["PC"].get("Prop") for element in imcexp_1]
    # remove unneccesary elements
    imcexp_3 = [{property["@ID"]: type_cast_prop(property["@Val"], property["@Type"]) for property in element if
                 property.get("@ID") is not None}
                for element in imcexp_2 if element is not None]

    # remove elements that dont have a name in their properties and reshape into dictionary
    imcexp_4 = {element["1001"]: element for element in imcexp_3 if element["1001"] is not None}

    # only allow entries with more than 40 property values
    imcexp_5 = {key: value for key, value in imcexp_4.items() if len(value) >= 40}  # actual parameters
    imcexp_5_2 = {key: value for key, value in imcexp_4.items() if len(value) < 40}  # status values

    debug = False
    if debug:
        # if ID 1001 exists for name. eventually compare lists containing
        rel_paths = imcexp_output_paths(xml_dict, desired_prop_id="1064")
        abs_paths = imcexp_output_paths(xml_dict, desired_prop_id="1080")
        names = imcexp_output_paths(xml_dict, desired_prop_id="1001")
        description = imcexp_output_paths(xml_dict, desired_prop_id="1004")
        description_filled = [desc for desc in description if len(desc) > 0]
        path_diff = list(set(rel_paths) - set([os.path.basename(path) for path in abs_paths]))
    return imcexp_5


def config_from_istar_flight(flight_name: str) -> dict:
    """
    receives flight_name in regular or abbreviated form.
    Finds matching flight directory in fx-backup
    gets config from imcexp

    :param flight_name:
    :return: configuration for istar
    :rtype:
    """
    path = r"\\fx-backup.intra.dlr.de\FlightTestData\D-BDLR\Daten"
    # find subfolder by flight_name string. open folders 2021, 2022
    flights = [[os.path.join(path, year_dir, flight_dir),
                re.sub(r'\d{8}_', '', os.path.basename(flight_dir))]  # add abbreviated version to second list item
               for year_dir in os.listdir(path)
               for flight_dir in os.listdir(os.path.join(path, year_dir))]
    # find flight_name in flight paths and return matching path
    path_flights = [flight[0] for flight in flights
                    if flight[1] in flight_name or flight_name in flight[0]]
    if len(path_flights) > 1:
        warnings.warn(str("in config_from_istar_flight():\tMore than 1 flights found for flight_name: " + flight_name))

    # find imcexp file
    path_imcexp = [os.path.join(path_flights[0], file) for file in os.listdir(path_flights[0]) if
                   file.endswith(".imcexp")]
    if len(path_imcexp) > 1:
        warnings.warn(
            str("in config_from_istar_flight():\tMore than 1 imcexp files found for flight_path: " + path_flights[0]))
    config = read_istar_config(path_imcexp[0])
    return config


def read_istar_config(file='../testing/conmo_20220530.imcexp'):
    # parameter convention von stephan graeber: 1 links, 2 rechts
    imcexp = read_imcexp(path=file)

    # parameter = "ASCB_ADS_Ads1ADA_airData50msec_mbBaroCorrection1_o"
    # parameter = "NOSE_FFT1"
    # exported_xml = read_config_xml.get_user_tags(parameter, r"C:\Users\klei_cl\Desktop\Geräteconfig_klein.de.xml")
    # comparison_value = imcexp[parameter]

    """    # debug and check for unique values
    from itertools import chain
    a = [[property["value"] for property in element.values() if property["type"] == "30" ] for element in
         imcexp.values()]
    b = list(dict.fromkeys(chain.from_iterable(a)))
    """
    # output_paths = imcexp_output_paths(imcexp)
    # get excel file from teamsite
    # excel_file = get_excel_from_teamsite_to_config()

    excel_file = "readFunctions/AllParameters_ASCBD_V2.xlsx"
    # define sheets and columns containing the parameter name
    sheet_and_indices = [["Act Parameter ASCB", "Parameter_Name"],
                         ["Parameter Analog", "Parameter_Name"],
                         ["Parameter IMAR", "Parameternumber"],
                         ["Parameter NOSEBOOM", "Parameter_Name"]]
    sensors_istar = {}
    for sheet_and_index in sheet_and_indices:
        df = pd.read_excel(excel_file, sheet_name=sheet_and_index[0], index_col=sheet_and_index[1], header=0)
        # generate dictionary with keys that possess keys named attribute names containing the cells
        # use dropna to remove nan values
        sensors_istar.update({parameter: df.loc[parameter].dropna().to_dict() for parameter in list(df.index)})

    # assign prop_id values and sensors_istar
    config = assign_prop_id_values(imcexp)
    # TODO: implement abstract sensor classes
    # TODO: merge sensibly so imcexp has priority and is always right.
    #  unit, sampling rate, description not needed when imcexp already contains them.
    filter_list = ["Unit", "Description", "Frequency\n[Hz]", "Sampling Interval"]
    for sensor_name, sensor_value in config.items():
        excel_value = sensors_istar.get(sensor_name)
        if excel_value is not None:
            config.get(sensor_name).update(excel_value)

    return config


def get_excel_from_teamsite_to_config():
    # import all the libraries
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.client_context import ClientContext
    from office365.sharepoint.files.file import File
    import io
    import pandas as pd
    import json

    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.runtime.client_request import ClientRequest
    from office365.runtime.http.request_options import RequestOptions

    # target url taken from sharepoint and credentials
    url = "https://teamsites.dlr.de/ft/ISTAR-FTI/Parameterlisten/AllParameters_ASCBD_V2.xlsx"
    url = "https://teamsites.dlr.de/ft/ISTAR-FTI/Parameterlisten/AllParameters_ASCBD_V2.xlsx?d=waa66ce7fc63840508a53598fd0451639"

    tenant_url = "https://teamsites.dlr.de"
    ctx_auth = AuthenticationContext(tenant_url)

    site_url = "https://teamsites.dlr.de/ft/ISTAR-FTI"

    if ctx_auth.acquire_token_for_user(username, password):
        request = ClientRequest(ctx_auth)
        options = RequestOptions("{0}/_api/web/".format(site_url))
        options.set_header('Accept', 'application/json')
        options.set_header('Content-Type', 'application/json')
        data = request.execute_request_direct(options)
        s = json.loads(data.content)
        web_title = s['Title']
        print("Web title: " + web_title)
    else:
        print(ctx_auth.get_last_error())

    # save data to BytesIO stream
    bytes_file_obj = io.BytesIO()
    bytes_file_obj.write(response.content)
    bytes_file_obj.seek(0)  # set file object to start

    # read excel file and each sheet into pandas dataframe
    df = pd.read_excel(bytes_file_obj, sheetname=None)
    # read file into pandas dataframe

    return bytes_file_obj


def check_propid_assignment(file='../testing/conmo_20220530.imcexp'):
    # compare values
    prop_id_assignment = {
        "1001": 'eChannelName',
        "1004": 'eChannelComment',
        "1013": 'eUserUnit',
        "1031": 'eCurveYAxisMin',
        "1032": 'eCurveYAxisMax',
        "1055": 'eSampleTime',
        "1058": 'eDeviceSN',
        "1064": 'ePCFileName',
    }
    error_list = []
    missing_values = []
    imcexp = read_imcexp(path=file)
    for parameter in imcexp:
        xml = read_config_xml.get_user_tags(parameter, r"C:\Users\klei_cl\Desktop\Geräteconfig_klein.de.xml")
        if xml is None:
            missing_values.append(parameter)
            continue
        imc_value = imcexp[parameter]
        # check prop_id values
        for prop_id, xml_key in prop_id_assignment.items():
            value = imc_value[prop_id]
            # get xml element and check if it exists
            xml_element = xml.get(xml_key)
            if xml_element is not None:
                xml_value = xml_element["value"]
            else:
                xml_value = None
            # special case for our boi sampling rate
            if xml_key == "eSampleTime":
                value = str(int(float(value) * 1000)) + " ms"
                if value == "1000 ms":
                    value = "1 s"

            if value == "":
                value = None

            if value != xml_value:
                if xml_key in ["eSampleTime", "eUserUnit", "eChannelComment", "ePCFileName"]:
                    if xml_key == "ePCFileName" and os.path.splitext(xml_value)[0] == os.path.splitext(value)[0]:
                        continue
                    error_string = parameter + ":\tError  XML: " + str(xml_value) + "\t\tprop_value: " + str(value)
                    print(error_string)
                    error_list.append(error_string)
                elif float(value) != float(xml_value):
                    error_string = parameter + ":\tError  XML: " + str(xml_value) + "\t\tprop_value: " + str(value)
                    print(error_string)
                    error_list.append(error_string)

    print("finished")


if __name__ == "__main__":
    check_propid_assignment()
    # read_istar_config()
