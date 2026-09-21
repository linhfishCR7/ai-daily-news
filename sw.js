/*
 * AI Daily News - Service Worker
 *
 * Strategy (always show today's latest report when online):
 *   - documents / archive pages / manifest JSON → network-first (latest online, cache offline)
 *   - same-origin static assets (CSS/icons/SVG)  → stale-while-revalidate
 *   - cross-origin requests (Google Fonts, etc.) → passed through, not cached
 */

const CACHE = 'aidaily-v5';

/* Install: precache the core shell */
const CORE = [
  './',
  './assets/style.css?v=3', // keep in sync with STYLE_VERSION in scripts/generate.py
  './assets/vendor/page-flip.browser.js',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(CORE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Let the browser handle cross-origin requests
  if (url.origin !== self.location.origin) return;

  const isDoc =
    req.mode === 'navigate' ||
    url.pathname.endsWith('/') ||
    url.pathname.endsWith('.html') ||
    url.pathname.endsWith('archive_manifest.json');

  if (isDoc) {
    // network-first: fetch the latest report, fall back to cache when offline
    event.respondWith(
      fetch(req, { cache: 'no-cache' })
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match('./')))
    );
    return;
  }

  // Static assets: stale-while-revalidate (serve cache, refresh in background)
  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(req);
      const network = fetch(req)
        .then((res) => { cache.put(req, res.clone()); return res; })
        .catch(() => null);
      return hit || await network;
    })()
  );
});
