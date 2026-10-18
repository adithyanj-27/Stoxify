import os
import sys
import tempfile

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

os.environ["VERCEL"] = "1"

def test_notifications():
    print("==================================================")
    print(" Running Stoxify Notifications Automated Test Suite")
    print("==================================================")

    import database
    import notifications
    import main

    database.DB_PATH = os.path.join(tempfile.gettempdir(), "stoxify_test_notifications.db")
    if os.path.exists(database.DB_PATH):
        try:
            os.remove(database.DB_PATH)
        except Exception:
            pass

    database.SUPABASE_URL = ""
    database.SUPABASE_KEY = ""
    database._db_initialized = False
    database.init_db()

    # 1. Test Notification Creation & Persistence
    print("\n[1/5] Testing In-App Notification Store...")
    notif_id = database.add_notification(
        user_id="test_user",
        title="📈 Drastic Rise: RELIANCE is +4.20%",
        message="Reliance Industries Ltd surged to ₹3,020.00. Tap to view chart.",
        type="PRICE_ALERT",
        symbol="RELIANCE.NS",
        asset_type="STOCK",
        change_pct=4.20,
        price=3020.0,
        action_url="/stock/RELIANCE.NS"
    )
    assert notif_id > 0, f"Expected valid notification ID, got {notif_id}"

    res = database.get_notifications("test_user")
    assert res["total"] == 1, f"Expected total 1, got {res['total']}"
    assert res["unread_count"] == 1, f"Expected unread 1, got {res['unread_count']}"
    item = res["notifications"][0]
    assert item["symbol"] == "RELIANCE.NS"
    assert item["change_pct"] == 4.20
    assert item["is_read"] == 0
    print(" ✓ Created and retrieved in-app price alert notification")

    # Mark as read
    database.mark_notification_read("test_user", notification_id=notif_id)
    res_after_read = database.get_notifications("test_user")
    assert res_after_read["unread_count"] == 0, "Expected unread_count 0 after marking read"
    print(" ✓ Mark as read verified")

    # Clear notifications
    database.delete_notification("test_user", delete_all=True)
    res_after_clear = database.get_notifications("test_user")
    assert res_after_clear["total"] == 0, "Expected 0 notifications after clear"
    print(" ✓ Clear all notifications verified")

    # 2. Test Notification Preferences
    print("\n[2/5] Testing User Notification Settings...")
    default_settings = database.get_notification_settings("test_user")
    assert default_settings["price_alerts_enabled"] is True
    assert default_settings["threshold_pct"] == 3.0
    print(" ✓ Default notification preferences: Enabled @ ±3.0% threshold")

    updated = database.update_notification_settings("test_user", threshold_pct=5.0)
    assert updated["threshold_pct"] == 5.0
    saved = database.get_notification_settings("test_user")
    assert saved["threshold_pct"] == 5.0
    print(" ✓ Updated notification threshold to ±5.0%")

    # 3. Test Web Push Subscription & VAPID Keypair
    print("\n[3/5] Testing VAPID Keys & Push Subscription Store...")
    keys = notifications.ensure_vapid_keys()
    assert keys.get("public_key"), "Expected public key generated"
    assert keys.get("private_key"), "Expected private key generated"
    pub_key = notifications.get_vapid_public_key()
    assert len(pub_key) > 40, f"Public key unexpectedly short: {pub_key}"
    print(f" ✓ Persistent VAPID Keypair active (Public Key: {pub_key[:24]}...)")

    mock_endpoint = "https://fcm.googleapis.com/fcm/send/test_endpoint_token_123"
    database.save_push_subscription("test_user", mock_endpoint, "test_p256dh_key", "test_auth_secret")
    subs = database.get_user_push_subscriptions("test_user")
    assert len(subs) == 1
    assert subs[0]["endpoint"] == mock_endpoint
    print(" ✓ Push subscription saved and linked to user account")

    database.delete_push_subscription(mock_endpoint)
    subs_after = database.get_user_push_subscriptions("test_user")
    assert len(subs_after) == 0
    print(" ✓ Push unsubscribe verified")

    # 4. Test Smart Alert De-duplication & Cooldown Logic
    print("\n[4/5] Testing Drastic Price Change Trigger & Smart Cooldown...")
    # 1. Below threshold (1.5% vs 3.0%) -> Should NOT alert
    below = database.can_and_record_price_alert("u1", "TCS.NS", current_pct=1.5, current_price=3900.0, threshold_pct=3.0)
    assert below is False, "Expected False for move below threshold"
    print(" ✓ Sub-threshold change (+1.5% < 3.0%) correctly ignored")

    # 2. Drastic change (+3.8%) -> Should alert
    first_surge = database.can_and_record_price_alert("u1", "TCS.NS", current_pct=3.8, current_price=4050.0, threshold_pct=3.0)
    assert first_surge is True, "Expected True for first drastic change"
    print(" ✓ Drastic price surge (+3.8%) triggered notification")

    # 3. Small jitter immediately after (+3.9%) -> Cooldown should suppress spam
    jitter = database.can_and_record_price_alert("u1", "TCS.NS", current_pct=3.9, current_price=4055.0, threshold_pct=3.0)
    assert jitter is False, "Expected False due to cooldown suppression"
    print(" ✓ Jitter change (+3.9% vs +3.8%) suppressed by smart cooldown")

    # 4. Significant delta expansion (+6.2%, >= 2% jump) -> Should alert again!
    expansion = database.can_and_record_price_alert("u1", "TCS.NS", current_pct=6.2, current_price=4150.0, threshold_pct=3.0)
    assert expansion is True, "Expected True for significant delta expansion"
    print(" ✓ Further breakout (+6.2% vs +3.8%, delta >= 2%) passed cooldown")

    # 5. Trend reversal (-3.5%) -> Should alert on direction flip
    reversal = database.can_and_record_price_alert("u1", "TCS.NS", current_pct=-3.5, current_price=3800.0, threshold_pct=3.0)
    assert reversal is True, "Expected True for trend reversal flip"
    print(" ✓ Sudden reversal (-3.5%) triggered drop alert")

    # 5. Test API Endpoints
    print("\n[5/5] Testing FastAPI Notification & Push Endpoints...")
    pub_resp = main.api_get_push_public_key()
    assert "public_key" in pub_resp
    assert len(pub_resp["public_key"]) > 0

    test_resp = main.api_push_test(main.PushTestRequest(symbol="RELIANCE.NS", change_pct=4.5), request=None)
    assert test_resp["success"] is True
    assert "RELIANCE" in test_resp["title"]
    print(" ✓ POST /api/push/test successfully dispatched simulated price surge")

    notifs_api = main.api_get_notifications(request=None)
    assert notifs_api["total"] >= 1
    assert notifs_api["unread_count"] >= 1
    print(f" ✓ GET /api/notifications returned {notifs_api['total']} items ({notifs_api['unread_count']} unread)")

    print("\n==================================================")
    print(" ALL NOTIFICATION & WEB PUSH TESTS PASSED 100%! ")
    print("==================================================")

if __name__ == "__main__":
    test_notifications()
