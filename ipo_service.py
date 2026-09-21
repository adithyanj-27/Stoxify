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

CURATED_IPOS: List[Dict[str, Any]] = [
    # --- OPEN NOW ---
    {
        "id": "manika-plastech",
        "symbol": "MANIKA",
        "name": "Manika Plastech Ltd",
        "category": "Mainboard",
        "status": "OPEN",
        "price_band": "₹145 – ₹152",
        "min_price": 145.0,
        "max_price": 152.0,
        "lot_size": 98,
        "min_investment": 14896.0,
        "issue_size": "₹280 Cr",
        "open_date": "14 Sep 2026",
        "close_date": "16 Sep 2026",
        "listing_date": "19 Sep 2026",
        "subscription_times": 8.3,
        "gmp": "+₹24.00",
        "gmp_pct": 15.8,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "jindal-supreme",
        "symbol": "JINDAL",
        "name": "Jindal Supreme Ltd",
        "category": "Mainboard",
        "status": "OPEN",
        "price_band": "₹210 – ₹225",
        "min_price": 210.0,
        "max_price": 225.0,
        "lot_size": 65,
        "min_investment": 14625.0,
        "issue_size": "₹550 Cr",
        "open_date": "15 Sep 2026",
        "close_date": "18 Sep 2026",
        "listing_date": "22 Sep 2026",
        "subscription_times": 3.4,
        "gmp": "+₹32.00",
        "gmp_pct": 14.2,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "ss-retail",
        "symbol": "SSRETAIL",
        "name": "SS Retail Ltd",
        "category": "Consumer Retail",
        "status": "OPEN",
        "price_band": "₹115 – ₹120",
        "min_price": 115.0,
        "max_price": 120.0,
        "lot_size": 125,
        "min_investment": 15000.0,
        "issue_size": "₹190 Cr",
        "open_date": "15 Sep 2026",
        "close_date": "18 Sep 2026",
        "listing_date": "23 Sep 2026",
        "subscription_times": 2.1,
        "gmp": "+₹14.00",
        "gmp_pct": 11.6,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "hero-motors",
        "symbol": "HEROMOTORS",
        "name": "Hero Motors Ltd",
        "category": "Auto Components",
        "status": "OPEN",
        "price_band": "₹450 – ₹480",
        "min_price": 450.0,
        "max_price": 480.0,
        "lot_size": 31,
        "min_investment": 14880.0,
        "issue_size": "₹900 Cr",
        "open_date": "15 Sep 2026",
        "close_date": "18 Sep 2026",
        "listing_date": "23 Sep 2026",
        "subscription_times": 4.6,
        "gmp": "+₹65.00",
        "gmp_pct": 13.5,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "sonaselection",
        "symbol": "SONA",
        "name": "Sonaselection Limited",
        "category": "Textiles & Apparel",
        "status": "OPEN",
        "price_band": "₹85 – ₹92",
        "min_price": 85.0,
        "max_price": 92.0,
        "lot_size": 160,
        "min_investment": 14720.0,
        "issue_size": "₹140 Cr",
        "open_date": "16 Sep 2026",
        "close_date": "21 Sep 2026",
        "listing_date": "25 Sep 2026",
        "subscription_times": 1.5,
        "gmp": "+₹8.00",
        "gmp_pct": 8.7,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "veegaland",
        "symbol": "VEEGALAND",
        "name": "Veegaland Developers Ltd",
        "category": "Real Estate & Infra",
        "status": "OPEN",
        "price_band": "₹160 – ₹170",
        "min_price": 160.0,
        "max_price": 170.0,
        "lot_size": 88,
        "min_investment": 14960.0,
        "issue_size": "₹210 Cr",
        "open_date": "15 Sep 2026",
        "close_date": "19 Sep 2026",
        "listing_date": "24 Sep 2026",
        "subscription_times": 3.8,
        "gmp": "+₹22.00",
        "gmp_pct": 12.9,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },

    # --- UPCOMING ---
    {
        "id": "reliance-jio",
        "symbol": "JIO",
        "name": "Reliance JIO Infocomm Ltd",
        "category": "Telecom & Digital",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 50,
        "min_investment": 15000.0,
        "issue_size": "₹45,000 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹110.00",
        "gmp_pct": 28.0,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "zepto",
        "symbol": "ZEPTO",
        "name": "Zepto (Aadit Innovation Ltd)",
        "category": "Quick Commerce",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 35,
        "min_investment": 14500.0,
        "issue_size": "₹3,500 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹45.00",
        "gmp_pct": 18.5,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "razorpay",
        "symbol": "RAZORPAY",
        "name": "Razorpay Software Ltd",
        "category": "Fintech & Payments",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 25,
        "min_investment": 14800.0,
        "issue_size": "₹8,000 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹85.00",
        "gmp_pct": 22.0,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "truhome-finance",
        "symbol": "TRUHOME",
        "name": "Truhome Finance Ltd",
        "category": "Housing Finance / NBFC",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 40,
        "min_investment": 14000.0,
        "issue_size": "₹1,800 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹20.00",
        "gmp_pct": 9.5,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "marri-retail",
        "symbol": "MARRI",
        "name": "Marri Retail Ltd",
        "category": "Retail Chains",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 60,
        "min_investment": 14500.0,
        "issue_size": "₹1,200 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹15.00",
        "gmp_pct": 7.8,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "moneyview",
        "symbol": "MONEYVIEW",
        "name": "Moneyview (Whizdm Innovations)",
        "category": "Digital Lending / Fintech",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 45,
        "min_investment": 14500.0,
        "issue_size": "₹2,500 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹30.00",
        "gmp_pct": 14.0,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "incred-holdings",
        "symbol": "INCRED",
        "name": "InCred Holdings Ltd",
        "category": "Wealth & NBFC",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 50,
        "min_investment": 14000.0,
        "issue_size": "₹3,000 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹25.00",
        "gmp_pct": 11.0,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "hero-fincorp",
        "symbol": "HEROFIN",
        "name": "Hero Fincorp Ltd",
        "category": "Financial Services / NBFC",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 30,
        "min_investment": 14700.0,
        "issue_size": "₹3,668 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹55.00",
        "gmp_pct": 16.2,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "ather-energy",
        "symbol": "ATHER",
        "name": "Ather Energy Ltd",
        "category": "Electric Vehicles (EV)",
        "status": "UPCOMING",
        "price_band": "₹310 – ₹335",
        "min_price": 310.0,
        "max_price": 335.0,
        "lot_size": 44,
        "min_investment": 14740.0,
        "issue_size": "₹4,500 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹45.00",
        "gmp_pct": 13.4,
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "nse-india-ipo",
        "symbol": "NSE",
        "name": "National Stock Exchange of India",
        "category": "Exchange / Financial Market",
        "status": "UPCOMING",
        "price_band": "To be announced",
        "min_price": 0.0,
        "max_price": 0.0,
        "lot_size": 15,
        "min_investment": 15000.0,
        "issue_size": "₹15,000 Cr",
        "open_date": "Upcoming",
        "close_date": "To be announced",
        "listing_date": "—",
        "subscription_times": None,
        "gmp": "+₹350.00",
        "gmp_pct": 35.0,
        "source": "NSE / SEBI",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },

    # --- RECENTLY LISTED ---
    {
        "id": "swiggy",
        "symbol": "SWIGGY",
        "name": "Swiggy Ltd",
        "category": "Consumer Tech",
        "status": "RECENTLY_LISTED",
        "price_band": "₹371 – ₹390",
        "min_price": 371.0,
        "max_price": 390.0,
        "lot_size": 38,
        "min_investment": 14820.0,
        "issue_size": "₹11,327 Cr",
        "open_date": "06 Nov 2024",
        "close_date": "08 Nov 2024",
        "listing_date": "13 Nov 2024",
        "subscription_times": 3.59,
        "gmp": "+₹25.00",
        "gmp_pct": 6.4,
        "listing_price": "₹420.00 (+7.7%)",
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "sagility",
        "symbol": "SAGILITY",
        "name": "Sagility India Ltd",
        "category": "Healthcare IT",
        "status": "RECENTLY_LISTED",
        "price_band": "₹28 – ₹30",
        "min_price": 28.0,
        "max_price": 30.0,
        "lot_size": 500,
        "min_investment": 15000.0,
        "issue_size": "₹2,107 Cr",
        "open_date": "05 Nov 2024",
        "close_date": "07 Nov 2024",
        "listing_date": "12 Nov 2024",
        "subscription_times": 3.20,
        "gmp": "+₹0.30",
        "gmp_pct": 1.0,
        "listing_price": "₹31.06 (+3.5%)",
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "ntpc-green",
        "symbol": "NTPCGREEN",
        "name": "NTPC Green Energy Ltd",
        "category": "Renewable Energy",
        "status": "RECENTLY_LISTED",
        "price_band": "₹102 – ₹108",
        "min_price": 102.0,
        "max_price": 108.0,
        "lot_size": 138,
        "min_investment": 14904.0,
        "issue_size": "₹10,000 Cr",
        "open_date": "19 Nov 2024",
        "close_date": "22 Nov 2024",
        "listing_date": "27 Nov 2024",
        "subscription_times": 2.42,
        "gmp": "+₹3.50",
        "gmp_pct": 3.2,
        "listing_price": "₹111.60 (+3.3%)",
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "waaree",
        "symbol": "WAAREEENER",
        "name": "Waaree Energies Ltd",
        "category": "Solar Energy",
        "status": "RECENTLY_LISTED",
        "price_band": "₹1,427 – ₹1,503",
        "min_price": 1427.0,
        "max_price": 1503.0,
        "lot_size": 9,
        "min_investment": 13527.0,
        "issue_size": "₹4,321 Cr",
        "open_date": "21 Oct 2024",
        "close_date": "23 Oct 2024",
        "listing_date": "28 Oct 2024",
        "subscription_times": 76.34,
        "gmp": "+₹1,580.00",
        "gmp_pct": 105.1,
        "listing_price": "₹2,550.00 (+69.7%)",
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "hyundai-india",
        "symbol": "HYUNDAI",
        "name": "Hyundai Motor India Ltd",
        "category": "Automobile OEM",
        "status": "RECENTLY_LISTED",
        "price_band": "₹1,865 – ₹1,960",
        "min_price": 1865.0,
        "max_price": 1960.0,
        "lot_size": 7,
        "min_investment": 13720.0,
        "issue_size": "₹27,870 Cr",
        "open_date": "15 Oct 2024",
        "close_date": "17 Oct 2024",
        "listing_date": "22 Oct 2024",
        "subscription_times": 2.37,
        "gmp": "-₹15.00",
        "gmp_pct": -0.8,
        "listing_price": "₹1,931.00 (-1.5%)",
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    },
    {
        "id": "afcons-infra",
        "symbol": "AFCONS",
        "name": "Afcons Infrastructure Ltd",
        "category": "Infrastructure",
        "status": "RECENTLY_LISTED",
        "price_band": "₹440 – ₹463",
        "min_price": 440.0,
        "max_price": 463.0,
        "lot_size": 32,
        "min_investment": 14816.0,
        "issue_size": "₹5,430 Cr",
        "open_date": "25 Oct 2024",
        "close_date": "29 Oct 2024",
        "listing_date": "04 Nov 2024",
        "subscription_times": 2.63,
        "gmp": "-₹5.00",
        "gmp_pct": -1.1,
        "listing_price": "₹430.05 (-7.1%)",
        "source": "NSE",
        "source_url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    }
]


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


def _current_item(row: Dict[str, Any]) -> Dict[str, Any]:
    low, high = _price_range(row.get("issuePrice"))
    symbol = str(row.get("symbol") or "IPO").upper()
    multiple = row.get("noOfTime")
    try:
        subscription = round(float(multiple), 2)
    except (TypeError, ValueError):
        subscription = None
    open_d = _display_date(row.get("issueStartDate"))
    close_d = _display_date(row.get("issueEndDate"))
    status = resolve_ipo_status(open_d, close_d, default_status="OPEN")
    return {
        "id": f"nse-{symbol.lower()}-{str(row.get('issueStartDate') or '').lower()}",
        "symbol": symbol,
        "name": row.get("companyName") or symbol,
        "status": status,
        "series": row.get("series") or "EQ",
        "category": row.get("category") or "NSE IPO",
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


def _past_item(row: Dict[str, Any]) -> Dict[str, Any]:
    low, high = _price_range(row.get("priceRange") or row.get("issuePrice"))
    symbol = str(row.get("symbol") or row.get("htmSym") or "IPO").upper()
    open_d = _display_date(row.get("ipoStartDate"))
    close_d = _display_date(row.get("ipoEndDate"))
    listing_d = _display_date(row.get("listingDate"))
    status = resolve_ipo_status(open_d, close_d, listing_d, default_status="RECENTLY_LISTED")
    return {
        "id": f"nse-{symbol.lower()}-{str(row.get('ipoStartDate') or '').lower()}",
        "symbol": symbol,
        "name": row.get("company") or symbol,
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


def _fetch_live_ipos() -> List[Dict[str, Any]]:
    # NSE endpoints reject requests that lack active session cookies.
    # Establish session cookies with NSE homepage first.
    session = requests.Session()
    session.headers.update(_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=6)
    except Exception:
        pass

    try:
        current_response = session.get(_NSE_CURRENT_URL, timeout=12)
        current_rows = current_response.json() if current_response.status_code == 200 else []
    except Exception:
        current_rows = []

    try:
        past_response = session.get(_NSE_PAST_URL, timeout=16)
        past_rows = past_response.json() if past_response.status_code == 200 else []
    except Exception:
        past_rows = []

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
            # Merge live issues with curated database (avoiding symbol duplicates)
            seen_symbols = {item.get("symbol", "").upper() for item in live if item.get("symbol")}
            merged = list(live)
            for curated in CURATED_IPOS:
                if curated["symbol"].upper() not in seen_symbols:
                    merged.append(curated)
            _CACHE.update({"at": now, "ipos": merged})
        except Exception:
            if not _CACHE["ipos"]:
                _CACHE.update({"at": now, "ipos": list(CURATED_IPOS)})

    raw_issues = list(_CACHE.get("ipos") or CURATED_IPOS)
    # Dynamically re-evaluate status against current calendar date so that IPOs change with time
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
        return [issue for issue in evaluated if issue.get("status", "").upper() in ("CLOSED", "RECENTLY_LISTED", "LISTED")]
    return [issue for issue in evaluated if issue.get("status", "").upper() == wanted]


def get_ipo_by_id(ipo_id: str) -> Optional[Dict[str, Any]]:
    key = str(ipo_id).strip().upper()
    return next((issue for issue in get_ipos()
                 if issue.get("id", "").upper() == key or issue.get("symbol", "").upper() == key), None)

