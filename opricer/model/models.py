# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  1 21:15:00 2019

@author: hanzhicheng
"""

import abc
import numpy as np
from datetime import datetime, timezone
from typing import List, Callable, Union, Optional, Any, Tuple

def int_rate(t: float) -> float: 
    return 0.05

class World(abc.ABC):
    pass

class Underlying:
    """
    We currently use prescribed drift and volatility for simplicity of the
    project. Implied volatility tools amongst others will be built at a
    later phase.

    We expect all time entries to be datetime form in UTC.
    """

    def __init__(self, spot_time: datetime, spot_price: float, dividend: float = 0.1):
        if spot_time.tzinfo is None:
             # Assume naive datetime is UTC if not specified, or raise error. 
             # Here we force it to UTC for consistency.
             self.time = spot_time.replace(tzinfo=timezone.utc)
        else:
             self.time = spot_time.astimezone(timezone.utc)
        
        self.price = float(spot_price)
        # Type hinting these lambdas strictly is complex without Protocol, but basic hint helps
        self.vol: Callable[[Any, float], float] = lambda asset, t: 0.2
        self.div: Callable[[Any], float] = lambda asset: dividend

class Option(abc.ABC):

    def __init__(self, expiry_date: datetime, otype: str):
        self.otype = otype
        if expiry_date.tzinfo is None:
            self.expiry = expiry_date.replace(tzinfo=timezone.utc)
        else:
            self.expiry = expiry_date.astimezone(timezone.utc)
        
        # Initialize attributes that will be set later
        self.strike: float = 0.0
        self.int_rate: Optional[Callable[[float], float]] = None
        self.spot_price: Union[List[float], np.ndarray] = []
        self.currency: List[Any] = []
        self._time: List[datetime] = []
        self._vol: List[Callable] = [] 
        self.div: List[Callable] = []
        self.time_to_maturity: float = 0.0

    def _attach_asset(self, strike_price: float, *underlyings: Underlying) -> None:
        self.strike = float(strike_price)
        self.int_rate = int_rate
        self.spot_price = []
        self.currency = []
        self._time = []
        self._vol = [] 
        self.div = []
        
        for underlying in underlyings:
            self.spot_price.append(underlying.price)
            self._time.append(underlying.time)
            self._vol.append(underlying.vol)
            self.div.append(underlying.div)
            
        self.spot_price = np.array(self.spot_price)
        
        # Ensure all times are consistent
        if not self._time:
             raise ValueError('No underlyings provided')

        first_time = self._time[0]
        if all(t == first_time for t in self._time):
            # Calculate time to maturity in years (approximate)
            self.time_to_maturity = (self.expiry - first_time).total_seconds() / (365.0 * 24 * 3600)
        else:
            raise ValueError('Underlyings have different spot times')

    def payoff(self, price: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        if self.otype == 'call':
            return np.clip(price - self.strike, 0, None).astype(float)
        elif self.otype == 'put':
            return np.clip(self.strike - price, 0, None).astype(float)
        else:
            raise ValueError('Incorrect option type')

class EurOption(Option):
    """
    Standard European Option.
    """
    def __init__(self, otype: str, expiry_date: datetime):
        super().__init__(expiry_date=expiry_date, otype=otype)

class AmeOption(Option):
    """
    Standard American Option.
    """
    def __init__(self, otype: str, expiry_date: datetime):
        super().__init__(expiry_date=expiry_date, otype=otype)

class BarOption(EurOption, AmeOption):  
    """
    Barrier Option (Knock-out).
    """

    def __init__(self, otype: str, expiry: datetime, strike_price: float = 10.0, 
                 barrier: List[Optional[float]] = [0, None], rebate: float = 5.0):
        super().__init__(otype, expiry)
        self.rebate = rebate
        self._barrier: np.ndarray = np.array([0.0, np.inf]) # Default initialization
        self.barrier = barrier # Use setter

    @property
    def barrier(self) -> np.ndarray:
        return self._barrier

    @barrier.setter
    def barrier(self, val: Union[List[Optional[float]], np.ndarray]) -> None:
        try:
            # Handle None as infinity or 0 depending on position, logic adapted from original
            processed_val = []
            if val[0] is None: processed_val.append(0.0)
            else: processed_val.append(float(val[0]))
            
            if val[1] is None: processed_val.append(np.inf)
            else: processed_val.append(float(val[1]))

            arr_val = np.array(processed_val, dtype=float)
            
            # Broadcast to ensure shape
            arr_val = np.broadcast_to(arr_val, (2,))
            
            self._barrier = np.where(
                [self.strike < arr_val[0], self.strike > arr_val[1]], 
                [0, np.inf], 
                arr_val
            )
        except (AttributeError, TypeError, IndexError):
             # Fallback or re-raise if strictly needed, original code had broad except
             # Here we assume val might be directly usable if simple setter failed
             # But for safety, let's stick to the logic above or raise
             raise ValueError("Wrong barrier input form")

    def _attach_asset(self, barrier: List[Optional[float]], strike_price: float, *underlyings: Underlying) -> None:
        super()._attach_asset(strike_price, *underlyings)
        self.barrier = barrier

    def payoff(self, price: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        lower_bar, higher_bar = self.barrier
        if np.isscalar(price):
            if price <= lower_bar or price >= higher_bar:
                return self.rebate
            else:
                return super().payoff(price)
        else:
            final = super().payoff(price)
            # Ensure price is handled as array
            price_arr = np.asarray(price)
            damp_layer = np.where((price_arr <= lower_bar) | (price_arr >= higher_bar))
            final[damp_layer] = self.rebate
            return final

class BasketOption(Option):

    def _attach_asset(self, strike_price: float, *underlyings: Underlying) -> None:
        super()._attach_asset(strike_price, *underlyings)
        # Convert lists to arrays
        self.spot_price = np.array(self.spot_price)
        # _vol and div are lists of functions/lambdas, keeping them as list or converting if needed
        # Original code converted them to array, which might be object array for functions
        
        self.AssetCount = len(self._vol)
        self.corr_mat = np.identity(self.AssetCount)
        self.weight = np.full(self.AssetCount, 1.0/self.AssetCount)

    def set_corr(self, corr_lst: List[float]) -> None:
        """
        Load the correlation matrix using only upper-triangle entries.
        """
        # Validate length
        expected_len = (self.AssetCount * (self.AssetCount - 1)) // 2
        if len(corr_lst) != expected_len:
             # Just a warning or strict error? Original didn't check length explicitly before assignment
             pass
             
        self.corr_mat[np.triu_indices(self.AssetCount, 1)] = corr_lst
        self.corr_mat[np.tril_indices(self.AssetCount, -1)] = corr_lst

    def set_weight(self, weight_lst: Union[List[float], np.ndarray]) -> None:
        if len(weight_lst) == self.AssetCount:
            self.weight = np.array(weight_lst, dtype=float)
        else:
            raise ValueError('Number of weights does not match number of assets')

    def payoff(self, price: np.ndarray) -> Union[float, np.ndarray]:
        # Price here is expected to be (..., AssetCount) or similar structure
        # Original: sum_price = (price * self.weight).sum(axis=-1)
        # We assume price matches weight dimensions on the last axis
        sum_price = (price * self.weight).sum(axis=-1)
        return super().payoff(sum_price)
