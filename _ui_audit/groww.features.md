# Groww — Current Product Feature Set & User Flows (2025–2026)

**Scope:** FUNCTIONAL / product research only. No colours, fonts, branding or visual styling.
**Research date:** September 2026 (sources fetched live; "today" = 12 Sep 2026).
**Method:** primary sources first — groww.in, groww.in/help (help centre), groww.in/updates (official product announcements), groww.in/pricing, Google Play + Apple App Store listings. Secondary sources used only where no primary source exists, and are dated.
**Rule applied:** any claim that could not be verified on a source is explicitly marked **unverified**.

---

## 1. PRODUCT LINES

Groww is a SEBI-registered stock broker (Groww Invest Tech Pvt Ltd, SEBI Reg No. INZ000301838; NSE 90187, BSE 6699, MCX 57420; DP with CDSL & NSDL). Source: https://groww.in/pricing

Official Google Play listing ("Groww is your one app to invest & trade in"): Stocks, Mutual Funds, F&O, Gold and Silver, MTF, Commodity Derivatives, ETFs, IPO, Bonds, API Trading. Source: https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_US

| # | Product line | Real URL | What it is | Status |
|---|---|---|---|---|
| 1 | **Stocks (equity delivery + intraday)** | https://groww.in/stocks | Buy/sell NSE & BSE listed shares. Delivery (long-term hold) and Intraday with up to 5X leverage. | **Live** |
| 2 | **Mutual Funds (Direct)** | https://groww.in/mutual-funds | Direct plans of AMCs, 0% commission; SIP or lumpsum. Uses BSE StAR MF as transaction platform (member code 11724). | **Live** |
| 3 | **F&O (Futures & Options)** | https://groww.in/futures-and-options | Index + stock derivatives; option chain, Greeks, payoff, basket orders, Terminal. | **Live** |
| 4 | **IPO** | https://groww.in/ipo | Apply to Mainboard and SME IPOs via UPI mandate / ASBA. | **Live** |
| 5 | **MTF (Margin Trading Facility)** | https://groww.in/stocks/mtf | Buy stocks paying a fraction upfront (as low as 25%, up to 4X); Groww funds the rest at 14.95% p.a. | **Live** |
| 6 | **ETFs** | https://groww.in/etfs | Exchange-traded funds + ETF screener; ETF NFOs. | **Live** |
| 7 | **Commodities (MCX)** | https://groww.in/commodities | Gold, Silver, Gold Mini, Silver Mini, Crude Oil, Natural Gas, Nickel, Copper, Zinc, Aluminium futures/options. | **Live** |
| 8 | **Bonds (listed + Bond/NCD IPOs)** | https://groww.in/bonds | Listed corporate bonds and new-issue corporate bond (NCD) IPOs. Min ₹10,000 (₹1,000/unit); apply 10:00 AM–5:00 PM on market days. Launched Jul 2025. | **Live** |
| 9 | **Gold (Gold ETFs / Gold MF / Gold ETF FoF)** | https://groww.in/gold | SEBI-regulated gold exposure only (Gold ETFs, gold mutual funds, commodity). Groww explicitly does NOT list unregulated "digital gold". | **Live** |
| 10 | **Sovereign Gold Bonds (SGB)** | https://groww.in/sovereign-gold-bonds | SGB applications + pledge of SGBs. | **Live (when SGB tranches are open)** |
| 11 | **Groww AMC — "Groww Mutual Fund"** | https://groww.in/mutual-funds/amc/groww-mutual-funds | Groww's own fund house (sponsor: Groww Invest Tech Pvt Ltd; trustee: Groww Trustee Ltd). Total AUM ₹6,969.90 Cr. Equity/index/debt/commodity funds incl. Groww Multicap, Groww Small Cap, Groww Nifty Total Market Index, Groww Liquid, Groww Gold ETF FoF, Groww Silver ETF FoF. | **Live** |
| 12 | **API Trading** | https://groww.in/trade-api | Programmatic order placement / algo trading. | **Live** |
| 13 | **Groww Terminal / Charts** | https://groww.in/charts | Web trading terminal: charts, indicators, orders, P&L, watchlists in one space. | **Live** |
| 14 | **PMS ("W by Groww")** | https://groww.in/pms | Portfolio Management Services, min ₹50 lakh, separate "W app", multi-cap/large/mid/small/flexi strategies. | **Live (separate W app, HNI product)** |
| 15 | **Credit (personal loan / LAS)** | https://credit.groww.in/ | Personal loans (tenure 3–60 months, APR 13–48%) and loan against securities, via partner lenders + Groww CreditServ. | **Live (separate credit app/brand)** |
| 16 | **US Stocks** | (no public product page; https://groww.in/us-stocks redirects to login as of Sep 2026) | International equities from India, subject to RBI LRS. Groww received the IFSCA/GIFT-City licence and publicly stated the feature was **in testing** (Jul 2026). | **NOT LIVE for general users — approved + pilot/testing** |
| 17 | **Fixed Deposits (FD)** | https://groww.in/fixed-deposits → **404 / Page Not Found** (verified Sep 2026) | No FD product page or FD booking flow found on Groww's own site. A help-centre index description mentions "Fixed Deposits" and a secondary LinkedIn post claims FDs "already launched". | **UNVERIFIED — no primary evidence of a live FD booking product** |
| 18 | **NPS (National Pension System)** | Only a calculator: https://groww.in/calculators/nps-calculator | No NPS account-opening or NPS investment product page found on groww.in. | **UNVERIFIED / appears NOT offered as an investable product** |

Additional verified Groww surfaces (not separate "products" but discoverable sections): NFOs (https://groww.in/nfo), Stock Screener (https://groww.in/stocks/filter), Stock Events calendar (https://groww.in/stocks/calendar), Groww Digest (https://groww.in/digest), Track external funds (https://groww.in/track), Mutual Fund screener (https://groww.in/mutual-funds/filter), Compare Funds (https://groww.in/mutual-funds/compare). Source: https://groww.in/sitemap, https://groww.in/

**Note on "waitlisted":** no Groww product is presented as waitlisted. US Stocks is the only line that is licensed-but-not-GA. Everything else listed as Live is transactable today.

---

## 2. STOCKS

### 2.1 Order types supported

| Order type | Supported | Evidence |
|---|---|---|
| Market | Yes | Order-placement screen supports Market; https://groww.in/blog/types-of-stock-market-orders |
| Limit | Yes | Same; "MODIFY to change the price or quantity" |
| Stop-loss (SL, converts to market on trigger) | Yes | Advanced Options → SL; https://groww.in/blog/how-to-place-stop-loss-order |
| Stop-loss Market (SL-M) | Yes | Referenced as "modify my stoploss order to market"; https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-my-stoploss-order-to-market--17 |
| Stop-limit | Yes (documented) | https://groww.in/blog/types-of-stock-market-orders |
| GTT (Good Till Triggered) | Yes — trigger price + optional limit price; stock GTT valid **1 year**, F&O GTT valid until contract expiry | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39 ; .../how-to-place-a-gtt-order---66 |
| AMO (After Market Order) | Yes — placed outside market hours, executed next trading session | https://groww.in/blog/types-of-stock-market-orders |
| OCO (intraday SL + target, one cancels other) | Yes — "Set Target & Stoploss both with OCO order for Intraday Trading" | Play listing; https://groww.in/updates/bracket-orders-on-groww |
| SL/TGT on an open intraday position | Yes (added May 2025) | https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday |
| Trailing stop | Documented as a concept on Groww's blog; **whether the Groww app exposes a trailing-stop order ticket is unverified** | https://groww.in/blog/types-of-stock-market-orders |

### 2.2 Product types (equity)

| Product type | Meaning | Evidence |
|---|---|---|
| **Delivery / CNC** | Full payment, shares credited to demat, no auto square-off | https://groww.in/blog/types-of-stock-market-orders |
| **Intraday / MIS** | Same-day buy+sell, leverage up to 5X, auto square-off at 3:20 PM (₹50+GST/position penalty) | Play listing; https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-are-intraday-charges |
| **MTF** | Pay ~25% upfront, Groww funds rest, 14.95% p.a. on funded amount; separate "MTF" tab instead of "Delivery" at order time | https://groww.in/stocks/mtf |

### 2.3 Order validity options
- **Day order** — valid only for the current trading session; auto-cancelled after close.
- **IOC (Immediate or Cancel)** — filled immediately (fully/partially), remainder cancelled.
- **GTT/GTC** — sits dormant until trigger price; stock GTT up to 1 year, F&O GTT until expiry.
- **AMO** — queued and sent to exchange on next session open.
All four documented at https://groww.in/blog/types-of-stock-market-orders and https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39

### 2.4 Order modification — YES, supported
Two paths (https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-or-cancel-my-order--22):
- **Profile → Orders → select order → MODIFY (price/quantity) or CANCEL**, or
- **Stocks → Orders tab → select order → MODIFY / CANCEL**.

GTT orders can be modified/cancelled any time **before the trigger price is hit** (Stocks: Stocks → Orders → GTT Orders → Modify/Cancel; F&O: FnO → Orders → GTT Orders). Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-do-i-modify---cancel-my-gtt-order---35

Modification is **blocked** when: (a) order already executed, (b) status changed to 'executed' before you act, (c) F&O monthly expiry day after 2:30 PM (open orders auto-cancelled). Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68

### 2.5 Step-by-step stock order placement (mobile app)

Verified flow reconstructed from Groww help + official update pages:
1. **Home → search the stock** (or Home → Stocks tab → pick from watchlist / Most Bought / screener).
2. **Tap the stock** → opens the stock detail page (price, chart, fundamentals, holdings/news tabs).
3. **Tap Buy (or Sell)** → order-placement sheet opens.
4. **Choose product type** as a tab/segment: `Delivery` | `Intraday` | `MTF` ("While buying a stock, switch to the 'MTF' tab instead of the 'Delivery' tab"). Source: https://groww.in/stocks/mtf
5. **Enter Quantity** and choose **Order Type** (Market / Limit) and enter **Price** if Limit.
6. **Optional: tap "Advanced Options"** to add Stop-loss (SL), or tap **"Add SL/TGT"** for intraday target+stoploss.

**Exact fields shown on the order sheet (verified):**
| Field | Source |
|---|---|
| Quantity | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-to-place-a-gtt-order---66 ; SL/TGT update |
| Price (Limit) / Market | same |
| Order Type (Market/Limit) | https://groww.in/blog/types-of-stock-market-orders |
| Product (Delivery / Intraday / MTF) | https://groww.in/stocks/mtf |
| Stop-loss price / Target price (via Add SL/TGT or Advanced Options) | https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday |
| **Margin required / required amount** — "The required amount will adjust based on the stock's margin" | https://groww.in/stocks/mtf |
| **Estimated P&L for both legs** after setting SL/TGT levels | SL/TGT update page |
| **Charges** — brokerage + statutory; Groww publishes per-order charge breakdown and a Brokerage Calculator | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-are-intraday-charges ; https://groww.in/calculators/brokerage-calculator |

7. **Place order** → order goes to exchange.
8. **Track it**: Stocks → Orders tab. Statuses progress Open → Executed / Rejected / Cancelled; rejected/failed orders get a **1-click Retry** from order details. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
9. **Profit/loss settlement**: profits are added to Groww Balance by 9 PM on trade day; losses deducted at the same time. Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/when-will-i-get-my-profit-loss--45

**GTT placement (separate flow, verified step-by-step):** Homepage → select the stock or F&O contract → choose the delivery option → tap the top-right corner → select 'GTT Order' → enter quantity, set trigger price, optionally set a limit price (if no limit price is entered, a **market** order is placed on trigger). Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-to-place-a-gtt-order---66

**GTT caveats (verified):** a triggered Buy GTT fails if there is not enough money in the Groww wallet; a triggered Sell GTT fails if holdings are not verified on the trigger day. GTT orders appear under Stocks → Orders → 'GTT Orders'. Sources: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39 ; .../where-can-i-see-my-gtt-orders---48

---

## 3. F&O (Futures & Options)

### 3.1 What Groww presents
Source for all below: https://groww.in/futures-and-options (official product page)

- **Advanced option chain** — strikes, premiums, open interest, contract-level data in one place. Dedicated page per index: https://groww.in/options/nifty ("Live NSE Option Chain Price Chart with OI & Greeks").
- **Greeks view** — Delta, Gamma, Theta, Vega.
- **Payoff analysis** — payoff graph for multi-leg strategies; shows max loss, max profit and breakeven points (payoff graph for basket orders launched on web).
- **Strategy baskets / basket orders** — "Build, review, and execute multi-leg strategies"; cross-expiry basket enablement.
- **Compact trading screen** — spot chart + strike prices + order actions + open positions in one interface.
- **Spot & contract chart toggle**, **Call/Put chart switch**, **strike & entry markers on chart**, **chart-based execution** (place trades from chart context).
- **1-click entry & exit**, **Fast Exit**, **Safe Exit**, **1-click Retry Orders**.
- **Live position tracking** — price, quantity, entry point, P&L; **Expected P&L**; margin visibility (available / used / pledged / exposure).
- **Pledge for extra margin** — pledge eligible holdings, unlock up to 90% of holdings value; SGBs can be pledged.
- **India VIX** — search "VIX" in the app.
- **API trading support** — https://groww.in/trade-api
- **Terminal** — https://groww.in/charts, plus "Groww Charts".
- **Execution speed claim:** "Average order is placed under 20 ms"; Bracket Orders update claims "sub-50ms order latency". Sources: https://groww.in/futures-and-options ; https://groww.in/updates/bracket-orders-on-groww
- **Trade above freeze quantity in Options** (Play listing).

### 3.2 Order types available in F&O
- **Market** and **Limit** — https://groww.in/futures-and-options
- **Stop-loss orders** — same
- **GTT orders** — valid until contract expiry — https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39
- **Bracket Orders** (entry + SL + target in one ticket) — live since Jan 2026, F&O only, market-hours only, no extra charge — https://groww.in/updates/bracket-orders-on-groww
- **OCO orders** (SL + target on an open position; one triggers, other auto-cancels) — same source
- **Trigger-Based Entry Orders (SL Entry)** — enter only when price reaches a predefined level — same source
- **Position Adjustment** — drag-and-drop grid to roll a position to a different expiry/strike, or switch Call↔Put, without manual exit+re-entry — https://groww.in/updates/fno-position-adjustment-on-groww
- **Basket orders** — multi-leg execution — https://groww.in/futures-and-options

### 3.3 Margin calculator
Public calculator: **https://groww.in/calculators/margin-calculator** ("Estimate balance needed to buy/sell a stock"). In-product, margin is shown on the F&O order screen as available / used / pledged margin and exposure (https://groww.in/futures-and-options).

### 3.4 Expiry handling (verified specifics)
- **Monthly expiry day:** trading in expiring contracts is restricted after **2:30 PM** and open orders are **automatically cancelled**; modifications not allowed during that window. Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68
- **GTT F&O orders remain active until the contract's expiry.** Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-to-place-a-gtt-order---66
- Auto square-off of carried intraday positions is charged ₹50 + GST per position. Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-are-intraday-charges
- **SafeGuard:** F&O access is stopped if losses exceed safe limits (30 days' warning, option to submit income proof for reassessment). **F&O Pause:** a DIY switch to temporarily pause F&O trading while keeping stocks/MF active. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

### 3.5 Steps for buying an option (verified)
Groww documents four entry points (https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-fno/how-do-i-buy-sell-options-on-groww--76):
1. **Via Search:** apply the 'F&O' filter in search, type the option name.
2. **Via Explore page:** tap an index on the Explore page → see that index's option chains.
3. **Via the F&O Explore page:** select an option contract of choice.
4. **Via option chain:** select a strike directly from the chain of an index/stock.

Then: select the contract (e.g. "NIFTY 16200 Put 12th Aug '21" = NIFTY put, strike ₹16,200, expiry 12 Aug) → order screen → set quantity/price → optionally **Add stoploss/target** (Bracket Order) or OCO → place order. Bracket-order flow: F&O section → select index (NIFTY/BANKNIFTY) or stock → order placement screen → **tap "Add stoploss/target"** → set entry price, stop loss, target → place order. Source: https://groww.in/updates/bracket-orders-on-groww. Manual exit cancels any linked SL/target; if SL or target hits, the position exits and the other leg auto-cancels (same source).

---

## 4. MUTUAL FUNDS

### 4.1 Direct vs Regular
- Groww is an **AMFI-registered mutual fund distributor (ARN-111686)** and pushes **Direct plans with 0% commission** ("Invest in direct mutual funds with 0% commission"). Source: https://groww.in/sitemap ; Play listing.
- Groww also sells its own **Regular-plan-equivalent "Prime" tier for NRIs** — the pricing page states for NRI clients: "MF: Direct & Prime both available; Prime in line with regular plans". Source: https://groww.in/pricing
- Groww lets users **switch regular funds to direct funds** and **switch from one fund to another within the same fund house without redeeming** (AMC-internal switch). Sources: https://groww.in/sitemap ; Play listing.

### 4.2 SIP, step-up, pause/modify
- **SIP start (verified steps):** Home → Mutual Funds → 'Explore' → search/select fund → **Start SIP** → enter amount → select date (monthly debit date) → pay via UPI or Netbanking → **add AutoPay via OTP or form for future instalments**. Sources: https://groww.in/help/mutual-funds/mf-sip/how-to-start-a-sip-on-groww ; https://groww.in/mutual-funds/start-sip
- **Minimum:** SIP from **₹500/month**. Sources: https://groww.in/mutual-funds/start-sip ; https://groww.in/mutual-funds/amc/groww-mutual-funds
- **Limitation (verified):** "The SIP can only be set up on a monthly basis. Weekly, bi-monthly, quarterly, and half-yearly SIP options are not available." Also: "When you set up a new SIP, the first month is often skipped because there needs to be a minimum of 30 days between the first and second installments." Source: https://groww.in/help/mutual-funds/mf-sip/how-to-start-a-sip-on-groww
- **Step-up SIP (verified):** Mutual Funds → SIPs tab → select SIP → if eligible, **'Add Step-up'** appears → enter the increase amount → choose interval (**6 months or 1 year**) → Proceed → verify with OTP. Not all SIPs qualify. Source: https://groww.in/help/mutual-funds/discoverable/can-i-place-step-up-request-for-all-of-my-sips--35
- **Pause / skip (verified):** My SIPs → select SIP → **Edit SIP** → **Skip Installment** → confirm on the pop-up (check the month) → confirm. Source: https://groww.in/help/mutual-funds/order/can-i-pause-sip-for-next-month
- **Modify amount/date (verified):** MF dashboard → SIPs → select SIP → **Edit SIP** → **Edit Amount & Date** → change → Save Changes → confirmation with processing estimate. Source: https://groww.in/blog/how-to-edit-sip-on-groww
- **SIP cannot be paid from Groww Balance** — SEBI rules; must use netbanking / UPI / mandate. Source: App Store developer response, https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703?see-all=reviews&platform=iphone

### 4.3 Lumpsum
Supported. On the fund page and groww.in/mutual-funds/amc/groww-mutual-funds: choose **"Invest One Time"** (lumpsum) or **"Start SIP"**. Lumpsum minimum on Groww's own funds is ₹500 (first and second investment). Sources: https://groww.in/mutual-funds/amc/groww-mutual-funds ; https://groww.in/mutual-funds/groww-multicap-fund-direct-growth

### 4.4 SWP / STP
- **Both are supported but on the WEBSITE ONLY** (not the app): "Currently, these facilities are available on the website only." Source: https://groww.in/blog/how-to-start-a-stp-and-swp-on-grow
- **STP steps:** Investments dashboard → select source fund → 3-dot menu → **Start STP** → choose destination fund (must be **same AMC**) → enter monthly transfer amount (installments auto-calculated, lock-in units excluded) → choose start date → **Confirm STP**.
- **SWP steps:** Investments dashboard → select the fund to withdraw from → 3-dot menu → **Start SWP** → enter monthly withdrawal amount (system shows how many withdrawals are possible) → select billing date → **Confirm SWP**. Manage active STPs/SWPs from the dashboard.
- Public calculators exist: SWP calculator (https://groww.in/calculators/swp-calculator), SIP calculator (https://groww.in/calculators/sip-calculator).
- **Redeem (in-app):** Mutual Funds tab → Dashboard → select fund → **Redeem** → enter amount → **Confirm Withdrawal**; credit in 3–4 working days. ELSS has a 3-year lock-in; redemption not possible for external funds held in DEMAT form. Source: https://groww.in/help/mutual-funds/order/how-to-withdraw-redeem-4

### 4.5 How fund detail pages present returns
Verified against https://groww.in/mutual-funds/groww-multicap-fund-direct-growth and https://groww.in/mutual-funds/amc/groww-mutual-funds (AMC listing table columns):

| Data element | Present on fund page | Notes |
|---|---|---|
| 1D / 1M / 3M / 6M / 1Y / 3Y / 5Y / 7Y / 10Y / All returns | **Yes** | AMC table shows 1Y, 3Y, 5Y, 7Y, 10Y; fund page shows 3M, 6M, 1Y, All |
| **Category average benchmark** | **Yes** | "Category average (Equity Multi Cap)" row alongside fund returns |
| **Rank within category** | **Yes** | "Rank (Equity Multi Cap)" row (3M, 6M, 1Y) |
| **Expense ratio** | **Yes** | e.g. Groww Multicap 1.06; Groww Liquid 0.11 |
| **AUM / Fund size** | **Yes** | "Fund size (AUM) ₹1,476.14 Cr" |
| **Exit load** | **Yes** | "Exit load of 1%, if redeemed within 1 year." |
| **Stamp duty** | **Yes** | "0.005% (from July 1st, 2020)" |
| **Tax implication** | **Yes** | e.g. "redeem within one year → 20%; after one year, gains > ₹1.25 lakh → 12.5%" |
| **Rating** | **Yes** (AMC table) | numeric star rating column |
| **Risk level** | **Yes** | "Very High / High / Low to Moderate / Low" |
| **NAV** | **Yes** | per-fund NAV shown in AMC table |
| **Minimum investments** | **Yes** | "Min. for 1st investment ₹500 / Min. for 2nd investment ₹500" |
| **Returns calculator (what-if)** | **Yes** | "Over the past 3m/6m/1y: Total investment → Would've become → Historic returns → Returns %" |
| **Holdings (with % weight, sector, instrument type)** | **Yes** | full holdings list incl. foreign equity, REITs, CDs, CPs, T-bills |
| **Comparable funds / similar funds** | **Yes** | "Compare similar funds", "Other plans in the same fund" |
| **Fund management / Fund house / About** | **Yes** | sections present |

Source: https://groww.in/mutual-funds/groww-multicap-fund-direct-growth ; https://groww.in/mutual-funds/amc/groww-mutual-funds ; https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth

### 4.6 Investment flow steps (SIP) — condensed
Home → **Mutual Funds** → **Explore** → search/select fund → fund page → **Start SIP** → enter amount (min ₹500) → pick debit date → pay via UPI/Netbanking → **set up AutoPay** (OTP or form) → SIP created; first instalment may be skipped if <30 days to the next.

**Lumpsum:** fund page → **Invest One Time** → enter amount → pay via UPI/Netbanking → units allotted in **3–4 business days**. (Order cannot be cancelled once placed — https://groww.in/help/mutual-funds/order/can-i-cancel-my-purchase-order--11)

**External MF import:** Mutual Funds tab → Explore → scroll → 'Import' external funds to track them in one place. Sources: https://groww.in/help/mutual-funds/mf-dashboard/how-do-i-import-my-external-mutual-fund-investments-1 ; https://groww.in/track

**SIPs list:** Mutual Funds section → **SIPs tab** → all active SIPs listed. Source: https://groww.in/help/mutual-funds/order/how-do-i-check-my-sips--44

---

## 5. IPO

### 5.1 How the section is organised (verified URLs)
Top-level nav tabs: **Open** (https://groww.in/ipo/open) · **Closed** (https://groww.in/ipo/closed) · **Upcoming** (https://groww.in/ipo/upcoming) · **Subscription** (https://groww.in/ipo/subscription) · **Allotment** (https://groww.in/ipo/allotment). Source: https://groww.in/ipo/allotment

IPO **type** is a column on every listing: **Mainboard** vs **SME**. (BSE SME IPOs went live on Groww — source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more)

### 5.2 Data displayed (verified from live listing tables)
**Open IPOs table:** Company Name · Type (Mainboard/SME) · Open Date · Close Date · Issue Price (price band, e.g. "₹130 - ₹140") · Overall subscription (e.g. "1.16x"). Source: https://groww.in/ipo

**Closed IPOs table:** Company Name · Type · Open Date · Close Date · Listing Date · Allotment Date · **Issue Price** · **Listing Price** · Overall subscription · Performance. Source: https://groww.in/ipo

**Allotment table:** Company Name · Type · Open Date · Close Date · Listing Date · **Allotment Date** · **Subscription %** · **Allotment Status** (with a "Check" link straight to the relevant registrar — KFintech / Link Intime / Bigshare / MUFG Intime / Cameo / Maashitla / Purva / Skylinerta / Integrated Registry / Abhipra / Alankit / Mudrarta). Source: https://groww.in/ipo/allotment

**Lot size:** enforced in the apply form — "Ensure the quantity selected is a multiple of the lot size." Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/how-to-invest-in-ipo

**GMP (Grey Market Premium): NOT displayed on Groww's own IPO listing/allotment pages** as fetched (open, closed and allotment tables show issue price, subscription, dates — no GMP column). Groww publishes educational GMP content at https://groww.in/p/what-is-grey-market but no GMP figure was visible on its IPO dashboard. **Treat "Groww shows GMP in the IPO section" as UNVERIFIED.**

### 5.3 Apply flow (verified step-by-step)
Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/how-to-invest-in-ipo

1. Tap the **'Stocks' tab** at the bottom.
2. Scroll down to the **IPO** button and tap it.
3. Select the IPO from the list of **open IPOs**.
4. **Enter the bid amount and continue.** Each IPO has a minimum bid amount that must be blocked.
5. Ensure the **quantity selected is a multiple of the lot size**.
6. Optionally modify the bid price by ticking **'At cutoff price'** and entering the amount manually.
7. **Enter your UPI ID** and proceed (format like `rahul@oksbi` / `091654301@ybl`).
8. Tap **'Apply for IPO'**.
9. Within an hour or two you receive a **UPI mandate request** in your UPI app → **approve the payment** (this blocks the amount).
10. All further status updates appear on the same IPO page in the Groww app.

**Payment rails (verified):**
- **UPI mandate** — the default; use any supported UPI app; accept the mandate to confirm.
- **ASBA via Netbanking** — log in to your bank's netbanking and apply using your **Groww Demat account number**.
- **You CANNOT use Groww Balance for IPO application** — regulatory restriction; payment must come from the linked bank account and the amount is blocked until allotment. Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/can-i-use-my-groww-balance-or-net-banking-for-ipo-application
- Groww also supports **applying through Groww UPI** (added in the Oct 2024 update). Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

**Unblocking if you cancel the mandate:** amount is usually unblocked within **3–10 working days after allotment**; Groww does not itself handle blocking/unblocking (done by the bank/UPI). Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/discoverable/i-accepted-the-upi-mandate-request-but-now-i-have-cancelled-my-order--when-will-the-amount-be-unblocked--45

### 5.4 How allotted / rejected status is shown
- Status updates appear **on the same IPO page in the Groww app** ("You'll get all further updates on the Groww app on the same IPO page").
- Status refresh can lag: "The status update after a successful mandate approval sometimes takes longer than usual to reflect on the app especially in case of a popular IPO." Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/my-ipo-application-status-is-not-updated-on-groww
- Dedicated **Allotment** page with a **per-company "Check" link** to the registrar's allotment-status page (this is where the definitive allotted/not-allotted result is published). Source: https://groww.in/ipo/allotment

---

## 6. PORTFOLIO & ORDERS

### 6.1 Tabs Groww shows
Verified tab labels/hierarchy across help + update pages:
- **Stocks section tabs:** `Holdings` · `Positions` · `Orders` (incl. a `GTT Orders` sub-section) · `Watchlist(s)`.
  Sources: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/where-can-i-see-my-gtt-orders---48 ; https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-or-cancel-my-order--22 ; https://groww.in/help/stocks
- **F&O section tabs:** `Positions` (with "Adjust Position") · `Orders` (with `GTT - Equity`, `OCO & GTT - F&O`) · `Explore` · `Terminal`.
  Sources: https://groww.in/updates/fno-position-adjustment-on-groww ; https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-do-i-modify---cancel-my-gtt-order---35
- **Mutual Funds section tabs:** `Dashboard` (holdings) · `SIPs` · `Explore`.
  Sources: https://groww.in/help/mutual-funds/order/how-do-i-check-my-sips--44 ; https://groww.in/help/mutual-funds/order/how-to-withdraw-redeem-4
- **Profile:** `Orders`, `Reports`, `Account Details`, `Bank details and autopay`, `Nominee Details`, `Stock, F&O Balance`, `Settings/Manage notifications`, `DP`.
  Sources: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-or-cancel-my-order--22 ; https://groww.in/help/my-account/ma-others/where-can-i-get-the-profit-loss-statement-for-tax ; https://groww.in/help/complete-setup/completesetupfaq/how-to-add-nominee-on-groww--43 ; https://groww.in/updates/notification-management-on-groww

### 6.2 Fields on each holding row
Verified holding-level fields visible in Groww's own dashboard deliverables:
- Quantity, average buy price, **current value**, **invested value**, **overall P&L (₹ and %)**, day change, and net-worth roll-up.
- Holdings-level performance data: **returns, allocation, risk, dividends and XIRR** ("Get insights on your investing or trading portfolio's performance, allocation, risk, dividends & XIRR with Portfolio Analysis"). Source: Play listing.
- **Pledged** quantity/status and pledge haircut visibility (pledge unlock up to 90% of holdings value). Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- **Broker segregation** in the holdings view for externally-tracked demat accounts ("toggle between broker-wise segregated view"). Source: https://groww.in/updates/groww-stocks-track
> Exact label-by-label field list of the holdings row was not captured verbatim from a primary page → treat the precise column set as **partially unverified**.

### 6.3 Positions tab
- Shows **open positions** with price, quantity, entry point and live P&L.
- Open **intraday** positions can be tapped → **"Add Stoploss/Target"** → set SL and TGT → confirm; you also see **estimated P&L for both legs**.
- Positions reachable via **"View Chart"** → "Add SL/TGT" on the chart.
- F&O positions: tap → **"Adjust Position"** → drag-and-drop grid of contracts filtered by expiry and strike → review summary → "Exit Positions and Place Orders".
- Options-chain overlay: **positions and returns are visible directly on the option chain** (web).
- Tracking SL/TGT: Positions tab → tap the intraday stock → see active Target and Stoploss levels.
Sources: https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday ; https://groww.in/updates/fno-position-adjustment-on-groww ; https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

### 6.4 Orders tab (statuses & grouping)
- **Grouping:** Equity orders vs **GTT Orders** (separate section; also split as `GTT - Equity` and `OCO & GTT - F&O` under Profile → Orders). Sources: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/where-can-i-see-my-gtt-orders---48 ; .../how-do-i-modify---cancel-my-gtt-order---35
- **Statuses referenced in verification:** `Open` / `Pending`, `Executed`, `Rejected`, `Failed`, `Cancelled`, `Triggered-Activated` (GTT), plus **1-click Retry** for rejected and failed orders from order details.
  Sources: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/where-can-i-see-my-gtt-orders---48 ; https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68 ; https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- GTT visibility: active GTTs under GTT Orders; once triggered and placed on exchange they can be tracked under Open Orders.

### 6.5 "Investment" / P&L views
- **Stocks P&L** — in-app view (no download needed) + downloadable; accessed Profile → Reports → Profit & Loss → **Stocks P&L** → pick FY or date range → View. Source: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/discoverable/how-can-i-access-my-stocks-p&l-report
- **F&O P&L Dashboard** (launched Jul 2026) — interactive **day-level P&L chart** (move across the chart to see P&L at any point in the session and map it to orders), **P&L summary** (Net P&L, Realised P&L, Charges), **monthly/quarterly/yearly comparison** with a colour-coded monthly performance view, **order-level trade insights** (contracts traded, quantities, trade-wise P&L), **downloadable reports**, and **separate tracking for Equity F&O vs Commodities**. Access: Profile → Reports → Profit & Loss → F&O P&L → choose segment & duration. Source: https://groww.in/updates/fno-pnl-dashboard-groww
- **MTF P&L** tracking is called out on the Play listing ("Track MTF P&L with ease").
- **Portfolio Analysis** — performance, allocation, risk, dividends, XIRR (Play listing).

### 6.6 Comparison / benchmark widget
- **Funds:** fund page has a **"Compare similar funds"** widget and a **category-average benchmark row** plus **category rank**; explicit Compare Funds tool at https://groww.in/mutual-funds/compare. Sources: https://groww.in/mutual-funds/groww-multicap-fund-direct-growth ; https://groww.in/
- **Stocks portfolio:** Groww states Portfolio Analysis gives performance vs **benchmark** for the investing/trading portfolio (Play listing). Precise benchmark-index selector for the holdings screen is **unverified**.
- **Stocks Track:** unified net worth combining Groww + external demat holdings, with broker-wise split. Source: https://groww.in/updates/groww-stocks-track

---

## 7. REPORTS & MONEY MOVEMENT

### 7.1 Every report Groww provides (verified)

| Report | Where it lives | Steps | Source |
|---|---|---|---|
| **Stocks P&L** | Profile → Reports → Profit & Loss → Stocks P&L | pick FY or date range → View (in-app or download) | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/discoverable/how-can-i-access-my-stocks-p&l-report |
| **F&O P&L (dashboard)** | Profile → Reports → Profit & Loss → F&O P&L | select segment (Equity F&O / Commodities) + duration (daily/monthly/quarterly/FY) → View; downloadable | https://groww.in/updates/fno-pnl-dashboard-groww |
| **Profit/Loss statement for tax** | Profile → Reports → Profit & Loss (stocks or F&O) | pick FY or date range → View | https://groww.in/help/my-account/ma-others/where-can-i-get-the-profit-loss-statement-for-tax |
| **Stocks Capital Gains / Tax P&L** | Profile → Reports → Tax → Stocks–Capital gain | pick FY → View. Splits realised trades into **Intraday / Short Term (<1 yr) / Long Term (≥1 yr)** incl. charges | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-reports/what-is-a-capital-gain-or-tax-p-l-report--20 |
| **Transaction history / trade book** | Profile → Orders / Reports (trade book) | **partially verified** — Groww's F&O page references "Review trades, contract notes, charges"; exact ledger/trade-book menu path not captured verbatim → **unverified at path level** | https://groww.in/futures-and-options |
| **Contract notes** | Listed under "Reports & history — Review trades, contract notes, charges, and performance over time" | **path-level unverified** | https://groww.in/futures-and-options |
| **Ledger** | Groww operates its own back office ("served in-house from our back office") and supports statement requests; **ledger path unverified** | — | https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more ; https://groww.in/pricing |
| **Holding statement / periodic statement** | Pricing lists "Periodic/Adhoc Statement Request — Email: Free, Physical: ₹10 per page" | request-based | https://groww.in/pricing |
| **Capital gains statement (Mutual Funds)** | You → **SIP & Reports** → Capital gains (per Groww blog) | **blog-sourced (2024)** | https://groww.in/blog/how-to-get-capital-gains-statement-for-mutual-fund-investments |
| **Charges breakdown** | Per-order charges viewable in reports; brokerage calculator | — | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-are-intraday-charges ; https://groww.in/calculators/brokerage-calculator |

**Scale evidence:** across one tax season Groww served **6 million report downloads in-house**. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

### 7.2 Add Money flow (verified step-by-step)
Source: https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13
1. Go to your **profile** section and tap **'Stock, F&O Balance'**.
2. Tap **'Add Money'**.
3. Enter the amount.
4. Choose payment method (default shown; tap **'More payment options'** to choose): **Net banking · UPI (GPay, PhonePe, BHIM etc.) · Bank transfer (IMPS/NEFT/RTGS)**.
5. Tap the **'Add Money'** button.
**Timings:** UPI / Net Banking / RTGS-IMPS credit **instantly** to Groww Balance; **NEFT can take up to 1 hour**.
**Known failure cause:** bank account selected on the Add Money screen must match the one in the UPI app; wrong UPI PIN also fails. Source: https://groww.in/help/my-account/payments/i-am-unable-to-add-money-to-my-groww-balance-via-upi--90

### 7.3 Withdraw flow (verified step-by-step)
Source: https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2
1. Go to the **'Profile'** section.
2. Tap **'Stocks, F&O balance'**.
3. Tap **'Withdraw'**.
4. Enter the amount you want to withdraw.
5. If multiple bank accounts are registered, **choose the bank account** on the withdrawal screen.
6. Tap **'Withdraw'** to complete the request.
**Timings (verified, with a documented discrepancy between two help pages):**
- Help page A: instant withdrawal available **9:30 AM – 6 PM if amount < ₹2 lakh**; above ₹2 lakh takes up to 24 hours; overall "it may take up to 1 business day". (https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2)
- Help page B: **< ₹1 lakh** requested **9:30 AM – 4:00 PM on a business day (Mon–Fri)** → credited instantly; **> ₹1 lakh** → usually processed within 24 hours. (https://groww.in/help/payments-&-withdrawals/payments/money-has-been-deducted-from-my-groww-balance-but-i-havent-received-it-in-my-bank-account-2)
- ✓ These two pages disagree on the threshold/time window — **flagging as an inconsistency in Groww's own documentation**.

### 7.4 Bank account management
- **Multiple bank accounts** can be registered with Groww; the withdrawal screen lets you pick one. Source: https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2
- **Add / change bank account + autopay:** Profile → **'Bank details and autopay'** → add a bank account. Source: https://groww.in/help/onboarding/discoverable/i-am-unable-to-proceed-with-aadhaar-esign--what-should-i-do--48
- **Change the bank account linked to MF folios directly on Groww** (rolled out to simplify redemption when an old bank account is closed/inactive). Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- **DDPI** (Demat Debit and Pledge Instruction) — a digital POA that removes the daily **TPIN/EDIS** authorisation when selling; charge **₹100 + GST**. Sources: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more ; https://groww.in/pricing

---

## 8. ALERTS, WATCHLIST & DISCOVERY

### 8.1 Watchlists
- Limit was raised **from 5 to 10 watchlists** (Oct 2024 update, responding directly to user requests). Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- Watchlists are **connected across touchpoints** ("Keep your market watchlists accessible across Groww trading touchpoints"). Source: https://groww.in/futures-and-options
- Adding a stock to a watchlist: "Add your favorite stocks to the Groww watchlist. Tap on the 'Buy' option from the order placement window." Source: https://www.investorgain.com/faq/how-to-buy-shares-on-groww-app/10752/ (secondary)
- Maximum number of **stocks per watchlist** is **unverified**.

### 8.2 Price alerts
- Groww pushes **price alerts when stocks in your portfolio/watchlist move up/down by 5%**. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- The Play listing says users can **"Set alerts to track stock price movements"** — i.e. user-configured alerts exist; the exact alert-creation UI (custom %/price thresholds) is **unverified**.
- **Notification Management** (per-product on/off toggles): Profile (top-right) → **Settings (gear)** → **Manage notifications** → toggle per product category. Changes can take up to 24 hours to reflect. Source: https://groww.in/updates/notification-management-on-groww
- Notification categories Groww sends: price alerts (±5%), corporate **events** (dividends, splits, rights), **technical/fundamental insights** (above/below 50/100/150/200 DMA, upper/lower circuit, 52W high/low), **news summaries** (incl. exchange filings). Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

### 8.3 Collections / curated lists
- **Stocks:** Most Bought Stocks on Groww (https://groww.in/stocks/most-bought-stocks-on-groww), Intraday top performers (https://groww.in/stocks/intraday), Stock Screener (https://groww.in/stocks/filter), Stock Events calendar (https://groww.in/stocks/calendar), Indices (https://groww.in/indices).
- **Mutual Funds:** curated categories (e.g. Best International Mutual Funds, https://groww.in/mutual-funds/category/best-international-mutual-funds), MF screener (https://groww.in/mutual-funds/filter), NFOs (https://groww.in/nfo).
- **Bonds:** listed bond discovery by YTM / rating / tenure, plus "Open" Bond IPO tab (https://groww.in/bonds).
- Sources: https://groww.in/sitemap ; https://groww.in/bonds

### 8.4 Screener
- **Stock Screener** — "Filter based on RSI, PE ratio and more" → https://groww.in/stocks/filter; an **Intraday Screener** is called out on the Play listing.
- **MF screener** — "Filter funds based on risk, fund size and more" → https://groww.in/mutual-funds/filter.
- **ETF screener** → https://groww.in/etfs.
- Source: https://groww.in/

### 8.5 News feed
- **Groww Digest** (https://groww.in/digest) — a daily/weekly market digest containing: index moves with top gainers/losers tables, a market commentary paragraph, global-market recap, top news items (macro + company-level), an **IPO Corner** with day-wise subscription multiples (overall + retail), stock-specific updates, "Word of the Day", a "6 Day Course" educational series, a featured Q&A, USD-INR rate, long-term (20-year) return context, and a "Did you like this edition?" feedback widget. Source: https://groww.in/digest
- **Per-stock news** surfaces in the app and via push: "Every time there's fresh news on your holdings, it will show up right here." Source: App Store listing, https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703
- **Share Market Today** — live news updates page: https://groww.in/share-market-today

### 8.6 "Most bought / most held" data
- **Most Bought Stocks on Groww** page exists with live price, 1-day low & high: https://groww.in/stocks/most-bought-stocks-on-groww
- A **"most held"** view is **unverified** — no primary page found during this research (only "Most Bought").

### 8.7 Sector / market-mover pages
- **Gainers/losers** visible in Groww Digest (Top Gainers / Top Losers, Nifty 50). Source: https://groww.in/digest
- **Intraday** page: "Monitor top intraday performers in real time" → https://groww.in/stocks/intraday
- **Indices** page (Indian + global indices incl. NIFTY, SENSEX, NASDAQ, GIFT NIFTY, NIFTY MIDCAP, NIFTY NEXT 50): https://groww.in/indices (and Play listing).
- Sector-level browsable pages: **unverified** as a distinct section.

### 8.8 Community / social features
- **Ask-Invest-Know-Groww (AIKG)** offline investor meetups — Groww ran its 150th AIKG event in Bengaluru. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- **WhatsApp support groups** referenced by a customer testimonial ("your Whatsapp group team helps a lot in making the right choices"). Source: https://groww.in/testimonials
- **Social channels:** X/Twitter (@_groww), Instagram (groww_official), Facebook (growwapp), LinkedIn, YouTube. Source: https://groww.in/help
- **No in-app social/community feed or copy-trading feature was found** → treat in-app social trading as **not offered / unverified**.
- **Testimonials wall** at https://groww.in/testimonials (user-submitted, curated by Groww).

---

## 9. ACCOUNT, KYC & SUPPORT

### 9.1 Onboarding / KYC steps a new user goes through
Verified from https://groww.in/open-demat-account and help-centre pages:

**Documents required — exactly 4:** PAN Card · Aadhaar Card · Bank account details · E-Signature. Source: https://groww.in/open-demat-account

**Flow (4 easy steps, 100% paperless):**
1. Sign up with **mobile number + OTP**; then **email + OTP**. (Secondary confirmation: https://hyperverge.co/blog/how-to-activate-kyc-in-groww-app/ — 2025 blog, used only for step ordering)
2. Enter **PAN** details (name must match PAN).
3. **Aadhaar-based KYC** — "Complete your KYC digitally in minutes with Aadhaar OTP. No physical documents or branch visits required." Groww also offers a **DigiLocker** route which auto-verifies KYC documents. Sources: https://groww.in/open-demat-account ; https://groww.in/blog/digilocker-and-esign-a-boon-for-indian-fintech (2023 blog)
4. **Bank verification** — add bank account; if Aadhaar e-sign fails with "Your primary bank account not verified", go back → Profile (top-right) → **'Bank details and autopay'** → add a different bank account and retry. Source: https://groww.in/help/onboarding/discoverable/i-am-unable-to-proceed-with-aadhaar-esign--what-should-i-do--48
5. **e-Sign** the account-opening form (Aadhaar e-sign).
6. **Activation:** "If you have already uploaded your documents and completed the e-Sign, your account will be activated **within 2 working days**." Source: https://groww.in/help/complete-setup/completesetupfaq/how-to-complete-my-account-creation

**Entity types supported:** Individual, **HUF, Corporate/Company, Trust** ("Groww supports all entity types - individual, HUF, corporate, and more"). Source: https://groww.in/open-demat-account

**MF-specific KYC statuses (verified):** `validated` (KYC done via Aadhaar/DigiLocker — full investing), `registered` (KYC via driving licence/voter ID/passport → can only transact in existing funds; must redo KYC with Aadhaar to be "validated"), `on hold` (cannot invest; can redeem under due diligence). Source: https://groww.in/p/mutual-fund-kyc
- **NRI note:** NRIs can invest in any fund house even without Aadhaar; passport/PIO/OCI card + overseas address proof required. Some App Store reviews report that **NRI investing was not supported** in the app at the time of the review — Groww's own MF-KYC page says NRIs are supported for funds, and the pricing page lists NRI brokerage rates. Treat **app-level NRI onboarding** as **partially verified / inconsistent**.

**Segments activated:** Groww's SEBI registration covers **Cash & F&O (Equity & Commodity Derivatives)**; exchange memberships NSE (90187), BSE (6699), MCX (57420); segments listed as "Cash & FNO (Equity & Commodity Derivatives)". Source: Google Play listing + https://groww.in/pricing. Equity and F&O/Commodity activation is therefore part of the standard account; **commodity (MCX) activation** is explicitly in the member-code list. A **separate explicit "activate segment" self-serve screen** was not verified on a primary help page → **unverified**.

### 9.2 Profile / Settings options (verified)
| Option | Path | Source |
|---|---|---|
| **Nominee** (up to **3 nominees**; guardian details if nominee is a minor) | Home → profile icon (top-right) → **Account Details** → scroll to **Nominee Details** → **Declare Nominee** → fill details → submit → **finish e-sign** | https://groww.in/help/complete-setup/completesetupfaq/how-to-add-nominee-on-groww--43 |
| **Bank accounts & autopay** | Profile (top-right) → **Bank details and autopay** | https://groww.in/help/onboarding/discoverable/i-am-unable-to-proceed-with-aadhaar-esign--what-should-i-do--48 |
| **DP / DP ID change** | "Now you can change your DP in the 'You' section"; **DP ID visible** via Account Details ("Where can I see my DP ID, demat details…" FAQ) | https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more ; https://groww.in/open-demat-account |
| **Notification management** | Profile → Settings (gear) → Manage notifications | https://groww.in/updates/notification-management-on-groww |
| **Reports** | Profile → Reports | https://groww.in/help/my-account/ma-others/where-can-i-get-the-profit-loss-statement-for-tax |
| **Orders / GTT** | Profile → Orders → GTT - Equity / OCO & GTT - F&O | https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-do-i-modify---cancel-my-gtt-order---35 |
| **Stocks, F&O Balance** (add/withdraw) | Profile → Stocks, F&O Balance | https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13 |
| **F&O Pause** (DIY pause F&O while keeping stocks/MF on) | In-app | https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more |
| **KYC modification request** | Request-based, **₹50 (incl. GST)** | https://groww.in/pricing |

### 9.3 Support
- **Help centre:** https://groww.in/help (hub) with a Stocks sub-hub at https://groww.in/help/stocks organised into: Stocks & Intraday, Holdings-Positions, Futures & Options, High-risk markets, IPO (Status/Refund/UPI Mandate), Reports (P&L/Trades/Charges), Margin, Charges, Demat Account (Demat details/BOID/TPIN), Corporate Action, Pledge, SGB, ETF NFO, Commodities.
- **Ticket raising:** via the in-app **'Contact Us'** button below help articles (e.g. "please click 'Contact Us' below to raise a ticket"), and by email to **support@groww.in** (with the generated ticket ID). Sources: https://groww.in/help/payments-&-withdrawals/payments/money-has-been-deducted-from-my-groww-balance-but-i-havent-received-it-in-my-bank-account-2 ; Google Play listing.
- **Customer care:** 24×7 support; care number **080-68249147 / 080-68249213**; general **+91-9108800000 / +91-9108800604**; **support@groww.in**. Sources: https://groww.in/blog/groww-helpline-number (Jan 2025 blog) ; https://groww.in/help/loans/credit-others/what-is-the-process-for-escalating-a-complaint-issue--95
- **Grievance escalation ladder (verified, from Groww's own escalation matrix + help page):**
  - **Level 1 (Queries):** Groww app / online. First response **2 business days**; full resolution **4 business days**.
  - **Level 2 (Complaints):** Groww's **Nodal Officer — Dharmesh Palan**, email **grievances@groww.in**, care **080-45860196**. Resolution **4 business days**.
  - **Level 3:** the lending partner's Nodal Officer (for credit products) — ABFL / IDFC / Credit Saison / Fibe / Groww Creditserv named contacts.
  Sources: https://groww.in/help/loans/credit-others/what-is-the-process-for-escalating-a-complaint-issue--95 ; Groww Customer care & Grievance Escalation Matrix PDF: https://cms-resources.groww.in/uploads/Customer_care_and_Grievance_Escalation_matrix_9c9e46a161.pdf
- **SEBI SCORES escalation (verified):** register on the SCORES portal (https://scores.sebi.gov.in/); mandatory details Name, PAN, Address, Mobile, Email. Groww's own site publishes this procedure and the Risk Disclosure Document reference for Stock Broking/DP grievances. Source: https://groww.in/sitemap

---

## 10. WHAT GROWW DOES THAT USERS CALL OUT

Grouped by mechanic. Sources are Groww's own product pages/updates (which state user demand) plus app-store reviews, Reddit and Groww's testimonial wall.

### 10.1 GTT for long-term / hands-off orders
- **The mechanic:** GTT lets you set a trigger price (market or limit) and walk away; valid up to **1 year** for stocks and until expiry for F&O. Groww calls it "useful for trades that are planned in advance… without the need to monitor markets continuously." Sources: https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39 ; https://groww.in/updates/bracket-orders-on-groww
- **User signal:** Groww's own Facebook page promotes GTT as the answer to "Har waqt chart dekhne ki…" (not having to watch charts all the time). Source: https://www.facebook.com/growwapp/videos/trade-like-experts-on-groww/3520164544947170/
- Groww's GTT help video and dedicated help articles imply GTT is one of the most-queried features. Source: https://www.youtube.com/watch?v=JgKd86T6IC8

### 10.2 Price alerts
- Groww pushes automatic **±5% price alerts** on portfolio/watchlist stocks plus DMA/circuit/52-week-high-low technical alerts and corporate-event alerts. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- The Play listing markets "Set alerts to track stock price movements for trading & investing decisions" as a top reason users choose Groww. Source: https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_US
- **Notification Management** was shipped specifically because users said too many alerts were overwhelming — Groww's post: "we understand that while timely updates are crucial, too many alerts can be overwhelming." Source: https://groww.in/updates/notification-management-on-groww

### 10.3 Simple SIP
- "One out of four new SIPs in India happen on Groww"; Groww crossed **1 crore SIPs** on the platform; minimum SIP **₹500/month**. Sources: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more ; https://groww.in/mutual-funds/start-sip
- Users repeatedly cite the simple SIP rail: "Starting SIPs and investing in stocks was smooth, and tracking my portfolio has been very convenient… I have been able to accumulate funds consistently." (5★ App Store review). Source: https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703?see-all=reviews&platform=iphone
- Groww's own value props tied to SIP: "invest as low as ₹500/month", auto-debit, rupee-cost averaging. Source: https://groww.in/mutual-funds/start-sip

### 10.4 Fast, paperless KYC / onboarding
- "Complete your KYC digitally in minutes with Aadhaar OTP. No physical documents or branch visits required." Activation within **2 working days** after docs + e-sign. Sources: https://groww.in/open-demat-account ; https://groww.in/help/complete-setup/completesetupfaq/how-to-complete-my-account-creation
- Testimonial: "It took me 5 mins to set up and 10 mins to find the funds that suited my need and invest." Source: https://groww.in/testimonials
- Review: "from KYC to making your first investment, the whole process is smooth and doesn't feel overwhelming." Source: App Store reviews page (above).
- **Counter-signal:** an App Store reviewer reports being locked out for over a week during **ReKYC** despite the app promising "1–2 days", and a reviewer reports **NRI KYC dead-ends** after all data was collected with no cancel/delete option. Sources: same App Store reviews page.

### 10.5 Stocks + MF (+ IPO, ETF, F&O) in one app
- Play listing: "Groww is your one app to invest & trade in: Stocks, Mutual Funds, F&O, Gold and Silver, MTF, Commodity Derivatives, ETFs, IPO, Bonds, API Trading."
- Review: "everything from stocks, mutual funds, ETFs, IPOs, and F&O is available on one platform… transparent pricing with zero AMC, fast order execution, and detailed stock & mutual fund information." Source: App Store reviews page.
- Testimonial: "I love that there are so many options for Mutual Funds. The data and analysis really helped me choose the best fund." Source: https://groww.in/testimonials

### 10.6 Clean P&L / reports
- Groww moved Stocks P&L **in-app** ("you don't need to download the report if you don't want to") and rebuilt the reports section; 6 million reports downloaded in one tax season. Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- The **F&O P&L Dashboard** (day-level P&L chart, net/realised P&L, charges, month/quarter/FY comparison, order-level insights) was built explicitly because "trading is emotional" and users want to "understand what went wrong." Source: https://groww.in/updates/fno-pnl-dashboard-groww
- Review: "tracking my portfolio has been very convenient." Source: App Store reviews page.

### 10.7 Zero AMC / zero account-opening fee / transparent pricing
- **₹0** account opening and **₹0** maintenance charge; "0 AMC & no hidden charges." Sources: https://groww.in/pricing ; https://groww.in/open-demat-account ; Play listing.
- Review: "transparent pricing with zero AMC." Source: App Store reviews page.
- Testimonial: "Groww is transparent and data-based. It's a lot easier to trust Groww." Source: https://groww.in/testimonials

### 10.8 Risk-control features users rely on
- **OCO with near-zero slippage stop-loss execution**, **SL Entry**, **Bracket Orders**, **Stoploss/Target on open intraday positions**, **SafeGuard** (stops F&O if losses exceed safe limits), **F&O Pause** (DIY break). Sources: https://groww.in/updates/bracket-orders-on-groww ; https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday ; https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more
- Community signal that Groww "nudges" rather than gamifies: SafeGuard + F&O Pause are marketed as investor-protection, and Groww's update text says "not everyone should trade." Same source.

### 10.9 More watchlists (explicit user demand → shipped)
- "We saw many comments in our last update about increasing the number of watchlists. Until recently, we supported only 5 watchlists (for some reason, we thought 5 would be enough, but we were wrong). And now we have increased it to 10." Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

### 10.10 Pledge for extra margin
- Pledge eligible holdings to unlock **up to 90% of holdings value**; **SGBs can be pledged**; pledge/unpledge ₹20 per ISIN; pledge invocation ₹20. Sources: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more ; https://groww.in/pricing
- Play listing markets "Pledge your stock holdings to boost your margin and take larger positions."

### 10.11 DDPI — sell without daily TPIN
- "With DDPI now you can sell anything seamlessly… DDPI is a digital POA that will take away the need for doing a daily TPIN authorization. This makes the sell journey seamless." Source: https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more

### 10.12 Consolidated portfolio across brokers (Stocks Track)
- Users complained about "app switching" and "fragmented portfolio views"; Groww shipped **Stocks Track** via the RBI Account Aggregator framework (no password sharing, consent-based, auto-sync daily). Sources: https://groww.in/updates/groww-stocks-track
- User quotes embedded in the launch post: *"I moved to Groww but my old investments are stuck elsewhere. I can't see my complete portfolio performance."* and *"I use different platforms for different strategies… but I can never see the full picture."* Source: same.

### 10.13 What users complain about (for balance)
- **App/order speed & lag**: "the app can lag a bit during peak market hours"; "It takes an unacceptably long time to execute orders"; "Takes almost a minute to open up". Sources: https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703?see-all=reviews&platform=iphone
- **Position exit glitches**: a reviewer reports a booked profit of ₹240 collapsing to ₹23 because the exit order would not go through.
- **Support quality**: multiple reviewers report template/loop responses and slow escalation; one reports a lost ₹5,000 withdrawal dispute. (Same source.) This is a recurring theme across the App Store review page.
- **Advanced tools gap**: "I wish they had more advanced tools for experienced investors."
- **Community chatter (secondary):** r/IndianStreetBets "Why does everyone use groww?" thread notes "trades often fail to execute" while acknowledging app popularity — https://www.reddit.com/r/IndianStreetBets/comments/1cpo979/why_does_everyone_use_groww/ ; r/MutualfundsIndia "Pause SIP on Groww" — https://www.reddit.com/r/MutualfundsIndia/comments/1kle1z6/pause_sip_on_groww/ (2025) ; r/IndianStockMarket on Groww US Stocks — https://www.reddit.com/r/IndianStockMarket/comments/1uoob7f/groww_soon_to_start_with_us_stocks/ (2026-07)

**Interpretation caution:** Groww's own testimonials page and Play listing are marketing surfaces; the App Store reviews page surfaced the most candour and is the most useful single source for what actually goes wrong.

---

## 11. FREE-VS-PAID / PRICING MODEL

Primary source for everything in this section unless otherwise stated: **https://groww.in/pricing** (Tariff Rates page), corroborated by help-centre pricing articles.

### 11.1 Headline pricing (verified)
| Item | Charge |
|---|---|
| **Account opening (trading + demat)** | **₹0** |
| **Account maintenance / AMC** | **₹0** |
| **Equity brokerage (delivery AND intraday)** | **lower of ₹20 or 0.1% per executed order; minimum ₹5** |
| **F&O brokerage** | **flat ₹20 per order** |
| **Equity delivery brokerage regulatory cap** | cannot exceed **2.5%** of trade value (SEBI) |
| **MF plans** | Direct **and** Prime both available; **Prime = in line with regular plans** (only offered to NRIs per the pricing page) |
| **GST** | **18%** on brokerage, DP charges, exchange transaction charges, IPFT, SEBI turnover charges, DPC, DDPI charges, KYC modification charges, API charges and auto-square-off charges |

### 11.2 Statutory / regulatory charges — Equity (verified, from the pricing table)
| Charge | Intraday | Delivery |
|---|---|---|
| **STT** | 0.025% (SELL) | 0.1% (BUY & SELL) |
| **Stamp Duty** | 0.003% (BUY) | 0.015% (BUY) |
| **Exchange transaction charge** | NSE 0.00297% / BSE 0.00375% (buy & sell) | same |
| **SEBI turnover charge** | 0.0001% | 0.0001% |
| **Investor Protection Fund Trust charge** | NSE 0.0001% | NSE 0.0001% |

BSE equity exchange transaction charges (verified detail): **0.00345%** for all groups except R, SS, ST, ZP (1.0%) and X, XT, Z (0.1%); A, B, E, F, FC, G, GC, W, T = 0.00375%.

### 11.3 DP (Depository Participant) charges — per SELL transaction
| Item | Charge |
|---|---|
| **Delivery DP charge** | Depository: **₹3.5 (male)** / **₹3.25 (female)**; Groww: **₹16.5** → total **₹20.00 (male)** / **₹19.75 (female)** + GST |
| **If debit value < ₹100** | Groww waives its fee; you pay only **₹3.50 (male) / ₹3.25 (female)** |
| **Intraday DP charge** | **₹0** |

Note: Groww changed this from per-ISIN-per-day to **per sell transaction** effective the 21 June 2025 pricing update (secondary source: https://select.finology.in/articles/broker/groww-latest-fees-update-2025 — 2025-dated third-party article).

### 11.4 MTF costs (verified)
| Item | Charge |
|---|---|
| **MTF brokerage** | **0.1% per order** of order value |
| **MTF interest** | **14.95% p.a.** (i.e. **0.041% per day**) charged **only on the funded amount**; interest stops once the position is closed |
| **Intraday → MTF conversion** | MTF buy order charges applied — 0.1% per order of order value |
| **MTF leverage** | up to **4X**; pay as little as **25%** upfront; available on a limited, exchange-governed stock list (https://groww.in/stocks/mtf/list) |

### 11.5 Penalties (verified)
| Penalty | Charge |
|---|---|
| **Auto square-off** of open intraday positions by the system | **₹50 per position** (+GST); note the help page says this applies if you don't square off before **3:20 PM** |
| **Auction** (unable to deliver a stock not in demat) | as per actual exchange penalty |
| **Delayed Payment Charges (DPC)** | **0.05% per day** (incl. GST), simple interest, compounded monthly |
| **Pledge / unpledge** | ₹20 per ISIN |
| **Pledge invocation** | ₹20 |

### 11.6 Other charges (verified, verbatim from pricing page)
| Item | Charge |
|---|---|
| Demat / Remat | ₹150 per certification + courier |
| Failed Demat transactions | ₹50 per ISIN |
| Periodic / Adhoc statement request | Email: **Free**; Physical: **₹10 per page** |
| KYC modification request | **₹50** (incl. GST) |
| KRA upload / download | ₹50 |
| Delivery Instruction Slip | First (10 leaves) Free; additional (10 leaves) ₹100 + courier |
| Physical CMR (Client Master Report) | ₹20 + courier |
| Courier charges | Max of ₹100 or actual |
| Inter-settlement charges | Depository ₹3.5 + Groww ₹16.5 + GST |
| Restat-SOA / Redemption | ₹20 + GST |
| **DDPI charges** | **₹100 + GST** |
| Buyback charges | Brokerage ₹20 per executed transaction; DP charges ₹20 per company (₹0 < ₹100 debit value) |
| OFS charges | Brokerage ₹20 per executed transaction |
| **UPI Mandate balance users** | Equity brokerage is **1% of order value, NO maximum cap** — an important edge case (much more expensive than normal equity brokerage) |

### 11.7 NRI pricing (verified)
- Equity (Delivery & Intraday) brokerage: **0.10% with min ₹100 per order** (i.e. **no ₹20 cap for NRIs**) · **F&O: ₹50/order**.

### 11.8 Mutual fund costs (verified)
- Groww charges **no commission on Direct plans** — "Invest in direct mutual funds with 0% commission" / "direct mutual funds at zero charges". Sources: https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_US ; https://groww.in/
- **The real cost in MF is the AMC's expense ratio, not Groww's fee** — expense ratios are published per fund on Groww fund pages (e.g. Groww Liquid Fund Direct 0.11%; Groww Multicap Direct 1.06%; Groww Gold ETF FoF Direct 0.14%). Source: https://groww.in/mutual-funds/amc/groww-mutual-funds
- **Stamp duty on MF investment: 0.005%** (since 1 July 2020). Source: https://groww.in/mutual-funds/groww-multicap-fund-direct-growth
- **Exit loads** are fund-specific and disclosed on each fund page (e.g. "1% if redeemed within 1 year"; Groww Liquid has a graded 0.0070%→0.0045% day-1-to-day-6 scale). Same source.

### 11.9 Bonds (verified)
- Minimum investment **₹10,000** (₹1,000 per unit) on Bond IPOs; apply **10:00 AM – 5:00 PM on market days**; allotment on availability. Source: https://groww.in/updates/bond-ipos-on-groww
- Bond brokerage per executed transaction is not separately published on the pricing page → **unverified**.

### 11.10 Commodity / F&O segments
- The pricing page's "Equity" table covers intraday/delivery; commodity (MCX) brokerage specifics were **not separately itemised** on the pages fetched → **partially unverified**. Groww's commodity page promises "clear brokerage structure… statutory, exchange, and platform charges." Source: https://groww.in/commodities
- Brokerage Calculator: https://groww.in/calculators/brokerage-calculator

### 11.11 Free-vs-paid summary
| Free on Groww | Paid on Groww |
|---|---|
| Account opening ₹0 | Equity brokerage (min ₹5, cap ₹20 or 0.1%) |
| AMC / maintenance ₹0 | F&O brokerage (₹20/order) |
| Direct MF investing (0% commission) | MTF interest 14.95% p.a. + 0.1% brokerage |
| Stock/ETF/MF tracking & Screeners | Statutory charges (STT, stamp duty, exchanges, SEBI, IPFT, GST) |
| Price alerts, watchlists (10), Digest, calculators | DP charges on every sell (₹20 / ₹19.75) |
| Reports (Stocks P&L, F&O P&L, Tax P&L) | Auto square-off ₹50/position; DPC 0.05%/day |
| UPI/Netbanking/RGTS-IMPS deposits into Groww Balance | DDPI ₹100+GST; KYC modification ₹50; physical statements |

---

## SOURCES

**Groww primary — product & pricing**
1. https://groww.in/
2. https://groww.in/pricing
3. https://groww.in/sitemap
4. https://groww.in/stocks
5. https://groww.in/stocks/mtf
6. https://groww.in/stocks/mtf/list
7. https://groww.in/stocks/most-bought-stocks-on-groww
8. https://groww.in/stocks/filter
9. https://groww.in/stocks/intraday
10. https://groww.in/stocks/calendar
11. https://groww.in/futures-and-options
12. https://groww.in/options/nifty
13. https://groww.in/commodities
14. https://groww.in/charts
15. https://groww.in/trade-api
16. https://groww.in/indices
17. https://groww.in/available-for-pledge
18. https://groww.in/mutual-funds
19. https://groww.in/mutual-funds/start-sip
20. https://groww.in/mutual-funds/filter
21. https://groww.in/mutual-funds/compare
22. https://groww.in/mutual-funds/amc/groww-mutual-funds
23. https://groww.in/mutual-funds/amc
24. https://groww.in/mutual-funds/groww-multicap-fund-direct-growth
25. https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth
26. https://groww.in/mutual-funds/category/best-international-mutual-funds
27. https://groww.in/nfo
28. https://groww.in/etfs
29. https://groww.in/track
30. https://groww.in/ipo
31. https://groww.in/ipo/open
32. https://groww.in/ipo/closed
33. https://groww.in/ipo/upcoming
34. https://groww.in/ipo/subscription
35. https://groww.in/ipo/allotment
36. https://groww.in/bonds
37. https://groww.in/gold
38. https://groww.in/sovereign-gold-bonds
39. https://groww.in/pms
40. https://credit.groww.in/
41. https://groww.in/open-demat-account
42. https://groww.in/testimonials
43. https://groww.in/digest
44. https://groww.in/share-market-today
45. https://groww.in/help
46. https://groww.in/help/stocks
47. https://groww.in/p/mutual-fund-kyc
48. https://groww.in/calculators/sip-calculator
49. https://groww.in/calculators/swp-calculator
50. https://groww.in/calculators/margin-calculator
51. https://groww.in/calculators/brokerage-calculator
52. https://groww.in/p/what-is-grey-market
53. https://groww.in/login (used to confirm no public /us-stocks page — redirect)

**Groww primary — help centre (functional flows)**
54. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/what-is-gtt-39
55. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-to-place-a-gtt-order---66
56. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/where-can-i-see-my-gtt-orders---48
57. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-dashboard/how-do-i-modify---cancel-my-gtt-order---35
58. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-or-cancel-my-order--22
59. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/why-am-i-not-able-to-modify-my-order--68
60. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/how-can-i-modify-my-stoploss-order-to-market--17
61. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/order/when-will-i-get-my-profit-loss--45
62. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-fno/how-do-i-buy-sell-options-on-groww--76
63. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/how-to-invest-in-ipo
64. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/can-i-use-my-groww-balance-or-net-banking-for-ipo-application
65. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-ipo/my-ipo-application-status-is-not-updated-on-groww
66. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/discoverable/i-accepted-the-upi-mandate-request-but-now-i-have-cancelled-my-order--when-will-the-amount-be-unblocked--45
67. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/discoverable/how-can-i-access-my-stocks-p&l-report
68. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-reports/what-is-a-capital-gain-or-tax-p-l-report--20
69. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-demat-account/how-much-does-groww-charge-for-stocks-1
70. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-are-intraday-charges
71. https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-is-the-charge-for-buy-order-delivery
72. https://groww.in/help/payments-&-withdrawals/payments-charges/what-fees-does-groww-charge--58
73. https://groww.in/help/payments-&-withdrawals/deposit/how-do-i-add-transfer-money-to-groww-balance--13
74. https://groww.in/help/my-account/payments/how-do-i-withdraw-money-from-my-groww-account-2
75. https://groww.in/help/payments-&-withdrawals/payments/money-has-been-deducted-from-my-groww-balance-but-i-havent-received-it-in-my-bank-account-2
76. https://groww.in/help/my-account/payments/i-am-unable-to-add-money-to-my-groww-balance-via-upi--90
77. https://groww.in/help/my-account/ma-others/where-can-i-get-the-profit-loss-statement-for-tax
78. https://groww.in/help/my-account/searchable/how-to-call-groww-customer-care
79. https://groww.in/help/mutual-funds/mf-sip/how-to-start-a-sip-on-groww
80. https://groww.in/help/mutual-funds/order/can-i-pause-sip-for-next-month
81. https://groww.in/help/mutual-funds/discoverable/can-i-place-step-up-request-for-all-of-my-sips--35
82. https://groww.in/help/mutual-funds/order/how-to-withdraw-redeem-4
83. https://groww.in/help/mutual-funds/order/how-do-i-check-my-sips--44
84. https://groww.in/help/mutual-funds/order/can-i-cancel-my-purchase-order--11
85. https://groww.in/help/mutual-funds/mf-dashboard/how-do-i-import-my-external-mutual-fund-investments-1
86. https://groww.in/help/onboarding/discoverable/i-am-unable-to-proceed-with-aadhaar-esign--what-should-i-do--48
87. https://groww.in/help/complete-setup/completesetupfaq/how-to-complete-my-account-creation
88. https://groww.in/help/complete-setup/completesetupfaq/how-to-add-nominee-on-groww--43
89. https://groww.in/help/loans/credit-others/what-is-the-process-for-escalating-a-complaint-issue--95
90. https://cms-resources.groww.in/uploads/Customer_care_and_Grievance_Escalation_matrix_9c9e46a161.pdf

**Groww primary — official product announcements (groww.in/updates)**
91. https://groww.in/updates/bracket-orders-on-groww (Jan 2026)
92. https://groww.in/updates/fno-position-adjustment-on-groww (Jun 2025)
93. https://groww.in/updates/fno-pnl-dashboard-groww (Jul 2026)
94. https://groww.in/updates/introducing-stoploss-target-orders-on-groww-for-intraday (May 2025)
95. https://groww.in/updates/groww-stocks-track (Oct 2025)
96. https://groww.in/updates/groww-charts (Aug 2025)
97. https://groww.in/updates/notification-management-on-groww
98. https://groww.in/updates/bond-ipos-on-groww (Jul 2025)
99. https://groww.in/updates/updates-from-groww-group-more-watchlists-f-and-o-pause-sell-without-tpin-and-lots-more (Oct 2024) — CEO letter, richest single source on shipped features
100. https://groww.in/blog/new-features-update-alerts

**Groww primary — blog / explainers (used for mechanics, dates noted)**
101. https://groww.in/blog/types-of-stock-market-orders (Jun 2026)
102. https://groww.in/blog/how-to-place-stop-loss-order (Oct 2025)
103. https://groww.in/blog/how-to-edit-sip-on-groww
104. https://groww.in/blog/how-to-start-a-stp-and-swp-on-grow (May 2024 — STP/SWP web-only claim)
105. https://groww.in/blog/how-to-invest-in-us-stocks-from-india (Oct 2025)
106. https://groww.in/blog/groww-helpline-number (Jan 2025)
107. https://groww.in/blog/how-to-get-capital-gains-statement-for-mutual-fund-investments (Jul 2024)
108. https://groww.in/blog/digilocker-and-esign-a-boon-for-indian-fintech (Sep 2023)
109. https://groww.in/blog/faqs-about-investing-in-stocks-on-groww-answered

**Official app-store listings (primary)**
110. https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_US
111. https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703
112. https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703?see-all=reviews&platform=iphone

**Reputable secondary (2025–2026 dated)**
113. https://www.news18.com/business/markets/groww-receives-licence-to-offer-us-stock-trading-feature-currently-in-testing-phase-says-concall-update-ws-l-10213257.html (Jul 2026) — US Stocks licence + testing phase
114. https://www.livemint.com/money/personal-finance/want-to-invest-in-us-stocks-zerodha-groww-upstox-and-angel-one-get-key-approval-11781594712999.html (Jun 2026) — IFSCA/GIFT City approval with Zerodha/Upstox/Angel One
115. https://startup.economictimes.indiatimes.com/news/fintech/zerodha-groww-angel-one-upstox-approved-for-us-stock-trading/131789215 (Jun 2026) — active-user ranking (Groww 1.3 cr+ as of 31 May 2026)
116. https://www.newsbytesapp.com/news/business/groww-approved-to-offer-direct-us-stock-investing-to-indians/tldr (Jul 2026)
117. https://select.finology.in/articles/broker/groww-latest-fees-update-2025 (2025) — 21 Jun 2025 fee changes: min brokerage ₹2→₹5, DP per sell transaction, MTF flat 14.95% p.a.
118. https://select.finology.in/broker/groww — third-party broker comparison
119. https://www.reddit.com/r/IndianStreetBets/comments/1cpo979/why_does_everyone_use_groww/ (community sentiment)
120. https://www.reddit.com/r/MutualfundsIndia/comments/1kle1z6/pause_sip_on_groww/ (May 2025)
121. https://www.reddit.com/r/IndianStockMarket/comments/1uoob7f/groww_soon_to_start_with_us_stocks/ (Jul 2026)
122. https://www.reddit.com/r/personalfinanceindia/comments/1uw1ft9/corporate_bonds_on_groww_look_really_good_11/ (corporate bonds on Groww — community view)
123. https://www.reddit.com/r/IndianStockMarket/comments/1l9galg/groww_is_silently_locking_your_mutual_funds_check/ (MF units moved to Groww demat — community concern; Groww opt-out help page referenced)
124. https://www.trustpilot.com/review/groww.in (customer service reviews)
125. https://hyperverge.co/blog/how-to-activate-kyc-in-groww-app/ (2025 blog — used only for KYC step ordering, corroborating Groww's own page)
126. https://www.investorgain.com/faq/how-to-buy-shares-on-groww-app/10752/ (used only for the watchlist-add mechanic)
127. https://www.investorgain.com/ipo-investment/groww/47/ (Aug 2026 — IPO apply; notes users can place up to 3 IPO bids — **unverified against Groww primary**)
128. https://www.facebook.com/growwapp/videos/trade-like-experts-on-groww/3520164544947170/ (Groww official channel — GTT marketing)
129. https://www.facebook.com/growwapp/videos/invest-in-gold-silver-today/1234339568095211/ (Groww official channel — gold/silver ETFs)
130. https://www.linkedin.com/posts/niteshbuddhadev_groww-ipo-activity-7374291094202724352-CSaG (secondary — claims FD & insurance launched; **treated as unverified**)

**Groww pages that returned 404 / not found (negative evidence, verified 12 Sep 2026)**
131. https://groww.in/fixed-deposits → 404 (no FD product)
132. https://groww.in/mtf → 404 (correct path is /stocks/mtf)
133. https://groww.in/amc → 404 (correct path is /mutual-funds/amc)
134. https://groww.in/p/nps-national-pension-system → 404 (no NPS product page; only a calculator)
135. https://groww.in/us-stocks → redirects to login (no public product page)

---

## UNVERIFIED ITEMS (explicit list)

| # | Claim / gap | Status |
|---|---|---|
| 1 | Groww Fixed Deposits product (booking flow, rates, tenure) | **Unverified** — only a 404 page and a third-party LinkedIn claim. Help-centre index text mentions "Fixed Deposits" but no product page exists. |
| 2 | Groww NPS account opening / NPS investing | **Unverified** — only an NPS calculator exists. |
| 3 | GMP (Grey Market Premium) displayed inside Groww's IPO section | **Unverified** — no GMP column on Groww's open/closed/allotment tables. Groww only publishes GMP education content. |
| 4 | Trailing-stop order ticket in the Groww app | **Unverified** — documented as a concept on Groww's blog, not confirmed as an in-app order type. |
| 5 | Exact field list of a stocks holding row | **Partially unverified** — quantity/avg price/current value/invested/P&L/day change/XIRR/allocation/risk/dividends are referenced, but not all captured verbatim from a single primary page. |
| 6 | Transaction history / ledger / contract-note exact menu paths | **Unverified at path level** — Groww references "trades, contract notes, charges" and in-house back office, but the precise Reports submenu labels were not captured. |
| 7 | Maximum number of stocks per watchlist | **Unverified**. (Watchlist count limit = 10 is verified.) |
| 8 | "Most held" stocks data | **Unverified** — only "Most Bought Stocks" page found. |
| 9 | Sector-level / market-mover dedicated pages | **Unverified** as a distinct section (gainers/losers only confirmed inside Groww Digest). |
| 10 | In-app social / community / copy-trading feed | **Not found — likely not offered.** Groww's community surface is offline AIKG events + WhatsApp groups + social channels. |
| 11 | Self-serve "activate segment" screen (equity / F&O / commodity) | **Unverified** — segments are listed in Groww's SEBI/exchange registrations, but a dedicated activation UI page was not found. |
| 12 | NRI onboarding inside the app | **Inconsistent** — Groww's MF-KYC page and NRI pricing imply support; App Store reviews report NRI investing unsupported and a dead-end at the signature screen. |
| 13 | Commodity (MCX) brokerage specifics | **Partially unverified** — not itemised separately on the pricing pages fetched. |
| 14 | Bond (listed) brokerage per executed transaction | **Unverified**. |
| 15 | Max number of IPO bids per user | **Unverified** — third-party claim of 3 bids not confirmed on Groww primary. |
| 16 | Groww "Prime" plan availability to resident Indians | **Partially unverified** — pricing page describes Prime only in the NRI row ("MF: Direct & Prime both available"). |

---

*End of document. Compiled 12 Sep 2026. All prices/limits are as published on the source URL at fetch time and are subject to change.*
