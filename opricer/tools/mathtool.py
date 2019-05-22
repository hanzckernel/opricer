#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 20:08:02 2019

@author: hanzhicheng
"""
# %%
import numpy as np
from functools import wraps


def force_broadcast(func):
    @wraps(func)
    def keep_shape(*args):
        return np.broadcast_arrays(*args, func(*args))[-1].copy('K')
    return keep_shape


def force_no_use(func, *args, **kwargs):
    """
    This was another recipe following np.nditer. I keep this here just in case.
    """
    @wraps(func)
    def luf(*args, **kwargs):
        nargs = len(args)
        op = (kwargs.get('out', None),) + args
        it = np.nditer(op, ['buffered', 'external_loop'],
                       [['writeonly', 'allocate', 'no_broadcast']] +
                       [['readonly', 'nbo', 'aligned']]*nargs,
                       order=kwargs.get('order', 'K'),
                       casting=kwargs.get('casting', 'safe'),
                       buffersize=kwargs.get('buffersize', 0))
        while not it.finished:
            it[0] = func(*it[1:])
            it.iternext()
        return it.operands[0]
    return luf


def back_quad(func, arr):
    '''Receive a range of points and evaluate the area below graph from T to 0'''
    out_list = [0]
    for i in range(1, arr.size):
        increment = arr[-i] - arr[-i-1]
        to_add = increment * func((arr[-i] + arr[-i-1]) / 2)
        out_list.append(to_add)
    out_arr = np.array(out_list)
    return np.cumsum(out_arr)


# %%
