"""Focused regression checks for inventory, pending orders, and order history."""
import os
import tempfile

os.environ["VERCEL"] = "1"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

import database

database.DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify_trade_lifecycle_test.db")
database.SUPABASE_URL = ""
database.SUPABASE_KEY = ""
if os.path.exists(database.DB_PATH):
    os.remove(database.DB_PATH)
database._db_initialized = False
database.init_db()

USER = "trade-test"
database.create_user("Lifecycle Tester", "life@example.test", "9999999999", "ABCDE1234F", "Test Bank", "1234567890", "1234", user_id=USER)

assert database.execute_trade("TCS.NS", "TCS", "STOCK", "BUY", "DELIVERY", 10, 1000, user_id=USER)["success"]

# A pending sell reserves the shares, so a second sell cannot overcommit them.
first = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "DELIVERY", 10, 900, order_variety="LIMIT", limit_price=1100, user_id=USER)
assert first["success"] and first["status"] == "OPEN"
second = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "DELIVERY", 1, 1000, user_id=USER)
assert not second["success"]

# Cancelling releases the reservation and leaves an auditable order-history row.
assert database.cancel_order(first["order_id"], USER)["success"]
sold = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "DELIVERY", 10, 1100, user_id=USER)
assert sold["success"]
assert not database.get_holdings(USER)
orders = database.get_orders(user_id=USER)
assert any(o["status"] == "CANCELLED" for o in orders)
assert any(o["order_type"] == "SELL" and str(o["status"]).startswith("EXECUTED") for o in orders)

# Trigger-pending stop losses are cancellable.
assert database.execute_trade("INFY.NS", "Infosys", "STOCK", "BUY", "DELIVERY", 2, 1000, user_id=USER)["success"]
sl = database.execute_trade("INFY.NS", "Infosys", "STOCK", "SELL", "DELIVERY", 2, 1000, order_variety="STOP_LOSS", trigger_price=900, user_id=USER)
assert sl["success"] and sl["status"] == "TRIGGER_PENDING"
assert database.cancel_order(sl["order_id"], USER)["success"]

print("trade lifecycle checks passed")
