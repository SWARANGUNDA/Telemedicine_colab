// TeleMed AI Platform — Production Service Worker (Static Asset Cache Only)
const CACHE_NAME = 'telemed-static-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Only handle GET requests for internal static assets; bypass all API, WS, mutations, and non-http schemes
  if (event.request.method !== 'GET') {
    return;
  }

  const url = event.request.url;
  if (
    url.includes('/api/') ||
    url.includes('/ws/') ||
    !url.startsWith('http')
  ) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch((err) => {
        // Return cached index.html for navigation requests if network fails
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
        return new Response('', { status: 408, statusText: 'Network request offline' });
      });
    })
  );
});
