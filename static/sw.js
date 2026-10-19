// Stoxify PWA Service Worker with Web Push & Offline Support
const CACHE_NAME = 'stoxify-v5';

// The app shell is precached so a cold offline navigation has something to serve.
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/static/app.js',
  '/static/style.css',
  '/static/manifest.json',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(SHELL_ASSETS).catch(() => {});
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

/** A real Response, so respondWith() never receives undefined. */
function offlineResponse(request) {
  const acceptsHtml = (request.headers.get('accept') || '').includes('text/html');
  if (request.mode === 'navigate' || acceptsHtml) {
    return new Response(
      '<!doctype html><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      "<title>Stoxify — offline</title>" +
      '<body style="font-family:system-ui,sans-serif;background:#0B0F19;color:#e2e8f0;padding:2rem">' +
      '<h2>You are offline</h2>' +
      '<p>Reconnect to load live market data. Cached screens may still be available.</p>' +
      '</body>',
      { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
  return new Response('', { status: 504, statusText: 'Offline' });
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return;

  // Network-first, so a connected user always gets the current build.
  event.respondWith(
    fetch(request, { cache: 'no-store' })
      .then((response) => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME)
            .then((cache) => cache.put(request, copy))
            .catch(() => {});
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then((cached) => cached || offlineResponse(request))
      )
  );
});

// ==============================================================================
// --- Web Push & Notification Handlers ---
// ==============================================================================

self.addEventListener('push', (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'Stoxify Market Alert', body: event.data.text() };
    }
  }

  const title = data.title || 'Stoxify Price Alert';
  const notifData = data.data || {};
  const symbol = notifData.symbol || '';

  const options = {
    body: data.body || 'Drastic price movement detected in your portfolio / watchlist.',
    icon: data.icon || '/static/icon-192.png',
    badge: data.badge || '/static/icon-192.png',
    vibrate: [150, 80, 150, 80, 200],
    tag: symbol ? `price-alert-${symbol}` : 'stoxify-price-alert',
    renotify: true,
    requireInteraction: true,
    data: {
      url: notifData.url || (symbol ? `/stock/${symbol}` : '/'),
      symbol: symbol,
      assetType: notifData.asset_type || 'STOCK',
      id: notifData.id || null
    },
    actions: [
      { action: 'open_chart', title: 'Open Chart 📊' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const notifData = event.notification.data || {};
  const targetUrl = notifData.url || (notifData.symbol ? `/stock/${notifData.symbol}` : '/');
  const symbol = notifData.symbol;
  const assetType = notifData.assetType || 'STOCK';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // If a window is already open, focus it and tell app to open the asset modal
      for (const client of clientList) {
        if ('focus' in client) {
          return client.focus().then(() => {
            client.postMessage({
              type: 'OPEN_NOTIFICATION_ASSET',
              symbol: symbol,
              assetType: assetType,
              url: targetUrl
            });
            // If the client supports navigate and isn't on the target, optionally navigate
            if ('navigate' in client && client.url && !client.url.includes(targetUrl)) {
              return client.navigate(targetUrl);
            }
          });
        }
      }
      // If no window is open, open a new window
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
