# from data import models
# from algo import pde
# %%
import numpy as np
import datetime
from opricer.data import models
from opricer.algo import pde
from opricer.tests.test_algo import AnalyticSolver
import matplotlib.pyplot as plt


a = models.EurOption(datetime.datetime(2011, 1, 1), 'call')
b = models.Underlying(datetime.datetime(2010, 1, 1), 100, dividend=0.0)
c = models.BarOption(datetime.datetime(2011, 1, 1), 'call')
a._attach_asset(100, b)
c._attach_asset([40, 400], 100, b)
solver = pde.EurSolver()
solver2 = AnalyticSolver()
solver3 = pde.BarSolver()
# print(solver2(a), solver(a), solver.asset_samples)


fig = plt.figure(figsize=(15, 8))
ax = plt.axes()
price = solver2(a)
ax.plot(solver2.asset_samples, price, label='test')
ax.plot(solver2.asset_samples, solver(a), label='sim')
ax.plot(solver2.asset_samples, solver3(c), label='bar')
ax.legend(loc='best')
plt.show()
plt.gcf()


# %%
