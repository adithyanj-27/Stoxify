// Stoxify PWA Service Worker
const CACHE_NAME = 'stoxify-v6';
const STATIC_ASSETS = [
  '/manifest.json',
  '/static/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/static/icon-192.png',
  '/static/icon-512.png'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
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

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) return;

  const url = event.request.url;

  // Always fetch live fresh versions for app shell, scripts, styles, and HTML
  if (
    url.includes('app.js') || 
    url.includes('style.css') || 
    url.includes('sw.js') ||
    url.endsWith('/') || 
    url.includes('index.html') ||
    url.includes('?v=')
  ) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .then((response) => {
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Cache-first fallback for static icons/images
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    })
  );
});
