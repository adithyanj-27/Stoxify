"""End-to-end contract checks for the request bodies that static/app.js sends.

Drives the real FastAPI route functions with real Pydantic models, so a payload
that the frontend and the API disagree on fails here instead of silently
returning HTTP 422 in the browser. Supabase is forced off (pointed at a dead
port) so a local run never touches the cloud project.

Run:  python test_api_contract.py
"""
import os
import sys
import tempfile

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

os.environ["VERCEL"] = "1"

import database

database.DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify_contract.db")
if os.path.exists(database.DB_PATH):
    os.remove(database.DB_PATH)
database.SUPABASE_URL = ""
database.SUPABASE_KEY = ""
database._db_initialized = False
database.init_db()

from fastapi import HTTPException
import main

FAILURES = []


class FakeRequest:
    """Minimal stand-in for starlette's Request (headers + query params)."""

    def __init__(self, user_id=None):
        self.headers = {"x-user-id": user_id} if user_id else {}
        self.query_params = {}


def check(name, expected, actual, note=""):
    ok = expected == actual
    print(f"[{'OK ' if ok else 'FAIL'}] {name}")
    if not ok:
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")
        FAILURES.append(name)
    elif note:
        print(f"        {note}")


print("=" * 72)
print(" 1. Onboarding -> funding -> order placement")
print("=" * 72)
created = main.api_create_user(main.CreateUserRequest(
    name="Contract Tester", email="contract@example.test",
    phone="9111111111", username="contract_tester",
    password="Sup3rSecret!", pin="4321",
    bank_name="HDFC Bank", bank_account="123456789012"))
uid = created["user"]["id"]
req = FakeRequest(uid)
check("sign-up returns a user id", True, bool(uid), f"id={uid}")

check("fresh trading wallet starts at 0 (bank holds the capital)", 0.0,
      main.read_account(req)["balance"])

funded = main.api_upi_add_funds(
    main.UpiAddFundsRequest(amount=1000000.0, pin="4321"), req)
check("bank -> wallet transfer funds the account", 1000000.0,
      round(funded["wallet_balance"], 2))

order = main.place_order(main.OrderRequest(
    symbol="TCS.NS", name="Tata Consultancy Services Ltd", asset_type="STOCK",
    order_type="BUY", product_type="DELIVERY", quantity=10, price=1000.0,
    order_variety="MARKET"), req)
charges_total = order["charges"]["total"]
check("market BUY succeeds", True, bool(order.get("success")))
check("wallet debited by order value + charges",
      round(1000000.0 - 10000.0 - charges_total, 2),
      round(main.read_account(req)["balance"], 2), f"charges={charges_total}")

print()
print("=" * 72)
print(" 2. MF SIP - the payload static/app.js now sends")
print("=" * 72)
sip = main.api_create_sip(main.SIPRequest(
    fund_id="122639",
    fund_name="Parag Parikh Flexi Cap Fund - Direct Plan",
    monthly_amount=5000.0, sip_day=5), req)
check("POST /api/mf/sip accepted (previously HTTP 422)", True, bool(sip.get("success")),
      f"next installment = {sip.get('next_date')}")
check("SIP appears in GET /api/mf/sips", 1, len(main.api_get_sips(req)))

try:
    main.api_create_sip(main.SIPRequest(
        fund_id="122639", fund_name="X", monthly_amount=5000.0, sip_day=45), req)
    check("out-of-range sip_day is rejected", 400, None)
except HTTPException as exc:
    check("out-of-range sip_day is a 400, not a 500", 400, exc.status_code,
          f"detail={exc.detail}")

print()
print("=" * 72)
print(" 3. IPO bid - the payload static/app.js now sends")
print("=" * 72)
bid = main.api_apply_ipo(main.IPOApplyRequest(
    ipo_id="swiggy", ipo_name="Swiggy Ltd", lots=1, shares=38,
    bid_price=390.0, upi_id="trader@okhdfcbank"), req)
check("POST /api/ipo/apply accepted (previously HTTP 422)", True, bool(bid.get("success")),
      bid.get("message"))
check("blocked amount == lots x shares x price", 14820.0, round(bid["amount_blocked"], 2))
check("IPO bid appears in GET /api/ipo/applications", 1, len(main.api_get_ipo_bids(req)))

print()
print("=" * 72)
print(" 4. A resting order is serviced on the Orders poll")
print("=" * 72)
# Pin the feed so the resting/triggering conditions are deterministic and the
# test does not depend on where Wipro happens to be trading today.
real_quote = main.market_service.get_stock_quote
market_prices = {"WIPRO.NS": 600.0}
main.market_service.get_stock_quote = lambda sym: {
    "symbol": sym, "price": market_prices.get(sym.upper(), 600.0),
    "change": 0.0, "change_pct": 0.0, "asset_type": "STOCK", "name": "Wipro Ltd"}
main.market_service._CACHE.pop("quote_WIPRO.NS", None)
main.market_service._CACHE_EXPIRY.pop("quote_WIPRO.NS", None)
try:
    main.place_order(main.OrderRequest(
        symbol="WIPRO.NS", name="Wipro Ltd", asset_type="STOCK", order_type="BUY",
        product_type="DELIVERY", quantity=4, price=600.0, order_variety="LIMIT",
        limit_price=550.0), req)
    open_before = [o for o in main.read_orders(req) if o["status"] == "OPEN"]
    check("limit BUY rests while the market trades above the limit", 1, len(open_before))

    market_prices["WIPRO.NS"] = 540.0
    after = main.read_orders(req)
    check("the price drop fills it on the next Orders poll", 0,
          len([o for o in after if o["status"] == "OPEN"]),
          "previously only another order for the same symbol could trigger a fill")
    check("the fill is recorded as EXECUTED", True,
          any(o["symbol"] == "WIPRO.NS" and str(o["status"]).startswith("EXECUTED")
              for o in after))
    held = [h for h in database.get_holdings(uid) if h["symbol"] == "WIPRO.NS"]
    check("the fill produced a holding at the traded price", 540.0,
          held[0]["avg_price"] if held else None)
finally:
    main.market_service.get_stock_quote = real_quote

print()
print("=" * 72)
print(" 5. Guest / stale account never shows phantom capital")
print("=" * 72)
anon = main.read_account(FakeRequest())
check("no user id -> guest with 0 balance", (True, 0.0),
      (anon.get("is_guest"), anon.get("balance")))
stale = main.read_account(FakeRequest("ghost-12345"))
check("unknown user id -> guest with 0 balance", (True, 0.0),
      (stale.get("is_guest"), stale.get("balance")),
      "previously reported a fabricated Rs.10,00,000 balance")

print()
print("=" * 72)
print(" 6. Remaining read endpoints answer with data")
print("=" * 72)
check("market status has a session", True, "session" in main.read_market_status())
chain = main.api_option_chain("NIFTY")
check("option chain has 15 strikes", 15, len(chain.get("chain", [])))
check("portfolio is not guest for a real user", False, main.read_portfolio(req)["is_guest"])
check("positions endpoint responds", True, isinstance(main.read_positions(req), dict))
check("tax report has the 20% STCG rate", "20%", main.api_tax_report(req)["stcg_tax_rate"])
check("watchlist seeds for a new user", True, len(main.read_watchlist(req)) > 0)

print()
print("=" * 72)
print(f" {len(FAILURES)} failure(s)")
for name in FAILURES:
    print(f"   - {name}")
print("=" * 72)
sys.exit(1 if FAILURES else 0)
