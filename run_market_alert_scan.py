"""
Standalone Market Alert Scanner for Cloud / GitHub Actions / Cron runners.
Connects to Supabase, checks IST market hours, scans user watchlists/holdings,
and dispatches Web Push notifications directly to FCM.
"""
import sys
import logging
import market_hours
import notifications

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("market_scanner")


def main():
    status = market_hours.get_market_status()
    is_open = status.get("is_open")
    is_sim = status.get("is_simulated")
    logger.info(f"Market Status: {status.get('session')} (Open: {is_open}, Simulated: {is_sim})")

    force = "--force" in sys.argv
    if not is_open and not is_sim and not force:
        logger.info("Market is closed. Skipping price alert scan.")
        return

    logger.info("Starting price alert scan across monitored user assets...")
    dispatched = notifications.scan_and_dispatch_price_alerts()
    logger.info(f"Scan complete. Dispatched {len(dispatched)} alerts.")
    for a in dispatched:
        logger.info(f" -> Dispatched alert: {a.get('title')} to user {a.get('user_id')}")


if __name__ == "__main__":
    main()
