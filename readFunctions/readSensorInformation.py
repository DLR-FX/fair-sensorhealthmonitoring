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