#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 20:08:02 2019

@author: hanzhicheng
"""
# %%
import numpy as np
from functools import wraps
from sklearn.preprocessing import PolynomialFeatures


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
    diff = np.ediff1d(arr, to_end=0)
    diff *= func(arr + diff/2)
    diff = np.cumsum(np.flip(diff))
    return diff


def ArrFunc(func_lst, *arr):
    """
    Apply arrays of function to the same array. End array shape: (arr.shape, func_lst.shape)
    """
    output = np.array([func(*arr) for func in func_lst])
    output = np.moveaxis(output, 0, -1)
    return output


def poly_transform_(arr, axis=None, deg=2):
    """
    Ad-hoc workaround of polynomial transform for higher-dimensional tensors,
    as current scikit only accept vectors as samples.

    (a0, a1, ..., an) --> (a0, a1, ..., axis-1, axis+1, ..., axis_transform)

    Input array are assumed to be shape: (sample_no, sample.shape)

    Elementwise, poly_transform(deg = 2) is equivalent to
    PolynomialFeatures.fit_transform(
        2, interaction_only = True, include_Bias = False)

    If each sample is of shape (x_dim, y_dim), then Poly_transform(arr, axis = 0) apply
    Polynomial only in x_directions.

    The output of each sample is flattened for Linear Model fit.
    """
    arr = arr if axis else np.expand_dims(arr, -1)
    axis = axis if axis else -1
    para_no = arr.shape[axis]
    arr = np.moveaxis(arr, axis, -1)
    comb = PolynomialFeatures._combinations(
        para_no, deg, interaction_only=False, include_bias=False)
    poly_deg = np.vstack(
        [np.bincount(c, minlength=para_no) for c in comb])
    poly_deg = poly_deg.reshape(
        (poly_deg.shape[0],) + (1,) * (arr.ndim - 1) + (poly_deg.shape[1],))
    out_arr = np.power(arr, poly_deg).prod(axis=-1)
    return np.moveaxis(out_arr, 0, -1)


arr = np.arange(10)
# arr = np.moveaxis(arr, 0, -1)
print(arr.shape, poly_transform_(arr, axis=None, deg=3).shape)

# %%
