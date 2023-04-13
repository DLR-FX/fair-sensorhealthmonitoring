correlation = {"altitude": {"barometric": {"pressure altitude": ["ASCB_ADS_Ads1ADA_airData50msec_pressureAltitude_o"],
                                           "altitude": ["ASCB_ADS_Ads1ADA_airData50msec_baroAltitude1_o",
                                                        "ASCB_GGF_Ggf1GGA_pfdData_baroAltitude_o"],
                                           "static pressure": {"NOSE_StaticPressure": {
                                               "ASCB_ADS_Ads1ADA_airData50msec_mbBaroCorrection1_o"},
                                                               "ASCB_ADS_Ads1ADA_airData50msec_staticPressure": {
                                                                   "ASCB_ADS_Ads1ADA_airData50msec_mbBaroCorrection1_o"}
                                                               }
                                           },
                            "gnss": {"ellipsoid": ["ASCB_GPS_Gps1aGps429_gps50msec429_gpsHeight",
                                                   "IMAR_INS_Altitude"],
                                     "orthometric": ["IMAR_GNSS_Altitude",
                                                     "ASCB_GPS_Gps1aGps429_gps50msec429_altitude_o",
                                                     "ASCB_IRS_Irs1aIrs429_irs12msec429_inertialAltitude_o"]
                                     }
                            }
               }

"""
# difficult to dynamically point out relationships.
physical = {"altitude":{"gnss":{"ellipsoid":"+geoid",
                                "orthometric":"=",
                                "static pressure":"barometric equation",
                                "barometric":{"baro1":["static pressure", "reference pressure"]
    }}}
            
"""
