import math
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import market_service

# Lot sizes mandated by NSE (as of recent revised contract specs)
LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 40,
    "MIDCPNIFTY": 75,
    "SENSEX": 10
}

STRIKE_STEPS = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25,
    "SENSEX": 100
}

def _get_next_thursday():
    now = datetime.now()
    days_ahead = 3 - now.weekday()  # Thursday is 3
    if days_ahead <= 0:  # If today is Thursday or later, look to next week
        days_ahead += 7
    expiry_dt = now + timedelta(days=days_ahead)
    return expiry_dt.strftime("%d %b %Y")

def _black_scholes(s: float, k: float, t: float, r: float, sigma: float, option_type: str = "call") -> float:
    """Standard Black-Scholes formula for realistic option pricing."""
    if t <= 0:
        return max(0.0, s - k) if option_type == "call" else max(0.0, k - s)
    try:
        d1 = (math.log(s / k) + (r + 0.5 * sigma ** 2) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        def norm_cdf(x):
            return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

        if option_type == "call":
            price = s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)
        else:
            price = k * math.exp(-r * t) * norm_cdf(-d2) - s * norm_cdf(-d1)
        return max(0.05, round(price, 2))
    except Exception:
        intrinsic = max(0.0, s - k) if option_type == "call" else max(0.0, k - s)
        return max(0.05, round(intrinsic + 15.0, 2))

def get_option_chain(symbol: str = "NIFTY") -> Dict[str, Any]:
    clean_sym = symbol.upper().replace(" ", "").replace("^", "")
    if "BANK" in clean_sym:
        clean_sym = "BANKNIFTY"
        idx_sym = "^NSEBANK"
        default_spot = 51000.0
    else:
        clean_sym = "NIFTY"
        idx_sym = "^NSEI"
        default_spot = 24000.0

    # Get live spot index price
    indices = market_service.get_indices()
    spot_price = default_spot
    change = 0.0
    change_pct = 0.0

    for idx in indices:
        if (clean_sym == "NIFTY" and idx.get("name") == "NIFTY 50") or \
           (clean_sym == "BANKNIFTY" and idx.get("name") == "BANK NIFTY"):
            spot_price = float(idx.get("price") or default_spot)
            change = float(idx.get("change") or 0.0)
            change_pct = float(idx.get("change_pct") or 0.0)
            break

    step = STRIKE_STEPS.get(clean_sym, 50)
    lot_size = LOT_SIZES.get(clean_sym, 25)
    expiry = _get_next_thursday()

    # ATM Strike rounded to nearest step
    atm_strike = round(spot_price / step) * step

    # Generate 15 strikes centered around ATM (7 ITM, ATM, 7 OTM)
    strikes = []
    num_strikes = 7
    for i in range(-num_strikes, num_strikes + 1):
        k = atm_strike + (i * step)
        strikes.append(k)

    r = 0.065  # RBI repo rate approx 6.5%
    t = 4.0 / 365.0  # Approx 4 days to weekly expiry
    iv_base = 0.132  # India VIX approx 13.2%

    chain_rows = []
    total_call_oi = 0
    total_put_oi = 0

    for k in strikes:
        moneyness = (spot_price - k) / spot_price
        iv = max(0.08, iv_base + abs(moneyness) * 0.15)

        call_ltp = _black_scholes(spot_price, k, t, r, iv, "call")
        put_ltp = _black_scholes(spot_price, k, t, r, iv, "put")

        # Realistic Open Interest simulation based on strike distance
        dist_factor = max(0.1, 1.0 - (abs(k - spot_price) / (step * 8)))
        call_oi = round((12.5 * dist_factor + (0.5 if k >= spot_price else 0.2)) * 100000)
        put_oi = round((14.2 * dist_factor + (0.6 if k <= spot_price else 0.3)) * 100000)

        total_call_oi += call_oi
        total_put_oi += put_oi

        # Call Delta approx
        d1 = (math.log(spot_price / k) + (r + 0.5 * iv ** 2) * t) / (iv * math.sqrt(t))
        call_delta = round((1.0 + math.erf(d1 / math.sqrt(2.0))) / 2.0, 2)
        put_delta = round(call_delta - 1.0, 2)

        chain_rows.append({
            "strike": k,
            "is_atm": (k == atm_strike),
            "call": {
                "symbol": f"{clean_sym}{int(k)}CE",
                "ltp": call_ltp,
                "oi": call_oi,
                "oi_chg_pct": round((k % 17 - 8) * 1.5, 1),
                "iv": round(iv * 100, 1),
                "delta": call_delta,
                "in_the_money": (spot_price > k)
            },
            "put": {
                "symbol": f"{clean_sym}{int(k)}PE",
                "ltp": put_ltp,
                "oi": put_oi,
                "oi_chg_pct": round((k % 13 - 6) * 1.8, 1),
                "iv": round(iv * 100, 1),
                "delta": put_delta,
                "in_the_money": (spot_price < k)
            }
        })

    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else 1.0

    return {
        "underlying": clean_sym,
        "spot_price": spot_price,
        "change": change,
        "change_pct": change_pct,
        "expiry": expiry,
        "lot_size": lot_size,
        "atm_strike": atm_strike,
        "pcr": pcr,
        "pcr_sentiment": "Bullish" if pcr > 1.05 else ("Bearish" if pcr < 0.85 else "Neutral"),
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "chain": chain_rows
    }
