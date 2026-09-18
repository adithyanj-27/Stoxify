# Stoxify — Functional Capability & Flow Audit

**Scope:** Vanilla-JS SPA (`public/index.html` 3244 lines, `public/app.js` 7219 lines) + FastAPI backend (`main.py` 1199 lines, helpers in `database.py`, `market_service.py`, `market_hours.py`, `fo_service.py`, `ipo_service.py`).
**Nature of audit:** Functional only. Colors, fonts, CSS and theme are deliberately excluded.
**Rule applied:** A capability is "works" only if a UI control reaches a working endpoint / server function. An existing endpoint with no UI caller is reported as unreachable, never as a working feature.

Legend for **Status**: ✅ works end-to-end · ⚠️ partial / works with caveats · ❌ stubbed, broken, or unreachable.

---

## 1. FEATURE INVENTORY

### 1.1 Onboarding & Account

| UI label (user sees) | Screen / element id | JS render / handler (line) | API endpoint(s) | Status |
|---|---|---|---|---|
| "Open Your Demat Account" step 1 (mobile, email, username, password) | `#obStep-1`, `#obInputPhone/Email/Username/Password` | `submitObStep1()` app.js:5445 | `GET /api/user/check-username` (main.py:180), `POST /api/user/login` (main.py:393, used as an "email exists?" probe) | ✅ |
| Live username availability badge ("✓ @x available" / "✗ Taken") | `#obUsernameStatus` | `onUsernameInput()` app.js:5355 | `GET /api/user/check-username` | ✅ |
| Simulated SMS OTP banner + "Tap to auto-paste OTP" | `#smsPushBanner`, `#smsOtpCode` | `submitObStep1()` 5445, `pasteSmsOtp()` 5537, `resendOtp()` 5549 | none (client-generated 4-digit OTP, `Math.random`, app.js:5513) | ⚠️ client-side illusion; any code accepted if `generatedOtp` empty, and literal `4321` always passes (app.js:5587) |
| "Verify OTP" step 2 | `#obStep-2`, `#otp-1..4` | `submitObStep2()` 5581 | none (client compare) | ⚠️ as above |
| PAN + legal name + DOB + age + experience step 3 | `#obStep-3`, `#obInputPan/Name/Dob/Age/Experience` | `submitObStep3()` 5609 | none (client validation only; "Verified with Income Tax Dept" pill is cosmetic) | ⚠️ no real KYC |
| Bank link + "Penny Drop Verification" step 4 | `#obStep-4`, `#bank-chips`, `#pennyDropLoader` | `selectBank()` 5667, `submitObStep4()` 5675 | none (hardcoded 1 s + 1.2 s `setTimeout`) | ⚠️ cosmetic simulation |
| 4-digit trading PIN step 5 → **creates account** | `#obStep-5`, `#obInputPin/PinConfirm` | `submitObStep5()` 5718 | `POST /api/user/create` (main.py:224) | ✅ |
| "Account Successfully Activated!" summary (Demat id, bank, ₹10L) | `#obStep-6`, `#obCreatedDemat/Username/Email/Bank` | `submitObStep5()` 5718, `finishOnboarding()` 5787 | none | ✅ |
| Guided tour prompt ("Let's Go 🚀 / Skip") | `#tourPromptModal` | `checkAndLaunchTour()` 5805, `skipTour()` 5827, `acceptTour()` 5834 | `POST /api/user/complete-tour` (main.py:296) via `markTourCompleteOnServer()` 5846 | ✅ (beginner experience tiers only) |
| Gamified sandbox trade (age < 18) | `#sandboxTradeModal` | `openSandboxModal()` 5860, `executeSandboxTrade()` 5923 | none (in-memory mock, `ETERNAL` @ ₹260) | ⚠️ pure client mock |
| Dashboard spotlight tour (age ≥ 18), 3 steps | `#dashboardTourOverlay`, `#tourStepCard` | `startDashboardTour()` 6005, `renderTourStep()` 6012, `nextDashboardTourStep()` 6077, `endDashboardTour()` 6086 | `POST /api/user/complete-tour` | ⚠️ step 3 target `stockWatchlistContainer` does not exist → falls back to `#pane-explore` |
| Login modal ("Login / Register") | `#loginModalOverlay`, `#loginIdentifierInput/PinInput` | `openLoginModal()` 3687, `submitLogin()` 3784 | `POST /api/user/login` (main.py:393) | ✅ |
| "Saved Accounts on This Device" quick-login cards | `#loginSavedAccountsSection/List` | `loadSavedLoginAccounts()` 3731, `selectLoginAccount()` 3774 | none (localStorage `stoxify_recent_accounts`) | ✅ |
| Profile dropdown (balance, bank, Edit, Log Out, Delete) | `#navProfileWrapper`, `#userDropdownMenu` | `updateNavbarProfile()` 2699, `toggleProfileDropdown()` 2803 | `GET /api/account`, `GET /api/user/current` | ✅ |
| Account & Profile page (identity, wallet, bank, settings list) | `#pane-profile` | `showProfilePage()` 2613, `renderProfilePageData()` 3085 | `GET /api/funds/bank-account` (main.py:986) | ✅ |
| Edit Profile (name, username, email, phone, dob, PAN, bank, password, PIN, avatar colour) | `#editProfileModalOverlay` | `openEditProfileModal()` 2850, `saveUserProfile()` 2936 | `POST /api/user/update` (main.py:320) | ✅ |
| Copy Demat ID | `#profilePageDemat`, copy button | `copyDematId()` 3134 | none (clipboard) | ✅ |
| Log Out | dropdown / profile footer | `logoutUser()` 2788 | none (clears localStorage; no server call) | ✅ |
| Delete Account | dropdown / profile footer | `confirmDeleteAccount()` 2300 | `POST /api/user/delete` (main.py:1003) | ✅ |

### 1.2 Explore / Market data

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| Sticky indices bar (NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT) | `#indicesBar` | `fetchIndices()` 399 | `GET /api/indices` (main.py:496) | ✅ (clicking opens the index asset page via `openAssetModal`) |
| Global search box + dropdown | `#globalSearchInput`, `#searchResultsDropdown` | `selectSearchResult()` 1577, search listener 1502 | `GET /api/search` (main.py:505) | ✅ |
| "Most Bought on Stoxifyn" carousel | `#mostBoughtCarousel` | `renderExploreStocks()` 720 | `GET /api/explore` (main.py:501) | ✅ |
| "Top Indian Equities" grid + sector/gainers/losers filter pills | `#stocksGrid`, pills | `renderExploreStocks()` 720, `filterExploreStocks()` 512 | `GET /api/explore` | ✅ (filters are client-side over the returned list) |
| "Recently Viewed" stocks carousel + Clear | `#recentStocksSection`, `#recentStocksCarousel` | `renderRecentlyViewedStocks()` 644, `clearRecentlyViewed()` 631 | none (localStorage) | ✅ |
| Popular Mutual Funds grid | `#mfGrid` | `renderExploreMutualFunds()` 811 | `GET /api/explore` | ✅ |
| "Recently Viewed" mutual funds + Clear | `#recentMfSection`, `#recentMfCarousel` | `renderRecentlyViewedMutualFunds()` 682 | none (localStorage) | ✅ |
| Live market status pill + "Market Schedule & Timings" modal | `#marketStatusPill`, `#marketHoursModalOverlay` | `fetchMarketStatus()` 196, `openMarketHoursModal()` 220 | `GET /api/market-status` (main.py:469) | ✅ |
| "Simulated 24/7 Trading Mode" toggle | `#simulationModeToggle` | `toggleSimulationMode()` 229 | `POST /api/market-status/toggle-simulation` (main.py:477) | ✅ (global server flag) |

### 1.3 Stock detail (dedicated full-page asset view, `#pane-asset-detail`)

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| Hero price / change / star | `#pageAssetPrice`, `#pageAssetChangeBadge`, `#pageAssetStarBtn` | `showAssetPage()` 3868, `updatePageAssetStar()` 4070 | `GET /api/quote` (main.py:510) | ✅ |
| Chart (Line/Candle, 1D→ALL, 20/50 EMA, scrub crosshair) | `#pageAssetChartCanvas` | `loadPageChartTimeframe()` 4686, `setChartType()` 4150, `toggleEma()` 4159, `renderCandlestickCanvas()` 4270, `renderLineChartWithChartJs()` 4546 | `GET /api/history` (main.py:558) | ✅ |
| Live tick refresh (5 s) | same canvas/price | anonymous `setInterval` 4725 | `GET /api/quote` | ✅ |
| Performance card (Today high/low, 52w, open, prev close, volume, circuits) | `#perfTodayHigh/Low`, `#perf52wHigh/Low`, `#perfOpen/PrevClose/Volume/LowerCircuit/UpperCircuit` | `showAssetPage()` 3868 | `GET /api/quote` | ⚠️ circuits derived as ±10 % client-side; volume falls back to literal `'34.2L'` |
| Market Depth (Level-2, 5 bid/ask tiers + buy/sell %) | `#pageDepthBids`, `#pageDepthAsks`, `#pageDepthBuyBar/SellBar` | `fetchPageMarketDepth()` 4083 | `GET /api/depth` (main.py:517) | ⚠️ server fabricates all 5 tiers with `random.randint` (main.py:528-539) |
| Fundamentals & Key Ratios grid | `#pageFundamentalsGrid` | `renderPageFundamentals()` 4117 | `GET /api/quote` | ⚠️ many values are hardcoded fallbacks in JS (P/E 24.8, ROE 14.8 %, etc.) |
| "About" text | `#pageAboutText` | `showAssetPage()` 3868 | `GET /api/quote` | ⚠️ generic fallback sentence if no description |
| Tab: Financials (quarterly/annual bars + table) | `#asset-tab-content-financials` | `switchAssetPageTab()` 6987, `fetchStockFinancials()` 7019, `renderFinancialsBars()` 7033 | `GET /api/stock/financials` (main.py:1143) | ✅ |
| Tab: Shareholding pattern | `#asset-tab-content-shareholding` | `fetchStockShareholding()` 7096 | `GET /api/stock/shareholding` (main.py:1147) | ⚠️ missing fields default to hardcoded promoter 48 % / FII 20 % etc. |
| Tab: Peers comparison | `#asset-tab-content-peers` | `fetchStockPeers()` 7146 | `GET /api/stock/peers` (main.py:1151) | ✅ |
| Tab: News feed | `#asset-tab-content-news` | `fetchStockNews()` 7190 | `GET /api/stock/news` (main.py:1155) | ✅ |
| SIP calculator (sliders + "Schedule Monthly SIP" CTA) | `#pageSipCalcSection` | `onSipSliderChange()` 6741, `openSipModalForCurrentAsset()` 6769 | none | ✅ |

### 1.4 Trading (orders)

| UI label | Element id | JS handler (line) | API | Status |
|---|---|---|---|---|
| BUY/SELL toggle | `#pageBtnBuy/Sell` | `setPageOrderAction()` 4802 | — | ✅ |
| Product type Delivery (CNC) / Intraday (5× MIS) | `#pageProdDelivery/Intraday` | `setPageProductType()` 4870 | — | ✅ |
| Order variety Market / Limit / SL / GTT | `#pageVarietyMarket/Limit/SL/GTT` | `setPageOrderVariety()` 4892 | — | ⚠️ GTT create path is broken (see 2.j) |
| Quantity stepper + quick chips | `#pageOrderQuantity` | `stepPageQuantity()` 4941, `setPageQuickQuantity()` 4952 | — | ✅ |
| Limit price / Trigger price inputs | `#pageOrderLimitPrice`, `#pageOrderTriggerPrice` | `recalcPageMargin()` 4961 | — | ✅ |
| Required margin / available balance / est. charges / net credit | `#pageRequiredMargin`, `#pageAvailableCash`, `#pageEstCharges`, `#pageNetProceeds` | `recalcPageMargin()` 4961 | none (client calc `calculateEstimatedCharges` 1959) | ✅ |
| "Estimated Taxes & Charges" modal | `#chargesModalOverlay` | `openPageChargesModal()` 2018, `renderChargesModalContent()` 2045 | none (client calc) | ✅ |
| Execute order (BUY/SELL, Market/Limit/SL, Delivery/Intraday) | `#pageOrderExecuteBtn` | `executePageTrade()` 5129 | `POST /api/order` (main.py:766) | ✅ (Market/Limit/SL, CNC/MIS) |
| Mobile slide-up trade drawer (same controls) | `#mobileTradingDrawerOverlay` | `openMobileTradeDrawer()` 4761, `executePageTrade()` 5129 | `POST /api/order` | ✅ |
| Order success modal (filled / limit OPEN / SL trigger pending) | `#orderSuccessModal` | `openOrderSuccessModal()` 6099 | — | ✅ |
| Legacy trade modal (Market/Limit only) | `#tradeModalOverlay`, `#tradeExecuteBtn` | `legacyOpenAssetModal()` 1628, `submitOrder()` 2117 | `POST /api/order` | ❌ **DEAD** — `legacyOpenAssetModal` is never called; `openAssetModal` routes to the asset page instead |

### 1.5 Positions & intraday

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| Intraday positions table / cards | `#positionsTableBody`, `#positionsMobileList` | `fetchPositions()` 1002, `fetchPositionsInternal()` 1013 | `GET /api/positions` (main.py:675) | ✅ |
| Summary: unrealized P&L, margin deployed (5×), active count | `#posTotalPnl`, `#posMarginDeployed`, `#posActiveCount` | `fetchPositionsInternal()` 1013 | `GET /api/positions` | ✅ |
| "Exit" a single position | row button | `exitPosition()` 1144 | `POST /api/position/exit` (main.py:727) | ✅ |
| "Square Off All" | `#squareOffAllBtn` | `squareOffAllPositions()` 1166 | `POST /api/position/exit-all` (main.py:739) | ✅ |
| Nav badges (desktop + mobile) | `#navPositionsBadge`, `#mobPositionsBadge` | `fetchPositionsInternal()` 1013 | `GET /api/positions` | ✅ |
| Claimed "Auto Square-off at 03:20 PM IST" | `#squareOffAllBtn` area / copy | none | none | ❌ **no scheduler exists** — square-off is manually triggered only |

### 1.6 Holdings / Portfolio

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| Portfolio summary banner (current value, invested, total returns, 1D, available balance) | `#summaryCurrentVal/InvestedVal/TotalReturns/TodayPnl/AvailableBalance` | `fetchPortfolio()` 846, `fetchPortfolioInternal()` 857 | `GET /api/portfolio` (main.py:581) | ✅ |
| Holdings table (desktop) | `#holdingsTableBody` | `fetchPortfolioInternal()` 857 | `GET /api/portfolio` | ✅ |
| Holdings cards (mobile) | `#holdingsMobileList` | `fetchPortfolioInternal()` 857 | `GET /api/portfolio` | ✅ |
| "Sell" a holding | row / card button | `startHoldingSale()` 1613 → asset page SELL prefilled | `GET /api/portfolio` | ✅ |
| Guest lock card ("Holdings Locked") | `#holdingsGuestBanner` | `fetchPortfolioInternal()` 857 | none | ✅ |

### 1.7 Mutual funds & SIP

| UI label | Element id | JS handler (line) | API | Status |
|---|---|---|---|---|
| MF Explore grid (NAV, 1Y return, star) | `#mfGrid` | `renderExploreMutualFunds()` 811 | `GET /api/explore` | ✅ |
| MF asset page (NAV, category, AUM, expense ratio, returns) | `#pageFundamentalsGrid`, `#pageSipCalcSection` | `showAssetPage()` 3868, `renderPageFundamentals()` 4117 | `GET /api/quote` / `GET /api/history` | ⚠️ AUM / expense ratio / manager are hardcoded fallbacks |
| SIP Return Calculator | `#sipSliderMonthly/Return/Years`, `#sipRes*` | `onSipSliderChange()` 6741 | none (client compound formula) | ✅ |
| "Schedule Monthly SIP with Auto-Debit" → confirm | `#sipScheduleModal` | `openSipModal()` 6774, `submitSipSchedule()` 6798 | `POST /api/mf/sip` (main.py:1079) | ✅ |
| "My Active SIPs" table / cards | `#holdings-sips-container`, `#sipsTableBody`, `#sipsMobileList` | `loadActiveSips()` 6841 | `GET /api/mf/sips` (main.py:1091) | ❌ **BROKEN** — render reads `s.symbol` / `s.amount` / `s.sip_id` etc., but the server returns `fund_id` / `fund_name` / `monthly_amount` / `sip_day` (database.py sips schema). `s.symbol.replace(...)` throws → table never renders |
| "Stop SIP" | row / card button | `cancelSip()` 6899 | `DELETE /api/mf/sip/{sip_id}` (main.py:1098) | ❌ unreachable in practice — `s.sip_id` is undefined because the list render throws |

### 1.8 IPO

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| IPO grid + All / Recently Listed / Upcoming filters | `#ipoGrid` | `fetchIpos()` 6549, `filterIpos()` 6562, `renderIpos()` 6571 | `GET /api/ipo/list` (main.py:1106) | ✅ |
| "Apply Now (ASBA)" bid modal (lots, UPI id, blocked amount) | `#ipoBidModal` | `openIpoBidModal()` 6648, `recalcIpoAmount()` 6689, `submitIpoApplication()` 6702 | `POST /api/ipo/apply` (main.py:1118) | ✅ |
| "View Listing Details" (LISTED) | card button | `renderIpos()` 6571 | none (toast only) | ❌ cosmetic |
| "Notify on Open" (UPCOMING) | card button | `renderIpos()` 6571 | none (toast only) | ❌ cosmetic, no notification stored |
| My IPO applications / withdraw a bid | — | — | `GET /api/ipo/applications`, `DELETE /api/ipo/bid/{id}` exist (main.py:1128, 1135) but **no UI** | ❌ unreachable |

### 1.9 F&O / Options

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| F&O sub-tab, NIFTY/BANKNIFTY switcher, spot, PCR, expiry | `#explore-fo-container`, `#btnFoNifty/BankNifty`, `#foSpotPrice`, `#foPcrVal` | `switchFoUnderlying()` 6294, `fetchOptionChain()` 6303 | `GET /api/fo/option-chain` (main.py:1025) | ✅ |
| Option chain matrix (CE/PE LTP, delta, IV, OI, ATM highlight) | `#optionChainTableBody` | `renderOptionChain()` 6334 | `GET /api/fo/option-chain` | ✅ |
| Option buy/sell modal (lots, premium, available cash) | `#optionBuyModal` | `openOptionBuyModal()` 6384, `recalcOptionPremium()` 6459, `submitOptionTrade()` 6476 | `POST /api/order` (`asset_type: OPTION`, `product_type: INTRADAY`) | ✅ (no F&O positions view — lands in the same Positions list) |
| Futures trading | — | — | — | ❌ none (options only) |
| Option sell without holding / short | — | partial | `POST /api/order` | ⚠️ SELL of options relies on the generic sell-quantity check |

### 1.10 Watchlist

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| Star button on cards / asset page | `.card-star-btn`, `#pageAssetStarBtn` | `renderCardStarBtn()` 578, `toggleWatchlistItem()` 1439 | `POST /api/watchlist` (main.py:923), `DELETE /api/watchlist/{symbol}` (main.py:930) | ✅ (optimistic local cache + server write) |
| Watchlist page grid | `#watchlistGrid` | `fetchWatchlist()` 1391 | `GET /api/watchlist` (main.py:894) | ✅ |

### 1.11 Funds (add / withdraw money)

| UI label | Element id | JS handler (line) | API | Status |
|---|---|---|---|---|
| "Add Money" 3-step modal (amount → 4-digit PIN keypad → success receipt) | `#upiAddMoneyModal`, `#upiStepAmount/Pin/Success` | `openAddMoneyModal()` 3148, `validateUpiAddAmount()` 3225, `proceedToUpiPinScreen()` 3253, `executeUpiPayment()` 3366 | `POST /api/funds/upi-add` (main.py:959) | ✅ (simulated bank→wallet) |
| "Withdraw" modal (amount + PIN) | `#withdrawMoneyModal` | `openWithdrawModal()` 3479, `executeWithdrawal()` 3520 | `POST /api/funds/withdraw` (main.py:975) | ✅ |
| "Restore Full ₹10,00,000 Balance" | `#btnRestoreFullBalance` | `restoreFullBalance()` 2254 | `POST /api/account/restore` (main.py:994) | ✅ |
| "Reset Entire Portfolio & Orders to ₹10L" | `#btnResetPortfolio` | `resetEntirePortfolio()` 2277 | `POST /api/account/reset` (main.py:1015) | ✅ |
| Bank Passbook & Statement modal (balance, UPI id, transactions) | `#bankPassbookModal` | `openBankPassbookModal()` 3612 | `GET /api/funds/bank-account` (main.py:986) | ✅ |
| Bank account card on profile | `#profileBankNameDisplay/Account/Balance` | `renderProfilePageData()` 3085, `loadBankAccountDetails()` 3051 | `GET /api/funds/bank-account` | ✅ |

(POST `/api/account/deposit`, main.py:940, is an older deposit endpoint that **no UI calls**.)

### 1.12 Reports & analytics (tax, sector, P&L)

| UI label | Element id | JS render (line) | API | Status |
|---|---|---|---|---|
| Sub-tab "Analytics & Tax Report (Budget 2024)" | `#holdings-analytics-container` | `switchHoldingsSubnav()` 357 | — | ✅ |
| Sector & Asset Diversification stacked bar + legend | `#sectorAllocationContainer` | `loadPortfolioAnalytics()` 6918 | `GET /api/analytics/sector-allocation` (main.py:1171) | ✅ |
| Capital Gains tax card (Net STCG 20 %, Net LTCG 12.5 %, taxable, total) | `#taxStcgGain/Liability`, `#taxLtcgGain/Taxable/Liability`, `#taxTotalLiability` | `loadPortfolioAnalytics()` 6918 | `GET /api/analytics/tax-report` (main.py:1160) | ✅ |
| Tax trades table | `#taxTradesTableBody` | `loadPortfolioAnalytics()` 6918 (never populated) | `GET /api/analytics/tax-report` | ❌ **dead render** — the endpoint returns a `trades` array but the JS never touches `#taxTradesTableBody` |
| Download P&L / tax report (CSV/PDF) | — | — | — | ❌ absent |

### 1.13 Profile & settings

| UI label | Element id | JS (line) | API | Status |
|---|---|---|---|---|
| Profile identity + Demat + wallet + bank cards | `#pane-profile` | `renderProfilePageData()` 3085 | `GET /api/funds/bank-account` | ✅ |
| "All Orders & Contract Notes" | profile menu | `navigateTo('/orders')` | — | ⚠️ navigates to Orders; no contract notes exist |
| "Portfolio Holdings" | profile menu | `navigateTo('/holdings')` | — | ✅ |
| "Brokerage & Regulatory Charges" | profile menu | `openPageChargesModal()` 2018 | none | ✅ |
| "4-Digit Security PIN" | profile menu | `openEditProfileModal()` 2850 | `POST /api/user/update` | ✅ |
| "Market Timings & Rules" | profile menu | `openFundsModal()` 2215 / `openMarketHoursModal()` 220 | `GET /api/market-status` | ✅ |
| Theme toggle (light/dark) | navbar / profile | `toggleTheme()` 153 | none | ✅ |
| PWA install | `#btnInstallApp`, `#dropdownInstallItem`, `#mobileInstallBanner` | `installPWA()` 2456, `updateInstallButtonsVisibility()` 2370 | none | ✅ |

### 1.14 Alerts / notifications

| UI label | Element id | JS (line) | API | Status |
|---|---|---|---|---|
| Toast notifications | `#toastContainer` | `showToast()` 125 | none | ✅ (transient UI only) |
| Price alerts / order-trigger push | — | — | — | ❌ none |
| Web push / background notifications | — | — | — | ❌ `sw.js` has no `push` / `notificationclick` handlers |
| "Notify on Open" (IPO) | `#ipoGrid` button | `renderIpos()` 6571 | none | ❌ toast-only illusion |

### 1.15 PWA / offline

| UI label | Element id | JS (line) | API | Status |
|---|---|---|---|---|
| Install app (desktop button + mobile banner + guide modal) | `#btnInstallApp`, `#mobileInstallBanner`, `#pwaInstallGuideModalOverlay` | `installPWA()` 2456, `openPwaGuideModal()` 2424, `triggerNativeInstallPrompt()` 2440 | none | ✅ |
| Service worker registration | — | app.js:2494 | `/sw.js` (main.py:139) | ✅ |
| Offline data access | — | — | — | ❌ `sw.js` explicitly skips all `/api/` requests and network-firsts the app shell; icons only are cache-first. No offline content |
| Web app manifest | `<link rel="manifest">` | — | `/manifest.json` (main.py:126) | ✅ |


---

## 2. FLOW TRACES

Every endpoint name below is from `main.py`; the handler/helper line numbers are cited. Client steps cite `app.js` (or `index.html`) lines.

### (a) Signup / onboarding including the tour

1. User clicks "Login / Register" (`#navAuthBtn` → `openLoginModal()` app.js:3687) or "Open Demat Account" and lands on `/onboarding` (`handleRoute()` 2626 → `showOnboardingPage()` 5292). `showOnboardingPage()` resets every field (5303-5346) and calls `goToObStep(1)` 5398.
2. **Step 1** — user types phone/email/username/password. On username typing, `onUsernameInput()` 5355 debounces 300 ms then `GET /api/user/check-username?username=` (main.py:180) → shows "✓ available" / "✗ Taken".
3. `submitObStep1()` 5445: client validates 10-digit phone, email regex, username 3-25 `[A-Za-z0-9_]`, password ≥ 6. Then calls `GET /api/user/check-username` again (5480), then **probes for an existing account** with `POST /api/user/login {identifier: email}` (5493). If that returns `success` (an account exists), it aborts onboarding and opens the login modal prefilled (5501). Otherwise it generates a random 4-digit OTP `Math.floor(1000+Math.random()*9000)` (5513), shows the fake SMS banner and advances to step 2. *No OTP is ever sent to a server or a phone.*
4. **Step 2** — `submitObStep2()` 5581 compares the 4 typed digits against `obUserData.generatedOtp` (or the hard-coded bypass `'4321'`). Success → toast + step 3.
5. **Step 3** — `submitObStep3()` 5609 collects PAN, name, DOB, gender, occupation, income, age, experience (client-only validation; `onPanInput()` 5599 toggles a fake "Verified with Income Tax Department" pill at 10 chars). Age < 13 blocked.
6. **Step 4** — `selectBank()` 5667 sets bank name/IFSC from chips; `submitObStep4()` 5675 checks account entered twice + IFSC, then runs a purely cosmetic "NPCI IMPS penny drop" via two `setTimeout`s (5707-5715) and advances.
7. **Step 5** — `submitObStep5()` 5718 validates the 4-digit PIN twice, then `POST /api/user/create` (main.py:224) with `{name, username, password, email, phone, pan, dob, bank_name, bank_account, pin, age, experience}`.
   - **Server:** validates name/email present, DOB ≥ 13 yrs, age ≥ 13, username format/uniqueness, password ≥ 6; then `create_user(...)` (main.py:276) → database.py:728 inserts the user with **₹10,00,000 `balance` and `total_deposited`** and a `bank_balance` of ₹10,00,000; optionally syncs to Supabase auth (`sync_user_to_supabase_auth`, database.py:564).
   - **On success:** client sets `stoxify_user_id`/`stoxify_cached_user`, removes `stoxify_guest_mode`, adds `user-logged-in`, updates navbar, `saveRecentAccount()` 3714, `fetchAccount()` 380, and shows the congratulations screen `#obStep-6`.
   - **On failure:** any 4xx → `showToast(result.detail …, true)` and the user stays on step 5. (Note: `submitObStep5` has no client-side email-format check, unlike step 1.)
8. **Finish** — `finishOnboarding()` 5787 navigates to `/explore`, toasts "₹10,00,000 virtual cash ready…", then `checkAndLaunchTour()` 5805.
9. **Tour branch:** if `experience` ∈ {None/Total Beginner, < 1 Year} and `has_completed_tour` is false, `#tourPromptModal` appears after 600 ms.
   - "Skip" → `skipTour()` 5827 → `markTourCompleteOnServer()` 5846 → `POST /api/user/complete-tour` (main.py:296).
   - "Let's Go" → `acceptTour()` 5834: age < 18 → `openSandboxModal()` 5860 (client-only mock ETERNAL trade, `executeSandboxTrade()` 5923); age ≥ 18 → `startDashboardTour()` 6005 (3-step spotlight, `nextDashboardTourStep()` 6077, `endDashboardTour()` 6086 → `POST /api/user/complete-tour`).
10. Experienced users (`1–2 Years` / `2+ Years`) skip the prompt and are silently marked complete (5811-5814).

### (b) Login / logout

1. `openLoginModal()` 3687 clears inputs, calls `loadSavedLoginAccounts()` 3731 (renders `stoxify_recent_accounts`).
2. User enters identifier (username/email/phone) + password **or** PIN and hits "Log In" → `submitLogin()` 3784. Client only checks both are non-empty.
3. Client sends `POST /api/user/login {identifier, pin, password: pin}` (signals both fields with the same string).
   - **Server (main.py:393):** `find_user_by_identifier` (database.py:1059) → if no user, 404 "No registered account found…". If a secret was supplied, it must equal the stored plaintext `password` or `pin` (main.py:424-427), otherwise **401 "Incorrect Password or PIN"**. Critically, if the client sends an empty secret, the endpoint returns `success:true` with only `{name, username, email, id}` and `exists:true` — used by onboarding step 1 as an existence probe (main.py:404-415). Accounts with no stored credential can only ever be "found", never authenticated.
   - On success optionally lazily syncs Supabase auth (main.py:432-447).
4. **Success:** `currentUser = data.user`, clears `stoxify_guest_mode`, writes `stoxify_user_id` + `stoxify_cached_user`, shows "Welcome back, X!", calls `fetchAccount()`/`fetchWatchlist()` and refreshes the current tab; if on `/onboarding` or `/login`, redirects to `/explore`. (Note: the returned `user` from a password login is the **full** row — including `pin`, `password`, `bank_account` — and it is cached in localStorage.)
5. **Failure:** 404/401 → `showToast(data.detail, true)`; network error → "Failed to connect during login".
6. **Logout** — `logoutUser()` 2788: sets `stoxify_guest_mode='true'`, removes `stoxify_user_id` and `stoxify_cached_user`, resets navbar, toast, refreshes current tab, navigates to `/explore`. There is **no server-side logout / token invalidation** because there is no server session.

### (c) Add money via UPI, and withdraw

**Add money**
1. "Add Money" (`#upiAddMoneyModal`) → `openAddMoneyModal()` 3148. Guest → toast + redirect to `/onboarding` (3152). Otherwise resets to step 1, prefills ₹50,000, binds bank name/account/balance, and refreshes via `loadBankAccountDetails()` 3051 → `GET /api/funds/bank-account` (main.py:986).
2. `validateUpiAddAmount()` 3225 enforces min ₹100 and ≤ available **bank** balance (from `cachedBankAccount.bank_balance` or cached user); disables the CTA otherwise.
3. "Proceed to Enter PIN" → `proceedToUpiPinScreen()` 3253 shows `#upiStepPin` with the amount/bank summary and focuses the hidden PIN input/keypad (`pressUpiKey()` 3326, `onUpiPinInput()` 3312).
4. On 4th digit → `executeUpiPayment()` 3366: `POST /api/funds/upi-add?user_id=…` with header `X-User-Id` and body `{amount, pin, user_id}`.
   - **Server (main.py:959):** requires a non-guest uid; `transfer_bank_to_wallet(uid, amount, pin)` (database.py:1140).
   - **Success:** response `{success, amount, balance, bank_balance, reference_id}`. Client updates `currentUser.balance/bank_balance`, writes `stoxify_cached_user`, shows the success screen `#upiStepSuccess` with a receipt (amount, ref, debited account, new wallet/bank balances).
   - **Failure:** PIN wrong / insufficient bank funds → 400 → `#upiPinError` text is set (e.g. "Invalid Security PIN. Please try again."), PIN dots reset; network error → "Network error. Please try again."
5. "Done & Return to Portfolio" → `finishUpiSuccess()` 3470.

**Withdraw**
1. "Withdraw" → `openWithdrawModal()` 3479 (guest → onboarding). Loads bank details, shows available cash, clears inputs.
2. `executeWithdrawal()` 3520 validates: amount ≥ ₹100, amount ≤ `currentUser.balance`, PIN exactly 4 digits.
3. `POST /api/funds/withdraw?user_id=…` body `{amount, pin, user_id}` → main.py:975 → `withdraw_wallet_to_bank` (database.py:1244).
   - **Success:** updates cached balance/bank balance, refreshes account + bank details, closes modal, toast "₹X withdrawn to your bank account successfully!".
   - **Failure:** 400 → `#wdrErrorMsg` ("Withdrawal failed. Check your PIN and balance."); network error → "Network error. Please try again."

### (d) BUY a stock (delivery CNC)

1. User opens Explore → clicks a stock card (`renderExploreStocks()` 720 → `openAssetModal()` 1592) which routes to `/stock/SYM`; `handleRoute()` 2626 → `showAssetPage()` 3868.
2. `showAssetPage` fetches `GET /api/quote` (main.py:510), records the asset in Recently Viewed, renders everything, resets the order ticket to BUY / DELIVERY / MARKET / qty 1.
3. User keeps "Delivery (CNC)", picks qty, sees Required Margin = qty × LTP (100 %) and est. charges (`recalcPageMargin()` 4961 → `calculateEstimatedCharges()` 1959).
4. Clicks "BUY SYM" → `executePageTrade()` 5129. Guarded by `isGuest()` (redirects to onboarding). Sends `POST /api/order` (main.py:766) with `{symbol, name, asset_type:'STOCK', order_type:'BUY', product_type:'DELIVERY', quantity, price, order_variety:'MARKET', limit_price:null, trigger_price:0}`.
   - **Server:** requires uid + existing user (else 401 with "…unlock ₹10,00,000 virtual balance"); validates qty/price > 0; `validate_order_timing('DELIVERY')` (market_hours.py:114) → allowed, tag `NORMAL` (or `AMO` off-hours, market_hours.py:128); for stocks it prefers the cached quote price (main.py:795-799) so fill is at market. `execute_trade(...)` (database.py:1849) debits `balance` by the full amount + charges, and if `product_type=DELIVERY` upserts into the `holdings` table.
   - **On success:** client awaits `fetchAccount()`, `fetchPortfolio(true)`, `fetchPositions(true)`, `fetchOrders()`, then opens `#orderSuccessModal` ("Order Executed!", asset/qty/price/total/updated balance) and toasts the server message.
   - **On failure:** 400/401 → `showToast(result.detail || result.error, true)`; network error → "Failed to connect to trade server".

### (e) BUY intraday (MIS) with leverage

1. Same asset page; user taps "Intraday 5x MIS" (`setPageProductType()` 4870) → `#pageLeverageHint` shows "5× Intraday Leverage Applied (Only 20 % margin blocked)", and Required Margin becomes qty × LTP × 0.20 (`recalcPageMargin()` 4961).
2. `executePageTrade()` 5129 sends `POST /api/order` with `product_type:'INTRADAY'`.
   - **Server:** `validate_order_timing('INTRADAY')` always returns allowed with tag `NORMAL` (or `INTRADAY`); `execute_trade` sets `required_margin = total_amount * 0.20` for non-OPTION intraday (database.py:1911-1912) and books the trade into the `positions` table with `margin_used`.
   - **Success:** same refresh + `#orderSuccessModal`; the success modal's "View in Positions →" button navigates to `/positions`. Position appears with live P&L and an "Exit" button.
   - **Failure:** insufficient margin → 400 error toast; everything else as (d).

### (f) SELL / exit a holding

1. From Holdings, "Sell" on a row/card → `startHoldingSale()` 1613 stores `{symbol, assetType, quantity, product:'DELIVERY'}` in `sessionStorage.stoxify_holding_sale` and opens the asset page with `stoxify_preselect_action='SELL'`.
2. `showAssetPage()` 3868 sees the preselect, switches to SELL, sets product DELIVERY (or INTRADAY if only a position exists), pre-fills the exact holding quantity via `setPageQuickQuantity()` 4952, and shows gross value + est. charges + **Net Settlement Credit** (`recalcPageMargin()` 4961).
3. Click "SELL SYM" → `executePageTrade()` 5129 → `POST /api/order` with `order_type:'SELL'`.
   - **Server:** `execute_trade` performs a cross-product availability check (`get_available_sell_quantity`, database.py:1398) across holdings/positions; if not enough shares → 400 "Insufficient quantity to sell", if none → "You do not own any shares of SYM". On success it reduces holdings, credits `net_proceeds` (gross − charges) and books `realized_pnl`.
   - **Success:** `#orderSuccessModal` shows Gross Order Value, "-charges" row, **Net Balance Credited** and the updated balance; Holdings refresh shows the reduced/removed row.
   - **Failure:** 400 → error toast; nothing changes.

### (g) Square off one position, and Square-off-all

**Single:** Positions row "Exit" / card "Square Off Position" → `exitPosition(symbol)` 1144. A native `confirm()` gate, then `POST /api/position/exit {symbol}` (main.py:727) → fetches live `get_stock_quote` and `exit_position(symbol, price)` (database.py:2405) → which internally calls `execute_trade(SELL, INTRADAY, full qty, market)`. Success → toast "Position squared off: SYM at current market price", then `fetchPositions(true)`, `fetchAccount()`, `fetchOrders()`. Failure (no position / server error) → error toast.

**All:** `#squareOffAllBtn` (visible only when positions > 0) → `squareOffAllPositions()` 1166. `confirm()`, then `POST /api/position/exit-all` (main.py:739). Server iterates all positions for the uid, exits each at its live quote, and returns `{exited_count, symbols}`. Client toasts "Squared off N open intraday positions!" and refreshes. Note: **partial failures are not surfaced** — the client shows the count even if some exits failed, and any network error → "Failed to square off positions".

### (h) Place a limit order and see it fill

1. Asset page → "Limit" variety (`setPageOrderVariety()` 4892) → limit-price field appears. User enters a price below market (BUY) so it cannot fill immediately.
2. `executePageTrade()` 5129 → `POST /api/order` with `order_variety:'LIMIT', limit_price:X`.
   - **Server `execute_trade`:** `is_pending_limit` true when BUY limit < market (database.py:1884-1888). For a resting BUY it blocks `required_margin + pending_charges` from balance (database.py:1956-1961), inserts an order row `status='OPEN'`, and returns `{status:'OPEN'}`. Insufficient funds → 400 "Insufficient margin for Limit BUY".
   - **On success:** `#orderSuccessModal` detects `status==='OPEN'` and shows **"Limit Order Placed!"** with "will execute automatically when the market reaches your limit price" and a "View in Orders →" button. Open-orders badge count increments.
3. **Fill:** the *only* matching loop is `service_pending_orders(uid)` (main.py:856) invoked as a side-effect of `GET /api/orders` (main.py:891). It reads pending symbols (`get_pending_order_symbols`, database.py:2503) and calls `check_open_limit_orders(symbol, price)` (database.py:2522), which for each OPEN/TRIGGER_PENDING row atomically claims it via `cancel_order` (refund block, database.py:2437) and re-executes as a MARKET fill at the current price. So an order only fills **when the user opens/refreshes the Orders tab** (or places another order for the same symbol — main.py:826). There is no background scheduler.
4. User sees the fill after that refresh: the order moves from "Open Orders" to "Executed Orders" with a fill timestamp and the new holding/position.

### (i) Cancel an order

1. Orders → "Open Orders" tab (`switchOrdersSubnav('open')` 336) → `fetchOrders()` 1181 renders OPEN + TRIGGER_PENDING rows each with a "Cancel" button.
2. Click → `cancelOrder(orderId)` 1364 → `POST /api/order/cancel {order_id}` (main.py:835) → `cancel_order` (database.py:2437).
   - **Server:** only status OPEN/TRIGGER_PENDING can be cancelled; claims the row via `CANCELLING` guard, refunds exactly `blocked_amount` (or `total_amount` fallback) for BUY orders, sets status `CANCELLED`.
   - **Success:** toast "Order #N cancelled and blocked funds returned!", then `fetchOrders()`, `fetchAccount()`, `fetchPortfolio(true)`, `fetchPositions(true)`.
   - **Failure:** 400 ("Cannot cancel … status …" / "already being processed" / "not found") or network error → error toast.

### (j) GTT order create / cancel

**Create — BROKEN.**
1. Asset page → "GTT" variety (`setPageOrderVariety('GTT')` 4892) → both limit and trigger fields appear; CTA reads "CREATE GTT TRIGGER (BUY)".
2. `executePageTrade()` 5129 (branch at 5179) sends `POST /api/order/gtt` with `{symbol, transaction_type, quantity, trigger_price, limit_price}`.
3. **Server (main.py:1040, `GTTRequest` at 1030)** requires `symbol`, **`name`**, `trigger_price`, `quantity`; the field for side is `action` (not `transaction_type`) and there is no `limit_price` field (it has `target_price` / `stop_loss_price`). Because **`name` is required and never sent**, FastAPI/Pydantic returns **422** before the handler runs. The client sees no `result.success` and shows "Trade execution failed". **A GTT can never be created from the UI.**

**Cancel.**
1. Orders → "GTT & Triggers" tab (`switchOrdersSubnav('gtt')` 336) → `loadGttOrders()` 6207 → `GET /api/orders/gtt` (main.py:1058).
   - **Data-contract mismatch:** the client reads `o.order_id`, `o.transaction_type`, `o.limit_price`, but the server rows (database.py:2865, `gtt_orders` schema) expose `id`, `action`, `trigger_price`, `target_price`, `stop_loss_price`. So the table renders literal `undefined` cells and `formatINR(undefined)` → "₹0.00".
2. "Cancel"/"Cancel Trigger" → `cancelGttOrder(o.order_id)` 6272 → `DELETE /api/order/gtt/undefined` → 422 (path int parse) → caught → "Failed to cancel trigger". Even a valid id would work server-side (`cancel_gtt_order`, database.py:2873) but the UI can never pass one.

### (k) Start and cancel a SIP

**Start.** MF asset page → SIP calculator → "Schedule Monthly SIP with Auto-Debit" → `openSipModalForCurrentAsset()` 6769 → `openSipModal()` 6774 (guest → onboarding) → `#sipScheduleModal`. User sets amount (min ₹500) and debit day, then `submitSipSchedule()` 6798:
- Client sends `POST /api/mf/sip {fund_id, fund_name, monthly_amount, sip_day}` (corrected field names, see comment app.js:6810).
- **Server (main.py:1079):** requires account, amount ≥ ₹500, day 1-31; `create_sip` (database.py:2887) inserts into `sips` and computes the next installment date (clamping 29-31 to month end).
- **Success:** toast "Monthly SIP of ₹X scheduled on the Nth of every month!" and `loadActiveSips()`.
- **Failure:** 400 → error toast.

**List / cancel — BROKEN.**
- `loadActiveSips()` 6841 → `GET /api/mf/sips` (main.py:1091) returns `get_user_sips` rows with `fund_id, fund_name, monthly_amount, sip_day, next_installment_date, status`. The render code reads `s.symbol`, `s.amount`, `s.installment_day`, `s.next_trigger_date`, `s.sip_id`, `s.installments_completed`. The very first row calls `s.symbol.replace('.NS','')` on `undefined` → **TypeError** → the whole table never updates from its empty state. "Active SIPs" is therefore effectively a dead tab, and "Stop SIP" (`cancelSip()` 6899 → `DELETE /api/mf/sip/{id}`) can never be invoked with a real id.

### (l) Apply for an IPO, and withdraw a bid

**Apply.** Explore → IPOs sub-tab (`switchExploreSubnav('ipo')` 306 → `fetchIpos()` 6549 → `GET /api/ipo/list`) → "Apply Now (ASBA)" → `openIpoBidModal()` 6648 (guest → onboarding). Modal shows price band, lot size, GMP, computes blocked amount = lots × lot_size × max_price (`recalcIpoAmount()` 6689). `submitIpoApplication()` 6702 → `POST /api/ipo/apply {ipo_id, ipo_name, lots, shares: lot_size, bid_price: max_price, upi_id}`.
- **Server (main.py:1118):** `apply_ipo` (database.py:2933) checks balance ≥ lots×shares×bid_price, debits it, inserts an `ipo_bids` row with status `APPLIED`.
- **Success:** toast "IPO bid submitted for N lot(s)… ₹X blocked via simulated ASBA mandate", modal closes, `fetchAccount()`.
- **Failure:** insufficient balance → 400 with required/available; network error → "Failed to apply for IPO".

**Withdraw — UNREACHABLE.** The backend exposes `GET /api/ipo/applications` (main.py:1128) and `DELETE /api/ipo/bid/{bid_id}` (main.py:1135, refunds the blocked amount), but **no UI element calls them**. There is no "My Applications" list and no "Withdraw bid" button.

### (m) Buy an option from the option chain

1. Explore → "F&O (Futures & Options)" (`switchExploreSubnav('fo')` 306) → `fetchOptionChain()` 6303 → `GET /api/fo/option-chain?symbol=NIFTY` (main.py:1025). `renderOptionChain()` 6334 renders CE/PE LTP buttons with delta.
2. Click a Call/Put LTP → `openOptionBuyModal(underlying, strike, optType, ltp, iv, lotSize)` 6384 (guest → onboarding). Shows spot, LTP, lot size, IV; lots stepper; premium = lots × lotSize × ltp (`recalcOptionPremium()` 6459).
3. "EXECUTE OPTION TRADE" → `submitOptionTrade()` 6476 → `POST /api/order` with `asset_type:'OPTION'`, `product_type:'INTRADAY'`, `symbol='NIFTY_24000_CE'`, `quantity=lots*lotSize`, `price=ltp`, `order_variety:'MARKET'`.
   - **Server:** `execute_trade` explicitly exempts OPTION from the 20 % margin rule (database.py:1911), so full premium is blocked; the position lands in `positions` (or `holdings` if delivery).
   - **Success:** refreshes account/positions/orders, closes modal, toast "BUY N lot(s) executed at ₹…". The option shows up as an intraday position that can be exited like any other.
   - **Failure:** 400 → error toast; no dedicated option-position screen, no futures trading, and no option sell-to-open protection beyond the generic quantity check.

### (n) Add / remove a watchlist star

1. Star button on any stock/MF card / asset page → `toggleWatchlistItem(symbol, name, assetType)` 1439.
2. If **not** in the set: optimistically `state.watchlist.add(symbol)`, `saveLocalWatchlistSet()` (key `stoxify_watchlist_cache`), star icon fills, toast "Added X to watchlist", then fire-and-forget `POST /api/watchlist {symbol, name, asset_type}` (main.py:923; uid falls back to `"default"` when signed out).
3. If already in the set: remove locally, toast "Removed X from watchlist", then fire-and-forget `DELETE /api/watchlist/{symbol}` (main.py:930).
4. Failures are **silently swallowed** (`try { await fetch(...) } catch (e) {}` at 1447-1461) — the star stays correct locally even if the server write failed, so a later `GET /api/watchlist` can disagree.
5. `GET /api/watchlist` (main.py:894) resolves live quotes for each stored symbol and is rendered by `fetchWatchlist()` 1391, which also merges server symbols back into the local cache.

### (o) View the tax report / P&L / sector allocation

1. Holdings → "Analytics & Tax Report (Budget 2024)" (`switchHoldingsSubnav('analytics')` 357) → `loadPortfolioAnalytics()` 6918 (returns early if guest).
2. `GET /api/analytics/sector-allocation` (main.py:1171) → `get_sector_allocation` (database.py:3158) → stacked bar + legend rendered into `#sectorAllocationContainer` (weights + ₹ values).
3. `GET /api/analytics/tax-report` (main.py:1160) → `get_capital_gains_tax_report` (database.py:3015, Budget-2024 rules: STCG 20 %, LTCG 12.5 %, ₹1.25 L exemption) → fills `#taxStcgGain`, `#taxStcgLiability`, `#taxLtcgGain`, `#taxLtcgTaxable`, `#taxLtcgLiability`, `#taxTotalLiability`.
   - Both calls are in one `try`; on any error the whole analytics pane silently keeps its previous/zero values (`console.error` only, 6975).
4. **Gap:** the response's `trades[]` array (used to populate `#taxTradesTableBody`, index.html:644) is **never rendered**, so the "Tax Trades" table always reads "No realized sell trades to report…". There is no export/download of the P&L or tax statement.

---

## 3. GAPS BETWEEN BACKEND AND UI

### 3.1 Backend capabilities NO UI control reaches

All API routes declared in `main.py` were enumerated and each was checked against `app.js`/`index.html`. The following have **zero callers** (never even a dead-code reference):

| Endpoint (main.py) | What it can do | Why it is unreachable |
|---|---|---|
| `GET /api/ipo/applications` (main.py:1128) | List the user's IPO bids via `get_ipo_bids` | No "My IPO Applications" screen exists. IPOs are fire-and-forget. |
| `DELETE /api/ipo/bid/{bid_id}` (main.py:1135) | Cancel a bid and refund the blocked amount (`cancel_ipo_bid`, database.py:2972) | No withdraw control anywhere. |
| `GET /api/user/list` (main.py:464) | List every user (`list_users`) | No admin/user-picker UI. Also a privacy-leak surface (no auth). |
| `GET /api/trade/charges` (main.py:846) | Server-authoritative charge estimate (`calculate_trade_charges`) | The client re-implements the same math in `calculateEstimatedCharges()` (app.js:1959), so the UI never asks the server. Two sources of truth that can drift. |
| `POST /api/account/deposit` (main.py:940) | Simple balance top-up (`deposit_funds`, database.py:2654) | Superseded in the UI by the simulated-bank `/api/funds/upi-add` flow; the old endpoint is now dark. |

Additionally these **alias routes** exist only as duplicate URL spellings of endpoints the UI already calls via the `/api/...` form (not separate capabilities): `GET /account`, `/portfolio`, `/positions`, `/indices`, `/quote`, `/depth`, `/history`, `/search`, `/watchlist`, `/market-status`, `/order`, `/order/cancel`, `/position/exit`, `/position/exit-all`, `POST /account/deposit`, `/account/restore`, `/account/reset`, `/funds/*`, `POST/PUT/PATCH /api/user/update`, `POST/PUT /api/user/profile`, `DELETE /api/user/current`, and the SPA deep-link routes.

### 3.2 UI affordances that do nothing / render nothing / are broken

| Affordance | Location | What actually happens |
|---|---|---|
| **Legacy trade modal** (`#tradeModalOverlay`, "BUY" button, modal chart `#tradeChartCanvas`, `#modalDepthSection`, watchlist pill) | index.html:1851-2052; app.js `legacyOpenAssetModal()` 1628, `submitOrder()` 2117 | Never opened: `openAssetModal()` (1592) routes to `/stock/…` instead; the only opener, `legacyOpenAssetModal`, has **no caller**. Consequently `loadChartTimeframe` 1761, `renderChart` 1798, `fetchMarketDepth` 1707, `renderMarketDepth` 1717, `renderModalWatchlistBtn` 1743, `calculateOrderMargin` 1938 and `openChargesModal` 2005 are all effectively dead code. |
| **"Active SIPs" tab** (`#sipsTableBody`, `#sipsMobileList`) | app.js `loadActiveSips()` 6841 | Render throws a TypeError on `s.symbol` (server returns `fund_id`/`monthly_amount`, not `symbol`/`amount`/`sip_id`). Table never updates; "Stop SIP" (`cancelSip()` 6899) can never receive a real id. |
| **"GTT & Triggers" tab** (`#gttOrdersTableBody`, `#gttOrdersMobileList`) | app.js `loadGttOrders()` 6207, `cancelGttOrder()` 6272 | Renders `undefined` for order id / side / limit price (`o.order_id`, `o.transaction_type`, `o.limit_price` do not exist on the server rows). Cancel sends `DELETE /api/order/gtt/undefined` → 422 → "Failed to cancel trigger". |
| **GTT ("CREATE GTT TRIGGER") order placement** | app.js `executePageTrade()` 5129 (GTT branch 5179) | Sends `{symbol, transaction_type, quantity, trigger_price, limit_price}` but `GTTRequest` (main.py:1030) requires `name` (missing) and uses `action` + `target_price`/`stop_loss_price`. FastAPI rejects with 422 → "Trade execution failed". No GTT can be created. |
| **Tax trades table** (`#taxTradesTableBody`) | index.html:644 | `loadPortfolioAnalytics()` 6918 never writes to it; the `trades[]` from `/api/analytics/tax-report` is ignored. Always shows the empty state. |
| **"Notify on Open" / "View Listing Details" (IPO)** | app.js `renderIpos()` 6571 | Inline `onclick="showToast('Alert set for …')"` — no alert is stored or delivered. |
| **"All Orders & Contract Notes" (profile menu)** | index.html:1390 | Just `navigateTo('/orders')`; no contract-note generation or download exists anywhere. |
| **"Auto Square-off at 03:20 PM IST"** | index.html:705, 1972 | No server job or client timer performs it. `exit-all` is user-triggered only. |
| **`#chargesModalNote`** | app.js:2071 | Element does not exist in `index.html` → note text branch is a silent no-op. |
| **`#mobOpenOrdersBadge`** | app.js:1202 | Element does not exist → badge update is a no-op (only `#mobOrdersBadge` exists). |
| **Tour step 3 target `stockWatchlistContainer`** | app.js:5997 | Element does not exist; step falls back to `#pane-explore` (works but the step is meaningless). |
| **`#navGetStartedBtn`** | app.js:2700 | Queried via the combined selector `#navAuthBtn, #navGetStartedBtn, #navGuestButtons`; the element itself does not exist (harmless). |
| **Market-timings pill on mobile** | index.html:89 | `.market-status-pill` is `desktop-only`; mobile users can only reach timings via the profile menu. |

### 3.3 Contract mismatches worth flagging (server ↔ UI)

- **SIP list** (server: `fund_id/fund_name/monthly_amount/sip_day/next_installment_date` vs client `symbol/amount/installment_day/next_trigger_date/sip_id/installments_completed`).
- **GTT list** (server: `id/symbol/action/trigger_price/target_price/stop_loss_price` vs client `order_id/transaction_type/limit_price`).
- **GTT create** (server expects `name` + `action`; client sends `transaction_type`, no `name`).
- **IPO bid withdraw** (server `bid_id`; client has no list to obtain one).
- **Order fill trigger** (client expects automatic fills, but the matching loop only runs inside `GET /api/orders`) — see §2(h).

---

## 4. MISSING PRODUCT MECHANICS (present vs absent)

Verified against `main.py`, `database.py`, `market_hours.py`, `fo_service.py`, `ipo_service.py`, `app.js`, `index.html`. "Absent" means no implementation was found in **any** of those files.

### Order types
| Mechanism | Present? | Evidence |
|---|---|---|
| Market order | ✅ | `order_variety='MARKET'`, database.py:1849+ |
| Limit order | ✅ | `is_pending_limit` database.py:1883-1888; OPEN handling 1950-2014 |
| Stop-loss (SL, i.e. SL-Limit) | ✅ | `order_variety in ('STOP_LOSS','SL')`, database.py:1875, 1890-1896; UI `#pageVarietySL` |
| SL-M (stop-loss market) | ❌ | No distinct code path; only SL/LIMIT semantics |
| AMO (After-Market Order) as a user choice | ❌ (silent only) | `validate_order_timing` auto-tags off-hours DELIVERY as AMO (market_hours.py:128); no AMO toggle or AMO order type in the UI |
| GTT (Good-Till-Triggered) | ⚠️ backend present, create broken in UI | `place_gtt_order` database.py:2843; UI create returns 422 (see §2.j). No trigger evaluation exists for `gtt_orders` at all |
| OCO (One-Cancels-Other) | ❌ | No OCO logic anywhere |
| Cover order | ❌ | None |
| Bracket order | ❌ | None |
| Basket / multi-leg orders | ❌ | None |
| Order modification (price/qty) | ❌ | Only cancel exists (`cancel_order` database.py:2437) |

### Product types
| Mechanism | Present? | Evidence |
|---|---|---|
| CNC / Delivery | ✅ | `product_type='DELIVERY'`; holdings table |
| MIS / Intraday | ✅ | `product_type='INTRADAY'`; 20 % margin (database.py:1911); positions table |
| NRML (F&O carry-forward) | ❌ | Options are hard-forced to `INTRADAY` (app.js:6498) |
| MTF (Margin Trading Facility) | ❌ | Zero references |

### Trading features
| Mechanism | Present? | Evidence |
|---|---|---|
| Trade charges estimation | ✅ | Client `calculateEstimatedCharges` 1959 + server `calculate_trade_charges` database.py:1769 (unused by UI) |
| Order history filters | ⚠️ partial | Only status sub-tabs `switchOrdersSubnav()` 336 (Executed/Open/GTT); `GET /api/orders` supports only `limit` + `status`; no date/symbol/date-range filter |
| Order history / ledger export | ❌ | No CSV/PDF generation anywhere |
| P&L report download | ❌ | On-screen analytics only |
| Contract notes | ❌ | Label only (profile menu) |
| Ledger statement | ❌ | Bank passbook transactions exist; no trading ledger |
| Realized P&L per order | ✅ | `realized_pnl` shown in Executed Orders |
| Tax report (STCG/LTCG) | ✅ | `get_capital_gains_tax_report` database.py:3015 |
| Sector allocation | ✅ | `get_sector_allocation` database.py:3158 |

### Funds, IPO, MF, F&O extras
| Mechanism | Present? | Evidence |
|---|---|---|
| Add / withdraw money (simulated) | ✅ | `/api/funds/upi-add`, `/api/funds/withdraw` |
| Bank passbook / statement | ✅ | `get_bank_account_details` → transactions list |
| IPO ASBA apply | ✅ | `/api/ipo/apply` |
| IPO allotment / listing credit | ❌ | Bids stay `APPLIED` forever; no allotment job, no listing into holdings |
| IPO bid withdraw | ❌ (backend only) | `/api/ipo/bid/{id}` has no UI |
| SIP create / cancel | ⚠️ create works, list/cancel broken | see §2(k) |
| SIP auto-debit execution | ❌ | No scheduler executes SIP installments; `sips` is a stored schedule only |
| F&O option chain + buy/sell | ✅ | `fo_service.get_option_chain`; `/api/order` with `asset_type='OPTION'` |
| Futures trading | ❌ | None |
| F&O margin / NRML / expiry settlement | ❌ | Options forced INTRADAY |
| Intraday auto square-off | ❌ | No scheduler (see §3.2) |

### Accounts, identity & safety
| Mechanism | Present? | Evidence |
|---|---|---|
| Real authentication (session/token) | ❌ | Identity is a client-supplied `X-User-Id` header / `?user_id=` (main.py:68); full user rows (including plaintext `pin`/`password`) are returned to the client and cached in localStorage (`stoxify_cached_user`). |
| Password/PIN hashing | ❌ | `users.password` / `users.pin` are plain `TEXT` (database.py:166), compared in plaintext (main.py:424-427). No `bcrypt`/`hashlib` anywhere. |
| KYC flow | ❌ | Onboarding collects PAN/DOB but there is no verification (cosmetic "Verified with Income Tax Department" pill, app.js:5602). "KYC Verified ✓" badges are static. |
| Nominee | ❌ | Zero references |
| Bank account management (add / multiple / re-verify) | ⚠️ single only | One bank stored on the user; editable in Edit Profile; the "penny drop" is a `setTimeout` |
| Multi-account support | ❌ | One active session; `stoxify_recent_accounts` are login shortcuts only |
| Referral | ❌ | Zero references |
| Community / social | ❌ | Zero references |
| Disclaimers | ⚠️ | Simulated-trading labelling exists ("Simulated Gateway", "Virtual Trading Simulation"); marketing copy actively pushes "NO INCOME PROOF NEEDED" (index.html:381) |

### Market data & discovery
| Mechanism | Present? | Evidence |
|---|---|---|
| Index pages | ⚠️ partial | Indices bar + clickable index asset pages (`openAssetModal('^NSEI')`); no dedicated index page/lists |
| ETF pages | ❌ | None |
| Sector / market movers pages | ⚠️ partial | Only client-side filter pills over a fixed NSE sample (`renderExploreStocks()` 720); no dedicated movers page |
| Screener | ❌ | Zero references |
| Collections / curated lists | ❌ | Zero references |
| News feed | ⚠️ per-stock only | `fetchStockNews()` 7190; no market-wide news page |
| Fundamentals in UI | ✅ | Financials / Shareholding / Peers / News tabs + fundamentals grid + Level-2 depth |
| Price alerts | ❌ | Only an IPO toast ("Alert set for …") |
| Notifications (push / in-app inbox) | ❌ | Only transient toasts; `sw.js` has no push handlers |
| Offline mode / cached market data | ❌ | `sw.js` skips `/api/` entirely and only cache-firsts icons |

---

## 5. STATE, DATA & POLLING

### 5.1 Client state
- A single mutable global `state` object (app.js:78-93): `currentTab`, `exploreSubnav`, `ordersSubnav`, `exploreStockFilter`, `exploreData`, `account {balance, bank_balance}`, `watchlist` (a `Set`), `currentModalAsset`, `currentModalTimeframe`, `orderAction`, `productType`, `orderVariety`, `marketStatus`, `chartInstance`.
- Parallel globals outside `state`: `currentUser` (32), `pageOrderState` (3860), `currentPageAsset` (3859), `currentOptionTrade` (6292), `currentIpoModalData` (65547), `obUserData` (5274), `sandboxMockState` (5797), `allIpos` (65545), request-coalescing `portfolioRequest`/`positionsRequest` (844-845, 1000-1001), chart globals (4155-4157, 4187).
- **Optimistic UI:** watchlist stars and quantity helpers update immediately, but every trade/fund action awaits an authoritative refetch (`fetchAccount/fetchPortfolio/fetchPositions/fetchOrders`) before showing the success modal.
- **Routing:** hand-rolled History API router (`navigateTo` 2588, `handleRoute` 2626, `popstate` 2662); `/stock/{sym}`, `/mf/{sym}`, `/profile`, `/onboarding`, `/login`, `/holdings`, `/positions`, `/orders`, `/watchlist`, `/explore`.

### 5.2 Every localStorage / sessionStorage key
| Key | Where | Purpose |
|---|---|---|
| `stoxify_user_id` | app.js:17,24,39,2681,2790,3359,3579,5762 | The identity sent as `X-User-Id` |
| `stoxify_cached_user` | 26,2224,2517,2682,2960,3026,3404,3575,5763,5849 | Full user JSON cache (includes `balance`, `pin`, `bank_account`) |
| `stoxify_guest_mode` | 25,226,2518,2668,2789,2790,5761 | `'true'` = signed-out guest |
| `stoxify_theme` | 22,147,157 | `dark` / `light` |
| `stoxify_watchlist_cache` | 61,73,463 | Local set of starred symbols (mirrors the server list) |
| `stoxify_recent_accounts` | 2322,3717,3727 | Up to 5 saved accounts for the login modal |
| `stoxify_recent_stocks` | 596,608,627 | Up to 10 recently viewed stocks |
| `stoxify_recent_mutual_funds` | 596,608,627 | Up to 10 recently viewed funds |
| `stoxify_explore_cache` | 464,475 | Last good `/api/explore` payload (fallback render) |
| `stoxify_app_installed` | 2512 | Removed on every boot (legacy) |
| `sessionStorage.stoxify_preselect_action` | 1595,3992,3999 | Carry BUY/SELL choice across the route change |
| `sessionStorage.stoxify_holding_sale` | 1619,3995,3997 | Carry {symbol, quantity, product} for a Holdings "Sell" |
| `sessionStorage.stoxify_mob_install_dismissed` | 2365 | Dismiss mobile install banner for the session |

Also an in-boot migration shim (app.js:4-14) that copies legacy un-prefixed keys (`user_id`, `cached_user`, `theme`, …) to `stoxify_*`.

### 5.3 Polling intervals
| Interval | Period | What it does | Location |
|---|---|---|---|
| `fetchMarketStatus()` | **10 s** | `GET /api/market-status`, updates pill + modal clock | app.js:2569 |
| indices + tab-aware portfolio/positions | **20 s** | `fetchIndices()` always; `fetchPortfolio()` when on holdings; `fetchPositions()` when on positions | app.js:2570-2574 |
| Asset-page live tick | **5 s** | `GET /api/quote` for the open asset; mutates the last chart point | app.js:4725 |
| Orders refresh | event-driven | `fetchOrders()` runs on navigation, after trades, and **is the only place `service_pending_orders` / limit-order matching is evaluated** | main.py:885-892 |
| Watchlist | event-driven | on navigation / star toggle | 1391 |
| SIP / GTT / IPO applications | event-driven (nothing on a timer) | — | — |

No polling/interval exists for: pending limit fills (they piggyback on `/api/orders`), GTT triggers, SIP debits, intraday auto square-off, IPO allotment, or alerts.

### 5.4 API base URL resolution
There is none. Every request uses a **root-relative path** (`fetch('/api/...')`), so the API is always same-origin. `main.py` additionally rewrites Vercel-style paths (`/api/index.py/...`) in a middleware (main.py:45-59) and serves the SPA for deep links (main.py:1179-1198). `<script src="/static/app.js?v=7.2">` and `style.css?v=7.2` use `onerror` fallbacks to `/app.js` / `/style.css`.

### 5.5 How the user id is transmitted
A global `window.fetch` interceptor (app.js:36-48) injects the header `X-User-Id: <stoxify_user_id>` on **every** request whenever the value is not `default`/`guest`. The server reads `request.headers.get('x-user-id') or request.query_params.get('user_id')` (main.py:68-72), rejecting `default/guest/null/undefined/''`. Money endpoints also pass `?user_id=` explicitly (3155, 3387, 3562) plus a redundant body `user_id`. Consequence: the "session" is entirely client-controlled — anyone can act as any user id by setting the header; there is no token, signature, or expiry.

### 5.6 Failure behaviour when a request fails
Mixed, and mostly **silent**:
- **Silent `console.error` / `console.warn` only** (no user feedback): `fetchMarketStatus` (216), `fetchAccount` (394), `fetchIndices` (419), `fetchExploreData` (503, falls back to cache), `fetchPortfolioInternal` (995), `fetchPositionsInternal` (1140), `fetchOrders` (1360), `fetchWatchlist` (1435), `fetchPageMarketDepth` (4113), `loadPageChartTimeframe` (4709), the 5 s quote tick (4757), `loadBankAccountDetails` (3066), `loadPortfolioAnalytics` (6976), `loadActiveSips` (6895), `loadGttOrders` (6268), `fetchStockFinancials/Shareholding/Peers/News` (each logs + shows an inline "temporarily unavailable" message), `fetchOptionChain` (inline message).
- **Toast (error):** trade submission (`executePageTrade` 5264, `submitOrder` 2210), `cancelOrder` 1386, `exitPosition` 1162, `squareOffAllPositions` 1176, `executeUpiPayment` (inline `#upiPinError` + console), `executeWithdrawal` (inline), `submitLogin` 3844, `saveUserProfile` 3034, `submitObStep5` 5783, `submitSipSchedule` 6837, `submitIpoApplication` 6732, `submitOptionTrade` 6532, `cancelSip`/`cancelGttOrder`, `restoreFullBalance`/`resetEntirePortfolio`/`confirmDeleteAccount`, `toggleSimulationMode`.
- **Native `confirm()` dialogs** gate destructive actions: `exitPosition` 1145, `squareOffAllPositions` 1167, `resetEntirePortfolio` 2278, `confirmDeleteAccount` 2309.
- **Fire-and-forget with swallowed errors:** watchlist add/remove (1447-1461), `markTourCompleteOnServer` (5856).
- No request has a retry, backoff, offline queue, or global fetch-error handler (other than the timeout `AbortController` on `/api/explore`, app.js:2490-2492).

---

## Appendix — notable server-side facts that shape the UI

- New users are created with ₹10,00,000 in **both** `balance` and `bank_balance`, so "Add Money"/bank balance and virtual cash are two separate ledgers (database.py:728+ / `transfer_bank_to_wallet` database.py:1140, `withdraw_wallet_to_bank` database.py:1244).
- The simulated matching engine fills resting LIMIT and STOP_LOSS orders only when `GET /api/orders` is called (`service_pending_orders`, main.py:856-892); fills claim the order atomically through `cancel_order`'s `CANCELLING` guard (database.py:2457-2464).
- `GET /api/depth` fabricates bids/asks with `random.randint` around the LTP (main.py:528-539); index/depth/fundamental values in the UI have hardcoded fallbacks.
- `market_hours.validate_order_timing` **never blocks** any order: INTRADAY always passes (market_hours.py:118-122), DELIVERY is allowed on/off hours (tagged AMO), so market-hours enforcement is effectively cosmetic.
- The full user object (including `pin` and `password`) is returned by `/api/user/login` and `/api/user/current` and cached client-side — a data-exposure consideration inherent to the x-user-id auth model.
