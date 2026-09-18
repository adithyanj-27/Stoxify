// Stoxifyn PWA Service Worker
const CACHE_NAME = 'stoxifyn-v1';

// The app shell is precached so a cold offline navigation has something to
// serve. It previously cached only icons and manifest, so offline never worked
// for the app itself.
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
      // A single missing asset must not abort the whole install.
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
      "<title>Stoxifyn — offline</title>" +
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

  // Network-first, so a connected user always gets the current build. The
  // cache is only a fallback — but it is a *real* fallback now: the previous
  // implementation ended in `caches.match(request)`, which resolves to
  // undefined on a miss and made respondWith() throw.
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
