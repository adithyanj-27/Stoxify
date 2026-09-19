import os
import sys
import time
import webbrowser
import threading
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\nLaunching Stoxify in your browser: {url}")
    webbrowser.open(url)

def main():
    print("""
=========================================================
  STOXIFY - STOCK & MUTUAL FUND BROKER PLATFORM
  "Modern Stock & Mutual Fund Broker Platform"
=========================================================
  Status: Online & Ready
  Starting Account Balance: Rs. 10,00,000
  Local URL: http://127.0.0.1:8000
=========================================================
    """)

    # Launch browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Uvicorn server
    try:
        import uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
    except ImportError:
        print("Required dependencies not found. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        import uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
