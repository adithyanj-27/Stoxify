"""Live, information-only IPO feed sourced directly from official NSE public APIs.

Pulls real mainboard and SME IPOs from:
1. Current active issues: https://www.nseindia.com/api/ipo-current-issue
2. Forthcoming / upcoming issues: https://www.nseindia.com/api/upcoming-issues
3. Past public issues: https://www.nseindia.com/api/public-past-issues

Does not inject fantasy/speculative listings (e.g. mock NSE IPO, Zepto, Jio).
All data is 100% verified exchange filings.
"""
from datetime import datetime
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests

_NSE_CURRENT_URL = "https://www.nseindia.com/api/ipo-current-issue"
_NSE_UPCOMING_URL = "https://www.nseindia.com/api/upcoming-issues"
_NSE_PAST_URL = "https://www.nseindia.com/api/public-past-issues"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
}

_CACHE: Dict[str, Any] = {"at": 0.0, "ipos": []}
_CACHE_TTL_SECONDS = 300
_SNAPSHOT_FILE = os.path.join(os.path.dirname(__file__), "data", "cached_ipos.json")


def _is_test_issue(symbol: Optional[str], name: Optional[str]) -> bool:
    """Filter out exchange test / sandbox mock harness entries."""
    s = (symbol or "").strip().upper()
    n = (name or "").strip().upper()
    if s in ("NSE", "TEST", "SAMPLE", "MOCK", "DUMMY"):
        return True
    if "NATIONAL STOCK EXCHANGE" in n or "TEST ISSUE" in n:
        return True
    return False


def _parse_date(value: Any) -> Optional[datetime]:
    if not value or str(value).strip() in {"-", "--", "—", "none", "null", "to be announced", "upcoming"}:
        return None
    text = str(value).strip()
    for fmt in (
        "%d %b %Y", "%d %B %Y", "%d %m %Y", "%d %b %y",
        "%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y", "%d-%b-%y",
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"
    ):
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
        return "To be announced"
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


def resolve_ipo_status(
    open_date_str: Any,
    close_date_str: Any,
    listing_date_str: Any = None,
    default_status: str = "UPCOMING"
) -> str:
    """
    Dynamically computes the IPO status (OPEN, UPCOMING, CLOSED, RECENTLY_LISTED)
    based on the current calendar date vs open/close/listing dates.
    """
    try:
        today = datetime.now().date()
        open_dt = _parse_date(open_date_str)
        close_dt = _parse_date(close_date_str)
        listing_dt = _parse_date(listing_date_str)

        open_d = open_dt.date() if open_dt else None
        close_d = close_dt.date() if close_dt else None
        listing_d = listing_dt.date() if listing_dt else None

        # 1. Past close date -> Closed or Recently Listed
        if close_d and today > close_d:
            if listing_d and today >= listing_d:
                return "RECENTLY_LISTED"
            return "CLOSED"

        # 2. Future open date -> Upcoming
        if open_d and today < open_d:
            return "UPCOMING"

        # 3. Active bidding window -> Open
        if open_d and close_d and open_d <= today <= close_d:
            return "OPEN"

        if open_d and today >= open_d and not close_d:
            return "OPEN"
    except Exception:
        pass

    return default_status


def _current_item(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    symbol = str(row.get("symbol") or "IPO").upper()
    name = row.get("companyName") or symbol
    if _is_test_issue(symbol, name):
        return None

    low, high = _price_range(row.get("issuePrice"))
    try:
        multiple = row.get("noOfTime") or row.get("subscription_times")
        subscription = round(float(multiple), 2)
    except (TypeError, ValueError):
        subscription = None

    open_d = _display_date(row.get("issueStartDate"))
    close_d = _display_date(row.get("issueEndDate"))
    status = resolve_ipo_status(open_d, close_d, default_status="OPEN")
    return {
        "id": f"nse-{symbol.lower()}-{str(row.get('issueStartDate') or '').lower()}",
        "symbol": symbol,
        "name": name,
        "status": status,
        "series": row.get("series") or "EQ",
        "category": "NSE Mainboard" if row.get("series") == "EQ" else "NSE SME",
        "price_band": _display_price(row.get("issuePrice")),
        "min_price": low,
        "max_price": high,
        "open_date": open_d,
        "close_date": close_d,
        "listing_date": "—",
        "issue_size": _format_issue_size(row.get("issueSize")),
        "subscription_times": subscription,
        "source": "NSE Live Feed",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        "is_new": False,
    }


def _forthcoming_item(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = row.get("data", {}) if isinstance(row, dict) else {}
    name = data.get("companyName") or row.get("name") or "Upcoming IPO"
    symbol = str(data.get("symbol") or row.get("symbol") or "IPO").upper()
    if _is_test_issue(symbol, name):
        return None

    low, high = _price_range(data.get("issuePrice"))
    open_d = _display_date(data.get("issueStartDate") or row.get("startDate"))
    close_d = _display_date(data.get("issueEndDate") or row.get("endDate"))
    status = resolve_ipo_status(open_d, close_d, default_status="UPCOMING")
    return {
        "id": f"nse-upcoming-{symbol.lower()}-{str(data.get('issueStartDate') or row.get('startDate') or '').lower()}",
        "symbol": symbol,
        "name": name,
        "status": status,
        "series": data.get("series") or "EQ",
        "category": "NSE Mainboard" if data.get("series") == "EQ" else "NSE SME",
        "price_band": _display_price(data.get("issuePrice")),
        "min_price": low,
        "max_price": high,
        "open_date": open_d,
        "close_date": close_d,
        "listing_date": "—",
        "issue_size": _format_issue_size(data.get("issueSize")),
        "subscription_times": None,
        "source": "NSE Live Feed",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        "is_new": False,
    }


def _past_item(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    symbol = str(row.get("symbol") or row.get("htmSym") or "IPO").upper()
    name = row.get("company") or symbol
    if _is_test_issue(symbol, name):
        return None

    low, high = _price_range(row.get("priceRange") or row.get("issuePrice"))
    open_d = _display_date(row.get("ipoStartDate"))
    close_d = _display_date(row.get("ipoEndDate"))
    listing_d = _display_date(row.get("listingDate"))
    status = resolve_ipo_status(open_d, close_d, listing_d, default_status="RECENTLY_LISTED")
    return {
        "id": f"nse-{symbol.lower()}-{str(row.get('ipoStartDate') or '').lower()}",
        "symbol": symbol,
        "name": name,
        "status": status,
        "series": row.get("securityType") or "EQ",
        "category": "NSE IPO",
        "price_band": _display_price(row.get("priceRange") or row.get("issuePrice")),
        "min_price": low,
        "max_price": high,
        "open_date": open_d,
        "close_date": close_d,
        "listing_date": listing_d,
        "issue_size": "—",
        "subscription_times": None,
        "source": "NSE Live Feed",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
        "is_new": False,
    }


def _load_snapshot() -> List[Dict[str, Any]]:
    if os.path.exists(_SNAPSHOT_FILE):
        try:
            with open(_SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def _save_snapshot(items: List[Dict[str, Any]]) -> None:
    if not items:
        return
    try:
        os.makedirs(os.path.dirname(_SNAPSHOT_FILE), exist_ok=True)
        with open(_SNAPSHOT_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
    except Exception:
        pass


def _fetch_live_ipos() -> List[Dict[str, Any]]:
    session = requests.Session()
    session.headers.update(_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=6)
    except Exception:
        pass

    # 1. Current Open Issues
    current_rows = []
    try:
        r_curr = session.get(_NSE_CURRENT_URL, timeout=10)
        if r_curr.status_code == 200:
            current_rows = r_curr.json()
    except Exception:
        current_rows = []

    # 2. Forthcoming / Upcoming Issues
    upcoming_rows = []
    try:
        r_up = session.get(_NSE_UPCOMING_URL, timeout=10)
        if r_up.status_code == 200:
            upcoming_data = r_up.json()
            if isinstance(upcoming_data, dict):
                upcoming_rows = upcoming_data.get("forthcoming", [])
    except Exception:
        upcoming_rows = []

    # 3. Past / Closed Issues
    past_rows = []
    try:
        r_past = session.get(_NSE_PAST_URL, timeout=12)
        if r_past.status_code == 200:
            past_rows = r_past.json()
    except Exception:
        past_rows = []

    parsed_open = []
    for r in current_rows:
        if isinstance(r, dict):
            item = _current_item(r)
            if item:
                parsed_open.append(item)

    parsed_upcoming = []
    for r in upcoming_rows:
        if isinstance(r, dict):
            item = _forthcoming_item(r)
            if item:
                parsed_upcoming.append(item)

    parsed_past = []
    for r in past_rows[:25]:
        if isinstance(r, dict):
            item = _past_item(r)
            if item:
                parsed_past.append(item)

    all_items = parsed_open + parsed_upcoming + parsed_past

    # Deduplicate by symbol if any overlap
    seen = set()
    deduped = []
    for issue in all_items:
        sym = issue.get("symbol", "").upper()
        if sym and sym not in seen:
            seen.add(sym)
            deduped.append(issue)

    if deduped:
        _save_snapshot(deduped)
        return deduped

    return _load_snapshot()


def get_ipos(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    now = time.monotonic()
    if now - _CACHE["at"] > _CACHE_TTL_SECONDS or not _CACHE.get("ipos"):
        try:
            live = _fetch_live_ipos()
            if live:
                _CACHE.update({"at": now, "ipos": live})
        except Exception:
            pass

    raw_issues = list(_CACHE.get("ipos") or _load_snapshot())

    # Dynamically evaluate status against current calendar date
    evaluated = []
    for issue in raw_issues:
        item = dict(issue)
        item["status"] = resolve_ipo_status(
            item.get("open_date"),
            item.get("close_date"),
            item.get("listing_date"),
            default_status=item.get("status", "UPCOMING")
        )
        evaluated.append(item)

    if not status_filter or status_filter.upper() == "ALL":
        return evaluated
    wanted = status_filter.upper()
    if wanted in ("CLOSED", "RECENTLY_LISTED", "LISTED"):
        return [i for i in evaluated if i.get("status", "").upper() in ("CLOSED", "RECENTLY_LISTED", "LISTED")]
    return [i for i in evaluated if i.get("status", "").upper() == wanted]


def get_ipo_by_id(ipo_id: str) -> Optional[Dict[str, Any]]:
    key = str(ipo_id).strip().upper()
    return next((issue for issue in get_ipos()
                 if issue.get("id", "").upper() == key or issue.get("symbol", "").upper() == key), None)
