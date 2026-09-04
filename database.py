import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import tempfile

if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = os.path.join(tempfile.gettempdir(), "growwfahh.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "growwfahh.db")

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

    # Holdings table
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
            status TEXT NOT NULL DEFAULT 'EXECUTED',
            realized_pnl REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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
            ("122639", "Parag Parikh Flexi Cap Fund - Direct Plan", "MUTUAL_FUND"),
            ("120828", "Quant Small Cap Fund - Direct Plan", "MUTUAL_FUND")
        ]
        cursor.executemany("INSERT OR IGNORE INTO watchlist (symbol, name, asset_type) VALUES (?, ?, ?)", default_items)

    # Clean up any legacy delisted tickers in watchlist
    cursor.execute("UPDATE watchlist SET symbol = 'TMPV.NS', name = 'Tata Motors Passenger Vehicles Ltd' WHERE symbol = 'TATAMOTORS.NS'")
    cursor.execute("UPDATE watchlist SET symbol = 'ETERNAL.NS', name = 'Zomato Ltd (Eternal Ltd)' WHERE symbol = 'ZOMATO.NS'")

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

def execute_trade(symbol: str, name: str, asset_type: str, order_type: str, product_type: str, quantity: float, price: float) -> Dict[str, Any]:
    order_type = order_type.upper()
    product_type = product_type.upper()
    total_amount = round(quantity * price, 2)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT balance FROM account WHERE id = 1")
        acc = cursor.fetchone()
        balance = acc["balance"] if acc else 1000000.0

        if order_type == "BUY":
            if balance < total_amount:
                conn.close()
                return {"success": False, "error": f"Insufficient balance. Required: ₹{total_amount:,.2f}, Available: ₹{balance:,.2f}"}

            new_balance = round(balance - total_amount, 2)
            cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

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
                    (symbol, name, asset_type, quantity, price)
                )

            cursor.execute(
                """INSERT INTO orders (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, status, realized_pnl)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EXECUTED', 0.0)""",
                (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount)
            )
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {"success": True, "order_id": order_id, "message": f"Successfully purchased {quantity} {symbol} at ₹{price:,.2f}"}

        elif order_type == "SELL":
            cursor.execute("SELECT quantity, avg_price FROM holdings WHERE symbol = ?", (symbol,))
            existing = cursor.fetchone()

            if not existing or existing["quantity"] < quantity:
                available_qty = existing["quantity"] if existing else 0
                conn.close()
                return {"success": False, "error": f"Insufficient shares to sell. Available: {available_qty}, Requested: {quantity}"}

            current_qty = existing["quantity"]
            avg_price = existing["avg_price"]
            realized_pnl = round((price - avg_price) * quantity, 2)

            new_balance = round(balance + total_amount, 2)
            cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

            remaining_qty = round(current_qty - quantity, 4)
            if remaining_qty <= 0.0001:
                cursor.execute("DELETE FROM holdings WHERE symbol = ?", (symbol,))
            else:
                cursor.execute("UPDATE holdings SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?", (remaining_qty, symbol))

            cursor.execute(
                """INSERT INTO orders (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, status, realized_pnl)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EXECUTED', ?)""",
                (symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, realized_pnl)
            )
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {"success": True, "order_id": order_id, "message": f"Successfully sold {quantity} {symbol} at ₹{price:,.2f}"}

        else:
            conn.close()
            return {"success": False, "error": f"Unknown order type {order_type}"}

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}

def get_orders(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, status, realized_pnl, timestamp
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
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()
