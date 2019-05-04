

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
int_rate = lamdbda x: 0.05


class Underlying(object):
    """
    We currently use prescribed drift and volatility for simplicity of the
    project. Implied volatility tools amongst others will be built at a
    later phase.

    We expect all time entries to be datetime form.
    """

    def __init__(self, ticker, spot_time, spot_price, dividend=0.0):
        self.time = spot_time
        self.price = spot_price
        self.ticker = ticker
        self.drift = None  # get these later
        self.vol = None  # get these later
        self.div = dividend


class Option(object):

    def __init__(self, ticker, expiry_date):
        self.ticker = ticker
        self.expiry = expiry_date

    def _attach_asset(self, strike_price, *underlyings):
        self.strike = strike_price
        self.int_rate = int_rate
        # We will fetch current 3-month Treasury rate from the web
        self.spot_price = []
        self.currency = []
        self._time = []
        self._vol = []
        self._drift = []
        for underlying in underlyings:
            self.spot_price.append(underlying.price)
            self._time.append(underlying.time)
            self._vol.append(underlying.vol)
            self._drift.append(underlying.drift)
        if len(self._time) == 1:
            self.time_to_maturity = self.expiry - self._time[0]
        else:
            raise ValueError("Underlyings have different spot times")

    def _payoff_fct(self, underlying):
        pass


class EurOption(Option):
    """
    we write this subclass just to make the structure clearer.
    AmeOption can be seen as EurOptio when dealing with pricing.
    """

    def __init__(self, ticker, expiry):
        super().__init__(ticker, expiry)

    def _payoff_fct(self, underlying):
        pass

    def gen_pde_coeff(self):
        try:
            end_time = self.time_to_maturity.days / 365  # use start = 0
        except ValueError:
            raise ("Underlying not attached")

        def second_order_coeff(asset, t):
            return (self._vol * asset) ** 2 / 2

        def first_order_coeff(asset, t):
            return (int_rate(t) - div_rate(t)) * asset

        def zero_order_coeff(asset, t):
            return -int_rate(t)
        return end_time, self.__dict__, second_order_coeff, first_order_coeff, \
            zero_order_coeff

    @staticmethod
    def payoff(optype='Call'):
        return lambda asset: max(asset, )


class AmeOption(Option):

    def __init__(self, ticker, expiry):
        super().__init__(ticker, expiry)


# %%
a = EurOption("A", datetime(2011, 1, 1))
b = Underlying("b", datetime(2010, 1, 1), 100)
Option._attach_asset(a, 100, b)
a._load_pde_coeff()
