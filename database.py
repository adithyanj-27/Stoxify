import os
import shutil
import sqlite3
import json
import uuid
import calendar
import random
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import concurrent.futures

_TRADE_SYNC_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4)

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
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or DEFAULT_SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

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
        # A database written by an earlier build can already have `users` while
        # missing columns added later (init_db() only runs its ALTERs when it is
        # actually invoked). Probe a column the current code selects.
        cursor.execute("SELECT blocked_amount FROM orders LIMIT 1")
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
    for col in ["dob TEXT", "username TEXT", "password TEXT", "bank_balance REAL DEFAULT 1000000.0", "bank_ifsc TEXT DEFAULT 'HDFC0001234'", "bank_upi_id TEXT DEFAULT ''", "age INTEGER DEFAULT 18", "experience TEXT DEFAULT 'None / Total Beginner'", "has_completed_tour INTEGER DEFAULT 0"]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col}")
            conn.commit()
        except Exception:
            pass

    # Ensure existing users with NULL bank_balance get initialized to 10L
    try:
        cursor.execute("UPDATE users SET bank_balance = 1000000.0 WHERE bank_balance IS NULL")
        cursor.execute("UPDATE users SET has_completed_tour = 1 WHERE has_completed_tour IS NULL")
        conn.commit()
    except Exception:
        pass

    # 1b. Simulated Bank Transactions Ledger (UPI Deposits & Withdrawals)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            from_account TEXT,
            to_account TEXT,
            reference_id TEXT UNIQUE,
            status TEXT DEFAULT 'SUCCESS',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_tx_user ON bank_transactions(user_id, id DESC)")
    conn.commit()

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
        CREATE TABLE IF NOT EXISTS position_tombstones (
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
            charges REAL DEFAULT 0.0,
            net_amount REAL DEFAULT 0.0,
            blocked_amount REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col, definition in [
        ("user_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("order_variety", "TEXT NOT NULL DEFAULT 'MARKET'"),
        ("limit_price", "REAL DEFAULT 0.0"),
        ("order_tag", "TEXT NOT NULL DEFAULT 'NORMAL'"),
        ("trigger_price", "REAL DEFAULT 0.0"),
        ("charges", "REAL DEFAULT 0.0"),
        ("net_amount", "REAL DEFAULT 0.0"),
        ("blocked_amount", "REAL DEFAULT 0.0")
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

    # Deduplicate existing holdings & positions and enforce unique indexes
    try:
        cursor.execute("""
            DELETE FROM holdings WHERE id NOT IN (
                SELECT MAX(id) FROM holdings GROUP BY user_id, symbol
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS holdings_user_symbol_idx ON holdings (user_id, symbol)")
    except Exception:
        pass

    try:
        cursor.execute("""
            DELETE FROM positions WHERE id NOT IN (
                SELECT MAX(id) FROM positions GROUP BY user_id, symbol
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS positions_user_symbol_idx ON positions (user_id, symbol)")
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

def sync_user_to_supabase_auth(
    user_id: str,
    email: str,
    password: Optional[str] = None,
    pin: Optional[str] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    pan: Optional[str] = None,
    username: Optional[str] = None,
    age: Optional[int] = 18,
    experience: Optional[str] = "None / Total Beginner",
    has_completed_tour: Optional[bool] = False
) -> Optional[str]:
    if not is_supabase_enabled():
        return None
    clean_email = (email or "").strip()
    if not clean_email or "@" not in clean_email:
        return None

    clean_password = password.strip() if password else None
    if clean_password and len(clean_password) >= 6:
        pwd = clean_password
    elif pin and len(str(pin)) >= 4:
        pwd = f"stoxify_{pin}" if len(str(pin)) < 6 else str(pin)
    else:
        pwd = f"stoxify_{user_id.replace('-', '_')}"

    clean_age = int(age) if age is not None else 18
    clean_exp = (experience or "None / Total Beginner").strip()

    user_meta = {
        "name": name or "Trader",
        "phone": phone or "",
        "demat": user_id,
        "pin": str(pin or ""),
        "pan": pan or "ABCDE1234F",
        "username": username or "",
        "age": clean_age,
        "experience": clean_exp,
        "has_completed_tour": bool(has_completed_tour)
    }

    auth_id = None
    # 1. Prefer Admin API via service_role key if available for instant confirmation and no rate limits
    if SUPABASE_SERVICE_ROLE_KEY:
        try:
            admin_url = f"{SUPABASE_URL}/auth/v1/admin/users"
            admin_headers = {
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            admin_payload = {
                "email": clean_email,
                "password": pwd,
                "email_confirm": True,
                "user_metadata": user_meta
            }
            req = urllib.request.Request(admin_url, data=json.dumps(admin_payload).encode("utf-8"), headers=admin_headers, method="POST")
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                auth_id = data.get("id") or data.get("user", {}).get("id")
                print(f"[Supabase Auth Admin] Successfully created {clean_email} (auth_id: {auth_id}) in Supabase Authentication -> Users")
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            if he.code == 422 and "user_already_exists" in err_body:
                print(f"[Supabase Auth Admin] User {clean_email} already exists. Searching and updating...")
                try:
                    # Find user auth_id from user list
                    list_req = urllib.request.Request(admin_url, headers=admin_headers)
                    with urllib.request.urlopen(list_req, timeout=5) as list_resp:
                        u_list = json.loads(list_resp.read().decode("utf-8")).get("users", [])
                        for au in u_list:
                            if au.get("email", "").lower() == clean_email.lower():
                                auth_id = au["id"]
                                upd_req = urllib.request.Request(
                                    f"{admin_url}/{auth_id}",
                                    data=json.dumps({"password": pwd, "user_metadata": user_meta}).encode("utf-8"),
                                    headers=admin_headers,
                                    method="PUT"
                                )
                                with urllib.request.urlopen(upd_req, timeout=5):
                                    pass
                                print(f"[Supabase Auth Admin] Successfully updated existing user {clean_email} (auth_id: {auth_id})")
                                break
                except Exception as ex:
                    print(f"[Supabase Auth Admin Note] Update error: {ex}")
            else:
                print(f"[Supabase Auth Admin Note] ({he.code}): {err_body}")
        except Exception as e:
            print(f"[Supabase Auth Admin Note] {e}")

    # 2. Fallback to public GoTrue signup if Admin API was not executed
    if not auth_id:
        try:
            auth_url = f"{SUPABASE_URL}/auth/v1/signup"
            auth_payload = {
                "email": clean_email,
                "password": pwd,
                "data": user_meta
            }
            auth_headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(auth_url, data=json.dumps(auth_payload).encode("utf-8"), headers=auth_headers, method="POST")
            with urllib.request.urlopen(req, timeout=6) as resp:
                content = resp.read().decode("utf-8")
                data = json.loads(content)
                auth_id = data.get("user", {}).get("id") or data.get("id")
                print(f"[Supabase Auth] Successfully registered {clean_email} (auth_id: {auth_id}) in Supabase Authentication -> Users")
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            if he.code == 422 and "user_already_exists" in err_body:
                print(f"[Supabase Auth] Email {clean_email} already exists in auth.users. Linking existing auth account...")
                token_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
                candidates = [pwd, clean_password, f"stoxify_{pin}" if pin else None, str(pin) if pin else None, f"stoxify_{user_id.replace('-', '_')}"]
                for test_pwd in candidates:
                    if not test_pwd:
                        continue
                    try:
                        tok_req = urllib.request.Request(
                            token_url,
                            data=json.dumps({"email": clean_email, "password": test_pwd}).encode("utf-8"),
                            headers=auth_headers,
                            method="POST"
                        )
                        with urllib.request.urlopen(tok_req, timeout=5) as tok_resp:
                            tok_data = json.loads(tok_resp.read().decode("utf-8"))
                            auth_id = tok_data.get("user", {}).get("id")
                            token = tok_data.get("access_token")
                            if token:
                                user_url = f"{SUPABASE_URL}/auth/v1/user"
                                upd_headers = {
                                    "apikey": SUPABASE_KEY,
                                    "Authorization": f"Bearer {token}",
                                    "Content-Type": "application/json"
                                }
                                upd_req = urllib.request.Request(
                                    user_url,
                                    data=json.dumps({"data": auth_payload["data"]}).encode("utf-8"),
                                    headers=upd_headers,
                                    method="PUT"
                                )
                                with urllib.request.urlopen(upd_req, timeout=5):
                                    pass
                            print(f"[Supabase Auth] Successfully linked and updated existing auth account {clean_email} (auth_id: {auth_id})")
                            break
                    except Exception:
                        continue
            else:
                print(f"[Supabase Auth Note] signup response ({he.code}): {err_body}")
        except Exception as e:
            print(f"[Supabase Auth Note] {e}")

    if auth_id and user_id != "default":
        try:
            supabase_api("PATCH", "users", payload={"auth_id": auth_id}, params={"id": f"eq.{user_id}"})
        except Exception:
            pass

    return auth_id

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
    password: Optional[str] = None,
    age: Optional[int] = 18,
    experience: Optional[str] = "None / Total Beginner"
) -> Dict[str, Any]:
    if not user_id:
        user_id = f"STOX-{random.randint(100000, 999999)}"
    palettes = ["#0EA5E9", "#10B981", "#6366F1", "#EC4899", "#F59E0B", "#8B5CF6"]
    avatar_color = palettes[len(name) % len(palettes)]

    clean_username = username.strip().lstrip("@").lower() if username else None
    clean_password = password.strip() if password else None
    bank_ifsc = f"{bank_name.split()[0].upper()[:4]}0001234"
    bank_upi_id = f"{(clean_username or user_id).lower()}@{bank_name.split()[0].lower()}bank"
    clean_age = int(age) if age is not None else 18
    clean_exp = (experience or "None / Total Beginner").strip()
    has_completed_tour = 0

    # 1. Insert into local SQLite (Bank gets ₹10 Lakh initial credit, trading wallet starts at ₹0 until added via UPI)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, name, email, phone, pan, dob, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password, bank_balance, bank_ifsc, bank_upi_id, age, experience, has_completed_tour)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 0.0, ?, ?, ?, 1000000.0, ?, ?, ?, ?, ?)
    """, (user_id, name, (email or "").strip(), phone or "", pan or "ABCDE1234F", dob or "", bank_name, bank_account, pin, avatar_color, clean_username, clean_password, bank_ifsc, bank_upi_id, clean_age, clean_exp, has_completed_tour))

    # Log initial opening deposit in bank_transactions
    cursor.execute("""
        INSERT OR IGNORE INTO bank_transactions (user_id, type, amount, from_account, to_account, reference_id, status, note)
        VALUES (?, 'INITIAL_CREDIT', 1000000.0, 'RBI Simulated Banking Gateway', ?, ?, 'SUCCESS', 'Welcome virtual capital credited to linked bank account')
    """, (user_id, f"{bank_name} A/C •••• {str(bank_account)[-4:]}", f"BANK-INIT-{user_id}"))

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

    # 2. Register into Supabase Authentication -> Users (auth.users)
    auth_id = None
    if is_supabase_enabled():
        auth_id = sync_user_to_supabase_auth(
            user_id=user_id,
            email=email,
            password=clean_password,
            pin=pin,
            name=name,
            phone=phone,
            pan=pan,
            username=clean_username,
            age=clean_age,
            experience=clean_exp,
            has_completed_tour=bool(has_completed_tour)
        )

        # 3. Sync directly to Supabase cloud public users table
        sb_user_payload = {
            "id": user_id,
            "name": name,
            "email": (email or "").strip(),
            "phone": phone or "",
            "pan": pan or "ABCDE1234F",
            "bank_name": bank_name,
            "bank_account": bank_account,
            "pin": pin,
            "balance": 0.0,
            "total_deposited": 0.0,
            "avatar_color": avatar_color,
            "age": clean_age,
            "experience": clean_exp,
            "has_completed_tour": bool(has_completed_tour)
        }
        if auth_id:
            sb_user_payload["auth_id"] = auth_id
        if dob:
            sb_user_payload["dob"] = dob.strip()

        sb_res = supabase_api("POST", "users", payload=sb_user_payload)
        if sb_res is None:
            # Fallback without extra columns in case Supabase schema lacks them
            sb_fallback = dict(sb_user_payload)
            sb_fallback.pop("age", None)
            sb_fallback.pop("experience", None)
            sb_fallback.pop("has_completed_tour", None)
            sb_res = supabase_api("POST", "users", payload=sb_fallback)

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

    return user_data

def mark_tour_completed(user_id: str) -> bool:
    if not user_id or user_id == "guest":
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET has_completed_tour = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    if is_supabase_enabled() and user_id != "default":
        try:
            supabase_api("PATCH", "users", payload={"has_completed_tour": True}, params={"id": f"eq.{user_id}"})
        except Exception:
            pass
    return True

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
            sb_payload["updated_at"] = datetime.now(timezone.utc).isoformat()
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
    if not user_id or user_id == "guest":
        return None

    # 1. Check local SQLite first (instant < 0.5ms)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)

    # 2. Fallback to Supabase if user not found in local SQLite
    if is_supabase_enabled():
        res = supabase_api("GET", "users", params={"id": f"eq.{user_id}", "select": "*"})
        if res and isinstance(res, list) and len(res) > 0:
            sb_u = res[0]
            # Ensure local SQLite cache is populated
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT bank_balance, bank_ifsc, bank_upi_id FROM users WHERE id = ?", (sb_u.get("id"),))
                _b_row = cur.fetchone()
                _b_bal = _b_row["bank_balance"] if _b_row and _b_row["bank_balance"] is not None else float(sb_u.get("bank_balance") or 1000000.0)
                _b_ifsc = _b_row["bank_ifsc"] if _b_row and _b_row["bank_ifsc"] else (sb_u.get("bank_ifsc") or f"{(sb_u.get('bank_name') or 'HDFC').split()[0].upper()[:4]}0001234")
                _b_upi = _b_row["bank_upi_id"] if _b_row and _b_row["bank_upi_id"] else (sb_u.get("bank_upi_id") or f"{(sb_u.get('username') or sb_u.get('id')).lower()}@{(sb_u.get('bank_name') or 'hdfc').split()[0].lower()}bank")

                cur.execute("""
                    INSERT OR REPLACE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password, bank_balance, bank_ifsc, bank_upi_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sb_u.get("id"),
                    sb_u.get("name"),
                    sb_u.get("email"),
                    sb_u.get("phone"),
                    sb_u.get("pan"),
                    sb_u.get("bank_name"),
                    sb_u.get("bank_account"),
                    sb_u.get("pin"),
                    float(sb_u.get("balance") or 0.0),
                    float(sb_u.get("total_deposited") or 0.0),
                    sb_u.get("avatar_color", "#0EA5E9"),
                    sb_u.get("username"),
                    sb_u.get("password"),
                    _b_bal, _b_ifsc, _b_upi
                ))
                conn.commit()
                conn.close()
                sb_u["bank_balance"] = _b_bal
                sb_u["bank_ifsc"] = _b_ifsc
                sb_u["bank_upi_id"] = _b_upi
            except Exception:
                pass
            if sb_u.get("bank_balance") is None:
                sb_u["bank_balance"] = 1000000.0
            if sb_u.get("balance") is None:
                sb_u["balance"] = 0.0
            return sb_u
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
                        cur.execute("SELECT bank_balance, bank_ifsc, bank_upi_id FROM users WHERE id = ?", (sb_u.get("id"),))
                        _b_row = cur.fetchone()
                        _b_bal = _b_row["bank_balance"] if _b_row and _b_row["bank_balance"] is not None else float(sb_u.get("bank_balance", 1000000.0))
                        _b_ifsc = _b_row["bank_ifsc"] if _b_row and _b_row["bank_ifsc"] else sb_u.get("bank_ifsc")
                        _b_upi = _b_row["bank_upi_id"] if _b_row and _b_row["bank_upi_id"] else sb_u.get("bank_upi_id")

                        cur.execute("""
                            INSERT OR REPLACE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password, bank_balance, bank_ifsc, bank_upi_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sb_u.get("id"), sb_u.get("name"), sb_u.get("email"), sb_u.get("phone"),
                            sb_u.get("pan"), sb_u.get("bank_name"), sb_u.get("bank_account"), sb_u.get("pin"),
                            float(sb_u.get("balance", 0.0)), float(sb_u.get("total_deposited", 0.0)),
                            sb_u.get("avatar_color", "#0EA5E9"), sb_u.get("username"), sb_u.get("password"),
                            _b_bal, _b_ifsc, _b_upi
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_deposited, bank_balance FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row and is_supabase_enabled() and user_id and user_id != "guest":
        sync_user_from_supabase_into_cursor(cursor, user_id)
        cursor.execute("SELECT balance, total_deposited, bank_balance FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
    if not row and user_id == "default":
        cursor.execute("SELECT balance, total_deposited FROM account WHERE id = 1")
        row = cursor.fetchone()
    conn.close()
    if row:
        b_bal = float(row["bank_balance"]) if "bank_balance" in row.keys() and row["bank_balance"] is not None else 1000000.0
        return {"balance": row["balance"], "total_deposited": row["total_deposited"], "bank_balance": b_bal, "exists": True}

    # No row for this user id. Returning ₹10,00,000 here made an unknown or stale
    # user id look like a fully funded account.
    return {"balance": 0.0, "total_deposited": 0.0, "bank_balance": 0.0, "exists": False}

# --- Simulated UPI & Bank Account Gateway ---
def transfer_bank_to_wallet(user_id: str, amount: float, pin: str) -> Dict[str, Any]:
    if not user_id or str(user_id).lower() in ["guest", "none", "null", "undefined", ""]:
        return {"success": False, "message": "Authentication required"}
    if amount <= 0:
        return {"success": False, "message": "Transfer amount must be greater than zero"}

    # Fetch user, auto-syncing from Supabase to SQLite if needed
    user = get_user(user_id)
    if not user:
        return {"success": False, "message": "User account not found"}

    stored_pin = (user.get("pin") or "").strip()
    stored_pass = (user.get("password") or "").strip()
    entered_pin = (pin or "").strip()

    pin_valid = False
    if stored_pin and entered_pin == stored_pin:
        pin_valid = True
    elif not stored_pin and stored_pass and entered_pin == stored_pass:
        pin_valid = True
    elif not stored_pin and not stored_pass:
        pin_valid = True

    if not pin_valid:
        return {"success": False, "message": "Incorrect 4-digit Security PIN. Please try again."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password, bank_balance, bank_ifsc, bank_upi_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.get("id"), user.get("name"), user.get("email"), user.get("phone"), user.get("pan"),
            user.get("bank_name"), user.get("bank_account"), user.get("pin"),
            float(user.get("balance") or 0.0), float(user.get("total_deposited") or 0.0),
            user.get("avatar_color", "#0EA5E9"), user.get("username"), user.get("password"),
            float(user.get("bank_balance") if user.get("bank_balance") is not None else 1000000.0), user.get("bank_ifsc"), user.get("bank_upi_id")
        ))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

    db_user = dict(row) if row else dict(user)
    bank_balance = float(db_user.get("bank_balance") if db_user.get("bank_balance") is not None else 1000000.0)
    wallet_balance = float(db_user.get("balance") or 0.0)

    if bank_balance < amount:
        conn.close()
        return {
            "success": False,
            "message": f"Insufficient bank balance. Available in {db_user.get('bank_name', 'Bank')}: ₹{bank_balance:,.2f}"
        }

    new_bank_balance = round(bank_balance - amount, 2)
    new_wallet_balance = round(wallet_balance + amount, 2)
    tx_ref = f"TXN/STX/{random.randint(10000000, 99999999)}"

    cursor.execute("""
        UPDATE users 
        SET bank_balance = ?, balance = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_bank_balance, new_wallet_balance, user_id))

    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_wallet_balance,))

    cursor.execute("""
        INSERT INTO bank_transactions (user_id, type, amount, from_account, to_account, reference_id, status, note)
        VALUES (?, 'BANK_DEPOSIT', ?, ?, 'Stoxifyin Trading Wallet', ?, 'SUCCESS', ?)
    """, (
        user_id,
        amount,
        f"{db_user.get('bank_name', 'Bank')} •••• {str(db_user.get('bank_account', ''))[-4:]}",
        tx_ref,
        "Simulated bank transfer to Stoxifyin trading wallet"
    ))

    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id != "guest":
        try:
            p = {
                "balance": new_wallet_balance,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            supabase_api("PATCH", f"users?id=eq.{user_id}", payload=p)
        except Exception:
            pass

    return {
        "success": True,
        "message": f"₹{amount:,.2f} added to Stoxifyin wallet from your {db_user.get('bank_name', 'Bank')} account!",
        "amount": amount,
        "balance": new_wallet_balance,
        "wallet_balance": new_wallet_balance,
        "bank_balance": new_bank_balance,
        "reference_id": tx_ref,
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

def withdraw_wallet_to_bank(user_id: str, amount: float, pin: str) -> Dict[str, Any]:
    if not user_id or str(user_id).lower() in ["guest", "none", "null", "undefined", ""]:
        return {"success": False, "message": "Authentication required"}
    if amount <= 0:
        return {"success": False, "message": "Withdrawal amount must be greater than zero"}

    user = get_user(user_id)
    if not user:
        return {"success": False, "message": "User account not found"}

    stored_pin = (user.get("pin") or "").strip()
    stored_pass = (user.get("password") or "").strip()
    entered_pin = (pin or "").strip()

    pin_valid = False
    if stored_pin and entered_pin == stored_pin:
        pin_valid = True
    elif not stored_pin and stored_pass and entered_pin == stored_pass:
        pin_valid = True
    elif not stored_pin and not stored_pass:
        pin_valid = True

    if not pin_valid:
        return {"success": False, "message": "Incorrect 4-digit PIN. Please try again."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited, avatar_color, username, password, bank_balance, bank_ifsc, bank_upi_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.get("id"), user.get("name"), user.get("email"), user.get("phone"), user.get("pan"),
            user.get("bank_name"), user.get("bank_account"), user.get("pin"),
            float(user.get("balance") or 0.0), float(user.get("total_deposited") or 0.0),
            user.get("avatar_color", "#0EA5E9"), user.get("username"), user.get("password"),
            float(user.get("bank_balance") if user.get("bank_balance") is not None else 1000000.0), user.get("bank_ifsc"), user.get("bank_upi_id")
        ))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

    db_user = dict(row) if row else dict(user)
    wallet_balance = float(db_user.get("balance") or 0.0)
    bank_balance = float(db_user.get("bank_balance") if db_user.get("bank_balance") is not None else 1000000.0)

    if wallet_balance < amount:
        conn.close()
        return {
            "success": False,
            "message": f"Insufficient trading cash balance. Available to withdraw: ₹{wallet_balance:,.2f}"
        }

    new_wallet_balance = round(wallet_balance - amount, 2)
    new_bank_balance = round(bank_balance + amount, 2)
    tx_ref = f"WDR/STX/{random.randint(10000000, 99999999)}"

    cursor.execute("""
        UPDATE users 
        SET balance = ?, bank_balance = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_wallet_balance, new_bank_balance, user_id))

    if user_id == "default":
        cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_wallet_balance,))

    cursor.execute("""
        INSERT INTO bank_transactions (user_id, type, amount, from_account, to_account, reference_id, status, note)
        VALUES (?, 'WITHDRAWAL', ?, 'Stoxifyin Trading Wallet', ?, ?, 'SUCCESS', ?)
    """, (
        user_id,
        amount,
        f"{db_user.get('bank_name', 'Bank')} •••• {str(db_user.get('bank_account', ''))[-4:]}",
        tx_ref,
        "Instant simulated withdrawal to linked bank account"
    ))

    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id != "guest":
        try:
            p = {
                "balance": new_wallet_balance,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            supabase_api("PATCH", f"users?id=eq.{user_id}", payload=p)
        except Exception:
            pass

    return {
        "success": True,
        "message": f"₹{amount:,.2f} withdrawn to your {db_user.get('bank_name', 'Bank')} account!",
        "amount": amount,
        "balance": new_wallet_balance,
        "wallet_balance": new_wallet_balance,
        "bank_balance": new_bank_balance,
        "reference_id": tx_ref,
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

def get_bank_account_details(user_id: str) -> Dict[str, Any]:
    if not user_id or user_id == "guest":
        return {}
    u = get_user(user_id)
    if not u:
        return {}
    bank_name = u.get("bank_name") or "HDFC Bank"
    bank_account = str(u.get("bank_account") or "50100234567890")
    bank_ifsc = u.get("bank_ifsc") or f"{bank_name.split()[0].upper()[:4]}0001234"
    bank_upi_id = u.get("bank_upi_id") or f"{(u.get('username') or user_id).lower()}@{bank_name.split()[0].lower()}bank"
    bank_balance = float(u.get("bank_balance") if u.get("bank_balance") is not None else 1000000.0)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM bank_transactions 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT 50
    """, (user_id,))
    rows = cursor.fetchall()
    txs = [dict(r) for r in rows]
    conn.close()

    masked = f"•••• {bank_account[-4:]}" if len(bank_account) >= 4 else bank_account

    return {
        "bank_name": bank_name,
        "bank_account": bank_account,
        "bank_masked_account": masked,
        "bank_account_masked": masked,
        "bank_ifsc": bank_ifsc,
        "bank_upi_id": bank_upi_id,
        "bank_balance": bank_balance,
        "wallet_balance": float(u.get("balance") or 0.0),
        "balance": float(u.get("balance") or 0.0),
        "account_holder": u.get("name") or "Trader",
        "transactions": txs
    }

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

def get_executed_delivery_quantity(cursor, user_id: str, symbol: str) -> Optional[float]:
    """Net delivery units from the immutable local order ledger, if known."""
    variants = get_symbol_variants(symbol)
    clause = " OR ".join(["UPPER(symbol) = ?"] * len(variants))
    cursor.execute(f"""
        SELECT order_type, COALESCE(SUM(quantity), 0) AS quantity
        FROM orders
        WHERE user_id = ? AND product_type = 'DELIVERY' AND status LIKE 'EXECUTED%'
          AND ({clause})
        GROUP BY order_type
    """, [user_id] + [v.upper() for v in variants])
    rows = cursor.fetchall()
    if not rows:
        return None
    totals = {row["order_type"]: float(row["quantity"] or 0.0) for row in rows}
    if totals.get("BUY", 0.0) <= 0.0001:
        return None
    return totals.get("BUY", 0.0) - totals.get("SELL", 0.0)

def get_executed_intraday_quantity(cursor, user_id: str, symbol: str) -> Optional[float]:
    variants = get_symbol_variants(symbol)
    clause = " OR ".join(["UPPER(symbol) = ?"] * len(variants))
    cursor.execute(f"""
        SELECT order_type, COALESCE(SUM(quantity), 0) AS quantity
        FROM orders
        WHERE user_id = ? AND product_type = 'INTRADAY' AND status LIKE 'EXECUTED%'
          AND ({clause})
        GROUP BY order_type
    """, [user_id] + [v.upper() for v in variants])
    rows = cursor.fetchall()
    if not rows:
        return None
    totals = {row["order_type"]: float(row["quantity"] or 0.0) for row in rows}
    if totals.get("BUY", 0.0) <= 0.0001:
        return None
    return totals.get("BUY", 0.0) - totals.get("SELL", 0.0)

def sync_user_from_supabase_into_cursor(cursor, user_id: str) -> Optional[Dict[str, Any]]:
    if not is_supabase_enabled() or not user_id or user_id in ["guest"]:
        return None
    try:
        res = supabase_api("GET", "users", params={"id": f"eq.{user_id}", "select": "*"})
        if res and isinstance(res, list) and len(res) > 0:
            sb_u = res[0]
            cursor.execute("SELECT bank_balance, bank_ifsc, bank_upi_id FROM users WHERE id = ?", (sb_u.get("id"),))
            _b_row = cursor.fetchone()
            _b_bal = _b_row["bank_balance"] if _b_row and _b_row["bank_balance"] is not None else float(sb_u.get("bank_balance", 1000000.0))
            _b_ifsc = _b_row["bank_ifsc"] if _b_row and _b_row["bank_ifsc"] else sb_u.get("bank_ifsc")
            _b_upi = _b_row["bank_upi_id"] if _b_row and _b_row["bank_upi_id"] else sb_u.get("bank_upi_id")

            cursor.execute("""
                INSERT OR REPLACE INTO users (
                    id, name, email, phone, pan, bank_name, bank_account, pin, 
                    balance, total_deposited, avatar_color, dob, username, password, updated_at,
                    bank_balance, bank_ifsc, bank_upi_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sb_u.get("id"), sb_u.get("name"), sb_u.get("email"), sb_u.get("phone"),
                sb_u.get("pan"), sb_u.get("bank_name"), sb_u.get("bank_account"), sb_u.get("pin"),
                float(sb_u.get("balance", 0.0)), float(sb_u.get("total_deposited", 0.0)),
                sb_u.get("avatar_color", "#0EA5E9"), sb_u.get("dob", ""), sb_u.get("username"), sb_u.get("password"),
                sb_u.get("updated_at"), _b_bal, _b_ifsc, _b_upi
            ))
            return sb_u
    except Exception as sync_e:
        print(f"[Supabase User Sync Warning] {sync_e}")
    return None

def sync_orders_from_supabase_into_cursor(cursor, user_id: str):
    if not is_supabase_enabled() or not user_id or user_id in ["guest"]:
        return None
    try:
        res = supabase_api("GET", "orders", params={"user_id": f"eq.{user_id}", "order": "id.asc", "limit": "500"})
        if res is not None and isinstance(res, list):
            for o in res:
                cursor.execute("""
                    INSERT OR REPLACE INTO orders (
                        id, user_id, symbol, name, asset_type, order_type, product_type,
                        quantity, price, total_amount, order_variety, limit_price,
                        order_tag, status, realized_pnl, timestamp, trigger_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    o.get("id"),
                    user_id,
                    o.get("symbol"),
                    o.get("name") or o.get("symbol"),
                    o.get("asset_type") or "STOCK",
                    o.get("order_type"),
                    o.get("product_type") or "DELIVERY",
                    float(o.get("quantity") or 0.0),
                    float(o.get("price") or 0.0),
                    float(o.get("total_amount") or 0.0),
                    o.get("order_variety") or "MARKET",
                    float(o.get("limit_price") or 0.0),
                    o.get("order_tag") or "NORMAL",
                    o.get("status") or "EXECUTED",
                    float(o.get("realized_pnl") or 0.0),
                    o.get("timestamp"),
                    float(o.get("trigger_price") or 0.0)
                ))
            return res
    except Exception as sync_e:
        print(f"[Supabase Orders Sync Warning] {sync_e}")
    return None

def sync_holdings_from_supabase_into_cursor(cursor, user_id: str):
    if not is_supabase_enabled() or not user_id or user_id in ["guest", "default"]:
        return None
    try:
        res = supabase_api("GET", "holdings", params={"user_id": f"eq.{user_id}", "quantity": "gt.0", "select": "symbol,name,asset_type,quantity,avg_price,updated_at"})
        if res is not None and isinstance(res, list):
            cursor.execute("SELECT symbol, name, asset_type, quantity, avg_price, updated_at FROM holdings WHERE user_id = ? AND quantity > 0", (user_id,))
            local_rows = cursor.fetchall()
            local_map = {(r["symbol"] or "").upper(): dict(r) for r in local_rows}

            sb_symbols = set()

            for h in res:
                h_sym = (h.get("symbol") or "").strip()
                variants = get_symbol_variants(h_sym)
                upper_variants = [v.upper() for v in variants]
                h_qty = float(h.get("quantity", 0))

                if h_qty <= 0.0001:
                    for v in upper_variants:
                        cursor.execute("DELETE FROM holdings WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                        cursor.execute("""
                            INSERT OR REPLACE INTO holding_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v))
                    for v in variants:
                        filters = {"user_id": f"eq.{user_id}", "symbol": f"eq.{v}"}
                        supabase_api("DELETE", "holdings", params=filters)
                    continue

                # A positive cloud row can still be stale. A full local sale writes a
                # tombstone; if that sale happened after the cloud row was updated,
                # the local ledger wins and the row is reconciled to zero. Previously
                # the tombstone was simply dropped and the sold holding was restored,
                # handing the user inventory they no longer owned.
                tombstone_at = None
                for v in upper_variants:
                    cursor.execute(
                        "SELECT deleted_at FROM holding_tombstones WHERE user_id = ? AND UPPER(symbol) = ?",
                        (user_id, v))
                    t_row = cursor.fetchone()
                    if t_row and t_row["deleted_at"]:
                        tombstone_at = t_row["deleted_at"]
                        break

                if tombstone_at is not None:
                    sold_dt = _parse_order_dt(tombstone_at)
                    remote_dt = _parse_order_dt(h.get("updated_at"))
                    if sold_dt and (remote_dt is None or sold_dt >= remote_dt):
                        for v in upper_variants:
                            cursor.execute("DELETE FROM holdings WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                        supabase_api("PATCH", "holdings", payload={
                            "quantity": 0,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }, params={"user_id": f"eq.{user_id}", "symbol": f"eq.{h_sym}"})
                        continue

                # Genuine acquisition (cloud row is newer): clear the stale tombstone
                for v in upper_variants:
                    sb_symbols.add(v)
                    cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                    cursor.execute("DELETE FROM holdings WHERE user_id = ? AND UPPER(symbol) = ? AND symbol != ?", (user_id, v, h_sym))

                cursor.execute("""
                    INSERT OR REPLACE INTO holdings (user_id, symbol, name, asset_type, quantity, avg_price, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    h["symbol"], 
                    h.get("name", h["symbol"]), 
                    h.get("asset_type", "STOCK"), 
                    h_qty, 
                    float(h["avg_price"]), 
                    h.get("updated_at")
                ))

            # Remove any local holdings that no longer exist in Supabase (sold or closed)
            for l_sym, l_data in local_map.items():
                matching_vars = [v.upper() for v in get_symbol_variants(l_sym)]
                if not any(v in sb_symbols for v in matching_vars):
                    for v in matching_vars:
                        cursor.execute("DELETE FROM holdings WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                        cursor.execute("""
                            INSERT OR REPLACE INTO holding_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v))
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
                p_sym = (p.get("symbol") or "").strip()
                variants = get_symbol_variants(p_sym)
                upper_variants = [v.upper() for v in variants]
                p_qty = float(p.get("quantity", 0))

                if p_qty <= 0.0001:
                    for v in upper_variants:
                        cursor.execute("DELETE FROM positions WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                        cursor.execute("""
                            INSERT OR REPLACE INTO position_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v))
                    for v in variants:
                        filters = {"user_id": f"eq.{user_id}", "symbol": f"eq.{v}"}
                        supabase_api("DELETE", "positions", params=filters)
                    continue

                # Same stale-cloud-row guard as holdings: a square-off that happened
                # after the cloud row was written must not be undone by the sync.
                tombstone_at = None
                for v in upper_variants:
                    cursor.execute(
                        "SELECT deleted_at FROM position_tombstones WHERE user_id = ? AND UPPER(symbol) = ?",
                        (user_id, v))
                    t_row = cursor.fetchone()
                    if t_row and t_row["deleted_at"]:
                        tombstone_at = t_row["deleted_at"]
                        break

                if tombstone_at is not None:
                    closed_dt = _parse_order_dt(tombstone_at)
                    remote_dt = _parse_order_dt(p.get("updated_at"))
                    if closed_dt and (remote_dt is None or closed_dt >= remote_dt):
                        for v in upper_variants:
                            cursor.execute("DELETE FROM positions WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                        supabase_api("PATCH", "positions", payload={
                            "quantity": 0,
                            "margin_used": 0,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }, params={"user_id": f"eq.{user_id}", "symbol": f"eq.{p_sym}"})
                        continue

                # Genuine re-entry (cloud row is newer): clear the stale tombstone
                for v in upper_variants:
                    sb_symbols.add(v)
                    cursor.execute("DELETE FROM position_tombstones WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                    cursor.execute("DELETE FROM positions WHERE user_id = ? AND UPPER(symbol) = ? AND symbol != ?", (user_id, v, p_sym))

                cursor.execute("""
                    INSERT OR REPLACE INTO positions (user_id, symbol, name, asset_type, quantity, avg_price, margin_used, product_type, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    p["symbol"], 
                    p.get("name", p["symbol"]), 
                    p.get("asset_type", "STOCK"), 
                    p_qty, 
                    float(p["avg_price"]), 
                    float(p.get("margin_used", 0.0)), 
                    p.get("product_type", "INTRADAY"), 
                    p.get("updated_at")
                ))

            # Remove any local positions that no longer exist in Supabase (squared off or closed)
            for l_sym, l_data in local_map.items():
                matching_vars = [v.upper() for v in get_symbol_variants(l_sym)]
                if not any(v in sb_symbols for v in matching_vars):
                    for v in matching_vars:
                        cursor.execute("DELETE FROM positions WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v))
                        cursor.execute("""
                            INSERT OR REPLACE INTO position_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v))
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
            sync_orders_from_supabase_into_cursor(cursor, user_id)
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
        FROM holdings WHERE user_id = ? AND quantity > 0.0001
    """, (user_id,))
    rows = cursor.fetchall()

    valid_rows = []
    for r in rows:
        sym = (r["symbol"] or "").upper()
        # Clean any stale tombstones for owned symbols
        for v in get_symbol_variants(sym):
            cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v.upper()))
        valid_rows.append(dict(r))

    conn.commit()
    conn.close()
    return valid_rows

def get_positions(user_id: str = "default") -> List[Dict[str, Any]]:
    # 1. Try Supabase merge first
    if is_supabase_enabled() and user_id and user_id != "guest" and should_sync_remote("positions", user_id):
        try:
            drain_sync_outbox(user_id)
            conn = get_connection()
            cursor = conn.cursor()
            sync_orders_from_supabase_into_cursor(cursor, user_id)
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
        FROM positions WHERE user_id = ? AND quantity > 0.0001
    """, (user_id,))
    rows = cursor.fetchall()

    valid_rows = []
    for r in rows:
        sym = (r["symbol"] or "").upper()
        # Clean any stale tombstones for owned symbols
        for v in get_symbol_variants(sym):
            cursor.execute("DELETE FROM position_tombstones WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v.upper()))
        valid_rows.append(dict(r))

    conn.commit()
    conn.close()
    return valid_rows

def calculate_trade_charges(order_type: str, product_type: str, asset_type: str = "STOCK", amount: float = 0.0) -> Dict[str, float]:
    """
    Calculate authentic Indian stock broker charges (Groww / CDSL / SEBI fee schedule).
    For Equity Delivery Sell:
      - Brokerage: ₹20 or 0.05% of turnover (whichever is lower)
      - DP Charges: Flat ₹13.50 (CDSL) + 18% GST (₹15.93 total)
      - STT: 0.1% of turnover
      - Exchange Txn Fee: 0.00297% (NSE)
      - SEBI Turnover Fee: 0.0001% (₹10/crore)
      - Stamp Duty: ₹0 on Sell (0.015% on Buy only)
      - GST: 18% on (Brokerage + Exchange Txn + SEBI + DP Charges)
    For Equity Intraday Sell:
      - Brokerage: ₹20 or 0.05% (whichever is lower)
      - DP Charges: ₹0 (not debited from demat)
      - STT: 0.025% on Sell side
      - Exchange Txn Fee: 0.00297%
      - SEBI Turnover Fee: 0.0001%
      - Stamp Duty: ₹0 on Sell
      - GST: 18% on (Brokerage + Exchange Txn + SEBI)
    """
    amount = float(amount or 0.0)
    if amount <= 0:
        return {
            "brokerage": 0.0, "dp_charges": 0.0, "stt": 0.0,
            "exchange": 0.0, "sebi": 0.0, "stamp": 0.0,
            "gst": 0.0, "total": 0.0
        }

    is_sell = order_type.upper() == "SELL"
    is_intra = product_type.upper() == "INTRADAY"
    is_mf = asset_type.upper() == "MUTUAL_FUND"

    if is_mf:
        # Direct Mutual Funds have zero brokerage, zero STT, zero DP charges on redemption
        return {
            "brokerage": 0.0, "dp_charges": 0.0, "stt": 0.0,
            "exchange": 0.0, "sebi": 0.0, "stamp": 0.0,
            "gst": 0.0, "total": 0.0
        }

    # Groww brokerage: min(₹20, 0.05% of order value)
    brokerage = round(min(20.0, amount * 0.0005), 2)

    # DP Charges: CDSL ₹13.50 flat per delivery sell (charged by depository)
    dp_charges = 13.50 if (is_sell and not is_intra) else 0.0

    # STT: Delivery sell = 0.1%, Intraday sell = 0.025%, Buy = 0.1% for Delivery, 0 for Intraday
    if is_sell:
        stt = round(amount * 0.00025, 2) if is_intra else round(amount * 0.001, 2)
    else:
        stt = 0.0 if is_intra else round(amount * 0.001, 2)

    # Exchange transaction fee: NSE 0.00297%
    exchange = round(amount * 0.0000297, 2)

    # SEBI turnover charge: ₹10 / crore (0.0001%)
    sebi = round((amount / 10000000.0) * 10.0, 2)

    # Stamp duty: only on BUY in India
    if is_sell:
        stamp = 0.0
    else:
        stamp = round(amount * (0.00003 if is_intra else 0.00015), 2)

    # GST: 18% on (Brokerage + Exchange + SEBI + DP charges)
    gst = round((brokerage + exchange + sebi + dp_charges) * 0.18, 2)

    total = round(brokerage + dp_charges + stt + exchange + sebi + stamp + gst, 2)

    return {
        "brokerage": brokerage,
        "dp_charges": dp_charges,
        "stt": stt,
        "exchange": exchange,
        "sebi": sebi,
        "stamp": stamp,
        "gst": gst,
        "total": total
    }

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

    # A LIMIT order is pending only when it is NOT immediately marketable:
    #   BUY  limit below market  -> wait for price to fall to the limit
    #   SELL limit above market  -> wait for price to rise to the limit
    # A marketable LIMIT order (BUY limit >= market / SELL limit <= market) must
    # fill at the better market price, not at the (worse) limit price.
    is_pending_limit = False
    if order_variety == "LIMIT" and limit_price and float(limit_price) > 0:
        if order_type == "BUY" and float(limit_price) < price:
            is_pending_limit = True
        elif order_type == "SELL" and float(limit_price) > price:
            is_pending_limit = True

    # Stop-Loss orders whose trigger cannot fire yet are held as TRIGGER_PENDING.
    is_pending_sl = False
    if order_variety in ("STOP_LOSS", "SL") and trigger_price and float(trigger_price) > 0:
        if order_type == "SELL" and price > float(trigger_price):
            is_pending_sl = True
        elif order_type == "BUY" and price < float(trigger_price):
            is_pending_sl = True

    # Fill price for an immediately executing order is the live market price.
    # Pending orders use their limit/trigger reference for margin blocking.
    if is_pending_limit:
        effective_price = float(limit_price)
    elif is_pending_sl and order_type == "BUY":
        # A buy-stop can only trigger at/above its trigger price, so its worst
        # case cost (and margin) must be evaluated at the trigger price.
        effective_price = float(trigger_price)
    else:
        effective_price = price
    total_amount = round(quantity * effective_price, 2)

    # Margin requirements: 20% for regular Intraday stocks (5x leverage), 100% for Delivery CNC & Options
    if product_type == "INTRADAY" and asset_type != "OPTION":
        required_margin = round(total_amount * 0.20, 2)
    else:
        required_margin = total_amount

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Sync user balance from Supabase if enabled to ensure fresh, authoritative state
        if is_supabase_enabled() and user_id and user_id != "guest":
            sync_user_from_supabase_into_cursor(cursor, user_id)

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
            if is_supabase_enabled() and user_id != "guest":
                try:
                    supabase_api("POST", "users?on_conflict=id", payload={
                        "id": user_id, "name": "Default Trader" if user_id == "default" else "Trader",
                        "email": "trader@stoxify.com", "phone": "9876543210", "pan": "ABCDE1234F",
                        "bank_name": "HDFC Bank", "bank_account": "50100234567890", "pin": "",
                        "balance": 1000000.0, "total_deposited": 1000000.0, "avatar_color": "#0EA5E9"
                    })
                except Exception:
                    pass
        balance = acc_row["balance"] if acc_row else 1000000.0

        sym_variants = get_symbol_variants(symbol)
        sym_clause = " OR ".join(["UPPER(symbol) = ?"] * len(sym_variants))
        sym_params = [v.upper() for v in sym_variants]

        if is_pending_limit:
            new_balance = balance
            blocked_amount = 0.0
            if order_type == "BUY":
                # A resting BUY has to reserve the margin AND the charges that will
                # be payable when it fills, otherwise the fill itself can fail.
                pending_charges = calculate_trade_charges("BUY", product_type, asset_type, total_amount)
                blocked_amount = round(required_margin + pending_charges["total"], 2)
                if balance < blocked_amount:
                    conn.close()
                    return {"success": False, "error": f"Insufficient margin for Limit BUY. Required: ₹{blocked_amount:,.2f}, Available: ₹{balance:,.2f}"}
                new_balance = round(balance - blocked_amount, 2)
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
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, trigger_price, order_tag, status, realized_pnl, blocked_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 0.0, ?)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price, trigger_price or 0.0, order_tag, blocked_amount))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            if is_supabase_enabled() and user_id != "guest" and order_type == "BUY":
                try:
                    supabase_api("PATCH", f"users?id=eq.{user_id}", payload={"balance": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()})
                except Exception as sb_e:
                    print(f"[Supabase Limit Margin Sync Warning] {sb_e}")

            return {
                "success": True, 
                "order_id": order_id, 
                "status": "OPEN", 
                "balance": new_balance,
                "new_balance": new_balance,
                "message": f"Limit {order_type} order placed for {quantity} {symbol} at ₹{effective_price:,.2f} (Status: Open)"
            }

        # Stop-Loss Orders (SL-Limit) handling
        if is_pending_sl:
            new_balance = balance
            blocked_amount = 0.0
            if order_type == "BUY":
                pending_charges = calculate_trade_charges("BUY", product_type, asset_type, total_amount)
                blocked_amount = round(required_margin + pending_charges["total"], 2)
                if balance < blocked_amount:
                    conn.close()
                    return {"success": False, "error": f"Insufficient margin for Stop-Loss BUY. Required: ₹{blocked_amount:,.2f}, Available: ₹{balance:,.2f}"}
                new_balance = round(balance - blocked_amount, 2)
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
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, trigger_price, order_tag, status, realized_pnl, blocked_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TRIGGER_PENDING', 0.0, ?)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or effective_price, trigger_price, order_tag, blocked_amount))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            if is_supabase_enabled() and user_id != "guest" and order_type == "BUY":
                try:
                    supabase_api("PATCH", f"users?id=eq.{user_id}", payload={"balance": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()})
                except Exception as sb_e:
                    print(f"[Supabase SL Margin Sync Warning] {sb_e}")

            return {
                "success": True, 
                "order_id": order_id, 
                "status": "TRIGGER_PENDING", 
                "balance": new_balance,
                "new_balance": new_balance,
                "message": f"Stop-Loss {order_type} placed for {quantity} {symbol}. Trigger Price: ₹{trigger_price:,.2f} (Status: Trigger Pending)"
            }

        # Immediate Execution
        if order_type == "BUY":
            # Statutory charges settle on the trade date: brokerage, STT, stamp
            # duty, exchange/SEBI fees and GST leave the wallet together with the
            # margin. They used to be written onto the contract note but never
            # debited, so every BUY overstated the account's cash.
            charges = calculate_trade_charges("BUY", product_type, asset_type, total_amount)
            required_cash = round(required_margin + charges["total"], 2)
            if balance < required_cash:
                conn.close()
                return {"success": False, "error": f"Insufficient margin. Required: ₹{required_cash:,.2f} (margin ₹{required_margin:,.2f} + charges ₹{charges['total']:,.2f}; 5x leverage applied if Intraday), Available: ₹{balance:,.2f}"}

            new_balance = round(balance - required_cash, 2)
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
                cursor.execute(f"DELETE FROM position_tombstones WHERE user_id = ? AND ({sym_clause})", [user_id] + sym_params)
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
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, charges, net_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status, charges["total"], total_amount))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Sync to Supabase synchronously so cloud state is consistent and immune to serverless freezing
            if is_supabase_enabled() and user_id != "guest":
                def _sync_buy():
                    try:
                        supabase_api("PATCH", f"users?id=eq.{user_id}", payload={"balance": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()})
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
                    finally:
                        _REMOTE_SYNC_LAST_AT.pop(f"holdings:{user_id}", None)
                        _REMOTE_SYNC_LAST_AT.pop(f"positions:{user_id}", None)
                        _REMOTE_SYNC_LAST_AT.pop(f"orders:{user_id}", None)

                _sync_buy()

            _REMOTE_SYNC_LAST_AT.pop(f"holdings:{user_id}", None)
            _REMOTE_SYNC_LAST_AT.pop(f"positions:{user_id}", None)
            _REMOTE_SYNC_LAST_AT.pop(f"orders:{user_id}", None)
            tag_msg = " as After-Market Order (AMO)" if order_tag == "AMO" else ""
            return {
                "success": True, 
                "order_id": order_id, 
                "status": order_status, 
                "balance": new_balance,
                "new_balance": new_balance,
                "charges": charges,
                "net_amount": total_amount,
                "message": f"Successfully purchased {quantity} {symbol} at ₹{effective_price:,.2f}{tag_msg}"
            }

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

                charges = calculate_trade_charges("SELL", "INTRADAY", asset_type, round(effective_price * quantity, 2))
                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                margin_released = round((quantity / curr_qty) * curr_margin, 2)
                net_proceeds = round(margin_released + realized_pnl - charges["total"], 2)
                new_balance = round(balance + net_proceeds, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                rem_qty = round(curr_qty - quantity, 4)
                intra_variants = get_symbol_variants(matched_symbol)
                if rem_qty <= 0.0001:
                    for v in intra_variants:
                        cursor.execute("DELETE FROM positions WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v.upper()))
                        cursor.execute("""
                            INSERT OR REPLACE INTO position_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v.upper()))
                        cursor.execute("""
                            INSERT OR REPLACE INTO position_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v))
                        enqueue_sync_operation(cursor, user_id, "DELETE", "positions", filters={"user_id": f"eq.{user_id}", "symbol": f"eq.{v}"})
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
                charges = calculate_trade_charges("SELL", "DELIVERY", asset_type, total_amount)
                realized_pnl = round((effective_price - avg_price) * quantity, 2)
                net_proceeds = max(0.0, round(total_amount - charges["total"], 2))
                new_balance = round(balance + net_proceeds, 2)
                cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, user_id))
                if user_id == "default":
                    cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_balance,))

                rem_qty = round(curr_qty - quantity, 4)
                deliv_variants = get_symbol_variants(matched_symbol)
                if rem_qty <= 0.0001:
                    for v in deliv_variants:
                        cursor.execute("DELETE FROM holdings WHERE user_id = ? AND UPPER(symbol) = ?", (user_id, v.upper()))
                        cursor.execute("""
                            INSERT OR REPLACE INTO holding_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v.upper()))
                        cursor.execute("""
                            INSERT OR REPLACE INTO holding_tombstones (user_id, symbol, deleted_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, v))
                        close_filters = {
                            "user_id": f"eq.{user_id}",
                            "symbol": f"eq.{v}"
                        }
                        enqueue_sync_operation(cursor, user_id, "PATCH", "holdings", filters=close_filters, payload={"quantity": 0, "updated_at": datetime.now(timezone.utc).isoformat()})
                        enqueue_sync_operation(cursor, user_id, "DELETE", "holdings", filters=close_filters)
                else:
                    cursor.execute("UPDATE holdings SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND UPPER(symbol) = ?", (rem_qty, user_id, matched_symbol.upper()))

            product_type = actual_product
            order_status = "EXECUTED (AMO)" if order_tag == "AMO" else "EXECUTED"
            cursor.execute("""
                INSERT INTO orders (user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, charges, net_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, symbol, name, asset_type, order_type, product_type, quantity, effective_price, total_amount, order_variety, limit_price or 0.0, order_tag, order_status, realized_pnl, charges["total"], net_proceeds))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Sync to Supabase synchronously so cloud state is consistent and immune to serverless freezing
            if is_supabase_enabled() and user_id != "guest":
                def _sync_sell():
                    try:
                        supabase_api("PATCH", f"users?id=eq.{user_id}", payload={"balance": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()})
                        if product_type == "INTRADAY":
                            if rem_qty <= 0.0001:
                                for v in intra_variants:
                                    filters = {"user_id": f"eq.{user_id}", "symbol": f"eq.{v}"}
                                    supabase_api("PATCH", "positions", payload={"quantity": 0, "margin_used": 0, "updated_at": datetime.now(timezone.utc).isoformat()}, params=filters)
                                    supabase_api("DELETE", "positions", params=filters)
                                    supabase_api("DELETE", "positions", params={"user_id": f"eq.{user_id}", "symbol": f"ilike.{v}"})
                            else:
                                supabase_api("POST", "positions?on_conflict=user_id,symbol", payload={
                                    "user_id": user_id, "symbol": matched_symbol, "name": name, "asset_type": asset_type,
                                    "quantity": rem_qty, "avg_price": avg_price, "margin_used": new_margin, "product_type": "INTRADAY"
                                })
                        else:
                            if rem_qty <= 0.0001:
                                for v in deliv_variants:
                                    close_filters = {
                                        "user_id": f"eq.{user_id}",
                                        "symbol": f"eq.{v}"
                                    }
                                    supabase_api("PATCH", "holdings", payload={"quantity": 0, "updated_at": datetime.now(timezone.utc).isoformat()}, params=close_filters)
                                    supabase_api("DELETE", "holdings", params=close_filters)
                                    supabase_api("DELETE", "holdings", params={"user_id": f"eq.{user_id}", "symbol": f"ilike.{v}"})
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
                    finally:
                        _REMOTE_SYNC_LAST_AT.pop(f"holdings:{user_id}", None)
                        _REMOTE_SYNC_LAST_AT.pop(f"positions:{user_id}", None)
                        _REMOTE_SYNC_LAST_AT.pop(f"orders:{user_id}", None)

                _sync_sell()

            _REMOTE_SYNC_LAST_AT.pop(f"holdings:{user_id}", None)
            _REMOTE_SYNC_LAST_AT.pop(f"positions:{user_id}", None)
            _REMOTE_SYNC_LAST_AT.pop(f"orders:{user_id}", None)
            tag_msg = " as After-Market Order (AMO)" if order_tag == "AMO" else ""
            return {
                "success": True, 
                "order_id": order_id, 
                "status": order_status, 
                "realized_pnl": realized_pnl,
                "gross_amount": total_amount,
                "charges": charges,
                "net_amount": net_proceeds,
                "balance": new_balance,
                "new_balance": new_balance,
                "message": f"Successfully sold {quantity} {symbol} at ₹{effective_price:,.2f} (Net: ₹{net_proceeds:,.2f}){tag_msg}"
            }

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
            SELECT id, user_id, symbol, order_type, total_amount, blocked_amount, status
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
            # Refund exactly what was withheld. `blocked_amount` is the margin plus
            # the buy-leg charges reserved when the order was accepted;
            # `total_amount` is the order value and is only a fallback for rows
            # written before that column existed.
            refund = float(order["blocked_amount"] or 0.0)
            if refund <= 0:
                refund = float(order["total_amount"] or 0.0)
            new_bal = round(curr_bal + refund, 2)
            cursor.execute("UPDATE users SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_bal, o_user))
            if o_user == "default":
                cursor.execute("UPDATE account SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (new_bal,))
            if is_supabase_enabled() and o_user != "guest":
                try:
                    supabase_api("PATCH", f"users?id=eq.{o_user}", payload={"balance": new_bal, "updated_at": datetime.now(timezone.utc).isoformat()})
                except Exception as sb_e:
                    print(f"[Supabase Cancel Margin Sync Warning] {sb_e}")

        cursor.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = ?", (order_id,))
        if is_supabase_enabled() and o_user != "guest":
            try:
                supabase_api("PATCH", "orders", params={"id": f"eq.{order_id}"}, payload={"status": "CANCELLED"})
            except Exception:
                pass
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Order #{order_id} for {order['symbol']} cancelled successfully"}

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}

def get_pending_order_symbols(user_id: str) -> List[str]:
    """Distinct symbols of resting orders, read straight from the local ledger.

    Used by the matching loop so it does not have to pull full order lists (which
    would hit the cloud) just to learn which symbols need a price check.
    """
    if not user_id:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT symbol FROM orders
        WHERE user_id = ? AND status IN ('OPEN', 'TRIGGER_PENDING')
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r["symbol"] for r in rows if r["symbol"]]


def check_open_limit_orders(symbol: str, current_price: float, user_id: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    # Match on symbol variants: callers may pass 'RELIANCE' while the stored row
    # says 'RELIANCE.NS', and an exact comparison silently matched nothing.
    variants = [v.upper() for v in get_symbol_variants(symbol)]
    clause = " OR ".join(["UPPER(symbol) = ?"] * len(variants))
    if user_id:
        cursor.execute(f"""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, trigger_price, total_amount, status 
            FROM orders WHERE status IN ('OPEN', 'TRIGGER_PENDING') AND ({clause}) AND user_id = ?
        """, variants + [user_id])
    else:
        cursor.execute(f"""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, limit_price, trigger_price, total_amount, status 
            FROM orders WHERE status IN ('OPEN', 'TRIGGER_PENDING') AND ({clause})
        """, variants)
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

    check_gtt_orders(symbol, current_price, user_id)

def check_gtt_orders(symbol: str, current_price: float, user_id: Optional[str] = None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        variants = [v.upper() for v in get_symbol_variants(symbol)]
        clause = " OR ".join(["UPPER(symbol) = ?"] * len(variants))
        if user_id:
            cursor.execute(f"""
                SELECT id, user_id, symbol, name, product_type, action, quantity, trigger_price, target_price, stop_loss_price, status
                FROM gtt_orders WHERE status = 'ACTIVE' AND ({clause}) AND user_id = ?
            """, variants + [user_id])
        else:
            cursor.execute(f"""
                SELECT id, user_id, symbol, name, product_type, action, quantity, trigger_price, target_price, stop_loss_price, status
                FROM gtt_orders WHERE status = 'ACTIVE' AND ({clause})
            """, variants)
        active_gtts = [dict(r) for r in cursor.fetchall()]
        conn.close()

        for g in active_gtts:
            act = (g.get("action") or "BUY").upper()
            trig = float(g.get("trigger_price") or 0.0)
            hit = (current_price >= trig) if act == "BUY" else (current_price <= trig)
            if hit and trig > 0:
                conn_claim = get_connection()
                cur_claim = conn_claim.cursor()
                cur_claim.execute("UPDATE gtt_orders SET status = 'TRIGGERED' WHERE id = ? AND status = 'ACTIVE'", (g["id"],))
                claimed = cur_claim.rowcount == 1
                conn_claim.commit()
                conn_claim.close()

                if claimed:
                    execute_trade(
                        symbol=g["symbol"],
                        name=g.get("name") or g["symbol"],
                        asset_type="STOCK",
                        order_type=act,
                        product_type=g.get("product_type") or "DELIVERY",
                        quantity=float(g["quantity"]),
                        price=current_price,
                        order_variety="GTT",
                        user_id=g["user_id"]
                    )
    except Exception:
        pass

def get_orders(limit: int = 100, status_filter: Optional[str] = None, user_id: str = "default") -> List[Dict[str, Any]]:
    # 1. Try Supabase first
    if is_supabase_enabled() and user_id and user_id != "guest":
        params = {"user_id": f"eq.{user_id}", "order": "id.desc", "limit": str(limit)}
        if status_filter:
            if status_filter.upper() == "EXECUTED":
                # Executed rows may carry an "(AMO)" suffix; treat them as executed.
                params["status"] = "like.EXECUTED%"
            else:
                params["status"] = f"eq.{status_filter}"
        res = supabase_api("GET", "orders", params=params)
        if res is not None and isinstance(res, list) and len(res) > 0:
            return res

    # 2. SQLite fallback
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter:
        if status_filter.upper() == "EXECUTED":
            cursor.execute("""
                SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, charges, net_amount, blocked_amount, timestamp
                FROM orders WHERE user_id = ? AND status LIKE 'EXECUTED%' ORDER BY id DESC LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, charges, net_amount, blocked_amount, timestamp
                FROM orders WHERE user_id = ? AND status = ? ORDER BY id DESC LIMIT ?
            """, (user_id, status_filter, limit))
    else:
        cursor.execute("""
            SELECT id, user_id, symbol, name, asset_type, order_type, product_type, quantity, price, total_amount, order_variety, limit_price, order_tag, status, realized_pnl, charges, net_amount, blocked_amount, timestamp
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
            "updated_at": datetime.now(timezone.utc).isoformat()
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
    cursor.execute("DELETE FROM position_tombstones WHERE user_id = ?", (user_id,))
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
            "updated_at": datetime.now(timezone.utc).isoformat()
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
    
    # Clear active holdings and positions when restoring balance to prevent balance duplication arbitrage
    cursor.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM position_tombstones WHERE user_id = ?", (user_id,))
    # Resting orders have already had their margin released by the balance reset
    # above. Leaving them OPEN let a later cancel refund the same margin a second
    # time, so "Restore full balance" followed by "cancel order" minted cash.
    # Retire them rather than deleting the rows so history stays auditable.
    cursor.execute("""
        UPDATE orders SET status = 'CANCELLED'
        WHERE user_id = ? AND status IN ('OPEN', 'TRIGGER_PENDING', 'CANCELLING')
    """, (user_id,))
    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id and user_id != "guest":
        try:
            supabase_api("PATCH", "orders", payload={"status": "CANCELLED"}, params={
                "user_id": f"eq.{user_id}",
                "status": "in.(OPEN,TRIGGER_PENDING,CANCELLING)"
            })
            supabase_api("PATCH", f"users?id=eq.{user_id}", payload={
                "balance": target_balance,
                "total_deposited": target_balance,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            supabase_api("DELETE", "holdings", params={"user_id": f"eq.{user_id}"})
            supabase_api("DELETE", "positions", params={"user_id": f"eq.{user_id}"})
        except Exception:
            pass
    _REMOTE_SYNC_LAST_AT.pop(f"holdings:{user_id}", None)
    _REMOTE_SYNC_LAST_AT.pop(f"positions:{user_id}", None)
    return target_balance

def delete_user(user_id: str) -> bool:
    if not user_id or user_id == "guest":
        return False

    # Resolve the account (and its Supabase auth id) BEFORE the local row is
    # removed. get_user() re-hydrates a missing local row from Supabase, so
    # looking the account up after the delete resurrected the very row we had
    # just deleted and the account reappeared on the next read.
    u_row = get_user(user_id) if is_supabase_enabled() else None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM position_tombstones WHERE user_id = ?", (user_id,))
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
        cursor.execute("DELETE FROM position_tombstones")
        cursor.execute("DELETE FROM sync_outbox")
        cursor.execute("DELETE FROM positions")
        cursor.execute("DELETE FROM orders")
        cursor.execute("UPDATE account SET balance = 1000000.0, total_deposited = 1000000.0 WHERE id = 1")
    conn.commit()
    conn.close()

    if is_supabase_enabled() and user_id != "default":
        try:
            auth_id = (u_row.get("auth_id") if u_row else None)
            admin_headers = {
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            if auth_id:
                try:
                    admin_del_url = f"{SUPABASE_URL}/auth/v1/admin/users/{auth_id}"
                    del_req = urllib.request.Request(admin_del_url, headers=admin_headers, method="DELETE")
                    with urllib.request.urlopen(del_req, timeout=5):
                        print(f"[Supabase Auth Admin] Removed auth user {auth_id} from Supabase Authentication -> Users")
                except Exception as e:
                    print(f"[Supabase Auth Delete Note]: {e}")
            elif u_row and u_row.get("email"):
                try:
                    search_email = u_row["email"].strip().lower()
                    admin_users_url = f"{SUPABASE_URL}/auth/v1/admin/users"
                    list_req = urllib.request.Request(admin_users_url, headers=admin_headers)
                    with urllib.request.urlopen(list_req, timeout=5) as list_resp:
                        u_list = json.loads(list_resp.read().decode("utf-8")).get("users", [])
                        for au in u_list:
                            if au.get("email", "").lower() == search_email:
                                target_aid = au["id"]
                                del_req = urllib.request.Request(f"{admin_users_url}/{target_aid}", headers=admin_headers, method="DELETE")
                                with urllib.request.urlopen(del_req, timeout=5):
                                    print(f"[Supabase Auth Admin] Found and removed auth user {target_aid} ({search_email})")
                                break
                except Exception as e:
                    print(f"[Supabase Auth Delete Note]: {e}")

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
    cursor.execute("UPDATE gtt_orders SET status = 'CANCELLED' WHERE id = ? AND user_id = ? AND status = 'ACTIVE'", (gtt_id, user_id))
    cancelled = cursor.rowcount
    conn.commit()
    conn.close()
    if not cancelled:
        # Without a rowcount check this reported success for ids that do not
        # exist or were already cancelled.
        return {"success": False, "error": f"Active GTT order #{gtt_id} not found"}
    return {"success": True, "message": f"GTT Order #{gtt_id} cancelled"}

# --- SIP (Systematic Investment Plans) ---
def create_sip(user_id: str, fund_id: str, fund_name: str, monthly_amount: float, sip_day: int = 5) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    # A SIP day of 29/30/31 does not exist in every month and datetime() raises
    # ValueError for those, which surfaced as an HTTP 500 instead of a schedule.
    # Roll to the next month and clamp to that month's last valid day.
    day = max(1, min(int(sip_day or 5), 31))
    year, month = now.year, now.month
    if now.day >= day:
        month += 1
        if month > 12:
            month, year = 1, year + 1
    last_day_of_month = calendar.monthrange(year, month)[1]
    next_dt = datetime(year, month, min(day, last_day_of_month))
    next_date_str = next_dt.strftime("%d %b %Y")

    cursor.execute("""
        INSERT INTO sips (user_id, fund_id, fund_name, monthly_amount, sip_day, status, next_installment_date)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (user_id, fund_id, fund_name, monthly_amount, day, next_date_str))
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
    cursor.execute("UPDATE sips SET status = 'CANCELLED' WHERE id = ? AND user_id = ? AND status = 'ACTIVE'", (sip_id, user_id))
    cancelled = cursor.rowcount
    conn.commit()
    conn.close()
    if not cancelled:
        return {"success": False, "error": f"Active SIP #{sip_id} not found"}
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
def _parse_order_dt(value) -> Optional[datetime]:
    """Parse both SQLite ('YYYY-MM-DD HH:MM:SS') and Supabase ISO-8601 stamps.

    Rows pulled from Supabase come back as '2026-01-01T10:00:00.123456+00:00'.
    Slicing the first 19 characters leaves the literal 'T' in place, so a
    strptime-only parser returned None for every cloud-synced order and the
    holding period silently collapsed to zero (everything became STCG).
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        pass
    try:
        return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def get_capital_gains_tax_report(user_id: str = "default") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    # Sells, oldest first, so lots can be FIFO-matched against earlier buys.
    cursor.execute("""
        SELECT id, symbol, name, product_type, quantity, price, realized_pnl, timestamp
        FROM orders WHERE user_id = ? AND order_type = 'SELL' AND status LIKE 'EXECUTED%'
        ORDER BY id ASC
    """, (user_id,))
    rows = cursor.fetchall()

    # Executed delivery buys per symbol (acquisition lots), oldest first.
    cursor.execute("""
        SELECT symbol, quantity, timestamp FROM orders
        WHERE user_id = ? AND product_type = 'DELIVERY' AND order_type = 'BUY' AND status LIKE 'EXECUTED%'
        ORDER BY id ASC
    """, (user_id,))
    buy_rows = cursor.fetchall()
    conn.close()

    from collections import deque
    buy_lots: Dict[str, deque] = {}
    for b in buy_rows:
        key = (b["symbol"] or "").upper()
        buy_lots.setdefault(key, deque()).append({
            "qty": float(b["quantity"] or 0.0),
            "ts": _parse_order_dt(b["timestamp"])
        })

    total_stcg_profit = 0.0
    total_stcg_loss = 0.0
    total_ltcg_profit = 0.0
    total_ltcg_loss = 0.0
    trades = []

    for r in rows:
        pnl = float(r["realized_pnl"] or 0.0)
        is_ltcg = False

        # Holding period is measured from when the shares were acquired (FIFO),
        # not from the sell date or from today.
        if r["product_type"] == "DELIVERY":
            sell_dt = _parse_order_dt(r["timestamp"])
            if sell_dt:
                qty_to_match = float(r["quantity"] or 0.0)
                lots = buy_lots.get((r["symbol"] or "").upper())
                acquisition_dt = None
                if lots:
                    while qty_to_match > 1e-6 and lots:
                        lot = lots[0]
                        take = min(lot["qty"], qty_to_match)
                        lot["qty"] -= take
                        qty_to_match -= take
                        acquisition_dt = lot["ts"] or acquisition_dt
                        if lot["qty"] <= 1e-6:
                            lots.popleft()
                if qty_to_match <= 1e-6 and acquisition_dt:
                    days_held = (sell_dt - acquisition_dt).days
                    is_ltcg = days_held >= 365

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

    # Keep the historical order of the response: newest sell first.
    trades.reverse()

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

