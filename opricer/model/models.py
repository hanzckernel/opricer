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
from dataclasses import dataclass, field

def default_int_rate(t: float) -> float: 
    return 0.05

class World(abc.ABC):
    """
    Placeholder for future World/Market environment settings.
    """
    pass

@dataclass
class Underlying:
    """
    Represents an underlying asset.
    We currently use prescribed drift and volatility for simplicity.
    All time entries are expected to be in UTC.
    """
    spot_time: datetime
    spot_price: float
    dividend: float = 0.0
    
    # Internal attributes initialized in __post_init__
    time: datetime = field(init=False)
    price: float = field(init=False)
    vol: Callable[[Any, float], float] = field(init=False)
    div: Callable[[Any], float] = field(init=False)

    def __post_init__(self):
        if self.spot_time.tzinfo is None:
             self.time = self.spot_time.replace(tzinfo=timezone.utc)
        else:
             self.time = self.spot_time.astimezone(timezone.utc)
        
        self.price = float(self.spot_price)
        # Default volatility and dividend functions
        self.vol = lambda asset, t: 0.2
        self.div = lambda asset: self.dividend

class Option(abc.ABC):

    def __init__(self, expiry_date: datetime, otype: str):
        self.otype = otype
        if expiry_date.tzinfo is None:
            self.expiry = expiry_date.replace(tzinfo=timezone.utc)
        else:
            self.expiry = expiry_date.astimezone(timezone.utc)
        
        # Initialize attributes
        self.strike: float = 0.0
        self.int_rate: Callable[[float], float] = default_int_rate
        self.spot_price: Union[List[float], np.ndarray] = np.array([])
        self.currency: List[Any] = []
        self._time: List[datetime] = []
        self._vol: List[Callable] = [] 
        self.div: List[Callable] = []
        self.time_to_maturity: float = 0.0

    def _attach_asset(self, strike_price: float, *underlyings: Underlying) -> None:
        """
        Attaches underlying assets to the option.
        """
        self.strike = float(strike_price)
        # Reset lists
        spot_prices = []
        self.currency = []
        self._time = []
        self._vol = [] 
        self.div = []
        
        for underlying in underlyings:
            spot_prices.append(underlying.price)
            self._time.append(underlying.time)
            self._vol.append(underlying.vol)
            self.div.append(underlying.div)
            
        self.spot_price = np.array(spot_prices)
        
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
            raise ValueError(f'Incorrect option type: {self.otype}')

class EurOption(Option):
    """
    Standard European Option.
    """
    pass

class AmeOption(Option):
    """
    Standard American Option.
    """
    pass

class BarOption(EurOption, AmeOption):  
    """
    Barrier Option (Knock-out).
    Inherits from EurOption and AmeOption to support both pricing methods where applicable.
    """

    def __init__(self, expiry: datetime, otype: str, strike_price: float = 10.0, 
                 barrier: List[Optional[float]] = [0, None], rebate: float = 5.0):
        # Initialize with EurOption's init (which is Option's init)
        EurOption.__init__(self, expiry, otype)
        self.strike = strike_price
        self.rebate = rebate
        self._barrier: np.ndarray = np.array([0.0, np.inf])
        self.barrier = barrier 

    @property
    def barrier(self) -> np.ndarray:
        return self._barrier

    @barrier.setter
    def barrier(self, val: Union[List[Optional[float]], np.ndarray]) -> None:
        try:
            processed_val = []
            if val[0] is None: processed_val.append(0.0)
            else: processed_val.append(float(val[0]))
            
            if val[1] is None: processed_val.append(np.inf)
            else: processed_val.append(float(val[1]))

            arr_val = np.array(processed_val, dtype=float)
            arr_val = np.broadcast_to(arr_val, (2,))
            
            # Adjust barrier based on strike price logic (Knock-out)
            # If strike is within the barrier, the barrier is valid.
            # If strike is outside, logic might be inverted, but here we assume standard knock-out
            self._barrier = np.where(
                [self.strike < arr_val[0], self.strike > arr_val[1]], 
                [0, np.inf], 
                arr_val
            )
        except (AttributeError, TypeError, IndexError):
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
            price_arr = np.asarray(price)
            damp_layer = np.where((price_arr <= lower_bar) | (price_arr >= higher_bar))
            final[damp_layer] = self.rebate
            return final

class BasketOption(Option):

    def _attach_asset(self, strike_price: float, *underlyings: Underlying) -> None:
        super()._attach_asset(strike_price, *underlyings)
        self.AssetCount = len(self._vol)
        self.corr_mat = np.identity(self.AssetCount)
        self.weight = np.full(self.AssetCount, 1.0/self.AssetCount)

    def set_corr(self, corr_lst: List[float]) -> None:
        """
        Load the correlation matrix using only upper-triangle entries.
        """
        self.corr_mat[np.triu_indices(self.AssetCount, 1)] = corr_lst
        self.corr_mat[np.tril_indices(self.AssetCount, -1)] = corr_lst

    def set_weight(self, weight_lst: Union[List[float], np.ndarray]) -> None:
        if len(weight_lst) == self.AssetCount:
            self.weight = np.array(weight_lst, dtype=float)
        else:
            raise ValueError('Number of weights does not match number of assets')

    def payoff(self, price: np.ndarray) -> Union[float, np.ndarray]:
        # Weighted sum of asset prices
        sum_price = (price * self.weight).sum(axis=-1)
        return super().payoff(sum_price)