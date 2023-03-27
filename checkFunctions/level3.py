from sympy import *
from scipy.optimize import fsolve
from scipy.constants import g, R
import pandas as pd
import numpy as np
from ambiance import Atmosphere


def altitude_from_pressure(p, p_0):
    # using standard library ambiance with standard pressure of 1013.25hPa
    # correcting pressure to correctly display according to reference pressure
    p_STD = 1013_25
    p_adjusted = p/p_0*p_STD
    altitude_above_msl = Atmosphere.from_pressure(p_adjusted).h
    return altitude_above_msl


def main():
    a = altitude_from_pressure(50_000, 100_000)


if __name__ == "__main__":
    main()
