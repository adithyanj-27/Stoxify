import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import database

class FakeRequest:
    def __init__(self, user_id=None):
        self.headers = {}
        self.query_params = {}
        if user_id:
            self.headers["authorization"] = f"Bearer {main.issue_session_token(user_id)}"

class TestPortfolioChart(unittest.TestCase):
    def test_empty_user(self):
        req = FakeRequest("non_existent_user_99999")
        res = main.read_portfolio_chart(req, timeframe="1M", asset_type="STOCK")
        self.assertEqual(res["points"], [])
        self.assertEqual(res["invested_val"], 0.0)
        self.assertEqual(res["current_val"], 0.0)

    def test_user_with_orders_no_phantom_history(self):
        req = FakeRequest("STOX-212881")
        res_1y = main.read_portfolio_chart(req, timeframe="1Y", asset_type="STOCK")
        self.assertIn("points", res_1y)
        self.assertIn("invested_val", res_1y)
        self.assertIn("current_val", res_1y)
        self.assertIn("timeframe_pnl", res_1y)
        # Should NOT have 250 points from 2025
        self.assertLess(len(res_1y["points"]), 50)
        if res_1y["points"]:
            first_pt = res_1y["points"][0]
            # Verify first point is from Sep 2026, NOT 2025
            self.assertIn("29 Sep", first_pt["time"])

    def test_mutual_fund_chart(self):
        req = FakeRequest("test_user_chart")
        res = main.read_portfolio_chart(req, timeframe="1M", asset_type="MUTUAL_FUND")
        self.assertIn("points", res)
        self.assertIn("invested_val", res)

if __name__ == "__main__":
    unittest.main()
