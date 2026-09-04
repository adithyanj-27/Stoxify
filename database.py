import os
import shutil
import sqlite3
import json
import uuid
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Any

# 1. Automatic .env loading (Zero third-party dependency)
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(ENV_FILE):
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as ef:
            for line in ef:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    import tempfile
    DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stoxify.db")
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

def is_supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table (Stores full simulated Groww profile)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            pan TEXT,
            bank_name TEXT DEFAULT 'HDFC Bank',
            bank_account TEXT DEFAULT '50100234567890',
            pin TEXT DEFAULT '1234',
            balance REAL NOT NULL DEFAULT 1000000.0,
            total_deposited REAL NOT NULL DEFAULT 1000000.0,
            avatar_color TEXT DEFAULT '#0EA5E9',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure default user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = 'default'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color)
            VALUES ('default', 'Default Trader', 'trader@stoxify.com', '9876543210', 'ABCDE1234F', 'HDFC Bank', '50100234567890', '1234', 1000000.0, 1000000.0, '#0EA5E9')
        """)

    # 2. Legacy Account table (for backwards compatibility)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            balance REAL NOT NULL DEFAULT 1000000.0,
            total_deposited REAL NOT NULL DEFAULT 1000000.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM account")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO account (id, balance, total_deposited) VALUES (1, 1000000.0, 1000000.0)")

    # 3. Holdings table (Delivery / CNC)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol)
        )
    """)
    # Migration check for older holdings without user_id
    try:
        cursor.execute("ALTER TABLE holdings ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
    except Exception:
        pass

    # 4. Positions table (Intraday / MIS with 5x leverage)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            margin_used REAL NOT NULL,
            product_type TEXT NOT NULL DEFAULT 'INTRADAY',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol)
        )
    """)
    try:
        cursor.execute("ALTER TABLE positions ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
    except Exception:
        pass

    # 5. Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
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
    for col, definition in [
        ("user_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("order_variety", "TEXT NOT NULL DEFAULT 'MARKET'"),
        ("limit_price", "REAL DEFAULT 0.0"),
        ("order_tag", "TEXT NOT NULL DEFAULT 'NORMAL'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} {definition}")
        except Exception:
            pass

    # 6. Watchlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol)
        )
    """)
    try:
        cursor.execute("ALTER TABLE watchlist ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
    except Exception:
        pass

    # Seed default watchlist if empty for default user
    cursor.execute("SELECT COUNT(*) FROM watchlist WHERE user_id = 'default'")
    if cursor.fetchone()[0] == 0:
        default_items = [
            ("default", "RELIANCE.NS", "Reliance Industries Ltd", "STOCK"),
            ("default", "TCS.NS", "Tata Consultancy Services Ltd", "STOCK"),
            ("default", "HDFCBANK.NS", "HDFC Bank Ltd", "STOCK"),
            ("default", "TMPV.NS", "Tata Motors Passenger Vehicles Ltd", "STOCK"),
            ("default", "ETERNAL.NS", "Zomato Ltd (Eternal Ltd)", "STOCK"),
            ("default", "FEDERALBNK.NS", "The Federal Bank Ltd", "STOCK"),
            ("default", "122639", "Parag Parikh Flexi Cap Fund - Direct Plan", "MUTUAL_FUND"),
            ("default", "120828", "Quant Small Cap Fund - Direct Plan", "MUTUAL_FUND")
        ]
        try:
            cursor.executemany("INSERT OR IGNORE INTO watchlist (user_id, symbol, name, asset_type) VALUES (?, ?, ?, ?)", default_items)
        except Exception:
            pass

    conn.commit()
    conn.close()

# --- User Profile Management (Groww Style) ---
def create_user(
    name: str, 
    email: Optional[str] = None, 
    phone: Optional[str] = None, 
    pan: Optional[str] = None,
    bank_name: str = "HDFC Bank",
    bank_account: str = "50100234567890",
    pin: str = "1234"
) -> Dict[str, Any]:
    user_id = "user_" + str(uuid.uuid4())[:8]
    palettes = ["#0EA5E9", "#10B981", "#6366F1", "#EC4899", "#F59E0B", "#8B5CF6"]
    avatar_color = palettes[len(name) % len(palettes)]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1000000.0, 1000000.0, ?)
    """, (user_id, name, email or "", phone or "", pan or "ABCDE1234F", bank_name, bank_account, pin, avatar_color))

    # Seed default watchlist for this new user
    default_items = [
        (user_id, "RELIANCE.NS", "Reliance Industries Ltd", "STOCK"),
        (user_id, "TCS.NS", "Tata Consultancy Services Ltd", "STOCK"),
        (user_id, "HDFCBANK.NS", "HDFC Bank Ltd", "STOCK"),
        (user_id, "ETERNAL.NS", "Zomato Ltd (Eternal Ltd)", "STOCK"),
        (user_id, "122639", "Parag Parikh Flexi Cap Fund - Direct Plan", "MUTUAL_FUND")
    ]
    cursor.executemany("INSERT OR IGNORE INTO watchlist (user_id, symbol, name, asset_type) VALUES (?, ?, ?, ?)", default_items)

    conn.commit()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    user_data = dict(row) if row else {}
    conn.close()
    return user_data

def get_user(user_id: str = "default") -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    if user_id == "default":
        return {
            "id": "default",
            "name": "Default Trader",
            "email": "trader@stoxify.com",
            "phone": "9876543210",
            "pan": "ABCDE1234F",
            "bank_name": "HDFC Bank",
            "bank_account": "50100234567890",
            "pin": "1234",
            "balance": 1000000.0,
            "total_deposited": 1000000.0,
            "avatar_color": "#0EA5E9"
        }
    return None

def list_users() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, bank_name, balance, avatar_color, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Account & Balances ---
def get_account(user_id: str = "default") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_deposited FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row and user_id == "default":
        cursor.execute("SELECT balance, total_deposited FROM account WHERE id = 1")
        row = cursor.fetchone()
    conn.close()
    if row:
        return {"balance": row["balance"], "total_deposited": row["total_deposited"]}
    return {"balance": 1000000.0, "total_deposited": 1000000.0}

def get_holdings(user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, name, asset_type, quantity, avg_price, updated_at 
        FROM holdings WHERE user_id = ? AND quantity > 0
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_positions(user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, name, asset_type, quantity, avg_price, margin_used, product_type, updated_at 
        FROM positions WHERE user_id = ? AND quantity > 0
    """, (user_id,))
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
    order_tag: str = "NORMAL",
    user_id: str = "default"
) -> Dict[str, Any]:
    order_type = order_type.upper()
    product_type = product_type.upper()
    order_variety = order_variety.upper()

    effective_price = limit_price if (order_variety == "LIMIT" and limit_price and limit_price > 0) else price
    total_amount = round(quantity * effective_price, 2)

    # 20% margin for Intraday (5x leverage), 100% for Delivery
    if product_type == "INTRADAY":
        required_margin = round(total_amount * 0.20, 2)
    else:
        required_margin = total_amount

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Fetch current balance
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        acc_row = cursor.fetchone()
        if not acc_row and user_id == "default":
            cursor.execute("SELECT balance FROM account WHERE id = 1")
            acc_row = cursor.fetchone()
        balance = acc_row["balance"] if acc_row else 1000000.0

        # Pending Limit orders check
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
                new_balance = round(balance - required_margin, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))
            else:
                if product_type == "INTRADAY":
                    cursor.execute("SELECT quantity FROM positions WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                else:
                    cursor.execute("SELECT quantity FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                existing = cursor.fetchone()
                if not existing or existing["quantity"] < quantity:
                    avail = existing["quantity"] if existing else 0
                    conn.close()
                    return {"success": False, "error": f"Insufficient quantity to place Limit SELL. Available: {avail}, Requested: {quantity}"}

            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 0.0)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, required_margin, order_variety, limit_price, order_tag))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {
                "success": True, 
                "order_id": order_id, 
                "status": "OPEN",
                "message": f"Limit {order_type} order placed for {quantity} {symbol} at ₹{effective_price:,.2f} (Status: Open)"
            }

        # Immediate Execution
        if order_type == "BUY":
            if balance < required_margin:
                conn.close()
                return {"success": False, "error": f"Insufficient margin. Required: ₹{required_margin:,.2f} (5x leverage applied if Intraday), Available: ₹{balance:,.2f}"}

            new_balance = round(balance - required_margin, 2)
            cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
            if user_id == "default":
                cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

            if product_type == "INTRADAY":
                cursor.execute("SELECT quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                pos = cursor.fetchone()
                if pos:
                    curr_qty = pos["quantity"]
                    curr_avg = pos["avg_price"]
                    curr_margin = pos["margin_used"]
                    new_qty = curr_qty + quantity
                    new_avg = round(((curr_qty * curr_avg) + (quantity * effective_price)) / new_qty, 2)
                    new_margin_used = round(curr_margin + required_margin, 2)
                    cursor.execute("""
                        UPDATE positions SET quantity = ?, avg_price = ?, margin_used = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ? AND symbol = ?
                    """, (new_qty, new_avg, new_margin_used, user_id, symbol))
                else:
                    cursor.execute("""
                        INSERT INTO positions (user_id, symbol, name, asset_type, quantity, avg_price, margin_used, product_type) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'INTRADAY')
                    """, (user_id, symbol, name, asset_type, quantity, effective_price, required_margin))
            else:
                cursor.execute("SELECT quantity, avg_price FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                existing = cursor.fetchone()
                if existing:
                    curr_qty = existing["quantity"]
                    curr_avg = existing["avg_price"]
                    new_qty = curr_qty + quantity
                    new_avg = round(((curr_qty * curr_avg) + total_amount) / new_qty, 2)
                    cursor.execute("""
                        UPDATE holdings SET quantity = ?, avg_price = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ? AND symbol = ?
                    """, (new_qty, new_avg, user_id, symbol))
                else:
                    cursor.execute("""
                        INSERT INTO holdings (user_id, symbol, name, asset_type, quantity, avg_price) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, symbol, name, asset_type, quantity, effective_price))

            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            tag_msg = " as After-Market Order (AMO)" if order_tag == "AMO" else ""
            return {"success": True, "order_id": order_id, "status": order_status, "message": f"Successfully purchased {quantity} {symbol} at ₹{effective_price:,.2f}{tag_msg}"}

        elif order_type == "SELL":
            if product_type == "INTRADAY":
                cursor.execute("SELECT quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                pos = cursor.fetchone()
                if not pos or pos["quantity"] < quantity:
                    avail = pos["quantity"] if pos else 0
                    conn.close()
                    return {"success": False, "error": f"Insufficient Intraday position to sell. Open: {avail}, Requested: {quantity}"}

                curr_qty = pos["quantity"]
                avg_price = pos["avg_price"]
                curr_margin = pos["margin_used"]

                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                margin_released = round((quantity / curr_qty) * curr_margin, 2)
                new_balance = round(balance + margin_released + realized_pnl, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                rem_qty = round(curr_qty - quantity, 4)
                if rem_qty <= 0.0001:
                    cursor.execute("DELETE FROM positions WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                else:
                    new_margin = round(curr_margin - margin_released, 2)
                    cursor.execute("UPDATE positions SET quantity = ?, margin_used = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND symbol = ?", (rem_qty, new_margin, user_id, symbol))

            else:
                cursor.execute("SELECT quantity, avg_price FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                existing = cursor.fetchone()
                if not existing or existing["quantity"] < quantity:
                    avail_qty = existing["quantity"] if existing else 0
                    conn.close()
                    return {"success": False, "error": f"Insufficient shares to sell. Available: {avail_qty}, Requested: {quantity}"}

                curr_qty = existing["quantity"]
                avg_price = existing["avg_price"]
                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                new_balance = round(balance + total_amount, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                rem_qty = round(curr_qty - quantity, 4)
                if rem_qty <= 0.0001:
                    cursor.execute("DELETE FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                else:
                    cursor.execute("UPDATE holdings SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND symbol = ?", (rem_qty, user_id, symbol))

            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status, realized_pnl))
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

def exit_position(symbol: str, exit_price: float, user_id: str = "default") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND symbol = ?", (user_id, symbol))
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
        order_variety="MARKET",
        user_id=user_id
    )

def cancel_order(order_id: int, user_id: str = "default") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, user_id, symbol, order_type, total_amount, status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return {"success": False, "error": f"Order #{order_id} not found"}

        if order["status"] != "OPEN":
            conn.close()
            return {"success": False, "error": f"Cannot cancel order #{order_id} with status '{order['status']}'"}

        o_user = order["user_id"] or user_id
        if order["order_type"] == "BUY":
            cursor.execute("SELECT balance FROM users WHERE id = ?", (o_user,))
            acc = cursor.fetchone()
            curr_bal = acc["balance"] if acc else 1000000.0
            new_bal = round(curr_bal + order["total_amount"], 2)
            cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_bal, o_user))
            if o_user == "default":
                cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_bal,))

        cursor.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Order #{order_id} for {order['symbol']} cancelled successfully"}

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}

def check_open_limit_orders(symbol: str, current_price: float, user_id: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, total_amount 
            FROM orders WHERE status = 'OPEN' AND symbol = ? AND user_id = ?
        """, (symbol, user_id))
    else:
        cursor.execute("""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, total_amount 
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
            cancel_order(o["id"], user_id=o["user_id"])
            execute_trade(
                symbol=o["symbol"],
                name=o["name"],
                asset_type=o["asset_type"],
                order_type=o["order_type"],
                product_type=o["product_type"],
                quantity=o["quantity"],
                price=current_price,
                order_variety="LIMIT",
                limit_price=o["limit_price"],
                user_id=o["user_id"]
            )

def get_orders(limit: int = 100, status_filter: Optional[str] = None, user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, timestamp
            FROM orders WHERE user_id = ? AND status = ? ORDER BY id DESC LIMIT ?
        """, (user_id, status_filter, limit))
    else:
        cursor.execute("""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, timestamp
            FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?
        """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_watchlist(user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, asset_type, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_to_watchlist(symbol: str, name: str, asset_type: str, user_id: str = "default") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO watchlist (user_id, symbol, name, asset_type) 
        VALUES (?, ?, ?, ?)
    """, (user_id, symbol, name, asset_type))
    conn.commit()
    conn.close()
    return True

def remove_from_watchlist(symbol: str, user_id: str = "default") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE user_id = ? AND symbol = ?", (user_id, symbol))
    conn.commit()
    conn.close()
    return True

def deposit_funds(amount: float, user_id: str = "default") -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_deposited FROM users WHERE id = ?", (user_id,))
    acc = cursor.fetchone()
    curr_bal = acc["balance"] if acc else 0.0
    curr_dep = acc["total_deposited"] if acc else 0.0
    new_balance = curr_bal + amount
    new_deposited = curr_dep + amount
    cursor.execute("""
        UPDATE users SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_balance, new_deposited, user_id))
    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance, new_deposited))
    conn.commit()
    conn.close()
    return new_balance

def reset_account(initial_balance: float = 1000000.0, user_id: str = "default"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (initial_balance, initial_balance, user_id))
    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (initial_balance, initial_balance))
    cursor.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
