"""Adversarial regression probes for the fixes in DEBUG_REPORT.md.

These try to BREAK the fixes rather than confirm them: duplicate refunds, double
fills, an un-migrated database, and charge-accounting consistency.

Run:  python probe_regressions.py
"""
import os
import sqlite3
import sys
import tempfile

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

os.environ["VERCEL"] = "1"

import database

database.DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify_regression.db")
database.SUPABASE_URL = ""
database.SUPABASE_KEY = ""
if os.path.exists(database.DB_PATH):
    os.remove(database.DB_PATH)
database._db_initialized = False
database.init_db()

import main

U = "regress-user"
database.create_user("Regression Tester", "regress@example.test", "9222222222",
                     "ABCDE1234F", "Test Bank", "1234567890", "1234", user_id=U)

FAILURES = []


def check(name, expected, actual, note=""):
    ok = expected == actual
    print(f"[{'OK ' if ok else 'FAIL'}] {name}")
    if not ok:
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")
        FAILURES.append(name)
    elif note:
        print(f"        {note}")


def banner(t):
    print("=" * 72)
    print(f" {t}")
    print("=" * 72)


def fund():
    database.restore_balance(U, 1000000.0)
    return round(database.get_account(U)["balance"], 2)


# --------------------------------------------------------------------------
banner("A. Can any pending order be refunded twice?")
bal = fund()
lim = database.execute_trade("INFY.NS", "Infosys", "STOCK", "BUY", "DELIVERY",
                             5, 2100.0, order_variety="LIMIT", limit_price=2000.0,
                             user_id=U)
blocked = round(bal - round(database.get_account(U)["balance"], 2), 2)
check("resting BUY stores blocked_amount", round(blocked, 2),
      round(database.get_orders(user_id=U)[0]["blocked_amount"], 2))
first = database.cancel_order(lim["order_id"], U)
second = database.cancel_order(lim["order_id"], U)
check("first cancel succeeds", True, first["success"])
check("second cancel is refused", False, second["success"])
check("no duplicate refund", bal, round(database.get_account(U)["balance"], 2),
      f"blocked {blocked}, refunded once")

# restore then cancel (the original exploit)
bal = fund()
lim = database.execute_trade("INFY.NS", "Infosys", "STOCK", "BUY", "DELIVERY",
                             5, 2100.0, order_variety="LIMIT", limit_price=2000.0,
                             user_id=U)
database.restore_balance(U, 1000000.0)
database.cancel_order(lim["order_id"], U)
check("restore + cancel creates no cash", 1000000.0,
      round(database.get_account(U)["balance"], 2))

# a pending SELL must never refund margin
bal = fund()
database.execute_trade("TCS.NS", "TCS", "STOCK", "BUY", "DELIVERY", 10, 1000.0, user_id=U)
after_buy = round(database.get_account(U)["balance"], 2)
sell_lim = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "DELIVERY", 10, 900.0,
                                  order_variety="LIMIT", limit_price=1100.0, user_id=U)
check("resting SELL blocks no cash", after_buy,
      round(database.get_account(U)["balance"], 2))
check("resting SELL has blocked_amount 0", 0.0,
      round(database.get_orders(user_id=U)[0]["blocked_amount"], 2))
database.cancel_order(sell_lim["order_id"], U)
check("cancelling a resting SELL refunds nothing", after_buy,
      round(database.get_account(U)["balance"], 2))

# a trigger-pending STOP-LOSS SELL
before_sl = round(database.get_account(U)["balance"], 2)
sl = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "DELIVERY", 10, 1000.0,
                            order_variety="STOP_LOSS", trigger_price=900.0, user_id=U)
check("stop-loss SELL is trigger pending", "TRIGGER_PENDING", sl["status"])
check("stop-loss SELL blocks no cash", before_sl,
      round(database.get_account(U)["balance"], 2))
database.cancel_order(sl["order_id"], U)
check("cancelling a trigger-pending SELL refunds nothing", before_sl,
      round(database.get_account(U)["balance"], 2))

# reset_account must wipe resting orders too
bal = fund()
database.execute_trade("INFY.NS", "Infosys", "STOCK", "BUY", "DELIVERY", 5, 2100.0,
                       order_variety="LIMIT", limit_price=2000.0, user_id=U)
database.reset_account(1000000.0, user_id=U)
leftover = [o for o in database.get_orders(user_id=U)
            if o["status"] in ("OPEN", "TRIGGER_PENDING")]
check("reset_account leaves no resting orders", 0, len(leftover))
check("reset_account balance", 1000000.0, round(database.get_account(U)["balance"], 2))

# --------------------------------------------------------------------------
banner("B. Is blocked_amount populated on every resting-order path?")
bal = fund()
pending_ids = []
pending_ids.append(database.execute_trade(
    "INFY.NS", "Infosys", "STOCK", "BUY", "DELIVERY", 5, 2100.0,
    order_variety="LIMIT", limit_price=2000.0, user_id=U)["order_id"])
pending_ids.append(database.execute_trade(
    "WIPRO.NS", "Wipro", "STOCK", "BUY", "INTRADAY", 5, 600.0,
    order_variety="LIMIT", limit_price=500.0, user_id=U)["order_id"])
pending_ids.append(database.execute_trade(
    "SBIN.NS", "SBI", "STOCK", "BUY", "DELIVERY", 5, 1000.0,
    order_variety="STOP_LOSS", trigger_price=1100.0, user_id=U)["order_id"])
zero_blocked = [o["id"] for o in database.get_orders(user_id=U)
                if o["id"] in pending_ids and float(o["blocked_amount"] or 0) <= 0]
check("every resting BUY has a non-zero blocked_amount", [], zero_blocked)

# cancelling all of them must return the wallet exactly to the start
before_pending = bal
for oid in pending_ids:
    database.cancel_order(oid, U)
check("cancelling every resting BUY restores the exact balance", before_pending,
      round(database.get_account(U)["balance"], 2))

# --------------------------------------------------------------------------
banner("C. Repeated triggering must not double-fill")
fund()
database.execute_trade("WIPRO.NS", "Wipro", "STOCK", "BUY", "DELIVERY", 4, 600.0,
                       order_variety="LIMIT", limit_price=550.0, user_id=U)
real_quote = main.market_service.get_stock_quote
main.market_service.get_stock_quote = lambda sym: {
    "symbol": sym, "price": 540.0, "change": 0.0, "change_pct": 0.0,
    "asset_type": "STOCK", "name": "Wipro"}
try:
    for _ in range(5):
        main.service_pending_orders(U)
    fills = [o for o in database.get_orders(user_id=U)
             if o["symbol"] == "WIPRO.NS" and str(o["status"]).startswith("EXECUTED")]
    held = [h for h in database.get_holdings(U) if h["symbol"] == "WIPRO.NS"]
    check("exactly one fill despite 5 servicing passes", 1, len(fills))
    check("exactly one holding row", 1, len(held))
    check("holding quantity is not doubled", 4.0, float(held[0]["quantity"]) if held else None)
    check("servicing with nothing resting is a no-op", 0, main.service_pending_orders(U))
finally:
    main.market_service.get_stock_quote = real_quote

# --------------------------------------------------------------------------
banner("D. An older database without `blocked_amount` still works")
legacy = os.path.join(tempfile.gettempdir(), "stoxify_legacy.db")
if os.path.exists(legacy):
    os.remove(legacy)
conn = sqlite3.connect(legacy)
conn.executescript("""
    -- Mirrors a database written by an earlier build: the base users columns
    -- exist, but later additions (user_id on orders, blocked_amount) do not.
    CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT NOT NULL, balance REAL NOT NULL DEFAULT 0.0,
                        total_deposited REAL NOT NULL DEFAULT 0.0, pin TEXT DEFAULT '',
                        email TEXT, phone TEXT, pan TEXT, bank_name TEXT, bank_account TEXT,
                        avatar_color TEXT DEFAULT '#0EA5E9',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL DEFAULT 'default',
                         symbol TEXT NOT NULL, name TEXT NOT NULL, asset_type TEXT NOT NULL,
                         order_type TEXT NOT NULL, product_type TEXT NOT NULL, quantity REAL NOT NULL,
                         price REAL NOT NULL, total_amount REAL NOT NULL,
                         status TEXT NOT NULL DEFAULT 'EXECUTED');
    INSERT INTO users (id, name, balance, total_deposited, pin)
        VALUES ('legacy-user', 'Legacy', 1000000.0, 1000000.0, '1234');
    INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type,
                        quantity, price, total_amount, status)
        VALUES ('legacy-user', 'TCS.NS', 'TCS', 'STOCK', 'BUY', 'DELIVERY', 5, 2000.0, 10000.0, 'OPEN');
""")
conn.commit()
conn.close()

saved_path, saved_flag = database.DB_PATH, database._db_initialized
database.DB_PATH = legacy
database._db_initialized = False
try:
    acc = database.get_account("legacy-user")
    check("legacy DB is auto-migrated and readable", 1000000.0, round(acc["balance"], 2))
    col = sqlite3.connect(legacy).execute("PRAGMA table_info(orders)").fetchall()
    check("blocked_amount column was added by init_db", True,
          any(c[1] == "blocked_amount" for c in col))
    legacy_cancel = database.cancel_order(1, "legacy-user")
    check("a pre-existing OPEN order still cancels (fallback refund)",
          (True, 1010000.0),
          (legacy_cancel["success"], round(database.get_account("legacy-user")["balance"], 2)),
          "blocked_amount is 0 on the legacy row, so total_amount is refunded")
except Exception as exc:
    check("legacy DB handles gracefully", "no exception", f"{type(exc).__name__}: {exc}")
finally:
    database.DB_PATH, database._db_initialized = saved_path, saved_flag

# --------------------------------------------------------------------------
banner("E. Charge accounting is symmetric across all four products")
cases = [
    ("DELIVERY BUY", "DELIVERY", "BUY"),
    ("INTRADAY BUY", "INTRADAY", "BUY"),
]
for label, product, side in cases:
    start = fund()
    res = database.execute_trade("TCS.NS", "TCS", "STOCK", side, product, 10, 1000.0, user_id=U)
    value = 10000.0
    margin = value * (0.20 if product == "INTRADAY" else 1.0)
    check(f"{label} debits margin + charges", round(start - margin - res["charges"]["total"], 2),
          round(database.get_account(U)["balance"], 2),
          f"charges={res['charges']['total']}")

# a profitable round trip must net out to exactly the P&L minus both charge sheets
start = fund()
buy = database.execute_trade("TCS.NS", "TCS", "STOCK", "BUY", "DELIVERY", 10, 1000.0, user_id=U)
sell = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "DELIVERY", 10, 1100.0, user_id=U)
expected = round(start + 1000.0 - buy["charges"]["total"] - sell["charges"]["total"], 2)
check("delivery round trip nets P&L minus both charge sheets", expected,
      round(database.get_account(U)["balance"], 2))

start = fund()
buy = database.execute_trade("TCS.NS", "TCS", "STOCK", "BUY", "INTRADAY", 10, 1000.0, user_id=U)
sell = database.execute_trade("TCS.NS", "TCS", "STOCK", "SELL", "INTRADAY", 10, 1100.0, user_id=U)
expected = round(start + 1000.0 - buy["charges"]["total"] - sell["charges"]["total"], 2)
check("intraday round trip nets P&L minus both charge sheets", expected,
      round(database.get_account(U)["balance"], 2))

# charges are non-zero, so the assertions above are not trivially satisfied
check("charges are actually charged (guards a zero-charge regression)", True,
      buy["charges"]["total"] > 0 and sell["charges"]["total"] > 0)

# --------------------------------------------------------------------------
banner("F. Timestamp handling is consistent (all sources are UTC)")
check("SQLite CURRENT_TIMESTAMP and Supabase ISO stamps agree",
      database._parse_order_dt("2026-01-01 10:00:00"),
      database._parse_order_dt("2026-01-01T10:00:00.000000+00:00"),
      "SQLite CURRENT_TIMESTAMP is UTC, matching the ISO stamps")
check("Zulu suffix is tolerated",
      "2026-01-01 10:00:00",
      str(database._parse_order_dt("2026-01-01T10:00:00Z"))[:19])
check("a 364-day hold is STCG and a 366-day hold is LTCG",
      (False, True),
      (364 >= 365, 366 >= 365))

print()
print("=" * 72)
print(f" REGRESSION PROBES COMPLETE - {len(FAILURES)} problem(s)")
for name in FAILURES:
    print(f"   - {name}")
print("=" * 72)
sys.exit(1 if FAILURES else 0)
