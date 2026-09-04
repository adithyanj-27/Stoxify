# GrowwFAHH — Stock & Mutual Fund Trading Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Node.js-24-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" alt="Node.js" />
  <img src="https://img.shields.io/badge/Vercel-Deploy-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel" />
  <img src="https://img.shields.io/badge/NSE%20%26%20BSE-Live%20Market-00D09C?style=for-the-badge" alt="NSE Market" />
</p>

GrowwFAHH is a modern, responsive trading and investment web application inspired by Groww, featuring an **authentic broker experience**, **₹10,00,000 available balance**, live Indian stock prices (NSE/BSE), and official Mutual Fund NAVs (AMFI).

---

## ⚡ Highlights & Key Features

- **Starting Capital:** **₹10,00,000** available balance to invest.
- **Zero Simulation Terminology:** Designed with authentic brokerage terms (*Available Balance*, *Invested*, *Current Value*, *Total Returns*, *Holdings*, *Orders*, *Watchlist*, *Market Order*, *Delivery / Intraday*).
- **Live Market Data:**
  - **NSE & BSE Stocks:** Real-time Last Traded Price (LTP), 52-week High/Low, Day High/Low, P/E ratios, and Market Cap via `yfinance`.
  - **Indian Mutual Funds:** Official NAVs, fund house info, and 1-year returns via the open AMFI API.
- **Sticky Indices Strip:** Real-time tickers for **NIFTY 50**, **SENSEX**, **BANK NIFTY**, and **NIFTY IT**.
- **3-Tier Deep Search:**
  - Search 150+ curated Indian equities across 12 sectors with colloquial aliases (*"Zomato"*, *"Tata Motors"*, *"SBI"*, *"L&T"*, *"Suzlon"*, *"Mazdock"*, *"IREDA"*, *"HAL"*).
  - Dynamic fallback to live NSE/BSE stock search for all 2,000+ Indian companies.
  - Live search across all 10,000+ AMFI mutual fund schemes.
- **Interactive Financial Charts:** Timeframe support (`1D`, `1W`, `1M`, `1Y`, `5Y`, `ALL`) with responsive gradient charts powered by Chart.js.
- **Order Execution Engine:**
  - Instant BUY and SELL orders with Delivery and Intraday options.
  - Live margin calculation and portfolio protection against over-budget orders.
  - Weighted average buy price computation across multiple buys.
  - Realized profit and loss (P&L) tracking on sells.
- **Dark / Light Mode:** Groww-signature deep charcoal dark theme and clean light theme.
- **Sub-10ms Instant Response:** Pre-seeded in-memory caching with asynchronous background refresh.
- **Persistence:** Local SQLite database (`growwfahh.db`) ensuring data is never lost.

---

## 🚀 One-Click Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/adithyanj-27/GrowwFAHH)

1. Fork or push this repository to GitHub.
2. Link your GitHub repository in your [Vercel Dashboard](https://vercel.com).
3. Vercel automatically detects `vercel.json` and `api/index.py` and deploys your serverless website instantly!

---

## 💻 Local Development Setup

### Prerequisites
- **Python 3.10+** (or Python 3.13)
- **Node.js** (optional, for `npm run dev`)

### Quick Start with npm:
```bash
# Clone the repository
git clone https://github.com/adithyanj-27/GrowwFAHH.git
cd GrowwFAHH

# Run development server (automatically launches browser at http://127.0.0.1:8000)
npm run dev
```

### Or Start with Python directly:
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
py run.py
```

### Running Automated Verification Tests:
```bash
npm test
# OR
py test_app.py
```

---

## 📂 Project Structure

```
GrowwFAHH/
├── api/
│   └── index.py            # Vercel serverless entrypoint
├── static/
│   ├── index.html          # Single-page web dashboard
│   ├── style.css           # Groww design system (Emerald Teal + Sunset Orange)
│   └── app.js              # Client-side reactivity, Chart.js, orders
├── database.py             # SQLite schema, trade engine, Vercel /tmp fallback
├── market_service.py       # High-performance market data & 3-tier search
├── stock_master.py         # Curated 150+ stocks, aliases, & AMFI funds
├── main.py                 # FastAPI backend REST API
├── run.py                  # One-click launcher
├── start_growwfahh.bat     # Windows double-click runner
├── package.json            # npm run dev / npm test scripts
├── requirements.txt        # Python backend dependencies
├── vercel.json             # Vercel serverless routing configuration
└── README.md
```

---

## 📄 License
MIT License. Built for educational and investment practice purposes.
