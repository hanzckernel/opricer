import plotly.plotly as py
import plotly.graph_objs as go
import json
from model import models
from algo.analytics import AnalyticSolver
import datetime
import pandas as pd
import numpy as np

# start = datetime.datetime(2012, 1, 1)
# end = datetime.datetime(2013, 1, 1)
# a = models.Underlying(start, 100)
# b = models.EurOption(end, 'call')
# b._attach_asset(100, a)

# solver = AnalyticSolver()

# timeRange = pd.date_range(start, end, 3).strftime(
#     '%d %B (%a), %Y')
# newTime = (start + pd.timedelta_range(0, end-start, 100)
#            ).values.astype('datetime64[h]')
# # newTime = start + np.linspace(0, 1, 100) * datetime.timedelta(days=366)
# # print(timeRange, newTime)
# # print(solver.time_samples)


# arr = np.linspace(0, 10, 9).reshape(3, 3)
# df = pd.DataFrame(arr, index=timeRange, columns=[0, 5, 10])
# y = pd.date_range(start, end, 100).strftime('%Y-%m-%d, %r').to_list()
# fig = {"data": [go.Surface(x=[1, 2, 3], y=[4, 5, 6], z=[7, 8, 9])]}

# print(fig.get("data")[0]['x'])


import math
import re


def func_check(string):
    expr = r'{}'.format(string)
    pattern = re.compile('lambda+')
    return pattern.findall(expr)
    # safe_list = dir(math)[6:]
    # safe_dict = dict([(k, getattr(math, k)) for k in safe_list])
    # return safe_dict


print(func_check('lambda x,y: x+y'))
