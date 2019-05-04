#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 20:08:02 2019

@author: hanzhicheng
"""
import numpy as np


def back_quad(func, arr):
    '''Receive a range of points and evaluate the area below graph from backwards'''
    arr = np.flip(arr, 0)  # flip to count form back to front
    out_list = []
    for i in range(1, len(arr)):
        increment = arr[i - 1] - arr[i]
        to_add = increment * func((arr[i - 1] + arr[i]) / 2)
        out_list.append(to_add)
    out_arr = np.array([0] + out_list)
    return np.cumsum(out_arr)
