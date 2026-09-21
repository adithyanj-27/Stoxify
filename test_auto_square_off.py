import os
import sys
import tempfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
os.environ["VERCEL"] = "1"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

import database
import market_hours
import main


# Use clean temporary database for testing
database.DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify_auto_sq_test.db")
database.SUPABASE_URL = ""
database.SUPABASE_KEY = ""
if os.path.exists(database.DB_PATH):
    os.remove(database.DB_PATH)
database._db_initialized = False
database.init_db()

import uuid

uid_suffix = uuid.uuid4().hex[:6]
USER = f"sqoff-{uid_suffix}"
database.create_user("Square-off Tester", f"sqoff_{uid_suffix}@example.test", "9999999991", "ABCDE1234F", "Test Bank", "1234567890", "1234", user_id=USER)
assert database.transfer_bank_to_wallet(USER, 1000000.0, "1234")["success"]

init_balance = database.get_account(USER)["balance"]
print(f"Initial wallet balance: Rs. {init_balance:,.2f}")

# 1. Place an Intraday Buy order (5x leverage applied: 20% margin)
buy_res = database.execute_trade(
    symbol="RELIANCE.NS",
    name="Reliance Industries",
    asset_type="STOCK",
    order_type="BUY",
    product_type="INTRADAY",
    quantity=10,
    price=2500.0,
    user_id=USER
)
assert buy_res["success"], f"Buy failed: {buy_res}"
positions = database.get_positions(USER)
assert len(positions) == 1, f"Expected 1 intraday position, got {positions}"
assert positions[0]["symbol"] == "RELIANCE.NS"
assert positions[0]["quantity"] == 10
print(f"[OK] Intraday position opened: {positions[0]['quantity']} shares of {positions[0]['symbol']} (Margin used: Rs. {positions[0]['margin_used']})")

# 2. Place a pending Intraday Limit Buy order
limit_res = database.execute_trade(
    symbol="INFY.NS",
    name="Infosys",
    asset_type="STOCK",
    order_type="BUY",
    product_type="INTRADAY",
    quantity=5,
    price=1500.0,
    order_variety="LIMIT",
    limit_price=1400.0, # below market -> pending
    user_id=USER
)
assert limit_res["success"]
print("limit_res:", limit_res)
orders = database.get_orders(user_id=USER)
print("orders:", orders)
assert any(o["symbol"] == "INFY.NS" and o["status"] == "OPEN" for o in orders)
print("[OK] Pending intraday limit order placed (status: OPEN)")

# 3. Trigger auto square-off
sq_res = database.auto_square_off_intraday(user_id=USER)
print(f"Auto square-off result: {sq_res}")
assert sq_res["success"]
assert sq_res["squared_off_positions_count"] == 1
assert sq_res["cancelled_orders_count"] == 1

# 4. Verify position is closed
rem_positions = database.get_positions(USER)
assert len(rem_positions) == 0, f"Expected 0 positions after auto square-off, found {rem_positions}"
print("[OK] Open intraday position successfully squared off (0 positions remaining)")

# 5. Verify pending limit order was cancelled
orders_after = database.get_orders(user_id=USER)
infy_order = next(o for o in orders_after if o["symbol"] == "INFY.NS")
assert infy_order["status"] == "CANCELLED", f"Expected CANCELLED, got {infy_order['status']}"
print("[OK] Pending intraday order successfully cancelled (status: CANCELLED)")

# 6. Verify executed auto square-off order exists in order history
sq_orders = [o for o in orders_after if o["symbol"] == "RELIANCE.NS" and o["order_type"] == "SELL"]
assert len(sq_orders) == 1
assert sq_orders[0]["order_tag"] == "AUTO_SQUARE_OFF"
assert str(sq_orders[0]["status"]).startswith("EXECUTED")
print(f"[OK] Auto square-off SELL order recorded in history with tag '{sq_orders[0]['order_tag']}'")

# 7. Check wallet transaction description
tx_data = database.get_wallet_transactions(USER)
txs = tx_data.get("transactions", []) if isinstance(tx_data, dict) else tx_data
sq_tx = next((t for t in txs if "Auto Square-off" in t.get("title", "")), None)
assert sq_tx is not None, f"Expected Auto Square-off transaction, found {txs}"
print(f"[OK] Wallet transaction recorded: '{sq_tx['title']}' - '{sq_tx['description']}'")

# 8. Verify idempotency: second run is a clean no-op
repeat_res = database.auto_square_off_intraday(user_id=USER)
assert repeat_res["squared_off_positions_count"] == 0
assert repeat_res["cancelled_orders_count"] == 0
print("[OK] Idempotent: repeated auto square-off is a clean no-op")

# 9. Verify market_hours helper
assert market_hours.is_intraday_auto_square_off_due(ignore_simulation=True) in (True, False)
print("[OK] market_hours.is_intraday_auto_square_off_due function works")

print("\nALL INTRADAY AUTO SQUARE-OFF CHECKS PASSED!")
