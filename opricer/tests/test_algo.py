#!/usr/bin/env python
# coding: utf-8
# %%
from opricer.data import models
from opricer.algo import pde
import datetime
import numpy as np
from scipy.stats import norm


class AnalyticSolver(pde.EurSolver):

    def __call__(self, model):
        return self.get_price(model)

    def get_price(self, model):
        spot_price = np.array(model.spot_price)
        self.low_val *= spot_price
        self.high_val *= spot_price
        self._gen_grid(self.low_val, self.high_val, 0,
                       model.time_to_maturity, self.time_no, self.asset_no)
        K, T = model.strike, model.time_to_maturity
        r, D, vol = model.int_rate(0), model.div(0), model._vol[0](0, 0)
        moneyness = np.log(self.asset_samples / K)
        d1 = (moneyness + (r-D + vol**2/2)*T)/(vol * np.sqrt(T))
        d2 = d1 - vol * np.sqrt(T)
        strike_disc = model.strike * np.exp(-r*T)
        if model.otype.lower() == 'call':
            return self.asset_samples * np.exp(-D*T) * norm.cdf(d1) - strike_disc * norm.cdf(d2)
        if model.otype.lower() == 'put':
            return strike_disc * norm.cdf(-d2) - self.asset_samples * np.exp(-D*T) * norm.cdf(-d1)


arr = np.linspace(1, 10, 10)
arr

# %%
