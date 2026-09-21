from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional, List
import time
import os
import json
import requests
import yfinance as yf

IST = timezone(timedelta(hours=5, minutes=30))

# Simulation flag to allow testing off-hours if the user wants
_SIMULATION_MODE = False

# In-memory caches
_HOLIDAY_CACHE: Dict[str, Any] = {}
_MARKET_ACTIVITY_CACHE: Dict[str, Any] = {}

# File cache path to ensure offline/network resiliency
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_FILE_PATH = os.path.join(DATA_DIR, "live_market_holidays.json")

def get_ist_now() -> datetime:
    return datetime.now(IST)

def set_simulation_mode(enabled: bool):
    global _SIMULATION_MODE
    _SIMULATION_MODE = bool(enabled)

def toggle_simulation(enabled: bool) -> Dict[str, Any]:
    set_simulation_mode(enabled)
    return get_market_status()

def is_simulation_mode() -> bool:
    return _SIMULATION_MODE

def fetch_live_market_holidays(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Fetches official live trading holidays from the web:
      1. Primary: National Stock Exchange of India (NSE) official holiday master API.
      2. Secondary: Upstox public market holidays API.
      3. Fallback: Local cached JSON file.
    Results are cached in memory for 12 hours.
    Returns:
      Dict mapping 'YYYY-MM-DD' to holiday details:
      {
        "2026-09-14": {
          "date": "2026-09-14",
          "name": "Ganesh Chaturthi",
          "weekday": "Monday",
          "source": "NSE Live Exchange Feed"
        }
      }
    """
    now = get_ist_now()
    now_ts = time.time()

    # 1. Return in-memory cache if valid
    cached = _HOLIDAY_CACHE.get("data")
    expires = _HOLIDAY_CACHE.get("expires", 0)
    if not force_refresh and cached and now_ts < expires:
        return cached

    holidays: Dict[str, Dict[str, Any]] = {}
    source_name = ""

    # 2. Try primary source: Official NSE India Holiday Master API
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com"
        }
        # Establish session cookies with NSE
        session.get("https://www.nseindia.com", headers=headers, timeout=4)
        resp = session.get("https://www.nseindia.com/api/holiday-master?type=trading", headers=headers, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            cm_list = data.get("CM", [])  # Capital Market (Equities) segment
            for item in cm_list:
                raw_date = item.get("tradingDate")
                desc = item.get("description", "").strip()
                weekday = item.get("weekDay", "").strip()
                if raw_date and desc:
                    try:
                        dt = datetime.strptime(raw_date.strip(), "%d-%b-%Y")
                        iso_date = dt.strftime("%Y-%m-%d")
                        holidays[iso_date] = {
                            "date": iso_date,
                            "trading_date": raw_date.strip(),
                            "name": desc,
                            "weekday": weekday,
                            "source": "NSE Live Exchange Feed"
                        }
                    except Exception:
                        pass
            if holidays:
                source_name = "NSE Live Exchange Feed"
    except Exception:
        pass

    # 3. Try secondary source: Upstox public market holidays API
    if not holidays:
        try:
            resp = requests.get("https://api.upstox.com/v2/market/holidays", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("data", []):
                    d = item.get("date")
                    desc = item.get("description", "").strip()
                    htype = item.get("holiday_type", "")
                    if d and desc and "TRADING_HOLIDAY" in htype:
                        try:
                            dt = datetime.strptime(d, "%Y-%m-%d")
                            holidays[d] = {
                                "date": d,
                                "trading_date": dt.strftime("%d-%b-%Y"),
                                "name": desc,
                                "weekday": dt.strftime("%A"),
                                "source": "Upstox Live API"
                            }
                        except Exception:
                            pass
                if holidays:
                    source_name = "Upstox Live API"
        except Exception:
            pass

    # 4. If web requests succeeded, persist to disk cache and update memory cache
    if holidays:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "updated_at": now.isoformat(),
                    "source": source_name,
                    "holidays": holidays
                }, f, indent=2)
        except Exception:
            pass

        _HOLIDAY_CACHE["data"] = holidays
        _HOLIDAY_CACHE["expires"] = now_ts + 43200  # 12 hours TTL
        _HOLIDAY_CACHE["source"] = source_name
        return holidays

    # 5. Network fallback: Read from disk cache if present
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                cached_file = json.load(f)
                loaded_holidays = cached_file.get("holidays", {})
                if loaded_holidays:
                    _HOLIDAY_CACHE["data"] = loaded_holidays
                    _HOLIDAY_CACHE["expires"] = now_ts + 3600  # 1 hour retry
                    _HOLIDAY_CACHE["source"] = cached_file.get("source", "Disk Cache")
                    return loaded_holidays
        except Exception:
            pass

    return {}

def check_live_market_activity_yahoo() -> Optional[bool]:
    """
    Checks Yahoo Finance live feed for the benchmark index ^NSEI (NIFTY 50).
    Returns:
      True  -> Market is actively trading today (live open and day_high exist).
      False -> Zero trades recorded today during normal hours (Exchange is closed / Holiday).
      None  -> Before 09:20 AM, after hours, or network check inconclusive.
    """
    now = get_ist_now()
    # Live ticker probe is only meaningful for the actual current day, not historical or mocked dates
    if now.date() != datetime.now(IST).date():
        return None

    today_str = now.strftime("%Y-%m-%d")
    total_minutes = now.hour * 60 + now.minute

    # Only evaluate once the regular session has had 5 minutes to generate ticks (after 09:20 AM IST)
    if total_minutes < 560 or total_minutes >= 930:
        return None

    # Check cache (5-minute TTL to keep status snappy and avoid network spam)
    cached = _MARKET_ACTIVITY_CACHE.get("activity")
    if cached and time.time() < cached.get("expires", 0) and cached.get("date") == today_str:
        return cached.get("is_active")

    try:
        ticker = yf.Ticker("^NSEI")
        fast = ticker.fast_info
        # When exchange is on holiday, Yahoo Finance provides no open or day_high for today
        if fast.open is None or fast.day_high is None:
            is_active = False
        else:
            is_active = True

        _MARKET_ACTIVITY_CACHE["activity"] = {
            "is_active": is_active,
            "date": today_str,
            "expires": time.time() + 300
        }
        return is_active
    except Exception:
        return None

def get_today_holiday() -> Dict[str, Any]:
    """
    Determines if today is a trading holiday using live web data.
    """
    now = get_ist_now()
    today_iso = now.strftime("%Y-%m-%d")
    holidays = fetch_live_market_holidays()

    if today_iso in holidays:
        holiday = holidays[today_iso]
        return {
            "is_holiday": True,
            "holiday_name": holiday.get("name", "Trading Holiday"),
            "date": today_iso,
            "weekday": holiday.get("weekday", now.strftime("%A")),
            "source": holiday.get("source", "Live Exchange Feed")
        }

    return {
        "is_holiday": False,
        "holiday_name": None,
        "date": today_iso,
        "weekday": now.strftime("%A"),
        "source": None
    }

def get_market_status(ignore_simulation: bool = False) -> Dict[str, Any]:
    """Current session state.

    `ignore_simulation=True` reports the *real* exchange session even when the
    simulation toggle is on. Order validation uses it so that intraday (MIS) is
    genuinely restricted outside 09:15-15:30 IST, while the simulation toggle
    stays useful for market-data browsing.
    """
    now = get_ist_now()
    weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
    current_time = now.time()

    time_str = now.strftime("%I:%M:%S %p IST")
    date_str = now.strftime("%d %b %Y")

    if _SIMULATION_MODE and not ignore_simulation:
        return {
            "is_open": True,
            "session": "REGULAR",
            "intraday_allowed": True,
            "status_text": "Live Market OPEN",
            "subtext": "Simulation Mode (24/7 Trading Active)",
            "badge_color": "green",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": None,
            "is_holiday": False,
            "simulation_mode": True
        }

    # 1. Check live holiday master from web
    holiday_info = get_today_holiday()
    if holiday_info.get("is_holiday"):
        holiday_name = holiday_info.get("holiday_name", "Trading Holiday")
        return {
            "is_open": False,
            "session": "HOLIDAY",
            "intraday_allowed": False,
            "status_text": f"Market CLOSED ({holiday_name})",
            "subtext": f"Trading Holiday: {holiday_name} • AMO Active",
            "badge_color": "gray",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": holiday_name,
            "is_holiday": True,
            "holiday_source": holiday_info.get("source"),
            "simulation_mode": False
        }

    # 2. Check for Weekend (Saturday / Sunday)
    if weekday >= 5:
        return {
            "is_open": False,
            "session": "WEEKEND",
            "intraday_allowed": False,
            "status_text": "Market CLOSED (Weekend)",
            "subtext": "Opens Monday at 09:15 AM IST • AMO Active",
            "badge_color": "gray",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": None,
            "is_holiday": False,
            "simulation_mode": False
        }

    # 3. Regular Weekday Trading Hours (Monday to Friday)
    h = current_time.hour
    m = current_time.minute
    total_minutes = h * 60 + m

    if 540 <= total_minutes < 555:
        return {
            "is_open": False,
            "session": "PRE_MARKET",
            "intraday_allowed": False,
            "status_text": "Pre-Market Session",
            "subtext": "Normal trading begins at 09:15 AM IST",
            "badge_color": "orange",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": None,
            "is_holiday": False,
            "simulation_mode": False
        }
    elif 555 <= total_minutes < 930:
        # Check Yahoo Finance live exchange activity
        is_live_trading = check_live_market_activity_yahoo()
        if is_live_trading is False:
            # During regular hours, but zero trades exist on Yahoo Finance -> Trading Holiday
            return {
                "is_open": False,
                "session": "HOLIDAY",
                "intraday_allowed": False,
                "status_text": "Market CLOSED (Trading Holiday)",
                "subtext": "Exchange is closed today (Verified via Yahoo Finance live feed) • AMO Active",
                "badge_color": "gray",
                "current_time_ist": time_str,
                "date_ist": date_str,
                "holiday_name": "Trading Holiday",
                "is_holiday": True,
                "verified_by_yahoo": True,
                "simulation_mode": False
            }

        intraday_allowed = total_minutes < 920
        sub = "Closes at 03:30 PM IST" if intraday_allowed else "Intraday cutoff reached (Auto square-off at 03:20 PM)"
        return {
            "is_open": True,
            "session": "REGULAR",
            "intraday_allowed": intraday_allowed,
            "status_text": "Live Market OPEN",
            "subtext": sub,
            "badge_color": "green",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": None,
            "is_holiday": False,
            "simulation_mode": False
        }
    elif 930 <= total_minutes < 940:
        return {
            "is_open": False,
            "session": "POST_MARKET",
            "intraday_allowed": False,
            "status_text": "Post-Market Session",
            "subtext": "Closing price discovery",
            "badge_color": "orange",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": None,
            "is_holiday": False,
            "simulation_mode": False
        }
    else:
        return {
            "is_open": False,
            "session": "AMO",
            "intraday_allowed": False,
            "status_text": "Market CLOSED (AMO Active)",
            "subtext": "Delivery orders accepted as After-Market Orders",
            "badge_color": "gray",
            "current_time_ist": time_str,
            "date_ist": date_str,
            "holiday_name": None,
            "is_holiday": False,
            "simulation_mode": False
        }

def validate_order_timing(product_type: str) -> Tuple[bool, str, str]:
    product = product_type.upper()
    # The real session, deliberately ignoring the simulation toggle: intraday
    # used to return success unconditionally, so MIS could be placed on a
    # Sunday while the README promised strict market-hours enforcement.
    status = get_market_status(ignore_simulation=True)

    if product == "INTRADAY":
        if not status["intraday_allowed"]:
            return (
                False,
                "INTRADAY",
                "Intraday (MIS) orders are accepted only between 09:15 AM and 03:20 PM IST "
                "on trading days. Place this as a Delivery order instead.",
            )
        return (True, "NORMAL", "")

    # Delivery orders
    if status["is_open"]:
        return (True, "NORMAL", "")
    else:
        return (True, "AMO", "Order placed as After-Market Order (AMO)")

def is_intraday_auto_square_off_due(ignore_simulation: bool = False) -> bool:
    """Returns True if the market is closed or the 03:20 PM IST intraday cutoff has been reached."""
    status = get_market_status(ignore_simulation=ignore_simulation)
    return not status.get("intraday_allowed", True)


def get_all_market_holidays() -> Dict[str, Any]:
    """
    Returns the complete list of live trading holidays and today's status for the UI.
    """
    now = get_ist_now()
    today_iso = now.strftime("%Y-%m-%d")
    holidays_dict = fetch_live_market_holidays()
    
    sorted_holidays: List[Dict[str, Any]] = []
    for d_iso in sorted(holidays_dict.keys()):
        h = holidays_dict[d_iso]
        sorted_holidays.append({
            "date": d_iso,
            "trading_date": h.get("trading_date", d_iso),
            "name": h.get("name"),
            "weekday": h.get("weekday"),
            "is_today": (d_iso == today_iso),
            "source": h.get("source")
        })

    today_info = get_today_holiday()

    return {
        "today": today_info,
        "holidays": sorted_holidays,
        "source": _HOLIDAY_CACHE.get("source", "NSE Live Exchange Feed"),
        "total_count": len(sorted_holidays)
    }

