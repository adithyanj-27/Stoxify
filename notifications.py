import os
import json
import base64
import time
import logging
import threading
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

import database
import market_service
import market_hours

logger = logging.getLogger("stoxify.notifications")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    import tempfile
    DATA_DIR = tempfile.gettempdir()
else:
    DATA_DIR = os.path.join(BASE_DIR, "data")
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        pass

VAPID_FILE = os.path.join(DATA_DIR, "vapid_keys.json")

_PUSH_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="stoxify-push")

_vapid_keys_cache: Optional[Dict[str, str]] = None
_vapid_lock = threading.Lock()


def ensure_vapid_keys() -> Dict[str, str]:
    """Load or generate persistent VAPID keypair for Web Push notifications."""
    global _vapid_keys_cache
    with _vapid_lock:
        if _vapid_keys_cache:
            return _vapid_keys_cache

        # 1. Environment variables override (ideal for cloud serverless like Vercel)
        env_pub = os.environ.get("VAPID_PUBLIC_KEY")
        env_priv = os.environ.get("VAPID_PRIVATE_KEY")
        if env_pub and env_priv:
            _vapid_keys_cache = {
                "public_key": env_pub,
                "private_key": env_priv,
                "subject": os.environ.get("VAPID_SUBJECT", "mailto:support@stoxify.app")
            }
            return _vapid_keys_cache

        # 2. Cached file on disk
        if os.path.exists(VAPID_FILE):
            try:
                with open(VAPID_FILE, "r", encoding="utf-8") as f:
                    keys = json.load(f)
                    if keys.get("public_key") and keys.get("private_key"):
                        _vapid_keys_cache = keys
                        return keys
            except Exception as e:
                logger.warning(f"Failed to read existing VAPID file: {e}")

        # 3. Generate fresh VAPID keypair
        try:
            from py_vapid import Vapid
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

            v = Vapid()
            v.generate_keys()
            raw_pub = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
            pub_b64 = base64.urlsafe_b64encode(raw_pub).decode().rstrip("=")
            priv_pem = v.private_pem().decode()

            keys = {
                "public_key": pub_b64,
                "private_key": priv_pem,
                "subject": "mailto:support@stoxify.app"
            }
            try:
                with open(VAPID_FILE, "w", encoding="utf-8") as f:
                    json.dump(keys, f, indent=2)
            except Exception as fe:
                logger.warning(f"Could not persist VAPID file to disk (in-memory only): {fe}")

            _vapid_keys_cache = keys
            logger.info("Generated new persistent VAPID keypair for Web Push")
            return keys
        except Exception as e:
            logger.error(f"Failed to generate VAPID keys: {e}")
            fallback = {
                "public_key": "",
                "private_key": "",
                "subject": "mailto:support@stoxify.app"
            }
            _vapid_keys_cache = fallback
            return fallback


def get_vapid_public_key() -> str:
    """Return the URL-safe base64 uncompressed public key for frontend push subscription."""
    keys = ensure_vapid_keys()
    return keys.get("public_key", "")


def send_web_push(subscription: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    """Send an encrypted Web Push notification payload to a browser endpoint."""
    keys = ensure_vapid_keys()
    priv_key = keys.get("private_key")
    if not priv_key:
        return False

    try:
        from pywebpush import webpush, WebPushException

        sub_info = {
            "endpoint": subscription["endpoint"],
            "keys": {
                "p256dh": subscription["p256dh"],
                "auth": subscription["auth"]
            }
        }
        claims = {
            "sub": keys.get("subject", "mailto:support@stoxify.app")
        }
        data_str = json.dumps(payload)

        webpush(
            subscription_info=sub_info,
            data=data_str,
            vapid_private_key=priv_key,
            vapid_claims=claims,
            timeout=10
        )
        return True
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Web push dispatch failed for {subscription.get('endpoint', '')[:40]}...: {err_msg}")
        # Auto-remove invalid or expired subscriptions (HTTP 404 or 410 Gone)
        if "410" in err_msg or "404" in err_msg or "NotRegistered" in err_msg or "expired" in err_msg.lower():
            try:
                database.delete_push_subscription(subscription.get("endpoint", ""))
                logger.info(f"Removed dead push subscription endpoint: {subscription.get('endpoint', '')[:40]}")
            except Exception:
                pass
        return False


def dispatch_notification(
    user_id: str,
    title: str,
    message: str,
    type: str = "PRICE_ALERT",
    symbol: Optional[str] = None,
    asset_type: str = "STOCK",
    change_pct: float = 0.0,
    price: float = 0.0,
    action_url: Optional[str] = None
) -> int:
    """
    1. Persist notification to database (In-App Notification Center).
    2. Broadcast to all active PWA push endpoints for the user asynchronously.
    """
    notif_id = database.add_notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        symbol=symbol,
        asset_type=asset_type,
        change_pct=change_pct,
        price=price,
        action_url=action_url
    )

    # Async Web Push to user's registered devices
    def _deliver_push():
        try:
            subs = database.get_user_push_subscriptions(user_id)
            if not subs:
                return

            push_payload = {
                "id": notif_id,
                "title": title,
                "body": message,
                "icon": "/static/icon-192.png",
                "badge": "/static/icon-192.png",
                "data": {
                    "id": notif_id,
                    "symbol": symbol,
                    "asset_type": asset_type,
                    "change_pct": change_pct,
                    "price": price,
                    "url": action_url or (f"/stock/{symbol}" if symbol else "/"),
                    "type": type
                }
            }

            for sub in subs:
                send_web_push(sub, push_payload)
        except Exception as ex:
            logger.warning(f"Error in background push delivery: {ex}")

    _PUSH_EXECUTOR.submit(_deliver_push)
    return notif_id


def scan_and_dispatch_price_alerts() -> List[Dict[str, Any]]:
    """
    Scans all stocks/MFs present in user watchlists and holdings.
    Fires notifications when drastic price changes (default >= +/- 3.0%) occur,
    respecting cooldowns and user preferences.
    """
    monitored_map = database.get_monitored_symbols_by_user()
    if not monitored_map:
        return []

    dispatched = []

    for sym, info in monitored_map.items():
        asset_type = info.get("asset_type", "STOCK")
        name = info.get("name", sym)

        # Get latest quote
        try:
            if asset_type == "MUTUAL_FUND":
                q = market_service.get_mutual_fund_quote(sym)
            else:
                q = market_service.get_stock_quote(sym)
        except Exception:
            continue

        if not q:
            continue

        price = float(q.get("price") or 0.0)
        change_pct = float(q.get("change_pct") or 0.0)

        if price <= 0:
            continue

        # Check each user watching this symbol
        for user_entry in info.get("users", []):
            uid = user_entry["user_id"]
            threshold = float(user_entry.get("threshold_pct") or 3.0)
            source = user_entry.get("source", "WATCHLIST")

            if abs(change_pct) < threshold:
                continue

            # Check de-duplication & smart cooldown
            if not database.can_and_record_price_alert(uid, sym, change_pct, price, threshold_pct=threshold):
                continue

            # Craft notification title & body
            sign = "+" if change_pct > 0 else ""
            direction_emoji = "📈" if change_pct > 0 else "📉"
            direction_word = "surged" if change_pct > 0 else "dropped"
            action_desc = "Surge" if change_pct > 0 else "Drop"

            clean_sym = sym.replace(".NS", "").replace(".BO", "")
            title = f"{direction_emoji} Drastic {action_desc}: {clean_sym} is {sign}{change_pct:.2f}%"
            message = f"{name} {direction_word} to ₹{price:,.2f} ({source}). Tap to view chart & trade."
            action_url = f"/stock/{sym}"

            notif_id = dispatch_notification(
                user_id=uid,
                title=title,
                message=message,
                type="PRICE_ALERT",
                symbol=sym,
                asset_type=asset_type,
                change_pct=change_pct,
                price=price,
                action_url=action_url
            )

            dispatched.append({
                "id": notif_id,
                "user_id": uid,
                "symbol": sym,
                "change_pct": change_pct,
                "price": price,
                "title": title
            })
            logger.info(f"Dispatched drastic price alert for {sym} to {uid}: {sign}{change_pct:.2f}%")

    return dispatched


def _price_alert_worker():
    """Background worker daemon thread that runs periodically during market hours."""
    while True:
        try:
            status = market_hours.get_market_status()
            # Run if market is actively open or simulation mode is toggled on
            if status.get("is_open") or status.get("is_simulated"):
                scan_and_dispatch_price_alerts()
                time.sleep(30)
            else:
                # When market is closed, sleep for 2 minutes between checks
                time.sleep(120)
        except Exception as e:
            logger.warning(f"Error in price alert background worker: {e}")
            time.sleep(30)


_worker_started = False
_worker_lock = threading.Lock()


def start_price_alert_worker():
    """Start the background price alert monitoring thread once."""
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            t = threading.Thread(target=_price_alert_worker, daemon=True, name="stoxify-price-alerts")
            t.start()
            _worker_started = True
            logger.info("Started background price alert scanner worker thread")
