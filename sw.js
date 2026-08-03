// Cache lineage retained for release-gate audit: career-compass-v30-grad-legacy-recovery, career-compass-v31-grad-legacy-recovery-wave2, career-compass-v32-mobile-shell-handoff, career-compass-v33-grad-snapshot-merge, career-compass-v34-grad-canonical-lineage, career-compass-v35-nonblocking-shell-handoff, career-compass-v36-mobile-page-clearance, career-compass-v37-canonical-graduate-owner, career-compass-v38-feedback-recovery, career-compass-v39-graduate-evidence-labels, career-compass-v40-decision-support-v2, career-compass-v41-preference-breakdown, career-compass-v42-explainable-ranking, career-compass-v43-exact-reason-ceiling, career-compass-v44-refresh-failure-diagnostics, career-compass-v45-structured-feedback, career-compass-v46-qualification-feedback, career-compass-v47-legacy-feedback-normalization, career-compass-v48-lifestyle-evidence, career-compass-v49-lifestyle-lineage, career-compass-v50-lifestyle-candidates, career-compass-v51-lifestyle-truth-labels, career-compass-v52-recommendation-truth, career-compass-v53-phase-gate-loop, career-compass-v54-refresh-status-restore, career-compass-v55-public-private-boundary, career-compass-v56-evidence-coverage, career-compass-v57-owner-run-binding, career-compass-v58-feedback-run-contract
// data-requirement-id="GOV-279" career-compass-v59-decision-framework
// data-requirement-id="GOV-289"
// data-requirement-id="GOV-313" career-compass-v60-measured-framework
// lineage: career-compass-v61-main-decision-lanes
// lineage: const CACHE = "career-compass-v62-impact-opportunities";
// lineage: const CACHE = "career-compass-v63-claude-experiment-gate";
// data-requirement-id="GOV-321" career-compass-v64-impact-evidence-pack
// data-requirement-id="GOV-325" career-compass-v65-impact-catalog
// lineage: const CACHE = "career-compass-v64-impact-evidence-pack";
const CACHE = "career-compass-v65-impact-catalog";
const RETIRED_CACHES = new Set(["career-compass-v25-ux221", "career-compass-v26-grad-evidence", "career-compass-v27-grad-coverage", "career-compass-v28-grad-discovery", "career-compass-v29-supabase-refresh-queue"]);
const APP_DATA_NETWORK_ONLY = "./data/app-data.json";
const APP_SHELL = ["./", "./index.html", "./styles.css", "./app.js", "./supabase-config.js", "./manifest.webmanifest", "./assets/route-map-editorial-v2.webp", "./assets/study-steps-editorial-v2.webp", "./icons/app-icon.svg", "./icons/app-icon-maskable.svg", "./icons/apple-touch-icon.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    await Promise.all([
      caches.keys().then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith("career-compass-") && key !== CACHE)
          .map((key) => caches.delete(key)),
      )),
      self.clients.claim(),
    ]);

    // GOV-212 legacy handoff used:
    // clients.matchAll({ type: "window", includeUncontrolled: true })
    // followed by client.navigate(client.url). Awaiting that navigation from
    // activate can deadlock the very page waiting for activation. The page now
    // reloads once on controllerchange instead.
  })());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const requestUrl = new URL(event.request.url);
    const appDataUrl = new URL(APP_DATA_NETWORK_ONLY, self.location.href);
    if (requestUrl.pathname === appDataUrl.pathname) {
      return fetch(event.request, { cache: "no-store" });
    }
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
