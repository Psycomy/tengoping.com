const CACHE_VERSION = 'tengoping-v3';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGES_CACHE = `${CACHE_VERSION}-pages`;

const PRECACHE_URLS = [
  '/',
  '/favicon.svg',
  '/offline.html',
  '/fonts/JetBrainsMono-Regular.woff2',
  '/fonts/JetBrainsMono-Bold.woff2',
];

// Assets built by Astro have content hashes in filename — safe to cache-first
function isHashedAsset(url) {
  return url.pathname.startsWith('/_astro/');
}

const MAX_PAGES = 50;

async function limitPagesCache() {
  const cache = await caches.open(PAGES_CACHE);
  const keys = await cache.keys();
  if (keys.length > MAX_PAGES) {
    const toDelete = keys.slice(0, keys.length - MAX_PAGES);
    await Promise.all(toDelete.map((k) => cache.delete(k)));
  }
}

// Install: precache shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== PAGES_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (url.origin !== location.origin) return;

  if (request.destination === 'document') {
    // Network-first for HTML pages, offline fallback
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(PAGES_CACHE).then(async (cache) => {
            await cache.put(request, clone);
            await limitPagesCache();
          });
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match('/offline.html'))
        )
    );
  } else if (isHashedAsset(url)) {
    // Cache-first ONLY for hashed assets (_astro/*) — filename changes on content change
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
            return response;
          })
      )
    );
  } else if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'font' ||
    request.destination === 'image'
  ) {
    // Network-first for non-hashed assets (images, icons, etc.)
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request))
    );
  }
});
