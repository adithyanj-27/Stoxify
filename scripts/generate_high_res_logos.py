"""
High-Resolution Logo Generator & Enhancer for Stoxify
Generates crisp 256x256 transparent PNG brand assets for:
- All 91 Indian Equities (72 Base Stocks + 19 Newly Listed)
- All 12 Mutual Fund AMCs (PPFAS, Quant, Mirae, Nippon, Axis, SBI, HDFC, ICICI, etc.)
- All 15 ETFs (NIFTYBEES, GOLDBEES, SILVERBEES, BANKBEES, etc.)
- All 35+ IPO Companies featured in the IPO section
"""
import os
import sys
import io
import json
import requests
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

# Curated Brand Color Palettes (Primary, Secondary, Text Color)
BRAND_PALETTES = {
    # Top Equities
    "RELIANCE": ("#002D62", "#004B87", "#FFFFFF"),
    "TCS": ("#0072C6", "#003A70", "#FFFFFF"),
    "HDFCBANK": ("#004C8F", "#ED1C24", "#FFFFFF"),
    "INFY": ("#007CC3", "#005A9C", "#FFFFFF"),
    "ICICIBANK": ("#9B1B1E", "#F37021", "#FFFFFF"),
    "SBIN": ("#280071", "#00A3E0", "#FFFFFF"),
    "BHARTIARTL": ("#E40000", "#FF4D4D", "#FFFFFF"),
    "ITC": ("#00205B", "#D4AF37", "#FFFFFF"),
    "LT": ("#004B87", "#D4AF37", "#FFFFFF"),
    "BAJFINANCE": ("#0066B2", "#004B87", "#FFFFFF"),
    "HINDUNILVR": ("#1F36C7", "#0B1A75", "#FFFFFF"),
    "MARUTI": ("#003B70", "#E31B23", "#FFFFFF"),
    "SUNPHARMA": ("#F47920", "#C85A00", "#FFFFFF"),
    "TITAN": ("#003B70", "#C5A059", "#FFFFFF"),
    "TATASTEEL": ("#0F3E7A", "#0072CE", "#FFFFFF"),
    "ADANIENT": ("#2A2A84", "#6B52AE", "#FFFFFF"),
    "ADANIPORTS": ("#1E2269", "#3B82F6", "#FFFFFF"),
    "ADANIGREEN": ("#10B981", "#059669", "#FFFFFF"),
    "ADANIPOWER": ("#D97706", "#B45309", "#FFFFFF"),
    "WIPRO": ("#004B87", "#8A2BE2", "#FFFFFF"),
    "POWERGRID": ("#00823B", "#005A2B", "#FFFFFF"),
    "NTPC": ("#003366", "#0284C7", "#FFFFFF"),
    "ONGC": ("#B22222", "#FFCC00", "#FFFFFF"),
    "COALINDIA": ("#222222", "#F59E0B", "#FFFFFF"),
    "M&M": ("#D32F2F", "#B71C1C", "#FFFFFF"),
    "TMCV": ("#0F3E7A", "#2563EB", "#FFFFFF"),
    "TMPV": ("#0F3E7A", "#3B82F6", "#FFFFFF"),
    "TATAMOTORS": ("#0F3E7A", "#2563EB", "#FFFFFF"),
    "AXISBANK": ("#97144D", "#ED1C24", "#FFFFFF"),
    "KOTAKBANK": ("#ED1C24", "#003366", "#FFFFFF"),
    "ULTRACEMCO": ("#F59E0B", "#1F2937", "#FFFFFF"),
    "ASIANPAINT": ("#E82C2A", "#FFD100", "#FFFFFF"),
    "BAJAJ-AUTO": ("#004B87", "#0284C7", "#FFFFFF"),
    "TRENT": ("#1A1A1A", "#C5A059", "#FFFFFF"),
    "JIOFIN": ("#0A2885", "#0284C7", "#FFFFFF"),
    "ETERNAL": ("#E23744", "#CB202D", "#FFFFFF"),
    "ZOMATO": ("#E23744", "#CB202D", "#FFFFFF"),
    "HAL": ("#004080", "#F59E0B", "#FFFFFF"),
    "BEL": ("#002D62", "#059669", "#FFFFFF"),
    "MAZDOCK": ("#002244", "#0284C7", "#FFFFFF"),
    "COCHINSHIP": ("#00558F", "#06B6D4", "#FFFFFF"),
    "GRSE": ("#0B2545", "#3B82F6", "#FFFFFF"),
    "BDL": ("#0A2540", "#DC2626", "#FFFFFF"),
    "IRFC": ("#8B0000", "#D4AF37", "#FFFFFF"),
    "IRCTC": ("#8B0000", "#F59E0B", "#FFFFFF"),
    "RVNL": ("#7A0000", "#D4AF37", "#FFFFFF"),
    "RAILTEL": ("#1E3A8A", "#D4AF37", "#FFFFFF"),
    "BHEL": ("#003865", "#0284C7", "#FFFFFF"),
    "TATAPOWER": ("#0F3E7A", "#06B6D4", "#FFFFFF"),
    "SUZLON": ("#689F38", "#33691E", "#FFFFFF"),
    "IREDA": ("#2E7D32", "#10B981", "#FFFFFF"),
    "NHPC": ("#0277BD", "#0369A1", "#FFFFFF"),
    "PFC": ("#0D47A1", "#F59E0B", "#FFFFFF"),
    "RECLTD": ("#0D47A1", "#10B981", "#FFFFFF"),
    "BANKBARODA": ("#F37021", "#EA580C", "#FFFFFF"),
    "PNB": ("#D32F2F", "#FBBF24", "#FFFFFF"),
    "CANBK": ("#0072CE", "#F59E0B", "#FFFFFF"),
    "IDFCFIRSTB": ("#9D2235", "#BE123C", "#FFFFFF"),
    "FEDERALBNK": ("#002E6E", "#F59E0B", "#FFFFFF"),
    "YESBANK": ("#003399", "#DC2626", "#FFFFFF"),
    "INDUSINDBK": ("#C01818", "#991B1B", "#FFFFFF"),
    "AUBANK": ("#4A154B", "#F97316", "#FFFFFF"),
    "BANDHANBNK": ("#005A9C", "#DC2626", "#FFFFFF"),
    "BSE": ("#0B3C5D", "#F59E0B", "#FFFFFF"),
    "CDSL": ("#003366", "#2563EB", "#FFFFFF"),
    "MCX": ("#0A3871", "#0284C7", "#FFFFFF"),
    "PAYTM": ("#002E6E", "#00BAF2", "#FFFFFF"),

    # Newly Listed Equities
    "HEROMOTORS": ("#EE2726", "#B91C1C", "#FFFFFF"),
    "SONA": ("#0F172A", "#3B82F6", "#FFFFFF"),
    "SSRETAIL": ("#7C3AED", "#6D28D9", "#FFFFFF"),
    "JSIPL": ("#0369A1", "#0284C7", "#FFFFFF"),
    "MANIKA": ("#059669", "#10B981", "#FFFFFF"),
    "VEEGALAND": ("#EA580C", "#F97316", "#FFFFFF"),
    "MPIMANIPAL": ("#1E40AF", "#3B82F6", "#FFFFFF"),
    "KARAMTARA": ("#374151", "#4B5563", "#FFFFFF"),
    "LCCPROJECT": ("#0D9488", "#14B8A6", "#FFFFFF"),
    "RENTOMOJO": ("#EF4444", "#DC2626", "#FFFFFF"),
    "STEAMHOUSE": ("#D97706", "#F59E0B", "#FFFFFF"),
    "ARCIL": ("#1E3A8A", "#2563EB", "#FFFFFF"),
    "GLASSWALL": ("#0891B2", "#06B6D4", "#FFFFFF"),
    "KANOHAR": ("#4F46E5", "#6366F1", "#FFFFFF"),
    "PRASOLCHEM": ("#047857", "#10B981", "#FFFFFF"),
    "PRANAV": ("#9333EA", "#A855F7", "#FFFFFF"),
    "DEEPA": ("#C026D3", "#D946EF", "#FFFFFF"),
    "PERNIASPOP": ("#BE185D", "#EC4899", "#FFFFFF"),
    "MOMSBELIEF": ("#E11D48", "#F43F5E", "#FFFFFF"),

    # Mutual Fund AMCs
    "122639": ("#0C2340", "#D4AF37", "#FFFFFF"), # PPFAS
    "120828": ("#1A1B4B", "#00A3E0", "#FFFFFF"), # Quant
    "118834": ("#002870", "#F58220", "#FFFFFF"), # Mirae Asset
    "119803": ("#E60012", "#B91C1C", "#FFFFFF"), # Nippon India
    "125354": ("#97144D", "#BE123C", "#FFFFFF"), # Axis MF
    "119551": ("#280071", "#00A3E0", "#FFFFFF"), # SBI MF
    "120503": ("#004C8F", "#ED1C24", "#FFFFFF"), # HDFC MF
    "120586": ("#9B1B1E", "#F37021", "#FFFFFF"), # ICICI Pru
    "127042": ("#FFD100", "#111111", "#111111"), # Motilal Oswal
    "135781": ("#0F3E7A", "#2563EB", "#FFFFFF"), # Tata MF
    "120716": ("#E65100", "#0D47A1", "#FFFFFF"), # UTI MF
    "148712": ("#111827", "#00C269", "#FFFFFF"), # Navi MF

    # ETFs
    "NIFTYBEES": ("#003366", "#0284C7", "#FFFFFF"),
    "BANKBEES": ("#0D47A1", "#1E40AF", "#FFFFFF"),
    "GOLDBEES": ("#B45309", "#F59E0B", "#FFFFFF"),
    "SILVERBEES": ("#334155", "#94A3B8", "#FFFFFF"),
    "ITBEES": ("#0077B6", "#00B4D8", "#FFFFFF"),
    "JUNIORBEES": ("#4338CA", "#6366F1", "#FFFFFF"),
    "CPSEETF": ("#C2410C", "#EA580C", "#FFFFFF"),
    "AUTOBEES": ("#15803D", "#22C55E", "#FFFFFF"),
    "PHARMABEES": ("#0E7490", "#06B6D4", "#FFFFFF"),
    "MON100": ("#4C1D95", "#7C3AED", "#FFFFFF"),
    "MAFANG": ("#18181B", "#3B82F6", "#FFFFFF"),
    "LIQUIDBEES": ("#0F766E", "#14B8A6", "#FFFFFF"),
    "SETFNIF50": ("#002D62", "#005A9C", "#FFFFFF"),
    "HDFCMFGETF": ("#004C8F", "#ED1C24", "#FFFFFF"),
    "ICICIB22": ("#9B1B1E", "#F37021", "#FFFFFF"),
}

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def render_crisp_vector_logo(symbol, display_name="", category="", size=256):
    """
    Renders a stunning 256x256 high-resolution brand logo emblem with smooth anti-aliased
    curves, gradient styling, brand mark typography, and subtle lighting.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    palette = BRAND_PALETTES.get(symbol.upper())
    if not palette:
        # Deterministic rich palette based on symbol hash
        h = sum(ord(c) for c in symbol)
        colors = [
            ("#0284C7", "#0369A1", "#FFFFFF"),
            ("#7C3AED", "#6D28D9", "#FFFFFF"),
            ("#059669", "#047857", "#FFFFFF"),
            ("#D97706", "#B45309", "#FFFFFF"),
            ("#DC2626", "#B91C1C", "#FFFFFF"),
            ("#2563EB", "#1D4ED8", "#FFFFFF"),
            ("#4F46E5", "#4338CA", "#FFFFFF"),
            ("#0D9488", "#0F766E", "#FFFFFF")
        ]
        palette = colors[h % len(colors)]

    bg_color = hex_to_rgb(palette[0])
    accent_color = hex_to_rgb(palette[1])
    text_color = hex_to_rgb(palette[2])

    # 1. Draw rounded container emblem (236x236 centered in 256x256)
    margin = 10
    corner_radius = 48
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        fill=bg_color
    )

    # 2. Modern subtle geometric accent curve in top right
    draw.pieslice(
        [size - 130, margin, size - margin, margin + 120],
        start=270,
        end=360,
        fill=(accent_color[0], accent_color[1], accent_color[2], 90)
    )

    # 3. Clean border
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        outline=(255, 255, 255, 30),
        width=3
    )

    # 4. Typography / Mark
    sym_clean = symbol.upper().replace(".NS", "").replace(".BO", "")
    
    # If ETF, show special symbol badge
    if "BEES" in sym_clean or "ETF" in sym_clean:
        font_main = get_font(52)
        font_sub = get_font(32)
        
        main_text = sym_clean[:5] if len(sym_clean) > 7 else sym_clean
        bbox_m = draw.textbbox((0, 0), main_text, font=font_main)
        w_m = bbox_m[2] - bbox_m[0]
        h_m = bbox_m[3] - bbox_m[1]
        draw.text(((size - w_m) // 2, (size // 2) - h_m - 8), main_text, fill=text_color, font=font_main)
        
        sub_text = "ETF"
        bbox_s = draw.textbbox((0, 0), sub_text, font=font_sub)
        w_s = bbox_s[2] - bbox_s[0]
        draw.text(((size - w_s) // 2, (size // 2) + 12), sub_text, fill=(accent_color[0], accent_color[1], accent_color[2], 240), font=font_sub)
        return img

    # Main symbol/initial rendering
    if len(sym_clean) <= 4:
        font = get_font(68)
        text = sym_clean
    elif len(sym_clean) <= 7:
        font = get_font(54)
        text = sym_clean
    else:
        # First 3-4 letters
        font = get_font(60)
        text = sym_clean[:4]

    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox - [0] if isinstance(bbox, list) else (bbox[2] - bbox[0])
    h = bbox[3] - bbox[1]

    # Center text
    x = (size - w) // 2
    y = (size - h) // 2 - 4
    draw.text((x, y), text, fill=text_color, font=font)

    return img

def try_download_fmp(symbol):
    clean = symbol.upper().replace(".NS", "").replace(".BO", "")
    urls = [
        f"https://images.financialmodelingprep.com/symbol/{clean}.NS.png",
        f"https://images.financialmodelingprep.com/symbol/{clean}.png"
    ]
    for u in urls:
        try:
            r = requests.get(u, timeout=2.5)
            if r.status_code == 200 and len(r.content) > 1200:
                im = Image.open(io.BytesIO(r.content))
                if im.size[0] >= 64 and im.size[1] >= 64:
                    return im
        except Exception:
            pass
    return None

def process_asset(symbol, force_render=False, display_name=""):
    clean = symbol.upper().replace(".NS", "").replace(".BO", "")
    target_path = os.path.join(STATIC_LOGOS_DIR, f"{clean}.png")

    # If we already have a high-res (>=120x120) image and not force_render, keep it
    if os.path.exists(target_path) and not force_render:
        try:
            existing = Image.open(target_path)
            if existing.size[0] >= 120 and existing.size[1] >= 120:
                return True
        except Exception:
            pass

    # Try downloading from FMP
    fmp_img = try_download_fmp(clean)
    if fmp_img:
        try:
            # Upscale/fit cleanly into 256x256 transparent square
            fmp_img = fmp_img.convert("RGBA")
            canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            fmp_img.thumbnail((240, 240), Image.Resampling.LANCZOS)
            cx = (256 - fmp_img.size[0]) // 2
            cy = (256 - fmp_img.size[1]) // 2
            canvas.paste(fmp_img, (cx, cy), fmp_img)
            canvas.save(target_path, "PNG", optimize=True)
            return True
        except Exception:
            pass

    # Fallback to pristine vector brand emblem (256x256)
    rendered = render_crisp_vector_logo(clean, display_name=display_name)
    rendered.save(target_path, "PNG", optimize=True)
    return True

import concurrent.futures

def run():
    print("=== STARTING HIGH-RES LOGO PIPELINE ===", flush=True)
    import stock_master
    
    # 1. Base Stocks (72)
    base_stocks = [s["symbol"] for s in stock_master.STOCK_MASTER]
    print(f"Processing {len(base_stocks)} base stocks in parallel...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(process_asset, base_stocks))

    # 2. Newly Listed Stocks (19)
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "newly_listed_stocks.json"), encoding="utf-8") as f:
            dyn = json.load(f)
            dyn_stocks = [s["symbol"] for s in dyn]
            print(f"Processing {len(dyn_stocks)} newly listed stocks in parallel...", flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
                list(pool.map(process_asset, dyn_stocks))
    except Exception as e:
        print(f"Newly listed stocks error: {e}", flush=True)

    # 3. ETFs (15)
    etfs = [e["symbol"] for e in stock_master.ETF_MASTER]
    print(f"Processing {len(etfs)} ETFs...", flush=True)
    for s in etfs:
        process_asset(s, force_render=True)

    # 4. Mutual Funds (12 AMCs)
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
    print(f"Processing {len(mf_amcs)} Mutual Fund AMCs...", flush=True)
    for code, amc in mf_amcs:
        img = render_crisp_vector_logo(code, display_name=amc)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{code}.png"), "PNG", optimize=True)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"MF_{amc}.png"), "PNG", optimize=True)
        img.save(os.path.join(STATIC_LOGOS_DIR, f"{amc}.png"), "PNG", optimize=True)

    # 5. IPO Companies (35)
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cached_ipos.json"), encoding="utf-8") as f:
            ipos = json.load(f)
            ipo_syms = [ipo.get("symbol") for ipo in ipos if ipo.get("symbol")]
            print(f"Processing {len(ipo_syms)} IPO companies in parallel...", flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
                list(pool.map(process_asset, ipo_syms))
    except Exception as e:
        print(f"IPO logos error: {e}", flush=True)

    print("=== HIGH-RES LOGO PIPELINE COMPLETE ===", flush=True)

if __name__ == "__main__":
    run()
