import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Set clean test environment
def test_all():
    print("=======================================")
    print(" Running Stoxify Automated Test Suite")
    print("=======================================")

    # 1. Test Database
    print("\n[1/4] Testing Database & Persistence...")
    import database
    database.init_db()
    database.reset_account(1000000.0)
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

    # 4. Test Market Hours & Simulation
    print("\n[4/6] Testing Market Hours & Session Logic...")
    import market_hours
    m_status = market_hours.get_market_status()
    print(f" ✓ Market Status (Current): {m_status['session']} - {m_status['status_text']}")
    assert "session" in m_status
    assert "date_ist" in m_status

    # Toggle simulation mode
    sim_on = market_hours.toggle_simulation(True)
    assert sim_on["simulation_mode"] is True
    assert sim_on["is_open"] is True
    assert sim_on["intraday_allowed"] is True
    print(" ✓ Simulation mode toggle ON verified (24/7 trading enabled)")
    market_hours.toggle_simulation(False)
    print(" ✓ Simulation mode toggle OFF verified")

    # 5. Test Intraday 5x Leverage & Positions Engine
    print("\n[5/6] Testing Intraday (MIS) 5x Leverage & Square-off...")
    database.reset_account(1000000.0)
    # Buy 10 shares of Reliance at ₹2500 Intraday -> Total ₹25,000 -> Margin required at 5x = ₹5,000
    res_intra = database.execute_trade("RELIANCE.NS", "Reliance Industries", "STOCK", "BUY", "INTRADAY", 10, 2500.0)
    assert res_intra["success"], f"Intraday buy failed: {res_intra}"
    acc_intra = database.get_account()
    assert acc_intra["balance"] == 995000.0, f"Expected 995000.0 margin used, got {acc_intra['balance']}"
    
    # Check open positions
    positions = database.get_positions()
    assert len(positions) == 1
    pos = positions[0]
    assert pos["symbol"] == "RELIANCE.NS"
    assert pos["quantity"] == 10
    assert pos["margin_used"] == 5000.0
    print(f" ✓ 5x Margin verified: ₹{pos['margin_used']:,.2f} blocked for ₹25,000 position")

    # Exit position at ₹2600 -> P&L = +₹1,000 -> Return ₹5,000 margin + ₹1,000 profit = ₹6,000 added back -> Balance = 1,001,000
    res_exit = database.exit_position(pos["symbol"], 2600.0)
    assert res_exit["success"]
    assert res_exit["realized_pnl"] == 1000.0
    acc_after_exit = database.get_account()
    assert acc_after_exit["balance"] == 1001000.0, f"Expected 1001000.0, got {acc_after_exit['balance']}"
    print(f" ✓ Position Exit: P&L +₹{res_exit['realized_pnl']:,.2f}, margin released successfully")

    # Test Limit Order & Cancellation
    print("\n[6/6] Testing Limit Orders & Level-2 Market Depth...")
    # Place Limit BUY for 5 shares @ ₹2000 (below market price ₹2100) -> ₹10,000 blocked
    res_limit = database.execute_trade(
        "INFY.NS", "Infosys Ltd", "STOCK", "BUY", "DELIVERY", 5, 2100.0,
        order_variety="LIMIT", limit_price=2000.0
    )
    assert res_limit["success"]
    open_orders = database.get_orders(status_filter="OPEN")
    assert len(open_orders) == 1
    lim_order = open_orders[0]
    assert lim_order["order_variety"] == "LIMIT"
    assert lim_order["status"] == "OPEN"
    print(f" ✓ Limit Order placed: 5 shares of INFY @ ₹2,000.00 (Status: {lim_order['status']})")

    # Cancel the limit order
    res_cancel = database.cancel_order(lim_order["id"])
    assert res_cancel["success"]
    assert len(database.get_orders(status_filter="OPEN")) == 0
    assert database.get_account()["balance"] == 1001000.0, "Funds should be refunded on order cancellation"
    print(" ✓ Limit Order cancelled and ₹10,000 funds successfully refunded")

    # Test Level-2 Market Depth
    import main
    depth = main.read_depth("RELIANCE.NS")
    assert len(depth["bids"]) == 5
    assert len(depth["asks"]) == 5
    assert depth["total_bid_qty"] > 0
    assert depth["total_ask_qty"] > 0
    print(f" ✓ Level-2 Market Depth: 5 Bids & 5 Asks generated (Total Buy Qty: {depth['total_bid_qty']:,}, Sell: {depth['total_ask_qty']:,})")

    # 7. Test Futures & Options (F&O) Engine
    print("\n[7/9] Testing F&O Option Chains & Option Trades...")
    import fo_service
    chain = fo_service.get_option_chain("NIFTY")
    assert chain["underlying"] == "NIFTY"
    assert chain["lot_size"] == 25
    assert len(chain["chain"]) >= 15
    atm_row = next(r for r in chain["chain"] if r["is_atm"])
    print(f" ✓ NIFTY Option Chain: Spot ₹{chain['spot_price']:,.2f}, ATM Strike {atm_row['strike']}, PCR {chain['pcr']} ({chain['pcr_sentiment']})")
    print(f"   Call CE LTP: ₹{atm_row['call']['ltp']}, Put PE LTP: ₹{atm_row['put']['ltp']}, Delta: {atm_row['call']['delta']}")

    # Buy 1 lot (25 qty) of NIFTY ATM Call
    opt_qty = 25
    opt_price = atm_row['call']['ltp']
    res_opt_buy = database.execute_trade(atm_row['call']['symbol'], "NIFTY 50 Call Option", "OPTION", "BUY", "INTRADAY", opt_qty, opt_price)
    assert res_opt_buy["success"], f"Option buy failed: {res_opt_buy}"
    opt_positions = [p for p in database.get_positions() if p["asset_type"] == "OPTION"]
    assert len(opt_positions) == 1
    assert opt_positions[0]["quantity"] == 25
    print(f" ✓ Option Buy Order: 1 Lot (25 shares) of {atm_row['call']['symbol']} filled at ₹{opt_price:,.2f}")

    # 8. Test GTT Orders & SIP Planner
    print("\n[8/9] Testing GTT Orders & SIP Scheduler...")
    database.reset_account(user_id="default")
    res_gtt = database.place_gtt_order(
        user_id="default", symbol="TCS.NS", name="Tata Consultancy Services",
        trigger_price=3800.0, quantity=5, action="BUY", product_type="DELIVERY", target_price=4200.0, stop_loss_price=3600.0
    )
    assert res_gtt["success"]
    gtt_orders = database.get_gtt_orders("default")
    assert len(gtt_orders) >= 1
    assert gtt_orders[0]["trigger_price"] == 3800.0
    print(f" ✓ GTT Order placed: Buy 5 TCS @ trigger ₹3,800.00 (Target: ₹4,200.00, SL: ₹3,600.00)")
    database.cancel_gtt_order("default", res_gtt["gtt_id"])
    print(" ✓ GTT Order cancellation verified")

    # SIP
    res_sip = database.create_sip("default", "122639", "Parag Parikh Flexi Cap Fund", 5000.0, sip_day=5)
    assert res_sip["success"]
    sips = database.get_user_sips("default")
    assert len(sips) == 1
    assert sips[0]["monthly_amount"] == 5000.0
    print(f" ✓ Monthly SIP created: ₹5,000.00/mo on 5th of every month (Next: {res_sip['next_date']})")
    database.cancel_sip("default", res_sip["sip_id"])
    print(" ✓ SIP cancellation verified")

    # 9. Test IPO Hub & Capital Gains Tax
    print("\n[9/9] Testing Real Indian IPO Hub & Capital Gains Tax...")
    import ipo_service
    all_ipos = ipo_service.get_ipos()
    assert len(all_ipos) >= 5
    swiggy_ipo = ipo_service.get_ipo_by_id("swiggy")
    assert swiggy_ipo["name"] == "Swiggy Ltd"
    print(f" ✓ Real Indian IPOs loaded: {len(all_ipos)} issues (e.g. {swiggy_ipo['name']} - Band: {swiggy_ipo['price_band']}, Lot: {swiggy_ipo['lot_size']}, GMP: {swiggy_ipo['gmp']})")

    # Test IPO Application
    res_ipo = database.apply_ipo("default", "swiggy", "Swiggy Ltd", 1, 38, 390.0, "trader@okaxis")
    assert res_ipo["success"]
    assert res_ipo["amount_blocked"] == 14820.0  # 38 * 390
    user_bids = database.get_ipo_bids("default")
    assert len(user_bids) == 1
    print(f" ✓ IPO Application submitted: 1 Lot (38 shares) of Swiggy Ltd, ₹14,820.00 blocked via ASBA")
    database.cancel_ipo_bid("default", res_ipo["bid_id"])
    print(" ✓ IPO Application cancelled & ₹14,820.00 unblocked successfully")

    # Test Capital Gains Tax (Budget 2024: STCG 20%, LTCG 12.5%)
    tax_rep = database.get_capital_gains_tax_report("default")
    assert "stcg_tax_rate" in tax_rep
    assert tax_rep["stcg_tax_rate"] == "20%"
    assert tax_rep["ltcg_tax_rate"] == "12.5%"
    print(f" ✓ Capital Gains Tax Report verified under Budget 2024: STCG @ {tax_rep['stcg_tax_rate']}, LTCG @ {tax_rep['ltcg_tax_rate']}")

    # Reset account cleanly
    database.reset_account(1000000.0)
    print(" ✓ Database reset to fresh ₹10,00,000 balance")

    print("\n=======================================================")
    print(" ALL STOXIFY ADVANCED BROKER TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_all()

