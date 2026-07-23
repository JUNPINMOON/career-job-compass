(() => {
  "use strict";

  const state = {
    data: null,
    selectedTrigger: null,
    bookmarks: new Set(readJSON("career-compass-bookmarks", [])),
    ...readJSON("career-compass-filters", { query: "", sector: "", minimumScore: 0, status: "" }),
  };

  const main = document.getElementById("mainContent");
  const filterSheet = document.getElementById("filterSheet");
  const dossier = document.getElementById("dossier");
  const snapshotLabel = document.getElementById("snapshotLabel");
  const offlineBanner = document.getElementById("offlineBanner");

  function readJSON(key, fallback) {
    try { const value = JSON.parse(localStorage.getItem(key)); return value ?? fallback; } catch (_) { return fallback; }
  }
  function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* local convenience only */ } }
  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])); }
  function icon(name) { return `<svg aria-hidden="true"><use href="#i-${name}" /></svg>`; }
  function route() { const value = (location.hash || "#/today").replace(/^#\/?/, "").split("/")[0]; return value === "trust" ? "sources" : value || "today"; }
  function go(path) { location.hash = path; }
  function score(value) { return Number(value || 0).toLocaleString("ko-KR", { maximumFractionDigits: 1 }); }
  function shortDate(value) { return value ? escapeHtml(value) : "원문에서 마감 확인"; }
  function sourceDate(value) { const date = value ? new Date(value) : null; return date && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat("ko-KR", { month: "long", day: "numeric" }).format(date) : "확인 시각 없음"; }
  function displayDate(value) { const date = value ? new Date(value) : null; return date && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "long", timeStyle: "short" }).format(date) : "확인 시각 없음"; }
  function jobs() { return state.data?.jobs || []; }
  function study() { return state.data?.study || []; }
  function jobById(id) { return jobs().find((job) => job.id === id); }
  function saveFilters() { store("career-compass-filters", { query: state.query, sector: state.sector, minimumScore: state.minimumScore, status: state.status }); }
  function saveBookmarks() { store("career-compass-bookmarks", [...state.bookmarks]); }
  function activeFilters() { return Number(Boolean(state.sector)) + Number(Boolean(state.minimumScore)) + Number(Boolean(state.status)); }

  function setActiveTab(current) {
    document.querySelectorAll("[data-tab]").forEach((tab) => tab.toggleAttribute("aria-current", tab.dataset.tab === current));
  }
  function filteredJobs() {
    const query = String(state.query || "").trim().toLocaleLowerCase("ko");
    return jobs().filter((job) => {
      const text = [job.title, job.company, job.location, job.sector, job.source, job.eligibilitySummary].join(" ").toLocaleLowerCase("ko");
      return (!query || text.includes(query)) && (!state.sector || job.sector === state.sector) && Number(job.score || 0) >= Number(state.minimumScore || 0) && (!state.status || job.status === state.status);
    });
  }
  function sectionTitle(kicker, title, action = "") { return `<div class="section-heading"><div><span>${kicker}</span><h2>${title}</h2></div>${action}</div>`; }
  function verifyCopy(job) { return escapeHtml(job.eligibilitySummary || "마감·자격·취업 허가를 원문에서 확인"); }
  function statusText(job) { return job.status === "조건 확인됨" ? "자료 조건 확인됨" : "원문에서 조건 확인 필요"; }
  function chunks(items, size) { return Array.from({ length: Math.ceil(items.length / size) }, (_, index) => items.slice(index * size, index * size + size)); }
  function pageFrame(content, index, total, label) {
    const previous = index > 0 ? `<button class="page-turn-prev" type="button" data-action="page-prev" aria-label="이전 페이지">이전</button>` : `<span aria-hidden="true"></span>`;
    const next = index < total - 1 ? `<button class="page-turn-next" type="button" data-action="page-next" aria-label="다음 페이지">다음 ${icon("arrow")}</button>` : `<span class="page-finish">끝</span>`;
    const progress = Math.round(((index + 1) / total) * 100);
    return `<section class="page-frame" data-page-index="${index}" style="--page-progress:${progress}%" aria-label="${escapeHtml(label)} ${index + 1} / ${total}">${content}<nav class="page-turn" aria-label="${escapeHtml(label)} 페이지 이동">${previous}<span class="page-counter"><i aria-hidden="true"></i>${String(index + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}</span>${next}</nav></section>`;
  }
  function movePage(trigger, direction) {
    const frame = trigger.closest(".page-frame");
    const frames = [...main.querySelectorAll(".page-frame")];
    const currentIndex = frames.indexOf(frame);
    const target = frames[currentIndex + (direction === "next" ? 1 : -1)];
    if (!target) return;
    const top = main.scrollTop + target.getBoundingClientRect().top - main.getBoundingClientRect().top;
    navigator.vibrate?.(8);
    main.scrollTo({ top, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  function priorityRow(job, index, compact = false) {
    const saved = state.bookmarks.has(job.id);
    return `<article class="opportunity ${compact ? "is-compact" : ""}">
      <button class="opportunity-main" type="button" data-open-job="${escapeHtml(job.id)}">
        <span class="opportunity-order">${String(index + 1).padStart(2, "0")}</span>
        <span class="score-mark"><b>${score(job.score)}</b><small>점</small></span>
        <span class="opportunity-copy"><em>${escapeHtml(job.company)}</em><strong>${escapeHtml(job.title)}</strong><small>${escapeHtml(job.location)}</small></span>
        <span class="opportunity-arrow">${icon("arrow")}</span>
      </button>
      <div class="opportunity-foot"><span><i class="source-dot ${job.status === "조건 확인됨" ? "is-solid" : ""}"></i>${statusText(job)}</span><span>${verifyCopy(job)}</span></div>
      <button class="save-dot ${saved ? "is-saved" : ""}" type="button" data-action="bookmark" data-job-id="${escapeHtml(job.id)}" aria-label="${saved ? "보관 취소" : "공고 보관"}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}</button>
    </article>`;
  }

  function renderToday() {
    const ordered = [...jobs()].sort((a, b) => Number(b.score) - Number(a.score));
    const lead = ordered[0];
    const top = ordered.slice(0, 3);
    const routes = study().slice(0, 2);
    const priorityPages = chunks(top, 2).map((group, pageIndex) => `<section class="decision-list ${pageIndex ? "priority-continuation" : ""}" aria-labelledby="priorityHeading${pageIndex}">
      ${pageIndex === 0 ? sectionTitle("01. 오늘의 우선순위", "먼저 원문을 열 세 가지", `<a href="#/jobs">전체 ${jobs().length}개 보기 ${icon("arrow")}</a>`) : `<div class="priority-continuation-head"><p class="eyebrow">01. 오늘의 우선순위 · 이어서</p><h2 id="priorityHeading${pageIndex}">세 번째 후보도<br />원문부터 확인</h2><p>세 항목 모두 점수만으로 지원 가능 여부를 확정하지 않아요.</p></div>`}
      ${pageIndex === 0 ? `<p class="section-intro">비슷한 카드들을 늘어놓지 않았어요. 지금 판단할 순서와, 열기 전에 확인할 조건만 남겼습니다.</p>` : ""}
      <div class="opportunity-list">${group.map((job, index) => priorityRow(job, pageIndex * 2 + index)).join("")}</div>
    </section>`);
    const pages = [`<section class="today-cover" aria-labelledby="todayTitle">
      <div class="cover-meta"><span>CAREER COMPASS</span><span>DAILY BRIEF / 01</span></div>
      <figure class="cover-art"><img src="./assets/daily-brief-cover-v3.png" alt="종이 위로 이어지는 파란 경로와 형광 화살표로 표현한 오늘의 방향" /></figure>
      <div class="cover-copy"><p>오늘의 선택 · ${sourceDate(state.data.stats?.newestSourceCheck)} 기준</p><h1 id="todayTitle"><span>오늘의</span><strong>한 가지</strong></h1></div>
      ${lead ? `<button class="cover-action" type="button" data-open-job="${escapeHtml(lead.id)}"><span>FIRST SOURCE CHECK</span><b>${escapeHtml(lead.company)}<em>${escapeHtml(lead.title)}</em></b>${icon("arrow")}</button>` : ""}
    </section>`, ...priorityPages, `<section class="route-callout" aria-labelledby="routeHeading">
      <div class="route-callout-image"><img src="./assets/study-steps-editorial-v2.webp" alt="책과 종이 계단으로 표현한 학업 경로" /></div>
      <div class="route-callout-copy"><p class="eyebrow">02. 진학과 재정</p><h2 id="routeHeading">이 경로도<br />같이 살펴보기</h2><p>학교 이름만 보지 말고, 시작 시점·장학 조건·교수 연구실을 따로 읽어야 해요.</p><a class="ink-link" href="#/study">진학 루트 열기 ${icon("arrow")}</a></div>
      <div class="route-mini-list">${routes.map((item) => `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer"><small>${escapeHtml(item.degree || "STUDY ROUTE")}</small><b>${escapeHtml(item.university)}</b><span>${escapeHtml(item.program)}</span>${icon("external")}</a>`).join("")}</div>
    </section>`];
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "오늘의 선택")).join("");
  }

  function renderJobResults() {
    const results = filteredJobs();
    const target = document.getElementById("jobResults");
    if (!target) return;
    const pages = chunks(results, 3);
    target.innerHTML = results.length ? pages.map((group, pageIndex) => pageFrame(`<section class="results-section"><div class="results-meta"><span>결과 ${pageIndex * 3 + 1}–${Math.min((pageIndex + 1) * 3, results.length)}</span><b>${results.length}개</b></div><div class="opportunity-list is-results">${group.map((job, index) => priorityRow(job, pageIndex * 3 + index, true)).join("")}</div></section>`, pageIndex + 1, pages.length + 1, "공고 탐색")).join("") : pageFrame(`<section class="results-section"><div class="empty"><p>지금 조건과 맞는 공고가 없어요.</p><button class="plain-button" type="button" data-action="clear-filters">필터 초기화</button></div></section>`, 1, 2, "공고 탐색");
  }

  function renderJobs() {
    const sectorChips = (state.data.sectors || []).slice(0, 6).map((sector) => `<button class="sector-chip ${state.sector === sector.name ? "is-active" : ""}" type="button" data-sector="${escapeHtml(sector.name)}">${escapeHtml(sector.name)} <b>${sector.publishedJobs}</b></button>`).join("");
    const total = Math.max(1, chunks(filteredJobs(), 3).length) + 1;
    main.innerHTML = pageFrame(`<section class="browse-head"><p class="eyebrow">공고 탐색</p><div class="browse-title-row"><h1>하나씩, 확실하게.</h1><button class="filter-trigger" type="button" data-action="open-filters">필터 ${activeFilters() ? `<b>${activeFilters()}</b>` : ""}${icon("filter")}</button></div><p>역할·기관·지역을 검색한 뒤, 관심 가는 공고만 원문으로 넘어가세요.</p>
      <label class="search-box">${icon("search")}<span class="sr-only">공고 검색</span><input id="jobSearch" type="search" value="${escapeHtml(state.query)}" placeholder="직무, 기관, 지역으로 찾기" autocomplete="off" /></label>
      <div class="sector-scroll"><button class="sector-chip ${!state.sector ? "is-active" : ""}" type="button" data-sector="">전체</button>${sectorChips}</div></section>`, 0, total, "공고 탐색") + `<div id="jobResults"></div>`;
    document.getElementById("jobSearch").addEventListener("input", (event) => { state.query = event.target.value; saveFilters(); renderJobResults(); });
    renderJobResults();
  }

  function renderStudy() {
    const routePages = chunks(study(), 2);
    const total = routePages.length + 1;
    const intro = `<section class="study-hero"><div><p class="eyebrow">진학 · 장학 · 연구</p><h1>다음 단계도<br />현실적으로.</h1><p>과정의 이름과 지원금은 다릅니다. 한 항목씩 공식 출처를 열고, 마감과 지원 자격을 다시 확인하세요.</p></div><img src="./assets/study-steps-editorial-v2.webp" alt="책과 종이 계단으로 표현한 학업 경로" /></section>`;
    const routes = routePages.map((group, pageIndex) => `<section class="study-list" aria-label="진학과 장학 루트">${group.map((item, index) => `<a class="study-row" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer"><span>${String(pageIndex * 2 + index + 1).padStart(2, "0")}</span><div><small>${escapeHtml(item.degree || "STUDY ROUTE")} · ${escapeHtml(item.country)}</small><h2>${escapeHtml(item.program)}</h2><p>${escapeHtml(item.university)}</p><em>${escapeHtml(item.funding || "재정 조건 원문 확인")}</em></div>${icon("external")}</a>`).join("")}</section>`);
    main.innerHTML = [intro, ...routes].map((page, index) => pageFrame(page, index, total, "진학과 재정")).join("");
  }

  function renderSources() {
    const stats = state.data.stats || {};
    const statusRows = Object.entries(stats.sourceStatusCounts || {}).sort(([a], [b]) => a.localeCompare(b)).map(([name, count]) => `<div><span>${escapeHtml(name.replaceAll("_", " "))}</span><b>${escapeHtml(count)}</b></div>`).join("");
    const pages = [`<section class="sources-head"><p class="eyebrow">자료의 범위</p><h1>앱이 아는 것,<br />아직 모르는 것.</h1><p>${escapeHtml(state.data.snapshotBoundary || "원문 확인 전에는 판단을 확정하지 않습니다.")}</p></section>`, `<section class="source-stamp"><span>LAST SNAPSHOT</span><b>${displayDate(state.data.generatedAt)}</b><i>SOURCE<br />FIRST</i></section><section class="stat-strip"><div><small>원시 공고</small><b>${escapeHtml(stats.rawJobs)}</b></div><div><small>점수화 풀</small><b>${escapeHtml(stats.scoredJobs)}</b></div><div><small>공개 공고</small><b>${escapeHtml(stats.publishedJobs)}</b></div></section>`, `<section class="source-explainer"><p class="eyebrow">출처 상태</p><h2>원문이 최종 기준입니다.</h2><p>이 화면은 공개 스냅샷을 읽기 쉽게 정리한 것입니다. 외부 지원·로그인·CRM 변경은 수행하지 않습니다.</p><div class="status-rows">${statusRows}</div></section>`];
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "자료의 범위")).join("");
  }

  function renderDetail(job) {
    const saved = state.bookmarks.has(job.id);
    const official = job.url ? `<a class="official-button" href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">공식 원문 열기 ${icon("external")}</a>` : `<span class="official-button is-disabled">공식 원문 주소 없음</span>`;
    dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${escapeHtml(job.source || "SOURCE")} · 공고 상세</small><button type="button" data-action="close-dossier" aria-label="상세 닫기">${icon("close")}</button></div></header><div class="detail-body"><p class="detail-score"><b>${score(job.score)}</b><span>우선순위 점수<br />100점 기준</span></p><h2 id="dossierTitle">${escapeHtml(job.title)}</h2><p class="detail-company">${escapeHtml(job.company)} · ${escapeHtml(job.location)}</p><div class="detail-primary">${official}</div><div class="detail-facts"><div><small>분야</small><b>${escapeHtml(job.sector)}</b></div><div><small>마감</small><b>${shortDate(job.deadline)}</b></div><div><small>출처 상태</small><b>${statusText(job)}</b></div><div><small>근거 완성도</small><b>${escapeHtml(job.evidenceCompleteness)}%</b></div></div><section class="check-note"><small>열기 전 체크</small><p>${verifyCopy(job)}</p></section><div class="detail-actions"><button class="detail-save ${saved ? "is-saved" : ""}" type="button" data-action="bookmark" data-job-id="${escapeHtml(job.id)}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}${saved ? "보관함에 있음" : "나중에 보기"}</button></div><p class="detail-boundary">원문에서 마감·자격·지원 가능 여부를 최종 확인하세요.</p></div></article>`;
  }
  function openDetail(id, trigger) { const job = jobById(id); if (!job) return; state.selectedTrigger = trigger || null; renderDetail(job); if (!dossier.open) dossier.showModal(); requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus()); }
  function closeDetail(restore = true) { if (dossier.open) dossier.close(); if (restore && state.selectedTrigger?.isConnected) state.selectedTrigger.focus(); state.selectedTrigger = null; }
  function openFilters() {
    const sectors = [...new Set(jobs().map((job) => job.sector))].sort((a, b) => a.localeCompare(b, "ko"));
    const select = document.getElementById("sectorFilter");
    select.innerHTML = `<option value="">전체 분야</option>${sectors.map((sector) => `<option value="${escapeHtml(sector)}">${escapeHtml(sector)}</option>`).join("")}`;
    select.value = state.sector; document.getElementById("scoreFilter").value = String(state.minimumScore); document.getElementById("statusFilter").value = state.status;
    if (!filterSheet.open) filterSheet.showModal(); select.focus();
  }
  function resetFilters() { state.query = ""; state.sector = ""; state.minimumScore = 0; state.status = ""; saveFilters(); const input = document.getElementById("jobSearch"); if (input) input.value = ""; renderJobResults(); }
  function updateNetwork() { offlineBanner.hidden = navigator.onLine; const recent = state.data?.stats?.newestSourceCheck; snapshotLabel.textContent = navigator.onLine ? `자료 ${sourceDate(recent)}` : "오프라인 스냅샷"; }
  function renderError() { main.innerHTML = `<section class="loading"><span>LOAD ERROR</span><b>자료를 열 수 없어요.</b><button class="plain-button" type="button" data-action="retry">다시 시도</button></section>`; }
  function render(focus = true) { if (!state.data) return; closeDetail(false); window.scrollTo(0, 0); main.scrollTop = 0; const current = route(); setActiveTab(current); if (current === "today") renderToday(); else if (current === "jobs") renderJobs(); else if (current === "study") renderStudy(); else if (current === "sources") renderSources(); else { go("#/today"); return; } requestAnimationFrame(() => { window.scrollTo(0, 0); main.scrollTop = 0; if (focus) main.querySelector("h1")?.focus({ preventScroll: true }); }); }
  async function load() { try { const response = await fetch("./data/app-data.json", { cache: "reload" }); if (!response.ok) throw new Error(response.status); const data = await response.json(); if (!Array.isArray(data.jobs) || !Array.isArray(data.study)) throw new Error("schema"); state.data = data; updateNetwork(); render(false); } catch (error) { console.error(error); snapshotLabel.textContent = "자료를 열 수 없음"; renderError(); } }

  document.addEventListener("click", (event) => {
    const routeButton = event.target.closest("[data-route]"); if (routeButton) { go(`#/${routeButton.dataset.route}`); return; }
    const jobButton = event.target.closest("[data-open-job]"); if (jobButton) { openDetail(jobButton.dataset.openJob, jobButton); return; }
    const sector = event.target.closest("[data-sector]"); if (sector) { state.sector = sector.dataset.sector; saveFilters(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); return; }
    const action = event.target.closest("[data-action]")?.dataset.action; if (!action) return;
    if (action === "page-next") { movePage(event.target.closest("[data-action]"), "next"); return; }
    if (action === "page-prev") { movePage(event.target.closest("[data-action]"), "prev"); return; }
    if (action === "open-filters") openFilters();
    if (action === "clear-filters") resetFilters();
    if (action === "close-dossier") closeDetail();
    if (action === "bookmark") { const id = event.target.closest("[data-job-id]").dataset.jobId; if (state.bookmarks.has(id)) state.bookmarks.delete(id); else state.bookmarks.add(id); saveBookmarks(); const job = jobById(id); if (job && dossier.open) renderDetail(job); else if (route() === "jobs") renderJobResults(); }
    if (action === "retry") load();
  });
  document.getElementById("filterForm").addEventListener("submit", (event) => { event.preventDefault(); state.sector = document.getElementById("sectorFilter").value; state.minimumScore = Number(document.getElementById("scoreFilter").value); state.status = document.getElementById("statusFilter").value; saveFilters(); filterSheet.close(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); });
  document.getElementById("resetFilters").addEventListener("click", () => { resetFilters(); filterSheet.close(); });
  filterSheet.addEventListener("cancel", (event) => { event.preventDefault(); filterSheet.close(); });
  dossier.addEventListener("cancel", (event) => { event.preventDefault(); closeDetail(); });
  dossier.addEventListener("click", (event) => { if (event.target === dossier) closeDetail(); });
  document.getElementById("snapshotButton").addEventListener("click", () => go("#/sources"));
  window.addEventListener("hashchange", () => render()); window.addEventListener("online", updateNetwork); window.addEventListener("offline", updateNetwork);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => undefined);
  load();
})();
