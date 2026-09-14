from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional
import time
import yfinance as yf

IST = timezone(timedelta(hours=5, minutes=30))

# Simulation flag to allow testing off-hours if the user wants
_SIMULATION_MODE = False

# In-memory cache for Yahoo Finance live market activity probe
_MARKET_ACTIVITY_CACHE: Dict[str, Any] = {}

def check_live_market_activity_yahoo() -> Optional[bool]:
    """
    Checks Yahoo Finance live feed for the benchmark index ^NSEI (NIFTY 50).
    Returns:
      True  -> Market is actively trading today (live open and day_high exist).
      False -> Zero trades recorded today during normal hours (Exchange is closed / Holiday).
      None  -> Before 09:20 AM or network check inconclusive.
    """
    now = get_ist_now()
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

# Standard National Holidays (Fixed Annual Dates)
NSE_HOLIDAYS: Dict[str, str] = {
    # Fixed national closures
    "01-26": "Republic Day",
    "05-01": "Maharashtra Day",
    "08-15": "Independence Day",
    "10-02": "Mahatma Gandhi Jayanti",
    "12-25": "Christmas",
}

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

def get_market_status() -> Dict[str, Any]:
    now = get_ist_now()
    weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
    current_time = now.time()

    time_str = now.strftime("%I:%M:%S %p IST")
    date_str = now.strftime("%d %b %Y")
    date_mm_dd = now.strftime("%m-%d")

    if _SIMULATION_MODE:
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

    # 1. Check for Scheduled Fixed National Holidays
    holiday_name = NSE_HOLIDAYS.get(date_mm_dd)
    if holiday_name:
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
    status = get_market_status()

    if product == "INTRADAY":
        if not status["intraday_allowed"]:
            # In paper trading / simulation platform, allow execution as 24/7 simulated intraday
            return (True, "INTRADAY", "Simulated Intraday 5x order executed")
        return (True, "NORMAL", "")

    # Delivery orders
    if status["is_open"]:
        return (True, "NORMAL", "")
    else:
        return (True, "AMO", "Order placed as After-Market Order (AMO)")
