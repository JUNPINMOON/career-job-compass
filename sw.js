// Cache lineage retained for release-gate audit: career-compass-v30-grad-legacy-recovery, career-compass-v31-grad-legacy-recovery-wave2
const CACHE = "career-compass-v32-mobile-shell-handoff";
const RETIRED_CACHES = new Set(["career-compass-v25-ux221", "career-compass-v26-grad-evidence", "career-compass-v27-grad-coverage", "career-compass-v28-grad-discovery", "career-compass-v29-supabase-refresh-queue"]);
const APP_SHELL = ["./", "./index.html", "./styles.css", "./app.js", "./supabase-config.js", "./manifest.webmanifest", "./data/app-data.json", "./assets/route-map-editorial-v2.webp", "./assets/study-steps-editorial-v2.webp", "./icons/app-icon.svg", "./icons/app-icon-maskable.svg", "./icons/apple-touch-icon.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    await Promise.all([
      caches.keys().then((keys) => Promise.all(
        keys
          .filter((key) => key !== CACHE || RETIRED_CACHES.has(key))
          .map((key) => caches.delete(key)),
      )),
      self.clients.claim(),
    ]);

    const windows = await clients.matchAll({ type: "window", includeUncontrolled: true });
    await Promise.all(windows.map((client) => {
      try {
        const clientUrl = new URL(client.url);
        const scopeUrl = new URL(self.registration.scope);
        if (clientUrl.origin !== scopeUrl.origin || !clientUrl.pathname.startsWith(scopeUrl.pathname)) {
          return undefined;
        }
        return client.navigate(client.url);
      } catch (_) {
        return undefined;
      }
    }));
  })());
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
