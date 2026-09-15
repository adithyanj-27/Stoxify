"""Live, information-only IPO feed sourced from NSE public APIs.

NSE publishes the current issue feed and a public past-issues feed. It does not
publish GMP, individual QIB/NII/retail subscription splits, retail lot size, or
company descriptions here, so this module deliberately omits those fields rather
than carrying forward stale or invented values.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import re
import time

import requests

_NSE_CURRENT_URL = "https://www.nseindia.com/api/ipo-current-issue"
_NSE_PAST_URL = "https://www.nseindia.com/api/public-past-issues"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
}
_CACHE: Dict[str, Any] = {"at": 0.0, "ipos": []}
_CACHE_TTL_SECONDS = 300


def _parse_date(value: Any) -> Optional[datetime]:
    if not value or str(value).strip() in {"-", "--"}:
        return None
    text = str(value).strip()
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y", "%d-%b-%y"):
        try:
            return datetime.strptime(text.title(), fmt)
        except ValueError:
            continue
    return None


def _display_date(value: Any) -> str:
    parsed = _parse_date(value)
    return parsed.strftime("%d %b %Y") if parsed else "—"


def _price_range(value: Any) -> tuple:
    numbers = re.findall(r"\d+(?:\.\d+)?", str(value or ""))
    if not numbers:
        return None, None
    values = [float(number) for number in numbers]
    return min(values), max(values)


def _display_price(value: Any) -> str:
    low, high = _price_range(value)
    if low is None:
        return "—"
    if low == high:
        return f"₹{low:,.2f}".rstrip("0").rstrip(".")
    return f"₹{low:,.2f} – ₹{high:,.2f}".replace(".00", "")


def _format_issue_size(value: Any) -> str:
    try:
        shares = float(value)
    except (TypeError, ValueError):
        return "—"
    if shares >= 10_000_000:
        return f"{shares / 10_000_000:.2f} Cr shares"
    if shares >= 100_000:
        return f"{shares / 100_000:.2f} L shares"
    return f"{shares:,.0f} shares"


def _current_item(row: Dict[str, Any]) -> Dict[str, Any]:
    low, high = _price_range(row.get("issuePrice"))
    symbol = str(row.get("symbol") or "IPO").upper()
    multiple = row.get("noOfTime")
    try:
        subscription = round(float(multiple), 2)
    except (TypeError, ValueError):
        subscription = None
    return {
        "id": f"nse-{symbol.lower()}-{str(row.get('issueStartDate') or '').lower()}",
        "symbol": symbol,
        "name": row.get("companyName") or symbol,
        "status": "OPEN",
        "series": row.get("series") or "EQ",
        "category": row.get("category") or "NSE IPO",
        "price_band": _display_price(row.get("issuePrice")),
        "min_price": low,
        "max_price": high,
        "open_date": _display_date(row.get("issueStartDate")),
        "close_date": _display_date(row.get("issueEndDate")),
        "listing_date": "—",
        "issue_size": _format_issue_size(row.get("issueSize")),
        "subscription_times": subscription,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        "is_new": False,
    }


def _past_item(row: Dict[str, Any]) -> Dict[str, Any]:
    low, high = _price_range(row.get("priceRange") or row.get("issuePrice"))
    symbol = str(row.get("symbol") or row.get("htmSym") or "IPO").upper()
    return {
        "id": f"nse-{symbol.lower()}-{str(row.get('ipoStartDate') or '').lower()}",
        "symbol": symbol,
        "name": row.get("company") or symbol,
        "status": "RECENTLY_LISTED",
        "series": row.get("securityType") or "EQ",
        "category": "NSE IPO",
        "price_band": _display_price(row.get("priceRange") or row.get("issuePrice")),
        "min_price": low,
        "max_price": high,
        "open_date": _display_date(row.get("ipoStartDate")),
        "close_date": _display_date(row.get("ipoEndDate")),
        "listing_date": _display_date(row.get("listingDate")),
        "issue_size": "—",
        "subscription_times": None,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        "is_new": False,
    }


def _fetch_live_ipos() -> List[Dict[str, Any]]:
    # NSE currently exposes open and public past issues. Its "all upcoming" endpoint
    # returns an empty object, so we never mislabel unavailable data as upcoming.
    current_response = requests.get(_NSE_CURRENT_URL, headers=_HEADERS, timeout=12)
    past_response = requests.get(_NSE_PAST_URL, headers=_HEADERS, timeout=16)
    current_rows = current_response.json() if current_response.status_code == 200 else []
    past_rows = past_response.json() if past_response.status_code == 200 else []
    if not isinstance(current_rows, list):
        current_rows = []
    if not isinstance(past_rows, list):
        past_rows = []

    open_issues = [_current_item(row) for row in current_rows if isinstance(row, dict)]
    past_issues = [_past_item(row) for row in past_rows if isinstance(row, dict)]
    # NSE public past data is newest first; show only a compact recent-news feed.
    return open_issues + past_issues[:18]


def get_ipos(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    now = time.monotonic()
    if now - _CACHE["at"] > _CACHE_TTL_SECONDS:
        try:
            live = _fetch_live_ipos()
            _CACHE.update({"at": now, "ipos": live})
        except Exception:
            # Preserve a previously fetched real NSE result. On the first outage the
            # honest result is an empty list, never a stale hardcoded IPO catalogue.
            if not _CACHE["ipos"]:
                _CACHE.update({"at": now, "ipos": []})

    issues = list(_CACHE["ipos"])
    if not status_filter or status_filter.upper() == "ALL":
        return issues
    wanted = status_filter.upper()
    return [issue for issue in issues if issue.get("status") == wanted]


def get_ipo_by_id(ipo_id: str) -> Optional[Dict[str, Any]]:
    key = str(ipo_id).strip().upper()
    return next((issue for issue in get_ipos()
                 if issue.get("id", "").upper() == key or issue.get("symbol", "").upper() == key), None)
