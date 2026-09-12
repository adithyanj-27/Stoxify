// Stoxify — Core Client Application Logic & Feature Engine

// Transparently migrate legacy storage keys into stoxify namespace
(function migrateStorage() {
  try {
    const keys = ['user_id', 'cached_user', 'theme', 'guest_mode', 'watchlist_cache', 'recent_accounts', 'app_installed', 'explore_cache'];
    keys.forEach(k => {
      const oldVal = localStorage.getItem('stoxify_' + k);
      if (oldVal !== null && localStorage.getItem('stoxify_' + k) === null) {
        localStorage.setItem('stoxify_' + k, oldVal);
      }
    });
  } catch (e) {}
})();

// Clean up legacy default session so unauthenticated visitors start in clean Guest mode
if (localStorage.getItem('stoxify_user_id') === 'default') {
  localStorage.removeItem('stoxify_user_id');
}

// Enable immediate CSS :active touch states on mobile WebKit/iOS/Android
document.addEventListener('touchstart', function() {}, { passive: true });

function isGuest() {
  if (localStorage.getItem('stoxify_guest_mode') === 'true') {
    return true;
  }
  const uid = localStorage.getItem('stoxify_user_id');
  return (!uid || uid === 'default' || uid === 'guest') && (!currentUser || currentUser.is_guest);
}

let currentUser = null;

// --- Active User Session & X-User-Id HTTP Interceptor ---
const _nativeFetch = window.fetch;
window.fetch = function(input, init = {}) {
  init = init || {};
  init.headers = init.headers || {};
  const uid = localStorage.getItem('stoxify_user_id');
  if (uid && uid !== 'default' && uid !== 'guest') {
    if (init.headers instanceof Headers) {
      init.headers.set('X-User-Id', uid);
    } else {
      init.headers['X-User-Id'] = uid;
    }
  }
  return _nativeFetch(input, init);
};


const INDEX_NAMES = {
  '^NSEI': 'NIFTY 50',
  '^BSESN': 'SENSEX',
  '^NSEBANK': 'BANK NIFTY',
  '^CNXIT': 'NIFTY IT',
  '^NSEMDCP50': 'NIFTY MIDCAP 50'
};

function getLocalWatchlistSet() {
  try {
    const raw = localStorage.getItem('stoxify_watchlist_cache');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return new Set(parsed);
    }
  } catch (e) {}
  return new Set();
}

function saveLocalWatchlistSet(set) {
  try {
    if (set) {
      localStorage.setItem('stoxify_watchlist_cache', JSON.stringify(Array.from(set)));
    }
  } catch (e) {}
}

const state = {
  currentTab: 'explore',
  exploreSubnav: 'stocks',
  ordersSubnav: 'executed',
  exploreStockFilter: 'all',
  exploreData: null,
  account: { balance: 0.0, bank_balance: 1000000.0 },
  watchlist: getLocalWatchlistSet(),
  currentModalAsset: null,
  currentModalTimeframe: '1D',
  orderAction: 'BUY',
  productType: 'DELIVERY',
  orderVariety: 'MARKET',
  marketStatus: null,
  chartInstance: null
};

// --- Helpers & Formatters ---
function getActiveAvailableCash() {
  if (state.account && typeof state.account.balance === 'number' && state.account.balance > 0) {
    return state.account.balance;
  }
  if (currentUser && typeof currentUser.balance === 'number' && currentUser.balance > 0) {
    return currentUser.balance;
  }
  if (state.account && state.account.balance !== undefined) {
    return state.account.balance;
  }
  if (currentUser && currentUser.balance !== undefined) {
    return currentUser.balance;
  }
  return 0.0;
}

function formatINR(val) {
  if (val === null || val === undefined || isNaN(val)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(val);
}

function formatNumber(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) return '0.00';
  return Number(val).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

function roundNumber(val, decimals = 2) {
  return Number(Math.round(val + 'e' + decimals) + 'e-' + decimals);
}

function formatChange(change, changePct) {
  const isPos = change >= 0;
  const sign = isPos ? '+' : '';
  return `${sign}${formatNumber(change)} (${sign}${formatNumber(changePct)}%)`;
}

function formatMarketCap(val) {
  if (val === null || val === undefined || isNaN(val) || Number(val) <= 0) return '—';
  const cr = Number(val) / 1e7;
  if (cr >= 100000) {
    return '₹' + (cr / 100000).toFixed(2) + 'L Cr';
  }
  return '₹' + cr.toLocaleString('en-IN', { maximumFractionDigits: 1 }) + ' Cr';
}

// --- Toast Notifications ---
function showToast(message, isError = false) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${isError ? 'error' : ''}`;
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${isError ? '#eb5b3c' : '#00d09c'}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
      ${isError 
        ? '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>' 
        : '<polyline points="20 6 9 17 4 12"></polyline>'}
    </svg>
    <span style="flex: 1; min-width: 0; word-break: break-word;">${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 320);
  }, 4200);
}

// --- Theme Management ---
function initTheme() {
  const saved = localStorage.getItem('stoxify_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
  updateFaviconAndMeta(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('stoxify_theme', next);
  updateThemeIcon(next);
  updateFaviconAndMeta(next);
  if (state.chartInstance && state.currentModalAsset) {
    loadChartTimeframe(state.currentModalTimeframe);
  }
}

function updateFaviconAndMeta(theme) {
  const faviconEl = document.getElementById('dynamicFavicon');
  if (faviconEl) {
    faviconEl.href = theme === 'light' ? '/static/favicon-light.png' : '/static/favicon-dark.png';
  }
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute('content', theme === 'light' ? '#F3EFE6' : '#080D14');
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (theme === 'light') {
    icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
  } else {
    icon.innerHTML = `
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    `;
  }
}

// --- Market Status Polling & Timings ---
async function fetchMarketStatus() {
  try {
    const res = await fetch('/api/market-status');
    const data = await res.json();
    state.marketStatus = data;

    const dot = document.getElementById('marketPulseDot');
    const label = document.getElementById('marketStatusText');

    if (dot) dot.className = `pulse-dot ${data.badge_color || 'gray'}`;
    if (label) label.innerText = data.status_text;

    // Update modal
    const clockEl = document.getElementById('modalClockIst');
    if (clockEl) clockEl.innerText = data.current_time_ist;
    const dateEl = document.getElementById('modalMarketDate');
    if (dateEl) dateEl.innerText = `${data.date_ist} • ${data.subtext}`;
  } catch (err) {
    console.error('Failed to fetch market status:', err);
  }
}

function openMarketHoursModal() {
  const menu = document.getElementById('userDropdownMenu');
  if (menu) menu.style.display = 'none';
  const overlay = document.getElementById('marketHoursModalOverlay');
  if (overlay) overlay.classList.add('active');
  fetchMarketStatus();
}

function closeMarketHoursModal() {
  const overlay = document.getElementById('marketHoursModalOverlay');
  if (overlay) overlay.classList.remove('active');
}

// --- Navigation Tabs (Desktop & Mobile Synchronized) ---
function switchTab(tabId, updateUrl = true) {
  document.body.classList.remove('viewing-asset-detail');
  document.documentElement.classList.remove('viewing-asset-detail');
  document.body.classList.remove('viewing-profile');
  document.documentElement.classList.remove('viewing-profile');
  closeMobileTradeDrawer();

  if (updateUrl) {
    const targetUrl = tabId === 'explore' ? '/explore' : `/${tabId}`;
    if (window.location.pathname !== targetUrl) {
      history.pushState(null, '', targetUrl);
    }
  }
  state.currentTab = tabId;

  // Desktop links
  document.querySelectorAll('.nav-links .nav-btn').forEach(btn => btn.classList.remove('active'));
  const desktopBtn = document.getElementById(`nav-${tabId}`);
  if (desktopBtn) desktopBtn.classList.add('active');

  // Mobile bottom bar items (Explore, Holdings, Positions, Orders, Watchlist)
  document.querySelectorAll('.mobile-bottom-bar .mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  const mobBottomBtn = document.getElementById(`mob-nav-${tabId}`);
  if (mobBottomBtn) mobBottomBtn.classList.add('active');

  // Pane activation
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
  const pane = document.getElementById(`pane-${tabId}`);
  if (pane) pane.classList.add('active');

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (tabId === 'holdings') fetchPortfolio();
  if (tabId === 'positions') fetchPositions();
  if (tabId === 'orders') fetchOrders();
  if (tabId === 'watchlist') fetchWatchlist();
  if (tabId === 'explore') fetchExploreData();
}

function navigateToExploreTab(subId) {
  navigateTo('/explore');
  switchExploreSubnav(subId);
  updateMobileBottomNav(subId);
}

function updateMobileBottomNav(activeId) {
  document.querySelectorAll('.mobile-bottom-bar .mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`mob-nav-${activeId}`);
  if (activeBtn) activeBtn.classList.add('active');
}

function toggleMobileSearch() {
  const wrapper = document.querySelector('.search-wrapper');
  if (wrapper) {
    wrapper.classList.toggle('mobile-open');
    if (wrapper.classList.contains('mobile-open')) {
      const input = document.getElementById('globalSearchInput');
      if (input) input.focus();
    }
  }
}

function switchExploreSubnav(subId) {
  state.exploreSubnav = subId;
  document.querySelectorAll('#pane-explore .sub-nav-btn').forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById(`subnav-${subId}`);
  if (btn) btn.classList.add('active');
  updateMobileBottomNav(subId);

  const containers = {
    stocks: document.getElementById('explore-stocks-container'),
    fo: document.getElementById('explore-fo-container'),
    mf: document.getElementById('explore-mf-container'),
    ipo: document.getElementById('explore-ipo-container')
  };

  Object.keys(containers).forEach(k => {
    if (containers[k]) containers[k].style.display = (k === subId) ? 'block' : 'none';
  });

  if (subId === 'stocks') {
    renderRecentlyViewedStocks();
    if (!state.exploreData) fetchExploreData();
  } else if (subId === 'fo') {
    fetchOptionChain();
  } else if (subId === 'mf') {
    renderExploreMutualFunds();
  } else if (subId === 'ipo') {
    fetchIpos();
  }
}

function switchOrdersSubnav(subId) {
  state.ordersSubnav = subId;
  document.querySelectorAll('#pane-orders .sub-nav-btn').forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById(`subnav-${subId}`);
  if (btn) btn.classList.add('active');

  const exec = document.getElementById('orders-executed-container');
  const open = document.getElementById('orders-open-container');
  const gtt = document.getElementById('orders-gtt-container');

  if (exec) exec.style.display = (subId === 'executed') ? 'block' : 'none';
  if (open) open.style.display = (subId === 'open') ? 'block' : 'none';
  if (gtt) gtt.style.display = (subId === 'gtt') ? 'block' : 'none';

  if (subId === 'executed' || subId === 'open') {
    fetchOrders();
  } else if (subId === 'gtt') {
    loadGttOrders();
  }
}

function switchHoldingsSubnav(subId) {
  document.querySelectorAll('#pane-holdings .sub-nav-btn').forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById(`subnav-holdings-${subId}`);
  if (btn) btn.classList.add('active');

  const list = document.getElementById('holdings-list-container');
  const analytics = document.getElementById('holdings-analytics-container');
  const sips = document.getElementById('holdings-sips-container');

  if (list) list.style.display = (subId === 'list') ? 'block' : 'none';
  if (analytics) analytics.style.display = (subId === 'analytics') ? 'block' : 'none';
  if (sips) sips.style.display = (subId === 'sips') ? 'block' : 'none';

  if (subId === 'list') {
    fetchPortfolio();
  } else if (subId === 'analytics') {
    loadPortfolioAnalytics();
  } else if (subId === 'sips') {
    loadActiveSips();
  }
}

// --- Account Balance & Header ---
async function fetchAccount() {
  try {
    const res = await fetch('/api/account');
    const data = await res.json();
    state.account = data;
    if (currentUser) {
      currentUser.balance = data.balance;
      if (data.bank_balance !== undefined) currentUser.bank_balance = data.bank_balance;
      try { localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser)); } catch (e) {}
    }
    const navBal = document.getElementById('navBalanceDisplay');
    if (navBal) navBal.innerText = formatINR(data.balance);
    const menuBal = document.getElementById('menuUserBalance');
    if (menuBal) menuBal.innerText = formatINR(data.balance);
    const summaryBal = document.getElementById('summaryAvailableBalance');
    if (summaryBal) summaryBal.innerText = formatINR(data.balance);
    const fundsBal = document.getElementById('fundsCurrentBalance');
    if (fundsBal) fundsBal.innerText = formatINR(data.balance);

    // Sync asset page and order confirmation cash elements
    const pageCashEl = document.getElementById('pageAvailableCash');
    if (pageCashEl && !isGuest()) pageCashEl.innerText = formatINR(data.balance);
    const drawerCashEl = document.getElementById('drawerAvailableCash');
    if (drawerCashEl && !isGuest()) drawerCashEl.innerText = formatINR(data.balance);
    const orderCashEl = document.getElementById('orderAvailableBalance');
    if (orderCashEl && !isGuest()) orderCashEl.innerText = formatINR(data.balance);
    const confirmCashEl = document.getElementById('confirmOrderAvailCash');
    if (confirmCashEl && !isGuest()) confirmCashEl.innerText = formatINR(data.balance);

    const assetPane = document.getElementById('pane-asset-detail');
    if (assetPane && assetPane.classList.contains('active')) {
      recalcPageMargin();
    }
  } catch (err) {
    console.error('Failed to fetch account:', err);
  }
}

// --- Indices Bar ---
async function fetchIndices() {
  try {
    const res = await fetch('/api/indices');
    const indices = await res.json();
    const container = document.getElementById('indicesBar');
    container.innerHTML = indices.map(idx => {
      const isPos = idx.change >= 0;
      const colorClass = isPos ? 'text-positive' : 'text-negative';
      const sign = isPos ? '+' : '';
      return `
        <div class="index-pill" onclick="openAssetModal('${idx.symbol}', 'STOCK')">
          <span class="name">${idx.short || idx.name}</span>
          <span class="price">${formatNumber(idx.price)}</span>
          <span class="${colorClass}" style="font-size: 0.75rem; font-weight: 600;">
            ${sign}${formatNumber(idx.change)} (${sign}${formatNumber(idx.change_pct)}%)
          </span>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to fetch indices:', err);
  }
}

const DEFAULT_EXPLORE_DATA = {
  all_stocks: [
    { symbol: 'RELIANCE.NS', name: 'Reliance Industries Ltd', price: 1322.00, change: 19.50, change_pct: 1.50, sector: 'Energy', asset_type: 'STOCK' },
    { symbol: 'TCS.NS', name: 'Tata Consultancy Services Ltd', price: 2304.00, change: -16.10, change_pct: -0.69, sector: 'IT', asset_type: 'STOCK' },
    { symbol: 'HDFCBANK.NS', name: 'HDFC Bank Ltd', price: 1684.50, change: 12.30, change_pct: 0.74, sector: 'Banking', asset_type: 'STOCK' },
    { symbol: 'INFY.NS', name: 'Infosys Ltd', price: 1820.00, change: -8.50, change_pct: -0.46, sector: 'IT', asset_type: 'STOCK' },
    { symbol: 'ICICIBANK.NS', name: 'ICICI Bank Ltd', price: 1248.00, change: 14.20, change_pct: 1.15, sector: 'Banking', asset_type: 'STOCK' },
    { symbol: 'SBIN.NS', name: 'State Bank of India', price: 1016.10, change: -7.25, change_pct: -0.71, sector: 'Banking', asset_type: 'STOCK' },
    { symbol: 'BHARTIARTL.NS', name: 'Bharti Airtel Ltd', price: 1635.00, change: 22.40, change_pct: 1.39, sector: 'Telecom', asset_type: 'STOCK' },
    { symbol: 'ITC.NS', name: 'ITC Ltd', price: 482.00, change: -2.10, change_pct: -0.43, sector: 'Consumer', asset_type: 'STOCK' },
    { symbol: 'HAL.NS', name: 'Hindustan Aeronautics Ltd', price: 4856.00, change: 90.50, change_pct: 1.90, sector: 'Defense', asset_type: 'STOCK' },
    { symbol: 'BEL.NS', name: 'Bharat Electronics Ltd', price: 304.00, change: 4.50, change_pct: 1.50, sector: 'Defense', asset_type: 'STOCK' },
    { symbol: 'IRFC.NS', name: 'Indian Railway Finance Corp', price: 156.00, change: 2.40, change_pct: 1.56, sector: 'Railways', asset_type: 'STOCK' },
    { symbol: 'RVNL.NS', name: 'Rail Vikas Nigam Ltd', price: 525.00, change: 14.00, change_pct: 2.74, sector: 'Railways', asset_type: 'STOCK' },
    { symbol: 'TATAPOWER.NS', name: 'Tata Power Company Ltd', price: 418.00, change: 5.80, change_pct: 1.41, sector: 'Energy', asset_type: 'STOCK' },
    { symbol: 'SUZLON.NS', name: 'Suzlon Energy Ltd', price: 66.50, change: 1.20, change_pct: 1.84, sector: 'Energy', asset_type: 'STOCK' },
    { symbol: 'ETERNAL.NS', name: 'Zomato Ltd (Eternal Ltd)', price: 262.00, change: 5.40, change_pct: 2.10, sector: 'Consumer', asset_type: 'STOCK' },
    { symbol: 'JIOFIN.NS', name: 'Jio Financial Services Ltd', price: 324.50, change: 3.80, change_pct: 1.18, sector: 'Finance', asset_type: 'STOCK' }
  ],
  gainers: [
    { symbol: 'RVNL.NS', name: 'Rail Vikas Nigam Ltd', price: 525.00, change: 14.00, change_pct: 2.74, sector: 'Railways', asset_type: 'STOCK' },
    { symbol: 'ETERNAL.NS', name: 'Zomato Ltd (Eternal Ltd)', price: 262.00, change: 5.40, change_pct: 2.10, sector: 'Consumer', asset_type: 'STOCK' },
    { symbol: 'HAL.NS', name: 'Hindustan Aeronautics Ltd', price: 4856.00, change: 90.50, change_pct: 1.90, sector: 'Defense', asset_type: 'STOCK' },
    { symbol: 'SUZLON.NS', name: 'Suzlon Energy Ltd', price: 66.50, change: 1.20, change_pct: 1.84, sector: 'Energy', asset_type: 'STOCK' }
  ],
  losers: [
    { symbol: 'TCS.NS', name: 'Tata Consultancy Services Ltd', price: 2304.00, change: -16.10, change_pct: -0.69, sector: 'IT', asset_type: 'STOCK' },
    { symbol: 'SBIN.NS', name: 'State Bank of India', price: 1016.10, change: -7.25, change_pct: -0.71, sector: 'Banking', asset_type: 'STOCK' },
    { symbol: 'ITC.NS', name: 'ITC Ltd', price: 482.00, change: -2.10, change_pct: -0.43, sector: 'Consumer', asset_type: 'STOCK' },
    { symbol: 'INFY.NS', name: 'Infosys Ltd', price: 1820.00, change: -8.50, change_pct: -0.46, sector: 'IT', asset_type: 'STOCK' }
  ],
  mutual_funds: [
    { symbol: '120503', name: 'Axis Small Cap Fund Direct Growth', price: 96.40, change: 0.85, change_pct: 0.89, category: 'Small Cap Equity', return_1y: 28.4, rating: 5, asset_type: 'MUTUAL_FUND' },
    { symbol: '118989', name: 'Mirae Asset Large Cap Fund Direct Growth', price: 114.20, change: 0.60, change_pct: 0.53, category: 'Large Cap Equity', return_1y: 21.2, rating: 5, asset_type: 'MUTUAL_FUND' },
    { symbol: '120716', name: 'UTI Nifty 50 Index Fund Direct Growth', price: 172.50, change: 1.10, change_pct: 0.64, category: 'Index Fund', return_1y: 23.5, rating: 5, asset_type: 'MUTUAL_FUND' },
    { symbol: '125354', name: 'Parag Parikh Flexi Cap Fund Direct Growth', price: 78.90, change: 0.70, change_pct: 0.90, category: 'Flexi Cap Equity', return_1y: 26.1, rating: 5, asset_type: 'MUTUAL_FUND' }
  ]
};

function loadStoredExploreData() {
  try {
    const raw = localStorage.getItem('stoxify_explore_cache');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && parsed.all_stocks && parsed.all_stocks.length > 0) return parsed;
    }
  } catch (e) {}
  return DEFAULT_EXPLORE_DATA;
}

function saveStoredExploreData(data) {
  try {
    localStorage.setItem('stoxify_explore_cache', JSON.stringify(data));
  } catch (e) {}
}

// --- Explore View ---
async function fetchExploreData() {
  // 1. Immediately render cached or bundled data so user never waits for an eternity
  if (!state.exploreData || !state.exploreData.all_stocks || state.exploreData.all_stocks.length === 0) {
    state.exploreData = loadStoredExploreData();
    renderExploreStocks();
    renderExploreMutualFunds();
  }

  // 2. Fetch fresh live quotes in background with timeout
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    const res = await fetch('/api/explore', { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.all_stocks && data.all_stocks.length > 0) {
      state.exploreData = data;
      saveStoredExploreData(data);
      renderExploreStocks();
      renderExploreMutualFunds();
    }
  } catch (err) {
    console.warn('Explore live fetch error (using cached/fallback):', err);
    if (!state.exploreData || !state.exploreData.all_stocks || state.exploreData.all_stocks.length === 0) {
      state.exploreData = loadStoredExploreData();
      renderExploreStocks();
      renderExploreMutualFunds();
    }
  }
}

function filterExploreStocks(filter) {
  state.exploreStockFilter = filter;
  document.querySelectorAll('.filter-pills .pill-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  renderExploreStocks();
}

// --- Company Domain Mapping for Automated High-Res Logo Resolution ---
const SYMBOL_DOMAINS = {
  'RELIANCE': 'ril.com',
  'TCS': 'tcs.com',
  'HDFCBANK': 'hdfcbank.com',
  'INFY': 'infosys.com',
  'ICICIBANK': 'icicibank.com',
  'SBIN': 'sbi.co.in',
  'BHARTIARTL': 'airtel.in',
  'ITC': 'itcportal.com',
  'LT': 'larsentoubro.com',
  'BAJFINANCE': 'bajajfinserv.in',
  'HINDUNILVR': 'hul.co.in',
  'MARUTI': 'marutisuzuki.com',
  'SUNPHARMA': 'sunpharma.com',
  'TITAN': 'titancompany.in',
  'TATASTEEL': 'tatasteel.com',
  'ADANIENT': 'adanienterprises.com',
  'ADANIPORTS': 'adaniports.com',
  'WIPRO': 'wipro.com',
  'POWERGRID': 'powergrid.in',
  'NTPC': 'ntpc.co.in',
  'ONGC': 'ongcindia.com',
  'COALINDIA': 'coalindia.in',
  'M&M': 'mahindra.com',
  'TMCV': 'tatamotors.com',
  'TMPV': 'tatamotors.com',
  'TATAMOTORS': 'tatamotors.com',
  'AXISBANK': 'axisbank.com',
  'KOTAKBANK': 'kotak.com',
  'ULTRACEMCO': 'ultratechcement.com',
  'ASIANPAINT': 'asianpaints.com',
  'BAJAJ-AUTO': 'bajajauto.com',
  'TRENT': 'mywestside.com',
  'JIOFIN': 'jiofinancialservices.com',
  'ETERNAL': 'zomato.com',
  'ZOMATO': 'zomato.com',
  'HAL': 'hal-india.co.in',
  'BEL': 'bel-india.in',
  'MAZDOCK': 'mazagondock.in',
  'COCHINSHIP': 'cochinshipyard.in',
  'GRSE': 'grse.in',
  'BDL': 'bdl-india.in',
  'IRFC': 'irfc.co.in',
  'IRCTC': 'irctc.co.in',
  'RVNL': 'rvnl.org',
  'RAILTEL': 'railtelindia.com',
  'BHEL': 'bhel.com',
  'TATAPOWER': 'tatapower.com',
  'SUZLON': 'suzlon.com',
  'IREDA': 'ireda.in',
  'ADANIGREEN': 'adanigreenenergy.com',
  'ADANIPOWER': 'adanipower.com',
  'NHPC': 'nhpcindia.com',
  'PFC': 'pfcindia.com',
  'RECLTD': 'recindia.nic.in',
  'BANKBARODA': 'bankofbaroda.in',
  'PNB': 'pnbindia.in',
  'CANBK': 'canarabank.com',
  'IDFCFIRSTB': 'idfcfirstbank.com',
  'FEDERALBNK': 'federalbank.co.in',
  'YESBANK': 'yesbank.in',
  'INDUSINDBK': 'indusind.com',
  'AUBANK': 'aubank.in',
  'BANDHANBNK': 'bandhanbank.com',
  'BSE': 'bseindia.com',
  'CDSL': 'cdslindia.com',
  'MCX': 'mcxindia.com',
  'PAYTM': 'paytm.com',
  'CIPLA': 'cipla.com',
  'DRREDDY': 'drreddys.com',
  'APOLLOHOSP': 'apollohospitals.com',
  'EICHERMOT': 'eichermotors.com',
  'TVSMOTOR': 'tvsmotor.com',
  'ASHOKLEY': 'ashokleyland.com',
  'MRF': 'mrfindia.com',
  'JSWSTEEL': 'jsw.in',
  'HINDALCO': 'hindalco.com',
  'VEDL': 'vedantalimited.com',
  'TATAELXSI': 'tataelxsi.com',
  'TATATECH': 'tatatechnologies.com',
  'NYKAA': 'nykaa.com',
  'DMART': 'dmartindia.com',
  'POLICYBZR': 'policybazaar.com',
  'DELHIVERY': 'delhivery.com',
  'SWIGGY': 'swiggy.com',
  'IDEA': 'myvi.in',
  'VODAFONE': 'myvi.in'
};
window.SYMBOL_DOMAINS = SYMBOL_DOMAINS;

// Automated Logo Error Handler: Cascades through high-reliability CDN sources before falling back to initial badge
function handleLogoError(img) {
  if (!img) return;
  const rawSym = img.getAttribute('data-symbol') || '';
  const sym = rawSym.toUpperCase().replace('.NS', '').replace('.BO', '').trim();

  // If numeric (e.g. mutual fund AMFI code) or empty, fall back directly to initial / icon
  if (!sym || /^\d+$/.test(sym)) {
    img.style.display = 'none';
    if (img.nextElementSibling) img.nextElementSibling.style.display = 'flex';
    return;
  }

  const step = parseInt(img.getAttribute('data-logo-step') || '0', 10);
  const cleanTicker = sym.toLowerCase().replace(/[^a-z0-9]/g, '');
  const rawDomain = img.getAttribute('data-website') || (window.SYMBOL_DOMAINS && window.SYMBOL_DOMAINS[sym]) || '';
  const domain = rawDomain.replace(/^https?:\/\//i, '').replace(/\/.*$/, '').replace(/^www\./i, '');

  const sources = [
    // 1. TradingView High-Res Vector SVG (covers hundreds of Indian equities)
    `https://s3-symbol-logo.tradingview.com/${cleanTicker}--big.svg`,
    // 2. Official Corporate Domain via Google Favicon CDN (128px high-res)
    ...(domain ? [`https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.${domain}&size=128`] : []),
    // 3. TradingView Ticker Vector
    `https://s3-symbol-logo.tradingview.com/crypto/XTVC${sym}.svg`,
    // 4. Inferred company domains (.com and .in) via Google Favicon CDN
    `https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.${cleanTicker}.com&size=128`,
    `https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.${cleanTicker}.in&size=128`,
    // 5. DuckDuckGo icon fallback
    `https://icons.duckduckgo.com/ip3/www.${cleanTicker}.com.ico`
  ];

  if (step < sources.length) {
    img.setAttribute('data-logo-step', (step + 1).toString());
    img.src = sources[step];
  } else {
    // All dynamic CDN sources exhausted -> show initial badge
    img.style.display = 'none';
    if (img.nextElementSibling) {
      img.nextElementSibling.style.display = 'flex';
    }
  }
}
window.handleLogoError = handleLogoError;

// --- Card Helpers: Avatars & Star Buttons ---
function getCleanInitial(name, symbol) {
  const str = (name || symbol || 'S').trim();
  // Strip common prefixes like 'The '
  const clean = str.replace(/^The\s+/i, '');
  return clean.charAt(0).toUpperCase();
}

function renderAssetAvatar(item, assetType) {
  const sym = item.symbol || '';
  const isIndex = sym.startsWith('^') || assetType === 'INDEX';
  const isMF = assetType === 'MUTUAL_FUND' || item.asset_type === 'MUTUAL_FUND';
  const cleanSym = sym.replace('.NS', '').replace('.BO', '');
  const initial = isIndex ? 'IDX' : getCleanInitial(item.name, item.symbol);
  const logoUrl = isIndex ? '' : `/static/logos/${cleanSym}.png`;

  const palettes = [
    { bg: 'rgba(14, 165, 233, 0.12)', text: '#38BDF8', border: 'rgba(14, 165, 233, 0.3)' },
    { bg: 'rgba(16, 185, 129, 0.12)', text: '#34D399', border: 'rgba(16, 185, 129, 0.3)' },
    { bg: 'rgba(99, 102, 241, 0.12)', text: '#818CF8', border: 'rgba(99, 102, 241, 0.3)' },
    { bg: 'rgba(236, 72, 153, 0.12)', text: '#F472B6', border: 'rgba(236, 72, 153, 0.3)' },
    { bg: 'rgba(245, 158, 11, 0.12)', text: '#FBBF24', border: 'rgba(245, 158, 11, 0.3)' },
    { bg: 'rgba(168, 85, 247, 0.12)', text: '#C084FC', border: 'rgba(168, 85, 247, 0.3)' },
  ];
  const idx = (initial.charCodeAt(0) || 0) % palettes.length;
  const p = isIndex
    ? { bg: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%)', text: '#38BDF8', border: 'rgba(14, 165, 233, 0.4)' }
    : palettes[idx];

  const fallbackHtml = isIndex
    ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>`
    : (isMF
      ? `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>`
      : initial);

  if (isIndex) {
    return `
      <div class="card-avatar avatar-index" style="background: ${p.bg}; color: ${p.text}; border-color: ${p.border};">
        <span style="display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; font-weight: 800;">
          ${fallbackHtml}
        </span>
      </div>
    `;
  }

  return `
    <div class="card-avatar ${isMF ? 'avatar-mf' : ''}" style="background: ${p.bg}; color: ${p.text}; border-color: ${p.border};">
      <img src="${logoUrl}" 
           alt="${item.name || cleanSym}" 
           loading="lazy"
           data-symbol="${cleanSym}"
           data-website="${item.website || ''}"
           data-logo-step="0"
           onerror="handleLogoError(this)"
           style="width: 26px; height: 26px; object-fit: contain; border-radius: 4px;">
      <span style="display: none; align-items: center; justify-content: center; width: 100%; height: 100%; font-weight: 800;">
        ${fallbackHtml}
      </span>
    </div>
  `;
}

function renderCardStarBtn(symbol, name, assetType) {
  const isStarred = state.watchlist && state.watchlist.has(symbol);
  const activeClass = isStarred ? 'active' : '';
  const escapedName = (name || symbol).replace(/'/g, "\\'");
  return `
    <button class="card-star-btn ${activeClass}" 
            onclick="event.stopPropagation(); toggleWatchlistItem('${symbol}', '${escapedName}', '${assetType}')" 
            title="${isStarred ? 'Remove from Watchlist' : 'Add to Watchlist'}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="${isStarred ? '#FBBF24' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
      </svg>
    </button>
  `;
}

// --- Recently Viewed Assets (Stocks & Mutual Funds) ---
function getRecentlyViewed(type) {
  try {
    const key = type === 'MUTUAL_FUND' ? 'stoxify_recent_mutual_funds' : 'stoxify_recent_stocks';
    const raw = localStorage.getItem(key);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return [];
}

function recordRecentlyViewed(item, type) {
  if (!item || !item.symbol) return;
  const key = type === 'MUTUAL_FUND' ? 'stoxify_recent_mutual_funds' : 'stoxify_recent_stocks';
  try {
    let list = getRecentlyViewed(type);
    const cleanSym = (item.symbol || '').toUpperCase();
    list = list.filter(i => (i.symbol || '').toUpperCase() !== cleanSym);
    list.unshift({
      symbol: item.symbol,
      name: item.name || item.symbol,
      price: item.price || 0,
      change: item.change !== undefined ? item.change : 0,
      change_pct: item.change_pct !== undefined ? item.change_pct : 0,
      return_1y: item.return_1y,
      asset_type: type,
      category: item.category,
      fund_house: item.fund_house,
      sector: item.sector,
      timestamp: Date.now()
    });
    if (list.length > 10) list = list.slice(0, 10);
    localStorage.setItem(key, JSON.stringify(list));
  } catch (e) {}
}

function clearRecentlyViewed(type) {
  const key = type === 'MUTUAL_FUND' ? 'stoxify_recent_mutual_funds' : 'stoxify_recent_stocks';
  try {
    localStorage.removeItem(key);
  } catch (e) {}
  if (type === 'MUTUAL_FUND') {
    renderRecentlyViewedMutualFunds();
  } else {
    renderRecentlyViewedStocks();
  }
}
window.clearRecentlyViewed = clearRecentlyViewed;

function renderRecentlyViewedStocks() {
  const sec = document.getElementById('recentStocksSection');
  const carousel = document.getElementById('recentStocksCarousel');
  if (!sec || !carousel) return;

  const list = getRecentlyViewed('STOCK');
  if (!list || list.length === 0) {
    sec.style.display = 'none';
    carousel.innerHTML = '';
    return;
  }

  sec.style.display = 'block';
  carousel.innerHTML = list.map(s => {
    let live = s;
    if (state.exploreData && state.exploreData.all_stocks) {
      const match = state.exploreData.all_stocks.find(st => (st.symbol || '').toUpperCase() === (s.symbol || '').toUpperCase());
      if (match) live = { ...s, price: match.price, change: match.change, change_pct: match.change_pct };
    }
    const isPos = (live.change || 0) >= 0;
    const cleanSym = (live.symbol || '').replace('.NS', '').replace('.BO', '');
    const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
    return `
      <div class="most-bought-card" onclick="openAssetModal('${live.symbol}', 'STOCK')">
        <div class="mb-top">
          ${renderAssetAvatar(live, 'STOCK')}
          <span class="mb-sym-pill">${cleanSym}</span>
        </div>
        <div class="mb-name" title="${live.name}">${live.name}</div>
        <div class="mb-bottom">
          <span class="mb-price">${formatINR(live.price)}</span>
          <span class="${badgeClass} mb-badge">${isPos ? '+' : ''}${formatNumber(live.change_pct)}%</span>
        </div>
      </div>
    `;
  }).join('');
}

function renderRecentlyViewedMutualFunds() {
  const sec = document.getElementById('recentMfSection');
  const carousel = document.getElementById('recentMfCarousel');
  if (!sec || !carousel) return;

  const list = getRecentlyViewed('MUTUAL_FUND');
  if (!list || list.length === 0) {
    sec.style.display = 'none';
    carousel.innerHTML = '';
    return;
  }

  sec.style.display = 'block';
  carousel.innerHTML = list.map(mf => {
    let live = mf;
    if (state.exploreData && state.exploreData.mutual_funds) {
      const match = state.exploreData.mutual_funds.find(m => (m.symbol || '').toUpperCase() === (mf.symbol || '').toUpperCase());
      if (match) live = { ...mf, price: match.price, return_1y: match.return_1y };
    }
    const cleanSym = (live.symbol || '').replace('.NS', '').replace('.BO', '');
    const returnVal = live.return_1y !== undefined ? live.return_1y : live.change_pct;
    const isPos = (returnVal || 0) >= 0;
    return `
      <div class="most-bought-card" onclick="openAssetModal('${live.symbol}', 'MUTUAL_FUND')">
        <div class="mb-top">
          ${renderAssetAvatar(live, 'MUTUAL_FUND')}
          <span class="mb-sym-pill" style="max-width: 70px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${cleanSym}</span>
        </div>
        <div class="mb-name" title="${live.name}">${live.name}</div>
        <div class="mb-bottom">
          <span class="mb-price">${formatINR(live.price)}</span>
          <span class="${isPos ? 'badge-positive' : 'badge-negative'} mb-badge">${isPos ? '+' : ''}${formatNumber(returnVal)}% 1Y</span>
        </div>
      </div>
    `;
  }).join('');
}

function renderExploreStocks() {
  renderRecentlyViewedStocks();
  if (!state.exploreData || !state.exploreData.all_stocks) return;
  const grid = document.getElementById('stocksGrid');
  const title = document.getElementById('exploreStocksTitle');
  const desc = document.getElementById('exploreStocksDesc');

  // Populate "Most Bought on Stoxify" horizontal carousel with premier Indian stocks
  const mbContainer = document.getElementById('mostBoughtCarousel');
  if (mbContainer && state.exploreData.all_stocks) {
    const popularSymbols = ['RELIANCE.NS', 'TATAMOTORS.NS', 'HDFCBANK.NS', 'INFY.NS', 'TCS.NS', 'ZOMATO.NS', 'HAL.NS', 'SBIN.NS'];
    const popularStocks = state.exploreData.all_stocks.filter(s => popularSymbols.includes(s.symbol));
    const finalPopular = popularStocks.length >= 4 ? popularStocks : state.exploreData.all_stocks.slice(0, 8);
    
    mbContainer.innerHTML = finalPopular.map(s => {
      const isPos = s.change >= 0;
      const cleanSym = (s.symbol || '').replace('.NS', '').replace('.BO', '');
      const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
      return `
        <div class="most-bought-card" onclick="openAssetModal('${s.symbol}', 'STOCK')">
          <div class="mb-top">
            ${renderAssetAvatar(s, 'STOCK')}
            <span class="mb-sym-pill">${cleanSym}</span>
          </div>
          <div class="mb-name" title="${s.name}">${s.name}</div>
          <div class="mb-bottom">
            <span class="mb-price">${formatINR(s.price)}</span>
            <span class="${badgeClass} mb-badge">${isPos ? '+' : ''}${formatNumber(s.change_pct)}%</span>
          </div>
        </div>
      `;
    }).join('');
  }

  let list = [];
  if (state.exploreStockFilter === 'all') {
    list = state.exploreData.all_stocks;
    title.innerText = `Explore Top Stocks (${list.length} available)`;
    if (desc) desc.innerText = 'Live market quotes directly from National Stock Exchange (NSE)';
  } else if (state.exploreStockFilter === 'gainers') {
    list = state.exploreData.gainers;
    title.innerText = `Top Gainers Today (${list.length})`;
    if (desc) desc.innerText = 'Stocks with the highest daily percentage gain on NSE';
  } else if (state.exploreStockFilter === 'losers') {
    list = state.exploreData.losers;
    title.innerText = `Top Losers Today (${list.length})`;
    if (desc) desc.innerText = 'Stocks with the highest daily percentage loss on NSE';
  } else {
    const filterKey = state.exploreStockFilter.toLowerCase();
    list = state.exploreData.all_stocks.filter(s => {
      const sec = (s.sector || '').toLowerCase();
      const sym = (s.symbol || '').toLowerCase();
      const nm = (s.name || '').toLowerCase();
      return sec.includes(filterKey) || sym.includes(filterKey) || nm.includes(filterKey);
    });
    title.innerText = `${state.exploreStockFilter} Equities (${list.length})`;
    if (desc) desc.innerText = `Track top listed companies in the Indian ${state.exploreStockFilter} sector`;
  }

  if (list.length === 0) {
    grid.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem; padding: 3rem; text-align: center;">No stocks found in this category.</div>';
    return;
  }

  grid.innerHTML = list.map(s => {
    const cleanSym = (s.symbol || '').replace('.NS', '').replace('.BO', '');
    const isPos = (s.change || 0) >= 0;
    const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
    return `
      <div class="stock-card" onclick="openAssetModal('${s.symbol}', 'STOCK')">
        <div class="card-top">
          <div class="card-header-left">
            ${renderAssetAvatar(s, 'STOCK')}
            <div class="card-info">
              <div class="card-title" title="${s.name}">${s.name}</div>
              <div class="card-subtitle">${cleanSym} • ${s.sector || 'NSE'}</div>
            </div>
          </div>
          ${renderCardStarBtn(s.symbol, s.name, 'STOCK')}
        </div>
        <div class="card-bottom">
          <div class="card-price">${formatINR(s.price)}</div>
          <div class="${badgeClass}">
            ${formatChange(s.change, s.change_pct)}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderExploreMutualFunds() {
  renderRecentlyViewedMutualFunds();
  if (!state.exploreData || !state.exploreData.mutual_funds) return;
  const grid = document.getElementById('mfGrid');
  grid.innerHTML = state.exploreData.mutual_funds.map(mf => {
    return `
      <div class="stock-card" onclick="openAssetModal('${mf.symbol}', 'MUTUAL_FUND')">
        <div class="card-top">
          <div class="card-header-left">
            ${renderAssetAvatar(mf, 'MUTUAL_FUND')}
            <div class="card-info">
              <div class="card-title" title="${mf.name}">${mf.name}</div>
              <div class="card-subtitle">${mf.category || 'Equity Fund'} • ${mf.fund_house || 'Mutual Fund'}</div>
            </div>
          </div>
          ${renderCardStarBtn(mf.symbol, mf.name, 'MUTUAL_FUND')}
        </div>
        <div class="card-bottom">
          <div class="card-price">${formatINR(mf.price)}</div>
          <div style="text-align: right;">
            <div class="badge-positive" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-green); font-weight: 700; border-radius: 6px; padding: 2px 6px;">
              +${formatNumber(mf.return_1y)}% 1Y
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// --- Holdings View (Delivery CNC) ---
// Navigation, polling, and trade completion can request the same portfolio at
// once. Coalesce those reads to avoid duplicate backend/cloud work.
let portfolioRequest = null;
let portfolioRequestVersion = 0;
function fetchPortfolio(force = false) {
  if (force || !portfolioRequest) {
    const version = ++portfolioRequestVersion;
    const request = fetchPortfolioInternal(version).finally(() => {
      if (portfolioRequest === request) portfolioRequest = null;
    });
    portfolioRequest = request;
  }
  return portfolioRequest;
}

async function fetchPortfolioInternal(requestVersion) {
  const guestBanner = document.getElementById('holdingsGuestBanner');
  const authContent = document.getElementById('holdingsAuthContent');

  if (isGuest()) {
    if (guestBanner) guestBanner.style.display = 'flex';
    if (authContent) authContent.style.display = 'none';
    return;
  }
  if (guestBanner) guestBanner.style.display = 'none';
  if (authContent) authContent.style.display = 'block';

  try {
    const res = await fetch('/api/portfolio');
    const data = await res.json();
    if (requestVersion !== portfolioRequestVersion) return data;
    state.account.balance = data.balance || 0;

    const navBal = document.getElementById('navBalanceDisplay');
    if (navBal) navBal.innerText = formatINR(data.balance);
    const menuBal = document.getElementById('menuUserBalance');
    if (menuBal) menuBal.innerText = formatINR(data.balance);
    const summaryBal = document.getElementById('summaryAvailableBalance');
    if (summaryBal) summaryBal.innerText = formatINR(data.balance);

    const curVal = data.current_value || 0;
    const invVal = data.invested_value ?? data.invested_amount ?? 0;
    const totalPnl = data.total_pnl ?? data.total_returns ?? 0;
    const totalPnlPct = data.total_pnl_pct ?? data.total_returns_pct ?? 0;
    const todayPnl = data.today_pnl ?? data.day_returns ?? 0;
    const todayPnlPct = data.today_pnl_pct ?? data.day_returns_pct ?? 0;

    const summaryCur = document.getElementById('summaryCurrentVal');
    if (summaryCur) summaryCur.innerText = formatINR(curVal);
    const summaryInv = document.getElementById('summaryInvestedVal');
    if (summaryInv) summaryInv.innerText = formatINR(invVal);

    const isTotalPos = totalPnl >= 0;
    const totalReturnsEl = document.getElementById('summaryTotalReturns');
    if (totalReturnsEl) {
      totalReturnsEl.innerText = formatINR(totalPnl);
      totalReturnsEl.className = `banner-metric-val ${isTotalPos ? 'text-positive' : 'text-negative'}`;
    }

    const totalPctEl = document.getElementById('summaryTotalReturnsPct');
    if (totalPctEl) {
      totalPctEl.innerHTML = `<span class="${isTotalPos ? 'text-positive' : 'text-negative'}">${isTotalPos ? '+' : ''}${formatNumber(totalPnlPct)}%</span>`;
    }

    const isDayPos = todayPnl > 0;
    const isDayNeg = todayPnl < 0;
    const daySign = isDayPos ? '+' : '';
    const dayColorClass = isDayPos ? 'text-positive' : (isDayNeg ? 'text-negative' : 'text-muted');
    const dayPnlEl = document.getElementById('summaryTodayPnl');
    if (dayPnlEl) {
      dayPnlEl.innerHTML = `<span class="${dayColorClass}">1D: ${daySign}${formatINR(todayPnl)} (${daySign}${formatNumber(todayPnlPct)}%)</span>`;
    }

    const tableBody = document.getElementById('holdingsTableBody');
    const mobileList = document.getElementById('holdingsMobileList');
    const holdings = data.holdings || [];

    if (holdings.length === 0) {
      if (tableBody) {
        tableBody.innerHTML = `
          <tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3.5rem;">No active holdings yet. Head to Explore to invest!</td></tr>
        `;
      }
      if (mobileList) {
        mobileList.innerHTML = `
          <div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No active holdings yet.</div>
        `;
      }
      return;
    }

    // Render Desktop Table
    if (tableBody) {
      tableBody.innerHTML = (data.holdings || []).map(h => {
        const isPosTotal = h.total_pnl > 0;
        const isNegTotal = h.total_pnl < 0;
        const totalClass = isPosTotal ? 'text-positive' : (isNegTotal ? 'text-negative' : 'text-muted');
        const totalSign = isPosTotal ? '+' : '';

        const isPosDay = h.today_pnl > 0;
        const isNegDay = h.today_pnl < 0;
        const dayClass = isPosDay ? 'text-positive' : (isNegDay ? 'text-negative' : 'text-muted');
        const daySign = isPosDay ? '+' : '';
        return `
          <tr>
            <td>
              <button type="button" class="holding-name-link" onclick="openHoldingDetails('${h.symbol}', '${h.asset_type}')" title="View details for ${h.name}">${h.name}</button>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${h.symbol}</div>
            </td>
            <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem;">${h.asset_type === 'MUTUAL_FUND' ? 'Mutual Fund' : 'Stock'}</span></td>
            <td style="font-weight: 600;">${h.quantity}</td>
            <td>${formatINR(h.avg_price)}</td>
            <td style="font-weight: 700;">${formatINR(h.current_price)}</td>
            <td style="font-weight: 700;">${formatINR(h.current_value)}</td>
            <td class="${totalClass}" style="font-weight: 700;">
              ${totalSign}${formatINR(h.total_pnl)}
              <div style="font-size: 0.75rem; font-weight: 600;">(${totalSign}${formatNumber(h.total_pnl_pct)}%)</div>
            </td>
            <td class="${dayClass}" style="font-weight: 600;">
              ${daySign}${formatINR(h.today_pnl)}
            </td>
            <td style="text-align: right;">
              <button class="btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="startHoldingSale('${h.symbol}', '${h.asset_type}', ${Number(h.quantity) || 0})">Sell</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    // Render Mobile Cards
    if (mobileList) {
      mobileList.innerHTML = (data.holdings || []).map(h => {
      const isPosTotal = h.total_pnl >= 0;
      return `
        <div class="mobile-card-item">
          <div class="mobile-card-top">
            <div>
              <button type="button" class="holding-name-link mobile-holding-title" onclick="openHoldingDetails('${h.symbol}', '${h.asset_type}')" title="View details for ${h.name}">${h.name}</button>
              <div class="mobile-card-symbol">${h.symbol}</div>
            </div>
            <div class="mobile-card-price">
              ${formatINR(h.current_value)}
              <div class="${isPosTotal ? 'text-positive' : 'text-negative'}" style="font-size: 0.78rem; font-weight: 700;">
                ${isPosTotal ? '+' : ''}${formatINR(h.total_pnl)} (${isPosTotal ? '+' : ''}${formatNumber(h.total_pnl_pct)}%)
              </div>
            </div>
          </div>
          <div class="mobile-card-grid">
            <div><span style="color:var(--text-muted);">Shares:</span> <strong>${h.quantity}</strong></div>
            <div><span style="color:var(--text-muted);">Avg Price:</span> <strong>${formatINR(h.avg_price)}</strong></div>
            <div><span style="color:var(--text-muted);">LTP:</span> <strong>${formatINR(h.current_price)}</strong></div>
            <div><span style="color:var(--text-muted);">Product:</span> <strong>Delivery CNC</strong></div>
          </div>
          <div class="mobile-card-actions">
            <button class="pill-btn" onclick="openAssetModal('${h.symbol}', '${h.asset_type}', 'BUY')">+ Add More</button>
            <button class="btn-danger" style="padding: 0.35rem 0.85rem; font-size: 0.8rem;" onclick="startHoldingSale('${h.symbol}', '${h.asset_type}', ${Number(h.quantity) || 0})">Sell</button>
          </div>
        </div>
      `;
    }).join('');
    }

  } catch (err) {
    console.error('Failed to fetch portfolio:', err);
  }
}

// --- Positions View (Intraday MIS with 5x Leverage) ---
let positionsRequest = null;
let positionsRequestVersion = 0;
function fetchPositions(force = false) {
  if (force || !positionsRequest) {
    const version = ++positionsRequestVersion;
    const request = fetchPositionsInternal(version).finally(() => {
      if (positionsRequest === request) positionsRequest = null;
    });
    positionsRequest = request;
  }
  return positionsRequest;
}

async function fetchPositionsInternal(requestVersion) {
  const guestBanner = document.getElementById('positionsGuestBanner');
  const authContent = document.getElementById('positionsAuthContent');

  if (isGuest()) {
    if (guestBanner) guestBanner.style.display = 'flex';
    if (authContent) authContent.style.display = 'none';
    return;
  }
  if (guestBanner) guestBanner.style.display = 'none';
  if (authContent) authContent.style.display = 'block';

  try {
    const res = await fetch('/api/positions');
    const data = await res.json();
    if (requestVersion !== positionsRequestVersion) return data;
    const positions = data.positions || [];

    // Update badges
    const navBadge = document.getElementById('navPositionsBadge');
    const mobBadge = document.getElementById('mobPositionsBadge');
    if (positions.length > 0) {
      if (navBadge) {
        navBadge.innerText = positions.length;
        navBadge.style.display = 'inline-flex';
      }
      if (mobBadge) {
        mobBadge.innerText = positions.length;
        mobBadge.style.display = 'flex';
      }
    } else {
      if (navBadge) navBadge.style.display = 'none';
      if (mobBadge) mobBadge.style.display = 'none';
    }

    // Update summary metrics
    const isPos = (data.total_unrealized_pnl || 0) >= 0;
    const pnlEl = document.getElementById('posTotalPnl');
    if (pnlEl) {
      pnlEl.innerText = `${isPos ? '+' : ''}${formatINR(data.total_unrealized_pnl || 0)}`;
      pnlEl.className = `banner-metric-val ${isPos ? 'text-positive' : 'text-negative'}`;
    }

    const marginEl = document.getElementById('posMarginDeployed');
    if (marginEl) marginEl.innerText = formatINR(data.total_margin_used || 0);
    const countEl = document.getElementById('posActiveCount');
    if (countEl) countEl.innerText = positions.length;

    const sqAllBtn = document.getElementById('squareOffAllBtn');
    if (sqAllBtn) sqAllBtn.style.display = positions.length > 0 ? 'inline-block' : 'none';

    const tableBody = document.getElementById('positionsTableBody');
    const mobileList = document.getElementById('positionsMobileList');

    if (positions.length === 0) {
      if (tableBody) {
        tableBody.innerHTML = `
          <tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 3rem;">No active intraday positions. Intraday trades will appear here with live P&L and 1-click square-off.</td></tr>
        `;
      }
      if (mobileList) {
        mobileList.innerHTML = `
          <div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No active intraday positions.</div>
        `;
      }
      return;
    }

    // Desktop Table
    if (tableBody) {
      tableBody.innerHTML = positions.map(p => {
        const isPosItem = p.unrealized_pnl >= 0;
        return `
          <tr>
            <td>
              <button type="button" class="holding-name-link" onclick="openHoldingDetails('${p.symbol}', '${p.asset_type || 'STOCK'}')" title="View details for ${p.name}">${p.name}</button>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${p.symbol}</div>
            </td>
            <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem; background: var(--brand-cyan-bg); color: var(--brand-cyan); border-color: rgba(255,107,0,0.3);">Intraday 5x</span></td>
            <td style="font-weight: 700;">${p.quantity}</td>
            <td>${formatINR(p.avg_price)}</td>
            <td style="font-weight: 700;">${formatINR(p.current_price)}</td>
            <td>${formatINR(p.margin_used)}</td>
            <td class="${isPosItem ? 'text-positive' : 'text-negative'}" style="font-weight: 700;">
              ${isPosItem ? '+' : ''}${formatINR(p.unrealized_pnl)}
              <div style="font-size: 0.75rem;">(${isPosItem ? '+' : ''}${formatNumber(p.unrealized_pnl_pct)}%)</div>
            </td>
            <td style="text-align: right;">
              <button class="btn-danger" style="padding: 0.35rem 0.85rem; font-size: 0.8rem;" onclick="exitPosition('${p.symbol}')">Exit</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    // Mobile Cards
    if (mobileList) {
      mobileList.innerHTML = positions.map(p => {
        const isPosItem = p.unrealized_pnl >= 0;
        return `
          <div class="mobile-card-item">
            <div class="mobile-card-top">
              <div>
                <button type="button" class="holding-name-link mobile-holding-title" onclick="openHoldingDetails('${p.symbol}', '${p.asset_type || 'STOCK'}')" title="View details for ${p.name}">${p.name}</button>
                <div class="mobile-card-symbol">${p.symbol} <span class="pill-btn" style="padding: 1px 5px; font-size: 0.65rem; background: var(--brand-cyan-bg); color: var(--brand-cyan);">MIS 5x</span></div>
              </div>
              <div class="mobile-card-price">
                <div class="${isPosItem ? 'text-positive' : 'text-negative'}" style="font-size: 1.1rem; font-weight: 800;">
                  ${isPosItem ? '+' : ''}${formatINR(p.unrealized_pnl)}
                </div>
              </div>
            </div>
            <div class="mobile-card-grid">
              <div><span style="color:var(--text-muted);">Shares:</span> <strong>${p.quantity}</strong></div>
              <div><span style="color:var(--text-muted);">Avg Price:</span> <strong>${formatINR(p.avg_price)}</strong></div>
              <div><span style="color:var(--text-muted);">LTP:</span> <strong>${formatINR(p.current_price)}</strong></div>
              <div><span style="color:var(--text-muted);">Margin Used:</span> <strong>${formatINR(p.margin_used)}</strong></div>
            </div>
            <div class="mobile-card-actions">
              <button class="btn-danger" style="padding: 0.35rem 0.85rem; font-size: 0.8rem;" onclick="exitPosition('${p.symbol}')">Square Off Position</button>
            </div>
          </div>
        `;
      }).join('');
    }

  } catch (err) {
    console.error('Failed to fetch positions:', err);
  }
}

async function exitPosition(symbol) {
  if (!confirm(`Are you sure you want to square off your intraday position for ${symbol} at market price?`)) return;
  try {
    const res = await fetch('/api/position/exit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol })
    });
    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'Failed to exit position', true);
      return;
    }
    showToast(`Position squared off: ${symbol} at current market price`);
    fetchPositions(true);
    fetchAccount();
    fetchOrders();
  } catch (err) {
    showToast('Failed to connect to execution server', true);
  }
}

async function squareOffAllPositions() {
  if (!confirm('Are you sure you want to SQUARE OFF ALL open intraday positions?')) return;
  try {
    const res = await fetch('/api/position/exit-all', { method: 'POST' });
    const result = await res.json();
    showToast(`Squared off ${result.exited_count} open intraday positions!`);
    fetchPositions(true);
    fetchAccount();
    fetchOrders();
  } catch (err) {
    showToast('Failed to square off positions', true);
  }
}

// --- Orders View (Executed & Open Orders) ---
async function fetchOrders() {
  try {
    const [execRes, openRes, slRes] = await Promise.all([
      fetch('/api/orders?status=EXECUTED').catch(() => null),
      fetch('/api/orders?status=OPEN').catch(() => null),
      fetch('/api/orders?status=TRIGGER_PENDING').catch(() => null)
    ]);
    const execJson = execRes && execRes.ok ? await execRes.json().catch(() => []) : [];
    const openJson = openRes && openRes.ok ? await openRes.json().catch(() => []) : [];
    const slJson = slRes && slRes.ok ? await slRes.json().catch(() => []) : [];

    const executedOrders = Array.isArray(execJson) ? execJson : [];
    // Pending stop-loss (TRIGGER_PENDING) orders are open orders too: they can
    // still be cancelled and must not appear in the executed history.
    const openOrders = [...(Array.isArray(openJson) ? openJson : []), ...(Array.isArray(slJson) ? slJson : [])]
      .sort((a, b) => (b.id || 0) - (a.id || 0));

    // Update Open Orders count badges
    const openOrdersCount = document.getElementById('openOrdersCount');
    if (openOrdersCount) openOrdersCount.innerText = openOrders.length;
    const navOrdersBadge = document.getElementById('navOrdersBadge');
    const mobOpenOrdersBadge = document.getElementById('mobOpenOrdersBadge');
    const mobOrdersBadge = document.getElementById('mobOrdersBadge');

    if (openOrders.length > 0) {
      if (navOrdersBadge) {
        navOrdersBadge.innerText = openOrders.length;
        navOrdersBadge.style.display = 'inline-flex';
      }
      if (mobOpenOrdersBadge) {
        mobOpenOrdersBadge.innerText = openOrders.length;
        mobOpenOrdersBadge.style.display = 'flex';
      }
      if (mobOrdersBadge) {
        mobOrdersBadge.innerText = openOrders.length;
        mobOrdersBadge.style.display = 'inline-flex';
      }
    } else {
      if (navOrdersBadge) navOrdersBadge.style.display = 'none';
      if (mobOpenOrdersBadge) mobOpenOrdersBadge.style.display = 'none';
      if (mobOrdersBadge) mobOrdersBadge.style.display = 'none';
    }

    // 1. Render Executed Orders Table & Mobile Cards
    const execTableBody = document.getElementById('ordersTableBody');
    const execMobileList = document.getElementById('ordersMobileList');

    if (execTableBody || execMobileList) {
      if (executedOrders.length === 0) {
        if (execTableBody) execTableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 3rem;">No orders placed yet.</td></tr>`;
        if (execMobileList) execMobileList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No orders placed yet.</div>`;
      } else {
        const rowsHtml = executedOrders.map(o => {
          const isBuy = o.order_type === 'BUY';
          const isPnlPos = o.realized_pnl >= 0;
          return `
            <tr>
              <td style="font-size: 0.8rem; color: var(--text-muted);">${o.timestamp || 'Today'}</td>
              <td>
                <button type="button" class="holding-name-link" onclick="openHoldingDetails('${o.symbol}', '${o.asset_type || 'STOCK'}')" title="View details for ${o.name}">${o.name}</button>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${o.symbol}</div>
              </td>
              <td><span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type}</span></td>
              <td><span class="pill-btn" style="padding: 0.15rem 0.45rem; font-size: 0.7rem;">${o.product_type}</span></td>
              <td><span style="font-size: 0.75rem; color: var(--text-muted);">${o.order_variety || 'MARKET'}</span></td>
              <td style="font-weight: 600;">${o.quantity}</td>
              <td>${formatINR(o.price)}</td>
              <td style="font-weight: 700;">
                ${formatINR(o.total_amount)}
                ${o.charges > 0 ? `<div style="font-size: 0.7rem; color: var(--text-muted); font-weight: normal;">Fee: ₹${Number(o.charges).toFixed(2)}</div>` : ''}
              </td>
              <td class="${isPnlPos ? 'text-positive' : 'text-negative'}" style="font-weight: 700;">
                ${o.realized_pnl ? (isPnlPos ? '+' : '') + formatINR(o.realized_pnl) : '—'}
              </td>
              <td><span class="pill-btn" style="padding: 0.15rem 0.45rem; font-size: 0.7rem; color: ${o.status.includes('CANCELLED') ? 'var(--danger-red)' : 'var(--accent-green)'};">${o.status}</span></td>
            </tr>
          `;
        }).join('');
        if (execTableBody) execTableBody.innerHTML = rowsHtml;

        if (execMobileList) {
          execMobileList.innerHTML = executedOrders.map(o => {
            const isBuy = o.order_type === 'BUY';
            return `
              <div class="mobile-card-item">
                <div class="mobile-card-top">
                  <div>
                    <button type="button" class="holding-name-link mobile-holding-title" onclick="openHoldingDetails('${o.symbol}', '${o.asset_type || 'STOCK'}')" title="View details for ${o.name}">${o.name}</button>
                    <div class="mobile-card-symbol">${o.symbol} <span class="badge-${isBuy ? 'positive' : 'negative'}" style="font-size: 0.7rem;">${o.order_type}</span> • ${o.product_type}</div>
                  </div>
                  <div class="mobile-card-price">
                    ${formatINR(o.total_amount)}
                    ${o.charges > 0 ? `<div style="font-size: 0.7rem; color: var(--text-muted);">Fee: ₹${Number(o.charges).toFixed(2)}</div>` : ''}
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${o.status}</div>
                  </div>
                </div>
                <div class="mobile-card-grid">
                  <div><span style="color:var(--text-muted);">Qty:</span> <strong>${o.quantity}</strong></div>
                  <div><span style="color:var(--text-muted);">Exec Price:</span> <strong>${formatINR(o.price)}</strong></div>
                  <div><span style="color:var(--text-muted);">Variety:</span> <strong>${o.order_variety || 'MARKET'}</strong></div>
                  <div><span style="color:var(--text-muted);">Time:</span> <strong>${(o.timestamp || 'Today').split(' ')[1] || 'Today'}</strong></div>
                </div>
              </div>
            `;
          }).join('');
        }
      }
    }

    // 2. Render Open Orders Table & Mobile Cards
    const openTableBody = document.getElementById('openOrdersTableBody');
    const openMobileList = document.getElementById('openOrdersMobileList');

    if (openTableBody || openMobileList) {
      if (openOrders.length === 0) {
        if (openTableBody) openTableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 3rem;">No pending orders.</td></tr>`;
        if (openMobileList) openMobileList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No pending orders.</div>`;
      } else {
        if (openTableBody) {
          openTableBody.innerHTML = openOrders.map(o => {
            const isBuy = o.order_type === 'BUY';
            const displayPrice = o.order_variety === 'STOP_LOSS'
              ? (o.trigger_price ? `Trig: ${formatINR(o.trigger_price)}` : formatINR(o.price))
              : formatINR(o.limit_price || o.price);
            return `
              <tr>
                <td>#${o.id}</td>
                <td>
                  <button type="button" class="holding-name-link" onclick="openHoldingDetails('${o.symbol}', '${o.asset_type || 'STOCK'}')" title="View details for ${o.name}">${o.name}</button>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${o.symbol}</div>
                </td>
                <td><span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type}</span></td>
                <td>${o.product_type}</td>
                <td style="font-weight: 600;">${o.quantity}</td>
                <td style="font-weight: 700; color: var(--brand-cyan);">${displayPrice}</td>
                <td>${formatINR(o.total_amount)}</td>
                <td style="font-size: 0.75rem; color: var(--text-muted);">${o.timestamp || 'Today'}</td>
                <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem; color: var(--brand-cyan);">${o.status}</span></td>
                <td style="text-align: right;">
                  <button class="btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="cancelOrder(${o.id})">Cancel</button>
                </td>
              </tr>
            `;
          }).join('');
        }

        if (openMobileList) {
          openMobileList.innerHTML = openOrders.map(o => {
            const isBuy = o.order_type === 'BUY';
            const displayPrice = o.order_variety === 'STOP_LOSS'
              ? (o.trigger_price ? `Trig: ${formatINR(o.trigger_price)}` : formatINR(o.price))
              : formatINR(o.limit_price || o.price);
            return `
              <div class="mobile-card-item" style="border-left: 4px solid var(--brand-cyan);">
                <div class="mobile-card-top">
                  <div>
                    <button type="button" class="holding-name-link mobile-holding-title" onclick="openHoldingDetails('${o.symbol}', '${o.asset_type || 'STOCK'}')" title="View details for ${o.name}">${o.name || o.symbol}</button>
                    <div class="mobile-card-symbol">${o.symbol} <span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type} ${o.order_variety || 'LIMIT'}</span> • Order #${o.id} • ${o.product_type}</div>
                  </div>
                  <div class="mobile-card-price">
                    <span style="color: var(--brand-cyan);">${displayPrice}</span>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${o.status === 'TRIGGER_PENDING' ? 'Trigger Pending' : 'Pending Execution'}</div>
                  </div>
                </div>
                <div class="mobile-card-grid">
                  <div><span style="color:var(--text-muted);">Qty:</span> <strong>${o.quantity}</strong></div>
                  <div><span style="color:var(--text-muted);">Blocked:</span> <strong>${formatINR(o.total_amount)}</strong></div>
                </div>
                <div class="mobile-card-actions">
                  <button class="btn-danger" style="width: 100%; justify-content: center; padding: 0.45rem;" onclick="cancelOrder(${o.id})">Cancel Order</button>
                </div>
              </div>
            `;
          }).join('');
        }
      }
    }

  } catch (err) {
    console.error('Failed to fetch orders:', err);
  }
}

async function cancelOrder(orderId) {
  try {
    const res = await fetch('/api/order/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId })
    });
    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'Failed to cancel order', true);
      return;
    }
    showToast(`Order #${orderId} cancelled and blocked funds returned!`);
    await fetchOrders();
    await fetchAccount();
    await fetchPortfolio(true);
    await fetchPositions(true);
    if (currentPageAsset && currentPageAsset.symbol) {
      updatePageAvailableHolding(currentPageAsset.symbol);
      recalcPageMargin();
    }
  } catch (err) {
    showToast('Failed to cancel order', true);
  }
}

// --- Watchlist View ---
async function fetchWatchlist() {
  try {
    const res = await fetch('/api/watchlist');
    const items = await res.json();
    if (Array.isArray(items)) {
      items.forEach(i => state.watchlist.add(i.symbol));
      saveLocalWatchlistSet(state.watchlist);
    }

    const grid = document.getElementById('watchlistGrid');
    if (!items || items.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 3rem;">Your watchlist is empty. Tap ★ on any stock or mutual fund to track it here!</div>`;
      return;
    }

    grid.innerHTML = items.map(item => {
      const isPos = item.change >= 0;
      const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
      const isMF = item.asset_type === 'MUTUAL_FUND';
      const subtitle = isMF ? 'Mutual Fund • Direct Plan' : `${item.symbol} • Stock`;
      const priceLabel = isMF ? 'NAV' : 'Market Price';

      return `
        <div class="stock-card" onclick="openAssetModal('${item.symbol}', '${item.asset_type}')">
          <div class="card-top">
            <div class="card-header-left">
              ${renderAssetAvatar(item, item.asset_type)}
              <div class="card-info">
                <div class="card-title" title="${item.name}">${item.name}</div>
                <div class="card-subtitle">${subtitle}</div>
              </div>
            </div>
            ${renderCardStarBtn(item.symbol, item.name, item.asset_type)}
          </div>
          <div class="card-bottom">
            <div class="card-price">${formatINR(item.price)}</div>
            <div class="${badgeClass}">
              ${formatChange(item.change, item.change_pct)}
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to fetch watchlist:', err);
  }
}

async function toggleWatchlistItem(symbol, name, assetType) {
  if (!state.watchlist) state.watchlist = getLocalWatchlistSet();
  const willRemove = state.watchlist.has(symbol);
  if (willRemove) {
    state.watchlist.delete(symbol);
    saveLocalWatchlistSet(state.watchlist);
    updatePageAssetStar(symbol);
    showToast(`Removed ${symbol} from watchlist`);
    try {
      await fetch(`/api/watchlist/${encodeURIComponent(symbol)}`, { method: 'DELETE' });
    } catch (e) {}
  } else {
    state.watchlist.add(symbol);
    saveLocalWatchlistSet(state.watchlist);
    updatePageAssetStar(symbol);
    showToast(`Added ${symbol} to watchlist`);
    try {
      await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, name: name || symbol, asset_type: assetType || 'STOCK' })
      });
    } catch (e) {}
  }
  updatePageAssetStar(symbol);
  if (state.currentTab === 'watchlist') {
    fetchWatchlist();
  } else if (state.currentTab === 'explore') {
    renderExploreStocks();
    renderExploreMutualFunds();
  }
  if (state.currentModalAsset && state.currentModalAsset.symbol === symbol) renderModalWatchlistBtn(symbol, name, assetType);
}
window.toggleWatchlist = toggleWatchlistItem;

// --- Search Auto-Complete & Dismiss Handling ---
const searchInput = document.getElementById('globalSearchInput');
const searchDropdown = document.getElementById('searchResultsDropdown');
let searchDebounceTimer = null;

function closeSearchBar(e) {
  if (e) {
    e.stopPropagation();
    e.preventDefault();
  }
  const input = document.getElementById('globalSearchInput');
  const dropdown = document.getElementById('searchResultsDropdown');
  const wrapper = document.querySelector('.search-wrapper');
  if (input) {
    input.value = '';
    const box = input.closest('.search-input-box');
    if (box) box.classList.remove('has-text');
    input.blur();
  }
  if (dropdown) {
    dropdown.style.display = 'none';
  }
  if (wrapper && wrapper.classList.contains('mobile-open')) {
    wrapper.classList.remove('mobile-open');
  }
}
window.closeSearchBar = closeSearchBar;

if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    const box = searchInput.closest('.search-input-box');
    if (box) {
      if (query.length > 0) {
        box.classList.add('has-text');
      } else {
        box.classList.remove('has-text');
      }
    }
    clearTimeout(searchDebounceTimer);
    if (!query) {
      searchDropdown.style.display = 'none';
      return;
    }
    searchDebounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const results = await res.json();
        if (results.length === 0) {
          searchDropdown.innerHTML = `<div style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">No securities found matching "${query}"</div>`;
        } else {
          searchDropdown.innerHTML = results.map(r => `
            <div class="search-item" onclick="selectSearchResult('${r.symbol}', '${r.asset_type}')">
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                ${renderAssetAvatar(r, r.asset_type)}
                <div>
                  <div class="search-item-title" style="font-weight: 700; font-size: 0.9rem;">${r.name}</div>
                  <div class="search-item-sub" style="font-size: 0.75rem; color: var(--text-muted);">${r.subtext}</div>
                </div>
              </div>
              <span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem;">
                ${r.asset_type === 'MUTUAL_FUND' ? 'Mutual Fund' : 'Stock'}
              </span>
            </div>
          `).join('');
        }
        searchDropdown.style.display = 'block';
      } catch (err) {
        console.error('Search error:', err);
      }
    }, 180);
  });
}

function handleOutsideSearch(e) {
  const input = document.getElementById('globalSearchInput');
  const dropdown = document.getElementById('searchResultsDropdown');
  const wrapper = document.querySelector('.search-wrapper');
  const mobileBtn = document.getElementById('mobileSearchBtn');

  // Close dropdown if clicked outside input and dropdown
  if (dropdown && dropdown.style.display !== 'none' && input) {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  }

  // Mobile View Only: Dismiss mobile search bar when touching/clicking elsewhere on screen
  if (wrapper && wrapper.classList.contains('mobile-open')) {
    if (!wrapper.contains(e.target) && (!mobileBtn || !mobileBtn.contains(e.target))) {
      wrapper.classList.remove('mobile-open');
      if (dropdown) dropdown.style.display = 'none';
      if (input) {
        input.blur();
      }
    }
  }
}

document.addEventListener('pointerdown', handleOutsideSearch);
document.addEventListener('touchstart', handleOutsideSearch, { passive: true });
document.addEventListener('click', handleOutsideSearch);

function selectSearchResult(symbol, assetType) {
  searchDropdown.style.display = 'none';
  if (searchInput) {
    searchInput.value = '';
    const box = searchInput.closest('.search-input-box');
    if (box) box.classList.remove('has-text');
  }
  const wrapper = document.querySelector('.search-wrapper');
  if (wrapper && wrapper.classList.contains('mobile-open')) {
    wrapper.classList.remove('mobile-open');
  }
  openAssetModal(symbol, assetType);
}

// --- Asset Detail & Trade Modal ---
function openAssetModal(symbol, assetType = 'STOCK', preselectAction = 'BUY') {
  const cleanSym = (symbol || '').replace('.NS', '').replace('.BO', '');
  if (preselectAction && preselectAction !== 'BUY') {
    sessionStorage.setItem('stoxify_preselect_action', preselectAction);
  } else {
    sessionStorage.removeItem('stoxify_preselect_action');
    sessionStorage.removeItem('stoxify_holding_sale');
  }
  if (assetType === 'MUTUAL_FUND' || symbol.match(/^\d+$/)) {
    navigateTo('/mf/' + cleanSym);
  } else {
    navigateTo('/stock/' + cleanSym);
  }
}

// Holdings have a known product and quantity. Carry those values through the
// route change instead of waiting for a second portfolio request before Sell.
function openHoldingDetails(symbol, assetType = 'STOCK') {
  openAssetModal(symbol, assetType, 'BUY');
}

function startHoldingSale(symbol, assetType = 'STOCK', quantity = 0) {
  const cleanQuantity = Number(quantity);
  if (!Number.isFinite(cleanQuantity) || cleanQuantity <= 0) {
    showToast('This holding has no sellable shares.', true);
    return;
  }
  sessionStorage.setItem('stoxify_holding_sale', JSON.stringify({
    symbol: (symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase(),
    assetType,
    quantity: cleanQuantity,
    product: 'DELIVERY'
  }));
  openAssetModal(symbol, assetType, 'SELL');
}

async function legacyOpenAssetModal(symbol, assetType = 'STOCK', preselectAction = 'BUY') {
  document.getElementById('tradeModalOverlay').classList.add('active');
  setOrderAction(preselectAction);
  setProductType('DELIVERY');
  setOrderVariety('MARKET');
  document.getElementById('tradeQuantityInput').value = 1;

  try {
    const res = await fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}&asset_type=${encodeURIComponent(assetType)}`);
    const data = await res.json();
    state.currentModalAsset = data;

    const isIndex = (data.symbol || '').startsWith('^') || assetType === 'INDEX';
    const indexName = isIndex ? (INDEX_NAMES[data.symbol] || data.name || data.symbol.replace('^', '')) : null;
    const cleanSym = isIndex ? (INDEX_NAMES[data.symbol] || data.symbol.replace('^', '')) : (data.symbol || '').replace('.NS', '').replace('.BO', '');
    const isMF = data.asset_type === 'MUTUAL_FUND';
    const initial = isIndex ? 'IDX' : getCleanInitial(data.name, data.symbol);
    const logoUrl = isIndex ? '' : `/static/logos/${cleanSym}.png`;
    const fallbackHtml = isIndex
      ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>`
      : (isMF
        ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>`
        : initial);

    const modalAvatarEl = document.getElementById('modalAvatar');
    modalAvatarEl.innerHTML = `
      <img src="${logoUrl}" 
           alt="${data.name || cleanSym}" 
           loading="lazy"
           data-symbol="${cleanSym}"
           data-website="${data.website || ''}"
           data-logo-step="0"
           onerror="handleLogoError(this)"
           style="width: 28px; height: 28px; object-fit: contain; border-radius: 4px;">
      <span style="display: ${isIndex ? 'flex' : 'none'}; align-items: center; justify-content: center; width: 100%; height: 100%; font-weight: 800;">
        ${fallbackHtml}
      </span>
    `;
    document.getElementById('modalTitle').innerText = isIndex ? indexName : data.name;
    document.getElementById('modalSymbol').innerText = isIndex ? cleanSym : data.symbol;
    document.getElementById('modalBadge').innerText = isIndex ? 'INDEX' : (data.asset_type === 'MUTUAL_FUND' ? 'MUTUAL FUND' : 'NSE');

    document.getElementById('modalPrice').innerText = formatINR(data.price);
    document.getElementById('tradePriceInput').value = data.price;
    document.getElementById('tradeLimitPriceInput').value = data.price;

    const isPos = data.change >= 0;
    const badge = document.getElementById('modalChangeBadge');
    badge.className = isPos ? 'badge-positive' : 'badge-negative';
    badge.innerText = formatChange(data.change, data.change_pct);

    // Fundamentals
    const fundContainer = document.getElementById('modalFundamentals');
    if (data.asset_type === 'STOCK') {
      fundContainer.innerHTML = `
        <div><span style="color: var(--text-muted);">Market Cap:</span> <strong>${data.market_cap ? '₹' + (data.market_cap / 1e7).toFixed(1) + ' Cr' : '—'}</strong></div>
        <div><span style="color: var(--text-muted);">P/E Ratio:</span> <strong>${data.pe_ratio || '—'}</strong></div>
        <div><span style="color: var(--text-muted);">52W High:</span> <strong>${formatINR(data.fifty_two_week_high)}</strong></div>
        <div><span style="color: var(--text-muted);">52W Low:</span> <strong>${formatINR(data.fifty_two_week_low)}</strong></div>
      `;
      document.getElementById('modalDepthSection').style.display = 'block';
      fetchMarketDepth(symbol);
    } else {
      fundContainer.innerHTML = `
        <div><span style="color: var(--text-muted);">Category:</span> <strong>${data.category || 'Equity'}</strong></div>
        <div><span style="color: var(--text-muted);">Fund House:</span> <strong>${data.fund_house || 'AMC'}</strong></div>
        <div><span style="color: var(--text-muted);">1Y Returns:</span> <strong>+${formatNumber(data.return_1y)}%</strong></div>
        <div><span style="color: var(--text-muted);">NAV Date:</span> <strong>${data.nav_date || 'Today'}</strong></div>
      `;
      document.getElementById('modalDepthSection').style.display = 'none';
    }

    renderModalWatchlistBtn(data.symbol, data.name, data.asset_type);
    calculateOrderMargin();
    loadChartTimeframe('1D');
  } catch (err) {
    console.error('Failed to load asset details:', err);
    showToast('Failed to load instrument details', true);
  }
}

// --- Level-2 Market Depth ---
async function fetchMarketDepth(symbol) {
  try {
    const res = await fetch(`/api/depth?symbol=${encodeURIComponent(symbol)}`);
    const data = await res.json();
    renderMarketDepth(data);
  } catch (err) {
    console.error('Failed to fetch market depth:', err);
  }
}

function renderMarketDepth(depth) {
  const bidsContainer = document.getElementById('depthBidsList');
  const asksContainer = document.getElementById('depthAsksList');

  bidsContainer.innerHTML = depth.bids.map(b => `
    <div class="depth-row bid">
      <span>${b.orders}</span>
      <span>${b.quantity}</span>
      <span class="price">${formatNumber(b.price)}</span>
    </div>
  `).join('');

  asksContainer.innerHTML = depth.asks.map(a => `
    <div class="depth-row ask">
      <span class="price">${formatNumber(a.price)}</span>
      <span>${a.quantity}</span>
      <span>${a.orders}</span>
    </div>
  `).join('');

  document.getElementById('depthBuyPct').innerText = `Buy: ${depth.buy_pct}%`;
  document.getElementById('depthSellPct').innerText = `Sell: ${depth.sell_pct}%`;
  document.getElementById('depthBuyProgress').style.width = `${depth.buy_pct}%`;
  document.getElementById('depthSellProgress').style.width = `${depth.sell_pct}%`;
}

function renderModalWatchlistBtn(symbol, name, assetType) {
  const container = document.getElementById('modalWatchlistBtnContainer');
  const isWatched = state.watchlist.has(symbol);
  container.innerHTML = `
    <button class="pill-btn ${isWatched ? 'active' : ''}" onclick="toggleWatchlistItem('${symbol}', '${name.replace(/'/g, "\\'")}', '${assetType}')">
      ${isWatched ? '★ Watched' : '+ Watchlist'}
    </button>
  `;
}

function closeTradeModal() {
  document.getElementById('tradeModalOverlay').classList.remove('active');
  if (state.chartInstance) {
    state.chartInstance.destroy();
    state.chartInstance = null;
  }
}

async function loadChartTimeframe(tf) {
  state.currentModalTimeframe = tf;
  document.querySelectorAll('.timeframe-group .tf-btn').forEach(b => {
    if (b.innerText.trim() === tf) b.classList.add('active');
    else b.classList.remove('active');
  });

  if (!state.currentModalAsset) return;
  const symbol = state.currentModalAsset.symbol;
  const assetType = state.currentModalAsset.asset_type;

  try {
    const res = await fetch(`/api/history?symbol=${encodeURIComponent(symbol)}&asset_type=${encodeURIComponent(assetType)}&timeframe=${tf}`);
    const points = await res.json();
    renderChart(points);

    const badge = document.getElementById('modalChangeBadge');
    if (badge && state.currentModalAsset) {
      if (tf === '1D' || !points || points.length === 0) {
        const isPos = (state.currentModalAsset.change || 0) >= 0;
        badge.className = isPos ? 'badge-positive' : 'badge-negative';
        badge.innerText = formatChange(state.currentModalAsset.change || 0, state.currentModalAsset.change_pct || 0);
      } else {
        const firstP = points[0];
        const firstVal = (firstP.open !== undefined ? firstP.open : (firstP.close !== undefined ? firstP.close : (firstP.value || firstP.price))) || (state.currentModalAsset.price - (state.currentModalAsset.change || 0));
        const diff = state.currentModalAsset.price - firstVal;
        const diffPct = firstVal ? (diff / firstVal) * 100 : 0;
        const isPos = diff >= 0;
        badge.className = isPos ? 'badge-positive' : 'badge-negative';
        badge.innerText = formatChange(diff, diffPct);
      }
    }
  } catch (err) {
    console.error('Failed to load chart data:', err);
  }
}

// --- Groww-Grade Aesthetic Financial Chart Plugin ---
// Provides subtle dashed baseline (previous close), interactive vertical guide,
// radiant hover pulse dot, and clean X-axis time pill without intrusive tooltips covering the curve.
const growwChartPlugin = {
  id: 'growwChartPlugin',
  afterDraw: (chart) => {
    const { ctx, chartArea, scales: { x: xScale, y: yScale } } = chart;
    if (!chartArea || !xScale || !yScale) return;

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const isMobile = window.innerWidth <= 768;

    // 1. Draw Previous Close Horizontal Baseline (for 1D session baseline)
    const baseline = chart.options.plugins?.growwOptions?.baseline;
    if (baseline && baseline >= yScale.min && baseline <= yScale.max) {
      const yBaseline = yScale.getPixelForValue(baseline);
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = isDark ? 'rgba(148, 163, 184, 0.28)' : 'rgba(100, 116, 139, 0.28)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(chartArea.left, yBaseline);
      ctx.lineTo(chartArea.right, yBaseline);
      ctx.stroke();

      // Right axis baseline indicator label (desktop only)
      if (!isMobile && chartArea.right - chartArea.left > 220) {
        ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
        ctx.font = '500 9.5px Sora, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`Prev. Close: ${formatINR(baseline)}`, chartArea.right - 8, yBaseline - 5);
      }
      ctx.restore();
    }

    // 2. Draw Interactive Vertical Crosshair Guide, Radar Pulse Glow Dot, & Time Pill
    const activeElements = (chart.getActiveElements && chart.getActiveElements().length > 0)
      ? chart.getActiveElements()
      : (chart.tooltip?._active || []);

    if (activeElements && activeElements.length > 0) {
      const activePoint = activeElements[0];
      const x = activePoint.element.x;
      const y = activePoint.element.y;
      const dataset = chart.data.datasets[activePoint.datasetIndex || 0];
      const strokeColor = dataset?.borderColor || '#00D09C';
      const isPos = strokeColor === '#00D09C';

      ctx.save();
      // Thin vertical dashed guide line from top to bottom of chart area
      ctx.setLineDash([3, 3]);
      ctx.strokeStyle = isDark ? 'rgba(148, 163, 184, 0.35)' : 'rgba(100, 116, 139, 0.35)';
      ctx.lineWidth = isMobile ? 0.8 : 1.0;
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.stroke();
      ctx.setLineDash([]);

      const auraRadius = isMobile ? 6.5 : 9.0;
      const dotRadius = isMobile ? 3.5 : 5.0;
      const ringWidth = isMobile ? 1.8 : 2.5;

      // Outer Glowing Aura Ring
      ctx.beginPath();
      ctx.arc(x, y, auraRadius, 0, 2 * Math.PI);
      ctx.fillStyle = isPos ? 'rgba(0, 208, 156, 0.22)' : 'rgba(235, 91, 60, 0.22)';
      ctx.fill();

      // Solid Trend Color Circle
      ctx.beginPath();
      ctx.arc(x, y, dotRadius, 0, 2 * Math.PI);
      ctx.fillStyle = strokeColor;
      ctx.fill();

      // Crisp Ring
      ctx.lineWidth = ringWidth;
      ctx.strokeStyle = isDark ? '#0F172A' : '#FFFFFF';
      ctx.stroke();

      // Inner Center Core
      ctx.beginPath();
      ctx.arc(x, y, isMobile ? 1.4 : 1.8, 0, 2 * Math.PI);
      ctx.fillStyle = isDark ? '#0F172A' : '#FFFFFF';
      ctx.fill();

      // Floating Sleek Top Badge showing the price & time of the touched point
      // Pinned steadily along the top edge (chartArea.top + 6) and centered over the cursor/scrub line x.
      // This prevents vertical jitter and jumping.
      const val = dataset?.data?.[activePoint.index];
      const label = chart.data.labels?.[activePoint.index];
      if (val !== undefined) {
        const priceStr = formatINR(val);
        const text = label ? `${priceStr}  •  ${label}` : priceStr;
        ctx.font = isMobile ? '600 9.5px Sora, sans-serif' : '600 10.5px Sora, sans-serif';
        const textWidth = ctx.measureText(text).width;
        const pillW = textWidth + (isMobile ? 14 : 18);
        const pillH = isMobile ? 20 : 22;
        const pillX = Math.max(chartArea.left + 4, Math.min(chartArea.right - pillW - 4, x - pillW / 2));
        const pillY = chartArea.top + 6;

        ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.96)';
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(pillX, pillY, pillW, pillH, 5);
        } else {
          ctx.rect(pillX, pillY, pillW, pillH);
        }
        ctx.fill();

        ctx.strokeStyle = isDark ? '#334155' : '#CBD5E1';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = isDark ? '#F8FAFC' : '#0F172A';
        ctx.textAlign = 'center';
        ctx.fillText(text, pillX + pillW / 2, pillY + (isMobile ? 14 : 15));
      }

      ctx.restore();
    }
  }
};
window.growwChartPlugin = growwChartPlugin;

function renderChart(points) {
  const canvas = document.getElementById('tradeChartCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (state.chartInstance) state.chartInstance.destroy();

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const isMobile = window.innerWidth <= 768;
  const labels = points.map(p => p.time);
  const values = points.map(p => (p.value !== undefined ? p.value : p.price) || 0);
  const firstVal = values[0] || 0;
  const lastVal = values[values.length - 1] || 0;
  
  const isPos = lastVal >= firstVal;
  const strokeColor = isPos ? '#00D09C' : '#EB5B3C';
  
  const chartHeight = canvas.clientHeight || 220;
  const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
  gradient.addColorStop(0, isPos ? 'rgba(0, 208, 156, 0.20)' : 'rgba(235, 91, 60, 0.20)');
  gradient.addColorStop(0.5, isPos ? 'rgba(0, 208, 156, 0.05)' : 'rgba(235, 91, 60, 0.05)');
  gradient.addColorStop(1, isPos ? 'rgba(0, 208, 156, 0.0)' : 'rgba(235, 91, 60, 0.0)');

  const baseline = state.currentModalAsset ? (state.currentModalAsset.price - (state.currentModalAsset.change || 0)) : null;

  state.chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        borderColor: strokeColor,
        borderWidth: isMobile ? 1.5 : 2.0,
        backgroundColor: gradient,
        fill: true,
        tension: 0.32,
        borderCapStyle: 'round',
        borderJoinStyle: 'round',
        pointRadius: 0,
        pointHoverRadius: isMobile ? 3.5 : 5.0,
        pointHoverBackgroundColor: strokeColor,
        pointHoverBorderColor: isDark ? '#0F172A' : '#fff',
        pointHoverBorderWidth: isMobile ? 1.8 : 2.5
      }]
    },
    plugins: [growwChartPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: isMobile ? 2 : 0,
          right: isMobile ? 2 : 0,
          top: 8,
          bottom: isMobile ? 4 : 0
        }
      },
      interaction: { intersect: false, mode: 'index', axis: 'x' },
      plugins: {
        legend: { display: false },
        growwOptions: { baseline: baseline },
        tooltip: {
          enabled: true,
          backgroundColor: isDark ? '#1C2230' : '#FFFFFF',
          titleColor: isDark ? '#94A3B8' : '#64748B',
          bodyColor: strokeColor,
          borderColor: isDark ? '#2B3548' : '#E2E8F0',
          borderWidth: 1,
          padding: 8,
          cornerRadius: 6,
          displayColors: false,
          callbacks: { label: (ctx) => `Price: ${formatINR(ctx.parsed.y)}` }
        }
      },
      scales: {
        x: { display: false, border: { display: false } },
        y: {
          position: 'right',
          grace: '8%',
          border: { display: false },
          grid: { 
            drawTicks: false,
            color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)' 
          },
          ticks: { 
            display: !isMobile,
            color: isDark ? '#64748B' : '#94A3B8', 
            font: { size: 10, family: 'Sora, sans-serif' }, 
            callback: (val) => `₹${val}` 
          }
        }
      }
    }
  });
}

// --- Order Execution Engine ---
function setOrderAction(action) {
  state.orderAction = action;
  const buyBtn = document.getElementById('orderActionBuy');
  const sellBtn = document.getElementById('orderActionSell');
  const execBtn = document.getElementById('tradeExecuteBtn');

  if (action === 'BUY') {
    buyBtn.className = 'trade-toggle-btn active buy';
    sellBtn.className = 'trade-toggle-btn';
    execBtn.className = 'btn-primary';
    execBtn.innerText = `BUY ${state.currentModalAsset ? state.currentModalAsset.symbol : ''}`;
  } else {
    buyBtn.className = 'trade-toggle-btn';
    sellBtn.className = 'trade-toggle-btn active sell';
    execBtn.className = 'btn-danger';
    execBtn.innerText = `SELL ${state.currentModalAsset ? state.currentModalAsset.symbol : ''}`;
  }
  calculateOrderMargin();
}

function setProductType(type) {
  state.productType = type;
  document.getElementById('productDelivery').className = type === 'DELIVERY' ? 'trade-toggle-btn active buy' : 'trade-toggle-btn';
  document.getElementById('productIntraday').className = type === 'INTRADAY' ? 'trade-toggle-btn active buy' : 'trade-toggle-btn';

  const levBanner = document.getElementById('leverageBanner');
  const marginLabel = document.getElementById('marginLabelText');
  if (type === 'INTRADAY') {
    levBanner.style.display = 'block';
    marginLabel.innerText = 'Required Margin (5x):';
  } else {
    levBanner.style.display = 'none';
    marginLabel.innerText = 'Required Amount (100%):';
  }
  calculateOrderMargin();
}

function setOrderVariety(variety) {
  state.orderVariety = variety;
  document.getElementById('varietyMarket').className = variety === 'MARKET' ? 'trade-toggle-btn active buy' : 'trade-toggle-btn';
  document.getElementById('varietyLimit').className = variety === 'LIMIT' ? 'trade-toggle-btn active buy' : 'trade-toggle-btn';

  const limitGroup = document.getElementById('limitPriceGroup');
  const marketGroup = document.getElementById('marketPriceGroup');
  if (variety === 'LIMIT') {
    limitGroup.style.display = 'block';
    marketGroup.style.display = 'none';
  } else {
    limitGroup.style.display = 'none';
    marketGroup.style.display = 'block';
  }
  calculateOrderMargin();
}

function stepQuantity(delta) {
  const input = document.getElementById('tradeQuantityInput');
  let val = parseFloat(input.value) || 1;
  val = Math.max(1, val + delta);
  input.value = val;
  calculateOrderMargin();
}

function setQuickQty(qty) {
  const input = document.getElementById('tradeQuantityInput');
  let val = parseFloat(input.value) || 0;
  input.value = val + qty;
  calculateOrderMargin();
}

function stepLimitPrice(delta) {
  const input = document.getElementById('tradeLimitPriceInput');
  let val = parseFloat(input.value) || (state.currentModalAsset ? state.currentModalAsset.price : 100);
  val = Math.max(0.05, Math.round((val + delta) * 100) / 100);
  input.value = val;
  calculateOrderMargin();
}

function calculateOrderMargin() {
  const qty = parseFloat(document.getElementById('tradeQuantityInput').value) || 0;
  let price = state.currentModalAsset ? state.currentModalAsset.price : 0;

  if (state.orderVariety === 'LIMIT') {
    const limitVal = parseFloat(document.getElementById('tradeLimitPriceInput').value);
    if (limitVal && limitVal > 0) price = limitVal;
  }

  const tradeTotal = qty * price;
  const isIntraday = state.productType === 'INTRADAY';
  const required = isIntraday ? tradeTotal * 0.20 : tradeTotal;

  document.getElementById('orderRequiredAmount').innerText = formatINR(required);
  document.getElementById('orderAvailableBalance').innerText = formatINR(getActiveAvailableCash());

  // Regulatory charges calculation
  const charges = calculateEstimatedCharges(tradeTotal, state.orderAction, state.productType);
  document.getElementById('orderEstCharges').innerText = `${formatINR(charges.total)} ℹ️`;
}

function calculateEstimatedCharges(amount, action = 'BUY', product = 'DELIVERY', assetType = 'STOCK') {
  amount = parseFloat(amount || 0);
  if (amount <= 0) {
    return { brokerage: 0, dp_charges: 0, stt: 0, exchange: 0, sebi: 0, stamp: 0, gst: 0, total: 0 };
  }
  const isSell = (action || '').toUpperCase() === 'SELL';
  const isIntra = (product || '').toUpperCase() === 'INTRADAY';
  const isMf = (assetType || '').toUpperCase() === 'MUTUAL_FUND';

  if (isMf) {
    return { brokerage: 0, dp_charges: 0, stt: 0, exchange: 0, sebi: 0, stamp: 0, gst: 0, total: 0 };
  }

  // Groww brokerage: min(₹20, 0.05% of order value)
  const brokerage = roundNumber(Math.min(20.0, amount * 0.0005), 2);
  // CDSL DP charges: flat ₹13.50 (+18% GST) on delivery sell
  const dp_charges = (isSell && !isIntra) ? 13.50 : 0.0;
  // STT: 0.1% on delivery sell / buy, 0.025% on intraday sell, 0 on intraday buy
  let stt = 0;
  if (isSell) {
    stt = isIntra ? roundNumber(amount * 0.00025, 2) : roundNumber(amount * 0.001, 2);
  } else {
    stt = isIntra ? 0.0 : roundNumber(amount * 0.001, 2);
  }
  // NSE exchange turnover charges: 0.00297%
  const exchange = roundNumber(amount * 0.0000297, 2);
  // SEBI turnover fee: ₹10 / crore (0.0001%)
  const sebi = roundNumber((amount / 10000000) * 10, 2);
  // Stamp duty: only on BUY (0.015% delivery, 0.003% intraday)
  const stamp = isSell ? 0.0 : roundNumber(amount * (isIntra ? 0.00003 : 0.00015), 2);
  // GST: 18% on (Brokerage + Exchange + SEBI + DP charges)
  const gst = roundNumber((brokerage + exchange + sebi + dp_charges) * 0.18, 2);
  const total = roundNumber(brokerage + dp_charges + stt + exchange + sebi + stamp + gst, 2);

  return {
    brokerage,
    dp_charges,
    stt,
    exchange,
    sebi,
    stamp,
    gst,
    total
  };
}

function openChargesModal() {
  const qty = parseFloat(document.getElementById('tradeQuantityInput').value) || 1;
  let price = state.currentModalAsset ? state.currentModalAsset.price : 100;
  if (state.orderVariety === 'LIMIT') {
    const lim = parseFloat(document.getElementById('tradeLimitPriceInput').value);
    if (lim && lim > 0) price = lim;
  }
  const totalVal = qty * price;
  const assetType = state.currentModalAsset ? state.currentModalAsset.asset_type : 'STOCK';
  const c = calculateEstimatedCharges(totalVal, state.orderAction, state.productType, assetType);
  renderChargesModalContent(c, state.orderAction, state.productType, totalVal);
}

function openPageChargesModal() {
  if (!currentPageAsset) return;
  const qtyInput = document.getElementById('pageOrderQuantity');
  const qty = parseInt((qtyInput ? qtyInput.value : '1') || '1', 10);
  const limInput = document.getElementById('pageOrderLimitPrice');
  const trigInput = document.getElementById('pageOrderTriggerPrice');

  let effectivePrice = currentPageAsset.price;
  if (pageOrderState.variety === 'LIMIT') {
    const limVal = parseFloat((limInput ? limInput.value : '') || '0');
    effectivePrice = limVal > 0 ? limVal : currentPageAsset.price;
  } else if (pageOrderState.variety === 'STOP_LOSS') {
    const trigVal = parseFloat((trigInput ? trigInput.value : '') || '0');
    if (pageOrderState.action === 'BUY' && trigVal > 0) {
      effectivePrice = trigVal;
    }
  } else if (pageOrderState.variety === 'GTT') {
    const limVal = parseFloat((limInput ? limInput.value : '') || '0');
    const trigVal = parseFloat((trigInput ? trigInput.value : '') || '0');
    effectivePrice = limVal > 0 ? limVal : (trigVal > 0 ? trigVal : currentPageAsset.price);
  }

  const totalVal = qty * effectivePrice;
  const c = calculateEstimatedCharges(totalVal, pageOrderState.action, pageOrderState.product, currentPageAsset.asset_type || 'STOCK');
  renderChargesModalContent(c, pageOrderState.action, pageOrderState.product, totalVal);
}

function renderChargesModalContent(c, action, product, totalVal) {
  const isSell = (action || '').toUpperCase() === 'SELL';
  const isIntra = (product || '').toUpperCase() === 'INTRADAY';
  const list = document.getElementById('chargesBreakdownList');
  if (!list) return;

  let html = `
    <div style="display: flex; justify-content: space-between;"><span>Brokerage (Groww: 0.05% max ₹20)</span><strong>${formatINR(c.brokerage)}</strong></div>
  `;
  if (isSell && !isIntra) {
    html += `
      <div style="display: flex; justify-content: space-between;"><span>CDSL DP Charges (Depository fee)</span><strong>${formatINR(c.dp_charges)}</strong></div>
    `;
  }
  html += `
    <div style="display: flex; justify-content: space-between;"><span>Securities Transaction Tax (STT)</span><strong>${formatINR(c.stt)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>Exchange Turnover Charges (NSE 0.00297%)</span><strong>${formatINR(c.exchange)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>SEBI Turnover Charges</span><strong>${formatINR(c.sebi)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>Stamp Duty (Govt)</span><strong>${formatINR(c.stamp)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>GST (18% on Brokerage, Txn & DP)</span><strong>${formatINR(c.gst)}</strong></div>
  `;
  list.innerHTML = html;

  const totalEl = document.getElementById('chargesModalTotal');
  if (totalEl) totalEl.innerText = formatINR(c.total);

  const noteEl = document.getElementById('chargesModalNote');
  if (noteEl) {
    if (isSell && !isIntra) {
      noteEl.innerHTML = `Standard SEBI, CDSL and exchange regulatory charges for Delivery Sell. <strong>Net settlement (${formatINR(Math.max(0, totalVal - c.total))})</strong> is credited to your balance upon sale.`;
    } else {
      noteEl.innerText = 'Taxes & regulatory charges are prescribed by SEBI, Exchange (NSE/BSE), and Ministry of Finance.';
    }
  }

  const modal = document.getElementById('chargesModalOverlay');
  if (modal) modal.classList.add('active');
}

function closeChargesModal() {
  document.getElementById('chargesModalOverlay').classList.remove('active');
}

function roundNumber(num, dec) {
  return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
}

function setOrderExecutionLoading(isLoading, action = 'BUY') {
  const pageBtn = document.getElementById('pageOrderExecuteBtn');
  const drawerBtn = document.getElementById('drawerOrderExecuteBtn');
  const tradeModalBtn = document.getElementById('tradeExecuteBtn');
  const optBtn = document.getElementById('optExecuteBtn');

  const btns = [pageBtn, drawerBtn, tradeModalBtn, optBtn].filter(Boolean);
  btns.forEach(btn => {
    if (isLoading) {
      if (!btn.dataset.originalHtml) {
        btn.dataset.originalHtml = btn.innerHTML;
      }
      btn.disabled = true;
      btn.innerHTML = `<span class="btn-spinner"></span> <span>Executing ${action || 'Order'}...</span>`;
    } else {
      btn.disabled = false;
      if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
        delete btn.dataset.originalHtml;
      }
    }
  });
}
window.setOrderExecutionLoading = setOrderExecutionLoading;

async function submitOrder() {
  if (isGuest()) {
    closeTradeModal();
    showToast('Please create your free account to unlock ₹10,00,000 virtual balance and start trading.', false);
    navigateTo('/onboarding');
    return;
  }

  if (!state.currentModalAsset) return;

  const qty = parseFloat(document.getElementById('tradeQuantityInput').value);
  if (!qty || qty <= 0) {
    showToast('Please enter a valid quantity', true);
    return;
  }

  let limitPrice = null;
  if (state.orderVariety === 'LIMIT') {
    limitPrice = parseFloat(document.getElementById('tradeLimitPriceInput').value);
    if (!limitPrice || limitPrice <= 0) {
      showToast('Please enter a valid Limit Price', true);
      return;
    }
  }

  const asset = state.currentModalAsset;
  const execPrice = (state.orderVariety === 'LIMIT' && limitPrice) ? limitPrice : asset.price;

  closeTradeModal();

  openOrderConfirmModal({
    origin: 'MODAL',
    symbol: asset.symbol,
    name: asset.name,
    asset_type: asset.asset_type || 'STOCK',
    action: state.orderAction,
    product: state.productType,
    quantity: qty,
    price: execPrice,
    variety: state.orderVariety,
    limit_price: limitPrice,
    trigger_price: 0
  });
}

// --- Market Timings & Rules (Replaced obsolete Funds & Timings Modal) ---
function openFundsModal() {
  openMarketHoursModal();
}

function closeFundsModal() {
  closeMarketHoursModal();
}

async function restoreFullBalance() {
  if (!currentUser || isGuest()) {
    showToast('Please log in or create an account to manage virtual funds.', true);
    return;
  }
  try {
    const res = await fetch('/api/account/restore', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      showToast('Trading capital fully restored to ₹10,00,000.00!');
      await fetchAccount();
      closeFundsModal();
      if (state.currentTab === 'holdings') fetchPortfolio();
      if (state.currentTab === 'positions') fetchPositions();
    } else {
      showToast(data.detail || 'Failed to restore capital', true);
    }
  } catch (err) {
    console.error('Failed to restore balance:', err);
    showToast('Error restoring balance', true);
  }
}

async function resetEntirePortfolio() {
  const confirmed = confirm('Are you sure you want to reset your entire portfolio?\n\nThis will clear all holdings, open positions, and order history, and restore your balance to ₹10,00,000.00.');
  if (!confirmed) return;

  try {
    const res = await fetch('/api/account/reset', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      showToast('Portfolio & trading balance completely reset to ₹10,00,000.00!');
      await fetchAccount();
      closeFundsModal();
      if (state.currentTab === 'holdings') fetchPortfolio();
      if (state.currentTab === 'positions') fetchPositions();
      if (state.currentTab === 'orders') fetchOrders();
    } else {
      showToast(data.detail || 'Failed to reset portfolio', true);
    }
  } catch (err) {
    console.error('Failed to reset portfolio:', err);
    showToast('Error resetting portfolio', true);
  }
}

async function confirmDeleteAccount() {
  const menu = document.getElementById('userDropdownMenu');
  if (menu) menu.style.display = 'none';

  if (!currentUser || isGuest()) {
    showToast('No active account to delete.', true);
    return;
  }

  const confirmed = confirm(
    `Are you sure you want to permanently delete your account (${currentUser.name})?\n\nThis will wipe all holdings, open positions, order history, watchlist, and virtual funds. This action cannot be undone.`
  );
  if (!confirmed) return;

  try {
    const res = await fetch('/api/user/delete', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      localStorage.removeItem('stoxify_user_id');
      localStorage.removeItem('stoxify_cached_user');
      localStorage.removeItem('stoxify_watchlist_cache');
      try {
        let recent = JSON.parse(localStorage.getItem('stoxify_recent_accounts') || '[]');
        if (currentUser && currentUser.id) {
          recent = recent.filter(item => item.id !== currentUser.id && item.email !== currentUser.email);
        }
        localStorage.setItem('stoxify_recent_accounts', JSON.stringify(recent));
      } catch (e) {}
      localStorage.setItem('stoxify_guest_mode', 'true');
      document.documentElement.classList.remove('user-logged-in');
      document.documentElement.classList.add('user-guest');
      currentUser = null;
      state.account = { balance: 0.0 };
      state.watchlist = new Set();
      updateNavbarProfile();
      closeFundsModal();
      showToast('Account permanently deleted. Returned to guest mode.');
      navigateTo('/explore');
      if (state.currentTab === 'holdings') fetchPortfolio();
      if (state.currentTab === 'positions') fetchPositions();
      if (state.currentTab === 'orders') fetchOrders();
      if (state.currentTab === 'watchlist') fetchWatchlist();
    } else {
      showToast(data.detail || 'Failed to delete account', true);
    }
  } catch (err) {
    console.error('Delete account failed:', err);
    showToast('Error deleting account', true);
  }
}

// --- PWA (Progressive Web App) Install Engine ---
let deferredInstallPrompt = null;

function isAppInstalled() {
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                       window.matchMedia('(display-mode: minimal-ui)').matches ||
                       window.matchMedia('(display-mode: fullscreen)').matches ||
                       window.matchMedia('(display-mode: window-controls-overlay)').matches ||
                       window.navigator.standalone === true ||
                       window.location.search.includes('source=pwa');
  return Boolean(isStandalone);
}

function dismissMobileInstallBanner() {
  sessionStorage.setItem('stoxify_mob_install_dismissed', '1');
  const banner = document.getElementById('mobileInstallBanner');
  if (banner) banner.style.display = 'none';
}

function updateInstallButtonsVisibility() {
  const installed = isAppInstalled();
  if (installed) {
    document.body.classList.add('pwa-installed');
  } else {
    document.body.classList.remove('pwa-installed');
  }

  const topBtn = document.getElementById('btnInstallApp');
  const dropdownItem = document.getElementById('dropdownInstallItem');
  const mobBanner = document.getElementById('mobileInstallBanner');
  const mobDismissed = sessionStorage.getItem('stoxify_mob_install_dismissed') === '1';

  // Desktop navbar header button is visible in browser view, hidden on mobile or standalone PWA
  const isMobile = window.innerWidth <= 768;
  if (topBtn) topBtn.style.display = (installed || isMobile) ? 'none' : 'inline-flex';
  if (dropdownItem) dropdownItem.style.display = installed ? 'none' : 'flex';

  // Mobile banner is visible on mobile browsers unless running in standalone PWA or dismissed in this session
  if (mobBanner) {
    if (installed || mobDismissed) {
      mobBanner.style.display = 'none';
    } else {
      const isMobile = window.innerWidth <= 768 || detectPlatform() !== 'desktop';
      mobBanner.style.display = isMobile ? 'flex' : 'none';
    }
  }
}

// Check getInstalledRelatedApps if supported by modern browser
if ('getInstalledRelatedApps' in navigator) {
  navigator.getInstalledRelatedApps().then(apps => {
    if (apps && apps.length > 0) {
      console.log('Stoxifyin related PWA detected on device');
    }
  }).catch(() => {});
}

function detectPlatform() {
  const ua = navigator.userAgent || navigator.vendor || window.opera || '';
  if (/iPad|iPhone|iPod/.test(ua) && !window.MSStream) return 'ios';
  if (/android/i.test(ua)) return 'android';
  return 'desktop';
}

function switchPwaTab(platform) {
  ['ios', 'android', 'desktop'].forEach(p => {
    const tabKey = p.charAt(0).toUpperCase() + p.slice(1);
    const tabBtn = document.getElementById(`pwaTabBtn${tabKey}`);
    const content = document.getElementById(`pwaContent${tabKey}`);
    if (tabBtn) tabBtn.classList.toggle('active', p === platform);
    if (content) content.style.display = (p === platform) ? 'block' : 'none';
  });
}

function openPwaGuideModal(defaultPlatform) {
  const plat = defaultPlatform || detectPlatform();
  switchPwaTab(plat);
  const promptWrap = document.getElementById('androidDirectPromptWrap');
  if (promptWrap) {
    promptWrap.style.display = deferredInstallPrompt ? 'block' : 'none';
  }
  const modal = document.getElementById('pwaInstallGuideModalOverlay');
  if (modal) modal.style.display = 'flex';
}

function closePwaGuideModal() {
  const modal = document.getElementById('pwaInstallGuideModalOverlay');
  if (modal) modal.style.display = 'none';
}

async function triggerNativeInstallPrompt() {
  if (deferredInstallPrompt) {
    try {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      if (outcome === 'accepted') {
        closePwaGuideModal();
        showToast("Stoxifyin' installed successfully! You can launch it from your home screen.");
      }
      deferredInstallPrompt = null;
    } catch (err) {
      console.warn('Native prompt error:', err);
    }
  }
}

async function installPWA() {
  if (isAppInstalled()) {
    showToast("Stoxifyin' is already running in app mode!");
    return;
  }
  if (deferredInstallPrompt) {
    try {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      if (outcome === 'accepted') {
        closePwaGuideModal();
        showToast("Stoxifyin' installed successfully! You can launch it from your home screen.");
        deferredInstallPrompt = null;
        return;
      }
      deferredInstallPrompt = null;
    } catch (err) {
      console.warn('Direct install prompt error:', err);
    }
  }
  openPwaGuideModal();
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  updateInstallButtonsVisibility();
  const promptWrap = document.getElementById('androidDirectPromptWrap');
  if (promptWrap) promptWrap.style.display = 'block';
});

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  closePwaGuideModal();
  showToast("Stoxifyin' installed successfully! You can launch it from your home screen.");
});

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).then((reg) => {
      reg.update();
      console.log('Stoxifyin PWA Service Worker registered:', reg.scope);
    }).catch((err) => {
      console.warn('Service Worker registration skipped:', err);
    });
  });
}

// --- Initialization ---
function bootApp() {
  if (window.__stoxify_booted) return;
  window.__stoxify_booted = true;

  // Clear stale install flag and saved accounts from localStorage
  try {
    localStorage.removeItem('stoxify_app_installed');
    localStorage.removeItem('stoxify_recent_accounts');
  } catch (e) {}

  // Instant synchronous session hydration: 0ms cold-start latency
  try {
    const cachedUserStr = localStorage.getItem('stoxify_cached_user');
    const guestFlag = localStorage.getItem('stoxify_guest_mode') === 'true';
    if (cachedUserStr && !guestFlag) {
      currentUser = JSON.parse(cachedUserStr);
      if (currentUser.balance !== undefined) {
        state.account.balance = Number(currentUser.balance);
        if (currentUser.bank_balance !== undefined) {
          state.account.bank_balance = Number(currentUser.bank_balance);
        }
      }
      if (currentUser.id && !localStorage.getItem('stoxify_user_id')) {
        localStorage.setItem('stoxify_user_id', currentUser.id);
      }
      document.documentElement.classList.add('user-logged-in');
      document.documentElement.classList.remove('user-guest');
      updateNavbarProfile();
    }
  } catch (e) {}

  initTheme();

  // Set install buttons visibility based on whether running in standalone mode
  updateInstallButtonsVisibility();

  // Close PWA guide modal on clicking backdrop
  const pwaModal = document.getElementById('pwaInstallGuideModalOverlay');
  if (pwaModal) {
    pwaModal.addEventListener('click', (e) => {
      if (e.target === pwaModal) closePwaGuideModal();
    });
  }

  // Instant render of explore data so user never waits for a loading state
  try {
    state.exploreData = loadStoredExploreData();
    renderExploreStocks();
    renderExploreMutualFunds();
  } catch (e) {
    console.warn('Initial explore render skipped:', e);
  }

  try {
    fetchCurrentUser();
  } catch (e) {}

  try {
    handleRoute();
  } catch (e) {
    console.error('Initial route failed:', e);
  }

  Promise.all([
    fetchMarketStatus().catch(e => console.warn(e)),
    fetchAccount().catch(e => console.warn(e)),
    fetchIndices().catch(e => console.warn(e)),
    fetchExploreData().catch(e => console.warn(e)),
    fetchWatchlist().catch(e => console.warn(e)),
    fetchPositions().catch(e => console.warn(e))
  ]);

  // Polling intervals
  setInterval(() => fetchMarketStatus(), 10000);
  setInterval(() => {
    fetchIndices();
    if (state.currentTab === 'holdings') fetchPortfolio();
    if (state.currentTab === 'positions') fetchPositions();
  }, 20000);
}

if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', bootApp);
} else {
  bootApp();
}



/* =======================================================
   CLIENT-SIDE ROUTER ENGINE (HTML5 History API)
   ======================================================= */
function navigateTo(path, pushState = true) {
  if (pushState && window.location.pathname !== path) {
    history.pushState(null, '', path);
  }
  handleRoute();
}

function goBackFromAssetPage() {
  if (window.history.length > 1) {
    window.history.back();
  } else {
    navigateTo('/explore');
  }
}

function goBackFromProfilePage() {
  document.body.classList.remove('viewing-profile');
  document.documentElement.classList.remove('viewing-profile');
  if (window.history.length > 1) {
    window.history.back();
  } else {
    navigateTo('/explore');
  }
}

function showProfilePage() {
  document.body.classList.remove('viewing-asset-detail');
  document.documentElement.classList.remove('viewing-asset-detail');
  document.body.classList.add('viewing-profile');
  document.documentElement.classList.add('viewing-profile');
  closeMobileTradeDrawer();
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.mobile-bottom-bar .mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  const profilePane = document.getElementById('pane-profile');
  if (profilePane) profilePane.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  renderProfilePageData();
}

function handleRoute() {
  const path = window.location.pathname;
  const userMenu = document.getElementById('userDropdownMenu');
  if (userMenu) userMenu.style.display = 'none';

  if (path !== '/profile') {
    document.body.classList.remove('viewing-profile');
    document.documentElement.classList.remove('viewing-profile');
  }

  if (path.startsWith('/stock/')) {
    const sym = decodeURIComponent(path.replace('/stock/', '')).trim();
    showAssetPage(sym, 'STOCK');
  } else if (path.startsWith('/mf/')) {
    const sym = decodeURIComponent(path.replace('/mf/', '')).trim();
    showAssetPage(sym, 'MUTUAL_FUND');
  } else if (path === '/onboarding') {
    showOnboardingPage();
  } else if (path === '/profile') {
    showProfilePage();
  } else if (path === '/login') {
    switchTab('explore', false);
    openLoginModal();
  } else if (path === '/holdings') {
    switchTab('holdings', false);
  } else if (path === '/positions') {
    switchTab('positions', false);
  } else if (path === '/orders') {
    switchTab('orders', false);
  } else if (path === '/watchlist') {
    switchTab('watchlist', false);
  } else {
    switchTab('explore', false);
  }
}

window.addEventListener('popstate', () => handleRoute());

/* =======================================================
   USER SESSION & NAVBAR PROFILE ENGINE
   ======================================================= */
async function fetchCurrentUser() {
  if (localStorage.getItem('stoxify_guest_mode') === 'true') {
    currentUser = null;
    localStorage.removeItem('stoxify_cached_user');
    document.documentElement.classList.remove('user-logged-in');
    document.documentElement.classList.add('user-guest');
    updateNavbarProfile();
    return;
  }
  try {
    const res = await fetch('/api/user/current');
    const u = await res.json();
    if (u && u.id && !u.is_guest) {
      currentUser = u;
      if (u.balance !== undefined) {
        state.account.balance = Number(u.balance);
        if (u.bank_balance !== undefined) state.account.bank_balance = Number(u.bank_balance);
      }
      localStorage.setItem('stoxify_user_id', u.id);
      localStorage.setItem('stoxify_cached_user', JSON.stringify(u));
      localStorage.removeItem('stoxify_guest_mode');
      document.documentElement.classList.add('user-logged-in');
      document.documentElement.classList.remove('user-guest');
    } else {
      currentUser = null;
      localStorage.removeItem('stoxify_user_id');
      localStorage.removeItem('stoxify_cached_user');
      document.documentElement.classList.remove('user-logged-in');
      document.documentElement.classList.add('user-guest');
    }
  } catch (err) {
    console.error('Failed to fetch user:', err);
  }
  updateNavbarProfile();
}

function updateNavbarProfile() {
  const getStartedBtn = document.getElementById('navGetStartedBtn');
  const profileWrapper = document.getElementById('navProfileWrapper');
  const initialsEl = document.getElementById('navUserInitials');
  const menuAvatarEl = document.getElementById('menuUserAvatar');
  const menuNameEl = document.getElementById('menuUserName');
  const menuEmailEl = document.getElementById('menuUserEmail');
  const menuDematEl = document.getElementById('menuUserDemat');
  const menuBankEl = document.getElementById('menuUserBank');
  const menuBalEl = document.getElementById('menuUserBalance');

  const guestBtns = document.querySelectorAll('#navAuthBtn, #navGetStartedBtn, #navGuestButtons');

  if (isGuest() || !currentUser) {
    document.documentElement.classList.remove('user-logged-in');
    document.documentElement.classList.add('user-guest');
    guestBtns.forEach(btn => {
      btn.style.setProperty('display', 'inline-flex', 'important');
    });
    if (profileWrapper) profileWrapper.style.setProperty('display', 'none', 'important');
    const navBalEl = document.getElementById('navBalanceDisplay');
    if (navBalEl) navBalEl.innerText = '₹0.00';
    return;
  }

  // Authenticated user
  document.documentElement.classList.add('user-logged-in');
  document.documentElement.classList.remove('user-guest');
  guestBtns.forEach(btn => {
    btn.style.setProperty('display', 'none', 'important');
  });
  if (profileWrapper) profileWrapper.style.setProperty('display', 'inline-flex', 'important');

  const initials = currentUser.name ? currentUser.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'ST';
  const avatarColor = currentUser.avatar_color || '#0EA5E9';
  if (initialsEl) {
    initialsEl.innerText = initials;
    const avatarBtn = document.getElementById('navUserAvatarBtn');
    if (avatarBtn) avatarBtn.style.background = avatarColor;
  }
  if (menuAvatarEl) {
    menuAvatarEl.innerText = initials;
    menuAvatarEl.style.background = avatarColor;
  }
  if (menuNameEl) menuNameEl.innerText = currentUser.name;
  if (menuEmailEl) menuEmailEl.innerText = currentUser.email || '';
  const menuUsernameEl = document.getElementById('menuUserUsername');
  if (menuUsernameEl) {
    if (currentUser.username) {
      menuUsernameEl.innerText = `@${currentUser.username}`;
      menuUsernameEl.style.display = 'inline-block';
    } else {
      menuUsernameEl.style.display = 'none';
    }
  }
  if (menuDematEl) menuDematEl.innerText = `Demat: STOX-${(currentUser.id || '9876').slice(-6).toUpperCase()}`;
  const last4 = (currentUser.bank_account || '5678').slice(-4);
  if (menuBankEl) menuBankEl.innerText = `${currentUser.bank_name || 'HDFC Bank'} •••• ${last4} (Verified ✓)`;
  const walletBal = currentUser.balance !== undefined ? currentUser.balance : 0.0;
  if (menuBalEl) menuBalEl.innerText = formatINR(walletBal);
  const navBalEl = document.getElementById('navBalanceDisplay');
  if (navBalEl) navBalEl.innerText = formatINR(walletBal);

  // Dedicated Groww-Style Profile Page Elements
  const profAvatarEl = document.getElementById('profilePageAvatar');
  const profNameEl = document.getElementById('profilePageName');
  const profEmailEl = document.getElementById('profilePageEmail');
  const profDematEl = document.getElementById('profilePageDemat');
  const profWalletBalEl = document.getElementById('profileWalletBalanceDisplay');
  const profBankNameEl = document.getElementById('profileBankNameDisplay');
  const profBankAccEl = document.getElementById('profileBankAccountDisplay');
  const profBankBalEl = document.getElementById('profileBankBalanceDisplay');

  if (profAvatarEl) {
    profAvatarEl.innerText = initials;
    profAvatarEl.style.background = avatarColor;
  }
  if (profNameEl) profNameEl.innerText = currentUser.name;
  if (profEmailEl) profEmailEl.innerText = currentUser.email || '';
  if (profDematEl) profDematEl.innerText = `Demat: STOX-${(currentUser.id || '9876').slice(-6).toUpperCase()}`;
  if (profWalletBalEl) profWalletBalEl.innerText = formatINR(walletBal);
  const bName = currentUser.bank_name || 'HDFC Bank';
  const bIfsc = currentUser.bank_ifsc || `${bName.split(' ')[0].toUpperCase().slice(0, 4)}0001234`;
  const bBal = currentUser.bank_balance !== undefined ? currentUser.bank_balance : 1000000.0;
  if (profBankNameEl) profBankNameEl.innerText = bName;
  if (profBankAccEl) profBankAccEl.innerText = `A/C •••• ${last4} • IFSC: ${bIfsc}`;
  if (profBankBalEl) profBankBalEl.innerText = formatINR(bBal);
}

function logoutUser() {
  localStorage.setItem('stoxify_guest_mode', 'true');
  localStorage.removeItem('stoxify_user_id');
  localStorage.removeItem('stoxify_cached_user');
  document.documentElement.classList.remove('user-logged-in');
  document.documentElement.classList.add('user-guest');
  currentUser = null;
  updateNavbarProfile();
  showToast('Logged out successfully.');
  if (state.currentTab === 'holdings') fetchPortfolio();
  if (state.currentTab === 'positions') fetchPositions();
  if (state.currentTab === 'orders') fetchOrders();
  navigateTo('/explore');
}

function toggleProfileDropdown() {
  if (window.innerWidth <= 768) {
    // Mobile view: Open dedicated Groww-style full profile page
    navigateTo('/profile');
    return;
  }
  const menu = document.getElementById('userDropdownMenu');
  if (!menu) return;
  menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

document.addEventListener('click', (e) => {
  const wrapper = document.getElementById('navProfileWrapper');
  const menu = document.getElementById('userDropdownMenu');
  if (wrapper && menu && !wrapper.contains(e.target)) {
    menu.style.display = 'none';
  }

  const editOverlay = document.getElementById('editProfileModalOverlay');
  if (editOverlay && e.target === editOverlay) {
    closeEditProfileModal();
  }
  const fundsOverlay = document.getElementById('fundsModalOverlay');
  if (fundsOverlay && e.target === fundsOverlay) {
    closeFundsModal();
  }
  const loginOverlay = document.getElementById('loginModalOverlay');
  if (loginOverlay && e.target === loginOverlay) {
    closeLoginModal();
  }
  const upiOverlay = document.getElementById('upiAddMoneyModal');
  if (upiOverlay && e.target === upiOverlay) {
    closeAddMoneyModal();
  }
  const wdrOverlay = document.getElementById('withdrawMoneyModal');
  if (wdrOverlay && e.target === wdrOverlay) {
    closeWithdrawModal();
  }
  const pbOverlay = document.getElementById('bankPassbookModal');
  if (pbOverlay && e.target === pbOverlay) {
    closeBankPassbookModal();
  }
});

// --- Edit Profile Management ---
let selectedEditAvatarColor = '#0EA5E9';

function openEditProfileModal() {
  const menu = document.getElementById('userDropdownMenu');
  if (menu) menu.style.display = 'none';

  if (!currentUser || isGuest()) {
    showToast('Please create or log into your account to edit profile.', true);
    navigateTo('/onboarding');
    return;
  }

  const nameInput = document.getElementById('editProfileName');
  const emailInput = document.getElementById('editProfileEmail');
  const phoneInput = document.getElementById('editProfilePhone');
  const dobInput = document.getElementById('editProfileDob');
  const panInput = document.getElementById('editProfilePan');
  const bankNameInput = document.getElementById('editProfileBankName');
  const bankAccInput = document.getElementById('editProfileBankAccount');
  const pinInput = document.getElementById('editProfilePin');
  const dematDisplay = document.getElementById('editProfileDematDisplay');

  if (nameInput) nameInput.value = currentUser.name || '';
  const usernameInput = document.getElementById('editProfileUsername');
  if (usernameInput) usernameInput.value = currentUser.username || '';
  const passwordInput = document.getElementById('editProfilePassword');
  if (passwordInput) passwordInput.value = '';
  if (emailInput) emailInput.value = currentUser.email || '';
  if (phoneInput) phoneInput.value = currentUser.phone || '';
  if (dobInput) dobInput.value = currentUser.dob || '';
  if (panInput) panInput.value = currentUser.pan || '';
  if (bankNameInput) bankNameInput.value = currentUser.bank_name || 'HDFC Bank';
  if (bankAccInput) bankAccInput.value = currentUser.bank_account || '';
  if (pinInput) pinInput.value = currentUser.pin || '';

  selectedEditAvatarColor = currentUser.avatar_color || '#0EA5E9';
  highlightSelectedAvatarColor(selectedEditAvatarColor);

  if (dematDisplay) {
    const dematId = currentUser.id ? `STOX-${currentUser.id.replace('STOX-', '').slice(-6).toUpperCase()}` : 'STOX-782910';
    dematDisplay.innerText = `Demat: ${dematId}`;
  }

  updateEditAvatarPreview();
  const overlay = document.getElementById('editProfileModalOverlay');
  if (overlay) overlay.classList.add('active');
}

function closeEditProfileModal() {
  const overlay = document.getElementById('editProfileModalOverlay');
  if (overlay) overlay.classList.remove('active');
}

function selectEditAvatarColor(color) {
  selectedEditAvatarColor = color;
  highlightSelectedAvatarColor(color);
  updateEditAvatarPreview();
}

function highlightSelectedAvatarColor(color) {
  document.querySelectorAll('.avatar-color-dot').forEach(dot => {
    if (dot.getAttribute('data-color') === color) {
      dot.style.outline = '2px solid var(--text-primary)';
      dot.style.transform = 'scale(1.22)';
    } else {
      dot.style.outline = 'none';
      dot.style.transform = 'scale(1)';
    }
  });
}

function updateEditAvatarPreview() {
  const nameInput = document.getElementById('editProfileName');
  const previewAvatar = document.getElementById('editProfileAvatarPreview');
  const previewName = document.getElementById('editProfilePreviewName');

  const nameVal = (nameInput ? nameInput.value.trim() : '') || (currentUser ? currentUser.name : 'Trader');
  const initials = nameVal ? nameVal.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'ST';

  if (previewAvatar) {
    previewAvatar.innerText = initials;
    previewAvatar.style.background = selectedEditAvatarColor;
  }
  if (previewName) {
    previewName.innerText = nameVal || 'Trader';
  }
}

async function saveUserProfile() {
  if (!currentUser || isGuest()) {
    showToast('No active account to update.', true);
    return;
  }

  const name = document.getElementById('editProfileName').value.trim();
  const username = document.getElementById('editProfileUsername') ? document.getElementById('editProfileUsername').value.trim().replace(/^@/, '').toLowerCase() : '';
  const password = document.getElementById('editProfilePassword') ? document.getElementById('editProfilePassword').value.trim() : '';
  const email = document.getElementById('editProfileEmail').value.trim();
  const phone = document.getElementById('editProfilePhone').value.trim();
  const dob = document.getElementById('editProfileDob').value.trim();
  const pan = document.getElementById('editProfilePan').value.trim().toUpperCase();
  const bank_name = document.getElementById('editProfileBankName').value.trim();
  const bank_account = document.getElementById('editProfileBankAccount').value.trim();
  const pin = document.getElementById('editProfilePin').value.trim();

  if (!name) {
    showToast('Legal Name is required', true);
    document.getElementById('editProfileName').focus();
    return;
  }
  if (username) {
    if (username.length < 3 || username.length > 25) {
      showToast('Username must be between 3 and 25 characters', true);
      document.getElementById('editProfileUsername')?.focus();
      return;
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      showToast('Username can only contain letters, numbers, and underscores', true);
      document.getElementById('editProfileUsername')?.focus();
      return;
    }
  }
  if (password && password.length < 6) {
    showToast('Password must be at least 6 characters', true);
    document.getElementById('editProfilePassword')?.focus();
    return;
  }
  if (!email || !email.includes('@')) {
    showToast('Please enter a valid email address', true);
    document.getElementById('editProfileEmail').focus();
    return;
  }
  if (pin && (pin.length !== 4 || !/^\d{4}$/.test(pin))) {
    showToast('Security PIN must be exactly 4 digits', true);
    document.getElementById('editProfilePin').focus();
    return;
  }
  if (dob) {
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    if (age < 10) {
      showToast('You must be at least 10 years of age', true);
      document.getElementById('editProfileDob').focus();
      return;
    }
  }

  const saveBtn = document.getElementById('btnSaveProfile');
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerText = 'Saving...';
  }

  try {
    const res = await fetch('/api/user/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: currentUser.id,
        name,
        username: username || null,
        password: password || null,
        email,
        phone,
        dob,
        pan,
        bank_name,
        bank_account,
        pin,
        avatar_color: selectedEditAvatarColor
      })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      currentUser = data.user;
      localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
      updateNavbarProfile();
      closeEditProfileModal();
      showToast('Profile updated successfully!');
    } else {
      showToast(data.detail || 'Failed to update profile', true);
    }
  } catch (err) {
    console.error('Failed to save profile:', err);
    showToast('Error saving profile changes', true);
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = 'Save Changes';
    }
  }
}

// =======================================================
// DEDICATED GROWW PROFILE & BANK ACCOUNT ENGINE
// =======================================================
let enteredUpiPin = '';
let currentUpiAddAmount = 50000;
let cachedBankAccount = null;

function getLocalBankTxs(uid) {
  if (!uid) return [];
  try {
    const raw = localStorage.getItem(`stoxify_bank_txs_${uid}`);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function saveLocalBankTx(uid, tx) {
  if (!uid || !tx) return;
  try {
    const list = getLocalBankTxs(uid);
    const txKey = tx.reference_id || `${tx.type}-${tx.amount}-${tx.created_at}`;
    if (list.some(item => (item.reference_id && item.reference_id === tx.reference_id) || `${item.type}-${item.amount}-${item.created_at}` === txKey)) {
      return;
    }
    list.unshift(tx);
    if (list.length > 50) list.length = 50;
    localStorage.setItem(`stoxify_bank_txs_${uid}`, JSON.stringify(list));
  } catch (e) {}
}

async function loadBankAccountDetails() {
  if (isGuest() || !currentUser) return null;
  const uid = currentUser.id || localStorage.getItem('stoxify_user_id');
  try {
    const res = await fetch(`/api/funds/bank-account?user_id=${encodeURIComponent(uid || '')}`, {
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    if (res.ok) {
      const data = await res.json();
      if (data && data.bank_name) {
        // Merge server transactions with local browser cached transactions
        const localTxs = getLocalBankTxs(uid);
        const seenRefs = new Set();
        const merged = [];
        (data.transactions || []).forEach(tx => {
          const key = tx.reference_id || `${tx.type}-${tx.amount}-${tx.created_at}`;
          seenRefs.add(key);
          merged.push(tx);
        });
        localTxs.forEach(tx => {
          const key = tx.reference_id || `${tx.type}-${tx.amount}-${tx.created_at}`;
          if (!seenRefs.has(key)) {
            seenRefs.add(key);
            merged.push(tx);
          }
        });
        if (merged.length > 0) {
          merged.sort((a, b) => {
            const da = a.created_at ? new Date(String(a.created_at).replace(' ', 'T')).getTime() : 0;
            const db = b.created_at ? new Date(String(b.created_at).replace(' ', 'T')).getTime() : 0;
            return db - da;
          });
          data.transactions = merged;
          try {
            localStorage.setItem(`stoxify_bank_txs_${uid}`, JSON.stringify(merged));
          } catch (e) {}
        }
        cachedBankAccount = data;
        if (currentUser && data.bank_balance !== undefined) {
          currentUser.bank_balance = data.bank_balance;
          try {
            localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
          } catch (e) {}
        }
        return data;
      }
    }
  } catch (err) {
    console.error('Failed to load bank account details:', err);
  }
  const rawAcc = String(currentUser.bank_account || '50100234567890');
  const masked = rawAcc.length >= 4 ? `•••• ${rawAcc.slice(-4)}` : rawAcc;
  const fallbackTxs = uid ? getLocalBankTxs(uid) : [];
  return cachedBankAccount || {
    bank_name: currentUser.bank_name || 'HDFC Bank',
    bank_account: rawAcc,
    bank_account_masked: masked,
    bank_masked_account: masked,
    bank_ifsc: currentUser.bank_ifsc || `${(currentUser.bank_name || 'HDFC').split(' ')[0].toUpperCase().slice(0, 4)}0001234`,
    bank_upi_id: currentUser.bank_upi_id || `${(currentUser.username || 'user').toLowerCase()}@${(currentUser.bank_name || 'hdfc').split(' ')[0].toLowerCase()}bank`,
    bank_balance: currentUser.bank_balance !== undefined ? currentUser.bank_balance : 1000000.0,
    balance: currentUser.balance !== undefined ? currentUser.balance : (state.account ? state.account.balance : 0.0),
    wallet_balance: currentUser.balance !== undefined ? currentUser.balance : (state.account ? state.account.balance : 0.0),
    account_holder: currentUser.name || 'Trader',
    transactions: fallbackTxs
  };
}

async function renderProfilePageData() {
  if (isGuest() || !currentUser) {
    const profNameEl = document.getElementById('profilePageName');
    if (profNameEl) profNameEl.innerText = 'Guest User';
    const profEmailEl = document.getElementById('profilePageEmail');
    if (profEmailEl) profEmailEl.innerText = 'Not logged in';
    const profDematEl = document.getElementById('profilePageDemat');
    if (profDematEl) profDematEl.innerText = 'Demat: GUEST';
    const profWalletBalEl = document.getElementById('profileWalletBalanceDisplay');
    if (profWalletBalEl) profWalletBalEl.innerText = '₹0.00';
    const profBankBalEl = document.getElementById('profileBankBalanceDisplay');
    if (profBankBalEl) profBankBalEl.innerText = '₹0.00';
    return;
  }

  updateNavbarProfile();

  const profBankNameEl = document.getElementById('profileBankNameDisplay');
  const profBankAccEl = document.getElementById('profileBankAccountDisplay');
  const profBankBalEl = document.getElementById('profileBankBalanceDisplay');
  const profWalletBalEl = document.getElementById('profileWalletBalanceDisplay');

  // Immediately populate with current user cached data to prevent any "undefined" flash
  const bName = currentUser.bank_name || 'HDFC Bank';
  const rawAcc = String(currentUser.bank_account || '50100234567890');
  const bMasked = rawAcc.length >= 4 ? `•••• ${rawAcc.slice(-4)}` : rawAcc;
  const bIfsc = currentUser.bank_ifsc || `${bName.split(' ')[0].toUpperCase().slice(0, 4)}0001234`;
  const bBal = currentUser.bank_balance !== undefined ? currentUser.bank_balance : 1000000.0;
  const wBal = currentUser.balance !== undefined ? currentUser.balance : (state.account ? state.account.balance : 0.0);

  if (profBankNameEl) profBankNameEl.innerText = bName;
  if (profBankAccEl) profBankAccEl.innerText = `A/C ${bMasked} • IFSC: ${bIfsc}`;
  if (profBankBalEl) profBankBalEl.innerText = formatINR(bBal);
  if (profWalletBalEl) profWalletBalEl.innerText = formatINR(wBal);

  const data = await loadBankAccountDetails();
  if (data && data.bank_name) {
    const accMasked = data.bank_account_masked || data.bank_masked_account || bMasked;
    const ifsc = data.bank_ifsc || bIfsc;
    const bankBal = data.bank_balance !== undefined ? data.bank_balance : bBal;
    const walletBal = data.balance !== undefined ? data.balance : (data.wallet_balance !== undefined ? data.wallet_balance : wBal);

    if (profBankNameEl) profBankNameEl.innerText = data.bank_name;
    if (profBankAccEl) profBankAccEl.innerText = `A/C ${accMasked} • IFSC: ${ifsc}`;
    if (profBankBalEl) profBankBalEl.innerText = formatINR(bankBal);
    if (profWalletBalEl) profWalletBalEl.innerText = formatINR(walletBal);
  }
}

function copyDematId() {
  const dematEl = document.getElementById('profilePageDemat');
  const text = dematEl ? dematEl.innerText.replace('Demat: ', '') : '';
  if (text && navigator.clipboard) {
    navigator.clipboard.writeText(text);
    showToast(`Copied ${text} to clipboard!`);
  } else {
    showToast('Copied Demat ID!');
  }
}

// =======================================================
// SIMULATED BANK DEPOSIT (BANK -> TRADING WALLET)
// =======================================================
async function openAddMoneyModal() {
  const menu = document.getElementById('userDropdownMenu');
  if (menu) menu.style.display = 'none';

  if (!currentUser || isGuest()) {
    showToast('Please create or log into your account to add funds.', true);
    navigateTo('/onboarding');
    return;
  }

  const modal = document.getElementById('upiAddMoneyModal');
  if (!modal) return;

  // Reset to Step 1
  const stepAmount = document.getElementById('upiStepAmount');
  const stepPin = document.getElementById('upiStepPin');
  const stepSuccess = document.getElementById('upiStepSuccess');
  if (stepAmount) stepAmount.style.display = 'block';
  if (stepPin) stepPin.style.display = 'none';
  if (stepSuccess) stepSuccess.style.display = 'none';

  const amountInput = document.getElementById('upiAddAmountInput');
  if (amountInput) amountInput.value = '50000';
  currentUpiAddAmount = 50000;

  // Immediately bind bank info from currentUser in memory so it NEVER shows wrong bank!
  const bName = document.getElementById('upiSourceBankName');
  const bAcc = document.getElementById('upiSourceBankAcc');
  const bBal = document.getElementById('upiSourceBankBal');
  const userBank = (currentUser && currentUser.bank_name) ? currentUser.bank_name : 'Federal Bank';
  const userAcc = (currentUser && currentUser.bank_account) ? `•••• ${String(currentUser.bank_account).slice(-4)}` : '•••• 8910';
  const userBal = (currentUser && currentUser.bank_balance !== undefined) ? currentUser.bank_balance : 1000000.0;

  if (bName) bName.innerText = userBank;
  if (bAcc) bAcc.innerText = `A/C ${userAcc}`;
  if (bBal) bBal.innerText = formatINR(userBal);

  const btnProceed = document.getElementById('btnProceedToUpiPin') || document.getElementById('btnProceedToPin');
  if (btnProceed) {
    btnProceed.disabled = false;
    btnProceed.innerText = 'Proceed to Enter PIN →';
  }

  modal.classList.add('active');

  // Fetch latest fresh bank details from server
  const bankData = await loadBankAccountDetails();
  if (bankData) {
    if (bName) bName.innerText = bankData.bank_name || userBank;
    if (bAcc) bAcc.innerText = `A/C ${bankData.bank_account_masked || bankData.bank_masked_account || userAcc}`;
    if (bBal) bBal.innerText = formatINR(bankData.bank_balance !== undefined ? bankData.bank_balance : userBal);
  }
  validateUpiAddAmount();
}

function closeAddMoneyModal() {
  const modal = document.getElementById('upiAddMoneyModal');
  if (modal) modal.classList.remove('active');
  resetUpiPinScreen();
}

function backToAmountStep() {
  const stepAmount = document.getElementById('upiStepAmount');
  const stepPin = document.getElementById('upiStepPin');
  if (stepAmount) stepAmount.style.display = 'block';
  if (stepPin) stepPin.style.display = 'none';
  resetUpiPinScreen();
}

function setUpiQuickAmount(amt) {
  const amountInput = document.getElementById('upiAddAmountInput');
  if (amountInput) {
    amountInput.value = amt;
    validateUpiAddAmount();
  }
}

function validateUpiAddAmount() {
  const input = document.getElementById('upiAddAmountInput');
  const btn = document.getElementById('btnProceedToUpiPin') || document.getElementById('btnProceedToPin');
  const errEl = document.getElementById('upiAmountError');
  if (!input || !btn) return;

  const val = parseFloat(input.value || '0');
  currentUpiAddAmount = val;

  const availBank = (cachedBankAccount && cachedBankAccount.bank_balance !== undefined)
    ? cachedBankAccount.bank_balance
    : (currentUser && currentUser.bank_balance !== undefined ? currentUser.bank_balance : 1000000.0);

  if (isNaN(val) || val < 100) {
    btn.disabled = true;
    btn.innerText = 'Enter min. ₹100';
    if (errEl) { errEl.innerText = 'Minimum deposit amount is ₹100'; errEl.style.display = 'block'; }
  } else if (val > availBank) {
    btn.disabled = true;
    btn.innerText = 'Exceeds Available Bank Balance';
    if (errEl) { errEl.innerText = `Amount exceeds available bank balance (${formatINR(availBank)})`; errEl.style.display = 'block'; }
  } else {
    btn.disabled = false;
    btn.innerText = `Proceed to Enter PIN →`;
    if (errEl) errEl.style.display = 'none';
  }
}

function proceedToUpiPinScreen() {
  validateUpiAddAmount();
  const btn = document.getElementById('btnProceedToUpiPin') || document.getElementById('btnProceedToPin');
  if (btn && btn.disabled) return;

  const stepAmount = document.getElementById('upiStepAmount');
  const stepPin = document.getElementById('upiStepPin');
  const stepSuccess = document.getElementById('upiStepSuccess');
  if (stepAmount) stepAmount.style.display = 'none';
  if (stepPin) stepPin.style.display = 'block';
  if (stepSuccess) stepSuccess.style.display = 'none';

  const dispAmt = document.getElementById('upiPinDisplayAmount');
  if (dispAmt) dispAmt.innerText = formatINR(currentUpiAddAmount);

  const dispBank = document.getElementById('upiPinDisplayBank');
  const bankName = (cachedBankAccount && cachedBankAccount.bank_name) || (currentUser && currentUser.bank_name) || 'Federal Bank';
  const rawAcc = (cachedBankAccount && (cachedBankAccount.bank_account_masked || cachedBankAccount.bank_masked_account))
    || (currentUser && currentUser.bank_account ? `•••• ${String(currentUser.bank_account).slice(-4)}` : '•••• 8910');
  if (dispBank) {
    dispBank.innerText = `${bankName} A/C ${rawAcc.startsWith('••••') ? rawAcc : `•••• ${rawAcc.slice(-4)}`}`;
  }

  const execBtn = document.getElementById('btnExecuteUpi');
  if (execBtn) {
    execBtn.disabled = false;
    execBtn.innerText = `✓ Authorize & Transfer ${formatINR(currentUpiAddAmount)}`;
  }

  resetUpiPinScreen();
  setTimeout(() => {
    focusUpiPinInput();
  }, 100);
}

let isTransferringFunds = false;

function resetUpiPinScreen() {
  isTransferringFunds = false;
  enteredUpiPin = '';
  const hidden = document.getElementById('upiHiddenPinInput');
  if (hidden) hidden.value = '';
  updateUpiPinDots();
  const errEl = document.getElementById('upiPinError');
  if (errEl) {
    errEl.innerText = '';
    errEl.style.display = 'none';
  }
  const btn = document.getElementById('btnExecuteUpi');
  if (btn) {
    btn.disabled = false;
    btn.innerText = `✓ Authorize & Transfer ${formatINR(currentUpiAddAmount)}`;
  }
}

function focusUpiPinInput() {
  const hidden = document.getElementById('upiHiddenPinInput');
  if (hidden) {
    hidden.focus();
  }
}

function onUpiPinInput(val) {
  if (isTransferringFunds) return;
  const clean = val.replace(/\D/g, '').slice(0, 4);
  enteredUpiPin = clean;
  updateUpiPinDots();
  if (clean.length === 4) {
    const errEl = document.getElementById('upiPinError');
    if (errEl) errEl.style.display = 'none';
    setTimeout(() => {
      executeUpiPayment();
    }, 200);
  }
}

function pressUpiKey(num) {
  if (isTransferringFunds) return;
  if (enteredUpiPin.length < 4) {
    enteredUpiPin += num;
    updateUpiPinDots();
    const hidden = document.getElementById('upiHiddenPinInput');
    if (hidden) hidden.value = enteredUpiPin;
    if (enteredUpiPin.length === 4) {
      setTimeout(() => {
        executeUpiPayment();
      }, 200);
    }
  }
}

function pressUpiBackspace() {
  if (isTransferringFunds) return;
  if (enteredUpiPin.length > 0) {
    enteredUpiPin = enteredUpiPin.slice(0, -1);
    updateUpiPinDots();
    const hidden = document.getElementById('upiHiddenPinInput');
    if (hidden) hidden.value = enteredUpiPin;
  }
}

function updateUpiPinDots() {
  for (let i = 1; i <= 4; i++) {
    const dot = document.getElementById(`upiDot${i}`);
    if (dot) {
      if (enteredUpiPin.length >= i) {
        dot.classList.add('filled');
      } else {
        dot.classList.remove('filled');
      }
    }
  }
  const errEl = document.getElementById('upiPinError');
  if (errEl) errEl.style.display = 'none';
}

async function executeUpiPayment() {
  if (isTransferringFunds) return;
  if (enteredUpiPin.length !== 4) {
    const errEl = document.getElementById('upiPinError');
    if (errEl) {
      errEl.innerText = "Please enter your 4-digit Security PIN";
      errEl.style.display = 'block';
    }
    return;
  }

  isTransferringFunds = true;
  const btn = document.getElementById('btnExecuteUpi');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="loading-spinner small"></span> Authorizing Transfer...`;
  }

  const uid = (currentUser && currentUser.id) || localStorage.getItem('stoxify_user_id');
  if (!uid) {
    showToast('Please log in or create an account to transfer funds.', true);
    if (btn) {
      btn.disabled = false;
      btn.innerText = `✓ Authorize & Transfer ${formatINR(currentUpiAddAmount)}`;
    }
    isTransferringFunds = false;
    return;
  }

  try {
    const res = await fetch(`/api/funds/upi-add?user_id=${encodeURIComponent(uid)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': uid
      },
      body: JSON.stringify({
        amount: currentUpiAddAmount,
        pin: enteredUpiPin,
        user_id: uid
      })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      if (currentUser) {
        currentUser.balance = data.balance;
        currentUser.bank_balance = data.bank_balance;
        localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
      }
      if (state.account) {
        state.account.balance = data.balance;
        state.account.bank_balance = data.bank_balance;
      }
      if (cachedBankAccount) {
        cachedBankAccount.bank_balance = data.bank_balance;
        cachedBankAccount.balance = data.balance;
        cachedBankAccount.wallet_balance = data.balance;
      }
      updateNavbarProfile();

      // Show Step 3 Success
      const stepAmount = document.getElementById('upiStepAmount');
      const stepPin = document.getElementById('upiStepPin');
      const successStep = document.getElementById('upiStepSuccess');
      if (stepAmount) stepAmount.style.display = 'none';
      if (stepPin) stepPin.style.display = 'none';
      if (successStep) successStep.style.display = 'block';

      const sAmt = document.getElementById('upiSuccessAmount');
      const sRef = document.getElementById('upiSuccessRef');
      const sSrc = document.getElementById('upiSuccessSource');
      const sWBal = document.getElementById('upiSuccessWalletBal');
      const sBBal = document.getElementById('upiSuccessBankBal');

      const bankName = (cachedBankAccount && cachedBankAccount.bank_name) || (currentUser && currentUser.bank_name) || 'HDFC Bank';
      const rawAcc = (cachedBankAccount && (cachedBankAccount.bank_account_masked || cachedBankAccount.bank_masked_account))
        || (currentUser && currentUser.bank_account ? `•••• ${String(currentUser.bank_account).slice(-4)}` : '•••• 4534');
      const actualAcc = rawAcc.startsWith('••••') ? rawAcc : `•••• ${rawAcc.slice(-4)}`;

      if (sAmt) sAmt.innerText = formatINR(data.amount || currentUpiAddAmount);
      const txnRef = data.reference_id || `TXN/STX/${Math.floor(10000000 + Math.random() * 90000000)}`;
      if (sRef) sRef.innerText = txnRef;
      if (sSrc) sSrc.innerText = `${bankName} A/C ${actualAcc}`;
      if (sWBal) sWBal.innerText = formatINR(data.balance);
      if (sBBal) sBBal.innerText = formatINR(data.bank_balance);

      saveLocalBankTx(uid, {
        user_id: uid,
        type: 'BANK_DEPOSIT',
        amount: data.amount || currentUpiAddAmount,
        from_account: `${bankName} ${actualAcc}`,
        to_account: 'Stoxifyin Trading Wallet',
        reference_id: txnRef,
        status: 'SUCCESS',
        note: 'Simulated bank transfer to Stoxifyin trading wallet',
        created_at: new Date().toISOString()
      });

      showToast(`Transferred ${formatINR(data.amount || currentUpiAddAmount)} to trading wallet! ✓`);
      fetchAccount();
      loadBankAccountDetails();
    } else {
      const errEl = document.getElementById('upiPinError');
      if (errEl) {
        errEl.innerText = data.detail || data.message || "Invalid Security PIN. Please try again.";
        errEl.style.display = 'block';
      }
      if (btn) {
        btn.disabled = false;
        btn.innerText = `✓ Authorize & Transfer ${formatINR(currentUpiAddAmount)}`;
      }
      enteredUpiPin = '';
      updateUpiPinDots();
      const hidden = document.getElementById('upiHiddenPinInput');
      if (hidden) hidden.value = '';
    }
  } catch (err) {
    console.error('Transfer error:', err);
    const errEl = document.getElementById('upiPinError');
    if (errEl) {
      errEl.innerText = 'Network error. Please try again.';
      errEl.style.display = 'block';
    }
    if (btn) {
      btn.disabled = false;
      btn.innerText = `✓ Authorize & Transfer ${formatINR(currentUpiAddAmount)}`;
    }
  } finally {
    isTransferringFunds = false;
  }
}

function finishUpiSuccess() {
  closeAddMoneyModal();
  showToast(`${formatINR(currentUpiAddAmount)} credited to trading wallet successfully!`);
  if (state.currentTab === 'holdings') fetchPortfolio();
}

// =======================================================
// WITHDRAWAL ENGINE (TRADING WALLET -> BANK ACCOUNT)
// =======================================================
async function openWithdrawModal() {
  const menu = document.getElementById('userDropdownMenu');
  if (menu) menu.style.display = 'none';

  if (!currentUser || isGuest()) {
    showToast('Please create or log into your account to withdraw funds.', true);
    navigateTo('/onboarding');
    return;
  }

  const modal = document.getElementById('withdrawMoneyModal');
  if (!modal) return;

  const bankData = await loadBankAccountDetails();
  const availCash = (currentUser && currentUser.balance !== undefined) ? currentUser.balance : (state.account ? state.account.balance : 0.0);

  const bName = document.getElementById('wdrBankName');
  const bAcc = document.getElementById('wdrBankAcc');
  const bCash = document.getElementById('wdrAvailCash');
  const amtInput = document.getElementById('wdrAmountInput');
  const pinInput = document.getElementById('wdrPinInput');
  const errEl = document.getElementById('wdrErrorMsg');

  if (bName && bankData) bName.innerText = bankData.bank_name || 'HDFC Bank';
  if (bAcc && bankData) bAcc.innerText = `A/C ${bankData.bank_account_masked || bankData.bank_masked_account || '•••• 5678'}`;
  if (bCash) bCash.innerText = formatINR(availCash);
  if (amtInput) amtInput.value = '';
  if (pinInput) pinInput.value = '';
  if (errEl) {
    errEl.innerText = '';
    errEl.style.display = 'none';
  }

  modal.classList.add('active');
}

function closeWithdrawModal() {
  const modal = document.getElementById('withdrawMoneyModal');
  if (modal) modal.classList.remove('active');
}

async function executeWithdrawal() {
  const amtInput = document.getElementById('wdrAmountInput');
  const pinInput = document.getElementById('wdrPinInput');
  const errEl = document.getElementById('wdrErrorMsg');
  const btn = document.getElementById('btnExecuteWithdraw');

  const amt = parseFloat(amtInput ? amtInput.value : '0');
  const pin = pinInput ? pinInput.value.trim() : '';

  if (isNaN(amt) || amt < 100) {
    if (errEl) {
      errEl.innerText = 'Minimum withdrawal amount is ₹100';
      errEl.style.display = 'block';
    }
    return;
  }

  const availCash = (currentUser && currentUser.balance !== undefined) ? currentUser.balance : 0.0;
  if (amt > availCash) {
    if (errEl) {
      errEl.innerText = 'Insufficient cash in trading wallet to withdraw this amount';
      errEl.style.display = 'block';
    }
    return;
  }

  if (pin.length !== 4) {
    if (errEl) {
      errEl.innerText = "Please enter your 4-digit Stoxifyin' PIN";
      errEl.style.display = 'block';
    }
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="loading-spinner small"></span> Processing Withdrawal...`;
  }

  const uid = (currentUser && currentUser.id) || localStorage.getItem('stoxify_user_id');
  if (!uid) {
    if (errEl) {
      errEl.innerText = 'Please log in or create an account to withdraw funds.';
      errEl.style.display = 'block';
    }
    if (btn) {
      btn.disabled = false;
      btn.innerText = 'Withdraw Funds Now';
    }
    return;
  }

  try {
    const res = await fetch(`/api/funds/withdraw?user_id=${encodeURIComponent(uid)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': uid
      },
      body: JSON.stringify({ amount: amt, pin, user_id: uid })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      if (currentUser) {
        currentUser.balance = data.balance;
        currentUser.bank_balance = data.bank_balance;
        localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
      }
      if (state.account) {
        state.account.balance = data.balance;
        state.account.bank_balance = data.bank_balance;
      }
      if (cachedBankAccount) {
        cachedBankAccount.bank_balance = data.bank_balance;
        cachedBankAccount.balance = data.balance;
        cachedBankAccount.wallet_balance = data.balance;
      }
      const bName = (cachedBankAccount && cachedBankAccount.bank_name) || (currentUser && currentUser.bank_name) || 'HDFC Bank';
      const rawAcc = (cachedBankAccount && (cachedBankAccount.bank_account_masked || cachedBankAccount.bank_masked_account))
        || (currentUser && currentUser.bank_account ? `•••• ${String(currentUser.bank_account).slice(-4)}` : '•••• 4534');
      const actualAcc = rawAcc.startsWith('••••') ? rawAcc : `•••• ${rawAcc.slice(-4)}`;
      const wdrRef = data.reference_id || `WDR/STX/${Math.floor(10000000 + Math.random() * 90000000)}`;

      saveLocalBankTx(uid, {
        user_id: uid,
        type: 'WITHDRAWAL',
        amount: amt,
        from_account: 'Stoxifyin Trading Wallet',
        to_account: `${bName} ${actualAcc}`,
        reference_id: wdrRef,
        status: 'SUCCESS',
        note: 'Simulated withdrawal to linked bank account',
        created_at: new Date().toISOString()
      });

      updateNavbarProfile();
      fetchAccount();
      loadBankAccountDetails();
      closeWithdrawModal();
      showToast(`₹${Number(amt).toLocaleString('en-IN', {minimumFractionDigits: 2})} withdrawn to your bank account successfully!`);
    } else {
      if (errEl) {
        errEl.innerText = data.detail || data.message || 'Withdrawal failed. Check your PIN and balance.';
        errEl.style.display = 'block';
      }
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Withdraw Funds Now';
      }
    }
  } catch (err) {
    console.error('Withdrawal error:', err);
    if (errEl) {
      errEl.innerText = 'Network error. Please try again.';
      errEl.style.display = 'block';
    }
    if (btn) {
      btn.disabled = false;
      btn.innerText = 'Withdraw Funds Now';
    }
  }
}

// =======================================================
// BANK PASSBOOK & STATEMENT ENGINE
// =======================================================
async function openBankPassbookModal() {
  if (!currentUser || isGuest()) {
    showToast('Please log in or create an account to view your bank passbook.', true);
    return;
  }

  const modal = document.getElementById('bankPassbookModal');
  if (!modal) return;
  modal.classList.add('active');

  const titleEl = document.getElementById('pbModalBankTitle');
  const subEl = document.getElementById('pbModalBankSub');
  const balEl = document.getElementById('pbModalBalance');
  const upiEl = document.getElementById('pbModalUpiId');
  const listEl = document.getElementById('pbModalTxList');

  if (listEl) listEl.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Loading transactions...</div>';

  const data = await loadBankAccountDetails();
  if (!data) {
    if (listEl) listEl.innerHTML = '<div style="text-align: center; color: var(--danger-red); padding: 2rem;">Failed to load bank statement.</div>';
    return;
  }

  if (titleEl) titleEl.innerText = `${data.bank_name || 'Bank'} Passbook`;
  const rawAcc = String(data.bank_account || (currentUser && currentUser.bank_account) || '50100234567890');
  const last4 = rawAcc.length >= 4 ? rawAcc.slice(-4) : rawAcc;
  if (subEl) subEl.innerText = `A/C •••• ${last4} • IFSC: ${data.bank_ifsc || 'HDFC0001234'}`;
  if (balEl) balEl.innerText = formatINR(data.bank_balance !== undefined ? data.bank_balance : 1000000.0);
  if (upiEl) upiEl.innerText = `UPI ID: ${data.bank_upi_id || ''}`;

  if (listEl) {
    if (!data.transactions || data.transactions.length === 0) {
      listEl.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No transactions found.</div>';
      return;
    }

    listEl.innerHTML = data.transactions.map(tx => {
      const isCredit = tx.type === 'INITIAL_CREDIT' || tx.type === 'WITHDRAWAL' || tx.type === 'CREDIT';
      const sign = isCredit ? '+' : '-';
      const colorClass = isCredit ? 'text-positive' : 'text-danger';
      const icon = isCredit ? '↓' : '↑';
      const badgeClass = isCredit ? 'credit' : 'debit';
      const desc = tx.note || tx.description || (isCredit ? 'Credit to Bank Account' : 'UPI Transfer to Trading Wallet');
      const safeDate = tx.created_at ? new Date(String(tx.created_at).replace(' ', 'T')) : new Date();
      const dateStr = isNaN(safeDate.getTime()) ? (tx.created_at || 'Recent') : safeDate.toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      return `
        <div class="passbook-tx-item">
          <div class="tx-item-left">
            <div class="tx-badge-icon ${badgeClass}">${icon}</div>
            <div>
              <div style="font-size: 0.88rem; font-weight: 700; color: var(--text-primary);">${desc}</div>
              <div style="font-size: 0.72rem; color: var(--text-muted);">${dateStr} • Ref: ${tx.reference_id || 'N/A'}</div>
            </div>
          </div>
          <div style="text-align: right;">
            <div class="${colorClass}" style="font-size: 0.95rem; font-weight: 800;">${sign}${formatINR(tx.amount)}</div>
            <div style="font-size: 0.72rem; color: var(--text-muted);">${tx.status || 'SUCCESS'}</div>
          </div>
        </div>
      `;
    }).join('');
  }
}

function closeBankPassbookModal() {
  const modal = document.getElementById('bankPassbookModal');
  if (modal) modal.classList.remove('active');
}

// --- User Authentication & Login Modal ---
async function openLoginModal(prefilledIdentifier) {
  const overlay = document.getElementById('loginModalOverlay');
  if (!overlay) return;

  const identInput = document.getElementById('loginIdentifierInput');
  const pinInput = document.getElementById('loginPinInput');
  if (identInput) identInput.value = prefilledIdentifier || '';
  if (pinInput) pinInput.value = '';

  overlay.classList.add('active');
  try {
    localStorage.removeItem('stoxify_recent_accounts');
  } catch (e) {}

  setTimeout(() => {
    if (identInput && !identInput.value) {
      identInput.focus();
    } else if (pinInput) {
      pinInput.focus();
    }
  }, 120);
}

function closeLoginModal() {
  const overlay = document.getElementById('loginModalOverlay');
  if (overlay) overlay.classList.remove('active');
}

function saveRecentAccount(u) {}
function loadSavedLoginAccounts() {}
function selectLoginAccount(id, name, email) {}

async function submitLogin() {
  const identInput = document.getElementById('loginIdentifierInput');
  const pinInput = document.getElementById('loginPinInput');
  const btn = document.getElementById('btnLoginSubmit');

  const identifier = identInput ? identInput.value.trim() : '';
  const pin = pinInput ? pinInput.value.trim() : '';

  if (!identifier) {
    showToast('Please enter your Username, Email Address or Phone Number', true);
    if (identInput) identInput.focus();
    return;
  }

  if (!pin) {
    showToast('Please enter your Password or 4-digit PIN', true);
    if (pinInput) pinInput.focus();
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Logging in...';
  }

  try {
    const res = await fetch('/api/user/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, pin, password: pin })
    });
    const data = await res.json();

    if (!res.ok || !data.success) {
      showToast(data.detail || 'Login failed. Please check your credentials.', true);
      return;
    }

    currentUser = data.user;
    localStorage.removeItem('stoxify_guest_mode');
    localStorage.setItem('stoxify_user_id', currentUser.id);
    localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
    document.documentElement.classList.add('user-logged-in');
    document.documentElement.classList.remove('user-guest');

    updateNavbarProfile();
    saveRecentAccount(currentUser);
    closeLoginModal();
    showToast(`Welcome back, ${currentUser.name}!`);

    await fetchAccount();
    await fetchWatchlist();
    if (state.currentTab === 'holdings') fetchPortfolio();
    if (state.currentTab === 'positions') fetchPositions();
    if (state.currentTab === 'orders') fetchOrders();

    if (window.location.pathname === '/onboarding' || window.location.pathname === '/login') {
      navigateTo('/explore');
    }
  } catch (err) {
    console.error('Login error:', err);
    showToast('Failed to connect during login', true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = 'Log In →';
    }
  }
}


/* =======================================================
   DEDICATED FULL-PAGE ASSET VIEW ENGINE
   ======================================================= */
let pageChartInstance = null;
let currentPageAsset = null;
let pageOrderState = {
  action: 'BUY',
  product: 'DELIVERY',
  variety: 'MARKET',
  quantity: 1,
  limitPrice: 0.0
};

async function showAssetPage(symbol, assetType = 'STOCK') {
  // Always fetch fresh account balance to keep trade card available cash accurate
  fetchAccount().catch(() => {});

  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-links .nav-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  
  const pagePane = document.getElementById('pane-asset-detail');
  if (pagePane) pagePane.classList.add('active');
  document.body.classList.remove('viewing-profile');
  document.documentElement.classList.remove('viewing-profile');
  document.body.classList.add('viewing-asset-detail');
  document.documentElement.classList.add('viewing-asset-detail');
  window.scrollTo(0, 0);

  const cleanSymInit = (symbol || '').replace('.NS', '').replace('.BO', '');
  const isMFInit = assetType === 'MUTUAL_FUND' || symbol.match(/^\d+$/);
  const isIndexInit = (symbol || '').startsWith('^') || assetType === 'INDEX';
  const indexNameInit = isIndexInit ? (INDEX_NAMES[symbol] || symbol.replace('^', '')) : null;

  document.getElementById('assetBreadcrumbCategory').innerText = isIndexInit ? 'Indices' : (isMFInit ? 'Mutual Funds' : 'Stocks');
  document.getElementById('pageAssetSymbol').innerText = isIndexInit ? (INDEX_NAMES[symbol] || cleanSymInit) : cleanSymInit;
  const dSymInit = document.getElementById('drawerAssetSymbol');
  if (dSymInit) dSymInit.innerText = isIndexInit ? (INDEX_NAMES[symbol] || cleanSymInit) : cleanSymInit;

  const knownInit = (state.exploreData && state.exploreData.all_stocks)
    ? state.exploreData.all_stocks.find(s => (s.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === cleanSymInit.toUpperCase())
    : null;
  if (knownInit) {
    document.getElementById('assetBreadcrumbName').innerText = knownInit.name;
    document.getElementById('pageAssetTitle').innerText = knownInit.name;
    document.getElementById('pageAssetPrice').innerText = formatINR(knownInit.price);
    const dTitle = document.getElementById('drawerAssetTitle');
    if (dTitle) dTitle.innerText = knownInit.name;
    const dPrice = document.getElementById('drawerAssetPrice');
    if (dPrice) dPrice.innerText = formatINR(knownInit.price);
  }

  try {
    const res = await fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}&asset_type=${encodeURIComponent(assetType)}`);
    const data = await res.json();
    currentPageAsset = data;
    state.currentModalAsset = data;

    const isIndex = (data.symbol || '').startsWith('^') || assetType === 'INDEX';
    const indexName = isIndex ? (INDEX_NAMES[data.symbol] || data.name || data.symbol.replace('^', '')) : null;
    const cleanSym = isIndex ? (INDEX_NAMES[data.symbol] || data.symbol.replace('^', '')) : (data.symbol || '').replace('.NS', '').replace('.BO', '');
    const isMF = data.asset_type === 'MUTUAL_FUND';
    if (!isIndex) {
      recordRecentlyViewed(data, isMF ? 'MUTUAL_FUND' : 'STOCK');
    }
    
    document.getElementById('assetBreadcrumbCategory').innerText = isIndex ? 'Indices' : (isMF ? 'Mutual Funds' : 'Stocks');
    document.getElementById('assetBreadcrumbName').innerText = isIndex ? indexName : data.name;

    document.getElementById('pageAssetAvatar').innerHTML = renderAssetAvatar(data, isIndex ? 'INDEX' : data.asset_type);
    document.getElementById('pageAssetTitle').innerText = isIndex ? indexName : data.name;
    document.getElementById('pageAssetSymbol').innerText = isIndex ? (INDEX_NAMES[data.symbol] || cleanSym) : cleanSym;
    document.getElementById('pageAssetBadge').innerText = isIndex ? 'INDEX' : (isMF ? 'Mutual Fund' : (data.exchange || 'NSE'));
    document.getElementById('pageAssetSector').innerText = isIndex ? 'Market Index' : (data.sector || (isMF ? data.category || 'Direct Plan' : 'Equities'));
    document.getElementById('pageAssetPrice').innerText = formatINR(data.price);

    const isPos = data.change >= 0;
    const badgeEl = document.getElementById('pageAssetChangeBadge');
    badgeEl.className = isPos ? 'badge-positive' : 'badge-negative';
    badgeEl.innerText = formatChange(data.change, data.change_pct);

    // Sync mobile slide-up drawer header
    const dAvatar = document.getElementById('drawerAssetAvatar');
    if (dAvatar) dAvatar.innerHTML = renderAssetAvatar(data, isIndex ? 'INDEX' : data.asset_type);
    const dTitle = document.getElementById('drawerAssetTitle');
    if (dTitle) dTitle.innerText = isIndex ? indexName : data.name;
    const dSym = document.getElementById('drawerAssetSymbol');
    if (dSym) dSym.innerText = isIndex ? (INDEX_NAMES[data.symbol] || cleanSym) : cleanSym;
    const dPrice = document.getElementById('drawerAssetPrice');
    if (dPrice) dPrice.innerText = formatINR(data.price);
    const dChg = document.getElementById('drawerAssetChange');
    if (dChg) {
      dChg.className = isPos ? 'badge-positive' : 'badge-negative';
      dChg.innerText = formatChange(data.change, data.change_pct);
    }

    updatePageAssetStar(data.symbol);
    const starBtn = document.getElementById('pageAssetStarBtn');
    if (starBtn) {
      starBtn.onclick = async () => {
        await toggleWatchlistItem(data.symbol, isIndex ? indexName : data.name, isIndex ? 'STOCK' : data.asset_type);
        updatePageAssetStar(data.symbol);
      };
    }

    const low = data.day_low ?? data.low ?? (data.price * 0.985);
    const high = data.day_high ?? data.high ?? (data.price * 1.015);
    const w52Low = data.fifty_two_week_low ?? data.low_52w ?? (data.price * 0.75);
    const w52High = data.fifty_two_week_high ?? data.high_52w ?? (data.price * 1.35);
    const openPrice = data.open ?? data.prev_close ?? data.price;
    const prevClose = data.previous_close ?? data.prev_close ?? (data.price - (data.change || 0));

    document.getElementById('perfTodayLow').innerText = formatINR(low);
    document.getElementById('perfTodayHigh').innerText = formatINR(high);
    document.getElementById('perf52wLow').innerText = formatINR(w52Low);
    document.getElementById('perf52wHigh').innerText = formatINR(w52High);
    document.getElementById('perfOpen').innerText = formatINR(openPrice);
    document.getElementById('perfPrevClose').innerText = formatINR(prevClose);
    document.getElementById('perfVolume').innerText = data.volume ? Number(data.volume).toLocaleString('en-IN') : '—';
    // Circuit limits are 10% below/above Previous Close in NSE standard circuit bands
    const lowerCircuit = prevClose ? prevClose * 0.90 : data.price * 0.90;
    const upperCircuit = prevClose ? prevClose * 1.10 : data.price * 1.10;
    document.getElementById('perfLowerCircuit').innerText = formatINR(lowerCircuit);
    document.getElementById('perfUpperCircuit').innerText = formatINR(upperCircuit);

    const todayPct = high > low ? Math.max(5, Math.min(95, ((data.price - low) / (high - low)) * 100)) : 50;
    document.getElementById('perfTodayMarker').style.left = `${todayPct}%`;
    const w52Pct = w52High > w52Low ? Math.max(5, Math.min(95, ((data.price - w52Low) / (w52High - w52Low)) * 100)) : 50;
    document.getElementById('perf52wMarker').style.left = `${w52Pct}%`;

    fetchPageMarketDepth(data.symbol);
    renderPageFundamentals(data);

    document.getElementById('pageAboutTitle').innerText = data.name;
    document.getElementById('pageAboutText').innerText = data.description || `${data.name} is a leading Indian security actively traded on the National Stock Exchange (NSE).`;

    pageOrderState.quantity = 1;
    document.getElementById('pageOrderQuantity').value = 1;
    document.getElementById('pageOrderLimitPrice').value = data.price;
    setPageOrderAction('BUY');
    setPageProductType('DELIVERY');
    setPageOrderVariety('MARKET');
    updatePageAvailableHolding(data.symbol);
    recalcPageMargin();

    // Check if preselect action was requested (e.g. from Sell button on Holdings)
    const preselect = sessionStorage.getItem('stoxify_preselect_action');
    let holdingSale = null;
    try {
      holdingSale = JSON.parse(sessionStorage.getItem('stoxify_holding_sale') || 'null');
    } catch (_) {}
    sessionStorage.removeItem('stoxify_holding_sale');
    if (preselect) {
      sessionStorage.removeItem('stoxify_preselect_action');
      setPageOrderAction(preselect);
      if (preselect === 'SELL') {
        const cleanSym = (data.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase();
        if (holdingSale && holdingSale.symbol === cleanSym && holdingSale.quantity > 0) {
          setPageProductType('DELIVERY');
          setPageQuickQuantity(holdingSale.quantity);
          updatePageAvailableHolding(data.symbol);
          if (window.innerWidth <= 768) {
            openMobileTradeDrawer('SELL');
          }
        } else {
          Promise.all([
            fetch('/api/portfolio').then(r => r.json()).catch(() => ({})),
            fetch('/api/positions').then(r => r.json()).catch(() => ({}))
          ]).then(([pData, posData]) => {
            const holding = (pData.holdings || []).find(h => (h.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === cleanSym);
            const pos = (posData.positions || []).find(p => (p.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === cleanSym);
            if (holding && holding.quantity > 0) {
              setPageProductType('DELIVERY');
              setPageQuickQuantity(holding.quantity);
            } else if (pos && pos.quantity > 0) {
              setPageProductType('INTRADAY');
              setPageQuickQuantity(pos.quantity);
            }
            updatePageAvailableHolding(data.symbol);
            if (window.innerWidth <= 768) {
              openMobileTradeDrawer('SELL');
            }
          }).catch(() => {});
        }
      }
    }

    // Toggle mobile sticky action bar (hide for market indices since they are non-tradable)
    const mobBar = document.getElementById('assetMobileActionBar');
    if (mobBar) mobBar.style.display = isIndex ? 'none' : '';

    // Configure Mutual Fund SIP calculator vs Stock fundamentals tabs
    const sipSec = document.getElementById('pageSipCalcSection');
    const tabFin = document.getElementById('tab-asset-financials');
    const tabSh = document.getElementById('tab-asset-shareholding');
    const tabPeers = document.getElementById('tab-asset-peers');
    if (sipSec) sipSec.style.display = isMF ? 'block' : 'none';
    if (tabFin) tabFin.style.display = isMF ? 'none' : 'inline-block';
    if (tabSh) tabSh.style.display = isMF ? 'none' : 'inline-block';
    if (tabPeers) tabPeers.style.display = isMF ? 'none' : 'inline-block';

    const chartToggle = document.querySelector('.chart-type-toggle');
    const emaBtn20 = document.getElementById('btnEma20');
    const emaBtn50 = document.getElementById('btnEma50');
    if (chartToggle) chartToggle.style.display = isMF ? 'none' : 'flex';
    if (emaBtn20) emaBtn20.style.display = isMF ? 'none' : 'inline-block';
    if (emaBtn50) emaBtn50.style.display = isMF ? 'none' : 'inline-block';
    if (isMF && currentChartType === 'candle') {
      currentChartType = 'line';
      const lineBtn = document.getElementById('btnChartLine');
      const candleBtn = document.getElementById('btnChartCandle');
      if (lineBtn) lineBtn.classList.add('active');
      if (candleBtn) candleBtn.classList.remove('active');
    }

    if (isMF) onSipSliderChange();
    switchAssetPageTab('overview');

    loadPageChartTimeframe('1D');

  } catch (err) {
    console.error('Failed to load asset page:', err);
    showToast('Failed to load asset details', true);
  }
}

function updatePageAssetStar(symbol) {
  const btn = document.getElementById('pageAssetStarBtn');
  if (!btn) return;
  const inWatchlist = state.watchlist && state.watchlist.has(symbol);
  if (inWatchlist) {
    btn.classList.add('active');
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="#F59E0B" stroke="#F59E0B" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>';
  } else {
    btn.classList.remove('active');
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>';
  }
}

async function fetchPageMarketDepth(symbol) {
  try {
    const res = await fetch(`/api/depth?symbol=${encodeURIComponent(symbol)}`);
    const d = await res.json();
    const buyBar = document.getElementById('pageDepthBuyBar');
    const sellBar = document.getElementById('pageDepthSellBar');
    if (buyBar && sellBar) {
      buyBar.style.width = `${d.buy_pct}%`;
      buyBar.innerText = `${d.buy_pct}% Buyers`;
      sellBar.style.width = `${d.sell_pct}%`;
      sellBar.innerText = `${d.sell_pct}% Sellers`;
    }

    const bidsEl = document.getElementById('pageDepthBids');
    const asksEl = document.getElementById('pageDepthAsks');
    if (bidsEl) {
      bidsEl.innerHTML = (d.bids || []).map(b => `
        <div class="depth-row bid">
          <span>${b.orders}</span><span>${b.quantity}</span><strong class="price">${formatINR(b.price)}</strong>
        </div>
      `).join('');
    }
    if (asksEl) {
      asksEl.innerHTML = (d.asks || []).map(a => `
        <div class="depth-row ask">
          <strong class="price">${formatINR(a.price)}</strong><span>${a.quantity}</span><span>${a.orders}</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load depth:', err);
  }
}

function renderPageFundamentals(data) {
  const grid = document.getElementById('pageFundamentalsGrid');
  if (!grid) return;
  if (data.asset_type === 'MUTUAL_FUND') {
    grid.innerHTML = `
      <div class="fundamental-item"><span class="f-name">NAV</span><strong class="f-val">${formatINR(data.price)}</strong></div>
      <div class="fundamental-item"><span class="f-name">Fund Category</span><strong class="f-val">${data.category || 'Flexi Cap'}</strong></div>
      <div class="fundamental-item"><span class="f-name">AUM (Fund Size)</span><strong class="f-val">${data.aum || '₹72,400 Cr'}</strong></div>
      <div class="fundamental-item"><span class="f-name">Expense Ratio</span><strong class="f-val">${data.expense_ratio ? data.expense_ratio + '%' : '0.62%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">1Y Return</span><strong class="f-val text-positive">${data.return_1y ? '+' + data.return_1y + '%' : '+18.4%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">3Y Return (CAGR)</span><strong class="f-val text-positive">${data.return_3y ? '+' + data.return_3y + '%' : '+24.1%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">Risk Rating</span><strong class="f-val">Very High</strong></div>
      <div class="fundamental-item"><span class="f-name">Fund Manager</span><strong class="f-val">${data.fund_manager || 'Rajeev Thakkar'}</strong></div>
    `;
  } else {
    const pe = (data.pe_ratio !== undefined && data.pe_ratio !== null) ? data.pe_ratio : '—';
    const pb = (data.pb_ratio !== undefined && data.pb_ratio !== null) ? data.pb_ratio : '—';
    const indPe = data.industry_pe || (data.pe_ratio ? (data.pe_ratio * 0.94).toFixed(2) : '—');
    const d2e = (data.debt_to_equity !== undefined && data.debt_to_equity !== null) ? data.debt_to_equity : '—';
    const roe = (data.roe !== undefined && data.roe !== null) ? data.roe + '%' : '—';
    const eps = (data.eps !== undefined && data.eps !== null) ? '₹' + data.eps : '—';
    const divYield = (data.dividend_yield !== undefined && data.dividend_yield !== null)
      ? data.dividend_yield + '%'
      : (data.div_yield ? data.div_yield + '%' : '0.00%');

    grid.innerHTML = `
      <div class="fundamental-item"><span class="f-name">Market Cap</span><strong class="f-val">${formatMarketCap(data.market_cap)}</strong></div>
      <div class="fundamental-item"><span class="f-name">P/E Ratio</span><strong class="f-val">${pe}</strong></div>
      <div class="fundamental-item"><span class="f-name">P/B Ratio</span><strong class="f-val">${pb}</strong></div>
      <div class="fundamental-item"><span class="f-name">Industry P/E</span><strong class="f-val">${indPe}</strong></div>
      <div class="fundamental-item"><span class="f-name">Debt to Equity</span><strong class="f-val">${d2e}</strong></div>
      <div class="fundamental-item"><span class="f-name">ROE</span><strong class="f-val">${roe}</strong></div>
      <div class="fundamental-item"><span class="f-name">EPS (TTM)</span><strong class="f-val">${eps}</strong></div>
      <div class="fundamental-item"><span class="f-name">Dividend Yield</span><strong class="f-val">${divYield}</strong></div>
    `;
  }
}

let currentChartType = 'line';
const activeEmas = new Set();
let currentChartPoints = [];
let currentChartRange = '1D';

function setChartType(type) {
  currentChartType = type;
  const lineBtn = document.getElementById('btnChartLine');
  const candleBtn = document.getElementById('btnChartCandle');
  if (lineBtn) lineBtn.classList.toggle('active', type === 'line');
  if (candleBtn) candleBtn.classList.toggle('active', type === 'candle');
  renderCurrentChart();
}

function toggleEma(period) {
  const btn = document.getElementById(`btnEma${period}`);
  if (activeEmas.has(period)) {
    activeEmas.delete(period);
    if (btn) btn.classList.remove('active');
  } else {
    activeEmas.add(period);
    if (btn) btn.classList.add('active');
  }
  renderCurrentChart();
}

function calculateEMA(prices, period) {
  const k = 2 / (period + 1);
  const ema = [];
  if (!prices || prices.length === 0) return ema;

  let prevEma = prices[0];
  ema.push(prevEma);

  for (let i = 1; i < prices.length; i++) {
    const cur = prices[i] * k + prevEma * (1 - k);
    ema.push(cur);
    prevEma = cur;
  }
  return ema;
}

let candleState = null;

function getActiveTimeframeChange() {
  if (!currentPageAsset) return { diff: 0, diffPct: 0, isPos: true, text: '+0.00 (+0.00%)' };

  if (currentChartRange === '1D' || !currentChartPoints || currentChartPoints.length === 0) {
    const diff = currentPageAsset.change || 0;
    const diffPct = currentPageAsset.change_pct || 0;
    return {
      diff,
      diffPct,
      isPos: diff >= 0,
      text: formatChange(diff, diffPct)
    };
  }

  const firstP = currentChartPoints[0];
  const baseline = (firstP.open !== undefined ? firstP.open : (firstP.close !== undefined ? firstP.close : (firstP.price !== undefined ? firstP.price : firstP.value))) || (currentPageAsset.price - (currentPageAsset.change || 0));
  const diff = currentPageAsset.price - baseline;
  const diffPct = baseline ? (diff / baseline) * 100 : 0;
  return {
    diff,
    diffPct,
    isPos: diff >= 0,
    text: formatChange(diff, diffPct)
  };
}

function updateHeroPriceForPoint(p) {
  // Main stock price header remains rock-solid at live LTP and never varies when touching the chart.
  // The touched point's price and timestamp are rendered directly on the graph's floating badge.
  return;
}

function resetHeroPrice() {
  if (!currentPageAsset) return;
  const priceEl = document.getElementById('pageAssetPrice');
  const badgeEl = document.getElementById('pageAssetChangeBadge');
  const drawerPriceEl = document.getElementById('drawerAssetPrice');
  const drawerBadgeEl = document.getElementById('drawerAssetChange');

  if (priceEl) priceEl.innerText = formatINR(currentPageAsset.price);
  if (drawerPriceEl) drawerPriceEl.innerText = formatINR(currentPageAsset.price);

  const tfData = getActiveTimeframeChange();
  if (badgeEl) {
    badgeEl.className = tfData.isPos ? 'badge-positive' : 'badge-negative';
    badgeEl.innerText = tfData.text;
  }
  if (drawerBadgeEl) {
    drawerBadgeEl.className = tfData.isPos ? 'badge-positive' : 'badge-negative';
    drawerBadgeEl.innerText = tfData.text;
  }
}

function renderCandlestickCanvas(canvas, points, hoveredIdx = -1, crosshairY = -1) {
  const ctx = canvas.getContext('2d');
  const isMobile = window.innerWidth <= 768;
  const parentW = canvas.parentElement ? canvas.parentElement.clientWidth : 0;
  const fallbackW = isMobile ? Math.min(window.innerWidth - 30, 420) : 800;
  const cssWidth = parentW > 50 ? parentW : fallbackW;
  const cssHeight = isMobile ? 255 : 380;
  const dpr = window.devicePixelRatio || 1;

  canvas.width = Math.round(cssWidth * dpr);
  canvas.height = Math.round(cssHeight * dpr);
  canvas.style.width = cssWidth + 'px';
  canvas.style.height = cssHeight + 'px';

  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  if (!points || points.length === 0) {
    ctx.restore();
    return;
  }

  const paddingLeft = isMobile ? 4 : 16;
  const paddingRight = isMobile ? 4 : 72;
  const paddingTop = 15;
  const paddingBottom = isMobile ? 6 : 26;
  const chartWidth = cssWidth - paddingLeft - paddingRight;
  const chartHeight = cssHeight - paddingTop - paddingBottom;

  // Compute OHLC for each point
  const ohlc = points.map((p, idx) => {
    const close = (p.price !== undefined ? p.price : p.value) || 100;
    const prevClose = idx > 0 ? ((points[idx - 1].price !== undefined ? points[idx - 1].price : points[idx - 1].value) || close) : close;
    const open = p.open || prevClose;
    const high = p.high || Math.max(open, close) * 1.002;
    const low = p.low || Math.min(open, close) * 0.998;
    const vol = p.volume || 10000;
    return { time: p.time, open, high, low, close, volume: vol };
  });

  const minPrice = Math.min(...ohlc.map(p => p.low)) * 0.998;
  const maxPrice = Math.max(...ohlc.map(p => p.high)) * 1.002;
  const priceRange = maxPrice - minPrice || 1;

  // Dedicated volume sub-pane at bottom 18% of chart, keeping price candles strictly above
  const volumeHeight = Math.round(chartHeight * 0.18);
  const pricePlotHeight = chartHeight - volumeHeight - 10;

  const getY = (val) => paddingTop + pricePlotHeight - ((val - minPrice) / priceRange) * pricePlotHeight;

  // Store layout state for interactive touch & mouse scrubbing
  candleState = {
    ohlc,
    paddingLeft,
    paddingRight,
    paddingTop,
    chartWidth,
    chartHeight,
    pricePlotHeight,
    volumeHeight,
    minPrice,
    maxPrice,
    priceRange,
    candleSlot: chartWidth / ohlc.length,
    cssWidth,
    cssHeight,
    getY
  };

  // Background Grid Lines & Y-Axis Labels
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  const gridSteps = 4;
  for (let i = 0; i <= gridSteps; i++) {
    const y = paddingTop + (pricePlotHeight / gridSteps) * i;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(cssWidth - paddingRight, y);
    ctx.stroke();

    if (!isMobile) {
      const priceAtGrid = maxPrice - (priceRange / gridSteps) * i;
      ctx.fillStyle = '#64748B';
      ctx.font = '10px Sora, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(formatINR(priceAtGrid), cssWidth - paddingRight + 6, y + 3);
    }
  }

  const n = ohlc.length;
  const candleSlot = chartWidth / n;
  let candleBodyWidth;
  if (candleSlot < 3) {
    candleBodyWidth = Math.max(1, candleSlot - 0.5);
  } else {
    candleBodyWidth = Math.max(2, Math.min(14, candleSlot * 0.68));
  }

  const maxVol = Math.max(...ohlc.map(p => p.volume)) || 1;

  // Draw Candlesticks and Volume
  ohlc.forEach((bar, i) => {
    const x = paddingLeft + i * candleSlot + candleSlot / 2;
    const isBull = bar.close >= bar.open;
    const color = isBull ? '#00D09C' : '#EB5B3C';

    // 1. Volume Bar (Separated in bottom sub-pane)
    const volH = Math.max(2, (bar.volume / maxVol) * volumeHeight);
    ctx.fillStyle = isBull ? 'rgba(0, 208, 156, 0.22)' : 'rgba(235, 91, 60, 0.22)';
    ctx.fillRect(x - candleBodyWidth / 2, paddingTop + chartHeight - volH, candleBodyWidth, volH);

    // 2. Wick
    ctx.strokeStyle = color;
    ctx.lineWidth = candleSlot < 3 ? 0.8 : 1.2;
    ctx.beginPath();
    ctx.moveTo(x, getY(bar.high));
    ctx.lineTo(x, getY(bar.low));
    ctx.stroke();

    // 3. Body
    const yOpen = getY(bar.open);
    const yClose = getY(bar.close);
    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(1.5, Math.abs(yClose - yOpen));

    ctx.fillStyle = color;
    ctx.fillRect(x - candleBodyWidth / 2, bodyTop, candleBodyWidth, bodyHeight);
  });

  // Overlay EMAs
  const closePrices = ohlc.map(b => b.close);
  if (activeEmas.has(20)) {
    const ema20 = calculateEMA(closePrices, 20);
    ctx.strokeStyle = '#F59E0B';
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ema20.forEach((val, i) => {
      const x = paddingLeft + i * candleSlot + candleSlot / 2;
      const y = getY(val);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  if (activeEmas.has(50)) {
    const ema50 = calculateEMA(closePrices, 50);
    ctx.strokeStyle = '#8B5CF6';
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ema50.forEach((val, i) => {
      const x = paddingLeft + i * candleSlot + candleSlot / 2;
      const y = getY(val);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // Time Axis Labels (Evenly spaced on desktop, hidden on mobile for clean full-height chart)
  if (!isMobile) {
    ctx.fillStyle = '#64748B';
    ctx.font = '10px Sora, sans-serif';
    const labelCount = 6;
    const step = Math.max(1, Math.floor(n / labelCount));
    for (let i = 0; i < n; i += step) {
      const x = paddingLeft + i * candleSlot + candleSlot / 2;
      if (i === 0) {
        ctx.textAlign = 'left';
        ctx.fillText(ohlc[i].time, paddingLeft, cssHeight - 8);
      } else if (i + step >= n) {
        ctx.textAlign = 'right';
        ctx.fillText(ohlc[i].time, paddingLeft + chartWidth, cssHeight - 8);
      } else {
        ctx.textAlign = 'center';
        ctx.fillText(ohlc[i].time, x, cssHeight - 8);
      }
    }
  }

  // Crosshair overlay if scrubbing
  if (hoveredIdx >= 0 && hoveredIdx < n) {
    const target = ohlc[hoveredIdx];
    const crossX = paddingLeft + hoveredIdx * candleSlot + candleSlot / 2;
    const targetY = getY(target.close);

    ctx.strokeStyle = 'rgba(148, 163, 184, 0.45)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // Vertical line
    ctx.beginPath();
    ctx.moveTo(crossX, paddingTop);
    ctx.lineTo(crossX, paddingTop + chartHeight);
    ctx.stroke();

    // Horizontal line
    ctx.beginPath();
    ctx.moveTo(paddingLeft, targetY);
    ctx.lineTo(cssWidth - paddingRight, targetY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Price badge on right axis (desktop only)
    if (!isMobile) {
      const badgeW = 62;
      ctx.fillStyle = '#1E293B';
      ctx.fillRect(cssWidth - paddingRight, targetY - 9, badgeW, 18);
      ctx.strokeStyle = '#38BDF8';
      ctx.strokeRect(cssWidth - paddingRight, targetY - 9, badgeW, 18);
      ctx.fillStyle = '#F8FAFC';
      ctx.font = '10px Sora, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(formatINR(target.close), cssWidth - paddingRight + badgeW / 2, targetY + 3.5);
    }
  }

  ctx.restore();
}

function initChartScrubbing() {
  const canvas = document.getElementById('pageAssetChartCanvas');
  if (!canvas || canvas.dataset.scrubAttached) return;
  canvas.dataset.scrubAttached = 'true';

  function handleTouchScrub(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;

    if (currentChartType === 'candle') {
      if (!candleState) return;
      const idx = Math.floor((x - candleState.paddingLeft) / candleState.candleSlot);
      if (idx >= 0 && idx < candleState.ohlc.length) {
        renderCandlestickCanvas(canvas, currentChartPoints, idx, y);
      }
    } else if (currentChartType === 'line' && pageChartInstance) {
      const chart = pageChartInstance;
      if (!chart.chartArea || !currentChartPoints || currentChartPoints.length === 0) return;

      const area = chart.chartArea;
      const clampedX = Math.max(area.left, Math.min(area.right, x));
      const ratio = (clampedX - area.left) / Math.max(1, area.right - area.left);
      const idx = Math.max(0, Math.min(currentChartPoints.length - 1, Math.round(ratio * (currentChartPoints.length - 1))));

      if (currentChartPoints[idx]) {
        chart.setActiveElements([{ datasetIndex: 0, index: idx }]);
        chart.update('none');
      }
    }
  }

  function handleTouchEnd() {
    if (currentChartType === 'candle') {
      renderCandlestickCanvas(canvas, currentChartPoints);
    } else if (currentChartType === 'line' && pageChartInstance) {
      pageChartInstance.setActiveElements([]);
      pageChartInstance.update('none');
    }
    resetHeroPrice();
  }

  // Smooth touch scrubbing for mobile devices
  canvas.addEventListener('touchstart', (e) => {
    if (e.touches && e.touches.length > 0) handleTouchScrub(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  canvas.addEventListener('touchmove', (e) => {
    if (e.touches && e.touches.length > 0) handleTouchScrub(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  canvas.addEventListener('touchend', handleTouchEnd);
  canvas.addEventListener('touchcancel', handleTouchEnd);

  // Desktop candlestick canvas hover (Chart.js handles line chart mouse hover natively with 0 lag/glitch)
  canvas.addEventListener('mousemove', (e) => {
    if (currentChartType === 'candle') {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      if (candleState) {
        const idx = Math.floor((x - candleState.paddingLeft) / candleState.candleSlot);
        if (idx >= 0 && idx < candleState.ohlc.length) {
          renderCandlestickCanvas(canvas, currentChartPoints, idx, y);
        }
      }
    }
  });
  canvas.addEventListener('mouseleave', () => {
    if (currentChartType === 'candle') {
      renderCandlestickCanvas(canvas, currentChartPoints);
      resetHeroPrice();
    }
  });
}

function renderCurrentChart() {
  const canvas = document.getElementById('pageAssetChartCanvas');
  if (!canvas || !currentChartPoints || currentChartPoints.length === 0) return;

  initChartScrubbing();

  if (currentChartType === 'candle') {
    if (pageChartInstance) {
      pageChartInstance.destroy();
      pageChartInstance = null;
    }
    renderCandlestickCanvas(canvas, currentChartPoints);
  } else {
    // Reset canvas attributes so Chart.js can mount cleanly
    canvas.removeAttribute('width');
    canvas.removeAttribute('height');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    renderLineChartWithChartJs(canvas, currentChartPoints);
  }
}

function renderLineChartWithChartJs(canvas, points) {
  const ctx = canvas.getContext('2d');

  if (pageChartInstance) {
    pageChartInstance.destroy();
    pageChartInstance = null;
  }

  const prices = points.map(p => (p.price !== undefined ? p.price : p.value) || 0);
  const firstVal = prices[0] || 0;
  const lastVal = prices[prices.length - 1] || 0;

  // Accurately determine trend: 1D compares against prev_close; multi-day compares against first point
  let isPos;
  if (currentChartRange === '1D' && currentPageAsset && currentPageAsset.change !== undefined) {
    isPos = currentPageAsset.change >= 0;
  } else {
    isPos = lastVal >= firstVal;
  }

  const isMobile = window.innerWidth <= 768;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const strokeColor = isPos ? '#00D09C' : '#EB5B3C';
  const chartHeight = canvas.clientHeight || (isMobile ? 255 : 380);

  // Triple-stop radiant luminous gradient (clean fade, zero muddiness)
  const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
  gradient.addColorStop(0, isPos ? 'rgba(0, 208, 156, 0.20)' : 'rgba(235, 91, 60, 0.20)');
  gradient.addColorStop(0.5, isPos ? 'rgba(0, 208, 156, 0.05)' : 'rgba(235, 91, 60, 0.05)');
  gradient.addColorStop(1, isPos ? 'rgba(0, 208, 156, 0.0)' : 'rgba(235, 91, 60, 0.0)');

  // Baseline calculation (Previous Close for 1D session baseline)
  let baseline = null;
  if (currentChartRange === '1D' && currentPageAsset) {
    baseline = currentPageAsset.previous_close || (currentPageAsset.price - (currentPageAsset.change || 0));
  }

  const datasets = [{
    label: 'Price',
    data: prices,
    borderColor: strokeColor,
    borderWidth: isMobile ? 1.5 : 2.0,
    backgroundColor: gradient,
    fill: true,
    tension: 0.32,
    borderCapStyle: 'round',
    borderJoinStyle: 'round',
    pointRadius: 0,
    pointHoverRadius: isMobile ? 3.5 : 5.0,
    pointHoverBackgroundColor: strokeColor,
    pointHoverBorderColor: isDark ? '#0F172A' : '#ffffff',
    pointHoverBorderWidth: isMobile ? 1.8 : 2.5
  }];

  if (activeEmas.has(20)) {
    datasets.push({
      label: '20 EMA',
      data: calculateEMA(prices, 20),
      borderColor: '#F59E0B',
      borderWidth: 1.8,
      fill: false,
      tension: 0.32,
      borderCapStyle: 'round',
      borderJoinStyle: 'round',
      pointRadius: 0
    });
  }

  if (activeEmas.has(50)) {
    datasets.push({
      label: '50 EMA',
      data: calculateEMA(prices, 50),
      borderColor: '#8B5CF6',
      borderWidth: 1.8,
      fill: false,
      tension: 0.32,
      borderCapStyle: 'round',
      borderJoinStyle: 'round',
      pointRadius: 0
    });
  }

  pageChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: points.map(p => p.time),
      datasets: datasets
    },
    plugins: [growwChartPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: isMobile ? 2 : 0,
          right: isMobile ? 2 : 0,
          top: 8,
          bottom: isMobile ? 2 : 0
        }
      },
      interaction: {
        mode: 'index',
        intersect: false,
        axis: 'x'
      },
      plugins: {
        legend: {
          display: activeEmas.size > 0,
          labels: { color: '#94A3B8', font: { family: 'Sora, sans-serif', size: 11 } }
        },
        growwOptions: {
          baseline: baseline
        },
        tooltip: {
          enabled: activeEmas.size > 0,
          mode: 'index',
          intersect: false,
          backgroundColor: isDark ? 'rgba(15, 23, 42, 0.94)' : 'rgba(255, 255, 255, 0.95)',
          titleColor: isDark ? '#94A3B8' : '#64748B',
          bodyColor: isDark ? '#F8FAFC' : '#0F172A',
          borderColor: isDark ? '#334155' : '#E2E8F0',
          borderWidth: 1,
          bodyFont: { weight: '600', size: 11, family: 'Sora, sans-serif' },
          padding: 8,
          cornerRadius: 6,
          displayColors: true,
          boxWidth: 8,
          boxHeight: 8,
          usePointStyle: true,
          callbacks: {
            title: (items) => (items.length ? (points[items[0].dataIndex]?.time || items[0].label) : ''),
            label: (item) => `${item.dataset.label}: ${formatINR(item.parsed.y)}`
          }
        }
      },
      scales: {
        x: { 
          display: !isMobile,
          border: { display: false },
          grid: { display: false },
          ticks: {
            display: !isMobile,
            color: isDark ? '#64748B' : '#94A3B8',
            font: { family: 'Sora, sans-serif', size: 10 },
            maxTicksLimit: 6,
            maxRotation: 0
          }
        },
        y: { 
          display: true,
          position: 'right',
          grace: '8%',
          border: { display: false },
          grid: { 
            drawTicks: false,
            color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)' 
          },
          ticks: {
            display: !isMobile,
            color: isDark ? '#64748B' : '#94A3B8',
            padding: isMobile ? 0 : 8,
            font: { family: 'Sora, sans-serif', size: 10.5, weight: '500' },
            callback: (val) => formatINR(val)
          }
        }
      }
    }
  });
}

async function loadPageChartTimeframe(range, btnEl = null) {
  if (btnEl) {
    document.querySelectorAll('.asset-chart-card .tf-btn').forEach(b => b.classList.remove('active'));
    btnEl.classList.add('active');
  } else {
    document.querySelectorAll('.asset-chart-card .tf-btn').forEach(b => {
      if (b.innerText.trim() === range) b.classList.add('active');
      else b.classList.remove('active');
    });
  }
  currentChartRange = range;
  if (!currentPageAsset) return;

  try {
    const assetType = currentPageAsset.asset_type || 'STOCK';
    const res = await fetch(`/api/history?symbol=${encodeURIComponent(currentPageAsset.symbol)}&asset_type=${encodeURIComponent(assetType)}&range=${range}&timeframe=${range}`);
    const raw = await res.json();
    if (currentChartRange !== range) return;
    const points = Array.isArray(raw) ? raw : (raw.points || []);
    currentChartPoints = points;
    renderCurrentChart();
    resetHeroPrice();
  } catch (err) {
    console.error('Failed to load chart:', err);
  }
}

let chartResizeTimeout = null;
window.addEventListener('resize', () => {
  updateInstallButtonsVisibility();
  if (chartResizeTimeout) clearTimeout(chartResizeTimeout);
  chartResizeTimeout = setTimeout(() => {
    const detailPane = document.getElementById('pane-asset-detail');
    if (detailPane && detailPane.classList.contains('active')) {
      renderCurrentChart();
    }
  }, 120);
});

// Live Quote & 1D Chart Real-time Tick Sync
setInterval(async () => {
  const detailPane = document.getElementById('pane-asset-detail');
  if (detailPane && detailPane.classList.contains('active') && currentPageAsset && currentPageAsset.symbol) {
    try {
      const res = await fetch(`/api/quote?symbol=${encodeURIComponent(currentPageAsset.symbol)}`);
      if (res.ok) {
        const fresh = await res.json();
        if (fresh && fresh.price && fresh.price !== currentPageAsset.price) {
          currentPageAsset.price = fresh.price;
          currentPageAsset.change = fresh.change;
          currentPageAsset.change_pct = fresh.change_pct;
          resetHeroPrice();
          if (currentChartPoints && currentChartPoints.length > 0 && currentChartRange === '1D') {
            const last = currentChartPoints[currentChartPoints.length - 1];
            if (last) {
              last.value = fresh.price;
              last.price = fresh.price;
              last.close = fresh.price;
              if (last.high !== undefined) last.high = Math.max(last.high, fresh.price);
              if (last.low !== undefined) last.low = Math.min(last.low, fresh.price);
              if (pageChartInstance) {
                const dataArr = pageChartInstance.data.datasets[0].data;
                dataArr[dataArr.length - 1] = fresh.price;
                pageChartInstance.update('none');
              } else if (currentChartType === 'candle') {
                const canvas = document.getElementById('pageAssetChartCanvas');
                if (canvas) renderCandlestickCanvas(canvas, currentChartPoints);
              }
            }
          }
        }
      }
    } catch (_) {}
  }
}, 5000);

function openMobileTradeDrawer(action = 'BUY') {
  if (isGuest()) {
    showToast('Please create your free account to unlock ₹10,00,000 virtual balance and start trading.', false);
    navigateTo('/onboarding');
    return;
  }
  setPageOrderAction(action);
  const drawer = document.getElementById('mobileTradingDrawerOverlay');
  if (drawer) {
    drawer.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  const dInput = document.getElementById('drawerOrderQuantity');
  const mainInput = document.getElementById('pageOrderQuantity');
  if (dInput) {
    const qVal = (mainInput && mainInput.value) ? mainInput.value : (pageOrderState.quantity || 1);
    dInput.value = qVal;
    if (mainInput) mainInput.value = qVal;
  }

  const dLimit = document.getElementById('drawerLimitPrice');
  const mainLimit = document.getElementById('pageOrderLimitPrice');
  if (dLimit) {
    const limVal = (mainLimit && mainLimit.value) ? mainLimit.value : (currentPageAsset ? currentPageAsset.price : '');
    dLimit.value = limVal;
    if (mainLimit && !mainLimit.value) mainLimit.value = limVal;
  }

  const dTrig = document.getElementById('drawerTriggerPrice');
  const mainTrig = document.getElementById('pageOrderTriggerPrice');
  if (dTrig) {
    const trigVal = (mainTrig && mainTrig.value) ? mainTrig.value : '';
    dTrig.value = trigVal;
  }

  if (currentPageAsset && currentPageAsset.symbol) {
    updatePageAvailableHolding(currentPageAsset.symbol);
  }
  recalcPageMargin();
}

function closeMobileTradeDrawer() {
  const drawer = document.getElementById('mobileTradingDrawerOverlay');
  if (drawer) {
    drawer.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function syncDrawerQuantity(val) {
  const q = parseInt(val || '1', 10);
  const safeQ = isNaN(q) || q < 1 ? 1 : q;
  const mainInput = document.getElementById('pageOrderQuantity');
  if (mainInput) mainInput.value = safeQ;
  pageOrderState.quantity = safeQ;
  recalcPageMargin();
}

function syncDrawerLimit(val) {
  const mainInput = document.getElementById('pageOrderLimitPrice');
  if (mainInput) mainInput.value = val;
  recalcPageMargin();
}

function syncDrawerTrigger(val) {
  const mainInput = document.getElementById('pageOrderTriggerPrice');
  if (mainInput) mainInput.value = val;
  recalcPageMargin();
}

function setPageOrderAction(action) {
  pageOrderState.action = action;
  const buyBtn = document.getElementById('pageBtnBuy');
  const sellBtn = document.getElementById('pageBtnSell');
  const execBtn = document.getElementById('pageOrderExecuteBtn');
  const drawerBuy = document.getElementById('drawerBtnBuy');
  const drawerSell = document.getElementById('drawerBtnSell');
  const drawerExec = document.getElementById('drawerOrderExecuteBtn');
  const cleanSym = currentPageAsset ? currentPageAsset.symbol.replace('.NS', '') : 'ASSET';

  if (action === 'BUY') {
    if (buyBtn) buyBtn.className = 'trade-tab-btn active buy';
    if (sellBtn) sellBtn.className = 'trade-tab-btn sell';
    if (drawerBuy) drawerBuy.className = 'trade-tab-btn active buy';
    if (drawerSell) drawerSell.className = 'trade-tab-btn sell';
    if (execBtn) {
      execBtn.className = 'btn-trade-execute buy';
      execBtn.innerText = `BUY ${cleanSym}`;
    }
    if (drawerExec) {
      drawerExec.className = 'btn-trade-execute buy';
      drawerExec.innerText = `BUY ${cleanSym}`;
    }
  } else {
    if (buyBtn) buyBtn.className = 'trade-tab-btn buy';
    if (sellBtn) sellBtn.className = 'trade-tab-btn active sell';
    if (drawerBuy) drawerBuy.className = 'trade-tab-btn buy';
    if (drawerSell) drawerSell.className = 'trade-tab-btn active sell';
    if (execBtn) {
      execBtn.className = 'btn-trade-execute sell';
      execBtn.innerText = `SELL ${cleanSym}`;
    }
    if (drawerExec) {
      drawerExec.className = 'btn-trade-execute sell';
      drawerExec.innerText = `SELL ${cleanSym}`;
    }

    // Smart Position Detection on SELL
    if (currentPageAsset && currentPageAsset.symbol) {
      const targetSym = currentPageAsset.symbol.replace('.NS', '').replace('.BO', '').toUpperCase();
      Promise.all([
        fetch('/api/portfolio').then(r => r.json()).catch(() => ({})),
        fetch('/api/positions').then(r => r.json()).catch(() => ({}))
      ]).then(([pData, posData]) => {
        const holding = (pData.holdings || []).find(h => (h.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === targetSym);
        const pos = (posData.positions || []).find(p => (p.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === targetSym);
        
        if (holding && holding.quantity > 0 && (!pos || pos.quantity <= 0)) {
          setPageProductType('DELIVERY');
          setPageQuickQuantity(holding.quantity);
        } else if (pos && pos.quantity > 0 && (!holding || holding.quantity <= 0)) {
          setPageProductType('INTRADAY');
          setPageQuickQuantity(pos.quantity);
        } else if (holding && holding.quantity > 0) {
          setPageQuickQuantity(holding.quantity);
        } else if (pos && pos.quantity > 0) {
          setPageQuickQuantity(pos.quantity);
        }
        updatePageAvailableHolding(currentPageAsset.symbol);
      }).catch(() => {});
    }
  }
  if (currentPageAsset && currentPageAsset.symbol) {
    updatePageAvailableHolding(currentPageAsset.symbol);
  }
  recalcPageMargin();
}

function setPageProductType(prod) {
  pageOrderState.product = prod;
  const dProd = document.getElementById('pageProdDelivery');
  const iProd = document.getElementById('pageProdIntraday');
  const dDrw = document.getElementById('drawerProdDelivery');
  const iDrw = document.getElementById('drawerProdIntraday');
  if (dProd) dProd.className = `seg-btn ${prod === 'DELIVERY' ? 'active' : ''}`;
  if (iProd) iProd.className = `seg-btn ${prod === 'INTRADAY' ? 'active' : ''}`;
  if (dDrw) dDrw.className = `seg-btn ${prod === 'DELIVERY' ? 'active' : ''}`;
  if (iDrw) iDrw.className = `seg-btn ${prod === 'INTRADAY' ? 'active' : ''}`;

  const levHint = document.getElementById('pageLeverageHint');
  if (levHint) levHint.style.display = prod === 'INTRADAY' ? 'flex' : 'none';
  const dLevHint = document.getElementById('drawerLeverageHint');
  if (dLevHint) dLevHint.style.display = prod === 'INTRADAY' ? 'flex' : 'none';

  if (currentPageAsset && currentPageAsset.symbol) {
    updatePageAvailableHolding(currentPageAsset.symbol);
  }
  recalcPageMargin();
}

function setPageOrderVariety(varType) {
  pageOrderState.variety = varType;
  const mktBtn = document.getElementById('pageVarietyMarket');
  const limBtn = document.getElementById('pageVarietyLimit');
  const slBtn = document.getElementById('pageVarietySL');
  const gttBtn = document.getElementById('pageVarietyGTT');
  if (mktBtn) mktBtn.className = `seg-btn ${varType === 'MARKET' ? 'active' : ''}`;
  if (limBtn) limBtn.className = `seg-btn ${varType === 'LIMIT' ? 'active' : ''}`;
  if (slBtn) slBtn.className = `seg-btn ${varType === 'STOP_LOSS' ? 'active' : ''}`;
  if (gttBtn) gttBtn.className = `seg-btn ${varType === 'GTT' ? 'active' : ''}`;

  const dmktBtn = document.getElementById('drawerVarietyMarket');
  const dlimBtn = document.getElementById('drawerVarietyLimit');
  const dslBtn = document.getElementById('drawerVarietySL');
  const dgttBtn = document.getElementById('drawerVarietyGTT');
  if (dmktBtn) dmktBtn.className = `seg-btn ${varType === 'MARKET' ? 'active' : ''}`;
  if (dlimBtn) dlimBtn.className = `seg-btn ${varType === 'LIMIT' ? 'active' : ''}`;
  if (dslBtn) dslBtn.className = `seg-btn ${varType === 'STOP_LOSS' ? 'active' : ''}`;
  if (dgttBtn) dgttBtn.className = `seg-btn ${varType === 'GTT' ? 'active' : ''}`;

  const limitGroup = document.getElementById('pageLimitPriceGroup');
  const trigGroup = document.getElementById('pageTriggerPriceGroup');
  const dLimitGroup = document.getElementById('drawerLimitGroup');
  const dTrigGroup = document.getElementById('drawerTriggerGroup');
  if (limitGroup) limitGroup.style.display = (varType === 'LIMIT' || varType === 'STOP_LOSS' || varType === 'GTT') ? 'block' : 'none';
  if (trigGroup) trigGroup.style.display = (varType === 'STOP_LOSS' || varType === 'GTT') ? 'block' : 'none';
  if (dLimitGroup) dLimitGroup.style.display = (varType === 'LIMIT' || varType === 'STOP_LOSS' || varType === 'GTT') ? 'block' : 'none';
  if (dTrigGroup) dTrigGroup.style.display = (varType === 'STOP_LOSS' || varType === 'GTT') ? 'block' : 'none';

  const trigHint = document.getElementById('pageTriggerHint');
  const dTrigHint = document.getElementById('drawerTriggerHint');
  const trigMsg = varType === 'GTT' 
    ? 'Good-Till-Triggered order remains active until trigger is reached' 
    : 'Order activates when market hits this stop-loss trigger';
  if (trigHint) trigHint.innerText = trigMsg;
  if (dTrigHint) dTrigHint.innerText = trigMsg;

  const cleanSym = currentPageAsset ? (currentPageAsset.symbol || '').replace('.NS', '') : '';
  const execBtn = document.getElementById('pageOrderExecuteBtn');
  const drawerExec = document.getElementById('drawerOrderExecuteBtn');

  if (!isGuest()) {
    let btnText = `${pageOrderState.action} ${cleanSym}`;
    if (varType === 'STOP_LOSS') btnText = `PLACE STOP-LOSS (${pageOrderState.action})`;
    if (varType === 'GTT') btnText = `CREATE GTT TRIGGER (${pageOrderState.action})`;
    if (execBtn) execBtn.innerText = btnText;
    if (drawerExec) drawerExec.innerText = btnText;
  }

  recalcPageMargin();
}

function stepPageQuantity(delta) {
  const input = document.getElementById('pageOrderQuantity');
  const dInput = document.getElementById('drawerOrderQuantity');
  let val = parseInt((input ? input.value : '1') || '1', 10) + delta;
  if (val < 1) val = 1;
  if (input) input.value = val;
  if (dInput) dInput.value = val;
  pageOrderState.quantity = val;
  recalcPageMargin();
}

function setPageQuickQuantity(qty) {
  const input = document.getElementById('pageOrderQuantity');
  const dInput = document.getElementById('drawerOrderQuantity');
  if (input) input.value = qty;
  if (dInput) dInput.value = qty;
  pageOrderState.quantity = qty;
  recalcPageMargin();
}

function recalcPageMargin() {
  if (!currentPageAsset) return;
  const qtyInput = document.getElementById('pageOrderQuantity');
  const qty = parseInt((qtyInput ? qtyInput.value : '1') || '1', 10);
  const limInput = document.getElementById('pageOrderLimitPrice');
  const trigInput = document.getElementById('pageOrderTriggerPrice');

  let effectivePrice = currentPageAsset.price;
  if (pageOrderState.variety === 'LIMIT') {
    const limVal = parseFloat((limInput ? limInput.value : '') || '0');
    effectivePrice = limVal > 0 ? limVal : currentPageAsset.price;
  } else if (pageOrderState.variety === 'STOP_LOSS') {
    const trigVal = parseFloat((trigInput ? trigInput.value : '') || '0');
    if (pageOrderState.action === 'BUY' && trigVal > 0) {
      effectivePrice = trigVal;
    } else {
      effectivePrice = currentPageAsset.price;
    }
  } else if (pageOrderState.variety === 'GTT') {
    const trigVal = parseFloat((trigInput ? trigInput.value : '') || '0');
    const limVal = parseFloat((limInput ? limInput.value : '') || '0');
    effectivePrice = limVal > 0 ? limVal : (trigVal > 0 ? trigVal : currentPageAsset.price);
  }

  const total = qty * effectivePrice;
  const isSell = pageOrderState.action === 'SELL';
  const margin = pageOrderState.product === 'INTRADAY' ? total * 0.20 : total;

  const pMarginLabel = document.getElementById('pageMarginLabel');
  if (pMarginLabel) pMarginLabel.innerText = isSell ? (pageOrderState.product === 'INTRADAY' ? 'Intraday Turnover' : 'Gross Value') : 'Required Margin';
  const dMarginLabel = document.getElementById('drawerMarginLabel');
  if (dMarginLabel) dMarginLabel.innerText = isSell ? (pageOrderState.product === 'INTRADAY' ? 'Intraday Turnover' : 'Gross Value') : 'Required Margin';

  const reqEl = document.getElementById('pageRequiredMargin');
  if (reqEl) reqEl.innerText = formatINR(isSell ? total : margin);
  const dReqEl = document.getElementById('drawerRequiredMargin');
  if (dReqEl) dReqEl.innerText = formatINR(isSell ? total : margin);

  // Dynamic broker charges and net credit calculation
  const charges = calculateEstimatedCharges(total, pageOrderState.action, pageOrderState.product, currentPageAsset.asset_type || 'STOCK');
  const netProceeds = Math.max(0, total - charges.total);

  const pChargesRow = document.getElementById('pageChargesRow');
  const pChargesVal = document.getElementById('pageEstCharges');
  const pNetRow = document.getElementById('pageNetProceedsRow');
  const pNetVal = document.getElementById('pageNetProceeds');

  const dChargesRow = document.getElementById('drawerChargesRow');
  const dChargesVal = document.getElementById('drawerEstCharges');
  const dNetRow = document.getElementById('drawerNetProceedsRow');
  const dNetVal = document.getElementById('drawerNetProceeds');

  if (isSell) {
    if (pChargesRow) pChargesRow.style.display = 'flex';
    if (pChargesVal) pChargesVal.innerText = `${formatINR(charges.total)} ℹ️`;
    if (pNetRow) pNetRow.style.display = 'flex';
    if (pNetVal) pNetVal.innerText = formatINR(netProceeds);

    if (dChargesRow) dChargesRow.style.display = 'flex';
    if (dChargesVal) dChargesVal.innerText = `${formatINR(charges.total)} ℹ️`;
    if (dNetRow) dNetRow.style.display = 'flex';
    if (dNetVal) dNetVal.innerText = formatINR(netProceeds);
  } else {
    if (pChargesRow) pChargesRow.style.display = 'none';
    if (pNetRow) pNetRow.style.display = 'none';
    if (dChargesRow) dChargesRow.style.display = 'none';
    if (dNetRow) dNetRow.style.display = 'none';
  }

  const availCash = getActiveAvailableCash();
  const cashEl = document.getElementById('pageAvailableCash');
  if (cashEl) cashEl.innerText = formatINR(availCash);
  const dCashEl = document.getElementById('drawerAvailableCash');
  if (dCashEl) dCashEl.innerText = formatINR(availCash);

  const execBtn = document.getElementById('pageOrderExecuteBtn');
  const drawerExec = document.getElementById('drawerOrderExecuteBtn');
  const cleanSym = currentPageAsset.symbol ? currentPageAsset.symbol.replace('.NS', '') : '';

  if (isGuest()) {
    if (cashEl) cashEl.innerText = '₹0.00 (Locked)';
    if (dCashEl) dCashEl.innerText = '₹0.00 (Locked)';
    if (execBtn) {
      execBtn.innerText = 'Start Investing to Trade (Unlock ₹10L)';
      execBtn.className = 'btn-trade-execute guest-locked';
    }
    if (drawerExec) {
      drawerExec.innerText = 'Start Investing to Trade (Unlock ₹10L)';
      drawerExec.className = 'btn-trade-execute guest-locked';
    }
  } else {
    let btnText = `${pageOrderState.action} ${cleanSym}`;
    if (pageOrderState.variety === 'STOP_LOSS') btnText = `PLACE STOP-LOSS (${pageOrderState.action})`;
    if (pageOrderState.variety === 'GTT') btnText = `CREATE GTT TRIGGER (${pageOrderState.action})`;
    
    if (execBtn) {
      execBtn.className = `btn-trade-execute ${pageOrderState.action.toLowerCase()}`;
      execBtn.innerText = btnText;
    }
    if (drawerExec) {
      drawerExec.className = `btn-trade-execute ${pageOrderState.action.toLowerCase()}`;
      drawerExec.innerText = btnText;
    }
  }
}

async function updatePageAvailableHolding(symbol) {
  try {
    if (!symbol) return;
    const cleanSym = symbol.replace('.NS', '').replace('.BO', '').toUpperCase();
    const [pRes, posRes] = await Promise.all([
      fetch('/api/portfolio').catch(() => null),
      fetch('/api/positions').catch(() => null)
    ]);

    let holdings = [];
    if (pRes && pRes.ok) {
      const pData = await pRes.json();
      holdings = pData.holdings || [];
    }
    let positions = [];
    if (posRes && posRes.ok) {
      const posData = await posRes.json();
      positions = posData.positions || [];
    }

    const holding = holdings.find(h => (h.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === cleanSym);
    const pos = positions.find(p => (p.symbol || '').replace('.NS', '').replace('.BO', '').toUpperCase() === cleanSym);

    const deliveryQty = holding ? (holding.quantity || 0) : 0;
    const intradayQty = pos ? (pos.quantity || 0) : 0;

    const isIntraday = pageOrderState.product === 'INTRADAY';
    const activeQty = isIntraday ? intradayQty : deliveryQty;
    const prodLabel = isIntraday ? 'Intraday' : 'Delivery';

    let displayTxt = `${activeQty} ${prodLabel} share${activeQty === 1 ? '' : 's'} owned`;
    if (!isIntraday && intradayQty > 0) {
      displayTxt += ` • ${intradayQty} open (Intraday)`;
    } else if (isIntraday && deliveryQty > 0) {
      displayTxt += ` • ${deliveryQty} owned (Delivery)`;
    }

    const clickHandler = () => {
      if (activeQty > 0) {
        setPageQuickQuantity(activeQty);
      }
    };

    const label = document.getElementById('pageAvailableHoldingQty');
    if (label) {
      label.innerText = displayTxt;
      label.title = activeQty > 0 ? 'Click to fill quantity' : '';
      label.style.cursor = activeQty > 0 ? 'pointer' : 'default';
      label.onclick = clickHandler;
    }
    const dLabel = document.getElementById('drawerHoldingQty');
    if (dLabel) {
      dLabel.innerText = displayTxt;
      dLabel.title = activeQty > 0 ? 'Click to fill quantity' : '';
      dLabel.style.cursor = activeQty > 0 ? 'pointer' : 'default';
      dLabel.onclick = clickHandler;
    }
  } catch (err) {
    console.error('updatePageAvailableHolding error:', err);
  }
}

async function executePageTrade() {
  if (isGuest()) {
    showToast('Please create your free account to unlock ₹10,00,000 virtual balance and start trading.', false);
    navigateTo('/onboarding');
    return;
  }

  const execBtn = document.getElementById('pageOrderExecuteBtn');
  const drawerExec = document.getElementById('drawerOrderExecuteBtn');
  if (execBtn && execBtn.disabled && (!drawerExec || drawerExec.disabled)) return;

  if (!currentPageAsset) {
    const path = window.location.pathname;
    const sym = path.startsWith('/stock/') ? path.replace('/stock/', '').trim() : (path.startsWith('/mf/') ? path.replace('/mf/', '').trim() : '');
    if (sym) {
      await showAssetPage(sym, path.startsWith('/mf/') ? 'MUTUAL_FUND' : 'STOCK');
    }
    if (!currentPageAsset) {
      showToast('Asset quote not loaded yet. Please wait a moment or refresh.', true);
      return;
    }
  }

  const qtyInput = document.getElementById('pageOrderQuantity');
  const dQtyInput = document.getElementById('drawerOrderQuantity');
  let rawQty = qtyInput ? qtyInput.value : '';
  if ((!rawQty || isNaN(parseInt(rawQty, 10))) && dQtyInput) {
    rawQty = dQtyInput.value;
  }
  const qty = parseInt(rawQty || pageOrderState.quantity || '1', 10);
  if (!qty || qty <= 0 || isNaN(qty)) {
    showToast('Please specify a valid quantity (minimum 1)', true);
    return;
  }

  const limitInput = document.getElementById('pageOrderLimitPrice');
  const dLimitInput = document.getElementById('drawerLimitPrice');
  let rawLimit = limitInput ? limitInput.value : '';
  if (!rawLimit && dLimitInput) rawLimit = dLimitInput.value;
  const limitPrice = (pageOrderState.variety === 'LIMIT' || pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT')
    ? parseFloat(rawLimit || currentPageAsset.price)
    : null;

  if (pageOrderState.variety === 'LIMIT' && (!limitPrice || limitPrice <= 0 || isNaN(limitPrice))) {
    showToast('Please enter a valid Limit Price', true);
    return;
  }

  const trigInput = document.getElementById('pageOrderTriggerPrice');
  const dTrigInput = document.getElementById('drawerTriggerPrice');
  let rawTrig = trigInput ? trigInput.value : '';
  if (!rawTrig && dTrigInput) rawTrig = dTrigInput.value;
  const triggerPrice = (pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT')
    ? parseFloat(rawTrig || '0')
    : 0.0;

  if ((pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT') && (!triggerPrice || triggerPrice <= 0 || isNaN(triggerPrice))) {
    showToast('Please enter a valid Trigger Price', true);
    return;
  }

  const execPrice = (pageOrderState.variety === 'LIMIT' || pageOrderState.variety === 'STOP_LOSS')
    ? (limitPrice || currentPageAsset.price)
    : (pageOrderState.variety === 'GTT' ? (limitPrice || triggerPrice || currentPageAsset.price) : currentPageAsset.price);

  const drawer = document.getElementById('mobileTradingDrawerOverlay');
  const isFromDrawer = drawer && drawer.classList.contains('active');

  openOrderConfirmModal({
    origin: isFromDrawer ? 'DRAWER' : 'PAGE',
    symbol: currentPageAsset.symbol,
    name: currentPageAsset.name,
    asset_type: currentPageAsset.asset_type || 'STOCK',
    action: pageOrderState.action,
    product: pageOrderState.product,
    quantity: qty,
    price: execPrice,
    variety: pageOrderState.variety,
    limit_price: limitPrice,
    trigger_price: triggerPrice
  });
}

/* =======================================================
   GROWW-STYLE ACCOUNT ONBOARDING WIZARD ENGINE (AUTHENTIC USER-TYPED)
   ======================================================= */
let obCurrentStep = 1;
let obUserData = {
  phone: '',
  email: '',
  username: '',
  password: '',
  name: '',
  pan: '',
  dob: '',
  gender: 'Male',
  occupation: 'Private Sector',
  income: '₹1L - ₹5L',
  bank_name: 'HDFC Bank',
  bank_account: '',
  ifsc: 'HDFC0001234',
  pin: '',
  generatedOtp: ''
};

function showOnboardingPage() {
  document.body.classList.remove('viewing-profile');
  document.documentElement.classList.remove('viewing-profile');
  document.body.classList.remove('viewing-asset-detail');
  document.documentElement.classList.remove('viewing-asset-detail');
  closeMobileTradeDrawer();
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-links .nav-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  const obPane = document.getElementById('pane-onboarding');
  if (obPane) obPane.classList.add('active');

  // Reset all input fields completely so user types their own fake details
  const phoneInput = document.getElementById('obInputPhone');
  if (phoneInput) phoneInput.value = '';
  const emailInput = document.getElementById('obInputEmail');
  if (emailInput) emailInput.value = '';
  const userInput = document.getElementById('obInputUsername');
  if (userInput) userInput.value = '';
  const passInput = document.getElementById('obInputPassword');
  if (passInput) passInput.value = '';
  const statusBadge = document.getElementById('obUsernameStatus');
  if (statusBadge) { statusBadge.style.display = 'none'; statusBadge.innerText = ''; }
  const panInput = document.getElementById('obInputPan');
  if (panInput) panInput.value = '';
  const nameInput = document.getElementById('obInputName');
  if (nameInput) nameInput.value = '';
  const dobInput = document.getElementById('obInputDob');
  if (dobInput) {
    const thirteenYearsAgo = new Date();
    thirteenYearsAgo.setFullYear(thirteenYearsAgo.getFullYear() - 13);
    const maxAllowedDob = thirteenYearsAgo.toISOString().split('T')[0];
    dobInput.max = maxAllowedDob;
    dobInput.value = '2000-01-01';
  }
  const ageInput = document.getElementById('obInputAge');
  if (ageInput) ageInput.value = '24';
  const expInput = document.getElementById('obInputExperience');
  if (expInput) expInput.value = 'None / Total Beginner';
  const accInput = document.getElementById('obInputAccount');
  if (accInput) accInput.value = '';
  const accConfInput = document.getElementById('obInputAccountConfirm');
  if (accConfInput) accConfInput.value = '';
  const ifscInput = document.getElementById('obInputIfsc');
  if (ifscInput) ifscInput.value = '';
  const pinInput = document.getElementById('obInputPin');
  if (pinInput) pinInput.value = '';
  const pinConfInput = document.getElementById('obInputPinConfirm');
  if (pinConfInput) pinConfInput.value = '';

  [1, 2, 3, 4].forEach(i => {
    const el = document.getElementById('otp-' + i);
    if (el) el.value = '';
  });

  const smsBanner = document.getElementById('smsPushBanner');
  if (smsBanner) smsBanner.style.display = 'none';

  goToObStep(1);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

let usernameDebounceTimer = null;
async function onUsernameInput(inputEl) {
  const statusBadge = document.getElementById('obUsernameStatus');
  if (!statusBadge) return;
  const raw = (inputEl.value || '').trim().replace(/^@/, '').toLowerCase();
  if (!raw) {
    statusBadge.style.display = 'none';
    return;
  }
  if (raw.length < 3) {
    statusBadge.style.display = 'inline';
    statusBadge.style.color = 'var(--text-muted)';
    statusBadge.innerText = 'Min 3 chars';
    return;
  }
  if (!/^[a-zA-Z0-9_]+$/.test(raw)) {
    statusBadge.style.display = 'inline';
    statusBadge.style.color = '#EF4444';
    statusBadge.innerText = 'Only letters, numbers, _';
    return;
  }

  statusBadge.style.display = 'inline';
  statusBadge.style.color = 'var(--text-muted)';
  statusBadge.innerText = 'Checking...';

  clearTimeout(usernameDebounceTimer);
  usernameDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/user/check-username?username=${encodeURIComponent(raw)}`);
      const data = await res.json();
      if (data.available) {
        statusBadge.style.color = '#10B981';
        statusBadge.innerText = `✓ @${raw} available`;
      } else {
        statusBadge.style.color = '#EF4444';
        statusBadge.innerText = `✗ Taken`;
      }
    } catch (_) {
      statusBadge.style.display = 'none';
    }
  }, 300);
}

function goToObStep(stepNum) {
  obCurrentStep = stepNum;
  for (let i = 1; i <= 6; i++) {
    const el = document.getElementById(`obStep-${i}`);
    if (el) el.classList.remove('active');
    const ind = document.getElementById(`obStepIndicator-${i}`);
    if (ind) {
      ind.classList.remove('active');
      if (i < stepNum) ind.classList.add('completed');
      else ind.classList.remove('completed');
      if (i === stepNum) ind.classList.add('active');
    }
    const conn = document.getElementById(`obConnector-${i}`);
    if (conn) {
      if (i < stepNum) conn.classList.add('completed');
      else conn.classList.remove('completed');
    }
  }

  if (stepNum === 3) {
    const dobInput = document.getElementById('obInputDob');
    const ageInput = document.getElementById('obInputAge');
    if (dobInput) {
      const thirteenYearsAgo = new Date();
      thirteenYearsAgo.setFullYear(thirteenYearsAgo.getFullYear() - 13);
      const maxAllowedDob = thirteenYearsAgo.toISOString().split('T')[0];
      dobInput.max = maxAllowedDob;
      if (!dobInput.value || new Date(dobInput.value) > thirteenYearsAgo) {
        dobInput.value = '2000-01-01';
      }
      dobInput.onchange = () => {
        if (dobInput.value) {
          const b = new Date(dobInput.value);
          const now = new Date();
          let calculatedAge = now.getFullYear() - b.getFullYear();
          const m = now.getMonth() - b.getMonth();
          if (m < 0 || (m === 0 && now.getDate() < b.getDate())) calculatedAge--;
          if (ageInput && calculatedAge >= 13) ageInput.value = calculatedAge;
        }
      };
    }
  }

  const activeContent = document.getElementById(`obStep-${stepNum}`);
  if (activeContent) activeContent.classList.add('active');
}

async function submitObStep1() {
  const phone = document.getElementById('obInputPhone').value.trim();
  const email = document.getElementById('obInputEmail').value.trim();
  const username = (document.getElementById('obInputUsername')?.value || '').trim().replace(/^@/, '').toLowerCase();
  const password = (document.getElementById('obInputPassword')?.value || '').trim();

  if (phone.length < 10) {
    showToast('Please enter a valid 10-digit mobile number', true);
    document.getElementById('obInputPhone').focus();
    return;
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email || !emailRegex.test(email)) {
    showToast('Please enter your email address (fake or real, e.g. name@example.com)', true);
    document.getElementById('obInputEmail').focus();
    return;
  }
  if (!username || username.length < 3 || username.length > 25) {
    showToast('Please choose a username between 3 and 25 characters', true);
    document.getElementById('obInputUsername')?.focus();
    return;
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    showToast('Username can only contain letters, numbers, and underscores', true);
    document.getElementById('obInputUsername')?.focus();
    return;
  }
  if (!password || password.length < 6) {
    showToast('Please create a password of at least 6 characters', true);
    document.getElementById('obInputPassword')?.focus();
    return;
  }

  // Verify username availability
  try {
    const uChk = await fetch(`/api/user/check-username?username=${encodeURIComponent(username)}`);
    const uData = await uChk.json();
    if (!uData.available) {
      showToast(uData.message || `@${username} is already taken. Please choose another.`, true);
      document.getElementById('obInputUsername')?.focus();
      return;
    }
  } catch (err) {
    console.warn('Username check warning:', err);
  }

  // Check if account already exists with this email or phone
  try {
    const chk = await fetch('/api/user/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier: email })
    });
    const chkData = await chk.json();
    if (chk.ok && chkData.success) {
      showToast(`Account found for ${chkData.user.name}! Please enter your Password or PIN to log in.`, false);
      openLoginModal(email);
      return;
    }
  } catch (_) {}

  obUserData.phone = phone;
  obUserData.email = email;
  obUserData.username = username;
  obUserData.password = password;
  document.getElementById('obDisplayPhone').innerText = `+91 ${phone}`;

  // Generate real simulated 4-digit OTP
  const otp = Math.floor(1000 + Math.random() * 9000).toString();
  obUserData.generatedOtp = otp;

  // Clear OTP boxes
  [1, 2, 3, 4].forEach(i => {
    const el = document.getElementById('otp-' + i);
    if (el) el.value = '';
  });

  // Display simulated push SMS banner
  const smsBanner = document.getElementById('smsPushBanner');
  const smsCodeEl = document.getElementById('smsOtpCode');
  if (smsBanner && smsCodeEl) {
    smsCodeEl.innerText = otp;
    smsBanner.style.display = 'flex';
  }

  goToObStep(2);
  setTimeout(() => {
    const firstOtp = document.getElementById('otp-1');
    if (firstOtp) firstOtp.focus();
  }, 100);
}

function pasteSmsOtp() {
  if (!obUserData.generatedOtp) return;
  const chars = obUserData.generatedOtp.split('');
  chars.forEach((c, idx) => {
    const el = document.getElementById(`otp-${idx + 1}`);
    if (el) el.value = c;
  });
  const fourth = document.getElementById('otp-4');
  if (fourth) fourth.focus();
  showToast('OTP auto-pasted from SMS!');
}

function resendOtp() {
  const otp = Math.floor(1000 + Math.random() * 9000).toString();
  obUserData.generatedOtp = otp;
  const smsCodeEl = document.getElementById('smsOtpCode');
  if (smsCodeEl) smsCodeEl.innerText = otp;
  const smsBanner = document.getElementById('smsPushBanner');
  if (smsBanner) {
    smsBanner.style.display = 'flex';
    smsBanner.style.animation = 'none';
    setTimeout(() => smsBanner.style.animation = 'slideDownSms 0.35s ease-out', 10);
  }
  showToast(`New OTP sent: ${otp}`);
}

function moveOtp(idx, e) {
  const val = e.target.value;
  if (val.length >= 1 && idx < 4) {
    const next = document.getElementById(`otp-${idx + 1}`);
    if (next) next.focus();
  }
}

function handleOtpBackspace(idx, e) {
  if (e.key === 'Backspace' && !e.target.value && idx > 1) {
    const prev = document.getElementById(`otp-${idx - 1}`);
    if (prev) {
      prev.focus();
      prev.value = '';
    }
  }
}

function submitObStep2() {
  const typed = [1, 2, 3, 4].map(i => document.getElementById(`otp-${i}`).value).join('');
  if (typed.length < 4) {
    showToast('Please enter the full 4-digit OTP code', true);
    return;
  }
  if (obUserData.generatedOtp && typed !== obUserData.generatedOtp && typed !== '4321') {
    showToast(`Invalid OTP. Please check the code (${obUserData.generatedOtp})`, true);
    return;
  }

  const smsBanner = document.getElementById('smsPushBanner');
  if (smsBanner) smsBanner.style.display = 'none';

  showToast('Mobile number verified successfully! ✓');
  goToObStep(3);
}

function onPanInput(el) {
  el.value = el.value.toUpperCase();
}

function submitObStep3() {
  const pan = document.getElementById('obInputPan').value.trim().toUpperCase();
  const name = document.getElementById('obInputName').value.trim();
  const dob = document.getElementById('obInputDob').value;
  const gender = document.getElementById('obInputGender').value;
  const occupation = document.getElementById('obInputOccupation')?.value || 'Private Sector';
  const income = document.getElementById('obInputIncome')?.value || '₹1L - ₹5L';
  const ageInput = document.getElementById('obInputAge');
  const expInput = document.getElementById('obInputExperience');

  if (!pan || pan.length !== 10) {
    showToast('Please enter a 10-digit PAN (e.g. ABCDE1234F)', true);
    document.getElementById('obInputPan').focus();
    return;
  }
  if (!name) {
    showToast('Please enter your full legal name', true);
    document.getElementById('obInputName').focus();
    return;
  }
  if (!dob) {
    showToast('Please enter your Date of Birth', true);
    document.getElementById('obInputDob').focus();
    return;
  }

  const birthDate = new Date(dob);
  const cutoffDate = new Date();
  cutoffDate.setFullYear(cutoffDate.getFullYear() - 13);

  if (isNaN(birthDate.getTime())) {
    showToast('Please enter a valid Date of Birth', true);
    document.getElementById('obInputDob').focus();
    return;
  }

  const ageVal = parseInt(ageInput ? ageInput.value : '18', 10);
  if (isNaN(ageVal) || ageVal < 13) {
    showToast('You must be at least 13 years of age to register', true);
    if (ageInput) ageInput.focus();
    return;
  }

  const expVal = expInput ? expInput.value : 'None / Total Beginner';

  obUserData.pan = pan;
  obUserData.name = name;
  obUserData.dob = dob;
  obUserData.gender = gender;
  obUserData.occupation = occupation;
  obUserData.income = income;
  obUserData.age = ageVal;
  obUserData.experience = expVal;

  showToast(`PAN ${pan} verified for ${name}! ✓`);
  goToObStep(4);
}

function selectBank(name, ifsc, el) {
  obUserData.bank_name = name;
  const ifscInput = document.getElementById('obInputIfsc');
  if (ifscInput) ifscInput.value = ifsc;
  document.querySelectorAll('.bank-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
}

function submitObStep4() {
  const acc = document.getElementById('obInputAccount').value.trim();
  const accConfirm = document.getElementById('obInputAccountConfirm').value.trim();
  const ifsc = document.getElementById('obInputIfsc').value.trim().toUpperCase();

  if (!acc) {
    showToast('Please enter your bank account number', true);
    document.getElementById('obInputAccount').focus();
    return;
  }
  if (acc !== accConfirm) {
    showToast('Bank account numbers do not match. Please re-check', true);
    document.getElementById('obInputAccountConfirm').focus();
    return;
  }
  if (!ifsc || ifsc.length < 4) {
    showToast('Please enter a valid IFSC code', true);
    document.getElementById('obInputIfsc').focus();
    return;
  }

  obUserData.bank_account = acc;
  obUserData.ifsc = ifsc;

  const loader = document.getElementById('pennyDropLoader');
  const btn = document.getElementById('btnVerifyBank');
  if (loader) {
    loader.style.display = 'flex';
    document.getElementById('pennyDropText').innerText = 'Connecting to NPCI IMPS...';
  }
  if (btn) btn.disabled = true;

  setTimeout(() => {
    document.getElementById('pennyDropText').innerText = `Deposited ₹1.00 via Penny Drop. Verified: ${obUserData.name} ✓`;
    setTimeout(() => {
      if (loader) loader.style.display = 'none';
      if (btn) btn.disabled = false;
      showToast(`${obUserData.bank_name} account verified & linked successfully! ✓`);
      goToObStep(5);
    }, 1200);
  }, 1000);
}

async function submitObStep5() {
  const pin = document.getElementById('obInputPin').value.trim();
  const confirmPin = document.getElementById('obInputPinConfirm').value.trim();

  if (!pin || pin.length !== 4) {
    showToast('Please enter a 4-digit security PIN', true);
    document.getElementById('obInputPin').focus();
    return;
  }
  if (pin !== confirmPin) {
    showToast('PINs do not match. Please enter the same 4-digit PIN in both fields', true);
    document.getElementById('obInputPinConfirm').focus();
    return;
  }

  obUserData.pin = pin;

  try {
    const res = await fetch('/api/user/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: obUserData.name,
        username: obUserData.username || null,
        password: obUserData.password || null,
        email: obUserData.email,
        phone: obUserData.phone,
        pan: obUserData.pan,
        dob: obUserData.dob,
        bank_name: obUserData.bank_name,
        bank_account: obUserData.bank_account,
        pin: obUserData.pin,
        age: obUserData.age || 18,
        experience: obUserData.experience || 'None / Total Beginner'
      })
    });
    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.detail || 'Failed to create account', true);
      return;
    }

    currentUser = result.user;
    localStorage.removeItem('stoxify_guest_mode');
    localStorage.setItem('stoxify_user_id', currentUser.id);
    localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
    document.documentElement.classList.add('user-logged-in');
    document.documentElement.classList.remove('user-guest');

    // Update Confirmation screen with user's actual entered details
    document.getElementById('obWelcomeName').innerText = currentUser.name;
    document.getElementById('obCreatedDemat').innerText = currentUser.id || `STOX-${Math.floor(100000 + Math.random() * 900000)}`;
    const usernameEl = document.getElementById('obCreatedUsername');
    if (usernameEl) usernameEl.innerText = currentUser.username ? ('@' + currentUser.username) : ('@' + (obUserData.username || 'trader'));
    const emailEl = document.getElementById('obCreatedEmail');
    if (emailEl) emailEl.innerText = currentUser.email || obUserData.email || '';
    const last4 = (currentUser.bank_account || '5678').slice(-4);
    document.getElementById('obCreatedBank').innerText = `${currentUser.bank_name} •••• ${last4} (Verified ✓)`;

    saveLocalBankTx(currentUser.id, {
      user_id: currentUser.id,
      type: 'INITIAL_CREDIT',
      amount: 1000000.0,
      from_account: 'RBI Simulated Banking Gateway',
      to_account: `${currentUser.bank_name || 'HDFC Bank'} •••• ${last4}`,
      reference_id: `BANK-INIT-${currentUser.id}`,
      status: 'SUCCESS',
      note: 'Welcome virtual capital credited to linked bank account',
      created_at: new Date().toISOString()
    });

    updateNavbarProfile();
    saveRecentAccount(currentUser);
    fetchAccount();
    goToObStep(6);

  } catch (err) {
    showToast('Error connecting to onboarding server', true);
  }
}

function finishOnboarding() {
  updateNavbarProfile();
  navigateTo('/explore');
  showToast(`Welcome to Stoxifyin', ${currentUser.name}! ₹10,00,000 virtual cash ready in your linked bank account!`);
}



/* =======================================================
   ORDER CONFIRMATION MODAL HELPERS
   ======================================================= */
function openOrderSuccessModal(orderData) {
  const modal = document.getElementById('orderSuccessModal');
  if (!modal) return;

  const titleEl = document.getElementById('orderSuccessTitle');
  const subtitleEl = document.getElementById('orderSuccessSubtitle');
  const viewBtn = document.getElementById('orderSuccessViewBtn');
  const status = (orderData.status || '').toUpperCase();

  if (status === 'OPEN') {
    if (titleEl) titleEl.innerText = 'Limit Order Placed!';
    if (subtitleEl) subtitleEl.innerText = 'Your order is OPEN and will execute automatically when the market reaches your limit price.';
    if (viewBtn) {
      viewBtn.innerText = 'View in Orders →';
      viewBtn.onclick = () => {
        closeOrderSuccessModal();
        navigateTo('/orders');
      };
    }
  } else if (status === 'TRIGGER_PENDING') {
    if (titleEl) titleEl.innerText = 'Stop-Loss Order Placed!';
    if (subtitleEl) subtitleEl.innerText = 'Your trigger is PENDING and will activate when the market reaches your trigger price.';
    if (viewBtn) {
      viewBtn.innerText = 'View in Orders →';
      viewBtn.onclick = () => {
        closeOrderSuccessModal();
        navigateTo('/orders');
      };
    }
  } else {
    if (titleEl) titleEl.innerText = 'Order Executed!';
    if (subtitleEl) subtitleEl.innerText = 'Your paper trade was filled and is now reflected in your portfolio.';
    if (viewBtn) {
      if (orderData.product === 'INTRADAY') {
        viewBtn.innerText = 'View in Positions →';
        viewBtn.onclick = () => {
          closeOrderSuccessModal();
          navigateTo('/positions');
        };
      } else {
        viewBtn.innerText = 'View in Holdings →';
        viewBtn.onclick = () => {
          closeOrderSuccessModal();
          navigateTo('/holdings');
        };
      }
    }
  }

  const assetEl = document.getElementById('orderSuccessAsset');
  if (assetEl) assetEl.innerText = `${orderData.name} (${orderData.symbol})`;
  const typeEl = document.getElementById('orderSuccessType');
  if (typeEl) typeEl.innerText = `${orderData.action} • ${orderData.product === 'INTRADAY' ? 'INTRADAY (MIS)' : 'DELIVERY (CNC)'}`;
  const qtyEl = document.getElementById('orderSuccessQty');
  if (qtyEl) qtyEl.innerText = `${orderData.quantity} Shares / Units`;
  const priceEl = document.getElementById('orderSuccessPrice');
  if (priceEl) priceEl.innerText = formatINR(orderData.price);
  const totalEl = document.getElementById('orderSuccessTotal');
  if (totalEl) totalEl.innerText = formatINR(orderData.total);

  const totalLabel = document.getElementById('orderSuccessTotalLabel');
  const chargesRow = document.getElementById('orderSuccessChargesRow');
  const chargesVal = document.getElementById('orderSuccessCharges');
  const netRow = document.getElementById('orderSuccessNetRow');
  const netVal = document.getElementById('orderSuccessNet');

  const isSell = (orderData.action || '').toUpperCase() === 'SELL';
  if (isSell && orderData.charges) {
    const totalCharges = typeof orderData.charges === 'object' ? (orderData.charges.total || 0) : (parseFloat(orderData.charges) || 0);
    const netAmount = orderData.net_amount !== undefined ? orderData.net_amount : Math.max(0, orderData.total - totalCharges);

    if (totalLabel) totalLabel.innerText = 'Gross Order Value';
    if (chargesRow) chargesRow.style.display = 'flex';
    if (chargesVal) chargesVal.innerText = `-${formatINR(totalCharges)}`;
    if (netRow) netRow.style.display = 'flex';
    if (netVal) netVal.innerText = formatINR(netAmount);
  } else {
    if (totalLabel) totalLabel.innerText = 'Total Amount';
    if (chargesRow) chargesRow.style.display = 'none';
    if (netRow) netRow.style.display = 'none';
  }

  // Authoritative confirmed balance display
  const balRow = document.getElementById('orderSuccessBalanceRow');
  const balVal = document.getElementById('orderSuccessBalance');
  if (orderData.balance !== undefined && balRow && balVal) {
    balRow.style.display = 'flex';
    balVal.innerText = formatINR(orderData.balance);
  } else if (balRow) {
    balRow.style.display = 'none';
  }

  modal.classList.add('active');
}

function closeOrderSuccessModal() {
  const modal = document.getElementById('orderSuccessModal');
  if (modal) modal.classList.remove('active');
}

function goToHoldingsFromModal() {
  closeOrderSuccessModal();
  navigateTo('/holdings');
}

/* =======================================================
   GROWW-STYLE ORDER CONFIRMATION SHEET ENGINE
   ======================================================= */
let pendingOrderSpec = null;

function roundTo2(val) {
  return Math.round((Number(val || 0) + Number.EPSILON) * 100) / 100;
}

function calculateClientCharges(orderType, productType, assetType, amount) {
  amount = parseFloat(amount || 0);
  if (amount <= 0 || (assetType || '').toUpperCase() === 'MUTUAL_FUND') {
    return { brokerage: 0, dp_charges: 0, stt: 0, exchange: 0, sebi: 0, stamp: 0, gst: 0, total: 0 };
  }
  const isSell = (orderType || '').toUpperCase() === 'SELL';
  const isIntra = (productType || '').toUpperCase() === 'INTRADAY';
  const brokerage = 0.0; // Stoxify standard: ₹0 brokerage
  const dp_charges = (isSell && !isIntra) ? 13.50 : 0.0;
  let stt = 0.0;
  if (isSell) {
    stt = isIntra ? roundTo2(amount * 0.00025) : roundTo2(amount * 0.001);
  } else {
    stt = isIntra ? 0.0 : roundTo2(amount * 0.001);
  }
  const exchange = roundTo2(amount * 0.0000297);
  const sebi = roundTo2((amount / 10000000.0) * 10.0);
  const stamp = isSell ? 0.0 : roundTo2(amount * (isIntra ? 0.00003 : 0.00015));
  const gst = roundTo2((brokerage + exchange + sebi + dp_charges) * 0.18);
  const total = roundTo2(brokerage + dp_charges + stt + exchange + sebi + stamp + gst);
  return { brokerage, dp_charges, stt, exchange, sebi, stamp, gst, total };
}

function openOrderConfirmModal(spec) {
  pendingOrderSpec = spec;
  const modal = document.getElementById('orderConfirmModal');
  if (!modal) return;

  const sideBadge = document.getElementById('confirmOrderSideBadge');
  const prodBadge = document.getElementById('confirmOrderProductBadge');
  const titleEl = document.getElementById('confirmOrderTitle');
  const subtitleEl = document.getElementById('confirmOrderSubtitle');
  const qtyPriceEl = document.getElementById('confirmOrderQtyPrice');
  const grossEl = document.getElementById('confirmOrderGrossValue');
  const marginReqEl = document.getElementById('confirmOrderMarginReq');
  const availCashEl = document.getElementById('confirmOrderAvailCash');
  const netTotalEl = document.getElementById('confirmOrderNetTotal');
  const errorEl = document.getElementById('confirmOrderError');
  const chargesHeaderEl = document.getElementById('confirmTotalChargesHeader');

  if (errorEl) {
    errorEl.style.display = 'none';
    errorEl.innerText = '';
  }

  const isBuy = (spec.action || 'BUY').toUpperCase() === 'BUY';
  if (sideBadge) {
    sideBadge.innerText = spec.action;
    sideBadge.className = isBuy ? 'badge-positive' : 'badge-negative';
  }

  if (prodBadge) {
    if (spec.variety === 'GTT') {
      prodBadge.innerText = `GTT TRIGGER (${spec.product || 'DELIVERY'})`;
    } else {
      prodBadge.innerText = `${spec.product || 'DELIVERY'} (${spec.product === 'INTRADAY' ? 'MIS' : 'CNC'})`;
    }
  }

  if (titleEl) titleEl.innerText = spec.name || spec.symbol;
  if (subtitleEl) subtitleEl.innerText = `${spec.symbol} · ${spec.asset_type || 'STOCK'} · NSE`;

  let varietyText = `@ Market (~${formatINR(spec.price)})`;
  if (spec.variety === 'LIMIT') {
    varietyText = `@ ${formatINR(spec.price)} (Limit)`;
  } else if (spec.variety === 'STOP_LOSS') {
    varietyText = `@ Trg ${formatINR(spec.trigger_price)} / Lmt ${formatINR(spec.price)}`;
  } else if (spec.variety === 'GTT') {
    varietyText = `@ Trg ${formatINR(spec.trigger_price)}`;
  }
  if (qtyPriceEl) qtyPriceEl.innerText = `${spec.quantity} ${spec.quantity === 1 ? 'Share' : 'Shares'} ${varietyText}`;

  const grossVal = roundTo2(spec.quantity * spec.price);
  if (grossEl) grossEl.innerText = formatINR(grossVal);

  const marginRequired = (spec.product === 'INTRADAY') ? roundTo2(grossVal * 0.2) : grossVal;
  if (marginReqEl) marginReqEl.innerText = formatINR(marginRequired);

  const currentBal = getActiveAvailableCash();
  if (availCashEl) availCashEl.innerText = formatINR(currentBal);

  // Calculate live SEBI charges
  const charges = calculateClientCharges(spec.action, spec.product, spec.asset_type || 'STOCK', grossVal);

  if (document.getElementById('confirmChargeStt')) document.getElementById('confirmChargeStt').innerText = formatINR(charges.stt);
  if (document.getElementById('confirmChargeExchange')) document.getElementById('confirmChargeExchange').innerText = formatINR(charges.exchange);
  if (document.getElementById('confirmChargeSebi')) document.getElementById('confirmChargeSebi').innerText = formatINR(charges.sebi);
  if (document.getElementById('confirmChargeStamp')) document.getElementById('confirmChargeStamp').innerText = formatINR(charges.stamp);
  if (document.getElementById('confirmChargeGst')) document.getElementById('confirmChargeGst').innerText = formatINR(charges.gst);
  if (document.getElementById('confirmChargeTotal')) document.getElementById('confirmChargeTotal').innerText = formatINR(charges.total);
  if (chargesHeaderEl) chargesHeaderEl.innerText = formatINR(charges.total);

  let netTotal = grossVal;
  if (isBuy) {
    netTotal = roundTo2(grossVal + charges.total);
  } else {
    netTotal = Math.max(0, roundTo2(grossVal - charges.total));
  }
  if (netTotalEl) netTotalEl.innerText = formatINR(netTotal);

  if (isBuy && (marginRequired + charges.total) > currentBal) {
    if (errorEl) {
      errorEl.innerText = `Insufficient funds: Required ${formatINR(marginRequired + charges.total)} (Margin ${formatINR(marginRequired)} + Charges ${formatINR(charges.total)}), Available ${formatINR(currentBal)}`;
      errorEl.style.display = 'block';
    }
  }

  const submitBtn = document.getElementById('btnSubmitConfirmedOrder');
  if (submitBtn) {
    submitBtn.innerText = isBuy ? 'Place Buy Order →' : 'Place Sell Order →';
    submitBtn.className = `btn-confirm-execute ${isBuy ? 'buy' : 'sell'}`;
    submitBtn.disabled = false;
  }

  modal.classList.add('active');
}

function closeOrderConfirmModal() {
  const modal = document.getElementById('orderConfirmModal');
  if (modal) modal.classList.remove('active');
  const spec = pendingOrderSpec;
  pendingOrderSpec = null;
  if (spec && spec.origin === 'MODAL') {
    const tradeModal = document.getElementById('tradeModalOverlay');
    if (tradeModal) tradeModal.classList.add('active');
  } else if (spec && spec.origin === 'DRAWER') {
    const drawer = document.getElementById('mobileTradingDrawerOverlay');
    if (drawer) drawer.classList.add('active');
  }
}

function toggleConfirmChargesDetails() {
  const body = document.getElementById('confirmChargesDetailsBody');
  const arrow = document.getElementById('confirmChargesArrow');
  if (!body) return;
  const isHidden = (body.style.display === 'none' || !body.style.display);
  body.style.display = isHidden ? 'block' : 'none';
  if (arrow) arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
}

async function executeConfirmedOrder() {
  if (!pendingOrderSpec) return;
  const spec = pendingOrderSpec;
  const submitBtn = document.getElementById('btnSubmitConfirmedOrder');
  const errorEl = document.getElementById('confirmOrderError');

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner-small"></span> Placing Order...';
  }
  if (errorEl) {
    errorEl.style.display = 'none';
    errorEl.innerText = '';
  }

  try {
    let res, result;
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);

    if (spec.variety === 'GTT') {
      res = await fetch('/api/order/gtt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(uid ? { 'X-User-Id': uid } : {})
        },
        body: JSON.stringify({
          symbol: spec.symbol,
          name: spec.name || spec.symbol,
          action: spec.action,
          transaction_type: spec.action,
          product_type: spec.product || 'DELIVERY',
          quantity: spec.quantity,
          trigger_price: spec.trigger_price,
          target_price: spec.limit_price || spec.trigger_price,
          limit_price: spec.limit_price || spec.trigger_price
        })
      });
      result = await res.json();
    } else {
      res = await fetch('/api/order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(uid ? { 'X-User-Id': uid } : {})
        },
        body: JSON.stringify({
          symbol: spec.symbol,
          name: spec.name,
          asset_type: spec.asset_type || 'STOCK',
          order_type: spec.action,
          product_type: spec.product,
          quantity: spec.quantity,
          price: spec.price,
          order_variety: spec.variety,
          limit_price: spec.limit_price,
          trigger_price: spec.trigger_price
        })
      });
      result = await res.json();
    }

    if (!res.ok || !result.success) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = spec.action === 'BUY' ? 'Place Buy Order →' : 'Place Sell Order →';
        submitBtn.className = `btn-confirm-execute ${spec.action === 'BUY' ? 'buy' : 'sell'}`;
      }
      const errMsg = result.detail || result.error || 'Trade execution failed';
      if (errorEl) {
        errorEl.innerText = errMsg;
        errorEl.style.display = 'block';
      }
      showToast(errMsg, true);
      return;
    }

    // Success: Close confirmation modal
    closeOrderConfirmModal();

    // Await authoritative backend reflection
    await Promise.allSettled([
      fetchAccount(),
      fetchPortfolio(true),
      fetchPositions(true),
      fetchOrders()
    ]);

    if (currentUser && state.account && state.account.balance !== undefined) {
      currentUser.balance = state.account.balance;
      try {
        localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
      } catch (e) {}
    }

    if (currentPageAsset) {
      updatePageAvailableHolding(currentPageAsset.symbol);
    }
    recalcPageMargin();
    closeMobileTradeDrawer();

    if (spec.variety === 'GTT') {
      loadGttOrders();
    }

    const confirmedBalance = (result.balance !== undefined)
      ? result.balance
      : (state.account ? state.account.balance : undefined);

    openOrderSuccessModal({
      symbol: spec.symbol,
      name: spec.name,
      action: spec.action,
      product: spec.product,
      quantity: spec.quantity,
      price: spec.price,
      total: spec.quantity * spec.price,
      charges: result.charges,
      net_amount: result.net_amount,
      status: result.status,
      balance: confirmedBalance
    });
    showToast(result.message || `${spec.action} order placed successfully!`);

  } catch (err) {
    console.error('executeConfirmedOrder error:', err);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerText = spec.action === 'BUY' ? 'Place Buy Order →' : 'Place Sell Order →';
      submitBtn.className = `btn-confirm-execute ${spec.action === 'BUY' ? 'buy' : 'sell'}`;
    }
    if (errorEl) {
      errorEl.innerText = 'Failed to connect to trade server';
      errorEl.style.display = 'block';
    }
    showToast('Failed to connect to trade server', true);
  }
}

/* =======================================================
   1. GTT & TRIGGER ORDERS ENGINE
   ======================================================= */
async function loadGttOrders() {
  if (isGuest()) return;
  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const res = await fetch(`/api/orders/gtt?user_id=${encodeURIComponent(uid || '')}`, {
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    const orders = await res.json();
    const countEl = document.getElementById('gttOrdersCount');
    if (countEl) countEl.innerText = Array.isArray(orders) ? orders.length : 0;

    const tbody = document.getElementById('gttOrdersTableBody');
    const mobList = document.getElementById('gttOrdersMobileList');

    if (!orders || !Array.isArray(orders) || orders.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3rem;">No active GTT or Stop-Loss triggers.</td></tr>';
      if (mobList) mobList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No active triggers.</div>';
      return;
    }

    if (tbody) {
      tbody.innerHTML = orders.map(o => {
        const trigId = o.id ?? o.order_id ?? '--';
        const sym = (o.symbol || '').replace('.NS', '');
        const action = (o.action || o.transaction_type || 'BUY').toUpperCase();
        const trigPrice = Number(o.trigger_price) || 0;
        const targetPrice = Number(o.target_price ?? o.limit_price ?? o.trigger_price) || 0;
        const dateStr = o.created_at ? new Date(o.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '--';

        return `
          <tr>
            <td><code style="font-size: 0.8rem; color: var(--text-muted);">#${trigId}</code></td>
            <td><strong>${sym}</strong></td>
            <td><span class="${action === 'BUY' ? 'badge-positive' : 'badge-negative'}">${action}</span></td>
            <td><strong>${formatINR(trigPrice)}</strong></td>
            <td>${formatINR(targetPrice)}</td>
            <td>${o.quantity}</td>
            <td>${dateStr}</td>
            <td><span class="pill-btn" style="color: var(--brand-cyan); font-size: 0.72rem;">${o.status}</span></td>
            <td style="text-align: right;">
              <button class="btn-cancel-small" onclick="cancelGttOrder(${trigId})">Cancel</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    if (mobList) {
      mobList.innerHTML = orders.map(o => {
        const trigId = o.id ?? o.order_id ?? '--';
        const sym = (o.symbol || '').replace('.NS', '');
        const action = (o.action || o.transaction_type || 'BUY').toUpperCase();
        const trigPrice = Number(o.trigger_price) || 0;
        const targetPrice = Number(o.target_price ?? o.limit_price ?? o.trigger_price) || 0;

        return `
          <div class="mobile-order-card">
            <div class="mob-order-header">
              <strong>${sym}</strong>
              <span class="${action === 'BUY' ? 'badge-positive' : 'badge-negative'}">${action}</span>
            </div>
            <div class="mob-order-row">
              <span>Trigger Price</span><strong>${formatINR(trigPrice)}</strong>
            </div>
            <div class="mob-order-row">
              <span>Limit Price</span><span>${formatINR(targetPrice)}</span>
            </div>
            <div class="mob-order-row">
              <span>Quantity</span><span>${o.quantity}</span>
            </div>
            <div class="mob-order-row">
              <span>Status</span><span class="pill-btn" style="color: var(--brand-cyan);">${o.status}</span>
            </div>
            <div style="margin-top: 0.75rem; text-align: right;">
              <button class="btn-cancel-small" onclick="cancelGttOrder(${trigId})">Cancel Trigger</button>
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Failed to load GTT orders:', err);
  }
}

async function cancelGttOrder(orderId) {
  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const res = await fetch(`/api/order/gtt/${orderId}?user_id=${encodeURIComponent(uid || '')}`, {
      method: 'DELETE',
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    const d = await res.json();
    if (d.success) {
      showToast(d.message || 'Trigger cancelled');
      loadGttOrders();
    } else {
      showToast(d.error || 'Failed to cancel trigger', true);
    }
  } catch (err) {
    showToast('Failed to cancel trigger', true);
  }
}


/* =======================================================
   2. F&O (FUTURES & OPTIONS) OPTION CHAIN ENGINE
   ======================================================= */
let currentFoUnderlying = 'NIFTY';
let currentOptionTrade = null;

function switchFoUnderlying(sym) {
  currentFoUnderlying = sym;
  const btnNifty = document.getElementById('btnFoNifty');
  const btnBankNifty = document.getElementById('btnFoBankNifty');
  if (btnNifty) btnNifty.classList.toggle('active', sym === 'NIFTY');
  if (btnBankNifty) btnBankNifty.classList.toggle('active', sym === 'BANKNIFTY');
  fetchOptionChain();
}

async function fetchOptionChain() {
  const tbody = document.getElementById('optionChainTableBody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 3rem;">Calculating Black-Scholes Greeks & Option Matrix...</td></tr>';

  try {
    const res = await fetch(`/api/fo/option-chain?symbol=${encodeURIComponent(currentFoUnderlying)}`);
    const data = await res.json();
    const strikeList = data.strikes || data.chain;
    if (!res.ok || !strikeList || !Array.isArray(strikeList) || strikeList.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Option chain data temporarily unavailable.</td></tr>';
      return;
    }

    const spotEl = document.getElementById('foSpotPrice');
    const pcrEl = document.getElementById('foPcrVal');
    const pcrSent = document.getElementById('foPcrSentiment');
    if (spotEl) spotEl.innerText = formatINR(data.spot_price);
    if (pcrEl) pcrEl.innerText = data.pcr ? data.pcr.toFixed(2) : '1.00';
    if (pcrSent) {
      const pcr = data.pcr || 1.0;
      pcrSent.innerText = pcr > 1.2 ? 'Bullish' : (pcr < 0.8 ? 'Bearish' : 'Neutral');
      pcrSent.className = pcr > 1.2 ? 'badge-positive' : (pcr < 0.8 ? 'badge-negative' : 'pill-btn');
    }

    renderOptionChain(data);
  } catch (err) {
    console.error('Failed to fetch option chain:', err);
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Option chain data temporarily unavailable.</td></tr>';
  }
}

function renderOptionChain(data) {
  const tbody = document.getElementById('optionChainTableBody');
  if (!tbody) return;

  const lotSize = data.lot_size || 25;
  const strikes = data.strikes || data.chain || [];

  tbody.innerHTML = strikes.map(s => {
    const isAtm = s.is_atm;
    const atmClass = isAtm ? 'atm-strike-row' : '';
    const atmBadge = isAtm ? '<span class="atm-badge">ATM</span>' : '';
    const ce = s.ce || s.call || {};
    const pe = s.pe || s.put || {};
    const ceLtp = Number(ce.ltp) || 0;
    const peLtp = Number(pe.ltp) || 0;
    const ceOi = Number(ce.oi) || 0;
    const peOi = Number(pe.oi) || 0;

    return `
      <tr class="${atmClass}">
        <!-- CALL SIDE -->
        <td class="fo-oi-col">${(ceOi / 100000).toFixed(1)}L</td>
        <td class="fo-iv-col">${ce.iv ?? 13}%</td>
        <td class="fo-ltp-col call">
          <button class="opt-trade-btn call" onclick="openOptionBuyModal('${data.underlying}', ${s.strike}, 'CE', ${ceLtp}, ${ce.iv ?? 13}, ${lotSize})">
            <strong>${formatINR(ceLtp)}</strong>
            <span class="delta-sub">Δ ${ce.delta ?? 0.5}</span>
          </button>
        </td>

        <!-- STRIKE CENTER -->
        <td class="fo-strike-col">
          <span class="strike-num">${Number(s.strike).toLocaleString('en-IN')}</span>
          ${atmBadge}
        </td>

        <!-- PUT SIDE -->
        <td class="fo-ltp-col put">
          <button class="opt-trade-btn put" onclick="openOptionBuyModal('${data.underlying}', ${s.strike}, 'PE', ${peLtp}, ${pe.iv ?? 13}, ${lotSize})">
            <strong>${formatINR(peLtp)}</strong>
            <span class="delta-sub">Δ ${pe.delta ?? -0.5}</span>
          </button>
        </td>
        <td class="fo-iv-col">${pe.iv ?? 13}%</td>
        <td class="fo-oi-col">${(peOi / 100000).toFixed(1)}L</td>
      </tr>
    `;
  }).join('');
}

function openOptionBuyModal(underlying, strike, optType, ltp, iv, lotSize) {
  if (isGuest()) {
    showToast('Please create an account to trade options with your ₹10,00,000 virtual balance!', false);
    navigateTo('/onboarding');
    return;
  }

  currentOptionTrade = {
    underlying,
    strike,
    optType,
    ltp,
    iv,
    lotSize: lotSize || (underlying === 'BANKNIFTY' ? 15 : 25),
    action: 'BUY',
    lots: 1
  };

  const titleEl = document.getElementById('optModalTitle');
  const subEl = document.getElementById('optModalSubtitle');
  const ltpEl = document.getElementById('optModalLtp');
  const lotEl = document.getElementById('optModalLotSize');
  const ivEl = document.getElementById('optModalIv');

  if (titleEl) titleEl.innerText = `${underlying} ${strike} ${optType}`;
  if (subEl) subEl.innerText = `Weekly Expiry • ${optType === 'CE' ? 'Call Option' : 'Put Option'}`;
  if (ltpEl) ltpEl.innerText = formatINR(ltp);
  if (lotEl) lotEl.innerText = `${currentOptionTrade.lotSize} shares / lot`;
  if (ivEl) ivEl.innerText = `${iv}%`;

  document.getElementById('optModalLots').value = 1;
  setOptionAction('BUY');
  recalcOptionPremium();

  const modal = document.getElementById('optionBuyModal');
  if (modal) modal.style.display = 'flex';
}

function closeOptionBuyModal() {
  const modal = document.getElementById('optionBuyModal');
  if (modal) modal.style.display = 'none';
  currentOptionTrade = null;
}

function setOptionAction(action) {
  if (!currentOptionTrade) return;
  currentOptionTrade.action = action;
  const buyBtn = document.getElementById('optBtnBuy');
  const sellBtn = document.getElementById('optBtnSell');
  const execBtn = document.getElementById('optExecuteBtn');
  if (buyBtn) buyBtn.className = `trade-tab-btn ${action === 'BUY' ? 'active buy' : ''}`;
  if (sellBtn) sellBtn.className = `trade-tab-btn ${action === 'SELL' ? 'active sell' : ''}`;
  if (execBtn) {
    execBtn.className = `btn-trade-execute ${action.toLowerCase()}`;
    execBtn.innerText = `${action} ${currentOptionTrade.underlying} ${currentOptionTrade.strike} ${currentOptionTrade.optType}`;
  }
}

function stepOptionLots(delta) {
  if (!currentOptionTrade) return;
  const input = document.getElementById('optModalLots');
  let val = parseInt(input.value || '1', 10) + delta;
  if (val < 1) val = 1;
  input.value = val;
  currentOptionTrade.lots = val;
  recalcOptionPremium();
}

function setOptionLots(lots) {
  if (!currentOptionTrade) return;
  document.getElementById('optModalLots').value = lots;
  currentOptionTrade.lots = lots;
  recalcOptionPremium();
}

function recalcOptionPremium() {
  if (!currentOptionTrade) return;
  const lots = parseInt(document.getElementById('optModalLots').value || '1', 10);
  currentOptionTrade.lots = lots;
  const totalQty = lots * currentOptionTrade.lotSize;
  const totalPremium = totalQty * currentOptionTrade.ltp;

  const qtyEl = document.getElementById('optModalTotalQty');
  const premEl = document.getElementById('optModalTotalPremium');
  const cashEl = document.getElementById('optModalAvailableCash');

  if (qtyEl) qtyEl.innerText = `${totalQty} Qty (${lots} ${lots === 1 ? 'Lot' : 'Lots'})`;
  if (premEl) premEl.innerText = formatINR(totalPremium);
  const bal = getActiveAvailableCash();
  if (cashEl) cashEl.innerText = formatINR(bal);
}

async function submitOptionTrade() {
  if (!currentOptionTrade) return;
  const lots = parseInt(document.getElementById('optModalLots').value || '1', 10);
  const totalQty = lots * currentOptionTrade.lotSize;
  const symbol = `${currentOptionTrade.underlying}_${currentOptionTrade.strike}_${currentOptionTrade.optType}`;

  const execBtn = document.getElementById('optExecuteBtn');
  const originalHtml = execBtn ? execBtn.innerHTML : '';
  if (execBtn) {
    execBtn.disabled = true;
    execBtn.innerHTML = '<span class="btn-spinner"></span> <span>Executing Option Trade...</span>';
  }

  try {
    const res = await fetch('/api/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: symbol,
        name: `${currentOptionTrade.underlying} ${currentOptionTrade.strike} ${currentOptionTrade.optType}`,
        asset_type: 'OPTION',
        order_type: currentOptionTrade.action,
        product_type: 'INTRADAY',
        quantity: totalQty,
        price: currentOptionTrade.ltp,
        order_variety: 'MARKET'
      })
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      if (execBtn) {
        execBtn.disabled = false;
        execBtn.innerHTML = originalHtml;
      }
      showToast(result.detail || result.error || 'Option execution failed', true);
      return;
    }

    // Await authoritative backend reflection
    await Promise.allSettled([
      fetchAccount(),
      fetchPositions(true),
      fetchOrders()
    ]);

    if (currentUser && state.account && state.account.balance !== undefined) {
      currentUser.balance = state.account.balance;
      try {
        localStorage.setItem('stoxify_cached_user', JSON.stringify(currentUser));
      } catch (e) {}
    }

    closeOptionBuyModal();
    showToast(`${currentOptionTrade.action} ${lots} lot(s) executed at ${formatINR(currentOptionTrade.ltp)}!`);
  } catch (err) {
    showToast('Failed to execute option trade', true);
  } finally {
    if (execBtn) {
      execBtn.disabled = false;
      execBtn.innerHTML = originalHtml;
    }
  }
}


/* =======================================================
   3. IPO HUB & ASBA LOT BIDDING ENGINE
   ======================================================= */
let allIpos = [];
let activeIpoFilter = 'ALL';
let currentIpoModalData = null;

async function fetchIpos() {
  const grid = document.getElementById('ipoGrid');
  if (grid) grid.innerHTML = '<div style="color: var(--text-muted); padding: 2rem;">Loading real Indian IPOs...</div>';

  try {
    const res = await fetch('/api/ipo/list');
    allIpos = await res.json();
    renderIpos(activeIpoFilter);
  } catch (err) {
    if (grid) grid.innerHTML = '<div style="color: var(--accent-red); padding: 2rem;">Failed to load IPOs</div>';
  }
}

async function filterIpos(filter, btn) {
  activeIpoFilter = filter;
  if (btn) {
    document.querySelectorAll('#explore-ipo-container .pill-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
  if (filter === 'APPLICATIONS') {
    await renderIpoApplications();
  } else {
    renderIpos(filter);
  }
}

async function renderIpoApplications() {
  const grid = document.getElementById('ipoGrid');
  if (!grid) return;

  if (isGuest()) {
    grid.innerHTML = '<div style="color: var(--text-muted); padding: 3rem; text-align: center;">Please <a href="javascript:void(0)" onclick="navigateTo(\'/onboarding\')" style="color: var(--brand-cyan); text-decoration: underline;">create an account</a> to view your IPO applications.</div>';
    return;
  }

  grid.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">Loading your IPO applications...</div>';

  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const res = await fetch(`/api/ipo/applications?user_id=${encodeURIComponent(uid || '')}`, {
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    const apps = await res.json();

    if (!apps || !Array.isArray(apps) || apps.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1.5rem; background: rgba(255,255,255,0.02); border: 1px dashed var(--border-subtle); border-radius: 16px;">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
          <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.4rem;">No IPO Applications Found</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem; max-width: 420px; margin: 0 auto 1.25rem;">You have not applied for any mainline or SME IPOs yet. Check the Open and Upcoming tabs to place your first bid using virtual ASBA funds.</p>
          <button class="btn-primary" onclick="filterIpos('ALL', document.querySelector('#explore-ipo-container .pill-btn'))">Explore Live IPOs</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = apps.map(b => {
      const isApplied = (b.status || '').toUpperCase() === 'APPLIED';
      const statusBadge = isApplied ? 'badge-positive' : 'badge-neutral';
      const totalShares = (b.lots || 1) * (b.shares || 1);
      const safeName = (b.ipo_name || 'IPO').replace(/'/g, "\\'");

      return `
        <div class="ipo-card">
          <div class="ipo-card-header">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
              <div class="card-avatar" style="background: rgba(14, 165, 233, 0.15); color: var(--brand-cyan); font-weight: 800;">
                ${(b.ipo_name || 'IP').slice(0, 2).toUpperCase()}
              </div>
              <div>
                <h4 class="ipo-card-title">${b.ipo_name}</h4>
                <span class="sub-text">UPI: ${b.upi_id || 'ASBA Mandate'}</span>
              </div>
            </div>
            <span class="${statusBadge}">${b.status}</span>
          </div>

          <div class="ipo-metrics-grid">
            <div class="ipo-metric-item">
              <span class="label">Bidding Lots</span>
              <strong>${b.lots} ${b.lots === 1 ? 'Lot' : 'Lots'} (${totalShares} Shares)</strong>
            </div>
            <div class="ipo-metric-item">
              <span class="label">Bid Price</span>
              <strong>₹${b.bid_price}</strong>
            </div>
            <div class="ipo-metric-item">
              <span class="label">Amount Blocked (ASBA)</span>
              <strong style="color: var(--brand-cyan);">${formatINR(b.amount_blocked)}</strong>
            </div>
            <div class="ipo-metric-item">
              <span class="label">Application Date</span>
              <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">${b.created_at ? new Date(b.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : '--'}</span>
            </div>
          </div>

          <div class="ipo-card-actions" style="margin-top: 1rem;">
            ${isApplied ? `
              <button class="btn-cancel-small" style="width: 100%; padding: 0.7rem; justify-content: center; font-size: 0.85rem;" onclick="withdrawIpoBid(${b.id}, '${safeName}')">
                Withdraw Bid & Unblock ₹${(b.amount_blocked || 0).toLocaleString('en-IN')}
              </button>
            ` : `
              <div style="font-size: 0.8rem; color: var(--text-muted); text-align: center; width: 100%; padding: 0.4rem;">Application ${b.status}</div>
            `}
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Failed to load IPO applications:', err);
    grid.innerHTML = '<div style="color: var(--danger-red); padding: 2rem;">Failed to load applications.</div>';
  }
}

async function withdrawIpoBid(bidId, ipoName) {
  if (!confirm(`Are you sure you want to withdraw your application for ${ipoName}? Blocked ASBA funds will be immediately released to your trading cash.`)) {
    return;
  }
  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const res = await fetch(`/api/ipo/bid/${bidId}?user_id=${encodeURIComponent(uid || '')}`, {
      method: 'DELETE',
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'IPO bid withdrawn successfully');
      await fetchAccount();
      await renderIpoApplications();
    } else {
      showToast(data.error || 'Failed to withdraw IPO bid', true);
    }
  } catch (err) {
    showToast('Failed to withdraw IPO bid', true);
  }
}

function renderIpos(filter) {
  const grid = document.getElementById('ipoGrid');
  if (!grid) return;

  const filtered = (allIpos || []).filter(item => {
    if (filter === 'ALL') return true;
    if (filter === 'LISTED') return item.status === 'LISTED';
    if (filter === 'UPCOMING') return item.status === 'UPCOMING' || item.status === 'OPEN';
    return true;
  });

  if (filtered.length === 0) {
    grid.innerHTML = '<div style="color: var(--text-muted); padding: 2rem;">No IPOs found in this category.</div>';
    return;
  }

  grid.innerHTML = filtered.map(ipo => {
    const isListed = ipo.status === 'LISTED';
    const isOpen = ipo.status === 'OPEN';
    const minInvestment = ipo.max_price * ipo.lot_size;

    const subTimes = ipo.subscription_times || (typeof ipo.subscription === 'object' ? (ipo.subscription.overall || '1.0x') : '1.0x');
    const gmpDisplay = typeof ipo.gmp === 'string' 
      ? `${ipo.gmp} (${ipo.gmp_pct > 0 ? '+' : ''}${ipo.gmp_pct}%)`
      : (ipo.gmp ? `+₹${ipo.gmp} (${ipo.gmp_pct}%)` : '--');
    const categoryDisplay = ipo.category || ipo.sector || 'Mainline';

    return `
      <div class="ipo-card">
        <div class="ipo-card-header">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div class="card-avatar" style="background: rgba(147, 51, 234, 0.15); color: #a855f7;">${(ipo.symbol || 'IP').slice(0, 2)}</div>
            <div>
              <h4 class="ipo-card-title">${ipo.name}</h4>
              <span class="sub-text">${categoryDisplay} • ${ipo.issue_size || ''}</span>
            </div>
          </div>
          <span class="pill-btn ${isOpen ? 'badge-positive' : ''}">${ipo.status}</span>
        </div>

        <div class="ipo-metrics-grid">
          <div class="ipo-metric-item">
            <span class="label">Price Band</span>
            <strong>₹${ipo.min_price} - ₹${ipo.max_price}</strong>
          </div>
          <div class="ipo-metric-item">
            <span class="label">Lot Size</span>
            <strong>${ipo.lot_size} Shares</strong>
          </div>
          <div class="ipo-metric-item">
            <span class="label">Min. Investment</span>
            <strong>${formatINR(minInvestment)}</strong>
          </div>
          <div class="ipo-metric-item">
            <span class="label">Estimated GMP</span>
            <strong style="color: var(--accent-green);">${gmpDisplay}</strong>
          </div>
        </div>

        <div class="ipo-sub-status">
          <span>Subscription: <strong>${subTimes.includes('x') ? subTimes : subTimes + 'x'}</strong></span>
          <span style="color: var(--text-muted); font-size: 0.75rem;">Closes: ${ipo.close_date || '--'}</span>
        </div>

        <div class="ipo-card-actions">
          ${isOpen 
            ? `<button class="btn-primary" style="width: 100%; justify-content: center;" onclick="openIpoBidModal('${ipo.id}')">Apply Now (ASBA)</button>`
            : isListed
            ? `<button class="btn-subtle" style="width: 100%; justify-content: center;" onclick="showToast('${ipo.name} listed at ₹${ipo.listing_price || ipo.max_price} (+${ipo.gmp_pct}%)')">View Listing Details</button>`
            : `<button class="btn-subtle" style="width: 100%; justify-content: center;" onclick="showToast('Alert set for ${ipo.name}!')">Notify on Open</button>`
          }
        </div>
      </div>
    `;
  }).join('');
}

function openIpoBidModal(ipoId) {
  if (isGuest()) {
    showToast('Please sign in to bid for IPOs using virtual funds!', false);
    navigateTo('/onboarding');
    return;
  }

  const ipo = (allIpos || []).find(i => i.id === ipoId);
  if (!ipo) return;
  currentIpoModalData = { ...ipo, lots: 1 };

  document.getElementById('ipoModalTitle').innerText = ipo.name;
  document.getElementById('ipoModalCategory').innerText = `${ipo.category} • Lot: ${ipo.lot_size} Shares`;
  document.getElementById('ipoModalPriceBand').innerText = `₹${ipo.min_price} - ₹${ipo.max_price}`;
  document.getElementById('ipoModalLotSize').innerText = `${ipo.lot_size} shares`;
  document.getElementById('ipoModalGmp').innerText = `+₹${ipo.gmp} (+${ipo.gmp_pct}%)`;

  document.getElementById('ipoModalLots').value = 1;
  recalcIpoAmount();

  const modal = document.getElementById('ipoBidModal');
  if (modal) modal.style.display = 'flex';
}

function closeIpoBidModal() {
  const modal = document.getElementById('ipoBidModal');
  if (modal) modal.style.display = 'none';
  currentIpoModalData = null;
}

function stepIpoLots(delta) {
  if (!currentIpoModalData) return;
  const input = document.getElementById('ipoModalLots');
  let val = parseInt(input.value || '1', 10) + delta;
  if (val < 1) val = 1;
  if (val > 13) val = 13;
  input.value = val;
  currentIpoModalData.lots = val;
  recalcIpoAmount();
}

function recalcIpoAmount() {
  if (!currentIpoModalData) return;
  const lots = parseInt(document.getElementById('ipoModalLots').value || '1', 10);
  currentIpoModalData.lots = lots;
  const totalShares = lots * currentIpoModalData.lot_size;
  const totalAmount = totalShares * currentIpoModalData.max_price;

  document.getElementById('ipoModalTotalShares').innerText = `${totalShares} Shares (${lots} ${lots === 1 ? 'Lot' : 'Lots'})`;
  document.getElementById('ipoModalTotalAmount').innerText = formatINR(totalAmount);
  const bal = getActiveAvailableCash();
  document.getElementById('ipoModalAvailableCash').innerText = formatINR(bal);
}

async function submitIpoApplication() {
  if (!currentIpoModalData) return;
  const lots = parseInt(document.getElementById('ipoModalLots').value || '1', 10);
  const upiId = document.getElementById('ipoModalUpi').value.trim() || 'trader@okhdfcbank';

  try {
    const res = await fetch('/api/ipo/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        // IPOApplyRequest requires ipo_name and shares; omitting them made every
        // bid fail validation. `shares` is the lot size (backend multiplies it).
        ipo_id: currentIpoModalData.id,
        ipo_name: currentIpoModalData.name,
        lots: lots,
        shares: currentIpoModalData.lot_size,
        bid_price: currentIpoModalData.max_price,
        upi_id: upiId
      })
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'IPO application failed', true);
      return;
    }

    showToast(result.message || 'IPO application submitted successfully!');
    closeIpoBidModal();
    await fetchAccount();
  } catch (err) {
    showToast('Failed to apply for IPO', true);
  }
}


/* =======================================================
   4. MUTUAL FUNDS & SIP RECURRING ENGINE
   ======================================================= */
function onSipSliderChange() {
  const monthly = parseFloat(document.getElementById('sipSliderMonthly').value || '5000');
  const rate = parseFloat(document.getElementById('sipSliderReturn').value || '12');
  const years = parseFloat(document.getElementById('sipSliderYears').value || '5');

  const monthlyValEl = document.getElementById('sipCalcMonthlyVal');
  const rateValEl = document.getElementById('sipCalcReturnVal');
  const yearsValEl = document.getElementById('sipCalcYearsVal');

  if (monthlyValEl) monthlyValEl.innerText = monthly.toLocaleString('en-IN');
  if (rateValEl) rateValEl.innerText = rate;
  if (yearsValEl) yearsValEl.innerText = years;

  const months = years * 12;
  const i = (rate / 100) / 12;
  const fv = monthly * ((Math.pow(1 + i, months) - 1) / i) * (1 + i);
  const invested = monthly * months;
  const gains = fv - invested;

  const invEl = document.getElementById('sipResInvested');
  const gainEl = document.getElementById('sipResGains');
  const totalEl = document.getElementById('sipResTotal');

  if (invEl) invEl.innerText = formatINR(invested);
  if (gainEl) gainEl.innerText = formatINR(gains);
  if (totalEl) totalEl.innerText = formatINR(fv);
}

function openSipModalForCurrentAsset() {
  if (!currentPageAsset) return;
  openSipModal(currentPageAsset.symbol, currentPageAsset.name);
}

function openSipModal(symbol, name) {
  if (isGuest()) {
    showToast('Please create an account to schedule automated SIPs!', false);
    navigateTo('/onboarding');
    return;
  }

  const cleanName = name || symbol;
  const monthlyVal = document.getElementById('sipSliderMonthly') ? document.getElementById('sipSliderMonthly').value : '5000';

  const fundInput = document.getElementById('sipModalFundName');
  const amtInput = document.getElementById('sipModalAmount');
  if (fundInput) fundInput.value = `${cleanName} (${symbol})`;
  if (amtInput) amtInput.value = monthlyVal;

  const modal = document.getElementById('sipScheduleModal');
  if (modal) modal.style.display = 'flex';
}

function closeSipModal() {
  const modal = document.getElementById('sipScheduleModal');
  if (modal) modal.style.display = 'none';
}

async function submitSipSchedule() {
  const fundInput = document.getElementById('sipModalFundName').value;
  const amount = parseFloat(document.getElementById('sipModalAmount').value || '5000');
  const day = parseInt(document.getElementById('sipModalDay').value || '5', 10);

  if (!amount || amount < 500) {
    showToast('Minimum SIP installment is ₹500', true);
    return;
  }

  const sym = currentPageAsset ? currentPageAsset.symbol : (fundInput.split('(')[1]?.replace(')', '') || fundInput);
  // The API model is SIPRequest(fund_id, fund_name, monthly_amount, sip_day).
  // Sending symbol/amount/installment_day made Pydantic reject every request.
  const fundName = (currentPageAsset && currentPageAsset.name)
    || fundInput.replace(/\s*\([^)]*\)\s*$/, '').trim()
    || 'Mutual Fund';

  try {
    const res = await fetch('/api/mf/sip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fund_id: String(sym || fundInput).trim(),
        fund_name: fundName,
        monthly_amount: amount,
        sip_day: day
      })
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'Failed to schedule SIP', true);
      return;
    }

    showToast(`Monthly SIP of ${formatINR(amount)} scheduled on the ${day}th of every month!`);
    closeSipModal();
    loadActiveSips();
  } catch (err) {
    showToast('Failed to schedule SIP', true);
  }
}

async function loadActiveSips() {
  if (isGuest()) return;
  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const res = await fetch(`/api/mf/sips?user_id=${encodeURIComponent(uid || '')}`, {
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    const sips = await res.json();

    const tbody = document.getElementById('sipsTableBody');
    const mobList = document.getElementById('sipsMobileList');

    if (!sips || !Array.isArray(sips) || sips.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 3rem;">No active SIP schedules.</td></tr>';
      if (mobList) mobList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No active SIP schedules.</div>';
      return;
    }

    if (tbody) {
      tbody.innerHTML = sips.map(s => {
        const fundName = s.fund_name || s.symbol || s.fund_id || 'Mutual Fund';
        const amount = s.monthly_amount ?? s.amount ?? 0;
        const sipDay = s.sip_day ?? s.installment_day ?? 5;
        const nextDate = s.next_installment_date || s.next_trigger_date || '--';
        const sipId = s.id ?? s.sip_id;
        const status = s.status || 'ACTIVE';

        const isActive = status === 'ACTIVE';
        return `
          <tr>
            <td><strong>${fundName}</strong></td>
            <td><strong style="color: var(--accent-green);">${formatINR(amount)}</strong></td>
            <td>${sipDay}th of month</td>
            <td>${nextDate}</td>
            <td><span class="${isActive ? 'badge-positive' : 'badge-neutral'}">${status}</span></td>
            <td style="text-align: right;">
              ${isActive ? `<button class="btn-cancel-small" onclick="cancelSip(${sipId})">Stop SIP</button>` : '<span style="font-size: 0.8rem; color: var(--text-muted);">Stopped</span>'}
            </td>
          </tr>
        `;
      }).join('');
    }

    if (mobList) {
      mobList.innerHTML = sips.map(s => {
        const fundName = s.fund_name || s.symbol || s.fund_id || 'Mutual Fund';
        const amount = s.monthly_amount ?? s.amount ?? 0;
        const sipDay = s.sip_day ?? s.installment_day ?? 5;
        const nextDate = s.next_installment_date || s.next_trigger_date || '--';
        const sipId = s.id ?? s.sip_id;
        const status = s.status || 'ACTIVE';
        const isActive = status === 'ACTIVE';

        return `
          <div class="mobile-order-card">
            <div class="mob-order-header">
              <strong>${fundName}</strong>
              <span class="${isActive ? 'badge-positive' : 'badge-neutral'}">${status}</span>
            </div>
            <div class="mob-order-row">
              <span>Monthly Amount</span><strong style="color: var(--accent-green);">${formatINR(amount)}</strong>
            </div>
            <div class="mob-order-row">
              <span>Debit Date</span><span>${sipDay}th Monthly</span>
            </div>
            <div class="mob-order-row">
              <span>Next Execution</span><span>${nextDate}</span>
            </div>
            <div style="margin-top: 0.75rem; text-align: right;">
              ${isActive ? `<button class="btn-cancel-small" onclick="cancelSip(${sipId})">Stop SIP</button>` : '<span style="font-size: 0.8rem; color: var(--text-muted);">Stopped</span>'}
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Failed to load SIPs:', err);
  }
}

async function cancelSip(sipId) {
  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const res = await fetch(`/api/mf/sip/${sipId}?user_id=${encodeURIComponent(uid || '')}`, {
      method: 'DELETE',
      headers: uid ? { 'X-User-Id': uid } : {}
    });
    const d = await res.json();
    if (d.success) {
      showToast('SIP cancelled successfully');
      loadActiveSips();
    } else {
      showToast(d.error || 'Failed to cancel SIP', true);
    }
  } catch (err) {
    showToast('Failed to cancel SIP', true);
  }
}


/* =======================================================
   5. PORTFOLIO ANALYTICS & BUDGET 2024 CAPITAL GAINS TAX
   ======================================================= */
async function loadPortfolioAnalytics() {
  if (isGuest()) return;
  try {
    const uid = localStorage.getItem('stoxify_user_id') || (currentUser ? currentUser.user_id : null);
    const authHeaders = uid ? { 'X-User-Id': uid } : {};

    // 1. Sector Allocation
    const secRes = await fetch(`/api/analytics/sector-allocation?user_id=${encodeURIComponent(uid || '')}`, { headers: authHeaders });
    const secData = await secRes.json();
    const secContainer = document.getElementById('sectorAllocationContainer');

    if (secContainer && Array.isArray(secData) && secData.length > 0) {
      const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#06b6d4', '#14b8a6'];
      secContainer.innerHTML = `
        <div class="sector-bar-wrapper">
          <div class="sector-stacked-bar">
            ${secData.map((s, idx) => `
              <div class="sector-segment" style="width: ${s.weight_pct}%; background: ${colors[idx % colors.length]};" title="${s.sector}: ${s.weight_pct}%"></div>
            `).join('')}
          </div>
          <div class="sector-legend-grid">
            ${secData.map((s, idx) => `
              <div class="sector-legend-item">
                <span class="legend-dot" style="background: ${colors[idx % colors.length]};"></span>
                <span class="legend-name">${s.sector}</span>
                <strong class="legend-val">${s.weight_pct}% (${formatINR(s.value)})</strong>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    // 2. Budget 2024 Tax Report
    const taxRes = await fetch(`/api/analytics/tax-report?user_id=${encodeURIComponent(uid || '')}`, { headers: authHeaders });
    const taxData = await taxRes.json();
    
    // NOTE: the element ids below are the ones actually present in index.html.
    // They previously read taxStcgRealized/taxStcgPayable/taxLtcgRealized/
    // taxLtcgPayable, which do not exist, so the whole tax card stayed at ₹0.00.
    const stcgRealized = document.getElementById('taxStcgGain');
    const stcgPayable = document.getElementById('taxStcgLiability');
    const ltcgRealized = document.getElementById('taxLtcgGain');
    const ltcgTaxable = document.getElementById('taxLtcgTaxable');
    const ltcgPayable = document.getElementById('taxLtcgLiability');
    const totalLiability = document.getElementById('taxTotalLiability');

    const sRealized = taxData.stcg_realized_gain ?? taxData.net_stcg ?? 0;
    const sPayable = taxData.stcg_tax_payable ?? taxData.stcg_tax ?? 0;
    const lRealized = taxData.ltcg_realized_gain ?? taxData.net_ltcg ?? 0;
    const lTaxable = taxData.ltcg_taxable_gain ?? taxData.taxable_ltcg ?? 0;
    const lPayable = taxData.ltcg_tax_payable ?? taxData.ltcg_tax ?? 0;
    const totLiability = taxData.total_tax_liability ?? (sPayable + lPayable);

    if (stcgRealized) stcgRealized.innerText = formatINR(sRealized);
    if (stcgPayable) stcgPayable.innerText = formatINR(sPayable);
    if (ltcgRealized) ltcgRealized.innerText = formatINR(lRealized);
    if (ltcgTaxable) ltcgTaxable.innerText = formatINR(lTaxable);
    if (ltcgPayable) ltcgPayable.innerText = formatINR(lPayable);
    if (totalLiability) totalLiability.innerText = formatINR(totLiability);

    // 3. Render Capital Gains Realized Trades Table
    const taxTradesTbody = document.getElementById('taxTradesTableBody');
    if (taxTradesTbody) {
      if (taxData.trades && Array.isArray(taxData.trades) && taxData.trades.length > 0) {
        taxTradesTbody.innerHTML = taxData.trades.map(t => {
          const pnl = parseFloat(t.pnl || 0);
          const pnlClass = pnl >= 0 ? 'text-positive' : 'text-negative';
          const pnlSign = pnl >= 0 ? '+' : '';
          const taxBadgeClass = (t.tax_type || '').includes('LTCG') ? 'badge-positive' : 'badge-neutral';
          const sym = (t.symbol || '').replace('.NS', '');

          return `
            <tr>
              <td><span style="color: var(--text-muted); font-size: 0.85rem;">${t.date || '--'}</span></td>
              <td>
                <div style="font-weight: 700; color: var(--text-primary);">${sym}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${t.name || ''}</div>
              </td>
              <td><span class="pill-btn" style="font-size: 0.72rem;">${t.product_type || 'DELIVERY'}</span></td>
              <td><strong>${t.quantity}</strong></td>
              <td>${formatINR(t.sell_price || 0)}</td>
              <td><strong class="${pnlClass}">${pnlSign}${formatINR(pnl)}</strong></td>
              <td><span class="${taxBadgeClass}">${t.tax_type || 'STCG (20%)'}</span></td>
            </tr>
          `;
        }).join('');
      } else {
        taxTradesTbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No realized sell trades to report for capital gains tax.</td></tr>';
      }
    }

  } catch (err) {
    console.error('Failed to load portfolio analytics:', err);
  }
}


/* =======================================================
   6. STOCK DETAIL TABS (FINANCIALS, SHAREHOLDING, PEERS, NEWS)
   ======================================================= */
let currentFinData = null;
let currentFinPeriod = 'quarterly';

function switchAssetPageTab(tabId) {
  document.querySelectorAll('.asset-tab-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`tab-asset-${tabId}`);
  if (activeBtn) activeBtn.classList.add('active');

  document.querySelectorAll('.asset-tab-pane').forEach(pane => pane.style.display = 'none');
  const activePane = document.getElementById(`asset-tab-content-${tabId}`);
  if (activePane) activePane.style.display = 'block';

  if (!currentPageAsset) return;
  const sym = currentPageAsset.symbol;

  if (tabId === 'financials') {
    fetchStockFinancials(sym);
  } else if (tabId === 'shareholding') {
    fetchStockShareholding(sym);
  } else if (tabId === 'peers') {
    fetchStockPeers(sym);
  } else if (tabId === 'news') {
    fetchStockNews(sym);
  }
}

function switchFinPeriod(period) {
  currentFinPeriod = period;
  const qBtn = document.getElementById('btnFinQuarterly');
  const aBtn = document.getElementById('btnFinAnnual');
  if (qBtn) qBtn.className = `seg-btn ${period === 'quarterly' ? 'active' : ''}`;
  if (aBtn) aBtn.className = `seg-btn ${period === 'annual' ? 'active' : ''}`;
  if (currentFinData) renderFinancialsBars(currentFinData, period);
}

async function fetchStockFinancials(symbol) {
  const container = document.getElementById('pageFinancialsBarsContainer');
  try {
    const res = await fetch(`/api/stock/financials?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('API error: ' + res.status);
    const data = await res.json();
    currentFinData = data;
    renderFinancialsBars(data, currentFinPeriod);
  } catch (err) {
    console.error('Failed to load financials:', err);
    if (container) container.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">Financial metrics temporarily unavailable for this asset.</div>';
  }
}

function renderFinancialsBars(data, period) {
  const container = document.getElementById('pageFinancialsBarsContainer');
  const tbody = document.getElementById('pageFinancialsTableBody');
  if (!container || !data) return;

  const dataset = period === 'quarterly' ? (data.quarterly || []) : (data.annual || []);
  if (!dataset || dataset.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">Financial statements not available for this period.</div>';
    return;
  }

  dataset.forEach((item, idx) => {
    const col = document.getElementById(`finPeriodCol${idx + 1}`);
    if (col) col.innerText = item.period || `P${idx + 1}`;
  });

  const maxRev = Math.max(...dataset.map(d => Number(d.revenue) || 1), 1000);
  const maxProf = Math.max(...dataset.map(d => Number(d.profit) || 1), 500);

  container.innerHTML = dataset.map(d => {
    const rev = Number(d.revenue) || 0;
    const prof = Number(d.profit) || 0;
    const revHeight = Math.min(100, Math.max(12, Math.round((rev / maxRev) * 100)));
    const profHeight = Math.min(100, Math.max(8, Math.round((prof / maxProf) * 100)));
    const revDisplay = rev >= 1000 ? `₹${(rev / 1000).toFixed(1)}k` : `₹${rev}`;

    return `
      <div class="fin-bar-col">
        <div class="fin-bars-group">
          <div class="fin-bar revenue" style="height: ${revHeight}%;" title="Revenue: ₹${rev.toLocaleString('en-IN')} Cr">
            <span class="fin-bar-val">${revDisplay}</span>
          </div>
          <div class="fin-bar profit" style="height: ${profHeight}%;" title="Net Profit: ₹${prof.toLocaleString('en-IN')} Cr">
            <span class="fin-bar-val">₹${prof >= 1000 ? (prof / 1000).toFixed(1) + 'k' : prof}</span>
          </div>
        </div>
        <span class="fin-bar-label">${d.period || ''}</span>
      </div>
    `;
  }).join('');

  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td><strong>Total Revenue</strong></td>
        ${dataset.map(d => `<td>₹${(Number(d.revenue) || 0).toLocaleString('en-IN')} Cr</td>`).join('')}
      </tr>
      <tr>
        <td><strong>Operating EBITDA</strong></td>
        ${dataset.map(d => `<td>₹${(Number(d.ebitda) || 0).toLocaleString('en-IN')} Cr</td>`).join('')}
      </tr>
      <tr>
        <td><strong>Net Profit (PAT)</strong></td>
        ${dataset.map(d => `<td style="color: var(--accent-green);">₹${(Number(d.profit) || 0).toLocaleString('en-IN')} Cr</td>`).join('')}
      </tr>
      <tr>
        <td><strong>EPS (₹)</strong></td>
        ${dataset.map(d => `<td>₹${d.eps ?? '--'}</td>`).join('')}
      </tr>
    `;
  }
}

async function fetchStockShareholding(symbol) {
  const container = document.getElementById('pageShareholdingContainer');
  try {
    const res = await fetch(`/api/stock/shareholding?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('API error: ' + res.status);
    const data = await res.json();

    const colors = {
      promoter: '#10b981',
      fii: '#3b82f6',
      dii: '#8b5cf6',
      mutual_funds: '#f59e0b',
      public: '#06b6d4'
    };

    const categories = [
      { key: 'promoter', label: 'Promoters & Group', pct: Number(data.promoter ?? data.promoters ?? 48.0) },
      { key: 'fii', label: 'Foreign Inst. (FII)', pct: Number(data.fii ?? 20.0) },
      { key: 'dii', label: 'Domestic Inst. (DII)', pct: Number(data.dii ?? 15.0) },
      { key: 'mutual_funds', label: 'Mutual Funds', pct: Number(data.mutual_funds ?? 10.0) },
      { key: 'public', label: 'Retail & Public', pct: Number(data.public ?? data.retail_public ?? 7.0) }
    ];

    container.innerHTML = `
      <div class="shareholding-progress-bar">
        ${categories.map(c => `
          <div class="sh-segment" style="width: ${c.pct}%; background: ${colors[c.key]};" title="${c.label}: ${c.pct}%"></div>
        `).join('')}
      </div>
      <div class="shareholding-list">
        ${categories.map(c => `
          <div class="sh-row">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
              <span class="legend-dot" style="background: ${colors[c.key]};"></span>
              <span class="sh-name">${c.label}</span>
            </div>
            <strong class="sh-val">${c.pct.toFixed(1)}%</strong>
          </div>
        `).join('')}
      </div>
      <div style="margin-top: 1rem; font-size: 0.75rem; color: var(--text-muted); text-align: right;">
        Promoter Pledging: <strong>${data.promoter_pledged || data.pledged_shares || '0.00%'}</strong>
      </div>
    `;
  } catch (err) {
    console.error('Failed to load shareholding:', err);
    if (container) container.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">Shareholding pattern temporarily unavailable for this asset.</div>';
  }
}

async function fetchStockPeers(symbol) {
  const tbody = document.getElementById('pagePeersTableBody');
  try {
    const res = await fetch(`/api/stock/peers?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('API error: ' + res.status);
    const peers = await res.json();

    if (!peers || peers.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No peer comparisons found.</td></tr>';
      return;
    }

    tbody.innerHTML = peers.map(p => {
      const pSym = (p.symbol || '').replace('.NS', '').replace('.BO', '');
      const pPrice = Number(p.price) || 0;
      const ret1y = String(p.return_1y || (p.change_pct ? (p.change_pct >= 0 ? '+' : '') + p.change_pct + '%' : '--'));
      const isPositive = ret1y.startsWith('+');
      const peStr = p.pe ?? p.pe_ratio ?? '--';
      const mcapStr = p.market_cap ? (typeof p.market_cap === 'number' ? `₹${(p.market_cap / 1e7).toFixed(0)} Cr` : String(p.market_cap)) : '--';
      const divYieldStr = p.div_yield ? (typeof p.div_yield === 'number' ? `${p.div_yield.toFixed(2)}%` : String(p.div_yield)) : '--';

      return `
        <tr>
          <td>
            <strong>${p.name || pSym}</strong>
            <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">${pSym}</span>
          </td>
          <td><strong>${formatINR(pPrice)}</strong></td>
          <td>${peStr}</td>
          <td>${mcapStr}</td>
          <td class="${isPositive ? 'text-positive' : 'text-negative'}">${ret1y}</td>
          <td>${divYieldStr}</td>
          <td style="text-align: right;">
            <button class="btn-subtle" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="showAssetPage('${p.symbol}', 'STOCK')">View</button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to load peers:', err);
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Sector peer comparison temporarily unavailable.</td></tr>';
  }
}

async function fetchStockNews(symbol) {
  const container = document.getElementById('pageNewsContainer');
  try {
    const res = await fetch(`/api/stock/news?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('API error: ' + res.status);
    const news = await res.json();

    if (!news || news.length === 0) {
      if (container) container.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">No recent news articles found for this asset.</div>';
      return;
    }

    container.innerHTML = news.map(n => `
      <div class="news-card-item">
        <div class="news-meta">
          <span class="news-source">${n.source || 'Market Feed'}</span>
          <span class="sub-sep">•</span>
          <span class="news-time">${n.time || 'Recently'}</span>
          <span class="news-sentiment ${n.sentiment === 'Positive' ? 'badge-positive' : 'pill-btn'}">${n.sentiment || 'Neutral'}</span>
        </div>
        <h4 class="news-title">${n.title || ''}</h4>
        <p class="news-summary">${n.summary || ''}</p>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load news:', err);
    if (container) container.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">Market news feed temporarily unavailable.</div>';
  }
}

// Window Global Exports for HTML inline event handlers
window.openOrderConfirmModal = openOrderConfirmModal;
window.closeOrderConfirmModal = closeOrderConfirmModal;
window.toggleConfirmChargesDetails = toggleConfirmChargesDetails;
window.executeConfirmedOrder = executeConfirmedOrder;
window.loadGttOrders = loadGttOrders;
window.cancelGttOrder = cancelGttOrder;
window.filterIpos = filterIpos;
window.renderIpoApplications = renderIpoApplications;
window.withdrawIpoBid = withdrawIpoBid;
window.loadActiveSips = loadActiveSips;
window.cancelSip = cancelSip;
window.loadPortfolioAnalytics = loadPortfolioAnalytics;
window.openMobileTradeDrawer = openMobileTradeDrawer;
window.closeMobileTradeDrawer = closeMobileTradeDrawer;
window.syncDrawerTrigger = syncDrawerTrigger;
