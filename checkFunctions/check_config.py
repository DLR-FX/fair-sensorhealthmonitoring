from Parsing.parseFunctions import get_mean_noise

# check definitions here
level2_checks = {"physical": {"error_tag": "physical values out of limits",
                              "min": "physical range min",
                              "max": "physical range max",
                              },
                 "amplitude": {"error_tag": "amplitude out of limits",
                               "min": "amplitude min",
                               "max": "amplitude max",
                               "function": get_mean_noise}}
