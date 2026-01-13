import unittest
import numpy as np
from datetime import datetime, timedelta, timezone
from opricer.model import models
from opricer.algo import pde, mc, analytics

class TestAlgo(unittest.TestCase):

    def setUp(self):
        self.spot_price = 100.0
        self.strike_price = 100.0
        self.now = datetime.now(timezone.utc)
        self.expiry = self.now + timedelta(days=365)
        self.underlying = models.Underlying(self.now, self.spot_price)
        
        # Basket setup
        self.underlying1 = models.Underlying(self.now, 100.0)
        self.underlying2 = models.Underlying(self.now, 100.0)

    def test_analytic_solver_eur_call(self):
        # Standardized signature: (expiry, otype)
        option = models.EurOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying)
        solver = analytics.AnalyticSolver()
        price = solver(option)
        self.assertIsNotNone(price)
        # Analytic solver returns (Time x Asset), check values
        self.assertTrue(np.all(np.isfinite(price)))

    def test_analytic_solver_eur_put(self):
        option = models.EurOption(self.expiry, 'put')
        option._attach_asset(self.strike_price, self.underlying)
        solver = analytics.AnalyticSolver()
        price = solver(option)
        self.assertIsNotNone(price)

    def test_pde_eur_solver(self):
        option = models.EurOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying)
        solver = pde.EurSolver()
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)
        self.assertTrue(price.size > 0)

    def test_pde_ame_solver(self):
        option = models.AmeOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying)
        solver = pde.AmeSolver()
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)
        self.assertTrue(price.size > 0)

    def test_pde_bar_solver(self):
        option = models.BarOption(self.expiry, 'call')
        barrier = [80.0, 120.0]
        option._attach_asset(barrier, self.strike_price, self.underlying)
        solver = pde.BarSolver()
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_eur_solver(self):
        option = models.EurOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying)
        solver = mc.EurMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_log_solver(self):
        option = models.EurOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying)
        solver = mc.LogMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_bar_solver(self):
        option = models.BarOption(self.expiry, 'call')
        barrier = [80.0, 120.0]
        option._attach_asset(barrier, self.strike_price, self.underlying)
        solver = mc.BarMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_ame_solver(self):
        option = models.AmeOption(self.expiry, 'put')
        option._attach_asset(self.strike_price, self.underlying)
        solver = mc.AmeMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_basket_solver(self):
        option = models.BasketOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying1, self.underlying2)
        option.set_corr([0.5]) 
        solver = mc.BasketMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_basket_ame_solver(self):
        option = models.BasketOption(self.expiry, 'put')
        option._attach_asset(self.strike_price, self.underlying1, self.underlying2)
        option.set_corr([0.5])
        solver = mc.BasketAmeSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

if __name__ == '__main__':
    unittest.main()