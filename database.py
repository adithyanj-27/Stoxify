import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import tempfile

import shutil

if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stoxify.db")
    # Migrate from brokeahh.db or growwfahh.db if existing and stoxify.db not yet created
    for prior_db_name in ["brokeahh.db", "growwfahh.db"]:
        prior_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), prior_db_name)
        if os.path.exists(prior_db) and not os.path.exists(DB_PATH):
            try:
                shutil.copy2(prior_db, DB_PATH)
                break
            except Exception:
                pass

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Account table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            balance REAL NOT NULL DEFAULT 1000000.0,
            total_deposited REAL NOT NULL DEFAULT 1000000.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed initial ₹10,00,000 if not exists
    cursor.execute("SELECT COUNT(*) FROM account")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO account (id, balance, total_deposited) VALUES (1, 1000000.0, 1000000.0)")

    # Holdings table (Delivery / CNC)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Positions table (Intraday / MIS with 5x leverage)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            margin_used REAL NOT NULL,
            product_type TEXT NOT NULL DEFAULT 'INTRADAY',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            order_type TEXT NOT NULL,
            product_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            order_variety TEXT NOT NULL DEFAULT 'MARKET',
            limit_price REAL DEFAULT 0.0,
            order_tag TEXT NOT NULL DEFAULT 'NORMAL',
            status TEXT NOT NULL DEFAULT 'EXECUTED',
            realized_pnl REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Attempt adding any newly added columns if table already existed
    for col, definition in [
        ("order_variety", "TEXT NOT NULL DEFAULT 'MARKET'"),
        ("limit_price", "REAL DEFAULT 0.0"),
        ("order_tag", "TEXT NOT NULL DEFAULT 'NORMAL'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} {definition}")
        except Exception:
            pass

    # Watchlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default watchlist if empty
    cursor.execute("SELECT COUNT(*) FROM watchlist")
    if cursor.fetchone()[0] == 0:
        default_items = [
            ("RELIANCE.NS", "Reliance Industries Ltd", "STOCK"),
            ("TCS.NS", "Tata Consultancy Services Ltd", "STOCK"),
            ("HDFCBANK.NS", "HDFC Bank Ltd", "STOCK"),
            ("TMPV.NS", "Tata Motors Passenger Vehicles Ltd", "STOCK"),
            ("ETERNAL.NS", "Zomato Ltd (Eternal Ltd)", "STOCK"),
            ("FEDERALBNK.NS", "The Federal Bank Ltd", "STOCK"),
            ("122639", "Parag Parikh Flexi Cap Fund - Direct Plan", "MUTUAL_FUND"),
            ("120828", "Quant Small Cap Fund - Direct Plan", "MUTUAL_FUND")
        ]
        cursor.executemany("INSERT OR IGNORE INTO watchlist (symbol, name, asset_type) VALUES (?, ?, ?)", default_items)

    conn.commit()
    conn.close()

def get_account() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_deposited FROM account WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"balance": row["balance"], "total_deposited": row["total_deposited"]}
    return {"balance": 1000000.0, "total_deposited": 1000000.0}

def get_holdings() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, updated_at FROM holdings WHERE quantity > 0")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_positions() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, margin_used, product_type, updated_at FROM positions WHERE quantity > 0")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def execute_trade(
    symbol: str, 
    name: str, 
    asset_type: str, 
    order_type: str, 
    product_type: str, 
    quantity: float, 
    price: float,
    order_variety: str = "MARKET",
    limit_price: Optional[float] = None,
    order_tag: str = "NORMAL"
) -> Dict[str, Any]:
    order_type = order_type.upper()
    product_type = product_type.upper()
    order_variety = order_variety.upper()

    effective_price = limit_price if (order_variety == "LIMIT" and limit_price and limit_price > 0) else price
    total_amount = round(quantity * effective_price, 2)

    # Calculate required margin (20% for Intraday = 5x leverage, 100% for Delivery)
    if product_type == "INTRADAY":
        required_margin = round(total_amount * 0.20, 2)
    else:
        required_margin = total_amount

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT balance FROM account WHERE id = 1")
        acc = cursor.fetchone()
        balance = acc["balance"] if acc else 1000000.0

        # Handle Limit Orders that do not immediately match market price
        is_pending_limit = False
        if order_variety == "LIMIT":
            if order_type == "BUY" and limit_price < price:
                is_pending_limit = True
            elif order_type == "SELL" and limit_price > price:
                is_pending_limit = True

        if is_pending_limit:
            if order_type == "BUY":
                if balance < required_margin:
                    conn.close()
                    return {"success": False, "error": f"Insufficient margin for Limit BUY. Required: ₹{required_margin:,.2f}, Available: ₹{balance:,.2f}"}
                # Block margin
                new_balance = round(balance - required_margin, 2)
                cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))
            else:
                # Validate shares exist to sell
                if product_type == "INTRADAY":
                    cursor.execute("SELECT quantity FROM positions WHERE symbol = ?", (symbol,))
                else:
                    cursor.execute("SELECT quantity FROM holdings WHERE symbol = ?", (symbol,))
                existing = cursor.fetchone()
                if not existing or existing["quantity"] < quantity:
                    avail = existing["quantity"] if existing else 0
                    conn.close()
                    return {"success": False, "error": f"Insufficient quantity to place Limit SELL. Available: {avail}, Requested: {quantity}"}

            cursor.execute("""
                INSERT INTO orders (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 0.0)
            """, (symbol, name, asset_type, order_type, product_type, quantity, effective_price, required_margin, order_variety, limit_price, order_tag))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {
                "success": True, 
                "order_id": order_id, 
                "status": "OPEN",
                "message": f"Limit {order_type} order placed for {quantity} {symbol} at ₹{effective_price:,.2f} (Status: Open)"
            }

        # Immediate Execution (Market or Executable Limit)
        if order_type == "BUY":
            if balance < required_margin:
                conn.close()
                return {"success": False, "error": f"Insufficient margin. Required: ₹{required_margin:,.2f} (5x leverage applied if Intraday), Available: ₹{balance:,.2f}"}

            new_balance = round(balance - required_margin, 2)
            cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

            if product_type == "INTRADAY":
                # Manage Intraday Positions table
                cursor.execute("SELECT quantity, avg_price, margin_used FROM positions WHERE symbol = ?", (symbol,))
                pos = cursor.fetchone()
                if pos:
                    current_qty = pos["quantity"]
                    current_avg = pos["avg_price"]
                    current_margin = pos["margin_used"]
                    new_qty = current_qty + quantity
                    new_avg = round(((current_qty * current_avg) + (quantity * effective_price)) / new_qty, 2)
                    new_margin_used = round(current_margin + required_margin, 2)
                    cursor.execute(
                        "UPDATE positions SET quantity = ?, avg_price = ?, margin_used = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?",
                        (new_qty, new_avg, new_margin_used, symbol)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO positions (symbol, name, asset_type, quantity, avg_price, margin_used, product_type) VALUES (?, ?, ?, ?, ?, ?, 'INTRADAY')",
                        (symbol, name, asset_type, quantity, effective_price, required_margin)
                    )
            else:
                # Manage Delivery Holdings table
                cursor.execute("SELECT quantity, avg_price FROM holdings WHERE symbol = ?", (symbol,))
                existing = cursor.fetchone()
                if existing:
                    current_qty = existing["quantity"]
                    current_avg = existing["avg_price"]
                    new_qty = current_qty + quantity
                    new_avg = round(((current_qty * current_avg) + total_amount) / new_qty, 2)
                    cursor.execute(
                        "UPDATE holdings SET quantity = ?, avg_price = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?",
                        (new_qty, new_avg, symbol)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO holdings (symbol, name, asset_type, quantity, avg_price) VALUES (?, ?, ?, ?, ?)",
                        (symbol, name, asset_type, quantity, effective_price)
                    )

            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0)
            """, (symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            tag_msg = " as After-Market Order (AMO)" if order_tag == "AMO" else ""
            return {"success": True, "order_id": order_id, "status": order_status, "message": f"Successfully purchased {quantity} {symbol} at ₹{effective_price:,.2f}{tag_msg}"}

        elif order_type == "SELL":
            if product_type == "INTRADAY":
                cursor.execute("SELECT quantity, avg_price, margin_used FROM positions WHERE symbol = ?", (symbol,))
                pos = cursor.fetchone()
                if not pos or pos["quantity"] < quantity:
                    avail = pos["quantity"] if pos else 0
                    conn.close()
                    return {"success": False, "error": f"Insufficient Intraday position to sell. Open: {avail}, Requested: {quantity}"}

                current_qty = pos["quantity"]
                avg_price = pos["avg_price"]
                current_margin = pos["margin_used"]

                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                margin_released = round((quantity / current_qty) * current_margin, 2)
                new_balance = round(balance + margin_released + realized_pnl, 2)
                cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                remaining_qty = round(current_qty - quantity, 4)
                if remaining_qty <= 0.0001:
                    cursor.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
                else:
                    new_margin = round(current_margin - margin_released, 2)
                    cursor.execute("UPDATE positions SET quantity = ?, margin_used = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?", (remaining_qty, new_margin, symbol))

            else:
                cursor.execute("SELECT quantity, avg_price FROM holdings WHERE symbol = ?", (symbol,))
                existing = cursor.fetchone()
                if not existing or existing["quantity"] < quantity:
                    available_qty = existing["quantity"] if existing else 0
                    conn.close()
                    return {"success": False, "error": f"Insufficient shares to sell. Available: {available_qty}, Requested: {quantity}"}

                current_qty = existing["quantity"]
                avg_price = existing["avg_price"]
                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                new_balance = round(balance + total_amount, 2)
                cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                remaining_qty = round(current_qty - quantity, 4)
                if remaining_qty <= 0.0001:
                    cursor.execute("DELETE FROM holdings WHERE symbol = ?", (symbol,))
                else:
                    cursor.execute("UPDATE holdings SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?", (remaining_qty, symbol))

            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status, realized_pnl))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            tag_msg = " as After-Market Order (AMO)" if order_tag == "AMO" else ""
            return {"success": True, "order_id": order_id, "status": order_status, "realized_pnl": realized_pnl, "message": f"Successfully sold {quantity} {symbol} at ₹{effective_price:,.2f}{tag_msg}"}

        else:
            conn.close()
            return {"success": False, "error": f"Unknown order type {order_type}"}

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}

def exit_position(symbol: str, exit_price: float) -> Dict[str, Any]:
    """
    Squares off an open Intraday position immediately at the given market price.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, margin_used FROM positions WHERE symbol = ?", (symbol,))
    pos = cursor.fetchone()
    conn.close()

    if not pos:
        return {"success": False, "error": f"No active intraday position found for {symbol}"}

    return execute_trade(
        symbol=pos["symbol"],
        name=pos["name"],
        asset_type=pos["asset_type"],
        order_type="SELL",
        product_type="INTRADAY",
        quantity=pos["quantity"],
        price=exit_price,
        order_variety="MARKET"
    )

def cancel_order(order_id: int) -> Dict[str, Any]:
    """
    Cancels an open/pending limit order and releases blocked margin if BUY order.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, symbol, order_type, total_amount, status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return {"success": False, "error": f"Order #{order_id} not found"}

        if order["status"] != "OPEN":
            conn.close()
            return {"success": False, "error": f"Cannot cancel order #{order_id} with status '{order['status']}'"}

        # Refund blocked margin if BUY
        if order["order_type"] == "BUY":
            cursor.execute("SELECT balance FROM account WHERE id = 1")
            acc = cursor.fetchone()
            curr_bal = acc["balance"] if acc else 1000000.0
            new_bal = round(curr_bal + order["total_amount"], 2)
            cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_bal,))

        cursor.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Order #{order_id} for {order['symbol']} cancelled successfully"}

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}

def check_open_limit_orders(symbol: str, current_price: float):
    """
    Checks and triggers execution for any pending limit orders matching current price.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, total_amount 
        FROM orders WHERE status = 'OPEN' AND symbol = ?
    """, (symbol,))
    open_orders = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for o in open_orders:
        should_fill = False
        if o["order_type"] == "BUY" and current_price <= o["limit_price"]:
            should_fill = True
        elif o["order_type"] == "SELL" and current_price >= o["limit_price"]:
            should_fill = True

        if should_fill:
            # Cancel open order record and execute real trade
            cancel_order(o["id"])
            execute_trade(
                symbol=o["symbol"],
                name=o["name"],
                asset_type=o["asset_type"],
                order_type=o["order_type"],
                product_type=o["product_type"],
                quantity=o["quantity"],
                price=current_price,
                order_variety="LIMIT",
                limit_price=o["limit_price"]
            )

def get_orders(limit: int = 100, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("""
            SELECT id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, timestamp
            FROM orders WHERE status = ? ORDER BY id DESC LIMIT ?
        """, (status_filter, limit))
    else:
        cursor.execute("""
            SELECT id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, timestamp
            FROM orders ORDER BY id DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_watchlist() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, asset_type, added_at FROM watchlist ORDER BY added_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_to_watchlist(symbol: str, name: str, asset_type: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO watchlist (symbol, name, asset_type) VALUES (?, ?, ?)", (symbol, name, asset_type))
    conn.commit()
    conn.close()
    return True

def remove_from_watchlist(symbol: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    conn.commit()
    conn.close()
    return True

def deposit_funds(amount: float) -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_deposited FROM account WHERE id = 1")
    acc = cursor.fetchone()
    new_balance = (acc["balance"] if acc else 0.0) + amount
    new_deposited = (acc["total_deposited"] if acc else 0.0) + amount
    cursor.execute("UPDATE account SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance, new_deposited))
    conn.commit()
    conn.close()
    return new_balance

def reset_account(initial_balance: float = 1000000.0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE account SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (initial_balance, initial_balance))
    cursor.execute("DELETE FROM holdings")
    cursor.execute("DELETE FROM positions")
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()

