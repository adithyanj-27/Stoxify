"""End-to-end contract checks for the request bodies that static/app.js sends.

Drives the real FastAPI route functions with real Pydantic models, so a payload
that the frontend and the API disagree on fails here instead of silently
returning HTTP 422 in the browser. Supabase is forced off (pointed at a dead
port) so a local run never touches the cloud project.

Run:  python test_api_contract.py
"""
import base64
import hashlib
import hmac
import os
import sys
import tempfile
import time

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


def _signed_token(user_id, expires, key=None):
    """Mint a token with an arbitrary expiry, optionally under a wrong key."""
    payload = f"{user_id}.{expires}"
    secret = key if key is not None else main._session_secret()
    signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload}.{base64.urlsafe_b64encode(signature).decode('ascii').rstrip('=')}"


class FakeRequest:
    """Minimal stand-in for starlette's Request (headers + query params).

    Identity is now a server-signed session token, so a logged-in stand-in must
    carry a real one. `legacy_id` deliberately sends the old `x-user-id` header
    instead, which must no longer authenticate on its own.
    """

    def __init__(self, user_id=None, legacy_id=None, query_id=None):
        self.headers = {}
        self.query_params = {"user_id": query_id} if query_id else {}
        if user_id:
            self.headers["authorization"] = f"Bearer {main.issue_session_token(user_id)}"
        if legacy_id:
            self.headers["x-user-id"] = legacy_id


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
print(" 0. Identity is a signed token, not a client-supplied id")
print("=" * 72)
# A bare `x-user-id` used to be accepted as proof of identity, which let any
# caller act as any account by changing one value. It must now do nothing.
check("a bare x-user-id header does not authenticate",
      None, main.get_user_id(FakeRequest(legacy_id="STOX-777001")))
check("a ?user_id= parameter does not authenticate",
      None, main.get_user_id(FakeRequest(query_id="STOX-777001")))
check("an issued session token authenticates",
      "STOX-777001", main.get_user_id(FakeRequest(user_id="STOX-777001")))
check("a token with a forged signature is rejected",
      None, main.verify_session_token("STOX-777001.9999999999.forged"))
check("an expired token is rejected",
      None, main.verify_session_token(_signed_token("STOX-777001", int(time.time()) - 10)))
check("a token re-signed with the wrong key is rejected",
      None, main.verify_session_token(_signed_token("STOX-777001", int(time.time()) + 600, b"wrong-key")))


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
print(" 7. Registration wizard payload (the body static/app.js now sends)")
print("=" * 72)

# Exactly the shape submitObStep5() posts: no username, no password, no PIN, but
# with the fields that used to be collected and silently dropped.
new_user_id = "STOX-777001"
created = main.api_create_user(main.CreateUserRequest(
    id=new_user_id,
    name="Prefill Tester",
    email="prefill.tester@example.test",
    phone="9333333333",
    pan="QWERT1234Z",
    dob="1996-04-11",
    age=30,
    experience="1–2 Years",
    gender="Female",
    occupation="Business",
    income="₹10L - ₹25L",
    ifsc="SBIN0001234",
    bank_name="State Bank of India",
    bank_account="11223344556",
    address_line1="Flat 701, Silver Heights",
    address_line2="Banjara Hills",
    city="Hyderabad",
    state="Telangana",
    pincode="500034"
))
user = created["user"]
check("registration succeeds without username/password/PIN", True, created["success"])
check("gender persisted", "Female", user.get("gender"))
check("occupation persisted", "Business", user.get("occupation"))
check("income persisted", "₹10L - ₹25L", user.get("income"))
check("address line 1 persisted", "Flat 701, Silver Heights", user.get("address_line1"))
check("city persisted", "Hyderabad", user.get("city"))
check("state persisted", "Telangana", user.get("state"))
check("pincode persisted", "500034", user.get("pincode"))
check("typed IFSC is kept, not derived from the bank name", "SBIN0001234", user.get("bank_ifsc"))
check("account starts with no credential", "", (user.get("pin") or ""))

# The mobile number is the account identity, so it must be unique.
try:
    main.api_create_user(main.CreateUserRequest(
        name="Second Tester", email="second@example.test", phone="9333333333",
        dob="1990-01-01", age=36))
    duplicate_phone_status = None
except HTTPException as exc:
    duplicate_phone_status = exc.status_code
check("duplicate mobile number is rejected", 400, duplicate_phone_status)

# A Demat account needs an adult applicant.
try:
    main.api_create_user(main.CreateUserRequest(
        name="Minor Tester", email="minor@example.test", phone="9444444444",
        dob="2015-01-01", age=11))
    minor_status = None
except HTTPException as exc:
    minor_status = exc.status_code
check("under-18 applicant is rejected", 400, minor_status)

# Login must not disclose who owns an identifier when no secret is supplied.
neutral = main.api_login_user(main.LoginRequest(identifier="9333333333"))
check("bare-identifier login reports no name", None, neutral.get("user"))
check("bare-identifier login asks for a credential", True, neutral.get("requires_credential"))

# ...and the credential set after activation actually works.
main.api_update_user_profile(
    main.UpdateProfileRequest(id=new_user_id, pin="5150"),
    FakeRequest(user_id=new_user_id))
logged_in = main.api_login_user(main.LoginRequest(identifier="9333333333", pin="5150"))
check("mobile + post-activation PIN logs in", True, logged_in.get("success"))
check("login returns the right account", new_user_id, logged_in.get("user", {}).get("id"))

print()
print("=" * 72)
print(f" {len(FAILURES)} failure(s)")
for name in FAILURES:
    print(f"   - {name}")
print("=" * 72)
sys.exit(1 if FAILURES else 0)
