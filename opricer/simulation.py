# from data import models
# from algo import pde
import numpy as np
import datetime
from opricer.data import models
from opricer.algo import pde

a = models.EurOption('A', datetime.datetime(2011, 1, 1))
b = models.Underlying('b', datetime.datetime(2010, 1, 1), 100)

a._attach_asset(100, b)
