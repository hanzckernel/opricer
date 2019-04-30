#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from numpy import linalg
import numpy as np


# In[ ]:


def BS_tester_call(asset, t, T, vol, r, D, K):
    moneyness = np.log(asset / K)
    d1 = (moneyness +(r-D + vol**2/2)*T)/(vol * np.sqrt(T))
    d2 = d1 - vol * np.sqrt(T)
    return asset * np.exp(-D*T)*norm.cdf(d1) - K * np.exp(-r*T)*norm.cdf(d2)

def plot(base_arr, *func):
    fig = plt.figure(figsize=(16, 8))
    ax = fig.add_subplot(111)
    plt.xlabel('asset value')
    plt.ylabel('option price')
    for f in func:
        ax.plot(base_arr, f(base_arr), '-o', label = f.__name__)
    ax.legend(loc ='best')
    plt.show()

