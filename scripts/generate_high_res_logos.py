"""
Professional High-Resolution Logo Generator for Stoxify
Generates crisp, large, vibrant 256x256 brand assets for:
- All 91 Indian Equities (72 Base Stocks + 19 Newly Listed)
- All 12 Mutual Fund AMCs (PPFAS, Quant, Mirae, Nippon, Axis, SBI, HDFC, ICICI, etc.)
- All 15 ETFs (Dedicated Gold, Silver, Index and Sectoral Badges - NO generic globes)
- All 35+ IPO Companies
"""
import os
import sys
import io
import json
import requests
import concurrent.futures
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATIC_LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "logos")
os.makedirs(STATIC_LOGOS_DIR, exist_ok=True)

# Select best system font
FONT_PATH = "C:\\Windows\\Fonts\\segoeuib.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

# Brand definitions with authentic corporate marks and colors
BRAND_CONFIGS = {
    # Banking & Finance
    "HDFCBANK": {"bg": "#004C8F", "accent": "#ED1C24", "text": "#FFFFFF", "mark": "HDFC"},
    "ICICIBANK": {"bg": "#9B1B1E", "accent": "#F37021", "text": "#FFFFFF", "mark": "ICICI"},
    "SBIN": {"bg": "#280071", "accent": "#00A3E0", "text": "#FFFFFF", "mark": "SBI", "circle_accent": True},
    "AXISBANK": {"bg": "#97144D", "accent": "#ED1C24", "text": "#FFFFFF", "mark": "AXIS"},
    "KOTAKBANK": {"bg": "#ED1C24", "accent": "#003366", "text": "#FFFFFF", "mark": "KOTAK"},
    "BANKBARODA": {"bg": "#F37021", "accent": "#EA580C", "text": "#FFFFFF", "mark": "BOB"},
    "PNB": {"bg": "#D32F2F", "accent": "#FBBF24", "text": "#FFFFFF", "mark": "PNB"},
    "CANBK": {"bg": "#0072CE", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "CANARA"},
    "IDFCFIRSTB": {"bg": "#9D2235", "accent": "#BE123C", "text": "#FFFFFF", "mark": "IDFC"},
    "FEDERALBNK": {"bg": "#002E6E", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "FED"},
    "YESBANK": {"bg": "#003399", "accent": "#DC2626", "text": "#FFFFFF", "mark": "YES"},
    "INDUSINDBK": {"bg": "#C01818", "accent": "#991B1B", "text": "#FFFFFF", "mark": "INDUS"},
    "AUBANK": {"bg": "#4A154B", "accent": "#F97316", "text": "#FFFFFF", "mark": "AU"},
    "BANDHANBNK": {"bg": "#005A9C", "accent": "#DC2626", "text": "#FFFFFF", "mark": "BANDHAN"},
    "BAJFINANCE": {"bg": "#0066B2", "accent": "#004B87", "text": "#FFFFFF", "mark": "BAJAJ"},
    "JIOFIN": {"bg": "#0A2885", "accent": "#0284C7", "text": "#FFFFFF", "mark": "JIO"},
    "PFC": {"bg": "#0D47A1", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "PFC"},
    "RECLTD": {"bg": "#0D47A1", "accent": "#10B981", "text": "#FFFFFF", "mark": "REC"},
    "IRFC": {"bg": "#8B0000", "accent": "#D4AF37", "text": "#FFFFFF", "mark": "IRFC"},

    # IT & Tech
    "TCS": {"bg": "#0072C6", "accent": "#003A70", "text": "#FFFFFF", "mark": "TCS"},
    "INFY": {"bg": "#007CC3", "accent": "#005A9C", "text": "#FFFFFF", "mark": "INFY"},
    "WIPRO": {"bg": "#004B87", "accent": "#8A2BE2", "text": "#FFFFFF", "mark": "WIPRO"},
    "TATAELXSI": {"bg": "#0F3E7A", "accent": "#2563EB", "text": "#FFFFFF", "mark": "ELXSI"},
    "TATATECH": {"bg": "#0F3E7A", "accent": "#3B82F6", "text": "#FFFFFF", "mark": "TATA"},
    "PAYTM": {"bg": "#002E6E", "accent": "#00BAF2", "text": "#FFFFFF", "mark": "Paytm"},
    "ETERNAL": {"bg": "#E23744", "accent": "#CB202D", "text": "#FFFFFF", "mark": "zomato"},
    "ZOMATO": {"bg": "#E23744", "accent": "#CB202D", "text": "#FFFFFF", "mark": "zomato"},

    # Conglomerates, Energy & Metals
    "RELIANCE": {"bg": "#002D62", "accent": "#004B87", "text": "#FFFFFF", "mark": "RIL"},
    "TATASTEEL": {"bg": "#0F3E7A", "accent": "#0072CE", "text": "#FFFFFF", "mark": "TATA"},
    "TATAPOWER": {"bg": "#0F3E7A", "accent": "#06B6D4", "text": "#FFFFFF", "mark": "TATA"},
    "JSWSTEEL": {"bg": "#C026D3", "accent": "#9333EA", "text": "#FFFFFF", "mark": "JSW"},
    "HINDALCO": {"bg": "#B45309", "accent": "#D97706", "text": "#FFFFFF", "mark": "HINDALCO"},
    "VEDL": {"bg": "#1E3A8A", "accent": "#2563EB", "text": "#FFFFFF", "mark": "VEDANTA"},
    "NTPC": {"bg": "#003366", "accent": "#0284C7", "text": "#FFFFFF", "mark": "NTPC"},
    "POWERGRID": {"bg": "#00823B", "accent": "#005A2B", "text": "#FFFFFF", "mark": "GRID"},
    "ONGC": {"bg": "#B22222", "accent": "#FFCC00", "text": "#FFFFFF", "mark": "ONGC"},
    "COALINDIA": {"bg": "#1E293B", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "CIL"},
    "ADANIENT": {"bg": "#2A2A84", "accent": "#6B52AE", "text": "#FFFFFF", "mark": "ADANI"},
    "ADANIPORTS": {"bg": "#1E2269", "accent": "#3B82F6", "text": "#FFFFFF", "mark": "ADANI"},
    "ADANIGREEN": {"bg": "#10B981", "accent": "#059669", "text": "#FFFFFF", "mark": "ADANI"},
    "ADANIPOWER": {"bg": "#D97706", "accent": "#B45309", "text": "#FFFFFF", "mark": "ADANI"},
    "SUZLON": {"bg": "#689F38", "accent": "#33691E", "text": "#FFFFFF", "mark": "SUZLON"},
    "IREDA": {"bg": "#2E7D32", "accent": "#10B981", "text": "#FFFFFF", "mark": "IREDA"},
    "NHPC": {"bg": "#0277BD", "accent": "#0369A1", "text": "#FFFFFF", "mark": "NHPC"},

    # Auto & Manufacturing
    "MARUTI": {"bg": "#003B70", "accent": "#E31B23", "text": "#FFFFFF", "mark": "MARUTI"},
    "TATAMOTORS": {"bg": "#0F3E7A", "accent": "#2563EB", "text": "#FFFFFF", "mark": "TATA"},
    "TMCV": {"bg": "#0F3E7A", "accent": "#2563EB", "text": "#FFFFFF", "mark": "TATA"},
    "TMPV": {"bg": "#0F3E7A", "accent": "#3B82F6", "text": "#FFFFFF", "mark": "TATA"},
    "M&M": {"bg": "#D32F2F", "accent": "#B71C1C", "text": "#FFFFFF", "mark": "M&M"},
    "BAJAJ-AUTO": {"bg": "#004B87", "accent": "#0284C7", "text": "#FFFFFF", "mark": "BAJAJ"},
    "TVSMOTOR": {"bg": "#1E40AF", "accent": "#DC2626", "text": "#FFFFFF", "mark": "TVS"},
    "EICHERMOT": {"bg": "#991B1B", "accent": "#DC2626", "text": "#FFFFFF", "mark": "ROYAL"},
    "ASHOKLEY": {"bg": "#15803D", "accent": "#16A34A", "text": "#FFFFFF", "mark": "LEYLAND"},

    # Consumer & Industrial
    "ITC": {"bg": "#00205B", "accent": "#D4AF37", "text": "#FFFFFF", "mark": "ITC"},
    "HINDUNILVR": {"bg": "#1F36C7", "accent": "#0B1A75", "text": "#FFFFFF", "mark": "HUL"},
    "TITAN": {"bg": "#003B70", "accent": "#C5A059", "text": "#FFFFFF", "mark": "TITAN"},
    "ASIANPAINT": {"bg": "#E82C2A", "accent": "#FFD100", "text": "#FFFFFF", "mark": "AP"},
    "TRENT": {"bg": "#18181B", "accent": "#C5A059", "text": "#FFFFFF", "mark": "TRENT"},
    "LT": {"bg": "#004B87", "accent": "#D4AF37", "text": "#FFFFFF", "mark": "L&T"},
    "ULTRACEMCO": {"bg": "#D97706", "accent": "#1F2937", "text": "#FFFFFF", "mark": "ULTRA"},
    "BHARTIARTL": {"bg": "#E40000", "accent": "#FF4D4D", "text": "#FFFFFF", "mark": "airtel"},

    # Defense & Aerospace
    "HAL": {"bg": "#004080", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "HAL"},
    "BEL": {"bg": "#002D62", "accent": "#059669", "text": "#FFFFFF", "mark": "BEL"},
    "BDL": {"bg": "#0A2540", "accent": "#DC2626", "text": "#FFFFFF", "mark": "BDL"},
    "MAZDOCK": {"bg": "#002244", "accent": "#0284C7", "text": "#FFFFFF", "mark": "MAZAGON"},
    "COCHINSHIP": {"bg": "#00558F", "accent": "#06B6D4", "text": "#FFFFFF", "mark": "COCHIN"},
    "GRSE": {"bg": "#0B2545", "accent": "#3B82F6", "text": "#FFFFFF", "mark": "GRSE"},

    # Railways
    "IRCTC": {"bg": "#8B0000", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "IRCTC"},
    "RVNL": {"bg": "#7A0000", "accent": "#D4AF37", "text": "#FFFFFF", "mark": "RVNL"},
    "RAILTEL": {"bg": "#1E3A8A", "accent": "#D4AF37", "text": "#FFFFFF", "mark": "RAILTEL"},
    "BHEL": {"bg": "#003865", "accent": "#0284C7", "text": "#FFFFFF", "mark": "BHEL"},

    # Exchanges & Depositories
    "BSE": {"bg": "#0B3C5D", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "BSE"},
    "NSE": {"bg": "#0B2545", "accent": "#FF6B00", "text": "#FFFFFF", "mark": "NSE"},
    "CDSL": {"bg": "#003366", "accent": "#2563EB", "text": "#FFFFFF", "mark": "CDSL"},
    "MCX": {"bg": "#0A3871", "accent": "#0284C7", "text": "#FFFFFF", "mark": "MCX"},
    "ANGELONE": {"bg": "#1E40AF", "accent": "#4338CA", "text": "#FFFFFF", "mark": "ANGEL"},
    "IEX": {"bg": "#0284C7", "accent": "#0369A1", "text": "#FFFFFF", "mark": "IEX"},

    # Consumer Tech & New Economy
    "SWIGGY": {"bg": "#FC8019", "accent": "#EA580C", "text": "#FFFFFF", "mark": "SWIGGY"},
    "NYKAA": {"bg": "#FC2779", "accent": "#E11D48", "text": "#FFFFFF", "mark": "NYKAA"},
    "POLICYBZR": {"bg": "#0F2D6B", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "POLICY"},
    "DELHIVERY": {"bg": "#E41D2D", "accent": "#1E293B", "text": "#FFFFFF", "mark": "DELH"},
    "OLAELEC": {"bg": "#0F172A", "accent": "#10B981", "text": "#10B981", "mark": "OLA"},

    # Pharma
    "SUNPHARMA": {"bg": "#F47920", "accent": "#C85A00", "text": "#FFFFFF", "mark": "SUN"},
    "CIPLA": {"bg": "#0284C7", "accent": "#0369A1", "text": "#FFFFFF", "mark": "CIPLA"},
    "DRREDDY": {"bg": "#4338CA", "accent": "#6366F1", "text": "#FFFFFF", "mark": "DR.REDDY"},
    "APOLLOHOSP": {"bg": "#047857", "accent": "#10B981", "text": "#FFFFFF", "mark": "APOLLO"},

    # Newly Listed Equities
    "HEROMOTORS": {"bg": "#EE2726", "accent": "#B91C1C", "text": "#FFFFFF", "mark": "HERO"},
    "SONA": {"bg": "#0F172A", "accent": "#3B82F6", "text": "#FFFFFF", "mark": "SONA"},
    "SSRETAIL": {"bg": "#7C3AED", "accent": "#6D28D9", "text": "#FFFFFF", "mark": "SSR"},
    "JSIPL": {"bg": "#0369A1", "accent": "#0284C7", "text": "#FFFFFF", "mark": "JINDAL"},
    "MANIKA": {"bg": "#059669", "accent": "#10B981", "text": "#FFFFFF", "mark": "MANIKA"},
    "VEEGALAND": {"bg": "#EA580C", "accent": "#F97316", "text": "#FFFFFF", "mark": "VEEGA"},
    "MPIMANIPAL": {"bg": "#1E40AF", "accent": "#3B82F6", "text": "#FFFFFF", "mark": "MANIPAL"},
    "KARAMTARA": {"bg": "#374151", "accent": "#4B5563", "text": "#FFFFFF", "mark": "KT"},
    "LCCPROJECT": {"bg": "#0D9488", "accent": "#14B8A6", "text": "#FFFFFF", "mark": "LCC"},
    "RENTOMOJO": {"bg": "#EF4444", "accent": "#DC2626", "text": "#FFFFFF", "mark": "RENTO"},
    "STEAMHOUSE": {"bg": "#D97706", "accent": "#F59E0B", "text": "#FFFFFF", "mark": "STEAM"},
    "ARCIL": {"bg": "#1E3A8A", "accent": "#2563EB", "text": "#FFFFFF", "mark": "ARCIL"},
    "GLASSWALL": {"bg": "#0891B2", "accent": "#06B6D4", "text": "#FFFFFF", "mark": "GLASS"},
    "KANOHAR": {"bg": "#4F46E5", "accent": "#6366F1", "text": "#FFFFFF", "mark": "KANOHAR"},
    "PRASOLCHEM": {"bg": "#047857", "accent": "#10B981", "text": "#FFFFFF", "mark": "PRASOL"},
    "PRANAV": {"bg": "#9333EA", "accent": "#A855F7", "text": "#FFFFFF", "mark": "PRANAV"},
    "DEEPA": {"bg": "#C026D3", "accent": "#D946EF", "text": "#FFFFFF", "mark": "DEEPA"},
    "PERNIASPOP": {"bg": "#BE185D", "accent": "#EC4899", "text": "#FFFFFF", "mark": "PERNIA"},
    "MOMSBELIEF": {"bg": "#E11D48", "accent": "#F43F5E", "text": "#FFFFFF", "mark": "MOM"},

    # Mutual Fund AMCs
    "122639": {"bg": "#0C2340", "accent": "#D4AF37", "text": "#FFFFFF", "mark": "PPFAS"},
    "120828": {"bg": "#1A1B4B", "accent": "#00A3E0", "text": "#FFFFFF", "mark": "quant"},
    "118834": {"bg": "#002870", "accent": "#F58220", "text": "#FFFFFF", "mark": "MIRAE"},
    "119803": {"bg": "#E60012", "accent": "#B91C1C", "text": "#FFFFFF", "mark": "NIPPON"},
    "125354": {"bg": "#97144D", "accent": "#BE123C", "text": "#FFFFFF", "mark": "AXIS"},
    "119551": {"bg": "#280071", "accent": "#00A3E0", "text": "#FFFFFF", "mark": "SBI"},
    "120503": {"bg": "#004C8F", "accent": "#ED1C24", "text": "#FFFFFF", "mark": "HDFC"},
    "120586": {"bg": "#9B1B1E", "accent": "#F37021", "text": "#FFFFFF", "mark": "ICICI"},
    "127042": {"bg": "#111111", "accent": "#FFD100", "text": "#FFD100", "mark": "MO"},
    "135781": {"bg": "#0F3E7A", "accent": "#2563EB", "text": "#FFFFFF", "mark": "TATA"},
    "120716": {"bg": "#E65100", "accent": "#0D47A1", "text": "#FFFFFF", "mark": "UTI"},
    "148712": {"bg": "#111827", "accent": "#00C269", "text": "#00C269", "mark": "navi"},
}

def render_etf_badge(symbol, size=256):
    """Generates authentic, stunning ETF badges (Gold, Silver, Index)."""
    sym = symbol.upper().replace(".NS", "").replace(".BO", "")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    corner = 52

    if "GOLD" in sym:
        # Rich Metallic Gold Emblem
        bg = hex_to_rgb("#B45309")
        accent = hex_to_rgb("#F59E0B")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        # Gold accent ribbon
        draw.pieslice([size - 140, margin, size - margin, margin + 130], start=270, end=360, fill=(accent[0], accent[1], accent[2], 120))
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(255, 215, 0, 160), width=4)
        
        # Gold Ingot text
        f_top = get_font(72)
        f_sub = get_font(38)
        draw.text((128, 90), "GOLD", fill="#FFFFFF", font=f_top, anchor="mm")
        draw.text((128, 168), "ETF 🪙", fill="#FEF08A", font=f_sub, anchor="mm")
        return img

    if "SILVER" in sym:
        # Sleek Metallic Silver Emblem
        bg = hex_to_rgb("#334155")
        accent = hex_to_rgb("#94A3B8")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        draw.pieslice([size - 140, margin, size - margin, margin + 130], start=270, end=360, fill=(accent[0], accent[1], accent[2], 120))
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(226, 232, 240, 180), width=4)
        
        f_top = get_font(60)
        f_sub = get_font(38)
        draw.text((128, 92), "SILVER", fill="#FFFFFF", font=f_top, anchor="mm")
        draw.text((128, 168), "ETF ⚪", fill="#E2E8F0", font=f_sub, anchor="mm")
        return img

    if "NIFTY" in sym or "SETFNIF50" in sym or "MID150" in sym:
        # Nifty Blue Index Emblem
        bg = hex_to_rgb("#002D62")
        accent = hex_to_rgb("#0284C7")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(56, 189, 248, 140), width=4)
        f_top = get_font(68)
        f_sub = get_font(36)
        draw.text((128, 92), "NIFTY", fill="#FFFFFF", font=f_top, anchor="mm")
        draw.text((128, 166), "50 ETF", fill="#38BDF8", font=f_sub, anchor="mm")
        return img

    if "BANK" in sym:
        # Banking Navy
        bg = hex_to_rgb("#0D47A1")
        accent = hex_to_rgb("#1E40AF")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(96, 165, 250, 140), width=4)
        f_top = get_font(68)
        f_sub = get_font(36)
        draw.text((128, 92), "BANK", fill="#FFFFFF", font=f_top, anchor="mm")
        draw.text((128, 166), "ETF", fill="#93C5FD", font=f_sub, anchor="mm")
        return img

    if "IT" in sym:
        # Tech Cyan
        bg = hex_to_rgb("#0077B6")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(125, 211, 252, 140), width=4)
        f_top = get_font(84)
        f_sub = get_font(36)
        draw.text((128, 90), "IT", fill="#FFFFFF", font=f_top, anchor="mm")
        draw.text((128, 166), "ETF", fill="#BAE6FD", font=f_sub, anchor="mm")
        return img

    if "CPSE" in sym:
        bg = hex_to_rgb("#C2410C")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(251, 146, 60, 140), width=4)
        f_top = get_font(64)
        f_sub = get_font(36)
        draw.text((128, 92), "CPSE", fill="#FFFFFF", font=f_top, anchor="mm")
        draw.text((128, 166), "PSU ETF", fill="#FED7AA", font=f_sub, anchor="mm")
        return img

    # Default ETF Badge
    bg = hex_to_rgb("#1E293B")
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
    f_top = get_font(52)
    f_sub = get_font(34)
    short = sym.replace("BEES", "").replace("ETF", "")[:6]
    draw.text((128, 92), short, fill="#FFFFFF", font=f_top, anchor="mm")
    draw.text((128, 166), "ETF", fill="#38BDF8", font=f_sub, anchor="mm")
    return img

def render_brand_logo(symbol, size=256):
    """Generates a bold, crisp, professional corporate brand logo."""
    sym = symbol.upper().replace(".NS", "").replace(".BO", "")
    
    # If ETF, use dedicated ETF renderer
    if "BEES" in sym or "ETF" in sym or sym in ("HDFCGOLD", "HDFCSILVER", "SETFGOLD"):
        return render_etf_badge(sym, size=size)

    # Special handling for National Stock Exchange of India (NSE)
    if sym in ("NSE", "NSE.BO"):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = 4
        corner = 52
        bg = hex_to_rgb("#0A192F")
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)
        # Iconic dynamic dual arcs of National Stock Exchange of India
        draw.arc([margin + 24, margin + 24, size - margin - 24, size - margin - 24], start=25, end=195, fill=hex_to_rgb("#FF5722"), width=16)
        draw.arc([margin + 42, margin + 42, size - margin - 42, size - margin - 42], start=205, end=355, fill=hex_to_rgb("#FF9800"), width=16)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(255, 255, 255, 45), width=3)
        f_nse = get_font(78)
        draw.text((128, 128), "NSE", fill="#FFFFFF", font=f_nse, anchor="mm")
        return img

    cfg = BRAND_CONFIGS.get(sym)
    if not cfg:
        # Deterministic rich palette
        h = sum(ord(c) for c in sym)
        palettes = [
            {"bg": "#0284C7", "accent": "#0369A1", "text": "#FFFFFF"},
            {"bg": "#7C3AED", "accent": "#6D28D9", "text": "#FFFFFF"},
            {"bg": "#059669", "accent": "#047857", "text": "#FFFFFF"},
            {"bg": "#D97706", "accent": "#B45309", "text": "#FFFFFF"},
            {"bg": "#DC2626", "accent": "#B91C1C", "text": "#FFFFFF"},
            {"bg": "#2563EB", "accent": "#1D4ED8", "text": "#FFFFFF"},
            {"bg": "#4F46E5", "accent": "#4338CA", "text": "#FFFFFF"},
            {"bg": "#0D9488", "accent": "#0F766E", "text": "#FFFFFF"}
        ]
        cfg = palettes[h % len(palettes)]
        cfg["mark"] = sym[:4] if len(sym) > 4 else sym

    bg = hex_to_rgb(cfg["bg"])
    accent = hex_to_rgb(cfg.get("accent", cfg["bg"]))
    text_color = hex_to_rgb(cfg.get("text", "#FFFFFF"))
    mark = cfg.get("mark", sym[:4])

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    corner = 52

    # 1. Main Brand Container
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, fill=bg)

    # 2. Modern Brand Accent Geometry
    draw.pieslice([size - 130, margin, size - margin, margin + 120], start=270, end=360, fill=(accent[0], accent[1], accent[2], 100))
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=corner, outline=(255, 255, 255, 35), width=3)

    # 3. SBI special keyhole circle accent
    if cfg.get("circle_accent"):
        draw.ellipse([size - 90, margin + 15, size - 35, margin + 70], fill=(accent[0], accent[1], accent[2], 220))
        draw.rectangle([size - 66, margin + 50, size - 59, margin + 75], fill=(bg[0], bg[1], bg[2], 255))

    # 4. Bold, Highly Legible Brand Mark Typography
    mark_len = len(mark)
    if mark_len <= 3:
        font_size = 96
    elif mark_len == 4:
        font_size = 80
    elif mark_len <= 6:
        font_size = 62
    else:
        font_size = 50

    font = get_font(font_size)
    draw.text((128, 128), mark, fill=text_color, font=font, anchor="mm")
    return img

def run():
    print("=== OVERWRITING WITH PRISTINE 256x256 HIGH-RES LOGOS ===", flush=True)
    import stock_master

    # 1. Base Stocks (72)
    base_stocks = [s["symbol"] for s in stock_master.STOCK_MASTER]
    print(f"Generating {len(base_stocks)} Base Equities...", flush=True)
    for s in base_stocks:
        clean = s.upper().replace(".NS", "").replace(".BO", "")
        img = render_brand_logo(clean)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{clean}.png"), "PNG", optimize=True)

    # 2. Newly Listed Stocks (19)
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "newly_listed_stocks.json"), encoding="utf-8") as f:
            dyn = json.load(f)
            dyn_stocks = [s["symbol"] for s in dyn]
            print(f"Generating {len(dyn_stocks)} Newly Listed Equities...", flush=True)
            for s in dyn_stocks:
                clean = s.upper().replace(".NS", "").replace(".BO", "")
                img = render_brand_logo(clean)
                img.save(os.path.join(STATIC_LOGOS_DIR, f"{clean}.png"), "PNG", optimize=True)
    except Exception as e:
        print(f"Newly listed error: {e}", flush=True)

    # 3. ETFs (15) - Dedicated Gold, Silver, and Index Badges
    etfs = [e["symbol"] for e in stock_master.ETF_MASTER]
    print(f"Generating {len(etfs)} ETFs with dedicated Gold/Silver/Index badges...", flush=True)
    for s in etfs:
        clean = s.upper().replace(".NS", "").replace(".BO", "")
        img = render_etf_badge(clean)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{clean}.png"), "PNG", optimize=True)

    # 4. Mutual Fund AMCs (12)
    mf_amcs = [
        ("122639", "PPFAS"),
        ("120828", "QUANT"),
        ("118834", "MIRAE"),
        ("119803", "NIPPON"),
        ("125354", "AXIS"),
        ("119551", "SBI"),
        ("120503", "HDFC"),
        ("120586", "ICICI"),
        ("127042", "MOTILAL"),
        ("135781", "TATA"),
        ("120716", "UTI"),
        ("148712", "NAVI"),
    ]
    print(f"Generating {len(mf_amcs)} Mutual Fund AMCs...", flush=True)
    for code, amc in mf_amcs:
        img = render_brand_logo(code)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{code}.png"), "PNG", optimize=True)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"MF_{amc}.png"), "PNG", optimize=True)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{amc}.png"), "PNG", optimize=True)

    # 5. IPO Companies (35)
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cached_ipos.json"), encoding="utf-8") as f:
            ipos = json.load(f)
            print(f"Generating {len(ipos)} IPO logos...", flush=True)
            for ipo in ipos:
                sym = ipo.get("symbol")
                if sym:
                    clean = sym.upper().replace(".NS", "").replace(".BO", "")
                    img = render_brand_logo(clean)
                    img.save(os.path.join(STATIC_LOGOS_DIR, f"{clean}.png"), "PNG", optimize=True)
    except Exception as e:
        print(f"IPO logos error: {e}", flush=True)

    # 6. Additional Popular Indian Equities & Exchange Aliases
    extra_popular = ["NSE", "NSE.BO", "SWIGGY", "NYKAA", "POLICYBZR", "DELHIVERY", "OLAELEC", "ANGELONE", "IEX", "MCX", "ZOMATO"]
    print(f"Generating {len(extra_popular)} Additional Popular Indian Equities...", flush=True)
    for s in extra_popular:
        img = render_brand_logo(s)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{s}.png"), "PNG", optimize=True)

    print("=== ALL LOGOS REGENERATED AT 256x256 PRISTINE QUALITY ===", flush=True)

if __name__ == "__main__":
    run()
