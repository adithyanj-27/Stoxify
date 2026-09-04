import os
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from database import (
    init_db, get_account, get_holdings, get_positions, execute_trade, 
    exit_position, cancel_order, check_open_limit_orders,
    get_orders, get_watchlist, add_to_watchlist, remove_from_watchlist,
    deposit_funds, reset_account, create_user, get_user, list_users
)
import market_service
import market_hours
from datetime import datetime

app = FastAPI(title="Stoxify", description="BrokeAhh - Stock & Mutual Fund Broker Platform", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(PUBLIC_DIR):
    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

@app.middleware("http")
async def normalize_vercel_path(request: Request, call_next):
    orig = request.headers.get("x-vercel-original-url")
    if orig:
        clean_path = orig.split("?")[0]
        request.scope["path"] = clean_path
    else:
        path = request.scope.get("path", "")
        if path.startswith("/api/index.py"):
            sub = path.replace("/api/index.py", "", 1)
            request.scope["path"] = sub if sub.startswith("/") else ("/" + sub)
        elif path.startswith("/index.py"):
            sub = path.replace("/index.py", "", 1)
            request.scope["path"] = sub if sub.startswith("/") else ("/" + sub)
    return await call_next(request)

@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception:
        pass

def get_user_id(request: Request) -> str:
    return request.headers.get("x-user-id") or request.query_params.get("user_id") or "default"

@app.get("/favicon.ico")
def favicon():
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#080D14"/><defs><linearGradient id="gC" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#38BDF8"/><stop offset="100%" stop-color="#0EA5E9"/></linearGradient><linearGradient id="gE" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#34D399"/><stop offset="100%" stop-color="#10B981"/></linearGradient></defs><circle cx="16" cy="16" r="12" stroke="url(#gC)" stroke-width="2.4" fill="none"/><path d="M10 20L15 15L18.5 17.5L23.5 10.5" stroke="url(#gE)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M19 10.5H23.5V15" stroke="url(#gE)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="23.5" cy="10.5" r="1.5" fill="#38BDF8"/></svg>"""
    return Response(content=svg_icon, media_type="image/svg+xml")

@app.get("/")
def read_root():
    for candidate in [
        os.path.join(PUBLIC_DIR, "index.html"),
        os.path.join(STATIC_DIR, "index.html"),
        os.path.join(BASE_DIR, "index.html")
    ]:
        if os.path.exists(candidate):
            return FileResponse(candidate)
    return Response(content="<h1>Stoxify is Online</h1>", media_type="text/html")

@app.get("/static/style.css")
@app.get("/style.css")
def get_style():
    for candidate in [
        os.path.join(STATIC_DIR, "style.css"),
        os.path.join(PUBLIC_DIR, "style.css"),
        os.path.join(BASE_DIR, "style.css")
    ]:
        if os.path.exists(candidate):
            return FileResponse(candidate, media_type="text/css")
    return Response(content="/* style not found */", media_type="text/css")

@app.get("/static/app.js")
@app.get("/app.js")
def get_script():
    for candidate in [
        os.path.join(STATIC_DIR, "app.js"),
        os.path.join(PUBLIC_DIR, "app.js"),
        os.path.join(BASE_DIR, "app.js")
    ]:
        if os.path.exists(candidate):
            return FileResponse(candidate, media_type="application/javascript")
    return Response(content="// script not found", media_type="application/javascript")

@app.get("/manifest.json")
@app.get("/manifest.webmanifest")
def get_manifest():
    for candidate in [
        os.path.join(STATIC_DIR, "manifest.json"),
        os.path.join(PUBLIC_DIR, "manifest.json"),
        os.path.join(BASE_DIR, "manifest.json")
    ]:
        if os.path.exists(candidate):
            return FileResponse(candidate, media_type="application/manifest+json")
    return Response(content="{}", media_type="application/manifest+json")

@app.get("/sw.js")
def get_sw():
    for candidate in [
        os.path.join(STATIC_DIR, "sw.js"),
        os.path.join(PUBLIC_DIR, "sw.js"),
        os.path.join(BASE_DIR, "sw.js")
    ]:
        if os.path.exists(candidate):
            return FileResponse(candidate, media_type="application/javascript")
    return Response(content="// sw not found", media_type="application/javascript")

# --- User Profile Endpoints (Simulated Groww Onboarding) ---
class CreateUserRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    pan: Optional[str] = None
    bank_name: Optional[str] = "HDFC Bank"
    bank_account: Optional[str] = "50100234567890"
    pin: Optional[str] = "1234"

@app.post("/api/user/create")
def api_create_user(req: CreateUserRequest):
    if not req.name or not req.name.strip():
        raise HTTPException(status_code=400, detail="Legal Name is required")
    u = create_user(
        name=req.name.strip(),
        email=req.email,
        phone=req.phone,
        pan=req.pan,
        bank_name=req.bank_name or "HDFC Bank",
        bank_account=req.bank_account or "50100234567890",
        pin=req.pin or "1234"
    )
    return {"success": True, "user": u}

@app.get("/api/user/current")
def api_get_current_user(request: Request):
    uid = get_user_id(request)
    u = get_user(uid)
    if not u:
        u = get_user("default")
    return u

@app.get("/api/user/list")
def api_list_users():
    return list_users()

# --- Market Status & Simulation Controls ---
@app.get("/api/market-status")
@app.get("/market-status")
def read_market_status():
    return market_hours.get_market_status()

class SimulationToggleRequest(BaseModel):
    enabled: bool

@app.post("/api/market-status/toggle-simulation")
@app.post("/market-status/toggle-simulation")
def toggle_simulation(req: SimulationToggleRequest):
    market_hours.set_simulation_mode(req.enabled)
    return market_hours.get_market_status()

# --- Financial Data & Quote Endpoints ---
@app.get("/api/account")
@app.get("/account")
def read_account(request: Request):
    uid = get_user_id(request)
    return get_account(uid)

@app.get("/api/indices")
@app.get("/indices")
def read_indices():
    return market_service.get_indices()

@app.get("/api/explore")
def read_explore():
    return market_service.get_explore_data()

@app.get("/api/search")
@app.get("/search")
def search(q: str = Query(..., min_length=1)):
    return market_service.search_market(q)

@app.get("/api/quote")
@app.get("/quote")
def read_quote(symbol: str, asset_type: str = "STOCK"):
    if asset_type.upper() == "MUTUAL_FUND":
        return market_service.get_mutual_fund_quote(symbol)
    return market_service.get_stock_quote(symbol)

@app.get("/api/depth")
@app.get("/depth")
def read_depth(symbol: str):
    quote = market_service.get_stock_quote(symbol)
    ltp = float(quote.get("price", 100.0))
    import random
    bids = []
    asks = []
    tot_bid = 0
    tot_ask = 0

    for i in range(1, 6):
        bp = round(ltp * (1.0 - (i * 0.0008)), 2)
        bq = random.randint(250, 4500)
        bo = random.randint(2, 22)
        tot_bid += bq
        bids.append({"orders": bo, "quantity": bq, "price": bp})

        ap = round(ltp * (1.0 + (i * 0.0008)), 2)
        aq = random.randint(250, 4500)
        ao = random.randint(2, 22)
        tot_ask += aq
        asks.append({"price": ap, "quantity": aq, "orders": ao})

    tot = tot_bid + tot_ask
    b_pct = round((tot_bid / tot) * 100, 1) if tot > 0 else 50.0
    a_pct = round(100.0 - b_pct, 1)

    return {
        "symbol": symbol,
        "ltp": ltp,
        "bids": bids,
        "asks": asks,
        "total_bid_qty": tot_bid,
        "total_ask_qty": tot_ask,
        "total_buy_qty": tot_bid,
        "total_sell_qty": tot_ask,
        "buy_pct": b_pct,
        "sell_pct": a_pct
    }

@app.get("/api/history")
@app.get("/history")
def read_history(symbol: str, range: str = "1M"):
    return market_service.get_stock_history(symbol, range)

@app.get("/api/portfolio")
@app.get("/portfolio")
def read_portfolio(request: Request):
    uid = get_user_id(request)
    account = get_account(uid)
    raw_holdings = get_holdings(uid)

    holdings_detail = []
    total_current_val = 0.0
    total_invested_val = 0.0
    total_day_pnl = 0.0

    for h in raw_holdings:
        if h["asset_type"] == "MUTUAL_FUND":
            quote = market_service.get_mutual_fund_quote(h["symbol"])
        else:
            quote = market_service.get_stock_quote(h["symbol"])

        cur_price = quote.get("price", h["avg_price"])
        chg = quote.get("change", 0.0)
        chg_pct = quote.get("change_pct", 0.0)

        inv_val = round(h["quantity"] * h["avg_price"], 2)
        cur_val = round(h["quantity"] * cur_price, 2)
        pnl = round(cur_val - inv_val, 2)
        pnl_pct = round((pnl / inv_val) * 100, 2) if inv_val > 0 else 0.0
        day_pnl = round(h["quantity"] * chg, 2)

        total_invested_val += inv_val
        total_current_val += cur_val
        total_day_pnl += day_pnl

        holdings_detail.append({
            "symbol": h["symbol"],
            "name": h["name"],
            "asset_type": h["asset_type"],
            "quantity": h["quantity"],
            "avg_price": h["avg_price"],
            "current_price": cur_price,
            "invested_value": inv_val,
            "current_value": cur_val,
            "total_pnl": pnl,
            "total_pnl_pct": pnl_pct,
            "today_pnl": day_pnl,
            "today_pnl_pct": chg_pct,
            "updated_at": h["updated_at"]
        })

    net_worth = round(account["balance"] + total_current_val, 2)
    total_pnl = round(total_current_val - total_invested_val, 2)
    total_pnl_pct = round((total_pnl / total_invested_val) * 100, 2) if total_invested_val > 0 else 0.0
    day_pnl_pct = round((total_day_pnl / total_current_val) * 100, 2) if total_current_val > 0 else 0.0

    return {
        "balance": account["balance"],
        "invested_value": round(total_invested_val, 2),
        "current_value": round(total_current_val, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "today_pnl": round(total_day_pnl, 2),
        "today_pnl_pct": round(day_pnl_pct, 2),
        "net_worth": net_worth,
        "holdings": holdings_detail
    }

@app.get("/api/positions")
def read_positions(request: Request):
    uid = get_user_id(request)
    raw_positions = get_positions(uid)
    positions_detail = []
    total_unrealized_pnl = 0.0
    total_margin_used = 0.0

    for p in raw_positions:
        quote = market_service.get_stock_quote(p["symbol"])
        cur_price = quote.get("price", p["avg_price"])
        unrealized = round((cur_price - p["avg_price"]) * p["quantity"], 2)
        unrealized_pct = round(((cur_price - p["avg_price"]) / p["avg_price"]) * 100, 2) if p["avg_price"] > 0 else 0.0

        total_unrealized_pnl += unrealized
        total_margin_used += p["margin_used"]

        positions_detail.append({
            "symbol": p["symbol"],
            "name": p["name"],
            "asset_type": p["asset_type"],
            "quantity": p["quantity"],
            "avg_price": p["avg_price"],
            "current_price": cur_price,
            "margin_used": p["margin_used"],
            "product_type": p["product_type"],
            "unrealized_pnl": unrealized,
            "unrealized_pnl_pct": unrealized_pct,
            "updated_at": p["updated_at"]
        })

    return {
        "positions": positions_detail,
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "total_margin_used": round(total_margin_used, 2)
    }

class ExitPositionRequest(BaseModel):
    symbol: str

@app.post("/api/position/exit")
@app.post("/position/exit")
def exit_single_position(req: ExitPositionRequest, request: Request):
    uid = get_user_id(request)
    quote = market_service.get_stock_quote(req.symbol)
    res = exit_position(req.symbol, quote["price"], user_id=uid)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to exit position"))
    return res

@app.post("/api/position/exit-all")
@app.post("/position/exit-all")
def exit_all_positions(request: Request):
    uid = get_user_id(request)
    raw_positions = get_positions(uid)
    exited = []
    for pos in raw_positions:
        quote = market_service.get_stock_quote(pos["symbol"])
        r = exit_position(pos["symbol"], quote["price"], user_id=uid)
        if r.get("success"):
            exited.append(pos["symbol"])
    return {"status": "success", "exited_count": len(exited), "symbols": exited}

class OrderRequest(BaseModel):
    symbol: str
    name: str
    asset_type: str = "STOCK"
    order_type: str
    product_type: str = "DELIVERY"
    quantity: float
    price: float
    order_variety: str = "MARKET"
    limit_price: Optional[float] = None

@app.post("/api/order")
@app.post("/order")
def place_order(order: OrderRequest, request: Request):
    uid = get_user_id(request)
    if order.quantity <= 0 or order.price <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity or price")

    is_allowed, order_tag, timing_msg = market_hours.validate_order_timing(order.product_type)
    if not is_allowed:
        raise HTTPException(status_code=400, detail=timing_msg)

    exec_price = order.price
    if order.order_variety.upper() == "MARKET" and order.asset_type.upper() == "STOCK":
        try:
            live_q = market_service.get_stock_quote(order.symbol)
            if live_q.get("price"):
                exec_price = live_q["price"]
        except Exception:
            pass

    result = execute_trade(
        symbol=order.symbol,
        name=order.name,
        asset_type=order.asset_type,
        order_type=order.order_type,
        product_type=order.product_type,
        quantity=order.quantity,
        price=exec_price,
        order_variety=order.order_variety,
        limit_price=order.limit_price,
        order_tag=order_tag,
        user_id=uid
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Transaction failed"))

    try:
        check_open_limit_orders(order.symbol, exec_price, user_id=uid)
    except Exception:
        pass

    return result

class CancelOrderRequest(BaseModel):
    order_id: int

@app.post("/api/order/cancel")
@app.post("/order/cancel")
def cancel_single_order(req: CancelOrderRequest, request: Request):
    uid = get_user_id(request)
    res = cancel_order(req.order_id, user_id=uid)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to cancel order"))
    return res

@app.get("/api/orders")
def read_orders(request: Request, limit: int = 100, status: Optional[str] = None):
    uid = get_user_id(request)
    return get_orders(limit=limit, status_filter=status, user_id=uid)

@app.get("/api/watchlist")
def read_watchlist(request: Request):
    uid = get_user_id(request)
    items = get_watchlist(uid)
    results = []
    for item in items:
        if item["asset_type"] == "MUTUAL_FUND":
            quote = market_service.get_mutual_fund_quote(item["symbol"])
        else:
            quote = market_service.get_stock_quote(item["symbol"])

        results.append({
            "symbol": item["symbol"],
            "name": item["name"],
            "asset_type": item["asset_type"],
            "price": quote["price"],
            "change": quote["change"],
            "change_pct": quote["change_pct"]
        })
    return results

class WatchlistRequest(BaseModel):
    symbol: str
    name: str
    asset_type: str = "STOCK"

@app.post("/api/watchlist")
@app.post("/watchlist")
def add_watchlist(item: WatchlistRequest, request: Request):
    uid = get_user_id(request)
    add_to_watchlist(item.symbol, item.name, item.asset_type, user_id=uid)
    return {"status": "success"}

@app.delete("/api/watchlist/{symbol}")
@app.delete("/watchlist/{symbol}")
def delete_watchlist(symbol: str, request: Request):
    uid = get_user_id(request)
    remove_from_watchlist(symbol, user_id=uid)
    return {"status": "success"}

class DepositRequest(BaseModel):
    amount: float

@app.post("/api/account/deposit")
@app.post("/account/deposit")
def deposit(req: DepositRequest, request: Request):
    uid = get_user_id(request)
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive")
    new_balance = deposit_funds(req.amount, user_id=uid)
    return {"status": "success", "new_balance": new_balance}

@app.post("/api/account/reset")
@app.post("/account/reset")
def reset(request: Request):
    uid = get_user_id(request)
    reset_account(1000000.0, user_id=uid)
    return {"status": "success", "message": "Account balance reset to ₹10,00,000"}

# --- Single Page Application (SPA) Deep-Linking Browser Routes ---
@app.get("/explore")
@app.get("/holdings")
@app.get("/positions")
@app.get("/orders")
@app.get("/watchlist")
@app.get("/onboarding")
@app.get("/login")
@app.get("/stock/{symbol}")
@app.get("/mf/{symbol}")
def get_spa_page(symbol: Optional[str] = None):
    return read_root()

# Catch-all fallback for any other deep link (so browser refreshes never 404)
@app.get("/{full_path:path}")
def catch_all_spa(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return read_root()
