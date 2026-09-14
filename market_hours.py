from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple

IST = timezone(timedelta(hours=5, minutes=30))

#Simulation flag to allow testing off-hours if the user wants
_SIMULATION_MODE = False

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

# Official NSE/BSE Trading Holidays Calendar
NSE_HOLIDAYS: Dict[str, str] = {
    # 2026
    "2026-01-26": "Republic Day",
    "2026-02-17": "Mahashivratri",
    "2026-03-03": "Holi",
    "2026-03-20": "Id-Ul-Fitr (Ramzan Id)",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-27": "Bakri Id",
    "2026-06-26": "Muharram",
    "2026-09-14": "Eid-e-Milad (Milad-un-Nabi)",
    "2026-09-16": "Eid-e-Milad",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-09": "Diwali Laxmi Pujan",
    "2026-11-10": "Diwali Balipratipada",
    "2026-11-24": "Gurunanak Jayanti",
    "2026-12-25": "Christmas",
    # 2025
    "2025-01-26": "Republic Day",
    "2025-02-26": "Mahashivratri",
    "2025-03-14": "Holi",
    "2025-03-31": "Id-Ul-Fitr",
    "2025-04-10": "Mahavir Jayanti",
    "2025-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2025-04-18": "Good Friday",
    "2025-05-01": "Maharashtra Day",
    "2025-06-07": "Bakri Id",
    "2025-07-06": "Muharram",
    "2025-08-15": "Independence Day",
    "2025-09-05": "Eid-e-Milad",
    "2025-10-02": "Mahatma Gandhi Jayanti",
    "2025-10-21": "Diwali Laxmi Pujan",
    "2025-10-22": "Diwali Balipratipada",
    "2025-11-05": "Gurunanak Jayanti",
    "2025-12-25": "Christmas",
    # 2024
    "2024-01-22": "Special Holiday (Ram Mandir)",
    "2024-01-26": "Republic Day",
    "2024-03-08": "Mahashivratri",
    "2024-03-25": "Holi",
    "2024-03-29": "Good Friday",
    "2024-04-11": "Id-Ul-Fitr (Ramzan Id)",
    "2024-04-17": "Shri Ram Navami",
    "2024-05-01": "Maharashtra Day",
    "2024-05-20": "General Elections (Mumbai)",
    "2024-06-17": "Bakri Id",
    "2024-07-17": "Muharram",
    "2024-08-15": "Independence Day",
    "2024-09-14": "Eid-e-Milad",
    "2024-09-16": "Eid-e-Milad",
    "2024-10-02": "Mahatma Gandhi Jayanti",
    "2024-11-01": "Diwali Laxmi Pujan",
    "2024-11-15": "Gurunanak Jayanti",
    "2024-11-20": "Maharashtra Assembly Elections",
    "2024-12-25": "Christmas",
}

def get_market_status() -> Dict[str, Any]:
    now = get_ist_now()
    weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
    current_time = now.time()

    time_str = now.strftime("%I:%M:%S %p IST")
    date_str = now.strftime("%d %b %Y")
    date_iso = now.strftime("%Y-%m-%d")

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

    # 1. Check for Scheduled Trading Holidays
    holiday_name = NSE_HOLIDAYS.get(date_iso)
    if holiday_name:
        short_name = holiday_name.split('(')[0].strip()
        return {
            "is_open": False,
            "session": "HOLIDAY",
            "intraday_allowed": False,
            "status_text": f"Market CLOSED ({short_name})",
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
