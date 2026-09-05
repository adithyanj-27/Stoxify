// Stoxify — Core Client Application Logic & Feature Engine

// Clean up legacy default session so unauthenticated visitors start in clean Guest mode
if (localStorage.getItem('stoxify_user_id') === 'default') {
  localStorage.removeItem('stoxify_user_id');
}

function isGuest() {
  const uid = localStorage.getItem('stoxify_user_id');
  return !uid || uid === 'default' || uid === 'guest';
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


const state = {
  currentTab: 'explore',
  exploreSubnav: 'stocks',
  ordersSubnav: 'executed',
  exploreStockFilter: 'all',
  exploreData: null,
  account: { balance: 1000000.0 },
  watchlist: new Set(),
  currentModalAsset: null,
  currentModalTimeframe: '1D',
  orderAction: 'BUY',
  productType: 'DELIVERY',
  orderVariety: 'MARKET',
  marketStatus: null,
  chartInstance: null
};

// --- Formatters ---
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

// --- Toast Notifications ---
function showToast(message, isError = false) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${isError ? 'error' : ''}`;
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${isError ? '#eb5b3c' : '#00d09c'}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      ${isError 
        ? '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>' 
        : '<polyline points="20 6 9 17 4 12"></polyline>'}
    </svg>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
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
    const simToggle = document.getElementById('simulationModeToggle');
    if (simToggle) simToggle.checked = !!data.simulation_mode;
  } catch (err) {
    console.error('Failed to fetch market status:', err);
  }
}

function openMarketHoursModal() {
  document.getElementById('marketHoursModalOverlay').classList.add('active');
  fetchMarketStatus();
}

function closeMarketHoursModal() {
  document.getElementById('marketHoursModalOverlay').classList.remove('active');
}

async function toggleSimulationMode(enabled) {
  try {
    const res = await fetch('/api/market-status/toggle-simulation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    const data = await res.json();
    showToast(enabled ? '24/7 Simulated Trading Mode Enabled' : 'Live Market Hours Enforcement Restored');
    fetchMarketStatus();
  } catch (err) {
    showToast('Failed to toggle simulation mode', true);
  }
}

// --- Navigation Tabs (Desktop & Mobile Synchronized) ---
function switchTab(tabId, updateUrl = true) {
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
    const navBal = document.getElementById('navBalanceDisplay');
    if (navBal) navBal.innerText = formatINR(data.balance);
    const menuBal = document.getElementById('menuUserBalance');
    if (menuBal) menuBal.innerText = formatINR(data.balance);
    const summaryBal = document.getElementById('summaryAvailableBalance');
    if (summaryBal) summaryBal.innerText = formatINR(data.balance);
    const fundsBal = document.getElementById('fundsCurrentBalance');
    if (fundsBal) fundsBal.innerText = formatINR(data.balance);
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

// --- Explore View ---
async function fetchExploreData() {
  try {
    const res = await fetch('/api/explore');
    const data = await res.json();
    state.exploreData = data;
    renderExploreStocks();
    renderExploreMutualFunds();
  } catch (err) {
    console.error('Failed to fetch explore data:', err);
  }
}

function filterExploreStocks(filter) {
  state.exploreStockFilter = filter;
  document.querySelectorAll('.filter-pills .pill-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  renderExploreStocks();
}

// --- Card Helpers: Avatars & Star Buttons ---
function getCleanInitial(name, symbol) {
  const str = (name || symbol || 'S').trim();
  // Strip common prefixes like 'The '
  const clean = str.replace(/^The\s+/i, '');
  return clean.charAt(0).toUpperCase();
}

function renderAssetAvatar(item, assetType) {
  const isMF = assetType === 'MUTUAL_FUND' || item.asset_type === 'MUTUAL_FUND';
  const cleanSym = (item.symbol || '').replace('.NS', '').replace('.BO', '');
  const initial = getCleanInitial(item.name, item.symbol);
  const logoUrl = `/static/logos/${cleanSym}.png`;

  const palettes = [
    { bg: 'rgba(14, 165, 233, 0.12)', text: '#38BDF8', border: 'rgba(14, 165, 233, 0.3)' },
    { bg: 'rgba(16, 185, 129, 0.12)', text: '#34D399', border: 'rgba(16, 185, 129, 0.3)' },
    { bg: 'rgba(99, 102, 241, 0.12)', text: '#818CF8', border: 'rgba(99, 102, 241, 0.3)' },
    { bg: 'rgba(236, 72, 153, 0.12)', text: '#F472B6', border: 'rgba(236, 72, 153, 0.3)' },
    { bg: 'rgba(245, 158, 11, 0.12)', text: '#FBBF24', border: 'rgba(245, 158, 11, 0.3)' },
    { bg: 'rgba(168, 85, 247, 0.12)', text: '#C084FC', border: 'rgba(168, 85, 247, 0.3)' },
  ];
  const idx = (initial.charCodeAt(0) || 0) % palettes.length;
  const p = palettes[idx];

  const fallbackHtml = isMF
    ? `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>`
    : initial;

  return `
    <div class="card-avatar ${isMF ? 'avatar-mf' : ''}" style="background: ${p.bg}; color: ${p.text}; border-color: ${p.border};">
      <img src="${logoUrl}" 
           alt="${item.name || cleanSym}" 
           loading="lazy"
           onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
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

function renderExploreStocks() {
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
async function fetchPortfolio() {
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

    const isDayPos = todayPnl >= 0;
    const dayPnlEl = document.getElementById('summaryTodayPnl');
    if (dayPnlEl) {
      dayPnlEl.innerHTML = `<span class="${isDayPos ? 'text-positive' : 'text-negative'}">1D: ${isDayPos ? '+' : ''}${formatINR(todayPnl)} (${isDayPos ? '+' : ''}${formatNumber(todayPnlPct)}%)</span>`;
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
    tableBody.innerHTML = data.holdings.map(h => {
      const isPosTotal = h.total_pnl >= 0;
      const isPosDay = h.today_pnl >= 0;
      return `
        <tr>
          <td>
            <div style="font-weight: 700;">${h.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${h.symbol}</div>
          </td>
          <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem;">${h.asset_type === 'MUTUAL_FUND' ? 'Mutual Fund' : 'Stock'}</span></td>
          <td style="font-weight: 600;">${h.quantity}</td>
          <td>${formatINR(h.avg_price)}</td>
          <td style="font-weight: 700;">${formatINR(h.current_price)}</td>
          <td style="font-weight: 700;">${formatINR(h.current_value)}</td>
          <td class="${isPosTotal ? 'text-positive' : 'text-negative'}" style="font-weight: 700;">
            ${isPosTotal ? '+' : ''}${formatINR(h.total_pnl)}
            <div style="font-size: 0.75rem; font-weight: 600;">(${isPosTotal ? '+' : ''}${formatNumber(h.total_pnl_pct)}%)</div>
          </td>
          <td class="${isPosDay ? 'text-positive' : 'text-negative'}" style="font-weight: 600;">
            ${isPosDay ? '+' : ''}${formatINR(h.today_pnl)}
          </td>
          <td style="text-align: right;">
            <button class="btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="openAssetModal('${h.symbol}', '${h.asset_type}', 'SELL')">Sell</button>
          </td>
        </tr>
      `;
    }).join('');

    // Render Mobile Cards
    mobileList.innerHTML = data.holdings.map(h => {
      const isPosTotal = h.total_pnl >= 0;
      return `
        <div class="mobile-card-item">
          <div class="mobile-card-top">
            <div>
              <div class="mobile-card-symbol">${h.symbol}</div>
              <div class="mobile-card-name">${h.name}</div>
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
            <button class="btn-danger" style="padding: 0.35rem 0.85rem; font-size: 0.8rem;" onclick="openAssetModal('${h.symbol}', '${h.asset_type}', 'SELL')">Sell</button>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Failed to fetch portfolio:', err);
  }
}

// --- Positions View (Intraday MIS with 5x Leverage) ---
async function fetchPositions() {
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
    const positions = data.positions || [];

    // Update badges
    const navBadge = document.getElementById('navPositionsBadge');
    const mobBadge = document.getElementById('mobPositionsBadge');
    if (positions.length > 0) {
      navBadge.innerText = positions.length;
      navBadge.style.display = 'inline-flex';
      mobBadge.innerText = positions.length;
      mobBadge.style.display = 'flex';
    } else {
      navBadge.style.display = 'none';
      mobBadge.style.display = 'none';
    }

    // Update summary metrics
    const isPos = data.total_unrealized_pnl >= 0;
    const pnlEl = document.getElementById('posTotalPnl');
    pnlEl.innerText = `${isPos ? '+' : ''}${formatINR(data.total_unrealized_pnl)}`;
    pnlEl.className = `banner-metric-val ${isPos ? 'text-positive' : 'text-negative'}`;

    document.getElementById('posMarginDeployed').innerText = formatINR(data.total_margin_used);
    document.getElementById('posActiveCount').innerText = positions.length;

    const sqAllBtn = document.getElementById('squareOffAllBtn');
    sqAllBtn.style.display = positions.length > 0 ? 'inline-block' : 'none';

    const tableBody = document.getElementById('positionsTableBody');
    const mobileList = document.getElementById('positionsMobileList');

    if (positions.length === 0) {
      tableBody.innerHTML = `
        <tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 3rem;">No active intraday positions. Intraday trades will appear here with live P&L and 1-click square-off.</td></tr>
      `;
      mobileList.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No active intraday positions.</div>
      `;
      return;
    }

    // Desktop Table
    tableBody.innerHTML = positions.map(p => {
      const isPosItem = p.unrealized_pnl >= 0;
      return `
        <tr>
          <td>
            <div style="font-weight: 700;">${p.name}</div>
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

    // Mobile Cards
    mobileList.innerHTML = positions.map(p => {
      const isPosItem = p.unrealized_pnl >= 0;
      return `
        <div class="mobile-card-item">
          <div class="mobile-card-top">
            <div>
              <div class="mobile-card-symbol">${p.symbol} <span class="pill-btn" style="padding: 1px 5px; font-size: 0.65rem; background: var(--brand-cyan-bg); color: var(--brand-cyan);">MIS 5x</span></div>
              <div class="mobile-card-name">${p.name}</div>
            </div>
            <div class="mobile-card-price">
              <div class="${isPosItem ? 'text-positive' : 'text-negative'}" style="font-size: 1.1rem; font-weight: 800;">
                ${isPosItem ? '+' : ''}${formatINR(p.unrealized_pnl)}
              </div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">(${isPosItem ? '+' : ''}${formatNumber(p.unrealized_pnl_pct)}%)</div>
            </div>
          </div>
          <div class="mobile-card-grid">
            <div><span style="color:var(--text-muted);">Qty:</span> <strong>${p.quantity}</strong></div>
            <div><span style="color:var(--text-muted);">Avg Buy:</span> <strong>${formatINR(p.avg_price)}</strong></div>
            <div><span style="color:var(--text-muted);">LTP:</span> <strong>${formatINR(p.current_price)}</strong></div>
            <div><span style="color:var(--text-muted);">Margin:</span> <strong>${formatINR(p.margin_used)}</strong></div>
          </div>
          <div class="mobile-card-actions">
            <button class="btn-danger" style="width: 100%; justify-content: center; padding: 0.5rem;" onclick="exitPosition('${p.symbol}')">
              Square Off / Exit Position
            </button>
          </div>
        </div>
      `;
    }).join('');

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
    fetchPositions();
    fetchAccount();
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
    fetchPositions();
    fetchAccount();
  } catch (err) {
    showToast('Failed to square off positions', true);
  }
}

// --- Orders View (Executed & Open Orders) ---
async function fetchOrders() {
  try {
    const [execRes, openRes] = await Promise.all([
      fetch('/api/orders'),
      fetch('/api/orders?status=OPEN')
    ]);
    const allOrders = await execRes.json();
    const openOrders = await openRes.json();
    const executedOrders = allOrders.filter(o => o.status !== 'OPEN');

    // Update Open Orders count badges
    document.getElementById('openOrdersCount').innerText = openOrders.length;
    const navOrdersBadge = document.getElementById('navOrdersBadge');
    const mobOpenOrdersBadge = document.getElementById('mobOpenOrdersBadge');
    const mobOrdersBadge = document.getElementById('mobOrdersBadge');

    if (openOrders.length > 0) {
      navOrdersBadge.innerText = openOrders.length;
      navOrdersBadge.style.display = 'inline-flex';
      if (mobOpenOrdersBadge) {
        mobOpenOrdersBadge.innerText = openOrders.length;
        mobOpenOrdersBadge.style.display = 'flex';
      }
      if (mobOrdersBadge) {
        mobOrdersBadge.innerText = openOrders.length;
        mobOrdersBadge.style.display = 'inline-flex';
      }
    } else {
      navOrdersBadge.style.display = 'none';
      if (mobOpenOrdersBadge) mobOpenOrdersBadge.style.display = 'none';
      if (mobOrdersBadge) mobOrdersBadge.style.display = 'none';
    }

    // 1. Render Executed Orders Table & Mobile Cards
    const execTableBody = document.getElementById('ordersTableBody');
    const execMobileList = document.getElementById('ordersMobileList');

    if (executedOrders.length === 0) {
      execTableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 3rem;">No orders placed yet.</td></tr>`;
      execMobileList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No orders placed yet.</div>`;
    } else {
      execTableBody.innerHTML = executedOrders.map(o => {
        const isBuy = o.order_type === 'BUY';
        const isPnlPos = o.realized_pnl >= 0;
        return `
          <tr>
            <td style="font-size: 0.8rem; color: var(--text-muted);">${o.timestamp || 'Today'}</td>
            <td><strong>${o.name}</strong><div style="font-size: 0.75rem; color: var(--text-muted);">${o.symbol}</div></td>
            <td><span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type}</span></td>
            <td><span class="pill-btn" style="padding: 0.15rem 0.45rem; font-size: 0.7rem;">${o.product_type}</span></td>
            <td><span style="font-size: 0.75rem; color: var(--text-muted);">${o.order_variety || 'MARKET'}</span></td>
            <td style="font-weight: 600;">${o.quantity}</td>
            <td>${formatINR(o.price)}</td>
            <td style="font-weight: 700;">${formatINR(o.total_amount)}</td>
            <td class="${isPnlPos ? 'text-positive' : 'text-negative'}" style="font-weight: 700;">
              ${o.realized_pnl ? (isPnlPos ? '+' : '') + formatINR(o.realized_pnl) : '—'}
            </td>
            <td><span class="pill-btn" style="padding: 0.15rem 0.45rem; font-size: 0.7rem; color: ${o.status.includes('CANCELLED') ? 'var(--danger-red)' : 'var(--accent-green)'};">${o.status}</span></td>
          </tr>
        `;
      }).join('');

      execMobileList.innerHTML = executedOrders.map(o => {
        const isBuy = o.order_type === 'BUY';
        return `
          <div class="mobile-card-item">
            <div class="mobile-card-top">
              <div>
                <div class="mobile-card-symbol">${o.symbol} <span class="badge-${isBuy ? 'positive' : 'negative'}" style="font-size: 0.7rem;">${o.order_type}</span></div>
                <div class="mobile-card-name">${o.name} • ${o.product_type}</div>
              </div>
              <div class="mobile-card-price">
                ${formatINR(o.total_amount)}
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

    // 2. Render Open Orders Table & Mobile Cards
    const openTableBody = document.getElementById('openOrdersTableBody');
    const openMobileList = document.getElementById('openOrdersMobileList');

    if (openOrders.length === 0) {
      openTableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 3rem;">No pending limit orders.</td></tr>`;
      openMobileList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No pending limit orders.</div>`;
    } else {
      openTableBody.innerHTML = openOrders.map(o => {
        const isBuy = o.order_type === 'BUY';
        return `
          <tr>
            <td>#${o.id}</td>
            <td><strong>${o.name}</strong><div style="font-size: 0.75rem; color: var(--text-muted);">${o.symbol}</div></td>
            <td><span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type}</span></td>
            <td>${o.product_type}</td>
            <td style="font-weight: 600;">${o.quantity}</td>
            <td style="font-weight: 700; color: var(--brand-cyan);">${formatINR(o.limit_price || o.price)}</td>
            <td>${formatINR(o.total_amount)}</td>
            <td style="font-size: 0.75rem; color: var(--text-muted);">${o.timestamp || 'Today'}</td>
            <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem; color: var(--brand-cyan);">OPEN</span></td>
            <td style="text-align: right;">
              <button class="btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="cancelOrder(${o.id})">Cancel</button>
            </td>
          </tr>
        `;
      }).join('');

      openMobileList.innerHTML = openOrders.map(o => {
        const isBuy = o.order_type === 'BUY';
        return `
          <div class="mobile-card-item" style="border-left: 4px solid var(--brand-cyan);">
            <div class="mobile-card-top">
              <div>
                <div class="mobile-card-symbol">${o.symbol} <span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type} LIMIT</span></div>
                <div class="mobile-card-name">Order #${o.id} • ${o.product_type}</div>
              </div>
              <div class="mobile-card-price">
                <span style="color: var(--brand-cyan);">${formatINR(o.limit_price || o.price)}</span>
                <div style="font-size: 0.75rem; color: var(--text-muted);">Pending Execution</div>
              </div>
            </div>
            <div class="mobile-card-grid">
              <div><span style="color:var(--text-muted);">Qty:</span> <strong>${o.quantity}</strong></div>
              <div><span style="color:var(--text-muted);">Blocked:</span> <strong>${formatINR(o.total_amount)}</strong></div>
            </div>
            <div class="mobile-card-actions">
              <button class="btn-danger" style="width: 100%; justify-content: center; padding: 0.45rem;" onclick="cancelOrder(${o.id})">Cancel Limit Order</button>
            </div>
          </div>
        `;
      }).join('');
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
    fetchOrders();
    fetchAccount();
  } catch (err) {
    showToast('Failed to cancel order', true);
  }
}

// --- Watchlist View ---
async function fetchWatchlist() {
  try {
    const res = await fetch('/api/watchlist');
    const items = await res.json();
    state.watchlist = new Set(items.map(i => i.symbol));

    const grid = document.getElementById('watchlistGrid');
    if (items.length === 0) {
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
  if (state.watchlist.has(symbol)) {
    await fetch(`/api/watchlist/${encodeURIComponent(symbol)}`, { method: 'DELETE' });
    state.watchlist.delete(symbol);
    showToast(`Removed ${symbol} from watchlist`);
  } else {
    await fetch('/api/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, name, asset_type: assetType })
    });
    state.watchlist.add(symbol);
    showToast(`Added ${symbol} to watchlist`);
  }
  if (state.currentTab === 'watchlist') {
    fetchWatchlist();
  } else if (state.currentTab === 'explore') {
    renderExploreStocks();
    renderExploreMutualFunds();
  }
  if (state.currentModalAsset && state.currentModalAsset.symbol === symbol) renderModalWatchlistBtn(symbol, name, assetType);
}

// --- Search Auto-Complete ---
const searchInput = document.getElementById('globalSearchInput');
const searchDropdown = document.getElementById('searchResultsDropdown');
let searchDebounceTimer = null;

searchInput.addEventListener('input', (e) => {
  const query = e.target.value.trim();
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

document.addEventListener('click', (e) => {
  if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
    searchDropdown.style.display = 'none';
  }
});

function selectSearchResult(symbol, assetType) {
  searchDropdown.style.display = 'none';
  searchInput.value = '';
  openAssetModal(symbol, assetType);
}

// --- Asset Detail & Trade Modal ---
function openAssetModal(symbol, assetType = 'STOCK', preselectAction = 'BUY') {
  const cleanSym = (symbol || '').replace('.NS', '').replace('.BO', '');
  if (assetType === 'MUTUAL_FUND' || symbol.match(/^\d+$/)) {
    navigateTo('/mf/' + cleanSym);
  } else {
    navigateTo('/stock/' + cleanSym);
  }
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

    const cleanSym = (data.symbol || '').replace('.NS', '').replace('.BO', '');
    const isMF = data.asset_type === 'MUTUAL_FUND';
    const initial = getCleanInitial(data.name, data.symbol);
    const logoUrl = `/static/logos/${cleanSym}.png`;
    const fallbackHtml = isMF
      ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>`
      : initial;

    const modalAvatarEl = document.getElementById('modalAvatar');
    modalAvatarEl.innerHTML = `
      <img src="${logoUrl}" 
           alt="${data.name || cleanSym}" 
           loading="lazy"
           onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
           style="width: 28px; height: 28px; object-fit: contain; border-radius: 4px;">
      <span style="display: none; align-items: center; justify-content: center; width: 100%; height: 100%; font-weight: 800;">
        ${fallbackHtml}
      </span>
    `;
    document.getElementById('modalTitle').innerText = data.name;
    document.getElementById('modalSymbol').innerText = data.symbol;
    document.getElementById('modalBadge').innerText = data.asset_type === 'MUTUAL_FUND' ? 'MUTUAL FUND' : 'NSE';

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
  document.querySelectorAll('.timeframe-group .tf-btn').forEach(b => b.classList.remove('active'));
  if (event && event.target && event.target.classList) {
    event.target.classList.add('active');
  }

  if (!state.currentModalAsset) return;
  const symbol = state.currentModalAsset.symbol;
  const assetType = state.currentModalAsset.asset_type;

  try {
    const res = await fetch(`/api/history?symbol=${encodeURIComponent(symbol)}&asset_type=${encodeURIComponent(assetType)}&timeframe=${tf}`);
    const points = await res.json();
    renderChart(points);
  } catch (err) {
    console.error('Failed to load chart data:', err);
  }
}

function renderChart(points) {
  const canvas = document.getElementById('tradeChartCanvas');
  const ctx = canvas.getContext('2d');
  if (state.chartInstance) state.chartInstance.destroy();

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const labels = points.map(p => p.time);
  const values = points.map(p => p.value);
  const isPos = values[values.length - 1] >= values[0];
  const strokeColor = isPos ? '#00D09C' : '#EB5B3C';
  
  const gradient = ctx.createLinearGradient(0, 0, 0, 220);
  gradient.addColorStop(0, isPos ? 'rgba(0, 208, 156, 0.25)' : 'rgba(235, 91, 60, 0.25)');
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

  state.chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        borderColor: strokeColor,
        borderWidth: 2,
        backgroundColor: gradient,
        fill: true,
        tension: 0.2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: strokeColor,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDark ? '#1C2230' : '#FFFFFF',
          titleColor: isDark ? '#F0F4F8' : '#0F172A',
          bodyColor: strokeColor,
          borderColor: isDark ? '#2B3548' : '#E2E8F0',
          borderWidth: 1,
          padding: 8,
          displayColors: false,
          callbacks: { label: (ctx) => `Price: ${formatINR(ctx.parsed.y)}` }
        }
      },
      scales: {
        x: { display: false },
        y: {
          position: 'right',
          grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
          ticks: { color: isDark ? '#64748B' : '#94A3B8', font: { size: 10 }, callback: (val) => `₹${val}` }
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
  document.getElementById('orderAvailableBalance').innerText = formatINR(state.account.balance);

  // Regulatory charges calculation
  const charges = calculateEstimatedCharges(tradeTotal, state.orderAction, state.productType);
  document.getElementById('orderEstCharges').innerText = `${formatINR(charges.total)} ℹ️`;
}

function calculateEstimatedCharges(amount, action, product) {
  const isIntra = product === 'INTRADAY';
  const isBuy = action === 'BUY';

  const brokerage = isIntra ? 20.0 : 0.0;
  const stt = isIntra ? (isBuy ? 0 : amount * 0.00025) : (amount * 0.001);
  const exchTxn = amount * 0.0000297;
  const sebi = (amount / 10000000) * 10;
  const stamp = isBuy ? amount * 0.00015 : 0;
  const gst = (brokerage + exchTxn + sebi) * 0.18;
  const total = brokerage + stt + exchTxn + sebi + stamp + gst;

  return {
    brokerage: roundNumber(brokerage, 2),
    stt: roundNumber(stt, 2),
    exchange: roundNumber(exchTxn, 2),
    sebi: roundNumber(sebi, 2),
    stamp: roundNumber(stamp, 2),
    gst: roundNumber(gst, 2),
    total: roundNumber(total, 2)
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
  const c = calculateEstimatedCharges(totalVal, state.orderAction, state.productType);

  const list = document.getElementById('chargesBreakdownList');
  list.innerHTML = `
    <div style="display: flex; justify-content: space-between;"><span>Brokerage (${state.productType === 'INTRADAY' ? '₹20 Flat' : 'Zero for Delivery'})</span><strong>${formatINR(c.brokerage)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>Securities Transaction Tax (STT)</span><strong>${formatINR(c.stt)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>Exchange Turnover Charges (NSE 0.00297%)</span><strong>${formatINR(c.exchange)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>SEBI Turnover Charges</span><strong>${formatINR(c.sebi)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>Stamp Duty (State Govt)</span><strong>${formatINR(c.stamp)}</strong></div>
    <div style="display: flex; justify-content: space-between;"><span>GST (18% on Brokerage & Txn Fee)</span><strong>${formatINR(c.gst)}</strong></div>
  `;
  document.getElementById('chargesModalTotal').innerText = formatINR(c.total);
  document.getElementById('chargesModalOverlay').classList.add('active');
}

function closeChargesModal() {
  document.getElementById('chargesModalOverlay').classList.remove('active');
}

function roundNumber(num, dec) {
  return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
}

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

  const payload = {
    symbol: state.currentModalAsset.symbol,
    name: state.currentModalAsset.name,
    asset_type: state.currentModalAsset.asset_type,
    order_type: state.orderAction,
    product_type: state.productType,
    quantity: qty,
    price: state.currentModalAsset.price,
    order_variety: state.orderVariety,
    limit_price: limitPrice
  };

  try {
    const res = await fetch('/api/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'Order rejected by broker engine', true);
      return;
    }

    showToast(result.message || `Order processed successfully: ${state.orderAction} ${qty} ${payload.symbol}`);
    closeTradeModal();
    await fetchAccount();
    await fetchPortfolio();
    await fetchPositions();
    await fetchOrders();

    openOrderSuccessModal({
      symbol: payload.symbol,
      name: payload.name,
      action: payload.order_type,
      product: payload.product_type,
      quantity: qty,
      price: payload.price,
      total: qty * payload.price
    });
  } catch (err) {
    console.error('Order submission error:', err);
    showToast('Failed to connect to execution server', true);
  }
}

// --- Virtual Funds & Timings Modal ---
function openFundsModal() {
  const menu = document.getElementById('userDropdownMenu');
  if (menu) menu.style.display = 'none';
  document.getElementById('fundsModalOverlay').classList.add('active');
  const bal = (state.account && state.account.balance !== undefined) ? state.account.balance : (currentUser ? currentUser.balance : 1000000.0);
  const fundsBal = document.getElementById('fundsCurrentBalance');
  if (fundsBal) fundsBal.innerText = formatINR(bal);

  const maxNotice = document.getElementById('maxFundsNotice');
  const depositArea = document.getElementById('depositFormArea');
  const depositInput = document.getElementById('depositAmountInput');
  const depositLimitLabel = document.getElementById('depositLimitLabel');

  if (bal >= 1000000.0) {
    if (maxNotice) maxNotice.style.display = 'block';
    if (depositArea) depositArea.style.display = 'none';
  } else {
    const deficit = Math.round((1000000.0 - bal) * 100) / 100;
    if (maxNotice) maxNotice.style.display = 'none';
    if (depositArea) depositArea.style.display = 'block';
    if (depositLimitLabel) depositLimitLabel.innerText = `Restore Balance (Max Allowed: ${formatINR(deficit)})`;
    if (depositInput) {
      depositInput.value = deficit;
      depositInput.max = deficit;
    }
  }
}

function closeFundsModal() {
  document.getElementById('fundsModalOverlay').classList.remove('active');
}

async function submitDeposit() {
  const bal = (state.account && state.account.balance !== undefined) ? state.account.balance : (currentUser ? currentUser.balance : 1000000.0);
  if (bal >= 1000000.0) {
    showToast('Your balance is already at the maximum limit of ₹10,00,000.', true);
    return;
  }
  const maxAllowed = 1000000.0 - bal;
  let amount = parseFloat(document.getElementById('depositAmountInput').value);
  if (!amount || amount <= 0) {
    showToast('Please enter a valid amount to restore', true);
    return;
  }
  if (amount > maxAllowed) {
    amount = maxAllowed;
  }

  try {
    const res = await fetch('/api/account/deposit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Added ${formatINR(amount)} to balance (maximum ₹10L reached)`);
      await fetchAccount();
      closeFundsModal();
      document.getElementById('depositAmountInput').value = '';
    } else {
      showToast(data.detail || 'Deposit failed', true);
    }
  } catch (err) {
    showToast('Deposit failed', true);
  }
}

// --- PWA (Progressive Web App) Install Engine ---
let deferredInstallPrompt = null;

function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.navigator.standalone === true;
}

function dismissMobileInstallBanner() {
  sessionStorage.setItem('stoxify_mob_install_dismissed', '1');
  const banner = document.getElementById('mobileInstallBanner');
  if (banner) banner.style.display = 'none';
}

function updateInstallButtonsVisibility() {
  const installed = isAppInstalled();
  const topBtn = document.getElementById('btnInstallApp');
  const dropdownItem = document.getElementById('dropdownInstallItem');
  const mobBanner = document.getElementById('mobileInstallBanner');
  const mobDismissed = sessionStorage.getItem('stoxify_mob_install_dismissed') === '1';

  // Desktop/header button is visible unless running as installed standalone PWA
  if (topBtn) topBtn.style.display = installed ? 'none' : 'inline-flex';
  if (dropdownItem) dropdownItem.style.display = installed ? 'none' : 'flex';

  // Mobile banner is visible on mobile browsers unless running in standalone PWA
  if (mobBanner) {
    if (installed || mobDismissed) {
      mobBanner.style.display = 'none';
    } else {
      const isMobile = window.innerWidth <= 768 || detectPlatform() !== 'desktop';
      mobBanner.style.display = isMobile ? 'flex' : 'none';
    }
  }
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
        localStorage.setItem('stoxify_app_installed', '1');
        updateInstallButtonsVisibility();
        closePwaGuideModal();
        showToast('Stoxify installed successfully!');
      }
      deferredInstallPrompt = null;
    } catch (err) {
      console.warn('Native prompt error:', err);
    }
  }
}

async function installPWA() {
  if (deferredInstallPrompt) {
    try {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      if (outcome === 'accepted') {
        localStorage.setItem('stoxify_app_installed', '1');
        updateInstallButtonsVisibility();
        closePwaGuideModal();
        showToast('Stoxify installed successfully!');
      }
      deferredInstallPrompt = null;
      return;
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
  localStorage.setItem('stoxify_app_installed', '1');
  updateInstallButtonsVisibility();
  closePwaGuideModal();
  showToast('Stoxify installed successfully!');
});

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).then((reg) => {
      console.log('Stoxify PWA Service Worker registered:', reg.scope);
    }).catch((err) => {
      console.warn('Service Worker registration skipped:', err);
    });
  });
}

// --- Initialization ---
window.addEventListener('DOMContentLoaded', () => {
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

  fetchCurrentUser();
  handleRoute();

  Promise.all([
    fetchMarketStatus(),
    fetchAccount(),
    fetchIndices(),
    fetchExploreData(),
    fetchWatchlist(),
    fetchPositions()
  ]);

  // Polling intervals
  setInterval(() => fetchMarketStatus(), 10000);
  setInterval(() => {
    fetchIndices();
    if (state.currentTab === 'holdings') fetchPortfolio();
    if (state.currentTab === 'positions') fetchPositions();
  }, 20000);
});



/* =======================================================
   CLIENT-SIDE ROUTER ENGINE (HTML5 History API)
   ======================================================= */
function navigateTo(path, pushState = true) {
  if (pushState && window.location.pathname !== path) {
    history.pushState(null, '', path);
  }
  handleRoute();
}

function handleRoute() {
  const path = window.location.pathname;
  const userMenu = document.getElementById('userDropdownMenu');
  if (userMenu) userMenu.style.display = 'none';

  if (path.startsWith('/stock/')) {
    const sym = decodeURIComponent(path.replace('/stock/', '')).trim();
    showAssetPage(sym, 'STOCK');
  } else if (path.startsWith('/mf/')) {
    const sym = decodeURIComponent(path.replace('/mf/', '')).trim();
    showAssetPage(sym, 'MUTUAL_FUND');
  } else if (path === '/onboarding') {
    showOnboardingPage();
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
  if (isGuest()) {
    currentUser = null;
    updateNavbarProfile();
    return;
  }
  try {
    const res = await fetch('/api/user/current');
    const u = await res.json();
    if (u && u.id && !u.is_guest) {
      currentUser = u;
      localStorage.setItem('stoxify_user_id', u.id);
    } else {
      localStorage.removeItem('stoxify_user_id');
      currentUser = null;
    }
  } catch (err) {
    console.error('Failed to fetch user:', err);
    currentUser = null;
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

  if (isGuest() || !currentUser) {
    if (getStartedBtn) getStartedBtn.style.display = 'inline-flex';
    if (profileWrapper) profileWrapper.style.display = 'none';
    const navBalEl = document.getElementById('navBalanceDisplay');
    if (navBalEl) navBalEl.innerText = '₹0.00';
    return;
  }

  // Authenticated user
  if (getStartedBtn) getStartedBtn.style.display = 'none';
  if (profileWrapper) profileWrapper.style.display = 'block';

  const initials = currentUser.name ? currentUser.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'ST';
  if (initialsEl) initialsEl.innerText = initials;
  if (menuAvatarEl) menuAvatarEl.innerText = initials;
  if (menuNameEl) menuNameEl.innerText = currentUser.name;
  if (menuEmailEl) menuEmailEl.innerText = currentUser.email || '';
  if (menuDematEl) menuDematEl.innerText = `Demat: STOX-${(currentUser.id || '9876').slice(-6).toUpperCase()}`;
  const last4 = (currentUser.bank_account || '5678').slice(-4);
  if (menuBankEl) menuBankEl.innerText = `${currentUser.bank_name || 'HDFC Bank'} •••• ${last4} (Verified ✓)`;
  if (menuBalEl) menuBalEl.innerText = formatINR(currentUser.balance || 1000000.0);
  const navBalEl = document.getElementById('navBalanceDisplay');
  if (navBalEl) navBalEl.innerText = formatINR(currentUser.balance || 1000000.0);
}

function logoutUser() {
  localStorage.removeItem('stoxify_user_id');
  currentUser = null;
  updateNavbarProfile();
  showToast('Switched to Guest Mode.');
  if (state.currentTab === 'holdings') fetchPortfolio();
  if (state.currentTab === 'positions') fetchPositions();
  if (state.currentTab === 'orders') fetchOrders();
  navigateTo('/explore');
}

function toggleProfileDropdown() {
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
});

async function openSwitchAccountModal() {
  toggleProfileDropdown();
  const overlay = document.getElementById('switchAccountModalOverlay');
  const container = document.getElementById('accountsListContainer');
  overlay.classList.add('active');

  try {
    const res = await fetch('/api/user/list');
    const users = await res.json();
    container.innerHTML = users.map(u => {
      const isCurrent = u.id === currentUser.id;
      const initials = u.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
      return `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.85rem; border-radius: 12px; background: var(--bg-main); border: 1px solid ${isCurrent ? 'var(--brand-cyan)' : 'var(--border-subtle)'}; cursor: pointer;"
             onclick="activateUserAccount('${u.id}')">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #0EA5E9, #10B981); color: #080D14; font-weight: 800; display: flex; align-items: center; justify-content: center;">
              ${initials}
            </div>
            <div>
              <div style="font-weight: 800; font-size: 0.95rem;">${u.name} ${isCurrent ? '<span style="color: var(--accent-green); font-size: 0.75rem;">(Active)</span>' : ''}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${u.bank_name || 'Bank'} • ${formatINR(u.balance)}</div>
            </div>
          </div>
          ${isCurrent ? '<span style="color: var(--brand-cyan); font-weight: 800;">✓</span>' : '<button class="pill-btn" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;">Switch</button>'}
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = '<div style="color: var(--text-muted);">Failed to load accounts.</div>';
  }
}

function closeSwitchAccountModal() {
  const overlay = document.getElementById('switchAccountModalOverlay');
  if (overlay) overlay.classList.remove('active');
}

async function activateUserAccount(userId) {
  localStorage.setItem('stoxify_user_id', userId);
  currentUser.id = userId;
  closeSwitchAccountModal();
  await fetchCurrentUser();
  fetchAccount();
  if (state.currentTab === 'holdings') fetchPortfolio();
  if (state.currentTab === 'positions') fetchPositions();
  if (state.currentTab === 'orders') fetchOrders();
  showToast(`Switched account to ${currentUser.name}!`);
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
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-links .nav-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  
  const pagePane = document.getElementById('pane-asset-detail');
  if (pagePane) pagePane.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  try {
    const res = await fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}&asset_type=${encodeURIComponent(assetType)}`);
    const data = await res.json();
    currentPageAsset = data;
    state.currentModalAsset = data;

    const cleanSym = (data.symbol || '').replace('.NS', '').replace('.BO', '');
    const isMF = data.asset_type === 'MUTUAL_FUND';
    
    document.getElementById('assetBreadcrumbCategory').innerText = isMF ? 'Mutual Funds' : 'Stocks';
    document.getElementById('assetBreadcrumbName').innerText = data.name;

    document.getElementById('pageAssetAvatar').innerHTML = renderAssetAvatar(data, data.asset_type);
    document.getElementById('pageAssetTitle').innerText = data.name;
    document.getElementById('pageAssetSymbol').innerText = cleanSym;
    document.getElementById('pageAssetBadge').innerText = isMF ? 'Mutual Fund' : (data.exchange || 'NSE');
    document.getElementById('pageAssetSector').innerText = data.sector || (isMF ? data.category || 'Direct Plan' : 'Equities');
    document.getElementById('pageAssetPrice').innerText = formatINR(data.price);

    const isPos = data.change >= 0;
    const badgeEl = document.getElementById('pageAssetChangeBadge');
    badgeEl.className = isPos ? 'badge-positive' : 'badge-negative';
    badgeEl.innerText = formatChange(data.change, data.change_pct);

    updatePageAssetStar(data.symbol);
    const starBtn = document.getElementById('pageAssetStarBtn');
    starBtn.onclick = () => {
      toggleWatchlist(data.symbol, data.name, data.asset_type);
      setTimeout(() => updatePageAssetStar(data.symbol), 150);
    };

    const low = data.low || data.price * 0.985;
    const high = data.high || data.price * 1.015;
    const w52Low = data.low_52w || data.price * 0.75;
    const w52High = data.high_52w || data.price * 1.35;

    document.getElementById('perfTodayLow').innerText = formatINR(low);
    document.getElementById('perfTodayHigh').innerText = formatINR(high);
    document.getElementById('perf52wLow').innerText = formatINR(w52Low);
    document.getElementById('perf52wHigh').innerText = formatINR(w52High);
    document.getElementById('perfOpen').innerText = formatINR(data.open || data.price * 0.99);
    document.getElementById('perfPrevClose').innerText = formatINR(data.prev_close || data.price - data.change);
    document.getElementById('perfVolume').innerText = data.volume ? Number(data.volume).toLocaleString('en-IN') : '34.2L';
    document.getElementById('perfLowerCircuit').innerText = formatINR(data.price * 0.9);
    document.getElementById('perfUpperCircuit').innerText = formatINR(data.price * 1.1);

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

    // Configure Mutual Fund SIP calculator vs Stock fundamentals tabs
    const sipSec = document.getElementById('pageSipCalcSection');
    const tabFin = document.getElementById('tab-asset-financials');
    const tabSh = document.getElementById('tab-asset-shareholding');
    const tabPeers = document.getElementById('tab-asset-peers');
    if (sipSec) sipSec.style.display = isMF ? 'block' : 'none';
    if (tabFin) tabFin.style.display = isMF ? 'none' : 'inline-block';
    if (tabSh) tabSh.style.display = isMF ? 'none' : 'inline-block';
    if (tabPeers) tabPeers.style.display = isMF ? 'none' : 'inline-block';
    if (isMF) onSipSliderChange();
    switchAssetPageTab('overview');

    loadPageChartTimeframe('1M');

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
      <div class="fundamental-item"><span class="f-name">Expense Ratio</span><strong class="f-val">${data.expense_ratio || '0.62%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">1Y Return</span><strong class="f-val text-positive">${data.return_1y || '+18.4%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">3Y Return (CAGR)</span><strong class="f-val text-positive">${data.return_3y || '+24.1%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">Risk Rating</span><strong class="f-val">Very High</strong></div>
      <div class="fundamental-item"><span class="f-name">Fund Manager</span><strong class="f-val">${data.fund_manager || 'Rajeev Thakkar'}</strong></div>
    `;
  } else {
    grid.innerHTML = `
      <div class="fundamental-item"><span class="f-name">Market Cap</span><strong class="f-val">${data.market_cap ? '₹' + Number(data.market_cap).toLocaleString('en-IN') + ' Cr' : '₹18.4L Cr'}</strong></div>
      <div class="fundamental-item"><span class="f-name">P/E Ratio</span><strong class="f-val">${data.pe_ratio || '24.8'}</strong></div>
      <div class="fundamental-item"><span class="f-name">P/B Ratio</span><strong class="f-val">${data.pb_ratio || '3.12'}</strong></div>
      <div class="fundamental-item"><span class="f-name">Industry P/E</span><strong class="f-val">${data.industry_pe || '22.4'}</strong></div>
      <div class="fundamental-item"><span class="f-name">Debt to Equity</span><strong class="f-val">${data.debt_to_equity || '0.42'}</strong></div>
      <div class="fundamental-item"><span class="f-name">ROE</span><strong class="f-val">${data.roe ? data.roe + '%' : '14.8%'}</strong></div>
      <div class="fundamental-item"><span class="f-name">EPS (TTM)</span><strong class="f-val">${data.eps ? '₹' + data.eps : '₹54.20'}</strong></div>
      <div class="fundamental-item"><span class="f-name">Dividend Yield</span><strong class="f-val">${data.div_yield ? data.div_yield + '%' : '0.45%'}</strong></div>
    `;
  }
}

let currentChartType = 'line';
const activeEmas = new Set();
let currentChartPoints = [];
let currentChartRange = '1M';

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

function renderCandlestickCanvas(canvas, points) {
  const ctx = canvas.getContext('2d');
  const width = canvas.parentElement.clientWidth || 800;
  const height = 380;
  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);

  if (!points || points.length === 0) return;

  const paddingLeft = 15;
  const paddingRight = 75;
  const paddingTop = 25;
  const paddingBottom = 40;
  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Compute OHLC for each point
  const ohlc = points.map((p, idx) => {
    const close = (p.price !== undefined ? p.price : p.value) || 100;
    const prevClose = idx > 0 ? ((points[idx - 1].price !== undefined ? points[idx - 1].price : points[idx - 1].value) || close) : close;
    const open = p.open || prevClose;
    const high = p.high || Math.max(open, close) * 1.003;
    const low = p.low || Math.min(open, close) * 0.997;
    const vol = p.volume || 10000;
    return { time: p.time, open, high, low, close, volume: vol };
  });

  const minPrice = Math.min(...ohlc.map(p => p.low)) * 0.998;
  const maxPrice = Math.max(...ohlc.map(p => p.high)) * 1.002;
  const priceRange = maxPrice - minPrice || 1;

  const getY = (val) => paddingTop + chartHeight - ((val - minPrice) / priceRange) * chartHeight;

  // Background Grid Lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = paddingTop + (chartHeight / 4) * i;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();

    const priceAtGrid = maxPrice - (priceRange / 4) * i;
    ctx.fillStyle = '#64748B';
    ctx.font = '10px Sora, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(formatINR(priceAtGrid), width - paddingRight + 8, y + 3);
  }

  const n = ohlc.length;
  const candleSlot = chartWidth / n;
  const candleBodyWidth = Math.max(2, Math.min(18, candleSlot * 0.68));

  // Draw Candlesticks and Volume
  ohlc.forEach((bar, i) => {
    const x = paddingLeft + i * candleSlot + candleSlot / 2;
    const isBull = bar.close >= bar.open;
    const color = isBull ? '#10B981' : '#F43F5E';

    // 1. Volume Bar (Bottom 18% of chart)
    const maxVol = Math.max(...ohlc.map(p => p.volume)) || 1;
    const volHeight = (bar.volume / maxVol) * (chartHeight * 0.18);
    ctx.fillStyle = isBull ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)';
    ctx.fillRect(x - candleBodyWidth / 2, paddingTop + chartHeight - volHeight, candleBodyWidth, volHeight);

    // 2. Wick
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(x, getY(bar.high));
    ctx.lineTo(x, getY(bar.low));
    ctx.stroke();

    // 3. Body
    const yOpen = getY(bar.open);
    const yClose = getY(bar.close);
    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(2, Math.abs(yClose - yOpen));

    ctx.fillStyle = color;
    ctx.fillRect(x - candleBodyWidth / 2, bodyTop, candleBodyWidth, bodyHeight);
  });

  // Overlay EMAs
  const closePrices = ohlc.map(b => b.close);
  if (activeEmas.has(20)) {
    const ema20 = calculateEMA(closePrices, 20);
    ctx.strokeStyle = '#F59E0B';
    ctx.lineWidth = 1.8;
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
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ema50.forEach((val, i) => {
      const x = paddingLeft + i * candleSlot + candleSlot / 2;
      const y = getY(val);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // Time Axis Labels (5-6 sample labels)
  ctx.fillStyle = '#64748B';
  ctx.font = '10px Sora, sans-serif';
  ctx.textAlign = 'center';
  const step = Math.max(1, Math.floor(n / 5));
  for (let i = 0; i < n; i += step) {
    const x = paddingLeft + i * candleSlot + candleSlot / 2;
    ctx.fillText(ohlc[i].time, x, height - 12);
  }
}

function renderCurrentChart() {
  const canvas = document.getElementById('pageAssetChartCanvas');
  if (!canvas || !currentChartPoints || currentChartPoints.length === 0) return;

  if (currentChartType === 'candle') {
    if (pageChartInstance) {
      pageChartInstance.destroy();
      pageChartInstance = null;
    }
    renderCandlestickCanvas(canvas, currentChartPoints);
  } else {
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
  const isPos = lastVal >= firstVal;
  const strokeColor = isPos ? '#10B981' : '#F43F5E';
  const gradient = ctx.createLinearGradient(0, 0, 0, 350);
  gradient.addColorStop(0, isPos ? 'rgba(16, 185, 129, 0.28)' : 'rgba(244, 63, 94, 0.28)');
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

  const datasets = [{
    label: 'Price',
    data: prices,
    borderColor: strokeColor,
    borderWidth: 2.2,
    backgroundColor: gradient,
    fill: true,
    tension: 0.2,
    pointRadius: 0,
    pointHoverRadius: 6,
    pointHoverBackgroundColor: strokeColor,
    pointHoverBorderColor: '#ffffff',
    pointHoverBorderWidth: 2
  }];

  if (activeEmas.has(20)) {
    datasets.push({
      label: '20 EMA',
      data: calculateEMA(prices, 20),
      borderColor: '#F59E0B',
      borderWidth: 1.8,
      fill: false,
      tension: 0.2,
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
      tension: 0.2,
      pointRadius: 0
    });
  }

  pageChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: points.map(p => p.time),
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: activeEmas.size > 0,
          labels: { color: '#94A3B8', font: { family: 'Sora', size: 11 } }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: '#0F172A',
          titleColor: '#94A3B8',
          bodyColor: '#F8FAFC',
          bodyFont: { weight: '800', size: 14, family: 'Sora' },
          padding: 10,
          displayColors: false,
          callbacks: {
            label: (item) => `${item.dataset.label || 'Price'}: ${formatINR(item.parsed.y)}`
          }
        }
      },
      scales: {
        x: { 
          display: true,
          grid: { display: false },
          ticks: {
            color: '#64748B',
            font: { family: 'Sora', size: 10 },
            maxTicksLimit: 6
          }
        },
        y: { 
          display: true,
          position: 'right',
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#64748B',
            font: { family: 'Sora', size: 11 },
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
  }
  currentChartRange = range;
  if (!currentPageAsset) return;

  try {
    const assetType = currentPageAsset.asset_type || 'STOCK';
    const res = await fetch(`/api/history?symbol=${encodeURIComponent(currentPageAsset.symbol)}&asset_type=${encodeURIComponent(assetType)}&range=${range}&timeframe=${range}`);
    const raw = await res.json();
    const points = Array.isArray(raw) ? raw : (raw.points || []);
    currentChartPoints = points;
    renderCurrentChart();
  } catch (err) {
    console.error('Failed to load chart:', err);
  }
}

function setPageOrderAction(action) {
  pageOrderState.action = action;
  const buyBtn = document.getElementById('pageBtnBuy');
  const sellBtn = document.getElementById('pageBtnSell');
  const execBtn = document.getElementById('pageOrderExecuteBtn');
  const cleanSym = currentPageAsset ? currentPageAsset.symbol.replace('.NS', '') : 'ASSET';

  if (action === 'BUY') {
    if (buyBtn) buyBtn.className = 'trade-tab-btn active buy';
    if (sellBtn) sellBtn.className = 'trade-tab-btn sell';
    if (execBtn) {
      execBtn.className = 'btn-trade-execute buy';
      execBtn.innerText = `BUY ${cleanSym}`;
    }
  } else {
    if (buyBtn) buyBtn.className = 'trade-tab-btn buy';
    if (sellBtn) sellBtn.className = 'trade-tab-btn active sell';
    if (execBtn) {
      execBtn.className = 'btn-trade-execute sell';
      execBtn.innerText = `SELL ${cleanSym}`;
    }
  }
  recalcPageMargin();
}

function quickMobileTrade(action) {
  setPageOrderAction(action);
  const terminal = document.querySelector('.asset-sidebar-col');
  if (terminal) {
    terminal.scrollIntoView({ behavior: 'smooth', block: 'center' });
    terminal.classList.add('pulse-highlight');
    setTimeout(() => terminal.classList.remove('pulse-highlight'), 1200);
  }
}

function setPageProductType(prod) {
  pageOrderState.product = prod;
  document.getElementById('pageProdDelivery').className = `seg-btn ${prod === 'DELIVERY' ? 'active' : ''}`;
  document.getElementById('pageProdIntraday').className = `seg-btn ${prod === 'INTRADAY' ? 'active' : ''}`;
  document.getElementById('pageLeverageHint').style.display = prod === 'INTRADAY' ? 'flex' : 'none';
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

  const limitGroup = document.getElementById('pageLimitPriceGroup');
  const trigGroup = document.getElementById('pageTriggerPriceGroup');
  if (limitGroup) limitGroup.style.display = (varType === 'LIMIT' || varType === 'STOP_LOSS' || varType === 'GTT') ? 'block' : 'none';
  if (trigGroup) trigGroup.style.display = (varType === 'STOP_LOSS' || varType === 'GTT') ? 'block' : 'none';

  const trigHint = document.getElementById('pageTriggerHint');
  if (trigHint) {
    trigHint.innerText = varType === 'GTT' 
      ? 'Good-Till-Triggered order remains active until trigger is reached' 
      : 'Order activates when market hits this stop-loss trigger';
  }

  const execBtn = document.getElementById('pageOrderExecuteBtn');
  if (execBtn && !isGuest()) {
    if (varType === 'STOP_LOSS') {
      execBtn.innerText = `PLACE STOP-LOSS (${pageOrderState.action})`;
    } else if (varType === 'GTT') {
      execBtn.innerText = `CREATE GTT TRIGGER (${pageOrderState.action})`;
    } else {
      execBtn.innerText = `${pageOrderState.action} ${currentPageAsset ? (currentPageAsset.symbol || '').replace('.NS', '') : ''}`;
    }
  }

  recalcPageMargin();
}

function stepPageQuantity(delta) {
  const input = document.getElementById('pageOrderQuantity');
  let val = parseInt(input.value || '1', 10) + delta;
  if (val < 1) val = 1;
  input.value = val;
  pageOrderState.quantity = val;
  recalcPageMargin();
}

function setPageQuickQuantity(qty) {
  document.getElementById('pageOrderQuantity').value = qty;
  pageOrderState.quantity = qty;
  recalcPageMargin();
}

function recalcPageMargin() {
  if (!currentPageAsset) return;
  const qty = parseInt(document.getElementById('pageOrderQuantity').value || '1', 10);
  const effectivePrice = (pageOrderState.variety === 'LIMIT' || pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT')
    ? parseFloat(document.getElementById('pageOrderLimitPrice').value || currentPageAsset.price)
    : currentPageAsset.price;

  const total = qty * effectivePrice;
  const margin = pageOrderState.product === 'INTRADAY' ? total * 0.20 : total;

  document.getElementById('pageRequiredMargin').innerText = formatINR(margin);
  
  const execBtn = document.getElementById('pageOrderExecuteBtn');
  if (isGuest()) {
    document.getElementById('pageAvailableCash').innerText = '₹0.00 (Locked)';
    if (execBtn) {
      execBtn.innerText = 'Start Investing to Trade (Unlock ₹10L)';
      execBtn.className = 'btn-trade-execute guest-locked';
    }
  } else {
    const availCash = state.account ? state.account.balance : (currentUser ? currentUser.balance : 1000000.0);
    document.getElementById('pageAvailableCash').innerText = formatINR(availCash);
    if (execBtn) {
      execBtn.className = `btn-trade-execute ${pageOrderState.action.toLowerCase()}`;
      if (pageOrderState.variety === 'STOP_LOSS') {
        execBtn.innerText = `PLACE STOP-LOSS (${pageOrderState.action})`;
      } else if (pageOrderState.variety === 'GTT') {
        execBtn.innerText = `CREATE GTT TRIGGER (${pageOrderState.action})`;
      } else {
        execBtn.innerText = `${pageOrderState.action} ${currentPageAsset.symbol || ''}`;
      }
    }
  }
}

async function updatePageAvailableHolding(symbol) {
  try {
    const res = await fetch('/api/portfolio');
    const data = await res.json();
    const holding = (data.holdings || []).find(h => h.symbol === symbol);
    const qty = holding ? holding.quantity : 0;
    const label = document.getElementById('pageAvailableHoldingQty');
    if (label) label.innerText = `${qty} shares owned`;
  } catch (err) {}
}

async function executePageTrade() {
  if (isGuest()) {
    showToast('Please create your free account to unlock ₹10,00,000 virtual balance and start trading.', false);
    navigateTo('/onboarding');
    return;
  }

  const execBtn = document.getElementById('pageOrderExecuteBtn');
  if (execBtn && execBtn.disabled) return;

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

  const qty = parseInt(document.getElementById('pageOrderQuantity').value || '1', 10);
  if (!qty || qty <= 0 || isNaN(qty)) {
    showToast('Please specify a valid quantity (minimum 1)', true);
    return;
  }

  const limitPrice = (pageOrderState.variety === 'LIMIT' || pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT')
    ? parseFloat(document.getElementById('pageOrderLimitPrice').value || currentPageAsset.price)
    : null;

  if (pageOrderState.variety === 'LIMIT' && (!limitPrice || limitPrice <= 0 || isNaN(limitPrice))) {
    showToast('Please enter a valid Limit Price', true);
    return;
  }

  const triggerPrice = (pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT')
    ? parseFloat(document.getElementById('pageOrderTriggerPrice').value || '0')
    : 0.0;

  if ((pageOrderState.variety === 'STOP_LOSS' || pageOrderState.variety === 'GTT') && (!triggerPrice || triggerPrice <= 0 || isNaN(triggerPrice))) {
    showToast('Please enter a valid Trigger Price', true);
    return;
  }

  const originalBtnText = execBtn ? execBtn.innerText : '';
  if (execBtn) {
    execBtn.disabled = true;
    execBtn.innerText = 'Executing Order...';
  }

  try {
    let res, result;
    if (pageOrderState.variety === 'GTT') {
      res = await fetch('/api/order/gtt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: currentPageAsset.symbol,
          transaction_type: pageOrderState.action,
          quantity: qty,
          trigger_price: triggerPrice,
          limit_price: limitPrice || triggerPrice
        })
      });
      result = await res.json();
    } else {
      res = await fetch('/api/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: currentPageAsset.symbol,
          name: currentPageAsset.name,
          asset_type: currentPageAsset.asset_type || 'STOCK',
          order_type: pageOrderState.action,
          product_type: pageOrderState.product,
          quantity: qty,
          price: currentPageAsset.price,
          order_variety: pageOrderState.variety,
          limit_price: limitPrice,
          trigger_price: triggerPrice
        })
      });
      result = await res.json();
    }

    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'Trade execution failed', true);
      return;
    }

    showToast(result.message || `${pageOrderState.action} order placed successfully!`);
    await fetchAccount();
    await fetchPortfolio();
    await fetchPositions();
    await fetchOrders();
    updatePageAvailableHolding(currentPageAsset.symbol);
    recalcPageMargin();

    openOrderSuccessModal({
      symbol: currentPageAsset.symbol,
      name: currentPageAsset.name,
      action: pageOrderState.action,
      product: pageOrderState.product,
      quantity: qty,
      price: (pageOrderState.variety === 'LIMIT' || pageOrderState.variety === 'STOP_LOSS') ? (limitPrice || currentPageAsset.price) : currentPageAsset.price,
      total: qty * ((pageOrderState.variety === 'LIMIT' || pageOrderState.variety === 'STOP_LOSS') ? (limitPrice || currentPageAsset.price) : currentPageAsset.price)
    });

  } catch (err) {
    console.error('executePageTrade error:', err);
    showToast('Failed to connect to trade server', true);
  } finally {
    if (execBtn) {
      execBtn.disabled = false;
      execBtn.innerText = originalBtnText;
    }
  }
}

/* =======================================================
   GROWW-STYLE ACCOUNT ONBOARDING WIZARD ENGINE (AUTHENTIC USER-TYPED)
   ======================================================= */
let obCurrentStep = 1;
let obUserData = {
  phone: '',
  email: '',
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
  const panInput = document.getElementById('obInputPan');
  if (panInput) panInput.value = '';
  const nameInput = document.getElementById('obInputName');
  if (nameInput) nameInput.value = '';
  const dobInput = document.getElementById('obInputDob');
  if (dobInput) dobInput.value = '';
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

  const panPill = document.getElementById('panVerifiedPill');
  if (panPill) panPill.style.display = 'none';
  const smsBanner = document.getElementById('smsPushBanner');
  if (smsBanner) smsBanner.style.display = 'none';

  goToObStep(1);
  window.scrollTo({ top: 0, behavior: 'smooth' });
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
  const activeContent = document.getElementById(`obStep-${stepNum}`);
  if (activeContent) activeContent.classList.add('active');
}

function submitObStep1() {
  const phone = document.getElementById('obInputPhone').value.trim();
  const email = document.getElementById('obInputEmail').value.trim();
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
  obUserData.phone = phone;
  obUserData.email = email;
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
  const pill = document.getElementById('panVerifiedPill');
  if (el.value.length === 10) {
    if (pill) pill.style.display = 'inline-flex';
  } else {
    if (pill) pill.style.display = 'none';
  }
}

function submitObStep3() {
  const pan = document.getElementById('obInputPan').value.trim().toUpperCase();
  const name = document.getElementById('obInputName').value.trim();
  const dob = document.getElementById('obInputDob').value;
  const gender = document.getElementById('obInputGender').value;
  const occupation = document.getElementById('obInputOccupation')?.value || 'Private Sector';
  const income = document.getElementById('obInputIncome')?.value || '₹1L - ₹5L';

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

  obUserData.pan = pan;
  obUserData.name = name;
  obUserData.dob = dob;
  obUserData.gender = gender;
  obUserData.occupation = occupation;
  obUserData.income = income;

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
        email: obUserData.email,
        phone: obUserData.phone,
        pan: obUserData.pan,
        bank_name: obUserData.bank_name,
        bank_account: obUserData.bank_account,
        pin: obUserData.pin
      })
    });
    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.detail || 'Failed to create account', true);
      return;
    }

    currentUser = result.user;
    localStorage.setItem('stoxify_user_id', currentUser.id);

    // Update Confirmation screen with user's actual entered details
    document.getElementById('obWelcomeName').innerText = currentUser.name;
    document.getElementById('obCreatedDemat').innerText = `STOX-${Math.floor(100000 + Math.random() * 900000)}`;
    const emailEl = document.getElementById('obCreatedEmail');
    if (emailEl) emailEl.innerText = currentUser.email || obUserData.email || '';
    const last4 = (currentUser.bank_account || '5678').slice(-4);
    document.getElementById('obCreatedBank').innerText = `${currentUser.bank_name} •••• ${last4} (Verified ✓)`;

    updateNavbarProfile();
    fetchAccount();
    goToObStep(6);

  } catch (err) {
    showToast('Error connecting to onboarding server', true);
  }
}


function finishOnboarding() {
  navigateTo('/explore');
  showToast(`Welcome to Stoxify, ${currentUser.name}! ₹10,00,000 virtual cash credited!`);
}


/* =======================================================
   ORDER CONFIRMATION MODAL HELPERS
   ======================================================= */
function openOrderSuccessModal(orderData) {
  const modal = document.getElementById('orderSuccessModal');
  if (!modal) return;

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

  const viewBtn = document.getElementById('orderSuccessViewBtn');
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
   1. GTT & TRIGGER ORDERS ENGINE
   ======================================================= */
async function loadGttOrders() {
  if (isGuest()) return;
  try {
    const res = await fetch('/api/orders/gtt');
    const orders = await res.json();
    const countEl = document.getElementById('gttOrdersCount');
    if (countEl) countEl.innerText = orders.length;

    const tbody = document.getElementById('gttOrdersTableBody');
    const mobList = document.getElementById('gttOrdersMobileList');

    if (!orders || orders.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3rem;">No active GTT or Stop-Loss triggers.</td></tr>';
      if (mobList) mobList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No active triggers.</div>';
      return;
    }

    if (tbody) {
      tbody.innerHTML = orders.map(o => `
        <tr>
          <td><code style="font-size: 0.8rem; color: var(--text-muted);">${o.order_id}</code></td>
          <td><strong>${o.symbol.replace('.NS', '')}</strong></td>
          <td><span class="badge-${o.transaction_type === 'BUY' ? 'positive' : 'negative'}">${o.transaction_type}</span></td>
          <td><strong>${formatINR(o.trigger_price)}</strong></td>
          <td>${formatINR(o.limit_price)}</td>
          <td>${o.quantity}</td>
          <td>${new Date(o.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
          <td><span class="pill-btn" style="color: var(--brand-cyan); font-size: 0.72rem;">${o.status}</span></td>
          <td style="text-align: right;">
            <button class="btn-cancel-small" onclick="cancelGttOrder('${o.order_id}')">Cancel</button>
          </td>
        </tr>
      `).join('');
    }

    if (mobList) {
      mobList.innerHTML = orders.map(o => `
        <div class="mobile-order-card">
          <div class="mob-order-header">
            <strong>${o.symbol.replace('.NS', '')}</strong>
            <span class="badge-${o.transaction_type === 'BUY' ? 'positive' : 'negative'}">${o.transaction_type}</span>
          </div>
          <div class="mob-order-row">
            <span>Trigger Price</span><strong>${formatINR(o.trigger_price)}</strong>
          </div>
          <div class="mob-order-row">
            <span>Limit Price</span><span>${formatINR(o.limit_price)}</span>
          </div>
          <div class="mob-order-row">
            <span>Quantity</span><span>${o.quantity}</span>
          </div>
          <div class="mob-order-row">
            <span>Status</span><span class="pill-btn" style="color: var(--brand-cyan);">${o.status}</span>
          </div>
          <div style="margin-top: 0.75rem; text-align: right;">
            <button class="btn-cancel-small" onclick="cancelGttOrder('${o.order_id}')">Cancel Trigger</button>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load GTT orders:', err);
  }
}

async function cancelGttOrder(orderId) {
  try {
    const res = await fetch(`/api/order/gtt/${orderId}`, { method: 'DELETE' });
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
  const tbody = document.getElementById('foTableBody');
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
  const tbody = document.getElementById('foTableBody');
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
  const bal = state.account ? state.account.balance : 1000000.0;
  if (cashEl) cashEl.innerText = formatINR(bal);
}

async function submitOptionTrade() {
  if (!currentOptionTrade) return;
  const lots = parseInt(document.getElementById('optModalLots').value || '1', 10);
  const totalQty = lots * currentOptionTrade.lotSize;
  const symbol = `${currentOptionTrade.underlying}_${currentOptionTrade.strike}_${currentOptionTrade.optType}`;

  const execBtn = document.getElementById('optExecuteBtn');
  if (execBtn) {
    execBtn.disabled = true;
    execBtn.innerText = 'Executing Option Trade...';
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
      showToast(result.detail || result.error || 'Option execution failed', true);
      return;
    }

    showToast(`${currentOptionTrade.action} ${lots} lot(s) executed at ${formatINR(currentOptionTrade.ltp)}!`);
    closeOptionBuyModal();
    await fetchAccount();
    await fetchPositions();
    await fetchOrders();
  } catch (err) {
    showToast('Failed to execute option trade', true);
  } finally {
    if (execBtn) execBtn.disabled = false;
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

function filterIpos(filter, btn) {
  activeIpoFilter = filter;
  if (btn) {
    document.querySelectorAll('#explore-ipo-container .pill-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
  renderIpos(filter);
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
  const bal = state.account ? state.account.balance : 1000000.0;
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
        ipo_id: currentIpoModalData.id,
        lots: lots,
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

  try {
    const res = await fetch('/api/mf/sip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: sym,
        amount: amount,
        installment_day: day
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
    const res = await fetch('/api/mf/sips');
    const sips = await res.json();

    const tbody = document.getElementById('sipsTableBody');
    const mobList = document.getElementById('sipsMobileList');

    if (!sips || sips.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 3rem;">No active SIP schedules.</td></tr>';
      if (mobList) mobList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No active SIP schedules.</div>';
      return;
    }

    if (tbody) {
      tbody.innerHTML = sips.map(s => `
        <tr>
          <td><strong>${s.symbol.replace('.NS', '')}</strong></td>
          <td><strong style="color: var(--accent-green);">${formatINR(s.amount)}</strong></td>
          <td>${s.installment_day}th of month</td>
          <td>${s.next_trigger_date}</td>
          <td>${s.installments_completed || 0}</td>
          <td><span class="badge-positive">${s.status}</span></td>
          <td style="text-align: right;">
            <button class="btn-cancel-small" onclick="cancelSip('${s.sip_id}')">Stop SIP</button>
          </td>
        </tr>
      `).join('');
    }

    if (mobList) {
      mobList.innerHTML = sips.map(s => `
        <div class="mobile-order-card">
          <div class="mob-order-header">
            <strong>${s.symbol.replace('.NS', '')}</strong>
            <span class="badge-positive">${s.status}</span>
          </div>
          <div class="mob-order-row">
            <span>Monthly Amount</span><strong style="color: var(--accent-green);">${formatINR(s.amount)}</strong>
          </div>
          <div class="mob-order-row">
            <span>Debit Date</span><span>${s.installment_day}th Monthly</span>
          </div>
          <div class="mob-order-row">
            <span>Next Execution</span><span>${s.next_trigger_date}</span>
          </div>
          <div style="margin-top: 0.75rem; text-align: right;">
            <button class="btn-cancel-small" onclick="cancelSip('${s.sip_id}')">Stop SIP</button>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load SIPs:', err);
  }
}

async function cancelSip(sipId) {
  try {
    const res = await fetch(`/api/mf/sip/${sipId}`, { method: 'DELETE' });
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
    // 1. Sector Allocation
    const secRes = await fetch('/api/analytics/sector-allocation');
    const secData = await secRes.json();
    const secContainer = document.getElementById('sectorDiversificationBars');

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
    const taxRes = await fetch('/api/analytics/tax-report');
    const taxData = await taxRes.json();
    
    const stcgRealized = document.getElementById('taxStcgRealized');
    const stcgPayable = document.getElementById('taxStcgPayable');
    const ltcgRealized = document.getElementById('taxLtcgRealized');
    const ltcgTaxable = document.getElementById('taxLtcgTaxable');
    const ltcgPayable = document.getElementById('taxLtcgPayable');
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
