"""
Harvest Real Official Brand Logos for Indian Equities, Mutual Funds, ETFs, and IPOs
Downloads authentic corporate logos from Groww CDN, Wikimedia, and verified brand domains.
Formats every logo into a crisp 256x256 transparent RGBA PNG.
Strictly follows rule: Real logos for all available stocks/funds; synthetic vector badge ONLY as fallback when no real logo exists online.
"""
import os
import sys
import io
import json
import shutil
import requests
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stock_master

STATIC_LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "logos")
os.makedirs(STATIC_LOGOS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 1. Direct verified URLs for Real Corporate Logos
REAL_LOGO_SOURCES = {
    # Exchanges
    "NSE": "https://assets-netstorage.groww.in/stock-assets/logos/NSE.png",
    "NSE.BO": "https://assets-netstorage.groww.in/stock-assets/logos/NSE.png",
    "BSE": "https://assets-netstorage.groww.in/stock-assets/logos/BSE.png",
    "CDSL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK540615.png",
    "MCX": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK534091.png",
    "IEX": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK540750.png",
    "ANGELONE": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543235.png",

    # Major Equities
    "RELIANCE": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500325.png",
    "TCS": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532540.png",
    "HDFCBANK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500180.png",
    "INFY": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500209.png",
    "ICICIBANK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532174.png",
    "SBIN": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500112.png",
    "SBI": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500112.png",
    "BHARTIARTL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532454.png",
    "ITC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500875.png",
    "LT": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500510.png",
    "BAJFINANCE": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500034.png",
    "HINDUNILVR": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500696.png",
    "MARUTI": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532500.png",
    "SUNPHARMA": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK524715.png",
    "TITAN": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500114.png",
    "TATASTEEL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500470.png",
    "ADANIENT": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK512599.png",
    "ADANIPORTS": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532921.png",
    "WIPRO": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK507685.png",
    "POWERGRID": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532898.png",
    "NTPC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532555.png",
    "ONGC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500312.png",
    "COALINDIA": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK533278.png",
    "M&M": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500520.png",
    "TMCV": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK544569.png",
    "TMPV": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500570.png",
    "TATAMOTORS": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500570.png",
    "AXISBANK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532215.png",
    "AXIS": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532215.png",
    "KOTAKBANK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500247.png",
    "ULTRACEMCO": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532538.png",
    "ASIANPAINT": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500820.png",
    "BAJAJ-AUTO": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532977.png",
    "TRENT": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500251.png",
    "ETERNAL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543320.png",
    "ZOMATO": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543320.png",
    "SWIGGY": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK544285.png",
    "HAL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK541154.png",
    "BEL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500049.png",
    "MAZDOCK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543237.png",
    "COCHINSHIP": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK540678.png",
    "GRSE": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK542011.png",
    "BDL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK541143.png",
    "IRFC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543257.png",
    "IRCTC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK542830.png",
    "RVNL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK542649.png",
    "RAILTEL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543265.png",
    "BHEL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500103.png",
    "TATAPOWER": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500400.png",
    "SUZLON": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532667.png",
    "ADANIGREEN": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK541450.png",
    "ADANIPOWER": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK533096.png",
    "NHPC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK533098.png",
    "RECLTD": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532955.png",
    "PFC": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532810.png",
    "FEDERALBNK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500469.png",
    "BANKBARODA": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532134.png",
    "PNB": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532461.png",
    "CANBK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532483.png",
    "IDFCFIRSTB": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK539437.png",
    "YESBANK": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532648.png",
    "EICHERMOT": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK505200.png",
    "TVSMOTOR": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK532343.png",
    "ASHOKLEY": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500477.png",
    "TATAELXSI": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500408.png",
    "PAYTM": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543396.png",
    "VEDL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500295.png",
    "JSWSTEEL": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500228.png",
    "HINDALCO": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500440.png",
    "CIPLA": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500087.png",
    "DRREDDY": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500124.png",
    "APOLLOHOSP": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK508869.png",

    # Tech & E-Commerce
    "NYKAA": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543384.png",
    "POLICYBZR": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543390.png",
    "DELHIVERY": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543529.png",
    "HEROMOTORS": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK500182.png",

    # Wikimedia & Verified Official Marks
    "TATATECH": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5b/Tata_Technologies_logo.svg/500px-Tata_Technologies_logo.svg.png",
    "JIOFIN": "https://thumb.wikimedia.org/wikipedia/en/thumb/8/86/Jio_Financial_Services_Logo.svg/960px-Jio_Financial_Services_Logo.svg.png",
    "IREDA": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/65/IREDA_Logo.png/500px-IREDA_Logo.png",

    # Indices & ETFs
    "SILVERBEES": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543525.png",
    "HDFCSILVER": "https://assets-netstorage.groww.in/stock-assets/logos/GSTK543525.png",
    "NIFTYBEES": "https://assets-netstorage.groww.in/stock-assets/logos/GIDXNIFTY.png",
    "BANKBEES": "https://assets-netstorage.groww.in/stock-assets/logos/GIDXNIFTYBANK.png",
}

# 12 Real Mutual Fund AMCs
MF_AMCS = {
    "122639": ("ppfas", "https://assets-netstorage.groww.in/mf-assets/logos/ppfas_groww.png"),
    "120828": ("quant", "https://assets-netstorage.groww.in/mf-assets/logos/quant_groww.png"),
    "118834": ("mirae", "https://assets-netstorage.groww.in/mf-assets/logos/mirae_groww.png"),
    "119803": ("nippon", "https://assets-netstorage.groww.in/mf-assets/logos/nippon_groww.png"),
    "125354": ("axis", "https://assets-netstorage.groww.in/mf-assets/logos/axis_groww.png"),
    "119551": ("sbi", "https://assets-netstorage.groww.in/mf-assets/logos/sbi_groww.png"),
    "120503": ("hdfc", "https://assets-netstorage.groww.in/mf-assets/logos/hdfc_groww.png"),
    "120586": ("icici", "https://assets-netstorage.groww.in/mf-assets/logos/icici_groww.png"),
    "127042": ("motilal", "https://assets-netstorage.groww.in/mf-assets/logos/motilal_groww.png"),
    "135781": ("tata", "https://assets-netstorage.groww.in/mf-assets/logos/tata_groww.png"),
    "120716": ("uti", "https://assets-netstorage.groww.in/mf-assets/logos/uti_groww.png"),
    "148712": ("navi", "https://assets-netstorage.groww.in/mf-assets/logos/navi_groww.png"),
}

# Verified Brand Favicons (128px high-res icons for companies with online presence)
BRAND_FAVICONS = {
    "ACEVECTOR": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.snapdeal.com&size=128",
    "MONEYVIEW": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://moneyview.in&size=128",
    "VARMORA": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.varmora.com&size=128",
    "RENTOMOJO": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.rentomojo.com&size=128",
    "PERNIASPOP": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.perniaspopupshop.com&size=128",
    "VEEGALAND": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.veegaland.com&size=128",
    "ARCIL": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.arcil.co.in&size=128",
}

def save_image_from_bytes(data: bytes, target_path: str) -> bool:
    try:
        img = Image.open(io.BytesIO(data))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Trim transparent borders if any
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        
        # Center in square canvas with a pleasant margin
        max_dim = max(img.width, img.height)
        pad = max(int(max_dim * 0.08), 8)
        canvas_dim = max_dim + (pad * 2)
        canvas = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
        offset_x = (canvas_dim - img.width) // 2
        offset_y = (canvas_dim - img.height) // 2
        canvas.paste(img, (offset_x, offset_y), img)
        
        # Crisp 256x256
        res = canvas.resize((256, 256), Image.Resampling.LANCZOS)
        res.save(target_path, "PNG", optimize=True)
        return True
    except Exception as e:
        print(f"Error processing image {target_path}: {e}")
        return False

def download_and_save(url: str, target_name: str) -> bool:
    target_path = os.path.join(STATIC_LOGOS_DIR, f"{target_name}.png")
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200 and len(r.content) > 300:
            return save_image_from_bytes(r.content, target_path)
    except Exception as e:
        print(f"Download failed for {target_name} ({url}): {e}")
    return False

def copy_logo(src_name: str, dst_name: str):
    src = os.path.join(STATIC_LOGOS_DIR, f"{src_name}.png")
    dst = os.path.join(STATIC_LOGOS_DIR, f"{dst_name}.png")
    if os.path.exists(src):
        shutil.copyfile(src, dst)
        return True
    return False

def harvest():
    print("=== HARVESTING REAL OFFICIAL BRAND LOGOS ===", flush=True)

    # 1. Download AMCs
    print("1. Harvesting 12 Mutual Fund AMCs...", flush=True)
    for code, (amc, url) in MF_AMCS.items():
        ok = download_and_save(url, code)
        download_and_save(url, f"MF_{amc.upper()}")
        download_and_save(url, amc.upper())
        print(f"   [MF] {amc.upper()}: {'OK' if ok else 'FAIL'}", flush=True)

    # 2. Download Real Logo Sources
    print("\n2. Harvesting Equities, Exchanges & ETFs...", flush=True)
    for sym, url in REAL_LOGO_SOURCES.items():
        ok = download_and_save(url, sym)
        print(f"   [REAL] {sym}: {'OK' if ok else 'FAIL'}", flush=True)

    # 3. Download Brand Favicons
    print("\n3. Harvesting Verified Brand Icons...", flush=True)
    for sym, url in BRAND_FAVICONS.items():
        ok = download_and_save(url, sym)
        print(f"   [BRAND] {sym}: {'OK' if ok else 'FAIL'}", flush=True)

    # 4. Synchronize Aliases & ETF AMC Mappings
    print("\n4. Synchronizing Cross-References and ETF Issuer AMCs...", flush=True)
    # Exchanges
    copy_logo("NSE", "NSE.BO")
    copy_logo("NSE.BO", "NSE")
    
    # Tata Group
    copy_logo("TMPV", "TATAMOTORS")
    copy_logo("TMPV", "TATA")
    
    # Banking aliases
    copy_logo("SBIN", "SBI")
    copy_logo("AXISBANK", "AXIS")
    copy_logo("HDFCBANK", "HDFC")
    copy_logo("ICICIBANK", "ICICI")
    
    # Consumer & Metals
    copy_logo("ZOMATO", "ETERNAL")
    copy_logo("JSWSTEEL", "JSIPL")

    # ETFs
    # Gold & Silver
    copy_logo("NIPPON", "GOLDBEES")
    copy_logo("HDFC", "HDFCGOLD")
    copy_logo("SBI", "SETFGOLD")
    copy_logo("SILVERBEES", "HDFCSILVER")

    # Nippon ETFs
    for bees in ["JUNIORBEES", "MID150BEES", "ITBEES", "PHARMABEES", "AUTOBEES", "CPSEETF"]:
        copy_logo("NIPPON", bees)

    # Global ETFs
    copy_logo("MOTILAL", "MON100")
    copy_logo("MIRAE", "MAFANG")

    print("\n=== HARVEST COMPLETE ===", flush=True)

if __name__ == "__main__":
    harvest()
