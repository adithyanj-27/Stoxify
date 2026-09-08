import os
import shutil
import sqlite3
import json
import uuid
import random
import re
import time
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

DEFAULT_SUPABASE_URL = "https://pqyjxpaqbjeelewcjwmd.supabase.co"
DEFAULT_SUPABASE_KEY = "sb_publishable__ywLDIS3oh2MnKdoXcnkYg_rNjN_tHw"

SUPABASE_URL = (os.environ.get("SUPABASE_URL") or DEFAULT_SUPABASE_URL).rstrip("/")
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[:-8].rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or DEFAULT_SUPABASE_KEY

def supabase_api(method: str, table_or_endpoint: str, payload: Optional[Any] = None, params: Optional[Dict[str, str]] = None) -> Optional[Any]:
    if not is_supabase_enabled():
        return None
    try:
        clean_endpoint = table_or_endpoint.lstrip("/")
        url = f"{SUPABASE_URL}/rest/v1/{clean_endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation"
        }
        data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method.upper())
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8")
            if content:
                try:
                    return json.loads(content)
                except Exception:
                    return content
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"[Supabase API Error] {method} {table_or_endpoint} -> HTTP {e.code}: {err_body}")
        return None
    except Exception as e:
        print(f"[Supabase Connection Error] {method} {table_or_endpoint} -> {e}")
        return None


if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    import tempfile
    DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stoxify.db")

_db_initialized = False
_REMOTE_SYNC_LAST_AT: Dict[str, float] = {}
_REMOTE_SYNC_INTERVAL_SECONDS = 12

def should_sync_remote(resource: str, user_id: str) -> bool:
    """Avoid a cloud round trip on every UI refresh while keeping data fresh."""
    key = f"{resource}:{user_id}"
    now = time.monotonic()
    if now - _REMOTE_SYNC_LAST_AT.get(key, 0.0) < _REMOTE_SYNC_INTERVAL_SECONDS:
        return False
    _REMOTE_SYNC_LAST_AT[key] = now
    return True

def enqueue_sync_operation(cursor, user_id: str, method: str, endpoint: str, filters: Optional[Dict[str, str]] = None, payload: Optional[Any] = None):
    """Persist an idempotent cloud operation with the local trade transaction."""
    cursor.execute("""
        INSERT INTO sync_outbox (user_id, method, endpoint, filters_json, payload_json)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, method, endpoint, json.dumps(filters or {}), json.dumps(payload) if payload is not None else None))

def drain_sync_outbox(user_id: str, limit: int = 20):
    if not is_supabase_enabled() or not user_id or user_id == "guest":
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, method, endpoint, filters_json, payload_json
        FROM sync_outbox WHERE user_id = ? ORDER BY id ASC LIMIT ?
    """, (user_id, limit))
    operations = [dict(row) for row in cursor.fetchall()]
    for operation in operations:
        try:
            result = supabase_api(
                operation["method"], operation["endpoint"],
                payload=json.loads(operation["payload_json"]) if operation["payload_json"] else None,
                params=json.loads(operation["filters_json"] or "{}")
            )
            if result is not None:
                cursor.execute("DELETE FROM sync_outbox WHERE id = ?", (operation["id"],))
            else:
                cursor.execute("UPDATE sync_outbox SET attempts = attempts + 1, last_attempt_at = CURRENT_TIMESTAMP WHERE id = ?", (operation["id"],))
        except Exception:
            cursor.execute("UPDATE sync_outbox SET attempts = attempts + 1, last_attempt_at = CURRENT_TIMESTAMP WHERE id = ?", (operation["id"],))
    conn.commit()
    conn.close()

def get_raw_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_db_initialized():
    global _db_initialized
    if _db_initialized:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users LIMIT 1")
        conn.close()
        _db_initialized = True
    except Exception:
        init_db()
        _db_initialized = True

def get_connection():
    ensure_db_initialized()
    return get_raw_connection()

def is_supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

def init_db():
    conn = get_raw_connection()
    cursor = conn.cursor()

    # 1. Users table (Stores full simulated Groww profile)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            phone TEXT,
            pan TEXT,
            dob TEXT,
            bank_name TEXT DEFAULT 'HDFC Bank',
            bank_account TEXT DEFAULT '50100234567890',
            pin TEXT DEFAULT '',
            balance REAL NOT NULL DEFAULT 1000000.0,
            total_deposited REAL NOT NULL DEFAULT 1000000.0,
            avatar_color TEXT DEFAULT '#0EA5E9',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col in ["dob TEXT", "username TEXT", "password TEXT"]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col}")
            conn.commit()
        except Exception:
            pass

    # Ensure default user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = 'default'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color)
            VALUES ('default', 'Default Trader', 'trader@stoxify.com', '9876543210', 'ABCDE1234F', 'HDFC Bank', '50100234567890', '', 1000000.0, 1000000.0, '#0EA5E9')
        """)
    if is_supabase_enabled():
        try:
            supabase_api("POST", "users", payload={
                "id": "default",
                "name": "Default Trader",
                "email": "trader@stoxify.com",
                "phone": "9876543210",
                "pan": "ABCDE1234F",
                "bank_name": "HDFC Bank",
                "bank_account": "50100234567890",
                "pin": "",
                "balance": 1000000.0,
                "total_deposited": 1000000.0,
                "avatar_color": "#0EA5E9"
            })
        except Exception:
            pass

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

    # A short-lived local marker prevents a stale remote row from reappearing
    # between a full sale and the cloud DELETE becoming visible to a read.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holding_tombstones (
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, symbol)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            method TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            filters_json TEXT NOT NULL DEFAULT '{}',
            payload_json TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_attempt_at TIMESTAMP
        )
    """)

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
        ("order_tag", "TEXT NOT NULL DEFAULT 'NORMAL'"),
        ("trigger_price", "REAL DEFAULT 0.0")
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

    # Ensure tables with legacy 'symbol PRIMARY KEY' are safely upgraded to composite UNIQUE(user_id, symbol)
    for tbl, cols, create_stmt in [
        ("holdings", ["user_id", "symbol", "name", "asset_type", "quantity", "avg_price"], """
            CREATE TABLE holdings (
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
        """),
        ("positions", ["user_id", "symbol", "name", "asset_type", "quantity", "avg_price", "margin_used", "product_type"], """
            CREATE TABLE positions (
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
        """),
        ("watchlist", ["user_id", "symbol", "name", "asset_type"], """
            CREATE TABLE watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, symbol)
            )
        """)
    ]:
        try:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tbl}'")
            row = cursor.fetchone()
            if row and "symbol TEXT PRIMARY KEY" in row[0]:
                temp_name = f"{tbl}_old"
                cursor.execute(f"ALTER TABLE {tbl} RENAME TO {temp_name}")
                cursor.execute(create_stmt)
                cols_str = ", ".join(cols)
                cursor.execute(f"INSERT OR IGNORE INTO {tbl} ({cols_str}) SELECT {cols_str} FROM {temp_name}")
                cursor.execute(f"DROP TABLE {temp_name}")
        except Exception:
            pass

    # 7. SIPs (Systematic Investment Plans) table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            fund_id TEXT NOT NULL,
            fund_name TEXT NOT NULL,
            monthly_amount REAL NOT NULL,
            sip_day INTEGER NOT NULL DEFAULT 5,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            next_installment_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. GTT (Good Till Triggered) Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gtt_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            product_type TEXT NOT NULL DEFAULT 'DELIVERY',
            action TEXT NOT NULL DEFAULT 'BUY',
            quantity REAL NOT NULL,
            trigger_price REAL NOT NULL,
            target_price REAL DEFAULT 0.0,
            stop_loss_price REAL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 9. IPO Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ipo_bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            ipo_id TEXT NOT NULL,
            ipo_name TEXT NOT NULL,
            lots INTEGER NOT NULL DEFAULT 1,
            shares INTEGER NOT NULL,
            bid_price REAL NOT NULL,
            amount_blocked REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'APPLIED',
            upi_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# --- User Profile Management (Groww Style) ---
def check_username_available(username: str, exclude_user_id: Optional[str] = None) -> bool:
    if not username:
        return False
    clean = username.strip().lstrip("@").lower()
    if len(clean) < 3 or len(clean) > 25:
        return False
    if not re.match(r"^[a-zA-Z0-9_]+$", clean):
        return False

    conn = get_connection()
    cursor = conn.cursor()
    if exclude_user_id:
        cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(username) = ? AND id != ?", (clean, exclude_user_id))
    else:
        cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(username) = ?", (clean,))
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        return False

    if is_supabase_enabled():
        try:
            params = {"username": f"eq.{clean}", "select": "id"}
            res = supabase_api("GET", "users", params=params)
            if res and isinstance(res, list) and len(res) > 0:
                if exclude_user_id and res[0].get("id") == exclude_user_id:
                    return True
                return False
        except Exception:
            pass

    return True

def create_user(
    name: str, 
    email: str, 
    phone: Optional[str] = None, 
    pan: Optional[str] = None,
    bank_name: str = "HDFC Bank",
    bank_account: str = "50100234567890",
    pin: str = "",
    user_id: Optional[str] = None,
    dob: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Dict[str, Any]:
    if not user_id:
        user_id = f"STOX-{random.randint(100000, 999999)}"
    palettes = ["#0EA5E9", "#10B981", "#6366F1", "#EC4899", "#F59E0B", "#8B5CF6"]
    avatar_color = palettes[len(name) % len(palettes)]

    clean_username = username.strip().lstrip("@").lower() if username else None
    clean_password = password.strip() if password else None

    # 1. Insert into local SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, name, email, phone, pan, dob, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1000000.0, 1000000.0, ?, ?, ?)
    """, (user_id, name, (email or "").strip(), phone or "", pan or "ABCDE1234F", dob or "", bank_name, bank_account, pin, avatar_color, clean_username, clean_password))

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

    # 2. Sync directly to Supabase cloud dashboard
    if is_supabase_enabled():
        sb_user_payload = {
            "id": user_id,
            "name": name,
            "email": (email or "").strip(),
            "phone": phone or "",
            "pan": pan or "ABCDE1234F",
            "bank_name": bank_name,
            "bank_account": bank_account,
            "pin": pin,
            "balance": 1000000.0,
            "total_deposited": 1000000.0,
            "avatar_color": avatar_color
        }
        if dob:
            sb_user_payload["dob"] = dob.strip()
        if clean_username:
            sb_user_payload["username"] = clean_username
        if clean_password:
            sb_user_payload["password"] = clean_password

        sb_res = supabase_api("POST", "users", payload=sb_user_payload)
        if sb_res is None:
            # Graceful fallback if new columns haven't been added yet in Supabase
            fallback_payload = dict(sb_user_payload)
            fallback_payload.pop("dob", None)
            fallback_payload.pop("username", None)
            fallback_payload.pop("password", None)
            sb_res = supabase_api("POST", "users", payload=fallback_payload)

        if sb_res is not None:
            print(f"[Supabase] User {user_id} ({name}) successfully saved to Supabase dashboard")
            # Seed default watchlist items to Supabase
            sb_wl_items = [
                {"user_id": user_id, "symbol": item[1], "name": item[2], "asset_type": item[3]}
                for item in default_items
            ]
            supabase_api("POST", "watchlist", payload=sb_wl_items)
        else:
            print(f"[Supabase] Warning: could not sync user {user_id} to Supabase")

        # 3. Register user directly into Supabase Authentication -> Users (auth.users)
        try:
            auth_url = f"{SUPABASE_URL}/auth/v1/signup"
            clean_email = (email or "").strip()
            if clean_email:
                if clean_password and len(clean_password) >= 6:
                    pwd = clean_password
                elif pin and len(str(pin)) >= 4:
                    pwd = f"stoxify_{pin}" if len(str(pin)) < 6 else str(pin)
                else:
                    pwd = f"stoxify_{user_id.replace('-', '_')}"
                auth_payload = {
                    "email": clean_email,
                    "password": pwd,
                    "data": {
                        "name": name,
                        "phone": phone or "",
                        "demat": user_id,
                        "pin": str(pin or ""),
                        "pan": pan or "ABCDE1234F",
                        "username": clean_username or ""
                    }
                }
                auth_headers = {
                    "apikey": SUPABASE_KEY,
                    "Content-Type": "application/json"
                }
                auth_req = urllib.request.Request(
                    auth_url, 
                    data=json.dumps(auth_payload).encode("utf-8"), 
                    headers=auth_headers, 
                    method="POST"
                )
                with urllib.request.urlopen(auth_req, timeout=6) as auth_resp:
                    print(f"[Supabase Auth] Successfully registered {clean_email} in Supabase Authentication -> Users")
        except urllib.error.HTTPError as he:
            err_text = he.read().decode("utf-8", errors="ignore")
            print(f"[Supabase Auth Note] signup response ({he.code}): {err_text}")
        except Exception as ae:
            print(f"[Supabase Auth Note] {ae}")

    return user_data

def update_user(
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    pan: Optional[str] = None,
    dob: Optional[str] = None,
    bank_name: Optional[str] = None,
    bank_account: Optional[str] = None,
    pin: Optional[str] = None,
    avatar_color: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    if not user_id or user_id == "guest":
        return None

    fields = []
    params = []
    sb_payload = {}

    if name is not None:
        fields.append("name = ?")
        params.append(name.strip())
        sb_payload["name"] = name.strip()
    if email is not None:
        fields.append("email = ?")
        params.append(email.strip())
        sb_payload["email"] = email.strip()
    if phone is not None:
        fields.append("phone = ?")
        params.append(phone.strip())
        sb_payload["phone"] = phone.strip()
    if pan is not None:
        fields.append("pan = ?")
        params.append(pan.strip().upper())
        sb_payload["pan"] = pan.strip().upper()
    if dob is not None:
        fields.append("dob = ?")
        params.append(dob.strip())
        sb_payload["dob"] = dob.strip()
    if bank_name is not None:
        fields.append("bank_name = ?")
        params.append(bank_name.strip())
        sb_payload["bank_name"] = bank_name.strip()
    if bank_account is not None:
        fields.append("bank_account = ?")
        params.append(bank_account.strip())
        sb_payload["bank_account"] = bank_account.strip()
    if pin is not None:
        fields.append("pin = ?")
        params.append(pin.strip())
        sb_payload["pin"] = pin.strip()
    if avatar_color is not None:
        fields.append("avatar_color = ?")
        params.append(avatar_color.strip())
        sb_payload["avatar_color"] = avatar_color.strip()
    if username is not None:
        clean_user = username.strip().lstrip("@").lower()
        fields.append("username = ?")
        params.append(clean_user)
        sb_payload["username"] = clean_user
    if password is not None:
        clean_pwd = password.strip()
        fields.append("password = ?")
        params.append(clean_pwd)
        sb_payload["password"] = clean_pwd

    if not fields:
        return get_user(user_id)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    updated = dict(row) if row else None
    conn.close()

    # Sync to Supabase
    if is_supabase_enabled() and user_id != "default":
        try:
            sb_payload["updated_at"] = datetime.utcnow().isoformat()
            res = supabase_api("PATCH", f"users?id=eq.{user_id}", payload=sb_payload)
            if res is None:
                sb_fallback = dict(sb_payload)
                sb_fallback.pop("dob", None)
                sb_fallback.pop("username", None)
                sb_fallback.pop("password", None)
                supabase_api("PATCH", f"users?id=eq.{user_id}", payload=sb_fallback)
        except Exception:
            pass

    return updated

def get_user(user_id: str = "default") -> Optional[Dict[str, Any]]:
    # 1. Try Supabase first if available
    if is_supabase_enabled() and user_id and user_id != "guest":
        res = supabase_api("GET", "users", params={"id": f"eq.{user_id}", "select": "*"})
        if res and isinstance(res, list) and len(res) > 0:
            sb_u = res[0]
            # Ensure local SQLite cache is populated
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sb_u.get("id"),
                    sb_u.get("name"),
                    sb_u.get("email"),
                    sb_u.get("phone"),
                    sb_u.get("pan"),
                    sb_u.get("bank_name"),
                    sb_u.get("bank_account"),
                    sb_u.get("pin"),
                    float(sb_u.get("balance", 1000000.0)),
                    float(sb_u.get("total_deposited", 1000000.0)),
                    sb_u.get("avatar_color", "#0EA5E9"),
                    sb_u.get("username"),
                    sb_u.get("password")
                ))
                conn.commit()
                conn.close()
            except Exception:
                pass
            return sb_u

    # 2. Local SQLite fallback
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
            "username": "default_trader",
            "email": "trader@stoxify.com",
            "phone": "9876543210",
            "pan": "ABCDE1234F",
            "bank_name": "HDFC Bank",
            "bank_account": "50100234567890",
            "pin": "",
            "balance": 1000000.0,
            "total_deposited": 1000000.0,
            "avatar_color": "#0EA5E9"
        }
    return None

def list_users() -> List[Dict[str, Any]]:
    # 1. Try Supabase first
    if is_supabase_enabled():
        res = supabase_api("GET", "users", params={"select": "id,name,username,email,phone,bank_name,balance,avatar_color,created_at", "order": "created_at.desc"})
        if res is None:
            # Fallback if username column not yet present in remote Supabase project
            res = supabase_api("GET", "users", params={"select": "id,name,email,phone,bank_name,balance,avatar_color,created_at", "order": "created_at.desc"})
        if res and isinstance(res, list) and len(res) > 0:
            return res

    # 2. Local SQLite fallback
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, username, email, phone, bank_name, balance, avatar_color, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def find_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    if not identifier:
        return None
    clean = identifier.strip().lstrip("@").lower()
    clean_raw = identifier.strip().lstrip("@")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE LOWER(id) = ? 
           OR LOWER(email) = ? 
           OR phone = ? 
           OR UPPER(pan) = ?
           OR LOWER(username) = ?
        ORDER BY CASE WHEN id = 'default' THEN 1 ELSE 0 END, created_at DESC
        LIMIT 1
    """, (clean, clean, clean_raw, clean_raw.upper(), clean))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)

    if is_supabase_enabled():
        for query_field, query_val in [("username", clean), ("email", clean), ("phone", clean_raw), ("id", clean_raw)]:
            try:
                res = supabase_api("GET", "users", params={query_field: f"eq.{query_val}", "select": "*"})
                if res and isinstance(res, list) and len(res) > 0:
                    sb_u = res[0]
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT OR REPLACE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sb_u.get("id"), sb_u.get("name"), sb_u.get("email"), sb_u.get("phone"),
                            sb_u.get("pan"), sb_u.get("bank_name"), sb_u.get("bank_account"), sb_u.get("pin"),
                            float(sb_u.get("balance", 1000000.0)), float(sb_u.get("total_deposited", 1000000.0)),
                            sb_u.get("avatar_color", "#0EA5E9"), sb_u.get("username"), sb_u.get("password")
                        ))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass
                    return sb_u
            except Exception:
                pass

    return None

# --- Account & Balances ---
def get_account(user_id: str = "default") -> Dict[str, Any]:
    # 1. Try Supabase first
    if is_supabase_enabled() and user_id and user_id != "guest":
        res = supabase_api("GET", "users", params={"id": f"eq.{user_id}", "select": "balance,total_deposited"})
        if res and isinstance(res, list) and len(res) > 0:
            return {"balance": float(res[0].get("balance", 1000000.0)), "total_deposited": float(res[0].get("total_deposited", 1000000.0))}

    # 2. SQLite fallback
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

def get_symbol_variants(symbol: str) -> List[str]:
    clean = (symbol or "").strip().upper()
    variants = [clean]
    if clean.endswith(".NS") or clean.endswith(".BO"):
        base = clean[:-3]
        variants.append(base)
    elif not clean.startswith("^"):
        variants.append(clean + ".NS")
        variants.append(clean + ".BO")
    return list(dict.fromkeys(variants))

def get_available_sell_quantity(cursor, user_id: str, symbol: str, product_type: str, owned_quantity: float) -> float:
    """Return inventory not already committed to another pending sell order."""
    variants = get_symbol_variants(symbol)
    clause = " OR ".join(["UPPER(symbol) = ?"] * len(variants))
    cursor.execute(f"""
        SELECT COALESCE(SUM(quantity), 0) AS reserved
        FROM orders
        WHERE user_id = ? AND order_type = 'SELL' AND product_type = ?
          AND status IN ('OPEN', 'TRIGGER_PENDING', 'EXECUTING')
          AND ({clause})
    """, [user_id, product_type] + [v.upper() for v in variants])
    reserved = float(cursor.fetchone()["reserved"] or 0.0)
    return max(0.0, float(owned_quantity) - reserved)

def sync_holdings_from_supabase_into_cursor(cursor, user_id: str):
    if not is_supabase_enabled() or not user_id or user_id in ["guest", "default"]:
        return None
    try:
        res = supabase_api("GET", "holdings", params={"user_id": f"eq.{user_id}", "quantity": "gt.0", "select": "symbol,name,asset_type,quantity,avg_price,updated_at"})
        if res is not None and isinstance(res, list):
            cursor.execute("DELETE FROM holding_tombstones WHERE deleted_at < datetime('now', '-5 minutes')")
            cursor.execute("SELECT symbol FROM holding_tombstones WHERE user_id = ?", (user_id,))
            tombstone_variants = {
                variant.upper()
                for row in cursor.fetchall()
                for variant in get_symbol_variants(row["symbol"])
            }
            cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, updated_at FROM holdings WHERE user_id = ? AND quantity > 0", (user_id,))
            local_rows = cursor.fetchall()
            local_map = {(r["symbol"] or "").upper(): dict(r) for r in local_rows}

            sb_symbols = set()
            for h in res:
                sb_sym = (h["symbol"] or "").upper()
                if sb_sym in tombstone_variants:
                    # Retry the idempotent delete. Do not restore an already-sold
                    # holding from a delayed Supabase response.
                    supabase_api("DELETE", "holdings", params={
                        "user_id": f"eq.{user_id}",
                        "symbol": f"eq.{h['symbol']}"
                    })
                    continue
                sb_symbols.add(sb_sym)
                cursor.execute("""
                    INSERT OR REPLACE INTO holdings (user_id, symbol, name, asset_type, quantity, avg_price, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    h["symbol"], 
                    h.get("name", h["symbol"]), 
                    h.get("asset_type", "STOCK"), 
                    float(h["quantity"]), 
                    float(h["avg_price"]), 
                    h.get("updated_at")
                ))

            # Push any local holdings that Supabase doesn't have yet
            for l_sym, l_data in local_map.items():
                matching_vars = get_symbol_variants(l_sym)
                if not any(v in sb_symbols for v in matching_vars):
                    try:
                        supabase_api("POST", "holdings?on_conflict=user_id,symbol", payload={
                            "user_id": user_id,
                            "symbol": l_data["symbol"],
                            "name": l_data["name"],
                            "asset_type": l_data["asset_type"],
                            "quantity": float(l_data["quantity"]),
                            "avg_price": float(l_data["avg_price"])
                        })
                    except Exception:
                        pass
            return res
    except Exception as sync_e:
        print(f"[Supabase Holdings Sync Error] {sync_e}")
    return None

def sync_positions_from_supabase_into_cursor(cursor, user_id: str):
    if not is_supabase_enabled() or not user_id or user_id in ["guest", "default"]:
        return None
    try:
        res = supabase_api("GET", "positions", params={"user_id": f"eq.{user_id}", "quantity": "gt.0", "select": "symbol,name,asset_type,quantity,avg_price,margin_used,product_type,updated_at"})
        if res is not None and isinstance(res, list):
            cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, margin_used, product_type, updated_at FROM positions WHERE user_id = ? AND quantity > 0", (user_id,))
            local_rows = cursor.fetchall()
            local_map = {(r["symbol"] or "").upper(): dict(r) for r in local_rows}

            sb_symbols = set()
            for p in res:
                sb_sym = (p["symbol"] or "").upper()
                sb_symbols.add(sb_sym)
                cursor.execute("""
                    INSERT OR REPLACE INTO positions (user_id, symbol, name, asset_type, quantity, avg_price, margin_used, product_type, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    p["symbol"], 
                    p.get("name", p["symbol"]), 
                    p.get("asset_type", "STOCK"), 
                    float(p["quantity"]), 
                    float(p["avg_price"]), 
                    float(p.get("margin_used", 0.0)), 
                    p.get("product_type", "INTRADAY"), 
                    p.get("updated_at")
                ))

            for l_sym, l_data in local_map.items():
                matching_vars = get_symbol_variants(l_sym)
                if not any(v in sb_symbols for v in matching_vars):
                    try:
                        supabase_api("POST", "positions?on_conflict=user_id,symbol", payload={
                            "user_id": user_id,
                            "symbol": l_data["symbol"],
                            "name": l_data["name"],
                            "asset_type": l_data["asset_type"],
                            "quantity": float(l_data["quantity"]),
                            "avg_price": float(l_data["avg_price"]),
                            "margin_used": float(l_data.get("margin_used", 0.0)),
                            "product_type": l_data.get("product_type", "INTRADAY")
                        })
                    except Exception:
                        pass
            return res
    except Exception as sync_e:
        print(f"[Supabase Positions Sync Error] {sync_e}")
    return None

def get_holdings(user_id: str = "default") -> List[Dict[str, Any]]:
    # 1. Try Supabase merge first
    if is_supabase_enabled() and user_id and user_id != "guest" and should_sync_remote("holdings", user_id):
        try:
            drain_sync_outbox(user_id)
            conn = get_connection()
            cursor = conn.cursor()
            sync_holdings_from_supabase_into_cursor(cursor, user_id)
            conn.commit()
            conn.close()
        except Exception:
            pass

    # 2. SQLite read
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
    # 1. Try Supabase merge first
    if is_supabase_enabled() and user_id and user_id != "guest" and should_sync_remote("positions", user_id):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            sync_positions_from_supabase_into_cursor(cursor, user_id)
            conn.commit()
            conn.close()
        except Exception:
            pass

    # 2. SQLite read
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
    user_id: str = "default",
    trigger_price: Optional[float] = None
) -> Dict[str, Any]:
    symbol = (symbol or "").strip().upper()
    order_type = order_type.upper()
    product_type = product_type.upper()
    order_variety = order_variety.upper()
    asset_type = asset_type.upper()
    quantity = float(quantity)
    price = float(price)

    if quantity <= 0 or price <= 0:
        return {"success": False, "error": "Quantity and price must be greater than zero."}
    if order_variety == "LIMIT" and (limit_price is None or float(limit_price) <= 0):
        return {"success": False, "error": "A valid limit price is required for a Limit order."}
    if order_variety in ("STOP_LOSS", "SL") and (trigger_price is None or float(trigger_price) <= 0):
        return {"success": False, "error": "A valid trigger price is required for a Stop-Loss order."}

    effective_price = limit_price if (order_variety == "LIMIT" and limit_price and limit_price > 0) else price
    total_amount = round(quantity * effective_price, 2)

    # Margin requirements: 20% for regular Intraday stocks (5x leverage), 100% for Delivery CNC & Options
    if product_type == "INTRADAY" and asset_type != "OPTION":
        required_margin = round(total_amount * 0.20, 2)
    else:
        required_margin = total_amount

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Fetch current balance
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        acc_row = cursor.fetchone()
        if not acc_row:
            cursor.execute("""
                INSERT OR IGNORE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited)
                VALUES (?, ?, 'trader@stoxify.com', '9876543210', 'ABCDE1234F', 'HDFC Bank', '50100234567890', '', 1000000.0, 1000000.0)
            """, (user_id, "Default Trader" if user_id == "default" else "Trader"))
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            acc_row = cursor.fetchone()
        balance = acc_row["balance"] if acc_row else 1000000.0

        sym_variants = get_symbol_variants(symbol)
        sym_clause = " OR ".join(["UPPER(symbol) = ?"] * len(sym_variants))
        sym_params = [v.upper() for v in sym_variants]

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
                tbl = "positions" if (product_type == "INTRADAY" or asset_type == "OPTION") else "holdings"
                cursor.execute(f"SELECT id, symbol, quantity FROM {tbl} WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                existing = cursor.fetchone()
                if (not existing or get_available_sell_quantity(cursor, user_id, symbol, product_type, existing["quantity"]) < quantity) and is_supabase_enabled() and user_id != "guest":
                    if tbl == "positions":
                        sync_positions_from_supabase_into_cursor(cursor, user_id)
                    else:
                        sync_holdings_from_supabase_into_cursor(cursor, user_id)
                    cursor.execute(f"SELECT id, symbol, quantity FROM {tbl} WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                    existing = cursor.fetchone()

                # Cross-product check if primary table doesn't have sufficient quantity
                if not existing or get_available_sell_quantity(cursor, user_id, symbol, product_type, existing["quantity"]) < quantity:
                    alt_tbl = "holdings" if tbl == "positions" else "positions"
                    cursor.execute(f"SELECT id, symbol, quantity FROM {alt_tbl} WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                    alt_existing = cursor.fetchone()
                    alt_product = "DELIVERY" if alt_tbl == "holdings" else "INTRADAY"
                    if alt_existing and get_available_sell_quantity(cursor, user_id, symbol, alt_product, alt_existing["quantity"]) >= quantity:
                        product_type = "DELIVERY" if alt_tbl == "holdings" else "INTRADAY"
                        existing = alt_existing
                    else:
                        avail = (existing["quantity"] if existing else 0) + (alt_existing["quantity"] if alt_existing else 0)
                        conn.close()
                        if avail <= 0:
                            return {"success": False, "error": f"You do not own any shares of {symbol} to place a Limit SELL."}
                        return {"success": False, "error": f"Insufficient quantity to place Limit SELL. Available: {avail}, Requested: {quantity}"}

            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, trigger_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 0.0)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, required_margin, order_variety, limit_price, trigger_price or 0.0, order_tag))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {
                "success": True, 
                "order_id": order_id, 
                "status": "OPEN", 
                "message": f"Limit {order_type} order placed for {quantity} {symbol} at ₹{effective_price:,.2f} (Status: Open)"
            }

        # Stop-Loss Orders (SL-Limit) check
        is_pending_sl = False
        if order_variety in ["STOP_LOSS", "SL"] and trigger_price and trigger_price > 0:
            if order_type == "SELL" and price > trigger_price:
                is_pending_sl = True
            elif order_type == "BUY" and price < trigger_price:
                is_pending_sl = True

        if is_pending_sl:
            if order_type == "BUY":
                if balance < required_margin:
                    conn.close()
                    return {"success": False, "error": f"Insufficient margin for Stop-Loss BUY. Required: ₹{required_margin:,.2f}, Available: ₹{balance:,.2f}"}
                new_balance = round(balance - required_margin, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))
            else:
                tbl = "positions" if (product_type == "INTRADAY" or asset_type == "OPTION") else "holdings"
                cursor.execute(f"SELECT id, symbol, quantity FROM {tbl} WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                existing = cursor.fetchone()
                if (not existing or get_available_sell_quantity(cursor, user_id, symbol, product_type, existing["quantity"]) < quantity) and is_supabase_enabled() and user_id != "guest":
                    if tbl == "positions":
                        sync_positions_from_supabase_into_cursor(cursor, user_id)
                    else:
                        sync_holdings_from_supabase_into_cursor(cursor, user_id)
                    cursor.execute(f"SELECT id, symbol, quantity FROM {tbl} WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                    existing = cursor.fetchone()

                if not existing or get_available_sell_quantity(cursor, user_id, symbol, product_type, existing["quantity"]) < quantity:
                    alt_tbl = "holdings" if tbl == "positions" else "positions"
                    cursor.execute(f"SELECT id, symbol, quantity FROM {alt_tbl} WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                    alt_existing = cursor.fetchone()
                    alt_product = "DELIVERY" if alt_tbl == "holdings" else "INTRADAY"
                    if alt_existing and get_available_sell_quantity(cursor, user_id, symbol, alt_product, alt_existing["quantity"]) >= quantity:
                        product_type = "DELIVERY" if alt_tbl == "holdings" else "INTRADAY"
                        existing = alt_existing
                    else:
                        avail = (existing["quantity"] if existing else 0) + (alt_existing["quantity"] if alt_existing else 0)
                        conn.close()
                        if avail <= 0:
                            return {"success": False, "error": f"You do not own any shares of {symbol} to place a Stop-Loss SELL."}
                        return {"success": False, "error": f"Insufficient quantity to place Stop-Loss SELL. Available: {avail}, Requested: {quantity}"}

            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, trigger_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TRIGGER_PENDING', 0.0)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, required_margin, order_variety, limit_price or effective_price, trigger_price, order_tag))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return {
                "success": True, 
                "order_id": order_id, 
                "status": "TRIGGER_PENDING", 
                "message": f"Stop-Loss {order_type} placed for {quantity} {symbol}. Trigger Price: ₹{trigger_price:,.2f} (Status: Trigger Pending)"
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
                cursor.execute(f"SELECT id, symbol, quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                pos = cursor.fetchone()
                if pos:
                    matched_sym = pos["symbol"]
                    curr_qty = pos["quantity"]
                    curr_avg = pos["avg_price"]
                    curr_margin = pos["margin_used"]
                    new_qty = curr_qty + quantity
                    new_avg = round(((curr_qty * curr_avg) + total_amount) / new_qty, 2)
                    new_margin_used = round(curr_margin + required_margin, 2)
                    cursor.execute("""
                        UPDATE positions SET quantity = ?, avg_price = ?, margin_used = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ? AND UPPER(symbol) = ?
                    """, (new_qty, new_avg, new_margin_used, user_id, matched_sym.upper()))
                else:
                    cursor.execute("""
                        INSERT INTO positions (user_id, symbol, name, asset_type, quantity, avg_price, margin_used, product_type) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'INTRADAY')
                    """, (user_id, symbol, name, asset_type, quantity, effective_price, required_margin))
            else:
                cursor.execute(f"SELECT id, symbol, quantity, avg_price FROM holdings WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                existing = cursor.fetchone()
                if existing:
                    matched_sym = existing["symbol"]
                    curr_qty = existing["quantity"]
                    curr_avg = existing["avg_price"]
                    new_qty = curr_qty + quantity
                    new_avg = round(((curr_qty * curr_avg) + total_amount) / new_qty, 2)
                    cursor.execute("""
                        UPDATE holdings SET quantity = ?, avg_price = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ? AND UPPER(symbol) = ?
                    """, (new_qty, new_avg, user_id, matched_sym.upper()))
                else:
                    cursor.execute("""
                        INSERT INTO holdings (user_id, symbol, name, asset_type, quantity, avg_price) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, symbol, name, asset_type, quantity, effective_price))
                cursor.execute(f"DELETE FROM holding_tombstones WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)

            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Sync to Supabase
            if is_supabase_enabled() and user_id != "guest":
                try:
                    supabase_api("PATCH", f"users?id=eq.{user_id}", payload={"balance": new_balance, "updated_at": datetime.utcnow().isoformat()})
                    if product_type == "INTRADAY":
                        sb_qty = new_qty if pos else quantity
                        sb_avg = new_avg if pos else effective_price
                        sb_margin = new_margin_used if pos else required_margin
                        sb_sym = matched_sym if pos else symbol
                        supabase_api("POST", "positions?on_conflict=user_id,symbol", payload={
                            "user_id": user_id, "symbol": sb_sym, "name": name, "asset_type": asset_type,
                            "quantity": sb_qty, "avg_price": sb_avg, "margin_used": sb_margin, "product_type": "INTRADAY"
                        })
                    else:
                        sb_qty = new_qty if existing else quantity
                        sb_avg = new_avg if existing else effective_price
                        sb_sym = matched_sym if existing else symbol
                        supabase_api("POST", "holdings?on_conflict=user_id,symbol", payload={
                            "user_id": user_id, "symbol": sb_sym, "name": name, "asset_type": asset_type,
                            "quantity": sb_qty, "avg_price": sb_avg
                        })
                    supabase_api("POST", "orders", payload={
                        "user_id": user_id, "symbol": symbol, "name": name, "asset_type": asset_type,
                        "order_type": order_type, "product_type": product_type, "quantity": quantity,
                        "price": effective_price, "total_amount": total_amount, "order_variety": order_variety,
                        "status": order_status, "realized_pnl": 0.0
                    })
                except Exception as sb_e:
                    print(f"[Supabase Trade Sync Warning] {sb_e}")

            tag_msg = " as After-Market Order (AMO)" if order_tag == "AMO" else ""
            return {"success": True, "order_id": order_id, "status": order_status, "message": f"Successfully purchased {quantity} {symbol} at ₹{effective_price:,.2f}{tag_msg}"}

        elif order_type == "SELL":
            # Fetch both positions (Intraday) and holdings (Delivery)
            cursor.execute(f"SELECT id, symbol, quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
            pos = cursor.fetchone()

            cursor.execute(f"SELECT id, symbol, quantity, avg_price FROM holdings WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
            deliv_hold = cursor.fetchone()

            # Sync from Supabase if both are missing or insufficient
            need_sync = False
            if product_type == "INTRADAY":
                if (not pos or pos["quantity"] < quantity) and (not deliv_hold or deliv_hold["quantity"] < quantity):
                    need_sync = True
            else:
                if (not deliv_hold or deliv_hold["quantity"] < quantity) and (not pos or pos["quantity"] < quantity):
                    need_sync = True

            if need_sync and is_supabase_enabled() and user_id != "guest":
                sync_positions_from_supabase_into_cursor(cursor, user_id)
                sync_holdings_from_supabase_into_cursor(cursor, user_id)
                cursor.execute(f"SELECT id, symbol, quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                pos = cursor.fetchone()
                cursor.execute(f"SELECT id, symbol, quantity, avg_price FROM holdings WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
                deliv_hold = cursor.fetchone()

            # Smart Cross-Product Auto-Routing:
            # If user requested Intraday but only has Delivery shares, sell Delivery!
            # If user requested Delivery but only has Intraday shares, square off Intraday!
            available_intra = get_available_sell_quantity(cursor, user_id, symbol, "INTRADAY", pos["quantity"] if pos else 0)
            available_deliv = get_available_sell_quantity(cursor, user_id, symbol, "DELIVERY", deliv_hold["quantity"] if deliv_hold else 0)
            actual_product = product_type
            if product_type == "INTRADAY":
                if available_intra < quantity and available_deliv >= quantity:
                    actual_product = "DELIVERY"
            else:
                if available_deliv < quantity and available_intra >= quantity:
                    actual_product = "INTRADAY"

            if actual_product == "INTRADAY":
                avail_intra = get_available_sell_quantity(cursor, user_id, symbol, "INTRADAY", pos["quantity"] if pos else 0)
                avail_deliv = get_available_sell_quantity(cursor, user_id, symbol, "DELIVERY", deliv_hold["quantity"] if deliv_hold else 0)
                if not pos or avail_intra < quantity:
                    total_avail = avail_intra + avail_deliv
                    conn.close()
                    if total_avail <= 0:
                        return {"success": False, "error": f"You do not own any shares of {symbol} to sell."}
                    return {"success": False, "error": f"Insufficient shares to sell {symbol}. You have {avail_intra} in Intraday and {avail_deliv} in Delivery ({total_avail} total), but requested to sell {quantity}."}

                matched_symbol = pos["symbol"]
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
                    cursor.execute("DELETE FROM positions WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, matched_symbol.upper()))
                else:
                    new_margin = round(curr_margin - margin_released, 2)
                    cursor.execute("UPDATE positions SET quantity = ?, margin_used = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND UPPER(symbol) = ?", (rem_qty, new_margin, user_id, matched_symbol.upper()))

            else: # DELIVERY
                avail_deliv = get_available_sell_quantity(cursor, user_id, symbol, "DELIVERY", deliv_hold["quantity"] if deliv_hold else 0)
                avail_intra = get_available_sell_quantity(cursor, user_id, symbol, "INTRADAY", pos["quantity"] if pos else 0)
                if not deliv_hold or avail_deliv < quantity:
                    total_avail = avail_deliv + avail_intra
                    conn.close()
                    if total_avail <= 0:
                        return {"success": False, "error": f"You do not own any shares of {symbol} to sell."}
                    return {"success": False, "error": f"Insufficient shares to sell {symbol}. You have {avail_deliv} in Delivery and {avail_intra} in Intraday ({total_avail} total), but requested to sell {quantity}."}

                matched_symbol = deliv_hold["symbol"]
                curr_qty = deliv_hold["quantity"]
                avg_price = deliv_hold["avg_price"]
                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                new_balance = round(balance + total_amount, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                rem_qty = round(curr_qty - quantity, 4)
                if rem_qty <= 0.0001:
                    cursor.execute("DELETE FROM holdings WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, matched_symbol.upper()))
                    cursor.execute("""
                        INSERT OR REPLACE INTO holding_tombstones (user_id, symbol, deleted_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, (user_id, matched_symbol))
                    enqueue_sync_operation(cursor, user_id, "DELETE", "holdings", filters={
                        "user_id": f"eq.{user_id}",
                        "symbol": f"eq.{matched_symbol}"
                    })
                else:
                    cursor.execute("UPDATE holdings SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND UPPER(symbol) = ?", (rem_qty, user_id, matched_symbol.upper()))

            product_type = actual_product
            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status, realized_pnl))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Sync to Supabase
            if is_supabase_enabled() and user_id != "guest":
                try:
                    supabase_api("PATCH", f"users?id=eq.{user_id}", payload={"balance": new_balance, "updated_at": datetime.utcnow().isoformat()})
                    if product_type == "INTRADAY":
                        if rem_qty <= 0.0001:
                            supabase_api("DELETE", f"positions?user_id=eq.{user_id}&symbol=eq.{urllib.parse.quote(matched_symbol)}")
                        else:
                            supabase_api("POST", "positions?on_conflict=user_id,symbol", payload={
                                "user_id": user_id, "symbol": matched_symbol, "name": name, "asset_type": asset_type,
                                "quantity": rem_qty, "avg_price": avg_price, "margin_used": new_margin, "product_type": "INTRADAY"
                            })
                    else:
                        if rem_qty <= 0.0001:
                            supabase_api("DELETE", "holdings", params={
                                "user_id": f"eq.{user_id}",
                                "symbol": f"eq.{matched_symbol}"
                            })
                        else:
                            supabase_api("POST", "holdings?on_conflict=user_id,symbol", payload={
                                "user_id": user_id, "symbol": matched_symbol, "name": name, "asset_type": asset_type,
                                "quantity": rem_qty, "avg_price": avg_price
                            })
                    supabase_api("POST", "orders", payload={
                        "user_id": user_id, "symbol": symbol, "name": name, "asset_type": asset_type,
                        "order_type": order_type, "product_type": product_type, "quantity": quantity,
                        "price": effective_price, "total_amount": total_amount, "order_variety": order_variety,
                        "status": order_status, "realized_pnl": realized_pnl
                    })
                except Exception as sb_e:
                    print(f"[Supabase Trade Sync Warning] {sb_e}")

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
    sym_variants = get_symbol_variants(symbol)
    sym_clause = " OR ".join(["UPPER(symbol) = ?"] * len(sym_variants))
    sym_params = [v.upper() for v in sym_variants]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT symbol, name, asset_type, quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
    pos = cursor.fetchone()

    if not pos and is_supabase_enabled() and user_id != "guest":
        sync_positions_from_supabase_into_cursor(cursor, user_id)
        conn.commit()
        cursor.execute(f"SELECT symbol, name, asset_type, quantity, avg_price, margin_used FROM positions WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
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
        cursor.execute("""
            SELECT id, user_id, symbol, order_type, total_amount, status
            FROM orders WHERE id = ? AND user_id = ?
        """, (order_id, user_id))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return {"success": False, "error": f"Order #{order_id} not found"}

        if order["status"] not in ("OPEN", "TRIGGER_PENDING"):
            conn.close()
            return {"success": False, "error": f"Cannot cancel order #{order_id} with status '{order['status']}'"}

        # Claim the pending order before releasing funds. Concurrent pollers
        # then see a non-pending state and cannot refund/fill it twice.
        cursor.execute("""
            UPDATE orders SET status = 'CANCELLING'
            WHERE id = ? AND status IN ('OPEN', 'TRIGGER_PENDING')
        """, (order_id,))
        if cursor.rowcount != 1:
            conn.rollback()
            conn.close()
            return {"success": False, "error": f"Order #{order_id} is already being processed"}

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
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, trigger_price, total_amount, status 
            FROM orders WHERE status IN ('OPEN', 'TRIGGER_PENDING') AND symbol = ? AND user_id = ?
        """, (symbol, user_id))
    else:
        cursor.execute("""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, trigger_price, total_amount, status 
            FROM orders WHERE status IN ('OPEN', 'TRIGGER_PENDING') AND symbol = ?
        """, (symbol,))
    pending_orders = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for o in pending_orders:
        should_fill = False
        if o["status"] == "OPEN":
            if o["order_type"] == "BUY" and current_price <= o["limit_price"]:
                should_fill = True
            elif o["order_type"] == "SELL" and current_price >= o["limit_price"]:
                should_fill = True
        elif o["status"] == "TRIGGER_PENDING":
            if o["order_type"] == "SELL" and o.get("trigger_price") and current_price <= o["trigger_price"]:
                should_fill = True
            elif o["order_type"] == "BUY" and o.get("trigger_price") and current_price >= o["trigger_price"]:
                should_fill = True

        if should_fill:
            # Only the worker that successfully cancels/releases this pending
            # order may execute it. This prevents duplicate fills on polling.
            released = cancel_order(o["id"], user_id=o["user_id"])
            if released.get("success"):
                execute_trade(
                    symbol=o["symbol"],
                    name=o["name"],
                    asset_type=o["asset_type"],
                    order_type=o["order_type"],
                    product_type=o["product_type"],
                    quantity=o["quantity"],
                    price=current_price,
                    order_variety="MARKET",
                    user_id=o["user_id"]
                )

def get_orders(limit: int = 100, status_filter: Optional[str] = None, user_id: str = "default") -> List[Dict[str, Any]]:
    # 1. Try Supabase first
    if is_supabase_enabled() and user_id and user_id != "guest":
        params = {"user_id": f"eq.{user_id}", "order": "id.desc", "limit": str(limit)}
        if status_filter:
            params["status"] = f"eq.{status_filter}"
        res = supabase_api("GET", "orders", params=params)
        if res is not None and isinstance(res, list) and len(res) > 0:
            return res

    # 2. SQLite fallback
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
    # 1. Try Supabase first
    if is_supabase_enabled() and user_id and user_id != "guest":
        res = supabase_api("GET", "watchlist", params={"user_id": f"eq.{user_id}", "order": "added_at.desc", "select": "symbol,name,asset_type,added_at"})
        if res is not None and isinstance(res, list) and len(res) > 0:
            return res

    # 2. SQLite fallback
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

    if is_supabase_enabled() and user_id and user_id != "guest":
        supabase_api("POST", "watchlist", payload={
            "user_id": user_id,
            "symbol": symbol,
            "name": name,
            "asset_type": asset_type
        })
    return True

def remove_from_watchlist(symbol: str, user_id: str = "default") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE user_id = ? AND symbol = ?", (user_id, symbol))
    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id and user_id != "guest":
        supabase_api("DELETE", f"watchlist?user_id=eq.{user_id}&symbol=eq.{urllib.parse.quote(symbol)}")
    return True

def deposit_funds(amount: float, user_id: str = "default") -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_deposited FROM users WHERE id = ?", (user_id,))
    acc = cursor.fetchone()
    curr_bal = acc["balance"] if acc else 0.0
    curr_dep = acc["total_deposited"] if acc else 0.0
    if curr_bal >= 1000000.0:
        conn.close()
        raise ValueError("Account balance is already at the maximum limit of ₹10,00,000. Cannot add more funds.")
    if curr_bal + amount > 1000000.0:
        amount = 1000000.0 - curr_bal
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

    # Sync to Supabase
    if is_supabase_enabled() and user_id and user_id != "guest":
        supabase_api("PATCH", f"users?id=eq.{user_id}", payload={
            "balance": new_balance,
            "total_deposited": new_deposited,
            "updated_at": datetime.utcnow().isoformat()
        })
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
    cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM sync_outbox WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM gtt_orders WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM sips WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM ipo_bids WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    # Sync to Supabase
    if is_supabase_enabled() and user_id and user_id != "guest":
        supabase_api("PATCH", f"users?id=eq.{user_id}", payload={
            "balance": initial_balance,
            "total_deposited": initial_balance,
            "updated_at": datetime.utcnow().isoformat()
        })
        supabase_api("DELETE", f"holdings?user_id=eq.{user_id}")
        supabase_api("DELETE", f"positions?user_id=eq.{user_id}")
        supabase_api("DELETE", f"orders?user_id=eq.{user_id}")

def restore_balance(user_id: str = "default", target_balance: float = 1000000.0) -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (target_balance, target_balance, user_id))
    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, total_deposited = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (target_balance, target_balance))
    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id and user_id != "guest":
        try:
            supabase_api("PATCH", f"users?id=eq.{user_id}", payload={
                "balance": target_balance,
                "total_deposited": target_balance,
                "updated_at": datetime.utcnow().isoformat()
            })
        except Exception:
            pass
    return target_balance

def delete_user(user_id: str) -> bool:
    if not user_id or user_id == "guest":
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM sync_outbox WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM gtt_orders WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM sips WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM ipo_bids WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if user_id == "default":
        cursor.execute("DELETE FROM holdings")
        cursor.execute("DELETE FROM holding_tombstones")
        cursor.execute("DELETE FROM sync_outbox")
        cursor.execute("DELETE FROM positions")
        cursor.execute("DELETE FROM orders")
        cursor.execute("UPDATE account SET balance = 1000000.0, total_deposited = 1000000.0 WHERE id = 1")
    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id != "default":
        try:
            supabase_api("DELETE", f"holdings?user_id=eq.{user_id}")
            supabase_api("DELETE", f"positions?user_id=eq.{user_id}")
            supabase_api("DELETE", f"orders?user_id=eq.{user_id}")
            supabase_api("DELETE", f"watchlist?user_id=eq.{user_id}")
            supabase_api("DELETE", f"gtt_orders?user_id=eq.{user_id}")
            supabase_api("DELETE", f"sips?user_id=eq.{user_id}")
            supabase_api("DELETE", f"ipo_bids?user_id=eq.{user_id}")
            supabase_api("DELETE", f"users?id=eq.{user_id}")
        except Exception:
            pass
    return True

# --- GTT (Good Till Triggered) Orders ---
def place_gtt_order(
    user_id: str,
    symbol: str,
    name: str,
    trigger_price: float,
    quantity: float,
    action: str = "BUY",
    product_type: str = "DELIVERY",
    target_price: float = 0.0,
    stop_loss_price: float = 0.0
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO gtt_orders (user_id, symbol, name, product_type, action, quantity, trigger_price, target_price, stop_loss_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
    """, (user_id, symbol, name, product_type.upper(), action.upper(), quantity, trigger_price, target_price, stop_loss_price))
    gtt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "gtt_id": gtt_id, "message": f"GTT order created for {quantity} {symbol} at trigger ₹{trigger_price:,.2f}"}

def get_gtt_orders(user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gtt_orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cancel_gtt_order(user_id: str, gtt_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE gtt_orders SET status = 'CANCELLED' WHERE id = ? AND user_id = ?", (gtt_id, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"GTT Order #{gtt_id} cancelled"}

# --- SIP (Systematic Investment Plans) ---
def create_sip(user_id: str, fund_id: str, fund_name: str, monthly_amount: float, sip_day: int = 5) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    if now.day < sip_day:
        next_dt = datetime(now.year, now.month, sip_day)
    else:
        month = now.month + 1 if now.month < 12 else 1
        year = now.year if now.month < 12 else now.year + 1
        next_dt = datetime(year, month, sip_day)
    next_date_str = next_dt.strftime("%d %b %Y")

    cursor.execute("""
        INSERT INTO sips (user_id, fund_id, fund_name, monthly_amount, sip_day, status, next_installment_date)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (user_id, fund_id, fund_name, monthly_amount, sip_day, next_date_str))
    sip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "sip_id": sip_id, "next_date": next_date_str, "message": f"SIP of ₹{monthly_amount:,.2f}/mo created for {fund_name} (Scheduled on {sip_day}th of every month)"}

def get_user_sips(user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sips WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cancel_sip(user_id: str, sip_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sips SET status = 'CANCELLED' WHERE id = ? AND user_id = ?", (sip_id, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"SIP #{sip_id} cancelled"}

# --- IPO Application Bidding ---
def apply_ipo(user_id: str, ipo_id: str, ipo_name: str, lots: int, shares: int, bid_price: float, upi_id: str = "trader@okaxis") -> Dict[str, Any]:
    total_blocked = round(lots * shares * bid_price, 2)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    balance = row["balance"] if row else 0.0

    if balance < total_blocked:
        conn.close()
        return {"success": False, "error": f"Insufficient balance for IPO application. Required: ₹{total_blocked:,.2f}, Available: ₹{balance:,.2f}"}

    new_bal = round(balance - total_blocked, 2)
    cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_bal, user_id))
    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_bal,))

    cursor.execute("""
        INSERT INTO ipo_bids (user_id, ipo_id, ipo_name, lots, shares, bid_price, amount_blocked, status, upi_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'APPLIED', ?)
    """, (user_id, ipo_id, ipo_name, lots, lots * shares, bid_price, total_blocked, upi_id))
    bid_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "success": True, 
        "bid_id": bid_id, 
        "amount_blocked": total_blocked,
        "message": f"IPO bid submitted for {lots} lot(s) ({lots*shares} shares) of {ipo_name}. ₹{total_blocked:,.2f} blocked via simulated ASBA mandate."
    }

def get_ipo_bids(user_id: str = "default") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ipo_bids WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cancel_ipo_bid(user_id: str, bid_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT amount_blocked, ipo_name, status FROM ipo_bids WHERE id = ? AND user_id = ?", (bid_id, user_id))
    bid = cursor.fetchone()
    if not bid or bid["status"] != "APPLIED":
        conn.close()
        return {"success": False, "error": "Active IPO bid not found"}

    blocked = bid["amount_blocked"]
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    new_bal = round((row["balance"] if row else 0.0) + blocked, 2)

    cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_bal, user_id))
    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_bal,))
    cursor.execute("UPDATE ipo_bids SET status = 'CANCELLED' WHERE id = ?", (bid_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"IPO application for {bid['ipo_name']} cancelled. ₹{blocked:,.2f} unblocked."}

# --- Capital Gains Tax (Budget 2024 Rules: STCG 20%, LTCG 12.5%) ---
def get_capital_gains_tax_report(user_id: str = "default") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, name, order_type, product_type, quantity, price, realized_pnl, timestamp 
        FROM orders WHERE user_id = ? AND order_type = 'SELL' AND status LIKE 'EXECUTED%'
        ORDER BY id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    total_stcg_profit = 0.0
    total_stcg_loss = 0.0
    total_ltcg_profit = 0.0
    total_ltcg_loss = 0.0
    trades = []

    for r in rows:
        pnl = float(r["realized_pnl"] or 0.0)
        is_ltcg = False
        try:
            order_dt = datetime.strptime(str(r["timestamp"])[:19], "%Y-%m-%d %H:%M:%S")
            days_held = (datetime.now() - order_dt).days
            if r["product_type"] == "DELIVERY" and days_held >= 365:
                is_ltcg = True
        except Exception:
            pass

        if is_ltcg:
            if pnl > 0:
                total_ltcg_profit += pnl
            else:
                total_ltcg_loss += abs(pnl)
        else:
            if pnl > 0:
                total_stcg_profit += pnl
            else:
                total_stcg_loss += abs(pnl)

        trades.append({
            "symbol": r["symbol"],
            "name": r["name"],
            "product_type": r["product_type"],
            "quantity": r["quantity"],
            "sell_price": r["price"],
            "pnl": pnl,
            "tax_type": "LTCG (12.5%)" if is_ltcg else "STCG (20%)",
            "date": str(r["timestamp"])[:10]
        })

    net_stcg = max(0.0, round(total_stcg_profit - total_stcg_loss, 2))
    stcg_tax = round(net_stcg * 0.20, 2)

    net_ltcg = max(0.0, round(total_ltcg_profit - total_ltcg_loss, 2))
    taxable_ltcg = max(0.0, net_ltcg - 125000.0)
    ltcg_tax = round(taxable_ltcg * 0.125, 2)

    return {
        "stcg_profit": round(total_stcg_profit, 2),
        "stcg_loss": round(total_stcg_loss, 2),
        "net_stcg": net_stcg,
        "stcg_realized_gain": net_stcg,
        "stcg_tax_rate": "20%",
        "stcg_tax": stcg_tax,
        "stcg_tax_payable": stcg_tax,
        "ltcg_profit": round(total_ltcg_profit, 2),
        "ltcg_loss": round(total_ltcg_loss, 2),
        "net_ltcg": net_ltcg,
        "ltcg_realized_gain": net_ltcg,
        "ltcg_exemption": 125000.0,
        "taxable_ltcg": taxable_ltcg,
        "ltcg_taxable_gain": taxable_ltcg,
        "ltcg_tax_rate": "12.5%",
        "ltcg_tax": ltcg_tax,
        "ltcg_tax_payable": ltcg_tax,
        "total_tax_liability": round(stcg_tax + ltcg_tax, 2),
        "trades": trades
    }

# --- Sector & Asset Allocation Analytics ---
SECTOR_MAP = {
    "RELIANCE.NS": "Energy & Oil",
    "TCS.NS": "IT & Software",
    "INFY.NS": "IT & Software",
    "HDFCBANK.NS": "Banking & Finance",
    "ICICIBANK.NS": "Banking & Finance",
    "SBIN.NS": "Banking & Finance",
    "FEDERALBNK.NS": "Banking & Finance",
    "TMPV.NS": "Automobile",
    "TATAMOTORS.NS": "Automobile",
    "M&M.NS": "Automobile",
    "MARUTI.NS": "Automobile",
    "ETERNAL.NS": "Consumer Tech",
    "ZOMATO.NS": "Consumer Tech",
    "HAL.NS": "Defense & Aero",
    "BEL.NS": "Defense & Aero",
    "RVNL.NS": "Railways & Infra",
    "IRFC.NS": "Railways & Infra",
    "NTPC.NS": "Power & Energy",
    "TATAPOWER.NS": "Power & Energy",
    "SUNPHARMA.NS": "Healthcare & Pharma",
    "CIPLA.NS": "Healthcare & Pharma",
    "ITC.NS": "FMCG & Consumer",
    "HINDUNILVR.NS": "FMCG & Consumer",
    "TATASTEEL.NS": "Metals & Mining",
    "JSWSTEEL.NS": "Metals & Mining"
}

def get_sector_allocation(user_id: str = "default") -> List[Dict[str, Any]]:
    holdings = get_holdings(user_id)
    if not holdings:
        return []

    sector_totals: Dict[str, float] = {}
    total_val = 0.0

    for h in holdings:
        val = h["quantity"] * h["avg_price"]
        total_val += val
        if h.get("asset_type") == "MUTUAL_FUND":
            sector = "Mutual Funds (Equities)"
        else:
            sector = SECTOR_MAP.get(h["symbol"], "Diversified / Others")
        sector_totals[sector] = sector_totals.get(sector, 0.0) + val

    if total_val <= 0:
        return []

    results = []
    for sector, amt in sector_totals.items():
        pct = round((amt / total_val) * 100, 1)
        results.append({
            "sector": sector,
            "amount": round(amt, 2),
            "percentage": pct
        })
    results.sort(key=lambda x: x["amount"], reverse=True)
    return results

