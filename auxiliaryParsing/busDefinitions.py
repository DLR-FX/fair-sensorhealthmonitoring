## this is the definitive single source of truth for arinc and later can decoding
# the dict recognizes streams by their respective streamid and returns the necessary information for decoding
# labelsInetX["ARINC-429"]["ac000a16"]["212"][1]


labelsInetx = {

    "D000": {
        "streamName": "BCU",
        "busType": "BCU",
        "contents": {"CSDB": {
            "VIR32": {
                "abbreviation": "VN",
                "bus characteristics": "NAV CTL BUS 1A/1B (VHF NAV SYSTEM)",
                "name": "VIR32"
            },
            "DME42": {
                "abbreviation": "DM",
                "bus characteristics": "DME BUS 1a/1b (DME SYSTEM)",
                "name": "DME42"
            },
            None: None  # TODO: decode these values transmitted by bcu at a later point
        },
            "CSDBVars": {
                0x21: [["VORBEAR", "VOR Bearing from A/C to Station", "deg", "Pos"],
                       ["VORFREQ", "VOR Frequency", "MHz", None],
                       ["VORBEARVALID", "VOR Bearing valid", None, None],
                       ["VORFREQVALID", "VOR Frequency valid", None, None]],
                0x22: [["ILSGLDDEV", "ILS Glideslope Deviation", "DDM", "Fly up"],
                       ["ILSLOCDEV", "ILS Localizer Deviation", "DDM", "Fly Right"],
                       ["ILSGLDDEVVALID", "ILS Glideslope valid", None, None],
                       ["ILSLOCDEVVALID", "ILS Localizer valid", None, None],
                       ],
                0x25: [["DISTVALID", "DME Distance valid", None, None],
                       ["DMEDIST", "DME Distance", "nm", None],
                       ["FREQVALID", "DME Frequency valid", None, None],
                       ["DMEFREQ", "DME Frequency", "MHz", None]],
                0x26: [["TIMESTATION", "DME Time to station", "min", None],
                       ["VELOCITY", "DME Velocity", "kn", None],
                       ["TTSVELVALID", "Time to station and velocity valid", None, None]],
                0x27: [["IDENT", "DME Identifier", None, None],
                       ["SRCH/TRCK", "DME Search Track Identifier", None, None]],
                0xf3: [["FAULT", "Fault Code", None, None]]
            }
        }
    },
    "0000d000": {
        "streamName": "BCU",
        "busType": "BCU",
    },
    "ca000000": {
        "streamName": "CAN",
        "busType": "CAN",
    },
    "ca010000": {
        "streamName": "CAN",
        "busType": "CAN",
    },
    "ca020000": {
        "streamName": "CAN",
        "busType": "CAN",
    },
    "ca030000": {
        # TODO: add rest of data from excel sheet
        "streamName": "CAN",
        "busType": "CAN",
        # +++ MSB(Word, Bit), LSB(Word, Bit)|Words:0...3, Bits 7...0 +++
        # multiple parentheses are to iterate through variable names inside a label
        # the nested list-tupel-tupel is stupid but it works. please change at will :)
        # MSB-Most significant Byte|LSB-Least significant Byte
        # label                     variable name  W, b  W, b
        "0a601501": {"variables": [((0, 7, 3, 0), "FD_ACTFORCE", "Elevator Actuator Control Force", "N", "n/a")],
                     },
        "0a60a010": {"variables":
                         [((0, 7, 3, 0), "FD_ELEVATOR", "Elevator position", "deg", "n/a"),
                          ((4, 7, 7, 0), "FD_RUDDER", "Rudder position", "deg", "n/a")],
                     },
        "0a60a020": {"variables":
                         [((0, 7, 3, 0), "FD_AILERON", "Aileron position", "deg", "n/a")],
                     },
        "0a60a030": {"variables":
                         [((4, 7, 7, 0), "FD_FLAP", "Flap position", "deg", "n/a"),
                          ((0, 7, 3, 0), "FD_THS", "Trimmable Horizontal stabilizer", "deg", "n/a")],
                     },
        "0a60a0a0": {"variables":
                         [((0, 6), "FD_GEARDOWN", "gear down locked", "Boolean", "n/a"),
                          ((0, 7), "FD_GEARUP", "gear up locked", "Boolean", "n/a"),
                          ((0, 5), "FD_WOW", "weight on wheels", "Boolean", "n/a")],
                     },
    },
    "ca040000": {
        "streamName": "CAN",
        "busType": "CAN",
    },
    "ac000a16": {
        "streamName": "airdata",
        "busType": "ARINC-429",
        "212": ("BNR", 28, 18, "AD_ALTRATE", "Altitude Rate", "ft/min", 16384, "Up", (0, 20000)),
        "204": ("BNR", 28, 12, "AD_BCALT1", "Baro corrected altitude #1", "ft", 65536, "Pos", (-1000, 53000)),
        "220": ("BNR", 28, 12, "AD_BCALT2", "Baro corrected altitude #2", "ft", 65536, "Pos", (-1000, 53000)),
        "234": ("BCD", 29, 11, "AD_BCORR1", "Baro Correction mb #1", "hPa", 26214.4, "No", (700, 1050)),
        "235": ("BCD", 29, 11, "AD_BCORR1H", "Baro Correction inHg #1", "inHg", 262.144, "No", (20.67, 31)),
        "236": ("BCD", 29, 11, "AD_BCORR2", "Baro Correction mb #2", "hPa", 26214.4, "No", (700, 1050)),
        "237": ("BCD", 29, 11, "AD_BCORR2H", "Baro Correction inHg #2", "inHg", 262.144, "No", (20.67, 31)),
        "206": ("BNR", 28, 15, "AD_CAS", "Computed Airspeed", "kts", 512, "No", (0 / 40, 450)),
        "270": ("DISC", "", "", "AD_DISC1", "Discrete Word #1", "", "", "n/a", None),
        "271": ("DISC", "", "", "AD_DISC2", "Discrete Word #2", "", "", "n/a", None),
        "377": ("DISC", "", "", "AD_EQID", "Equipment Identifier", "", "", "n/a", ("ID 006")),
        "353": ("BNR", 28, 13, "AD_IAS", "Indicated Airspeed", "kts", 2048, "No", (0 / 40, 450)),
        "215": ("BNR", 28, 15, "AD_IMPP", "Impact Pressure", "hPa", 256, "No", (0, 372.5)),
        "207": ("BNR", 28, 17, "AD_MAAS", "Maximum allowable Airspeed", "kts", 512, "No", (150, 450)),
        "205": ("BNR", 28, 13, "AD_MACH", "Mach number", "MACH", 2.048, "No", (0.2, 0.999)),
        "350": ("DISC", "", "", "AD_MAINT1", "Maintenance Word #1", "", "", "n/a", None),
        "351": ("DISC", "", "", "AD_MAINT2", "Maintenance Word #2", "", "", "n/a", None),
        "203": ("BNR", 28, 12, "AD_PALT", "Pressure altitude (1013.25 mbar)", "ft", 65536, "Pos", (-1000, 53000)),
        "213": ("BNR", 28, 18, "AD_SAT", "Static Air Temperature", "°C", 256, "Pos", (-99, 60)),
        "102": ("BNR", 28, 13, "AD_SELALT", "Selected Altitude", "ft", 32768, "Pos", (-55535, 65535)),
        "210": ("BNR", 28, 14, "AD_TAS", "True Airspeed", "kts", 1024, "No", (0 / 100, 599)),
        "211": ("BNR", 28, 18, "AD_TAT", "Total air temperature", "°C", 256, "Pos", (-60, 99)),
        "217": ("BNR", 28, 13, "AD_STATPM", "Static Pressure mb", "hPa", 1083.6448, "No", None),
        "242": ("BNR", 28, 13, "AD_TOTP", "Total Pressure", "hPa", 1024, "No", (135.5, 1354.5)),
    },
    "ac000a17"
    : {
        "streamName": "laserref",
        "busType": "ARINC-429",
        "040": ("BNR", 28, 11, "IR_TRATE", "Turn Rate", "deg/s", 64, "N.R.", None),
        "132": ("BNR", 28, 14, "IRH_THEAD", "Hybrid True Heading", "deg", 90, "CW from N", None),
        "135": ("BNR", 28, 11, "IR_VFOM", "Vertical Figure of Merit", "ft", 16384, "No", None),
        "137": ("BNR", 28, 14, "IRH_TA", "Hybrid Track Angle (True)", "deg", 90, "CW from N", None),
        "175": ("BNR", 28, 14, "IRH_GS", "Hybrid Ground Speed", "kts", 2048, "No", (0 / 100, 599)),
        "254": ("BNR", 28, 9, "IRH_LAT", "Hybrid Latitude Coarse", "deg", 90, "North", None),
        "255": ("BNR", 28, 9, "IRH_LONG", "Hybrid Longitude Coarse", "deg", 90, "East", None),
        "256": ("BNR", 28, 18, "IRH_LATFINE", "Hybrid Latitude Fine", "deg", 8.58307E-05, "No", None),
        "257": ("BNR", 28, 18, "IRH_LONGFINE", "Hybrid Longitude Fine", "deg", 8.58307E-05, "No", None),
        "261": ("BNR", 28, 9, "IRH_ALT", "Hybrid Altitude", "ft", 65536, "Up", (-1000, 53000)),
        "263": ("BNR", 28, 17, "IRH_FPA", "Hybrid Flight Path Angle", "deg", 90, "Up", None),
        "264": ("BNR", 28, 11, "IRH_HFOM", "Hybrid Horizontal Figure of Merit", "nm", 8, "No", None),
        "266": ("BNR", 28, 14, "IRH_VELNS", "Hybrid North-South Velocity", "kts", 2048, "North", (-530, 530)),
        "267": ("BNR", 28, 14, "IRH_VELEW", "Hybrid East-West Velocity", "kts", 2048, "East", (-530, 530)),
        "310": ("BNR", 28, 9, "IR_LAT", "Pos Latitude", "deg", 90, "North", None),
        "311": ("BNR", 28, 9, "IR_LONG", "Pos Longitude", "deg", 90, "East", None),
        "312": ("BNR", 28, 11, "IR_GS", "Ground Speed", "kts", 2048, "No", (1 / 100, 530)),
        "313": ("BNR", 28, 11, "IR_TTA", "True Track Angle", "deg", 90, "CW from N", None),
        "314": ("BNR", 28, 11, "IR_TRUEHEAD", "True Heading", "deg", 90, "CW from N", None),
        "315": ("BNR", 28, 11, "IR_WS", "Wind Speed", "kts", 128, "No", None),
        "316": ("BNR", 28, 11, "IR_WINDDIR", "Wind Direction", "deg", 90, "CW from N", None),
        "317": ("BNR", 28, 11, "IR_MAGTRACK", "Mag. Track Angle", "deg", 90, "CW from N", None),
        "320": ("BNR", 28, 11, "IR_MAGHEAD", "Mag. Heading", "deg", 90, "CW from N", None),
        "321": ("BNR", 28, 11, "IR_DA", "Drift Angle", "deg", 90, "N.R.", None),
        "322": ("BNR", 28, 11, "IR_FPA", "Flight Path Angle", "deg", 90, "N.R.", None),
        "323": ("BNR", 28, 11, "IR_FPACCEL", "Flight Path Acceleration", "g", 2, "Forward", None),
        "324": ("BNR", 28, 11, "IR_PITCH", "Pitch", "deg", 90, "Up", None),
        "325": ("BNR", 28, 11, "IR_ROLL", "Roll", "deg", 90, "R.W.down", None),
        "326": ("BNR", 28, 11, "IRB_PITCHRATE", "Body Pitch Rate", "deg/s", 64, "Up", None),
        "327": ("BNR", 28, 11, "IRB_ROLLRATE", "Body Roll Rate", "deg/s", 64, "R.W.down", None),
        "330": ("BNR", 28, 11, "IRB_YAWRATE", "Body Yaw Rate", "deg/s", 64, "N.R.", None),
        "331": ("BNR", 28, 11, "IRB_LONGACC", "Body Longitudinal Acceleration", "g", 2, "Forward", None),
        "332": ("BNR", 28, 11, "IRB_LATACC", "Body Lateral Acceleration", "g", 2, "Right", None),
        "333": ("BNR", 28, 11, "IRB_NORMACC", "Body Normal Acceleration", "g", 2, "Up", None),
        "334": ("BNR", 28, 11, "IR_HEADING", "Platform Heading", "deg", 90, "Up", None),
        "335": ("BNR", 28, 11, "IR_TARATE", "Track Angle Rate", "deg/s", 16, "CW from N", None),
        "336": ("BNR", 28, 11, "IR_PITCHATTRATE", "Pitch Attitude Rate", "deg/s", 64, "Up", None),
        "337": ("BNR", 28, 11, "IR_ROLLATTRATE", "Roll Attitude Rate", "deg/s", 64, "R.W.down", None),
        "345": ("BNR", 28, 14, "IRH_VERTVEL", "Hybrid Vertical Velocity", "ft/min", 16384, "Up", None),
        "361": ("BNR", 28, 9, "IR_INERTALT", "Inertial Altitude", "ft", 65536, "Up", (-1000, 53000)),
        "362": ("BNR", 28, 11, "IR_ALGTACC", "Along Track Acceleration", "g", 2, "Forward", None),
        "363": ("BNR", 28, 11, "IR_ACSTACC", "Across Track Acceleration", "g", 2, "Right", None),
        "364": ("BNR", 28, 11, "IR_VERTACC", "Vertical Acceleration", "g", 2, "Up", None),
        "365": ("BNR", 28, 11, "IR_IVERTSPD", "Inertial Vertical Speed", "ft/min", 16384, "Up", None),
        "366": ("BNR", 28, 11, "IR_VELNS", "North-South Velocity", "kts", 2048, "North", None),
        "367": ("BNR", 28, 11, "IR_VELEW", "East-West Velocity", "kts", 2048, "East", None),
        "370": ("BNR", 28, 11, "IR_UNBNORMACC", "Unbiased Normal Acceleration", "g", 4, "Up", None),
        "375": ("BNR", 28, 11, "IR_ALGHEADACC", "Along Heading Acceleration", "g", 2, "Forward", None),
        "376": ("BNR", 28, 11, "IR_ACSHEADACC", "Across Heading Acceleration", "g", 2, "Right", None), },
    "ac000a18": {
        "streamName": "Flight Management System",
        "busType": "ARINC-429",
        "001": ("BCD", 29, 11, "FM_DISTTOGO", "Distance To Go", "nm", 26214.4, "Pos", None),
        # "150": ("BNR", 28, 24, "FM_HOUR", "Hour", "hr", 16, "No"),
        "326": ("BNR", 28, 14, "FM_LATSCAFCT", "Lateral Deviation (Scale Factor)", "nm", 64, "Yes", None),
        "147": ("BNR", 28, 17, "FM_MAGNVAR", "Magnetic Variation", "deg", 90, "East", None),
        # "150": ("BNR", 23, 18, "FM_MINUTE", "Minute", "min", 32, "No"),
        # "150": ("BNR", 17, 12, "FM_SECOND", "Second", "sec", 32, "No"),
        "150": ("BNR", 28, 12, "FM_UTC", "UTC", "hh:mm:ss", 65536, "No", None),
        "117": ("BNR", 28, 15, "FM_VERTDEV", "Vertical Deviation", "ft", 8192, "Fly Down", None),
        "327": ("BNR", 28, 14, "FM_VERTSCAFCT", "Vertical Deviation (Scale Factor)", "ft", 1024, "Yes", None),
    },
}
