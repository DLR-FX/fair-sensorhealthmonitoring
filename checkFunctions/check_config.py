from Parsing.parseFunctions import get_mean_noise
from checkFunctions.level3 import altitude_from_pressure, baro_to_gnss, ellipsoid_to_orthometric, gnss_speed, \
    merge_altitudes

# check definitions here
check_config = {
    "level 2": {"physical": {"error_tag": "physical values out of limits",
                             "min": "physical range min",
                             "max": "physical range max",
                             },
                "amplitude": {"error_tag": "amplitude out of limits",
                              "min": "amplitude min",
                              "max": "amplitude max",
                              "function": get_mean_noise}},
    "level 3": {
        "components": {
            "altitude": {
                "function_merge": merge_altitudes,  # placeholder for Sensor fusion magic here
                "function": None,
                "components": {
                    "barometric": {
                        "components": {
                            "static pressure": {"function": altitude_from_pressure,
                                                "reference_value": True},
                            "barometric altitude": {"reference_value": True}},
                    },
                    "gnss": {
                        "components": {
                            # "orthometric altitude": {},
                            # "ellipsoid altitude": {"function": ellipsoid_to_orthometric}
                        },
                    },
                },
            },
            "velocity": {
                "components": {
                    "geodetic": {
                        "function": gnss_speed,
                        "components": {
                            "north-south velocity": {},
                            "east-west velocity": {}},
                    }
                }
            },
        },

        "mergefunction": lambda x: x,  # return df. works only at top level

    }

}
