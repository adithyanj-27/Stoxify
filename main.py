import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from database import (
    init_db, get_account, get_holdings, get_positions, execute_trade, 
    exit_position, cancel_order, check_open_limit_orders,
    get_orders, get_watchlist, add_to_watchlist, remove_from_watchlist,
    deposit_funds, reset_account
)
import market_service
import market_hours
from datetime import datetime

app = FastAPI(title="BrokeAhh", description="BrokeAhh - Stock & Mutual Fund Broker Platform", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(PUBLIC_DIR):
    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

@app.middleware("http")
async def normalize_vercel_path(request, call_next):
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

@app.get("/favicon.ico")
def favicon():
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00D09C"/><stop offset="100%" stop-color="#FF6B00"/></linearGradient></defs><rect width="32" height="32" rx="8" fill="#151922"/><path d="M6 22L14 14L19 19L26 8" stroke="url(#g)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>"""
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
    return Response(content="<h1>BrokeAhh is Online</h1>", media_type="text/html")

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

@app.get("/api/account")
@app.get("/account")
def read_account():
    return get_account()

@app.get("/api/indices")
@app.get("/indices")
def read_indices():
    return market_service.get_indices()

@app.get("/api/explore")
@app.get("/explore")
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
    buy_pct = round((tot_bid / tot) * 100, 1) if tot else 50.0
    sell_pct = round(100.0 - buy_pct, 1)

    return {
        "symbol": quote["symbol"],
        "price": ltp,
        "bids": bids,
        "asks": asks,
        "total_bid_qty": tot_bid,
        "total_ask_qty": tot_ask,
        "buy_pct": buy_pct,
        "sell_pct": sell_pct
    }

@app.get("/api/history")
@app.get("/history")
def read_history(symbol: str, asset_type: str = "STOCK", timeframe: str = "1D"):
    if asset_type.upper() == "MUTUAL_FUND":
        return market_service.get_mf_chart(symbol, timeframe)
    return market_service.get_stock_chart(symbol, timeframe)

@app.get("/api/portfolio")
@app.get("/portfolio")
def read_portfolio():
    account = get_account()
    raw_holdings = get_holdings()

    total_invested = 0.0
    total_current = 0.0
    day_returns = 0.0
    holdings_detail = []

    for h in raw_holdings:
        symbol = h["symbol"]
        asset_type = h["asset_type"]
        qty = h["quantity"]
        avg_price = h["avg_price"]
        invested_amt = round(qty * avg_price, 2)
        total_invested += invested_amt

        if asset_type == "MUTUAL_FUND":
            quote = market_service.get_mutual_fund_quote(symbol)
        else:
            quote = market_service.get_stock_quote(symbol)

        current_price = quote["price"]
        change = quote["change"]
        change_pct = quote["change_pct"]

        current_val = round(qty * current_price, 2)
        total_current += current_val

        total_pnl = round(current_val - invested_amt, 2)
        total_pnl_pct = round((total_pnl / invested_amt) * 100, 2) if invested_amt > 0 else 0.0

        today_pnl = round(qty * change, 2)
        day_returns += today_pnl

        holdings_detail.append({
            "symbol": symbol,
            "name": h["name"] or quote["name"],
            "asset_type": asset_type,
            "quantity": qty,
            "avg_price": avg_price,
            "current_price": current_price,
            "invested_amount": invested_amt,
            "current_value": current_val,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "today_pnl": today_pnl,
            "change_pct": change_pct
        })

    total_invested = round(total_invested, 2)
    total_current = round(total_current, 2)
    day_returns = round(day_returns, 2)
    total_returns = round(total_current - total_invested, 2)
    total_returns_pct = round((total_returns / total_invested) * 100, 2) if total_invested > 0 else 0.0

    prev_val = total_current - day_returns
    day_returns_pct = round((day_returns / prev_val) * 100, 2) if prev_val > 0 else 0.0
    total_portfolio_value = round(account["balance"] + total_current, 2)

    return {
        "balance": account["balance"],
        "total_portfolio_value": total_portfolio_value,
        "invested_amount": total_invested,
        "current_value": total_current,
        "total_returns": total_returns,
        "total_returns_pct": total_returns_pct,
        "day_returns": day_returns,
        "day_returns_pct": day_returns_pct,
        "holdings": holdings_detail
    }

@app.get("/api/positions")
@app.get("/positions")
def read_positions():
    raw_positions = get_positions()
    positions_detail = []
    total_unrealized_pnl = 0.0
    total_margin_used = 0.0

    for pos in raw_positions:
        symbol = pos["symbol"]
        quote = market_service.get_stock_quote(symbol)
        curr_p = quote["price"]
        qty = pos["quantity"]
        avg_p = pos["avg_price"]
        margin = pos["margin_used"]
        total_margin_used += margin

        unrealized_pnl = round((curr_p - avg_p) * qty, 2)
        total_unrealized_pnl += unrealized_pnl
        unrealized_pnl_pct = round(((curr_p - avg_p) / avg_p) * 100, 2) if avg_p else 0.0

        positions_detail.append({
            "symbol": symbol,
            "name": pos["name"] or quote["name"],
            "asset_type": pos["asset_type"],
            "quantity": qty,
            "avg_price": avg_p,
            "current_price": curr_p,
            "margin_used": margin,
            "product_type": "INTRADAY",
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct
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
def exit_single_position(req: ExitPositionRequest):
    quote = market_service.get_stock_quote(req.symbol)
    res = exit_position(req.symbol, quote["price"])
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to exit position"))
    return res

@app.post("/api/position/exit-all")
@app.post("/position/exit-all")
def exit_all_positions():
    raw_positions = get_positions()
    exited = []
    for pos in raw_positions:
        quote = market_service.get_stock_quote(pos["symbol"])
        r = exit_position(pos["symbol"], quote["price"])
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
def place_order(order: OrderRequest):
    if order.quantity <= 0 or order.price <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity or price")

    # Validate market timing rules (Intraday restricted to market hours, Delivery allowed as AMO)
    is_allowed, order_tag, timing_msg = market_hours.validate_order_timing(order.product_type)
    if not is_allowed:
        raise HTTPException(status_code=400, detail=timing_msg)

    # For market orders on stocks, use the latest real live quote
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
        order_tag=order_tag
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Transaction failed"))

    # Also evaluate any pending open limit orders for this symbol
    try:
        check_open_limit_orders(order.symbol, exec_price)
    except Exception:
        pass

    return result

class CancelOrderRequest(BaseModel):
    order_id: int

@app.post("/api/order/cancel")
@app.post("/order/cancel")
def cancel_single_order(req: CancelOrderRequest):
    res = cancel_order(req.order_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to cancel order"))
    return res

@app.get("/api/orders")
@app.get("/orders")
def read_orders(limit: int = 100, status: Optional[str] = None):
    return get_orders(limit=limit, status_filter=status)

@app.get("/api/watchlist")
@app.get("/watchlist")
def read_watchlist():
    items = get_watchlist()
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
def add_watchlist(item: WatchlistRequest):
    add_to_watchlist(item.symbol, item.name, item.asset_type)
    return {"status": "success"}

@app.delete("/api/watchlist/{symbol}")
@app.delete("/watchlist/{symbol}")
def delete_watchlist(symbol: str):
    remove_from_watchlist(symbol)
    return {"status": "success"}

class DepositRequest(BaseModel):
    amount: float

@app.post("/api/account/deposit")
@app.post("/account/deposit")
def deposit(req: DepositRequest):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive")
    new_balance = deposit_funds(req.amount)
    return {"status": "success", "new_balance": new_balance}

@app.post("/api/account/reset")
@app.post("/account/reset")
def reset():
    reset_account(1000000.0)
    return {"status": "success", "message": "Account balance reset to ₹10,00,000"}
