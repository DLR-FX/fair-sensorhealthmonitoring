import pandas as pd
import numpy as np


def normalize_unit(vector_in, unit_in):
    """
    todo: write tests

    receive unit and input
    return SI unit name and vector of unit.

    Works with lookup table
    :return:
    :rtype:
    """

    unit_correlation = {
        "rad ": {"unit": "deg", "equation": lambda radian: radian * 360 / (2 * np.pi)},
        "rad/s": {"unit": "deg/s", "equation": lambda radian: radian * 360 / (2 * np.pi)},
        "rad/s^2": {"unit": "deg/s^2", "equation": lambda radian: radian * 360 / (2 * np.pi)},
        "K": {"unit": "K", "equation": lambda K: K},
        "C": {"unit": "K", "equation": lambda C: C - 273.15},
        "F": {"unit": "K", "equation": lambda F: (F - 32) * 5 / 9 + 273.15},
        "t": {"unit": "kg", "equation": lambda t: t * 1000},
        "lb": {"unit": "kg", "equation": lambda lb: lb * 0.453592},
        "m": {"unit": "m", "equation": lambda m: m},
        "ft": {"unit": "m", "equation": lambda ft: ft * 0.3048},
        "km": {"unit": "m", "equation": lambda km: km * 1000},
        "NM": {"unit": "m", "equation": lambda NM: NM * 1852},
        "mm": {"unit": "m", "equation": lambda mm: mm / 1000},
        "m/s": {"unit": "m/s", "equation": lambda ms: ms},
        "kts": {"unit": "m/s", "equation": lambda kts: kts / 1.94384},
        "ft/min": {"unit": "m/s", "equation": lambda ftmin: ftmin / 196.85},
        "km/h": {"unit": "m/s", "equation": lambda kmh: kmh / 3.6},
        "m/s^2": {"unit": "m/s^2", "equation": lambda mss: mss},
        "g": {"unit": "m/s^2", "equation": lambda g: g * 9.80665},
        "Pa": {"unit": "Pa", "equation": lambda Pa: Pa},
        "hPa": {"unit": "Pa", "equation": lambda hPa: hPa * 100},
        "lb/ft^2": {"unit": "Pa", "equation": lambda lbft2: lbft2 * 47.8803},
        "mB": {"unit": "Pa", "equation": lambda mB: mB * 100},
        "psi": {"unit": "Pa", "equation": lambda psi: psi * 6894.76},
        "inHg": {"unit": "Pa", "equation": lambda inHg: inHg * 3386.39},
        "bar": {"unit": "Pa", "equation": lambda bar: 100_000 * bar},
    }

    output_value = unit_correlation[unit_in]
    func_unit_tf = np.vectorize(output_value["equation"])
    unit_out = output_value["unit"]
    vector_out = func_unit_tf(vector_in)
    return vector_out, unit_out


def ellipsoid_to_orthometric(ellipsoid_alt):
    """
    TODO: receive an ellipsoid altitude and return the orthometric altitude based on WGS84 geoid


    :param ellipsoid_alt:
    :type ellipsoid_alt:
    :return:
    :rtype:
    """

    return ellipsoid_alt[0]


def merge_altitudes(df):
    """
    perhaps low highpassfilter altitudes here
    :param df:
    :type df:
    :return:
    :rtype:
    """
    return df.mean(axis=1)


def gnss_speed(df):
    """
    TODO: calculate gnss speed based on north south and east west velocity

    :param ns_speed:
    :type ns_speed:
    :param ew_velocity:
    :type ew_velocity:
    :return:
    :rtype:
    """
    print("calculating gnss velocity")
    # TODO: calculate pythagorean root lol

    return df.mean(axis=1)


def baro_to_gnss(baro_alt):
    """
    TODO: implement series that receives baro series and transforms it to a valid gnss altitude

    :param baro_alt:
    :type baro_alt:
    :return:
    :rtype:
    """
    return baro_alt.mean(axis=1)


def altitude_from_pressure(p, p_0):
    """
    expects input units to be Pascal

    receive two pandas series.
    p for static pressure
    p_0 for reference.

    :param p:
    :type p:
    :param p_0:
    :type p_0:
    :return:
    :rtype:
    """
    # ranges for geopotential altitude referencing MSL. units are all normed to SI-standard m, s, K, Pa
    # NOTE: min and max purely references the geodetic position and not the inherent value
    isa_ranges = {"-2-11": {"p_min": 1.27774e5,
                            "p_max": 2.2632e4,
                            "T_min": 301.15,
                            "T_max": 216.65,
                            "a": -6.5e-3,
                            "h_0": -2e3},
                  "11-20": {"p_min": 2.2632e4,
                            "p_max": 5.47487e3,
                            "T_min": 216.65,
                            "T_max": 216.65,
                            "a": 0,
                            "h_0": 11e3},
                  "20-32": {"p_min": 5.47487e3,
                            "p_max": 8.68014e2,
                            "T_min": 216.65,
                            "T_max": 228.65,
                            "a": 1e-3,
                            "h_0": 20e3},
                  "32-47": {"p_min": 8.68014e2,
                            "p_max": 1.10906e2,
                            "T_min": 228.65,
                            "T_max": 270.65,
                            "a": 2.8e-3,
                            "h_0": 32e3},
                  "47-51": {"p_min": 1.10906e2,
                            "p_max": 6.69384e+1,
                            "T_min": 270.65,
                            "T_max": 270.65,
                            "a": 0,
                            "h_0": 47e3},
                  "51-71": {"p_min": 6.69384e+1,
                            "p_max": 3.95639e0,
                            "T_min": 270.65,
                            "T_max": 214.65,
                            "a": -2.83e-3,
                            "h_0": 51e3},
                  "71-80": {"p_min": 3.95639e0,
                            "p_max": 8.86272e-1,
                            "T_min": 214.65,
                            "T_max": 196.65,
                            "a": -2e-3,
                            "h_0": 71e3},
                  }

    # using standard library ambiance with standard pressure of 1013.25hPa
    # correcting pressure to correctly display according to reference pressure
    p_STD = 1013_25
    p_adjusted = p / p_0 * p_STD
    # loop through pressure values
    baro_func = np.vectorize(alt_from_p)
    altitude_above_msl = baro_func(p_adjusted, isa_ranges)
    if type(p_0) == pd.Series:
        altitude_above_msl = pd.Series(index=p_0.index, data=altitude_above_msl)
    return altitude_above_msl


def alt_from_p(pressure, isa_ranges):
    h = np.nan
    g = 9.80665
    R = 287.05287
    for key, i in isa_ranges.items():
        # find range
        if i["p_max"] < pressure <= i["p_min"]:
            if i["a"] == 0:
                h = np.log(pressure / i["p_min"]) * R * i["T_min"] / -g + i["h_0"]
            elif i["a"] != 0:
                h = ((pressure / i["p_min"]) ** (-i["a"] * R / g) - 1) * i["T_min"] / i["a"] + i["h_0"]
            else:
                raise Exception("Invalid isa a i within altitude from pressure")
    if h is np.nan:
        # warnings.warn("No valid pressure found for pressure: " + str(pressure))
        pass
    return h


def fuse_redundant_sensors(df):
    """
    receives dataframe containing redundant sensor values and merges them into just one value
    possible implementations are:
    -averaging
    -voting
    -kalman?
    -use method to predict value with covariance(noise) and check if measured value falls into expected range


    returns series with fused signal
    :param dataframe:
    :type dataframe:
    :return:
    :rtype:
    """
    if len(df.columns) < 3:
        results = df.mean(axis=1)
    else:
        # use smarter algorithm
        ##voting
        results = df.mean(axis=1)
        pass

    return results


def vote_timestep(value_list):
    # calculate value that exclues values if they are too far off from the expected values.
    pass


def short_time_statistics(series, nperseg=256):
    """
    receive series. slice into windows of default nperseg=256 values. in a similar manner as stft transform

    calculate standard deviation, mean and variance for given windows

    this will be used to detect signals that are larger than the mean value + 3x standard deviation

    perhaps also use mean to smoothe function (see: moving averages/lowpass subtraction)

    use pandas dataframe.rolling(

    :param series:
    :type series:
    :return:
    :rtype:
    """
    df = pd.DataFrame(series)
    df["mean"] = df[series.name].rolling(nperseg, center=True).mean()
    df["stdev"] = df[series.name].rolling(nperseg, center=True).std()

    sus_func = np.vectorize(detect_suspicious_behaviour)
    df["sus"] = sus_func(df[series.name], df["mean"], df["stdev"])
    report = df.loc[df['sus'] == True]
    return report


def detect_suspicious_behaviour(value, mean, stdev, factor=6) -> float:
    """
    detect values that are above "factor" times standard deviation

    1:detection
    0:no detection

    :param value:
    :type value:
    :param mean:
    :type mean:
    :param stdev:
    :type stdev:
    :return:
    :rtype:
    """
    # check if value is outside standard deviation and if it is also not None
    if pd.notna(value) and value > (mean + factor * stdev) or value < (mean - factor * stdev) and stdev / mean > 0.01:
        # define signal to noise ratio limit. E.g. snr = stdev/mean >! 0.01
        # add to issues list if signal t
        out_value = (value - mean) / stdev
    elif pd.isna(value):  # check if value is "not a number"
        out_value = 1.0
    else:
        out_value = 0
    return float(out_value)


def compare_reference_to_signal(reference, signal):
    """
    calculate difference. When difference is larger than standard dev+mean from ref_signal --> bad

    nperseg=number of values per segment
    :param signal:
    :type signal: pd.Series
    :param ref_signal:
    :type ref_signal: pd.Series
    :return:
    :rtype:
    """
    # determine signal offset
    offset = reference.mean() - signal.mean()
    # normalize signal to reference
    signal = signal + offset

    # calculate stdev for rolling window
    mean = reference.rolling(256, center=True).mean()
    reference_highpassed = reference - mean
    stdev = reference_highpassed.std()

    factor = 1
    sus_func = np.vectorize(detect_suspicious_behaviour)
    # check if signal is within standard deviation of reference signal
    sus = pd.Series(index=reference.index, data=sus_func(signal, reference, stdev, factor=factor))
    report = {"suspicious values": sus.loc[sus != 0],
              "offset": str(offset),
              "checking_range": str(stdev * factor)}
    # return issue list and offset
    # define percentile of standard deviation for signal
    return report


def main():
    a = altitude_from_pressure(50_000, 100_000)


if __name__ == "__main__":
    main()
