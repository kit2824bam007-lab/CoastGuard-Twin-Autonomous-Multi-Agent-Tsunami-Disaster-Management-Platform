// CoastGuard Twin Civilian Evacuation Offline Service Worker
const CACHE_NAME = 'coastguard-civilian-v1';
const OFFLINE_URLS = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(OFFLINE_URLS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Stale-while-revalidate strategy for offline evacuation resilience
  if (event.request.mode === 'navigate' || event.request.url.includes('/api/alerts/severity')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request).then((response) => {
          if (response) return response;
          // Fallback offline mock response for civilian evacuation
          return new Response(
            JSON.stringify({
              offline: true,
              classification: { predicted_class: 'SEVERE', confidence: 0.99 },
              civilian_instructions: "OFFLINE MODE: Network connection lost. Move to inland elevation above 50m immediately!",
              nearest_shelter: {
                shelter_name: "Highland Sanctuary Complex",
                distance_km: 2.4,
                heading_degrees: 45,
                direction_label: "NE Inland",
                safe_elevation_m: 85
              }
            }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        });
      })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
