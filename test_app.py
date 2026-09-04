import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Set clean test environment
def test_all():
    print("=======================================")
    print(" Running GrowwFAHH Automated Test Suite")
    print("=======================================")

    # 1. Test Database
    print("\n[1/4] Testing Database & Persistence...")
    import database
    database.init_db()
    acc = database.get_account()
    assert acc["balance"] == 1000000.0, f"Expected 1000000.0, got {acc['balance']}"
    print(" ✓ Database initialized with ₹10,00,000 balance")

    # 2. Test Market Service
    print("\n[2/4] Testing Market Data Feeds...")
    import market_service
    indices = market_service.get_indices()
    assert len(indices) >= 4, f"Expected at least 4 indices, got {len(indices)}"
    print(f" ✓ Indices fetched: {[idx['name'] + ': ' + str(idx['price']) for idx in indices[:2]]}")

    quote = market_service.get_stock_quote("RELIANCE.NS")
    assert quote["price"] > 0, "Expected price > 0"
    print(f" ✓ Stock Quote (Reliance): ₹{quote['price']}, Change: {quote['change']} ({quote['change_pct']}%)")

    mf_quote = market_service.get_mutual_fund_quote("122639")
    assert mf_quote["price"] > 0, "Expected MF NAV > 0"
    print(f" ✓ Mutual Fund (Parag Parikh): NAV ₹{mf_quote['price']}, 1Y Return: {mf_quote['return_1y']}%")

    search_res = market_service.search_market("Tata")
    assert len(search_res) > 0, "Expected search results for 'Tata'"
    print(f" ✓ Search Autocomplete: Found {len(search_res)} matching results")

    # 3. Test Trade Execution Engine
    print("\n[3/4] Testing Trade Execution & Portfolio Math...")
    # Buy 10 shares of Tata Motors at ₹1000
    res_buy = database.execute_trade("TATAMOTORS.NS", "Tata Motors Ltd", "STOCK", "BUY", "DELIVERY", 10, 1000.0)
    assert res_buy["success"], f"Buy failed: {res_buy}"
    acc_after_buy = database.get_account()
    assert acc_after_buy["balance"] == 990000.0, f"Expected 990000.0, got {acc_after_buy['balance']}"

    # Buy 5 more at ₹1300 -> 15 shares @ avg ((10*1000)+(5*1300))/15 = 1100
    res_buy2 = database.execute_trade("TATAMOTORS.NS", "Tata Motors Ltd", "STOCK", "BUY", "DELIVERY", 5, 1300.0)
    assert res_buy2["success"]
    holdings = database.get_holdings()
    tm_holding = next(h for h in holdings if h["symbol"] == "TATAMOTORS.NS")
    assert tm_holding["quantity"] == 15
    assert tm_holding["avg_price"] == 1100.0, f"Expected 1100.0, got {tm_holding['avg_price']}"
    print(f" ✓ Buy Orders: 15 shares @ ₹1,100.00 avg, Remaining Cash: ₹{database.get_account()['balance']:,.2f}")

    # Sell 5 shares at ₹1200 -> Realized P&L = 5 * (1200 - 1100) = +₹500
    res_sell = database.execute_trade("TATAMOTORS.NS", "Tata Motors Ltd", "STOCK", "SELL", "DELIVERY", 5, 1200.0)
    assert res_sell["success"]
    orders = database.get_orders(limit=1)
    assert orders[0]["realized_pnl"] == 500.0, f"Expected 500.0 P&L, got {orders[0]['realized_pnl']}"
    print(f" ✓ Sell Order: Executed successfully with Realized P&L: +₹{orders[0]['realized_pnl']:,.2f}")

    # Test Insufficient Funds Validation
    res_overbuy = database.execute_trade("EXPENSIVE.NS", "Expensive Stock", "STOCK", "BUY", "DELIVERY", 100, 2000000.0)
    assert not res_overbuy["success"], "Expected trade to fail due to insufficient balance"
    print(" ✓ Validation: Correctly prevented over-budget buy order")

    # Reset account back to clean ₹10,00,000
    database.reset_account(1000000.0)
    assert database.get_account()["balance"] == 1000000.0
    print(" ✓ Account Reset: Restored to fresh ₹10,00,000 state")

    # 4. Test FastAPI endpoints
    print("\n[4/4] Testing FastAPI Endpoints...")
    import main
    acc_res = main.read_account()
    assert acc_res["balance"] == 1000000.0
    print(f" ✓ /api/account returned balance: ₹{acc_res['balance']:,.2f}")

    portfolio_res = main.read_portfolio()
    assert "total_portfolio_value" in portfolio_res
    print(f" ✓ /api/portfolio calculated: ₹{portfolio_res['total_portfolio_value']:,.2f}")

    indices_res = main.read_indices()
    assert len(indices_res) >= 4
    print(f" ✓ /api/indices returned {len(indices_res)} indices")

    print("\n=======================================")
    print(" ALL GROWWFAHH TESTS PASSED 100% SUCCESS!")
    print("=======================================")

if __name__ == "__main__":
    test_all()
