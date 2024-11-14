""" Utility functions. """

__author__ = "janez presern, anja pavlin, andraz marinc"

import numpy as np
import scipy.signal as sg
import uncertainties.unumpy as unp


def sigmoid(x, x0, k, top=1, bottom=0):

    y = bottom / (top + np.exp(-k * (x - x0)))

    return y


def boltzman(x, x0, k, top=1, bottom=0):

    y = bottom + ((top - bottom) / (1 + np.exp((x0 - x)/k)))

    return y


def decay_exp(x, k, top=1, bottom=0):

    y = (top - bottom) * np.exp(-x/k) + bottom

    return y


def rise_exp(x, k, top=1, bottom=0):

    y = (top - bottom) * (1 - np.exp(-x/k)) + bottom

    return y


def rise_exp2(x, k, top=1, offset=0):

    y = top * (1 - np.exp(-x/k)) + offset

    return y


def unp_rise_exp2(x, k, top, bottom):

    return top * (1 - unp.exp(-x/k)) + bottom


def decay_exp2(x, k, top, bottom):

    return top * np.exp(-k * x) + bottom


def unp_decay_exp2(x, k, top, offset):

    return top * unp.exp(-k * x) + offset


def linear (x, k, intercept):

    return k * x + intercept


def r_square(x_fact, y_fact, p_popt, func):

    """
    Calculates R^2
    :param x_fact: actual x
    :param y_fact: actual y
    :param p_popt: fitted parameters
    :return r_squared:
    """

    if func == rise_exp2:

        residuals = y_fact - rise_exp2(x_fact, p_popt[0], p_popt[1], p_popt[2])

    elif func == decay_exp2:

        residuals = y_fact - decay_exp2(x_fact, p_popt[0], p_popt[1], p_popt[2])

    elif func == linear:

        residuals = y_fact - linear(x_fact, p_popt[0], p_popt[1])

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_fact - np.mean(y_fact)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    return r_squared


