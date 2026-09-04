// GrowwFAHH — Core Client Application Logic

const state = {
  currentTab: 'explore',
  exploreSubnav: 'stocks',
  exploreStockFilter: 'all',
  exploreData: null,
  account: { balance: 1000000.0 },
  watchlist: new Set(),
  currentModalAsset: null,
  currentModalTimeframe: '1D',
  orderAction: 'BUY',
  productType: 'DELIVERY',
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

function formatNumber(val) {
  if (val === null || val === undefined || isNaN(val)) return '0.00';
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(val);
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
  }, 4000);
}

// --- Theme Management ---
function initTheme() {
  const saved = localStorage.getItem('growwfahh_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('growwfahh_theme', next);
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

// --- Navigation Tabs ---
function switchTab(tabId) {
  state.currentTab = tabId;
  document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

  const navBtn = document.getElementById(`nav-${tabId}`);
  const pane = document.getElementById(`pane-${tabId}`);
  if (navBtn) navBtn.classList.add('active');
  if (pane) pane.classList.add('active');

  if (tabId === 'holdings') fetchPortfolio();
  if (tabId === 'orders') fetchOrders();
  if (tabId === 'watchlist') fetchWatchlist();
  if (tabId === 'explore') fetchExploreData();
}

function switchExploreSubnav(subId) {
  state.exploreSubnav = subId;
  document.querySelectorAll('.sub-nav-btn').forEach(btn => btn.classList.remove('active'));
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
    console.error('Failed to load explore data:', err);
  }
}

function filterExploreStocks(filter) {
  state.exploreStockFilter = filter;
  document.querySelectorAll('.filter-pills .pill-btn').forEach(btn => btn.classList.remove('active'));
  if (event && event.target) {
    event.target.classList.add('active');
  }
  renderExploreStocks();
}

function renderExploreStocks() {
  if (!state.exploreData || !state.exploreData.all_stocks) return;
  const grid = document.getElementById('stocksGrid');
  let list = [];
  const title = document.getElementById('exploreStocksTitle');
  const desc = document.getElementById('exploreStocksDesc');

  if (state.exploreStockFilter === 'all') {
    list = state.exploreData.all_stocks;
    title.innerText = `Explore Top Stocks (${list.length} available)`;
    if (desc) desc.innerText = 'Live quotes directly from National Stock Exchange (NSE) & BSE';
  } else if (state.exploreStockFilter === 'gainers') {
    list = state.exploreData.gainers;
    title.innerText = 'Top Gainers Today (NSE)';
  } else if (state.exploreStockFilter === 'losers') {
    list = state.exploreData.losers;
    title.innerText = 'Top Losers Today (NSE)';
  } else {
    list = state.exploreData.all_stocks.filter(s => s.sector && s.sector.toLowerCase().includes(state.exploreStockFilter.toLowerCase()));
    title.innerText = `${state.exploreStockFilter} Stocks (${list.length})`;
    if (list.length === 0) {
      list = state.exploreData.all_stocks;
    }
  }

  grid.innerHTML = list.map(s => {
    const isPos = s.change >= 0;
    const colorClass = isPos ? 'text-positive' : 'text-negative';
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
    const isPos = mf.change >= 0;
    const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
    return `
      <div class="stock-card" onclick="openAssetModal('${mf.symbol}', 'MUTUAL_FUND')">
        <div class="card-top">
          <div style="display: flex; gap: 0.75rem; align-items: center; overflow: hidden;">
            <div class="card-avatar" style="background: var(--brand-orange-bg); color: var(--brand-orange); border-color: rgba(255,107,0,0.3);">
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

// --- Holdings View ---
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
    if (data.holdings.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3.5rem;">
            No active investments yet. Head to Explore to build your portfolio!
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = data.holdings.map(h => {
      const isPosTotal = h.total_pnl >= 0;
      const isPosDay = h.today_pnl >= 0;
      return `
        <tr>
          <td>
            <div style="font-weight: 700;">${h.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${h.symbol}</div>
          </td>
          <td>
            <span class="pill-btn" style="padding: 0.15rem 0.5rem; font-size: 0.7rem;">
              ${h.asset_type === 'MUTUAL_FUND' ? 'Mutual Fund' : 'Stock'}
            </span>
          </td>
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
            <button class="btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; margin-right: 0.4rem;" onclick="openAssetModal('${h.symbol}', '${h.asset_type}', 'SELL')">
              Sell
            </button>
            <button class="btn-primary" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="openAssetModal('${h.symbol}', '${h.asset_type}', 'BUY')">
              Buy
            </button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to fetch portfolio:', err);
  }
}

// --- Orders View ---
async function fetchOrders() {
  try {
    const res = await fetch('/api/orders');
    const orders = await res.json();
    const tableBody = document.getElementById('ordersTableBody');

    if (orders.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3rem;">
            No transactions executed yet.
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = orders.map(o => {
      const isBuy = o.order_type === 'BUY';
      return `
        <tr>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${o.timestamp}</td>
          <td>
            <div style="font-weight: 700;">${o.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${o.symbol}</div>
          </td>
          <td>
            <span class="${isBuy ? 'badge-positive' : 'badge-negative'}" style="font-weight: 700; text-transform: uppercase;">
              ${o.order_type}
            </span>
          </td>
          <td style="font-size: 0.8rem; color: var(--text-secondary);">${o.product_type}</td>
          <td style="font-weight: 600;">${o.quantity}</td>
          <td>${formatINR(o.price)}</td>
          <td style="font-weight: 700;">${formatINR(o.total_amount)}</td>
          <td style="font-weight: 600;" class="${o.realized_pnl >= 0 ? 'text-positive' : 'text-negative'}">
            ${o.order_type === 'SELL' ? (o.realized_pnl >= 0 ? '+' : '') + formatINR(o.realized_pnl) : '—'}
          </td>
          <td>
            <span style="color: var(--brand-green); font-size: 0.75rem; font-weight: 700; background: var(--brand-green-bg); padding: 0.2rem 0.5rem; border-radius: 4px;">
              ${o.status}
            </span>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to fetch orders:', err);
  }
}

// --- Watchlist View ---
async function fetchWatchlist() {
  try {
    const res = await fetch('/api/watchlist');
    const items = await res.json();
    state.watchlist = new Set(items.map(x => x.symbol));
    const grid = document.getElementById('watchlistGrid');

    if (items.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 3rem;">
          Your watchlist is empty. Add instruments to track their live market performance!
        </div>
      `;
      return;
    }

    grid.innerHTML = items.map(item => {
      const isPos = item.change >= 0;
      const badgeClass = isPos ? 'badge-positive' : 'badge-negative';
      return `
        <div class="stock-card" onclick="openAssetModal('${item.symbol}', '${item.asset_type}')">
          <div class="card-top">
            <div style="display: flex; gap: 0.75rem; align-items: center; overflow: hidden;">
              <div class="card-avatar">${item.symbol.charAt(0).toUpperCase()}</div>
              <div class="card-info">
                <div class="card-title">${item.name}</div>
                <div class="card-subtitle">${item.symbol}</div>
              </div>
            </div>
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

// --- Search Bar & Autocomplete ---
let searchDebounceTimeout = null;
const searchInput = document.getElementById('globalSearchInput');
const searchDropdown = document.getElementById('searchResultsDropdown');

searchInput.addEventListener('input', (e) => {
  clearTimeout(searchDebounceTimeout);
  const q = e.target.value.trim();
  if (!q) {
    searchDropdown.style.display = 'none';
    return;
  }
  searchDebounceTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const results = await res.json();
      if (results.length === 0) {
        searchDropdown.innerHTML = '<div style="padding: 1rem; color: var(--text-muted); text-align: center; font-size: 0.85rem;">No matching securities found</div>';
      } else {
        searchDropdown.innerHTML = results.map(r => `
          <div class="search-item" onclick="selectSearchResult('${r.symbol}', '${r.asset_type}')">
            <div>
              <div style="font-weight: 700; font-size: 0.875rem;">${r.name}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${r.symbol}</div>
            </div>
            <span class="pill-btn" style="padding: 0.2rem 0.5rem; font-size: 0.7rem;">
              ${r.subtext || r.asset_type}
            </span>
          </div>
        `).join('');
      }
      searchDropdown.style.display = 'block';
    } catch (err) {
      console.error('Search error:', err);
    }
  }, 250);
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

    const isPos = data.change >= 0;
    const badge = document.getElementById('modalChangeBadge');
    badge.className = isPos ? 'badge-positive' : 'badge-negative';
    badge.innerText = formatChange(data.change, data.change_pct);

    document.getElementById('modalDayLow').innerText = `Low: ${formatINR(data.day_low || data.price * 0.99)}`;
    document.getElementById('modalDayHigh').innerText = `High: ${formatINR(data.day_high || data.price * 1.01)}`;

    // Fundamentals
    const fundContainer = document.getElementById('modalFundamentals');
    if (data.asset_type === 'STOCK') {
      fundContainer.innerHTML = `
        <div><span style="color: var(--text-muted);">Market Cap:</span> <strong>${data.market_cap ? '₹' + (data.market_cap / 1e7).toFixed(1) + ' Cr' : '—'}</strong></div>
        <div><span style="color: var(--text-muted);">P/E Ratio:</span> <strong>${data.pe_ratio || '—'}</strong></div>
        <div><span style="color: var(--text-muted);">52W High:</span> <strong>${formatINR(data.fifty_two_week_high)}</strong></div>
        <div><span style="color: var(--text-muted);">52W Low:</span> <strong>${formatINR(data.fifty_two_week_low)}</strong></div>
      `;
    } else {
      fundContainer.innerHTML = `
        <div><span style="color: var(--text-muted);">Category:</span> <strong>${data.category || 'Equity'}</strong></div>
        <div><span style="color: var(--text-muted);">Fund House:</span> <strong>${data.fund_house || 'AMC'}</strong></div>
        <div><span style="color: var(--text-muted);">1Y Returns:</span> <strong>+${formatNumber(data.return_1y)}%</strong></div>
        <div><span style="color: var(--text-muted);">NAV Date:</span> <strong>${data.nav_date || 'Today'}</strong></div>
      `;
    }

    // Watchlist button
    renderModalWatchlistBtn(data.symbol, data.name, data.asset_type);

    calculateOrderMargin();
    loadChartTimeframe('1D');
  } catch (err) {
    console.error('Failed to load asset details:', err);
    showToast('Failed to load instrument data', true);
  }
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
  renderModalWatchlistBtn(symbol, name, assetType);
  if (state.currentTab === 'watchlist') fetchWatchlist();
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
  event && event.target && event.target.classList.add('active');

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

  if (state.chartInstance) {
    state.chartInstance.destroy();
  }

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const labels = points.map(p => p.time);
  const values = points.map(p => p.value);

  const isPos = values[values.length - 1] >= values[0];
  const strokeColor = isPos ? '#00D09C' : '#EB5B3C';
  
  const gradient = ctx.createLinearGradient(0, 0, 0, 240);
  gradient.addColorStop(0, isPos ? 'rgba(0, 208, 156, 0.28)' : 'rgba(235, 91, 60, 0.28)');
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
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDark ? '#1C2230' : '#FFFFFF',
          titleColor: isDark ? '#F0F4F8' : '#0F172A',
          bodyColor: strokeColor,
          borderColor: isDark ? '#2B3548' : '#E2E8F0',
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          callbacks: {
            label: (ctx) => `Price: ${formatINR(ctx.parsed.y)}`
          }
        }
      },
      scales: {
        x: {
          display: false
        },
        y: {
          position: 'right',
          grid: {
            color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            color: isDark ? '#64748B' : '#94A3B8',
            font: { size: 10 },
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
}

function stepQuantity(delta) {
  const input = document.getElementById('tradeQuantityInput');
  let val = parseFloat(input.value) || 1;
  val = Math.max(1, val + delta);
  input.value = val;
  calculateOrderMargin();
}

function calculateOrderMargin() {
  const qty = parseFloat(document.getElementById('tradeQuantityInput').value) || 0;
  const price = state.currentModalAsset ? state.currentModalAsset.price : 0;
  const required = roundNumber(qty * price, 2);

  document.getElementById('orderRequiredAmount').innerText = formatINR(required);
  document.getElementById('orderAvailableBalance').innerText = formatINR(state.account.balance);
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

  const payload = {
    symbol: state.currentModalAsset.symbol,
    name: state.currentModalAsset.name,
    asset_type: state.currentModalAsset.asset_type,
    order_type: state.orderAction,
    product_type: state.productType,
    quantity: qty,
    price: state.currentModalAsset.price
  };

  try {
    const res = await fetch('/api/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (!res.ok || !result.success) {
      showToast(result.detail || result.error || 'Order rejected', true);
      return;
    }

    showToast(`Order executed: ${state.orderAction} ${qty} ${payload.symbol} at ${formatINR(payload.price)}`);
    closeTradeModal();

    await fetchAccount();
    if (state.currentTab === 'holdings') fetchPortfolio();
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
      showToast(`Successfully deposited ${formatINR(amount)} into balance`);
      await fetchAccount();
      closeFundsModal();
      document.getElementById('depositAmountInput').value = '';
    }
  } catch (err) {
    showToast('Deposit failed', true);
  }
}

async function submitResetAccount() {
  if (!confirm('Are you sure you want to reset your account? This will set your balance back to ₹10,00,000 and clear all holdings and orders.')) {
    return;
  }

  try {
    const res = await fetch('/api/account/reset', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Account successfully reset to ₹10,00,000');
      await fetchAccount();
      closeFundsModal();
      if (state.currentTab === 'holdings') fetchPortfolio();
      if (state.currentTab === 'orders') fetchOrders();
    }
  } catch (err) {
    showToast('Reset failed', true);
  }
}

// --- Initialization ---
window.addEventListener('DOMContentLoaded', () => {
  initTheme();
  // Fire all requests concurrently for instant zero-lag rendering
  Promise.all([
    fetchAccount(),
    fetchIndices(),
    fetchExploreData(),
    fetchWatchlist()
  ]);

  // Background ticker refresh every 20s
  setInterval(() => {
    fetchIndices();
    if (state.currentTab === 'holdings') fetchPortfolio();
  }, 20000);
});
