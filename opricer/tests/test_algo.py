
import unittest
import numpy as np
from datetime import datetime, timedelta
from opricer.model import models
from opricer.algo import pde, mc, analytics

class TestAlgo(unittest.TestCase):

    def setUp(self):
        self.spot_price = 100.0
        self.strike_price = 100.0
        self.now = datetime.now()
        self.expiry = self.now + timedelta(days=365)
        self.underlying = models.Underlying(self.now, self.spot_price)
        
        # Basket setup
        self.underlying1 = models.Underlying(self.now, 100.0)
        self.underlying2 = models.Underlying(self.now, 100.0)

    def test_analytic_solver_eur_call(self):
        option = models.EurOption('call', self.expiry)
        option._attach_asset(self.strike_price, self.underlying)
        solver = analytics.AnalyticSolver()
        price = solver(option)
        self.assertIsNotNone(price)
        self.assertTrue(np.any(price > 0))

    def test_analytic_solver_eur_put(self):
        option = models.EurOption('put', self.expiry)
        option._attach_asset(self.strike_price, self.underlying)
        solver = analytics.AnalyticSolver()
        price = solver(option)
        self.assertIsNotNone(price)

    def test_pde_eur_solver(self):
        option = models.EurOption('call', self.expiry)
        option._attach_asset(self.strike_price, self.underlying)
        solver = pde.EurSolver()
        price = solver(option)
        # EurSolver returns an array of prices (or greeks)
        self.assertIsInstance(price, np.ndarray)
        self.assertTrue(price.size > 0)

    def test_pde_ame_solver(self):
        option = models.AmeOption('call', self.expiry)
        option._attach_asset(self.strike_price, self.underlying)
        solver = pde.AmeSolver()
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)
        self.assertTrue(price.size > 0)

    def test_pde_bar_solver(self):
        # Barrier option setup
        # BarOption._attach_asset(barrier, strike, *underlyings)
        option = models.BarOption('call', self.expiry)
        barrier = [80.0, 120.0]
        option._attach_asset(barrier, self.strike_price, self.underlying)
        solver = pde.BarSolver()
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_eur_solver(self):
        option = models.EurOption('call', self.expiry)
        option._attach_asset(self.strike_price, self.underlying)
        solver = mc.EurMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_log_solver(self):
        option = models.EurOption('call', self.expiry)
        option._attach_asset(self.strike_price, self.underlying)
        solver = mc.logMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_bar_solver(self):
        option = models.BarOption('call', self.expiry)
        barrier = [80.0, 120.0]
        option._attach_asset(barrier, self.strike_price, self.underlying)
        solver = mc.BarMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_ame_solver(self):
        option = models.AmeOption('put', self.expiry) # Ame put is more interesting
        option._attach_asset(self.strike_price, self.underlying)
        solver = mc.AmeMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_basket_solver(self):
        option = models.BasketOption(self.expiry, 'call')
        option._attach_asset(self.strike_price, self.underlying1, self.underlying2)
        # Basket option needs correlation
        # 2 assets -> 1 pair (0,1)
        option.set_corr([0.5]) 
        solver = mc.BasketMCSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

    def test_mc_basket_ame_solver(self):
        option = models.BasketOption(self.expiry, 'put') # Use same option instance? No, new one for clarity
        # BasketOption inherits from Option, but BasketAmeSolver expects BasketOption model structure
        # Wait, models.BasketOption doesn't inherit from AmeOption explicitly in models.py?
        # models.BasketOption(Option)
        # But BasketAmeSolver uses AmeMCSolver.get_price which expects model.payoff logic.
        
        # Let's check models.BasketOption again. It inherits from Option.
        # But AmeMCSolver uses "Ame" logic (Longstaff-Schwartz).
        # BasketAmeSolver(BasketMCSolver, AmeMCSolver).
        
        # Let's try instantiating a BasketOption
        option = models.BasketOption(self.expiry, 'put')
        option._attach_asset(self.strike_price, self.underlying1, self.underlying2)
        option.set_corr([0.5])
        
        solver = mc.BasketAmeSolver(path_no=100, asset_no=10, time_no=10)
        price = solver(option)
        self.assertIsInstance(price, np.ndarray)

if __name__ == '__main__':
    unittest.main()
