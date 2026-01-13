
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from opricer.model import models
from opricer.algo import pde, analytics, mc
# Removed unused imports: scipy.linalg, scipy.sparse, pandas, etc. unless needed

# Ensure UTC for all datetimes
# Using timezone-aware datetimes
tz = datetime.timezone.utc

np.random.seed(123)

# Initialize Underlyings with UTC
a = models.Underlying(datetime.datetime(2010, 1, 1, tzinfo=tz), 100)
a1 = models.Underlying(datetime.datetime(2010, 1, 1, tzinfo=tz), 200)

# Initialize Options with UTC
b = models.EurOption(datetime.datetime(2011, 1, 1, tzinfo=tz), 'call')
b1 = models.AmeOption(datetime.datetime(2011, 1, 1, tzinfo=tz), 'call')
c = models.BasketOption(datetime.datetime(2011, 1, 1, tzinfo=tz), 'call')
d = models.BarOption(datetime.datetime(2011, 1, 1, tzinfo=tz), 'put')

# Attach Assets
b._attach_asset(100, a)
b1._attach_asset(100, a1)
c._attach_asset(100, a, a1)
# d._attach_asset([30, np.inf], 100, a) # Keeping commented as in original

# Solvers
solver = analytics.AnalyticSolver(high_val=2, low_val=0)
price = solver(b)
solver1 = pde.EurSolver()
solver2 = pde.AmeSolver(high_val=2, low_val=0)

Msolver = mc.EurMCSolver(path_no=60000, asset_no=10,
                         time_no=100, high_val=2, low_val=0)

print(f'Solver class: {solver.__class__.__name__}')

# Additional Solvers
solver4 = pde.BarSolver(high_val=2, low_val=0, asset_no=solver.asset_no)
Msolver2 = mc.BarMCSolver(high_val=2, low_val=0, asset_no=solver.asset_no)
Msolver3 = mc.BasketMCSolver(high_val=2, low_val=0, asset_no=solver.asset_no)
ABSolver = mc.BasketAmeSolver(high_val=2, low_val=0, asset_no=solver.asset_no)
ASolver = mc.AmeMCSolver(high_val=2, low_val=0, asset_no=solver.asset_no)


def plot(options, solvers, Msolvers, with_cursor=False):
    fig = plt.figure(figsize=(15, 8))
    ax = plt.axes()
    price = solver(b)
    # MCprice = Msolver(b) # Unused
    ax.plot(solver.asset_samples, price, label='AnalyticSol')

    for opt, sol in zip(options, Msolvers):
        ax.plot(solver.asset_samples, sol(opt), label=type(
            sol).__name__ + type(opt).__name__)
    
    ax.legend(loc='best')
    if with_cursor:
        cursor = Cursor(ax, useblit=True, linewidth=2)
    plt.show()

# Uncomment to run plot
# plot([b1, c], [], [ASolver, ABSolver])
