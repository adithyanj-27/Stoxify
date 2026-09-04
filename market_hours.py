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

def get_market_status() -> Dict[str, Any]:
    now = get_ist_now()
    weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
    current_time = now.time()

    time_str = now.strftime("%I:%M:%S %p IST")
    date_str = now.strftime("%d %b %Y")

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
            "simulation_mode": True
        }

    is_weekday = weekday < 5
    h = current_time.hour
    m = current_time.minute
    total_minutes = h * 60 + m


    if is_weekday:
        if 540 <= total_minutes < 548:
            return {
                "is_open": False,
                "session": "PRE_MARKET",
                "intraday_allowed": False,
                "status_text": "Pre-Market Session",
                "subtext": "Normal trading begins at 09:15 AM IST",
                "badge_color": "orange",
                "current_time_ist": time_str,
                "date_ist": date_str,
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
                "simulation_mode": False
            }
    else:
        return {
            "is_open": False,
            "session": "WEEKEND",
            "intraday_allowed": False,
            "status_text": "Market CLOSED (Weekend)",
            "subtext": "Opens Monday at 09:15 AM IST • AMO Active",
            "badge_color": "gray",
            "current_time_ist": time_str,
            "date_ist": date_str,
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
