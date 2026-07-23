const CACHE_NAME = 'classmapper-pwa-v16';
const CACHE_PREFIX = 'classmapper-pwa-';

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX)).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: 'window', includeUncontrolled: true }))
      .then((clients) => Promise.all(clients.map((client) => {
        if ('navigate' in client) {
          return client.navigate(client.url).catch(() => {});
        }
        return Promise.resolve();
      })))
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
    return;
  }
  if (event.data && event.data.type === 'CLEAR_CLASSMAPPER_CACHE') {
    event.waitUntil(
      caches.keys()
        .then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX)).map((key) => caches.delete(key))))
    );
  }
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== location.origin || event.request.method !== 'GET') {
    return;
  }

  if (url.pathname.endsWith('/data/jielong.csv') || url.pathname.endsWith('/data/map-data.json')) {
    event.respondWith(fetch(new Request(event.request, { cache: 'reload' })));
    return;
  }

  if (event.request.mode === 'navigate') {
    const freshRequest = new Request(event.request, { cache: 'reload' });
    event.respondWith(
      fetch(freshRequest)
        .catch(() => new Response('<!doctype html><meta charset="utf-8"><title>需要联网刷新</title><body style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;padding:24px;text-align:center;"><h3>需要联网刷新</h3><p>请连上网络后重新打开同学蹭饭地图。</p></body>', {
          headers: { 'Content-Type': 'text/html; charset=utf-8' }
        }))
    );
    return;
  }

  event.respondWith(
    fetch(new Request(event.request, { cache: 'reload' }))
  );
});
