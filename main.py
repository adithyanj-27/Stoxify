import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from database import (
    init_db, get_account, get_holdings, execute_trade, 
    get_orders, get_watchlist, add_to_watchlist, remove_from_watchlist,
    deposit_funds, reset_account
)
import market_service

app = FastAPI(title="GrowwFAHH", version="1.0.0")

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
    return Response(content="<h1>GrowwFAHH is Online</h1>", media_type="text/html")

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

class OrderRequest(BaseModel):
    symbol: str
    name: str
    asset_type: str = "STOCK"
    order_type: str
    product_type: str = "DELIVERY"
    quantity: float
    price: float

@app.post("/api/order")
@app.post("/order")
def place_order(order: OrderRequest):
    if order.quantity <= 0 or order.price <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity or price")

    result = execute_trade(
        symbol=order.symbol,
        name=order.name,
        asset_type=order.asset_type,
        order_type=order.order_type,
        product_type=order.product_type,
        quantity=order.quantity,
        price=order.price
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Transaction failed"))
    return result

@app.get("/api/orders")
@app.get("/orders")
def read_orders(limit: int = 50):
    return get_orders(limit=limit)

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
