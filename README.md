# BrokeAhh — Stock & Mutual Fund Broker Platform

> *"For traders too broke to lose real money on Zerodha."*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Node.js-24-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" alt="Node.js" />
  <img src="https://img.shields.io/badge/Vercel-Deploy-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel" />
  <img src="https://img.shields.io/badge/NSE%20%26%20BSE-Live%20Market-00D09C?style=for-the-badge" alt="NSE Market" />
</p>

BrokeAhh is a modern, broker-grade trading and investment platform inspired by Groww and Upstox, featuring **authentic Indian brokerage mechanics**, **₹10,00,000 available balance**, live Indian equities (NSE/BSE), official Mutual Fund NAVs (AMFI), strict IST market hours, and 5x intraday leverage.

---

## ⚡ Highlights & Broker Features

- **Starting Capital:** **₹10,00,000** available capital to learn and trade without risking real savings.
- **Strict Market Hours Enforcement:**
  - Active trading between **09:15 AM – 03:30 PM IST** (Monday–Friday).
  - Intraday (MIS) trades restricted outside market hours with standard broker alerts.
  - Off-market Delivery orders accepted as **AMO (After-Market Orders)**.
  - Built-in **24/7 Simulation Toggle** to practice anytime on weekends or evenings.
- **5x Intraday Leverage (20% Margin):**
  - Trade intraday with genuine 5x margin efficiency (e.g. ₹5,000 blocks a ₹25,000 position).
- **Dedicated Positions Tab:**
  - Track open MIS trades in real time with individual **Exit Position (Square Off)** and **Square Off All**.
- **Market & Limit Orders:**
  - Place Limit BUY/SELL orders. Margin is locked while open and refunded immediately upon cancellation.
- **Level-2 Market Depth:**
  - Live 5-tier Bid/Ask ladder with order quantities, counts, and Buyer vs Seller sentiment bar.
- **SEBI & Brokerage Fee Breakdown:**
  - Real-time transparent charge sheet calculating Brokerage, STT, Exchange fees, SEBI charges, Stamp Duty, and 18% GST.
- **Mobile First UX:**
  - Bottom app navigation bar on mobile browsers.
  - Slide-up bottom sheet trading drawer with quick quantity chips (+1, +5, +10, +25, +50).
- **Persistence:** Local SQLite database (`brokeahh.db`) ensuring all trades, holdings, and watchlists are preserved.

---

## 🚀 One-Click Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/adithyanj-27/BrokeAhh)

1. Push this repository to your GitHub account: `https://github.com/adithyanj-27/BrokeAhh`.
2. Link your GitHub repository in your [Vercel Dashboard](https://vercel.com).
3. Vercel deploys your site serverless with custom domain/subdomain like `https://brokeahh.vercel.app`.

---

## 💻 Local Development Setup

### Quick Start:
```bash
# Clone the repository
git clone https://github.com/adithyanj-27/BrokeAhh.git
cd BrokeAhh

# Install dependencies
pip install -r requirements.txt

# Run application (automatically opens http://127.0.0.1:8000)
py run.py
```

### Windows Double-Click Launcher:
Double-click `start_brokeahh.bat` to launch the platform.

### Running Automated Verification Tests:
```bash
py test_app.py
```

---

## 📂 Project Structure

```
BrokeAhh/
├── api/
│   └── index.py            # Vercel serverless entrypoint
├── static/
│   ├── index.html          # Responsive single-page web app
│   ├── style.css           # Modern brokerage design system
│   └── app.js              # Client-side reactivity, Chart.js, orders
├── market_hours.py         # IST calendar, sessions, and simulation toggle
├── database.py             # SQLite schema (brokeahh.db), 5x leverage, square-off engine
├── market_service.py       # High-performance market data & 3-tier search
├── stock_master.py         # Curated 150+ stocks, aliases, & AMFI funds
├── main.py                 # FastAPI backend REST API
├── run.py                  # One-click launcher
├── start_brokeahh.bat      # Windows launcher
├── package.json            # npm scripts
├── requirements.txt        # Python backend dependencies
├── vercel.json             # Vercel serverless routing configuration
└── README.md
```

---

## 📄 License
MIT License. Built for educational and investment practice purposes.

