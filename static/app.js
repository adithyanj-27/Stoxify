// BrokeAhh — Core Client Application Logic & Feature Engine

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
  const saved = localStorage.getItem('brokeahh_theme') || localStorage.getItem('growwfahh_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('brokeahh_theme', next);
  updateThemeIcon(next);
  if (state.chartInstance && state.currentModalAsset) {
    loadChartTimeframe(state.currentModalTimeframe);
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

    dot.className = `pulse-dot ${data.badge_color || 'gray'}`;
    label.innerText = data.status_text;

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
function switchTab(tabId) {
  state.currentTab = tabId;

  // Desktop links
  document.querySelectorAll('.nav-links .nav-btn').forEach(btn => btn.classList.remove('active'));
  const desktopBtn = document.getElementById(`nav-${tabId}`);
  if (desktopBtn) desktopBtn.classList.add('active');

  // Mobile bar items
  document.querySelectorAll('.mobile-nav-item').forEach(btn => btn.classList.remove('active'));
  const mobBtn = document.getElementById(`mob-nav-${tabId}`);
  if (mobBtn) mobBtn.classList.add('active');

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

function switchExploreSubnav(subId) {
  state.exploreSubnav = subId;
  document.querySelectorAll('#pane-explore .sub-nav-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`subnav-${subId}`).classList.add('active');

  if (subId === 'stocks') {
    document.getElementById('explore-stocks-container').style.display = 'block';
    document.getElementById('explore-mf-container').style.display = 'none';
  } else {
    document.getElementById('explore-stocks-container').style.display = 'none';
    document.getElementById('explore-mf-container').style.display = 'block';
    renderExploreMutualFunds();
  }
}

function switchOrdersSubnav(subId) {
  state.ordersSubnav = subId;
  document.querySelectorAll('#pane-orders .sub-nav-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`subnav-${subId}`).classList.add('active');

  if (subId === 'executed') {
    document.getElementById('orders-executed-container').style.display = 'block';
    document.getElementById('orders-open-container').style.display = 'none';
  } else {
    document.getElementById('orders-executed-container').style.display = 'none';
    document.getElementById('orders-open-container').style.display = 'block';
  }
}

// --- Account Balance & Header ---
async function fetchAccount() {
  try {
    const res = await fetch('/api/account');
    const data = await res.json();
    state.account = data;
    document.getElementById('navBalanceDisplay').innerText = formatINR(data.balance);
    document.getElementById('summaryAvailableBalance').innerText = formatINR(data.balance);
    document.getElementById('fundsCurrentBalance').innerText = formatINR(data.balance);
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

function renderExploreStocks() {
  if (!state.exploreData || !state.exploreData.all_stocks) return;
  const grid = document.getElementById('stocksGrid');
  const title = document.getElementById('exploreStocksTitle');
  const desc = document.getElementById('exploreStocksDesc');

  let list = [];
  if (state.exploreStockFilter === 'all') {
    list = state.exploreData.all_stocks;
    title.innerText = `Explore Top Stocks (${list.length} available)`;
    if (desc) desc.innerText = 'Live market quotes directly from National Stock Exchange (NSE)';
  } else if (state.exploreStockFilter === 'gainers') {
    list = state.exploreData.gainers;
    title.innerText = 'Top Gainers Today (NSE)';
  } else if (state.exploreStockFilter === 'losers') {
    list = state.exploreData.losers;
    title.innerText = 'Top Losers Today (NSE)';
  } else {
    list = state.exploreData.all_stocks.filter(s => s.sector && s.sector.toLowerCase().includes(state.exploreStockFilter.toLowerCase()));
    title.innerText = `${state.exploreStockFilter} Equities (${list.length})`;
    if (list.length === 0) list = state.exploreData.all_stocks;
  }

  grid.innerHTML = list.map(s => {
    const isPos = s.change >= 0;
    const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
    const initial = (s.symbol || 'S').charAt(0).toUpperCase();

    return `
      <div class="stock-card" onclick="openAssetModal('${s.symbol}', 'STOCK')">
        <div class="card-top">
          <div style="display: flex; gap: 0.75rem; align-items: center; overflow: hidden;">
            <div class="card-avatar">${initial}</div>
            <div class="card-info">
              <div class="card-title">${s.name}</div>
              <div class="card-subtitle">${s.symbol} • ${s.sector || 'NSE'}</div>
            </div>
          </div>
        </div>
        <div class="card-bottom">
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">Market Price</div>
            <div class="card-price">${formatINR(s.price)}</div>
          </div>
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
          <div style="display: flex; gap: 0.75rem; align-items: center; overflow: hidden;">
            <div class="card-avatar" style="background: var(--accent-gold-bg); color: var(--accent-gold); border-color: rgba(255,107,0,0.3);">
              MF
            </div>
            <div class="card-info">
              <div class="card-title">${mf.name}</div>
              <div class="card-subtitle">${mf.category} • ${mf.fund_house}</div>
            </div>
          </div>
        </div>
        <div class="card-bottom">
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">NAV</div>
            <div class="card-price">${formatINR(mf.price)}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">1Y Return</div>
            <div class="badge-positive" style="background: rgba(0, 208, 156, 0.15);">
              +${formatNumber(mf.return_1y)}%
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// --- Holdings View (Delivery CNC) ---
async function fetchPortfolio() {
  try {
    const res = await fetch('/api/portfolio');
    const data = await res.json();
    state.account.balance = data.balance;

    document.getElementById('navBalanceDisplay').innerText = formatINR(data.balance);
    document.getElementById('summaryAvailableBalance').innerText = formatINR(data.balance);
    document.getElementById('summaryCurrentVal').innerText = formatINR(data.current_value);
    document.getElementById('summaryInvestedVal').innerText = formatINR(data.invested_amount);

    const isTotalPos = data.total_returns >= 0;
    const totalReturnsEl = document.getElementById('summaryTotalReturns');
    totalReturnsEl.innerText = formatINR(data.total_returns);
    totalReturnsEl.className = `banner-metric-val ${isTotalPos ? 'text-positive' : 'text-negative'}`;

    const totalPctEl = document.getElementById('summaryTotalReturnsPct');
    totalPctEl.innerHTML = `<span class="${isTotalPos ? 'text-positive' : 'text-negative'}">${isTotalPos ? '+' : ''}${formatNumber(data.total_returns_pct)}%</span>`;

    const isDayPos = data.day_returns >= 0;
    const dayPnlEl = document.getElementById('summaryTodayPnl');
    dayPnlEl.innerHTML = `<span class="${isDayPos ? 'text-positive' : 'text-negative'}">1D: ${isDayPos ? '+' : ''}${formatINR(data.day_returns)} (${isDayPos ? '+' : ''}${formatNumber(data.day_returns_pct)}%)</span>`;

    const tableBody = document.getElementById('holdingsTableBody');
    const mobileList = document.getElementById('holdingsMobileList');

    if (data.holdings.length === 0) {
      tableBody.innerHTML = `
        <tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3.5rem;">No active holdings yet. Head to Explore to invest!</td></tr>
      `;
      mobileList.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No active holdings yet.</div>
      `;
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
          <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem; background: var(--accent-gold-bg); color: var(--accent-gold); border-color: rgba(255,107,0,0.3);">Intraday 5x</span></td>
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
              <div class="mobile-card-symbol">${p.symbol} <span class="pill-btn" style="padding: 1px 5px; font-size: 0.65rem; background: var(--accent-gold-bg); color: var(--accent-gold);">MIS 5x</span></div>
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

    if (openOrders.length > 0) {
      navOrdersBadge.innerText = openOrders.length;
      navOrdersBadge.style.display = 'inline-flex';
      mobOpenOrdersBadge.innerText = openOrders.length;
      mobOpenOrdersBadge.style.display = 'flex';
    } else {
      navOrdersBadge.style.display = 'none';
      mobOpenOrdersBadge.style.display = 'none';
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
            <td style="font-weight: 700; color: var(--accent-gold);">${formatINR(o.limit_price || o.price)}</td>
            <td>${formatINR(o.total_amount)}</td>
            <td style="font-size: 0.75rem; color: var(--text-muted);">${o.timestamp || 'Today'}</td>
            <td><span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem; color: var(--accent-gold);">OPEN</span></td>
            <td style="text-align: right;">
              <button class="btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="cancelOrder(${o.id})">Cancel</button>
            </td>
          </tr>
        `;
      }).join('');

      openMobileList.innerHTML = openOrders.map(o => {
        const isBuy = o.order_type === 'BUY';
        return `
          <div class="mobile-card-item" style="border-left: 4px solid var(--accent-gold);">
            <div class="mobile-card-top">
              <div>
                <div class="mobile-card-symbol">${o.symbol} <span class="badge-${isBuy ? 'positive' : 'negative'}">${o.order_type} LIMIT</span></div>
                <div class="mobile-card-name">Order #${o.id} • ${o.product_type}</div>
              </div>
              <div class="mobile-card-price">
                <span style="color: var(--accent-gold);">${formatINR(o.limit_price || o.price)}</span>
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
      return `
        <div class="stock-card" onclick="openAssetModal('${item.symbol}', '${item.asset_type}')">
          <div class="card-top">
            <div style="display: flex; gap: 0.75rem; align-items: center;">
              <div class="card-avatar">${(item.symbol || 'S').charAt(0).toUpperCase()}</div>
              <div class="card-info">
                <div class="card-title">${item.name}</div>
                <div class="card-subtitle">${item.symbol} • ${item.asset_type}</div>
              </div>
            </div>
            <button class="icon-btn" onclick="event.stopPropagation(); toggleWatchlistItem('${item.symbol}', '${item.name.replace(/'/g, "\\'")}', '${item.asset_type}')" style="color: #FFB800;">
              ★
            </button>
          </div>
          <div class="card-bottom">
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px;">Market Price</div>
              <div class="card-price">${formatINR(item.price)}</div>
            </div>
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
  if (state.currentTab === 'watchlist') fetchWatchlist();
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
          <div class="search-result-item" onclick="selectSearchResult('${r.symbol}', '${r.asset_type}')">
            <div>
              <div class="search-item-title">${r.name}</div>
              <div class="search-item-sub">${r.subtext}</div>
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
async function openAssetModal(symbol, assetType = 'STOCK', preselectAction = 'BUY') {
  document.getElementById('tradeModalOverlay').classList.add('active');
  setOrderAction(preselectAction);
  setProductType('DELIVERY');
  setOrderVariety('MARKET');
  document.getElementById('tradeQuantityInput').value = 1;

  try {
    const res = await fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}&asset_type=${encodeURIComponent(assetType)}`);
    const data = await res.json();
    state.currentModalAsset = data;

    document.getElementById('modalAvatar').innerText = (data.symbol || 'S').charAt(0).toUpperCase();
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
    if (state.currentTab === 'holdings') fetchPortfolio();
    if (state.currentTab === 'positions') fetchPositions();
    if (state.currentTab === 'orders') fetchOrders();
  } catch (err) {
    console.error('Order submission error:', err);
    showToast('Failed to connect to execution server', true);
  }
}

// --- Funds & Reset Modal ---
function openFundsModal() {
  document.getElementById('fundsModalOverlay').classList.add('active');
  document.getElementById('fundsCurrentBalance').innerText = formatINR(state.account.balance);
}

function closeFundsModal() {
  document.getElementById('fundsModalOverlay').classList.remove('active');
}

function quickAddFunds(amount) {
  document.getElementById('depositAmountInput').value = amount;
}

async function submitDeposit() {
  const amount = parseFloat(document.getElementById('depositAmountInput').value);
  if (!amount || amount <= 0) {
    showToast('Please enter a valid amount to deposit', true);
    return;
  }

  try {
    const res = await fetch('/api/account/deposit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Deposited ${formatINR(amount)} into balance`);
      await fetchAccount();
      closeFundsModal();
      document.getElementById('depositAmountInput').value = '';
    }
  } catch (err) {
    showToast('Deposit failed', true);
  }
}

async function submitResetAccount() {
  if (!confirm('Are you sure you want to reset your BrokeAhh account? This will set your balance back to ₹10,00,000 and clear all holdings, intraday positions, and order history.')) {
    return;
  }

  try {
    const res = await fetch('/api/account/reset', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('BrokeAhh account successfully reset to fresh ₹10,00,000');
      await fetchAccount();
      closeFundsModal();
      if (state.currentTab === 'holdings') fetchPortfolio();
      if (state.currentTab === 'positions') fetchPositions();
      if (state.currentTab === 'orders') fetchOrders();
    }
  } catch (err) {
    showToast('Reset failed', true);
  }
}

// --- PWA (Progressive Web App) Install Engine ---
let deferredInstallPrompt = null;

function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.navigator.standalone === true ||
         document.referrer.includes('android-app://');
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  if (!isAppInstalled()) {
    const btn = document.getElementById('btnInstallApp');
    if (btn) btn.style.display = 'inline-flex';
  }
});

async function installPWA() {
  if (!deferredInstallPrompt) {
    showToast('To install: click the Install icon (⤓) in your browser address bar');
    return;
  }
  deferredInstallPrompt.prompt();
  const { outcome } = await deferredInstallPrompt.userChoice;
  if (outcome === 'accepted') {
    const btn = document.getElementById('btnInstallApp');
    if (btn) btn.style.display = 'none';
  }
  deferredInstallPrompt = null;
}

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  const btn = document.getElementById('btnInstallApp');
  if (btn) btn.style.display = 'none';
  showToast('BrokeAhh installed successfully!');
});

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then((reg) => {
      console.log('BrokeAhh PWA Service Worker registered:', reg.scope);
    }).catch((err) => {
      console.warn('Service Worker registration skipped:', err);
    });
  });
}

// --- Initialization ---
window.addEventListener('DOMContentLoaded', () => {
  initTheme();
  
  // Hide install button immediately if already running in standalone/installed mode
  if (isAppInstalled()) {
    const btn = document.getElementById('btnInstallApp');
    if (btn) btn.style.display = 'none';
  }

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

