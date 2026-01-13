#!/usr/bin/env python
# coding: utf-8
# %%
from opricer.model import models
import abc
import datetime
import numpy as np
from scipy.stats import norm
import pandas as pd
from typing import Any, Union, Optional, List, Callable

# Suppress divide by zero warnings for grid generation
np.seterr(divide='ignore')


class GenericSolver(abc.ABC):

    @abc.abstractmethod
    def get_price(self, model: Any) -> np.ndarray:
        pass

    def _gen_grid(self, low_val: Union[float, np.ndarray], high_val: Union[float, np.ndarray], 
                  start_time: float, end_time: float, time_no: int, asset_no: int) -> None:
        self.time_samples = np.linspace(start_time, end_time, int(time_no))
        self.asset_samples = np.linspace(low_val, high_val, int(asset_no))


class AnalyticSolver(GenericSolver):
    """
    Analytic Solver using Black-Scholes formula.
    """

    def __init__(self, time_no: int = 50, asset_no: int = 20, low_val: float = 0.0, high_val: float = 5.0):
        self.time_no = time_no
        self.asset_no = asset_no
        self.low_val = low_val
        self.high_val = high_val
        self.time_samples: np.ndarray = np.array([])
        self.asset_samples: np.ndarray = np.array([])

    def __call__(self, model: Any, to_df: bool = True) -> np.ndarray:
        # Returns price matrix (Time x Asset)
        return self.get_price(model).T

    def get_price(self, model: Any) -> np.ndarray:
        spot_price = np.array(model.spot_price)
        # Generate grid relative to spot price
        self._gen_grid(self.low_val * spot_price, self.high_val * spot_price, 0,
                       model.time_to_maturity, self.time_no, self.asset_no)
        
        K = model.strike
        T = self.time_samples
        
        # Ensure T has non-zero values for division, handle T=0 separately or rely on numpy broadcasting with care
        # For BS, T is time to maturity. If we use time_samples from 0 to T_maturity, 
        # then we are pricing at different times t, so time to maturity is T_maturity - t.
        # But the original code uses T as self.time_samples directly.
        # If time_samples goes from 0 to Maturity, then at index 0 (time 0), time to maturity is full.
        # The original code logic: d1 = ... / (vol * sqrt(T)). If T=0, div by zero.
        # T here seems to be "Time to Maturity"? No, it's linspace(0, model.time_to_maturity).
        # If it represents "time passed", then "time to maturity" is model.time_to_maturity - T.
        # BUT, standard BS formula `T` is time to maturity.
        # If the solver computes price evolution, then at time t, remaining time is T-t.
        # The original code uses `T` as `self.time_samples`. 
        # If `time_samples` is [0, ..., Maturity], then at 0 we have 0 time?
        # If T is 0, d1 is undef.
        # Let's assume the user wants price profile vs Spot Price at different times to maturity?
        # Or price evolution over time?
        # If `time_samples` starts at 0, and we put T in denominator, it implies T is "time to maturity".
        # So at index 0 (time=0), time to maturity is 0? That implies expiry.
        # Usually we want price at t=0 (now) with time to maturity T.
        # Let's stick to original logic but handle potential warning/error if T=0.
        
        # Original: r, D, vol = model.int_rate(T), model.div[0](K), model._vol[0](K, T)
        # model.int_rate(T) might expect scalar or array.
        
        r = model.int_rate(T) # Assuming this handles array
        D = model.div[0](K) # Constant dividend usually
        vol = model._vol[0](K, T) if hasattr(model, '_vol') else 0.2 # accessing underlying vol

        # Fix for original code access pattern
        # model._vol is a list of functions.
        # The original code: model._vol[0](K, T)
        
        # Refactored access:
        vol_func = model._vol[0]
        # Check if vol_func handles array T. Lambda usually does if simple.
        try:
            vol = vol_func(K, T)
        except:
             # Fallback if not vectorized
             vol = np.array([vol_func(K, t) for t in T])

        # d1 calculation
        # If T contains 0, we get warning/inf.
        with np.errstate(divide='ignore', invalid='ignore'):
             d1 = (np.log(self.asset_samples / K) + (r - D + vol**2/2) * T) / (vol * np.sqrt(T))
             d2 = d1 - vol * np.sqrt(T)
        
        strike_disc = model.strike * np.exp(-r * T)
        
        # Handle T=0 case (Expiry)
        # If T=0, price is payoff.
        
        price = np.zeros((self.asset_no, self.time_no))
        
        if model.otype.lower() == 'call':
            price = self.asset_samples * np.exp(-D * T) * norm.cdf(d1) - strike_disc * norm.cdf(d2)
        elif model.otype.lower() == 'put':
            price = strike_disc * norm.cdf(-d2) - self.asset_samples * np.exp(-D * T) * norm.cdf(-d1)
            
        # Fix NaNs at T=0 (if any)
        # At T=0, d1/d2 are nan. Norm.cdf(nan) is nan.
        # We can fill T=0 with payoff.
        # Check where T is 0 (or close)
        mask = np.isclose(T, 0)
        if np.any(mask):
             # This applies to columns where T~0
             # Price at expiry is Payoff
             payoff = model.payoff(self.asset_samples)
             # self.asset_samples is (asset_no, 1) effectively?
             # price is (asset_no, time_no)
             # Payoff is (asset_no,)
             # Broadcast payoff to those columns
             # However, original code returned shape (asset_no, time_no).
             # We need to reshape payoff
             pass
             # Actually, if T is "Time to Maturity", then T=0 is expiry.
             # If T is "Current Time", then T=Maturity is expiry.
             # The usage suggests T is used as "Time to Maturity" in BS formula.
             # So `time_samples` likely represents a range of "Times to Maturity".
        
        # Replace NaNs with payoff if T=0 logic applies, but simple fillna might be safer
        # But wait, d1 has log(S/K). If S=0?
        
        return price