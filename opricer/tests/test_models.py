
import unittest
from datetime import datetime, timezone, timedelta
import numpy as np
from opricer.model import models

class TestModels(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.expiry = self.now + timedelta(days=365)
        self.underlying = models.Underlying(self.now, 100.0)

    def test_underlying_init(self):
        u = models.Underlying(self.now, 100.0, dividend=0.1)
        self.assertEqual(u.spot_price, 100.0)
        self.assertEqual(u.dividend, 0.1)
        # Check timezone enforcement
        naive_time = datetime(2025, 1, 1)
        u_naive = models.Underlying(naive_time, 100.0)
        self.assertIsNotNone(u_naive.time.tzinfo)

    def test_euro_option_init(self):
        opt = models.EurOption(self.expiry, 'call')
        self.assertEqual(opt.otype, 'call')
        self.assertEqual(opt.expiry, self.expiry)

    def test_attach_asset(self):
        opt = models.EurOption(self.expiry, 'call')
        opt._attach_asset(100.0, self.underlying)
        self.assertEqual(opt.strike, 100.0)
        self.assertEqual(len(opt.spot_price), 1)
        self.assertAlmostEqual(opt.time_to_maturity, 1.0, delta=0.01)

    def test_payoff_call(self):
        opt = models.EurOption(self.expiry, 'call')
        opt.strike = 100.0
        self.assertEqual(opt.payoff(110.0), 10.0)
        self.assertEqual(opt.payoff(90.0), 0.0)
        
    def test_payoff_put(self):
        opt = models.EurOption(self.expiry, 'put')
        opt.strike = 100.0
        self.assertEqual(opt.payoff(90.0), 10.0)
        self.assertEqual(opt.payoff(110.0), 0.0)

    def test_bar_option(self):
        opt = models.BarOption(self.expiry, 'call', strike_price=100.0, barrier=[80.0, 120.0])
        # Barrier setter logic check
        # Barrier is [80, 120]
        # Payoff within barrier
        self.assertEqual(opt.payoff(110.0), 10.0) # 110 is between 80 and 120
        # Payoff outside barrier (Knock-out -> rebate)
        self.assertEqual(opt.payoff(130.0), 5.0) # default rebate 5.0
        self.assertEqual(opt.payoff(70.0), 5.0)
    
    def test_basket_option(self):
        u2 = models.Underlying(self.now, 100.0)
        opt = models.BasketOption(self.expiry, 'call')
        opt._attach_asset(100.0, self.underlying, u2)
        self.assertEqual(opt.AssetCount, 2)
        # Default weights equal
        self.assertTrue(np.allclose(opt.weight, [0.5, 0.5]))
        
        # Payoff: sum of weighted prices
        # prices: [110, 110] -> avg 110 -> payoff 10
        prices = np.array([110.0, 110.0])
        self.assertEqual(opt.payoff(prices), 10.0)

if __name__ == '__main__':
    unittest.main()
