# Stoxify — Product & Flow Review vs Groww

**Scope:** features, working flows and information architecture — *not* visual theming.
**Reviewed:** `public/index.html` (3,244 lines), `public/app.js` (7,219 lines), `main.py` (1,064 lines), `database.py` (3,189 lines).
**Compared against:** Groww's live product, help centre and pricing pages (2025–2026). Sources at the end.
**Date:** 12 Sep 2026

Every claim about Stoxify below was read out of the source. Every claim about Groww carries a source URL. Where I could not verify a Groww behaviour, I say so rather than guess.

---

## 0. TL;DR — the ten changes that matter

| # | Change | Why it matters | Effort |
|---|---|---|---|
| 1 | **Fix the four broken flows** (GTT create/list/cancel, Active SIPs tab, tax trades table, IPO bid list + withdraw) | These are client↔server field-name mismatches. Features the user can see are silently failing. | 1–2 days |
| 2 | **Reorder the nav to Groww's mental model**: Home · Stocks · Mutual Funds · Orders · Profile | Today it is Explore · Holdings · Positions · Orders · Watchlist — a *trader's* IA, not an *investor's* IA. | 1 day |
| 3 | **Add an order confirmation + status lifecycle** (Open → Executed / Rejected / Cancelled, with retry) | Groww never places an order straight from the form. Stoxify has no confirmation step and no `REJECTED` state surfaced. | 2–3 days |
| 4 | **Add SL-M and AMO as real user choices**, plus order modification | Groww supports Market/Limit/SL/SL-M/GTT/AMO and lets you modify price & qty. Stoxify has Market/Limit/SL only, cancel-only. | 3–4 days |
| 5 | **Build the SIP execution engine** (auto-debit + units allotted) | Today a SIP is a stored row. It never debits, never buys units — so "My Active SIPs" can never be meaningful. | 3–4 days |
| 6 | **Add price alerts + a notification centre** | Groww's most-praised convenience feature (±5% auto alerts, DMA/circuit/52W). Stoxify has zero alerts. | 3–5 days |
| 7 | **Make intraday auto square-off real** | The UI promises "Auto Square-off 03:20 PM IST" but no scheduler exists. That is a false claim in the product. | 1–2 days |
| 8 | **Add a Reports section**: P&L report, tax P&L, transaction history, ledger, contract notes | Groww ships all of these; users downloaded 6M+ reports in one tax season. Stoxify has one tax card and no export. | 4–6 days |
| 9 | **Add a Stocks/MF discovery layer**: screener, collections, more-bought/most-held, index pages, ETF pages | Stoxify's whole discovery surface is one filter-pill row and a "Most Bought" carousel that is literally the first 8 rows of the master list. | 5–8 days |
| 10 | **Add NRML as a product type and stop hard-forcing options to INTRADAY** | `app.js:6498` forces every option trade to `INTRADAY`. Groww runs F&O on NRML with expiry handling. | 2 days |

---

## 1. Method & evidence

- **Screen/flow inventory** taken from `index.html` element ids, `app.js` render functions and the `main.py` route table (94 routes).
- **Cartesian check** of every client payload against its Pydantic model in `main.py`, and every rendered field against the real SQLite column set in `database.py`. This is what surfaced the broken flows in §4.
- **Groww reference** built from groww.in product pages, the Groww help centre, Groww's own `/updates` product-changelog posts, the Google Play and App Store listings, and groww.in/pricing.
- **Not verified:** Groww's exact mobile bottom-nav tab order (no primary source found), and Groww's `Withdraw` timing thresholds — Groww's own help pages contradict each other on this (see §9).

---

## 2. Where Stoxify stands today

### 2.1 Navigation & IA (as built)

```
Top nav (desktop):   Explore · Holdings · Positions · Orders · Watchlist
Explore sub-nav:     Stocks | F&O (Futures & Options) | Mutual Funds | IPOs
Holdings sub-nav:    Holdings | Analytics & Tax Report | Active SIPs
Orders sub-nav:      status filter only
Positions:           table + "Square Off All"
Profile:             reachable only via the avatar dropdown
Mobile:              bottom nav (5 tabs mirroring the desktop set)
```

### 2.2 What genuinely works end-to-end

Login · account creation (with ₹10,00,000 seeded to the *bank*, wallet starting at ₹0) · add money / withdraw (simulated UPI + 4-digit PIN) · BUY delivery (CNC) · BUY intraday (MIS, 20% margin) · SELL a holding · exit one position · square off all · limit order placement and cancel · option-chain BUY · watchlist star · sector allocation · capital-gains tax card · stock detail page with chart, L2 depth, fundamentals, Financials/Shareholding/Peers/News tabs · SIP calculator (pure client maths).

### 2.3 What is inert, broken or unreachable

| Area | Problem |
|---|---|
| GTT | Create → `422`; list renders `undefined`; cancel calls `/api/order/gtt/undefined` |
| SIP | "My Active SIPs" throws a `TypeError` on render; Stop SIP unreachable |
| Tax | `#taxTradesTableBody` is never written by any JS |
| IPO | `GET /api/ipo/applications` and `DELETE /api/ipo/bid/{id}` exist with **no UI at all** — you can apply but never see or withdraw a bid |
| Orders | No `REJECTED`/`FAILED` surfacing, no modify, no export |
| Positions | "Auto Square-off 03:20 PM" is copy only — no scheduler exists |
| Funds modal | Legacy `#tradeModalOverlay` (chart + depth + order form) is fully built but its opener `legacyOpenAssetModal` has **no caller** — ~400 lines of dead UI |
| Charges | Server endpoint `GET /api/trade/charges` is never called; the client re-implements the charge sheet in `calculateEstimatedCharges` (`app.js:1959`) |

### 2.4 The structural problem

Stoxify is built as a **trading terminal** (Explore → Positions → Orders, leverage front-and-centre, L2 depth on the default tab). Groww is built as an **investing app that also trades** (Home → Stocks → Mutual Funds → Orders, SIP and delivery first, leverage buried behind a product tab).

Matching Groww's *flows* is therefore mostly an **IA and sequencing job**, not a feature-count job. Most of the raw capability is already in `main.py` — it is either mis-wired or not surfaced.

---

## 3. Feature parity map

Legend: ✅ parity · 🟡 partial · ❌ missing

| Capability | Groww | Stoxify | Gap to close |
|---|---|---|---|
| **Order types** | Market, Limit, SL, SL-M, GTT, AMO ([src](https://groww.in/blog/types-of-stock-market-orders)) | Market, Limit, SL, GTT(⚠️broken) | Add SL-M + AMO toggle |
| **Product types** | Delivery/CNC, Intraday/MIS, MTF ([src](https://groww.in/stocks/mtf)) | CNC, MIS | Add MTF; add NRML for F&O |
| **Order modification** | Yes — price & qty ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-or-cancel-my-order--22)) | ❌ cancel only | Add `PUT /api/order/{id}` |
| **OCO / SL-Target** | Yes, incl. intraday SL/TGT ([src](https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday)) | ❌ | Add target+SL legs |
| **Bracket orders (F&O)** | Yes, Jan 2026 ([src](https://groww.in/updates/bracket-orders-on-groww)) | ❌ | Optional |
| **Basket orders** | Yes, F&O cross-expiry | ❌ | Optional |
| **Futures** | Yes ([src](https://groww.in/futures-and-options)) | ❌ options only | Add futures contracts |
| **GTT validity** | Stocks 1 year; F&O until expiry ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39)) | No trigger engine at all | Build the evaluator |
| **Options Greeks / strategy builder** | Option chain + Greeks; basket for strategies | Option chain, PCR, spot only | Add Greeks |
| **Intraday auto square-off** | 3:20 PM, ₹50/position ([src](https://groww.in/pricing)) | Copy claims it; no scheduler | Build the scheduler |
| **SIP** | Create, edit amount/date, skip instalment, step-up, pause ([src](https://groww.in/blog/how-to-edit-sip-on-groww)) | Create only (⚠️list/cancel broken) | Engine + edit/skip/step-up |
| **SIP execution** | Auto-debit + units allotted from NAV | ❌ stored row only | Build the job |
| **MF redemption** | Redeem, 3–4 working days ([src](https://groww.in/help/mutual-funds/order/how-to-withdraw-redeem-4)) | ❌ no redeem | Add redeem |
| **STP / SWP** | Web only ([src](https://groww.in/blog/how-to-start-a-stp-and-swp-on-grow)) | ❌ | Optional |
| **IPO apply** | UPI mandate / ASBA ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/how-to-invest-in-ipo)) | ✅ simulates it | — |
| **IPO tracking + withdraw** | Status on IPO page; Allotment tab with registrar links ([src](https://groww.in/ipo/allotment)) | ❌ no UI | Build "My Applications" |
| **IPO allotment processing** | Allotted/not-allotted | ❌ bids stay `APPLIED` forever | Build the job |
| **Holdings** | Total value / invested / returns, per-row detail | ✅ same metrics | — |
| **Positions** | Live P&L, exit individual / all | ✅ | — |
| **Orders** | Statuses Open/Executed/Rejected/Failed/Cancelled + **1-click retry** ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68)) | Status filter only | Add states + retry |
| **P&L dashboard** | Day-level chart, Net/Realised, charges, month/quarter/FY compare ([src](https://groww.in/updates/fno-pnl-dashboard-groww)) | ❌ | Build reports |
| **Tax P&L / capital gains** | In-app + download | 🟡 card only, no trades table, no export | Finish + export |
| **Transaction history / ledger** | Yes | ❌ | Build |
| **Contract notes** | Yes | ❌ (menu item just navigates to /orders) | Build |
| **Price alerts** | ±5% auto + DMA/circuit/52W; on/off management ([src](https://groww.in/updates/notification-management-on-groww)) | ❌ | Build |
| **Notifications inbox** | Yes | ❌ transient toasts only | Build |
| **Watchlists** | Up to **10** (announced on Groww's product-changelog, [src](https://groww.in/updates)) | 1 flat list | Add multiple lists |
| **Collections / curated lists** | Yes | ❌ | Add |
| **Screener** | Yes (ETF + stocks) | ❌ | Add |
| **Index pages** | Yes | 🟡 indices bar + index asset page | Finish |
| **ETF pages** | Yes ([src](https://groww.in/etfs)) | ❌ | Add |
| **Gold / Bonds / Commodities / US Stocks** | Live / live / live / pilot | ❌ | Out of scope for parity |
| **Pledge holdings for margin** | Up to 90%, ₹20/ISIN ([src](https://groww.in/pricing)) | ❌ | Optional |
| **DDPI (sell without TPIN)** | ₹100 + GST | ❌ (PIN on every trade) | Optional |
| **Consolidated portfolio (Stocks Track)** | Oct 2025, via RBI Account Aggregator ([src](https://groww.in/updates/groww-stocks-track)) | ❌ | Out of scope |
| **KYC** | Aadhaar-OTP, activation in 2 working days ([src](https://groww.in/open-demat-account)) | 🟡 theatrical — PAN collected, "Verified ✓" pill is cosmetic | Label honestly |
| **Segments (equity / F&O activation)** | Explicit activation step | ❌ F&O open to everyone | Add activation gate |
| **Add money** | UPI / Netbanking / IMPS / NEFT / RTGS ([src](https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13)) | ✅ simulated UPI only | Add method choice |
| **Withdraw + bank management** | Multiple banks selectable ([src](https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2)) | 🟡 single bank | Add multiple banks |
| **Nominee** | Yes | ❌ | Add |
| **Referral** | Yes | ❌ | Optional |
| **Real authentication** | Session/JWT | ❌ client-supplied `X-User-Id` (`main.py:68`); plaintext passwords/PIN | **See §9** |
| **Pricing transparency** | ₹0 account, ₹0 AMC, brokerage table ([src](https://groww.in/pricing)) | ✅ shows a charge sheet, computed client-side | Move to server |

---

## 4. Fix these first — the flows that are silently broken

All four are the same class of bug: the client sends or reads field names the server does not use. They are cheap to fix and they are the difference between "the feature exists" and "the feature works".

### 4.1 GTT orders — create, list and cancel are all broken

**Create** (`app.js:5179`) sends `transaction_type`, but `GTTRequest` (`main.py:1030`) requires `name` and reads `action`:

```python
# main.py:1030 — server contract
class GTTRequest(BaseModel):
    symbol: str
    name: str                    # ← client never sends this
    trigger_price: float
    quantity: float
    action: str = "BUY"          # ← client sends "transaction_type"
    ...
```

FastAPI rejects the body with **422** before the handler runs, so "GTT" in the order-variety toggle always ends in `Trade execution failed`.

**Fix** — align the client payload:

```js
body: JSON.stringify({
  symbol: currentPageAsset.symbol,
  name: currentPageAsset.name,           // required
  action: pageOrderState.action,          // renamed from transaction_type
  quantity: qty,
  trigger_price: triggerPrice,
  product_type: pageOrderState.productType,
  target_price: limitPrice || 0.0,
  stop_loss_price: 0.0
})
```

**List** (`app.js:6225`) renders `o.order_id`, `o.transaction_type`, `o.limit_price`, but `get_gtt_orders()` (`database.py:2865`) is a `SELECT *` on `gtt_orders`, whose columns are `id`, `user_id`, `symbol`, `name`, `product_type`, `action`, `quantity`, `trigger_price`, `target_price`, `stop_loss_price`, `status`. So the table shows `undefined` in four columns and the Cancel button calls `/api/order/gtt/undefined` → 422.

**Fix** — map the real keys: `o.id`, `o.action`, `o.target_price` (or show `—` when 0).

**Cancel** then works unchanged, because `cancel_gtt_order(user_id, gtt_id)` already takes the numeric `id`.

**Still missing after that fix:** nothing evaluates `trigger_price`. `place_gtt_order` inserts a row and no code path ever reads it back for evaluation — the same gap the DEBUG_REPORT flagged as N1 for limit orders before `service_pending_orders` was added. Reuse that hook:

```python
def service_gtt_orders(uid: str) -> int:
    for g in get_gtt_orders(uid):
        if g["status"] != "ACTIVE":
            continue
        q = market_service.get_stock_quote(g["symbol"])
        hit = (q["price"] >= g["trigger_price"]) if g["action"] == "BUY" \
              else (q["price"] <= g["trigger_price"])
        if hit:
            execute_trade(...)   # guarded ACTIVE → EXECUTING claim first
```

Groww's GTT is valid for **1 year on stocks** and **until contract expiry on F&O** ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39)) — so add an `expires_at` column rather than letting GTTs live forever.

### 4.2 "My Active SIPs" throws on every render

`get_user_sips()` (`database.py:2913`) returns raw `sips` rows: `id`, `user_id`, `fund_id`, `fund_name`, `monthly_amount`, `sip_day`, `status`, `next_installment_date`.

`loadActiveSips()` (`app.js:6841`) reads `s.symbol`, `s.amount`, `s.installment_day`, `s.next_trigger_date`, `s.installments_completed` and `s.sip_id`. `s.symbol.replace(...)` on line 6859 therefore throws a `TypeError` inside the `try`, the `catch` only logs to console, and the user sees a permanently empty table — with **Stop SIP** unreachable because it is inside the same failed template.

**Fix** — map the real keys (`s.fund_name`, `s.monthly_amount`, `s.sip_day`, `s.next_installment_date`, `s.id`). Note the server response is a bare list, which matches `sips.length`, so no envelope change is needed.

### 4.3 The tax trades table is dead markup

`#taxTradesTableBody` (`index.html:644`) is **never referenced anywhere in `app.js`** — grep returns zero matches. `loadPortfolioAnalytics()` fills the four summary cards from `GET /api/analytics/tax-report` but drops the `trades[]` array on the floor.

**Fix** — render `trades[]` into the existing table, and add the two columns Groww-style reporting needs: **holding period** and **STCG/LTCG** badge.

### 4.4 IPO: you can apply, but you can never see or withdraw a bid

`GET /api/ipo/applications` (`main.py:1128`) and `DELETE /api/ipo/bid/{id}` (`main.py:1135`) are fully implemented server-side and **called by nothing**. There is no "My Applications" surface. Groww shows status on the IPO page and routes the definitive result through the **Allotment** tab ([src](https://groww.in/ipo/allotment)).

**Fix** — add an `Applications` sub-tab next to All / Recently Listed / Upcoming in the IPO section, listing lot, bid price, amount blocked, status, and a **Withdraw** button. Also surface `ipo_id` on each card so withdraw can be targeted.

### 4.5 Two false claims in the product copy

- **`Auto Square-off 03:20 PM IST`** (`index.html:705`, `:1972`, `:2076`) — there is no scheduler in `main.py` or `database.py`. Either build it (§6.3) or remove the claim.
- **`Verified with Income Tax Department`** pill on the PAN step (`index.html:1569`) — the "verification" is cosmetic; no ITD/NSDL call exists. Relabel to something honest like "Format validated".

---

## 5. Flow-by-flow: how to make it *work* like Groww

For each area: what Stoxify does now, what Groww does, and the concrete change.

### 5.1 Information architecture

| | Stoxify today | Groww | Change |
|---|---|---|---|
| Primary nav | Explore · Holdings · Positions · Orders · Watchlist | Home · Stocks · Mutual Funds · Orders (+ Profile) | Replace. **Positions** and **Watchlist** become sections *inside* Portfolio and Stocks respectively — Groww keeps them as views, not top-level destinations ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/where-can-i-find-gtt-order--30) shows Orders containing tabs). |
| Explore sub-nav | Stocks / F&O / MF / IPOs | Separate product sections | Keep Stocks · F&O · MF · IPO, add **ETFs** and **Collections**. |

**Why this matters functionally, not cosmetically:** a first-time investor looking for "where do I invest monthly" cannot find Mutual Funds under a tab called *Explore*, and cannot find their profile at all without opening the avatar dropdown. Groww's nav answers "what do I want to do" — invest, trade, track.

Recommended target:

```
Home        → portfolio value card, indices strip, holdings summary, MY watchlist,
              most-bought, collections, IPO/open-SIP nudges, news
Stocks      → sub-tabs: Discover | Watchlist | Collections | ETFs | F&O | IPO
Mutual Funds→ sub-tabs: Explore | My SIPs | My Investments (holdings)
Portfolio   → sub-tabs: Holdings | Positions | Analytics | Reports
Orders      → sub-tabs: All | Open | Executed | Rejected | Cancelled | GTT
Profile     → account, bank, KYC/segments, nominee, security, reports, support
```

### 5.2 Stock detail page

**Now:** `showAssetPage` (`app.js:3868`) renders hero price, chart with 1D–ALL + EMA + scrub, performance card, L2 depth, fundamentals grid, About, then tabs for Financials / Shareholding / Peers / News, plus an SIP calculator on fund pages.

**Groww's anatomy:** price header → chart with timeframe tabs (1D/1W/1M/1Y/All) → key stats → about → financials → shareholding → peers → news, with the **Buy/Sell action pinned**, not buried.

**Changes:**
1. **Sequence it for an investor.** Today L2 depth (a trader's tool) sits above fundamentals. Move depth behind a "Market depth" expander, and lead with key stats + about.
2. **Pin the Buy/Sell CTA** as a sticky footer bar on mobile (`position: sticky; bottom: <bottom-nav height>`), so the action is always one tap away while scrolling DD.
3. **Add missing per-stock data that Groww shows:** 52-week high/low, P/E, market cap, dividend yield, book value, ROE, face value, and **DMA/52W markers on the chart**. The `quote` payload backs most of these already.
4. **Add "Add to watchlist" and "Set alert" next to the star** — Groww pairs them.

### 5.3 Order placement

**Now:** variety toggle (Market / Limit / SL / GTT) + product toggle (Delivery CNC / Intraday 5× MIS) + qty stepper with +1/+5/+10/+25/+50 chips + limit/trigger price + a margin/charges/net-credit card, then one primary button that fires `POST /api/order` immediately.

**Groww's flow:** tap Buy/Sell → **order sheet** with a product tab row (**Delivery | Intraday | MTF**) → quantity → order type (Market/Limit) → price if Limit → optional *Advanced Options → SL* or *Add SL/TGT* → the sheet shows **margin required and charges** → place → order lands in **Orders** with status *Open/Pending → Executed / Rejected / Failed / Cancelled* and **1-click Retry** ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68)).

**Changes:**

| # | Change | Detail |
|---|---|---|
| 1 | **Add a confirmation step** | After the execute button, show a confirm sheet: symbol, side, product, order type, qty, price, margin, charges, net. Groww never commits an order straight off the form — and it prevents fat-finger mistakes that a paper-trading app should be teaching users to avoid. |
| 2 | **Order-type row as a Groww-style tab set** | Market · Limit · SL · **SL-M** · GTT, with a "Advanced" expander holding SL/SL-M/GTT. `SL-M` = trigger → market; add `variety: "SL_M"` server-side. |
| 3 | **AMO as an explicit toggle** | Today the server silently tags off-hours orders. Groww lets the user place an AMO deliberately ([src](https://groww.in/blog/types-of-stock-market-orders)). Show a clear "This will be queued as an AMO for 09:15" confirmation. |
| 4 | **Show margin *before* the user commits** | Already done — keep it, but source it from `GET /api/trade/charges` instead of the duplicated client-side `calculateEstimatedCharges` (`app.js:1959`) so the quote and the settlement can never disagree. |
| 5 | **Surface order status properly** | Add `REJECTED` / `FAILED` states with a reason string ("insufficient funds", "market closed"), a status pill per row, and a **Retry** button. |
| 6 | **Add order modification** | `PUT /api/order/{id}` allowing price and quantity on `OPEN` orders only; block once executed (this is exactly what Groww documents). |
| 7 | **Kill the dead legacy modal** | `#tradeModalOverlay` + `legacyOpenAssetModal` + `submitOrder` (`app.js:1628`, `:2117`, `:1761`–`:2052`) is unreferenced. Delete it, or wire it — a second order path that can drift from the canonical one is a bug farm. |

### 5.4 Portfolio: holdings, positions, orders

**Now:** Holdings table + mobile cards with Current Value / Invested / Total Returns / 1D; a Positions table with total P&L, margin and count, plus per-row Exit and Square Off All; an Orders list with a status filter.

**Groww:** the same three views but grouped under one Portfolio entry, with **Invested / Current / Returns** at the top and each row expanding to show average price, quantity, day change, and a "View details" affordance. Positions is where intraday lives with live P&L and exit controls.

**Changes:**
1. **Group Holdings + Positions + Analytics + Reports under one `Portfolio` tab.** Three separate top-level destinations is why the app feels like separate tools rather than one portfolio.
2. **Add a portfolio-level P&L chart** (value over time) at the top of Holdings — the data is reconstructable from the orders ledger.
3. **Add per-row expansion** on mobile instead of a full-screen navigation.
4. **Add a benchmark comparison** row (portfolio vs NIFTY 50) — Groww-like and cheap, since `/api/indices` already exists.
5. **Add `REJECTED`/`CANCELLED` grouping and date filters** to Orders; today only `status` is passed through (`main.py:885`).

### 5.5 Mutual funds & SIP

**Now:** a grid of funds from `GET /api/explore`, a fund asset page reusing the *stock* template (so AUM and expense ratio are hardcoded fallbacks), an SIP calculator that is pure client maths, a "Schedule SIP" modal posting to `/api/mf/sip`, and a broken Active SIPs tab.

**Groww's flow:** Home → **Mutual Funds** → Explore → fund page (returns 1Y/3Y/5Y, benchmark, expense ratio, AUM, exit load) → **Start SIP** → amount (min ₹500) → monthly debit date → pay via UPI/Netbanking → **AutoPay mandate via OTP** → SIP created. Then: Edit SIP (amount & date), Skip instalment, Add Step-up (6-month or 1-year interval), Redeem ([src](https://groww.in/blog/how-to-edit-sip-on-groww), [src](https://groww.in/help/mutual-funds/mf-sip/how-to-start-a-sip-on-groww)).

**Changes, in order of value:**

1. **Give mutual funds their own page template.** A fund is not a stock: it needs *returns by period*, expense ratio, AUM, category, benchmark, exit load, fund manager and minimum SIP — not market depth and P/E. Right now `renderPageFundamentals` shows stock fields with hardcoded fallbacks.
2. **Add a real SIP lifecycle**, not just creation:
   - edit amount / debit date,
   - skip next instalment,
   - step-up (increase by X% every 6 or 12 months),
   - pause / resume,
   - cancel (already exists once §4.2 is fixed).
3. **Add the SIP execution job** — see §6.2. Without it, "Active SIPs" can only ever show a schedule.
4. **Add redemption** (full / partial / by amount / by units) with the T+3–4 working-day note Groww shows.
5. **Add a "My Investments" view** — SIP-accumulated fund holdings, distinct from stock holdings.
6. **Enforce the ₹500 minimum in the modal**, not only server-side, so the user gets the constraint before typing.
7. **Add return periods to the fund cards** (1Y / 3Y / 5Y) — the single most useful thing on a Groww fund card.

### 5.6 IPO

**Now:** IPO cards with filters (All / Recently Listed / Upcoming), an ASBA-style bid modal that works, and two buttons — "View Listing Details" and "Notify on Open" — that do nothing but fire a toast.

**Groww's flow:** Stocks tab → IPO → pick an open IPO → bid amount / quantity (must be a **multiple of the lot size**) → optional **"At cutoff price"** → UPI ID → Apply → a **UPI mandate** arrives within 1–2 hours → approving it **blocks the funds**. `Groww Balance cannot be used` for IPO margin — it is a regulatory separation. Status lives on the IPO page, and the definitive result is on the **Allotment** tab via registrar links ([src](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/how-to-invest-in-ipo), [src](https://groww.in/ipo/allotment)).

**Changes:**
1. **Build "My Applications"** (see §4.4) with status, blocked amount and Withdraw.
2. **Make "Notify on Open" real** — store an intent and surface it as a Home card / notification when the IPO opens. Today it is a lie.
3. **Replace "View Listing Details"** with an actual detail view: price band, lot size, **GMP**, subscription status by category (QIB / HNI / Retail), open/close dates, registrar.
4. **Add an "At cutoff price" checkbox** to the bid modal.
5. **Add the Allotment tab** — allotted / not allotted per application.
6. **Add the lot-size constraint in the UI** so `lots × shares` is always valid, rather than discovering it server-side.

### 5.7 Money movement (add / withdraw)

**Now:** a 3-step simulated UPI add-money flow with a 4-digit PIN, a withdraw flow, and a bank passbook modal. Single hardcoded bank.

**Groww:** Profile → **"Stock, F&O Balance"** → **Add Money** → amount → method (Netbanking / UPI / IMPS / NEFT / RTGS) → done. UPI/Netbanking/RTGS-IMPS are instant; NEFT can take up to an hour. Withdraw: choose from **multiple registered banks** ([src](https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13), [src](https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2)).

**Changes:**
1. **Add a method selector** (UPI / Netbanking / IMPS / NEFT / RTGS) with per-method ETA copy — cheap and it teaches how funding actually works.
2. **Support multiple bank accounts** — add/list/set-primary. The edit-profile modal already collects bank fields; the model just needs to be a list.
3. **Surface the wallet-vs-bank split explicitly.** This is the app's biggest conceptual trap: `create_user` seeds ₹10,00,000 to the **linked bank** while the **trading wallet starts at ₹0**, yet the onboarding copy says the capital is unlocked. Groww's model is "add money from bank → Groww balance", and the copy should say exactly that.
4. **Add a Funds ledger** — every deposit, withdrawal, margin block, charge and settlement as a dated row. That is what Groww's "Stock, F&O Balance" screen is, and it makes the charge sheet verifiable.

### 5.8 Onboarding & KYC

**Now:** 6 steps — phone/email/username/password → OTP → PAN/name/DOB/age/experience → bank + penny drop → 4-digit PIN → success. OTP is generated client-side with `Math.random` and **`4321` always passes** (`app.js:5587`); PAN "verification" is cosmetic; penny drop is a `setTimeout`.

**Groww:** mobile → OTP → PAN → Aadhaar-OTP KYC → bank verification → e-sign → **segment activation** (equity / F&O / commodity), activation within 2 working days ([src](https://groww.in/open-demat-account)).

**Changes:**
1. **Add an explicit segment-activation step** for F&O. Right now options trading is open to every account, whereas Groww gates F&O behind activation — and Stoxify's own F&O banner brags that it needs no income proof. Gating it (even with a one-tap "Activate") makes the product teach the real constraint instead of contradicting it.
2. **Label the simulation honestly.** Keep the flow, but mark the OTP/PAN/penny-drop steps as simulated. A trading-education product that claims "Verified with Income Tax Department" when nothing was verified is teaching the wrong thing.
3. **Add nominee** capture — a real, required part of Indian demat onboarding and a natural fit for the existing step pattern.
4. **Add a resume-an-onboarding state** so a reload mid-flow doesn't drop the user back to step 1.

### 5.9 Alerts, notifications and discovery

**Now:** nothing. Toasts only, and they vanish. "Most Bought" is `all_stocks[:8]` — the first eight rows of the master list.

**Groww:** automatic **±5% price alerts** on watchlist/portfolio stocks, plus **DMA / circuit / 52-week-high-low** and corporate-event alerts, with a **Notification Management** screen of per-category on/off toggles — shipped precisely because alerts became overwhelming ([src](https://groww.in/updates/notification-management-on-groww)). Plus screeners, collections, ETF pages, and a news feed.

**Changes:**
1. **Persistent notification centre** (bell in the header, unread badge) backed by a `notifications` table. Events to start with: order executed, order rejected, GTT triggered, SIP debited, IPO status change, price alert hit.
2. **Price alerts** — user-set trigger with a direction, evaluated in the same polling hook as pending orders.
3. **Auto ±5% day-move alerts** on watchlist + holdings, with a profile toggle.
4. **Fix "Most Bought".** Replace `all_stocks[:8]` with an actual ranking — most-held by users, or most-traded by order count — otherwise the section is a false claim.
5. **Collections / curated lists** — "Top Gainers", "52-week high", "Banking", "PSU", etc. The `filterExploreStocks` sector pills already approximate this statically; promote them to first-class browsable collections.
6. **A screener** with filters (market cap, P/E, sector, 1Y return) — Groww ships one for stocks and ETFs.

---

## 6. Missing mechanics to build

These are the structural gaps, in dependency order.

### 6.1 An order-matching engine, not an on-read trigger

Limit and (after §4.1) GTT orders are evaluated **only when the Orders tab polls** (`service_pending_orders`, per the DEBUG_REPORT). A user who never opens the app never gets a fill.

**Build:** a background job (or a single `POST /api/engine/tick` called by a scheduler) that every N seconds evaluates resting limit orders, GTTs, stop-losses and SL-M triggers against the quote cache. Make the Orders poll a pure read again.

### 6.2 A SIP execution engine

**Build:** a daily job that, for each `ACTIVE` SIP whose `next_installment_date` has arrived: debit `monthly_amount` from the wallet, allot units at the day's NAV, append a `sip_installments` row, advance `next_installment_date` (clamping month-end, per the existing `calendar.monthrange` logic at `database.py:2900`), and raise a notification. Insufficient funds → mark that instalment `FAILED` and notify, rather than silently skipping.

### 6.3 Auto square-off

**Build:** at 15:20 IST on trading days, square off every open `MIS` position at market and raise a notification. The market-hours machinery in `market_hours.py` already knows the session, so this is a thin addition. Until it exists, delete the on-screen promise.

### 6.4 IPO allotment processing

**Build:** move bids from `APPLIED` to `ALLOTTED` / `NOT_ALLOTTED` (simulated random or rule-based), unblock the non-allotted amount, and credit allotted shares to holdings. Today a bid is a black hole.

### 6.5 Real authentication

**Build:** session tokens (or Supabase Auth, already wired for storage) and hash passwords/PINs with `bcrypt`/`hashlib`. Currently identity is a header any client can set (`main.py:68`) and `pin`/`password` are stored as plaintext with a plaintext comparison (`main.py:424–427`). For a portfolio-tracking app this is the single most important non-UI fix — and it is the one Groww-parity item you must *not* skip, because every "my portfolio" flow is meaningless without it.

### 6.6 Reports & exports

**Build:** P&L report (realised + unrealised, per scrip and per period), Tax P&L (STCG/LTCG split with the ₹1.25 L LTCG exemption — `database.py:3015` already computes it), transaction history, ledger, and contract notes per executed order. CSV + PDF export. Groww users downloaded 6M+ reports in a single tax season ([src](https://groww.in/updates/fno-pnl-dashboard-groww)) — this is a retention feature, not a nice-to-have.

### 6.7 F&O depth

**Build:** futures contracts (today it is options-only), **option Greeks** (delta/theta/vega/gamma), an **NRML** product type, a **margin calculator** per contract, expiry-day handling, and un-hardcode the `INTRADAY` force at `app.js:6498`.

### 6.8 Discovery & market data

**Build:** index pages (NIFTY 50 / SENSEX / BANK NIFTY with constituents), **ETF pages**, more-bought/most-held rankings, collections, a screener, and a news feed beyond per-stock. Also replace the synthetic depth generated by `random.randint` (`main.py:528–539`) with something deterministic so the L2 ladder does not flicker meaninglessly.

---

## 7. Prioritised backlog

Effort is developer-days for one person familiar with the codebase. "Value" is user-perceived functional gain.

### P0 — broken or false (ship this week)

| Item | Value | Effort | Ref |
|---|---|---|---|
| Fix GTT create payload (`name` + `action`) | High | 0.5 d | §4.1 |
| Fix GTT list field mapping (`id`/`action`/`target_price`) | High | 0.5 d | §4.1 |
| Fix Active SIPs render + Stop SIP | High | 0.5 d | §4.2 |
| Render the tax trades table | Medium | 0.5 d | §4.3 |
| IPO "My Applications" + Withdraw | High | 1 d | §4.4 |
| Remove or implement the "Auto Square-off 3:20 PM" claim | Medium | 0.5 d | §4.5 |
| Relabel the cosmetic "Verified" pills (PAN, bank) as simulated | Medium | 0.5 d | §5.8 |
| Delete the dead `#tradeModalOverlay` order path | Medium | 0.5 d | §5.3 |
| Route the client charge estimate through `GET /api/trade/charges` | Medium | 0.5 d | §5.3 |

**P0 total ≈ 5 days** — and it removes every instance of "the UI says it works but it doesn't".

### P1 — Groww flows (next 3–4 weeks)

| Item | Value | Effort | Ref |
|---|---|---|---|
| IA restructure: Home / Stocks / MF / Portfolio / Orders / Profile | Very high | 2 d | §5.1 |
| Order confirmation step + status lifecycle + Retry | Very high | 3 d | §5.3 |
| SL-M and AMO support | High | 3 d | §5.3 |
| Order modification (`PUT /api/order/{id}`) | High | 2 d | §5.3 |
| Background trigger engine (limit / GTT / SL / SL-M) | Very high | 4 d | §6.1 |
| SIP execution engine | Very high | 4 d | §6.2 |
| Intraday auto square-off job | High | 2 d | §6.3 |
| Notification centre + price alerts | Very high | 5 d | §5.9 |
| Dedicated mutual-fund page template + 1Y/3Y/5Y returns | High | 3 d | §5.5 |
| SIP edit / skip / step-up / pause | High | 3 d | §5.5 |
| Real authentication + password hashing | Critical (non-UI) | 3 d | §6.5 |
| Fix "Most Bought" ranking | Medium | 1 d | §5.9 |
| Funds ledger | High | 3 d | §5.7 |
| Multiple bank accounts + add-money method selector | Medium | 3 d | §5.7 |

### P2 — depth & parity (quarter)

| Item | Value | Effort | Ref |
|---|---|---|---|
| Reports: P&L, Tax P&L, transactions, ledger, contract notes + CSV/PDF | High | 6 d | §6.6 |
| Portfolio value chart + NIFTY benchmark comparison | High | 3 d | §5.4 |
| F&O: futures, Greeks, NRML, margin calculator, expiry handling | High | 8 d | §6.7 |
| Multiple watchlists (Groww allows 10) | Medium | 2 d | §3 |
| Collections, screener, ETF & index pages | Medium–high | 8 d | §6.8 |
| Mutual-fund redemption (full/partial) + "My Investments" | High | 4 d | §5.5 |
| IPO detail view with GMP + subscription + Allotment tab | Medium | 4 d | §5.6 |
| Segment activation (equity/F&O) in onboarding | Medium | 2 d | §5.8 |
| Nominee capture | Medium | 1 d | §5.8 |
| SL/TGT on open positions (OCO) | Medium | 4 d | §3 |
| Sticky Buy/Sell footer + richer stock stats + DMA markers | Medium | 3 d | §5.2 |
| Deterministic market depth | Low | 1 d | §6.8 |

---

## 8. Phased implementation plan

**Phase 1 — Make it truthful (week 1).**
Fix the four contract mismatches, delete the dead order path, correct the false copy. Nothing new is added; the app stops lying. After this, every visible control does what it says.

**Phase 2 — Make it an investor's app (weeks 2–3).**
Restructure the IA to Home / Stocks / Mutual Funds / Portfolio / Orders / Profile. Move Positions and Watchlist into their natural parents. Add the Home screen (portfolio card, indices, my watchlist, most-bought, nudges). This is the change that makes the app *feel* like Groww, because Groww's distinctiveness is its ordering, not its feature list.

**Phase 3 — Make the flows match (weeks 3–6).**
Order confirmation → status lifecycle → retry → SL-M/AMO → modification. Mutual-fund page template, SIP edit/skip/step-up, redemption. IPO applications + allotment. Dedicated confirmation and success states throughout, so a user always knows what just happened.

**Phase 4 — Make it alive (weeks 6–9).**
Background engine for limit/GTT/SL triggers, SIP execution, auto square-off, IPO allotment. Notification centre and price alerts. This is the phase where the app stops being a form-and-refresh simulator and starts behaving like a broker: things happen while you are not looking.

**Phase 5 — Depth and reporting (weeks 9–14).**
Reports and exports, portfolio chart + benchmark, F&O depth (futures, Greeks, NRML, margin calculator), multiple watchlists, collections and screener.

**Cross-cutting, start in Phase 1:** real authentication and password hashing (§6.5). Every "my portfolio" flow is built on identity; retrofitting sessions later means touching every route.

---

## 9. Deliberate divergences — do **not** copy these

Parity is the goal, but three Groww behaviours should not be replicated here, and one structural gap must be closed first.

1. **Don't imply regulatory status you don't have.** Groww legitimately shows a SEBI registration number, "Groww is a broker", disclaimers and a complaint/SCORES escalation path. Stoxify is a simulator. Copying the *look* of compliance without it is the worst possible outcome for an education product. Keep an explicit, persistent "Simulated trading — no real money, no real securities" marker.
2. **Don't copy Groww's F&O optimism.** Groww gates F&O behind segment activation and ships risk tooling — SafeGuard, F&O Pause, OCO. Stoxify currently brags "**NO INCOME PROOF NEEDED**" (`index.html:381`) and hands every account 5× leverage. If you match Groww's F&O flow, match its guardrails too: activation, a loss cap, and a pause control. The 5× leverage badge is fine; the marketing line is not.
3. **Don't add Groww's money-movement fiction.** Groww's *real* constraint is that IPO margin cannot come from the Groww balance, and that SIPs cannot be funded from it either (SEBI). Simulating an IPO bid funded from a wallet teaches the opposite of how ASBA works. Block the IPO bid against the wallet and require a separate "UPI mandate" bucket — it is more realistic *and* easier to explain.
4. **Close the identity gap first.** Groww's per-user portfolio, alerts, reports and consent all rest on authenticated sessions. Stoxify's `X-User-Id` header means any client can read or mutate any other user's portfolio (`main.py:68`), and passwords/PINs are stored in plaintext. Restructure to sessions before building anything that stores user-specific intent (alerts, notify-on-open, SIPs), or those features inherit the flaw.

### Documented Groww inconsistencies (do not treat as spec)

- Groww's own help pages disagree about instant-withdrawal limits: one says instant 9:30 AM–6 PM under ₹2 lakh, another says 9:30 AM–4 PM Mon–Fri under ₹1 lakh ([a](https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13), [b](https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2)). Pick one rule and document it; don't copy the contradiction.
- `groww.in/fixed-deposits` returns 404 despite third-party claims the product exists — treat Groww Fixed Deposits as **unverified**.
- Groww's mobile bottom-nav tab order could not be confirmed from a primary source, so §5.1 proposes an order derived from the verified help-centre navigation paths (Stocks → Orders → GTT Orders; Mutual Funds → Dashboard → SIPs; Profile → Stock, F&O Balance), not a claimed screenshot.

---

## 10. Sources

**Groww — product pages, help centre, pricing**
- https://groww.in/pricing
- https://groww.in/stocks
- https://groww.in/mutual-funds
- https://groww.in/futures-and-options
- https://groww.in/ipo
- https://groww.in/ipo/allotment
- https://groww.in/etfs
- https://groww.in/stocks/mtf
- https://groww.in/open-demat-account
- https://groww.in/mutual-funds/start-sip
- https://groww.in/blog/types-of-stock-market-orders
- https://groww.in/blog/how-to-edit-sip-on-groww
- https://groww.in/blog/how-to-start-a-stp-and-swp-on-grow
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-to-place-a-gtt-order---66
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/where-can-i-see-my-gtt-orders---48
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/where-can-i-find-gtt-order--30
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-or-cancel-my-order--22
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68
- https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/how-to-invest-in-ipo
- https://groww.in/help/mutual-funds/mf-sip/how-to-start-a-sip-on-groww
- https://groww.in/help/mutual-funds/order/how-to-withdraw-redeem-4
- https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13
- https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2

**Groww — official product changelog (`/updates`)**
- https://groww.in/updates
- https://groww.in/updates/bracket-orders-on-groww
- https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday
- https://groww.in/updates/notification-management-on-groww
- https://groww.in/updates/fno-pnl-dashboard-groww
- https://groww.in/updates/groww-stocks-track

**Groww — app listings**
- https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_US
- https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703

**Stoxify — internal evidence**
- `main.py` (route table, Pydantic models), `database.py` (schema + engines), `public/app.js` (client flows), `public/index.html` (screens)
- `DEBUG_REPORT.md` — prior bug audit; N1 (no GTT trigger engine), N2 (Supabase-first reads), N4 (no authentication), N7 ("Most bought" is not most bought), N8 (offline never works), N9 (intraday timing not enforced), N10 (bank-vs-wallet copy)

---

## Appendix — what I could not verify

- Groww's exact mobile bottom-navigation tab labels and order.
- Groww's real instant-withdrawal thresholds and cut-off times (its own docs conflict).
- Whether Groww Fixed Deposits is a live product.
- Groww's per-order slippage/execution behaviour (only user complaints, no documentation).
- Groww's commodity (MCX) brokerage breakdown — not separately itemised in the tariff page.
