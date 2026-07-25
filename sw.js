const CACHE = "career-compass-v7";
const APP_SHELL = ["./", "./index.html", "./styles.css", "./app.js", "./manifest.webmanifest", "./data/app-data.json", "./data/refresh-bridge.json", "./assets/route-map-editorial-v2.webp", "./assets/study-steps-editorial-v2.webp", "./icons/app-icon.svg", "./icons/app-icon-maskable.svg", "./icons/apple-touch-icon.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(Promise.all([
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))),
    self.clients.claim(),
  ]));
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    try {
      const response = await fetch(event.request);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      event.waitUntil(caches.open(CACHE).then((cache) => cache.put(event.request.url, response.clone())));
      return response;
    } catch (_) {
      const cached = await caches.match(event.request);
      return cached || Response.error();
    }
  })());
});
