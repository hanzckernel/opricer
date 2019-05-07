

# In[103]:

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  1 21:15:00 2019

@author: hanzhicheng
"""
"""
some global parameters which later will be separated into another module
"""
"""
The timezone has not been handled!!! Assumed all within the same timezone
and so is the format
"""


import numpy as np
from datetime import datetime
@np.vectorize
def int_rate(x):
    return 0.05


class Underlying(object):
    """
    We currently use prescribed drift and volatility for simplicity of the
    project. Implied volatility tools amongst others will be built at a
    later phase.

    We expect all time entries to be datetime form.
    """

    def __init__(self, spot_time, spot_price, dividend=0.0):
        self.time = spot_time
        self.price = spot_price
        self.drift = None  # get these later
        self.vol = 0.2  # TODO: this part need to be changed
        self.div = dividend


class Option(object):

    def __init__(self, otype, expiry_date):
        self.otype = otype
        self.expiry = expiry_date

    def _attach_asset(self, strike_price, *underlyings):
        self.strike = strike_price
        self.int_rate = int_rate
        self.spot_price = []
        self.currency = []
        self._time = []
        self._vol = []  # TODO: This need to be modified when get data
        self._drift = []
        for underlying in underlyings:
            self.spot_price.append(underlying.price)
            self._time.append(underlying.time)
            self._vol.append(underlying.vol)
            self._drift.append(underlying.drift)
            self.div = underlying.div
        if len(self._time) == 1:
            self.time_to_maturity = self.expiry - self._time[0]
        else:
            raise ValueError('Undelyings have different spot times')

    def payoff(self, price):
        if self.otype == 'call':
            return np.clip(price - self.strike, 0, None)
        elif self.otype == 'put':
            return np.clip(self.strike - price, 0, None)
        elif self.otype == 'barrier':
            raise ValueError('Invalid option type')
        else:
            raise ValueError('Unknown option type')


class EurOption(Option):
    """
    we write this subclass just to make the structure clearer.
    AmeOption can be seen as EurOptio when dealing with pricing.
    """

    def __init__(self, otype, expiry):
        super().__init__(otype, expiry)

    def gen_pde_coeff(self):
        try:
            end_time = self.time_to_maturity.days / 365  # use start = 0
        except ValueError:
            raise ("Underlying not attached")

        @np.vectorize
        def coef2(asset, t):
            return (sum(self._vol) * asset) ** 2 / 2

        @np.vectorize
        def coef1(asset, t):
            return (int_rate(t) - self.div) * asset

        @np.vectorize
        def coef0(asset, t):
            return -int_rate(t)
        return end_time, [coef2, coef1, coef0]


class AmeOption(Option):

    def __init__(self, otype, expiry):
        super().__init__(otype, expiry)


class BarOption(EurOption):  # Barrier options

    def __init__(self, otype, expiry, rebate=0):
        super().__init__(otype, expiry)
        self.rebate = rebate

    def _attach_asset(self, barrier, strike_price, *underlyings):
        """
        barrier expect a list := [lower_bar, higher_bar]. If one of barrier does
        not exist, write 0. e.g., an down option has barrier = [lower_bar, 0]
        """
        try:
            super()._attach_asset(strike_price, *underlyings)
            self.barrier = barrier
        except TypeError as e:
            # TODO: How to overwrite parent exceptions?
            print(f"{e} or Forget to write barrier?")


# # %%
# a = EurOption("A", datetime(2011, 1, 1))
# b = Underlying("b", datetime(2010, 1, 1), 100)
# Option._attach_asset(a, 100, b)
# a.payoff(110)
