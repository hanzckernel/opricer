# from data import models
# from algo import pde
# %%
import numpy as np
import datetime
from opricer.data import models
from opricer.algo import pde, analytics, mc
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from scipy.sparse import diags
from scipy.linalg import lu_solve, lu_factor


a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
b = models.EurOption(datetime.datetime(2011, 1, 1), 'put')
c = models.AmeOption(datetime.datetime(2011, 1, 1), 'put')
d = models.BarOption(datetime.datetime(2011, 1, 1), 'put')
b._attach_asset(100, a)
c._attach_asset(100, a)
d._attach_asset([50, np.inf], 100, a)
solver = analytics.AnalyticSolver()
solver1 = pde.EurSolver()
solver2 = pde.AmeSolver()
solver3 = pde.BarSolver()
Msolver1 = mc.EurMCSolver()
Msolver2 = mc.logMCSolver()
# print(solver3.get_price(d))
# print(solver1(a).shape)
# print(c.__dict__)

# print(np.gradient(price, axis=0))


def plot(options, solvers, with_cursor=False):
    fig = plt.figure(figsize=(15, 8))
    ax = plt.axes()
    price = solver(b)
    MCprice = Msolver1(b)
    ax.plot(solver.asset_samples, price, label='AnalyticSol')
    ax.plot(Msolver1.asset_samples, MCprice, label='MC')
    ax.plot(Msolver1.asset_samples, Msolver2(b), label='logMC')
    for opt, sol in zip(options, solvers):
        ax.plot(solver.asset_samples, sol(opt)[0], label=type(
            sol).__name__ + type(opt).__name__)
    ax.legend(loc='best')
    if with_cursor:
        cursor = Cursor(ax, useblit=True, linewidth=2)
    plt.show()
    plt.gcf()


plot([], [])


# %%
# L = diags([solver3.L[50], 1], [-1, 0], shape=(48, 48)).A
# U = diags([solver3.H[50], solver3.C[1:-1, 50]], [0, 1], shape=(48, 48)).A

# # # L, H, C = solver3.L[50], solver3.H[50], solver3.C[1:-1, 50]
# # solver3._load_sim(c)
# # L1 = diags([solver3.L[50], 1], [-1, 0], shape=(48, 48)).A
# # U1 = diags([solver3.H[50], solver3.C[1:-1, 50]], [0, 1], shape=(48, 48)).A
# diag = diags([solver3.A[2:-1, 50], solver3.B[1:-1, 50], solver3.C[1:-2, 50]],
#              [-1, 0, 1], shape=(48, 48)).A

# %%
#
