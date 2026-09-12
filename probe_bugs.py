"""Regression probes for the logical errors found in the Stoxify audit.

Run:  python probe_bugs.py
Every probe prints EXPECT / ACTUAL. "OK" means the shipped behaviour is correct;
"BUG" means the defect is still present. Supabase is forced off so nothing
touches the network (probe 4 uses a local in-memory fake of the remote store).
"""
import os
import subprocess
import sys
import tempfile
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

os.environ["VERCEL"] = "1"

import database
import main
import market_hours
import market_service

database.DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify_probe.db")
database.SUPABASE_URL = ""
database.SUPABASE_KEY = ""
if os.path.exists(database.DB_PATH):
    os.remove(database.DB_PATH)
database._db_initialized = False
database.init_db()

U = "probe-user"
database.create_user("Probe Trader", "probe@example.test", "9000000000",
                     "ABCDE1234F", "Test Bank", "1234567890", "1234", user_id=U)
# Onboarding funds the simulated *bank*; the trading wallet is topped up by the user.
database.transfer_bank_to_wallet(U, 1000000.0, "1234")

FAILURES = []


def banner(n, title):
    print("=" * 72)
    print(f" PROBE {n} - {title}")
    print("=" * 72)


def check(name, expected, actual, note=""):
    ok = expected == actual
    print(f"[{'OK ' if ok else 'BUG'}] {name}")
    print(f"        expected: {expected}")
    print(f"        actual  : {actual}")
    if note:
        print(f"        note    : {note}")
    if not ok:
        FAILURES.append(name)
    print()


# ---------------------------------------------------------------------------
banner(1, "A BUY debits the gross value plus its statutory charges")
bal0 = round(database.get_account(U)["balance"], 2)
buy = database.execute_trade("TCS.NS", "TCS Ltd", "STOCK", "BUY", "DELIVERY",
                            10, 1000.0, user_id=U)
bal1 = round(database.get_account(U)["balance"], 2)
buy_charges = buy["charges"]["total"]
check("cash debited on BUY == gross value + buy charges",
      round(10000.0 + buy_charges, 2), round(bal0 - bal1, 2),
      f"buy charges of Rs.{buy_charges} now leave the wallet with the margin")

banner(2, "A flat round trip costs exactly the two charge sheets")
sell = database.execute_trade("TCS.NS", "TCS Ltd", "STOCK", "SELL", "DELIVERY",
                             10, 1000.0, user_id=U)
bal2 = round(database.get_account(U)["balance"], 2)
sell_charges = sell["charges"]["total"]
check("flat-price round trip leaves cash == start - (buy+sell charges)",
      round(1000000.0 - buy_charges - sell_charges, 2), bal2,
      "the charge sheet shown to the user is now real money")

banner(3, "Restore balance cannot be combined with cancel to mint cash")
database.restore_balance(U, 1000000.0)
lim = database.execute_trade("INFY.NS", "Infosys Ltd", "STOCK", "BUY", "DELIVERY",
                             5, 2100.0, order_variety="LIMIT", limit_price=2000.0,
                             user_id=U)
blocked = round(1000000.0 - round(database.get_account(U)["balance"], 2), 2)
database.restore_balance(U, 1000000.0)
cancel_res = database.cancel_order(lim["order_id"], U)
bal_after_cancel = round(database.get_account(U)["balance"], 2)
check("cancelling an order retired by 'restore' refunds nothing",
      1000000.0, bal_after_cancel,
      f"order blocked Rs.{blocked}; restore_balance() now retires resting orders "
      f"so the second refund is refused (cancel -> {cancel_res})")

banner(4, "delete_user removes the account locally and remotely")
database.restore_balance(U, 1000000.0)

# In-memory fake of the Supabase `users` table so the remote side is stateful.
remote_users = {U: {
    "id": U, "name": "Probe Trader", "email": "probe@example.test",
    "phone": "9000000000", "pan": "ABCDE1234F", "bank_name": "Test Bank",
    "bank_account": "1234567890", "pin": "1234", "balance": 1000000.0,
    "total_deposited": 1000000.0, "avatar_color": "#0EA5E9",
    "username": "probe", "password": None,
}}


def fake_supabase(method, endpoint, payload=None, params=None):
    method = method.upper()
    if endpoint.split("?")[0] != "users":
        return True
    if method == "GET":
        ident = (params or {}).get("id", "")
        key = ident.split("eq.")[-1] if ident.startswith("eq.") else None
        if key and key in remote_users:
            return [dict(remote_users[key])]
        return []
    if method in ("DELETE", "PATCH"):
        ident = (params or {}).get("id", "")
        key = ident.split("eq.")[-1] if ident.startswith("eq.") else None
        if key:
            remote_users.pop(key, None)
        else:
            remote_users.pop(U, None)
    return True


database.SUPABASE_URL = "https://example.test"
database.SUPABASE_KEY = "test-key"
database.supabase_api = fake_supabase
database.delete_user(U)
resurrected = database.get_user(U)
check("deleted user stays deleted (local row and remote row)",
      None, (resurrected or {}).get("id"),
      "delete_user() now resolves the account before removing the local row, so "
      "get_user() can no longer re-hydrate it from Supabase")
check("the remote row was actually purged", 0, len(remote_users))
database.SUPABASE_URL = ""
database.SUPABASE_KEY = ""

banner(5, "SIP dates beyond the 28th no longer crash")
for sip_day in (5, 31):
    try:
        res = database.create_sip(U, "122639", "Parag Parikh Flexi Cap", 5000.0, sip_day=sip_day)
        check(f"create_sip(sip_day={sip_day}) returns a schedule", "success",
              "success" if res.get("success") else res,
              f"next installment = {res.get('next_date')}")
    except Exception as exc:
        check(f"create_sip(sip_day={sip_day}) returns a schedule", "success",
              f"{type(exc).__name__}: {exc}")

banner(6, "Market session windows are contiguous")
real_now = market_hours.get_ist_now
IST_OFFSET = market_hours.IST


def session_at(hh, mm, weekday=2):
    """Drive the real get_market_status() with a pinned IST clock."""
    base = datetime(2026, 9, 9, hh, mm)  # Wednesday
    market_hours.get_ist_now = lambda: base.replace(tzinfo=IST_OFFSET)
    try:
        return market_hours.get_market_status()["session"]
    finally:
        market_hours.get_ist_now = real_now


check("09:05 IST -> PRE_MARKET", "PRE_MARKET", session_at(9, 5))
check("09:10 IST -> PRE_MARKET", "PRE_MARKET", session_at(9, 10),
      "the window used to stop at 09:08, so 09:08-09:14 was reported as AMO/closed")
check("09:14 IST -> PRE_MARKET", "PRE_MARKET", session_at(9, 14))
check("09:15 IST -> REGULAR", "REGULAR", session_at(9, 15))
check("15:29 IST -> REGULAR", "REGULAR", session_at(15, 29))
check("15:35 IST -> POST_MARKET", "POST_MARKET", session_at(15, 35))
print(f"        (15:20 intraday cutoff still reported) intraday_allowed at 15:25 = "
      f"{session_at(15, 25) and 'REGULAR'}")
print()

banner(7, "Cloud-synced ISO timestamps parse for the tax lot matcher")
parsed = database._parse_order_dt("2026-01-01T10:00:00.123456+00:00")
check("_parse_order_dt handles Supabase ISO stamps",
      "2026-01-01 10:00:00",
      str(parsed)[:19] if parsed else None,
      "previously returned None, so every cloud order was classified STCG")
check("_parse_order_dt still handles SQLite stamps",
      "2026-01-01 10:00:00",
      str(database._parse_order_dt("2026-01-01 10:00:00"))[:19])
check("_parse_order_dt tolerates empty values", None, database._parse_order_dt(None))

banner(8, "Peer comparison reads the dividend yield the quote publishes")
quote = market_service.get_stock_quote("TATASTEEL.NS")
peers = market_service.get_stock_peers("TATASTEEL.NS")
stale = [p for p in peers if p["div_yield"] == "0.80%"]
check("peer dividend yield is not the hard-coded 0.80% fallback",
      False, bool(stale) and quote.get("dividend_yield") != 0.8,
      "get_stock_peers() read q.get('div_yield'); quotes publish 'dividend_yield'")
print(f"        sample peers: {[(p['symbol'], p['div_yield']) for p in peers[:3]]}")
print()

banner(9, "Synthetic fallback prices are stable across processes")
snippet = ("import market_service;"
           "print(market_service._get_default_stock_quote('ZZUNKNOWN.NS')['price'])")
prices = set()
for _ in range(2):
    out = subprocess.run([sys.executable, "-c", snippet], capture_output=True,
                         text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    prices.add(out.stdout.strip().splitlines()[-1])
check("two separate interpreters agree on the fallback price", 1, len(prices),
      f"observed {sorted(prices)}; hash() is salted per interpreter, crc32 is not")

banner(10, "A resting LIMIT order actually fills when the price arrives")
database.restore_balance(U, 1000000.0)
resting = database.execute_trade("WIPRO.NS", "Wipro Ltd", "STOCK", "BUY", "DELIVERY",
                                 4, 600.0, order_variety="LIMIT", limit_price=550.0,
                                 user_id=U)
open_before = [o for o in database.get_orders(user_id=U) if o["status"] == "OPEN"]

# The price feed is what triggers the fill; pin it instead of hitting the network.
real_quote = market_service.get_stock_quote
market_service.get_stock_quote = lambda sym: {
    "symbol": sym, "price": 545.0, "change": -5.0, "change_pct": -0.9,
    "asset_type": "STOCK", "name": "Wipro Ltd"}
try:
    main.service_pending_orders(U)
finally:
    market_service.get_stock_quote = real_quote

filled = [o for o in database.get_orders(user_id=U)
          if o["symbol"] == "WIPRO.NS" and str(o["status"]).startswith("EXECUTED")]
held = [h for h in database.get_holdings(U) if h["symbol"] == "WIPRO.NS"]
check("pending order count before the price check", 1, len(open_before))
check("the limit order is no longer resting", 0,
      len([o for o in database.get_orders(user_id=U) if o["status"] == "OPEN"]),
      "resting orders used to be checked only when another order for the SAME "
      "symbol was placed, so they could rest forever")
check("the fill produced an executed order row", 1, len(filled))
check("the fill produced a holding at the market price", 545.0,
      held[0]["avg_price"] if held else None)

banner(11, "A bare symbol still matches a stored '.NS' symbol")
database.restore_balance(U, 1000000.0)
database.execute_trade("SBIN.NS", "State Bank of India", "STOCK", "BUY", "INTRADAY",
                       10, 1000.0, user_id=U)
sl = database.execute_trade("SBIN.NS", "State Bank of India", "STOCK", "SELL", "INTRADAY",
                            10, 1000.0, order_variety="STOP_LOSS", trigger_price=900.0,
                            user_id=U)
database.check_open_limit_orders("SBIN", 890.0, user_id=U)
still_pending = [o for o in database.get_orders(user_id=U) if o["status"] == "TRIGGER_PENDING"]
check("stop-loss triggered via the un-suffixed symbol", 0, len(still_pending),
      f"order created as {sl.get('status')}; check_open_limit_orders() used an exact "
      f"symbol match, so 'SBIN' never matched 'SBIN.NS'")

banner(12, "An unknown user id is not reported as fully funded")
ghost = database.get_account("no-such-user-id")
check("unknown user balance", 0.0, ghost["balance"])
check("unknown user is flagged as non-existent", False, ghost["exists"])


class _FakeRequest:
    headers = {"x-user-id": "no-such-user-id"}
    query_params = {}


guest_payload = main.read_account(_FakeRequest())
check("GET /api/account for an unknown id reports guest", True, guest_payload.get("is_guest"))
check("GET /api/account for an unknown id shows no capital", 0.0, guest_payload["balance"])

print("=" * 72)
print(f" PROBES COMPLETE - {len(FAILURES)} defect(s) still present")
for name in FAILURES:
    print(f"   - {name}")
print("=" * 72)
sys.exit(1 if FAILURES else 0)
