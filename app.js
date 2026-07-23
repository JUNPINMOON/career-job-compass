(() => {
  "use strict";

  const state = {
    data: null,
    ...readSession("career-compass-filters", { query: "", sector: "", minimumScore: 0, status: "" }),
    returnScroll: 0,
    bookmarks: new Set(readStorage("career-compass-bookmarks", [])),
  };

  const main = document.getElementById("mainContent");
  const filterSheet = document.getElementById("filterSheet");
  const snapshotLabel = document.getElementById("snapshotLabel");
  const snapshotDot = document.querySelector(".snapshot-button .status-dot");
  const offlineBanner = document.getElementById("offlineBanner");

  function readStorage(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key));
      return Array.isArray(value) ? value : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function readSession(key, fallback) {
    try {
      const value = JSON.parse(sessionStorage.getItem(key));
      return value && typeof value === "object" ? value : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function persistFilters() {
    try {
      sessionStorage.setItem("career-compass-filters", JSON.stringify({
        query: state.query,
        sector: state.sector,
        minimumScore: state.minimumScore,
        status: state.status,
      }));
    } catch (_) { /* optional resilience for PWA return trips */ }
  }

  function saveBookmarks() {
    try { localStorage.setItem("career-compass-bookmarks", JSON.stringify([...state.bookmarks])); } catch (_) { /* local-only optional feature */ }
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
  }

  function icon(name) {
    return `<svg aria-hidden="true"><use href="#i-${name}" /></svg>`;
  }

  function displayDate(value) {
    if (!value) return "날짜 원문 확인";
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? escapeHtml(value) : new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(parsed);
  }

  function sourceDate(value) {
    if (!value) return "확인 시각 없음";
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(parsed);
  }

  function route() {
    const hash = location.hash || "#/today";
    const parts = hash.replace(/^#\/?/, "").split("/").filter(Boolean).map((part) => decodeURIComponent(part));
    return { root: parts[0] || "today", id: parts[1] || "" };
  }

  function go(path) {
    location.hash = path;
  }

  function setActiveTab(root) {
    const tabRoot = root === "job" ? "jobs" : root;
    document.querySelectorAll("[data-tab]").forEach((node) => {
      const active = node.dataset.tab === tabRoot;
      if (active) node.setAttribute("aria-current", "page"); else node.removeAttribute("aria-current");
    });
  }

  function tagClass(status) {
    return status === "조건 확인됨" ? "verified" : "verify";
  }

  function getJobs() {
    return state.data ? state.data.jobs || [] : [];
  }

  function filteredJobs() {
    const query = state.query.trim().toLocaleLowerCase("ko");
    return getJobs().filter((job) => {
      const haystack = [job.title, job.company, job.location, job.sector, job.source].join(" ").toLocaleLowerCase("ko");
      return (!query || haystack.includes(query)) &&
        (!state.sector || job.sector === state.sector) &&
        Number(job.score || 0) >= state.minimumScore &&
        (!state.status || job.status === state.status);
    });
  }

  function currentFilterCount() {
    return Number(Boolean(state.query)) + Number(Boolean(state.sector)) + Number(Boolean(state.minimumScore)) + Number(Boolean(state.status));
  }

  function jobRow(job) {
    return `<button class="job-row" type="button" data-open-job="${escapeHtml(job.id)}">
      <span class="row-kicker"><span>${escapeHtml(job.company)}</span><span class="metric">${escapeHtml(job.score)}점</span></span>
      <span class="row-title">${escapeHtml(job.title)}</span>
      <span class="row-meta"><span>${escapeHtml(job.location)}</span><span class="tag ${tagClass(job.status)}">${escapeHtml(job.status)}</span></span>
      <span class="arrow">${icon("arrow")}</span>
    </button>`;
  }

  function renderJobResults() {
    const results = filteredJobs();
    const count = document.getElementById("jobResultCount");
    const list = document.getElementById("jobResults");
    const filterCount = document.getElementById("filterCount");
    if (!count || !list) return;
    count.textContent = `${results.length}개`;
    if (filterCount) {
      filterCount.textContent = String(currentFilterCount());
      filterCount.hidden = currentFilterCount() === 0;
    }
    list.innerHTML = results.length ? results.map(jobRow).join("") : `<div class="empty-state"><h2>조건에 맞는 공고가 없습니다</h2><p>현재 적용한 검색어와 조건을 확인하거나, 필터를 초기화해 보세요.</p><button class="secondary-button" type="button" data-action="clear-filters">조건 초기화</button></div>`;
  }

  function pageHead(eyebrow, title, lede) {
    return `<header class="page-head"><span class="eyebrow">${eyebrow}</span><h1 tabindex="-1">${title}</h1><p class="lede">${lede}</p></header>`;
  }

  function renderToday() {
    const jobs = getJobs().slice(0, 3);
    const study = (state.data.study || []).slice(0, 2);
    main.innerHTML = `${pageHead("오늘의 판단", "무엇을 먼저 확인할까요?", "공개 스냅샷의 우선 항목입니다. 마감과 지원 자격은 원문에서 다시 확인해야 합니다.")}
      <div class="notice">${icon("info")}<span>${escapeHtml(state.data.snapshotBoundary)}</span></div>
      <div class="today-grid">
        <section><div class="section-heading"><div><span class="eyebrow">공고</span><h2>먼저 원문을 볼 항목</h2></div><a href="#/jobs">모든 공고 보기</a></div><div class="action-list">${jobs.map(jobRow).join("")}</div></section>
        <section><div class="section-heading"><div><span class="eyebrow">학업·재정</span><h2>함께 검토할 경로</h2></div><a href="#/study">전체 보기</a></div><div class="action-list">${study.map(studyRow).join("")}</div></section>
      </div>`;
  }

  function renderJobs() {
    main.innerHTML = `${pageHead("공고 찾기", "목록에서 판단하고, 원문에서 확인합니다.", "이 화면은 ${escapeHtml(state.data.stats.publishedJobs)}개 경량 스냅샷입니다. 점수는 우선순위일 뿐, 마감·자격·지원 가능 여부를 확정하지 않습니다.")}
      <div class="jobs-toolbar"><label class="search-field"><span class="sr-only">공고 검색</span>${icon("search")}<input id="jobSearch" type="search" autocomplete="off" placeholder="직무, 기관, 지역, 분야 검색" value="${escapeHtml(state.query)}" /></label><button class="filter-trigger" type="button" data-action="open-filters">${icon("filter")} 조건 좁히기 <span class="filter-count" id="filterCount" hidden>0</span></button></div>
      <div class="list-summary"><span>스냅샷 <strong id="jobResultCount"></strong></span><button class="back-link" type="button" data-action="clear-filters">조건 초기화</button></div>
      <div class="opportunity-list" id="jobResults"></div>`;
    document.getElementById("jobSearch").addEventListener("input", (event) => { state.query = event.target.value; persistFilters(); renderJobResults(); });
    renderJobResults();
    const persistedScroll = Number(sessionStorage.getItem("career-compass-return-scroll") || 0);
    if (state.returnScroll || persistedScroll) {
      const scroll = state.returnScroll || persistedScroll;
      state.returnScroll = 0;
      sessionStorage.removeItem("career-compass-return-scroll");
      requestAnimationFrame(() => window.scrollTo({ top: scroll, behavior: "instant" }));
    }
  }

  function renderDetail(id) {
    const job = getJobs().find((item) => item.id === id);
    if (!job) { renderError("공고를 찾을 수 없습니다", "공개 스냅샷이 바뀌었거나, 이 항목은 더 이상 포함되지 않았습니다."); return; }
    const saved = state.bookmarks.has(job.id);
    const sourceDisabled = !job.url;
    main.innerHTML = `<article class="detail"><div class="detail-top"><button class="back-link" type="button" data-action="back-jobs">${icon("back")} 목록</button><button class="bookmark-button ${saved ? "is-saved" : ""}" type="button" data-action="bookmark" data-job-id="${escapeHtml(job.id)}" aria-pressed="${saved}" aria-label="${saved ? "저장 해제" : "나중에 볼 공고로 저장"}">${icon(saved ? "bookmark-filled" : "bookmark")}</button></div>
      <span class="tag ${tagClass(job.status)}">${escapeHtml(job.status)}</span><h1 class="detail-title" tabindex="-1">${escapeHtml(job.title)}</h1><p class="detail-company">${escapeHtml(job.company)} · ${escapeHtml(job.source)}</p><p class="detail-score">${escapeHtml(job.score)}<small>우선순위 점수</small></p>
      <dl class="fact-grid"><div><dt>근무지</dt><dd>${escapeHtml(job.location)}</dd></div><div><dt>분야</dt><dd>${escapeHtml(job.sector)}</dd></div><div><dt>마감</dt><dd>${escapeHtml(job.deadline || "원문 확인 필요")}</dd></div><div><dt>근거 완성도</dt><dd>${escapeHtml(job.evidenceCompleteness)}%</dd></div></dl>
      <section class="detail-section"><span class="eyebrow">지원 판단</span><h2>먼저 확인할 것</h2><div class="evidence-box">${escapeHtml(job.eligibilitySummary)}</div></section>
      <section class="detail-section"><span class="eyebrow">출처</span><h2>공개 스냅샷의 경계</h2><p class="muted">이 앱은 원문 공고를 저장한 읽기용 스냅샷입니다. 외부 지원, 로그인, CRM 변경을 하지 않습니다.</p><a class="source-link" ${sourceDisabled ? "aria-disabled=\"true\"" : `href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer"`}>${icon("external")} 공식 원문 확인</a><p class="detail-boundary">원문을 열기 전에 이 목록의 필터와 스크롤 위치는 이 기기에 유지됩니다.</p></section></article>`;
  }

  function studyRow(item) {
    return `<a class="study-row" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer"><span class="row-kicker"><span>${escapeHtml(item.university)}</span><span class="tag neutral">${escapeHtml(item.degree || "과정")}</span></span><span class="row-title">${escapeHtml(item.program)}</span><span class="row-meta"><span>${escapeHtml(item.country)}</span><span>${escapeHtml(item.deadline)}</span></span><span class="funding">${escapeHtml(item.funding)}</span><span class="arrow">${icon("external")}</span></a>`;
  }

  function renderSectors() {
    const sectors = state.data.sectors || [];
    main.innerHTML = `${pageHead("분야 탐색", "어느 분야에서 공고를 읽을까요?", "표시 건수는 이 공개 스냅샷 안의 수입니다. 전체 파이프라인의 결과 수와 동일하지 않을 수 있습니다.")}
      <div class="sector-list">${sectors.map((item) => `<button class="sector-row" type="button" data-sector="${escapeHtml(item.name)}"><div><h3>${escapeHtml(item.name)}</h3><p class="muted small">공개 스냅샷에서 관련 공고 보기</p></div><span class="sector-count">${escapeHtml(item.publishedJobs)}</span></button>`).join("")}</div>`;
  }

  function renderStudy() {
    const routes = state.data.study || [];
    main.innerHTML = `${pageHead("대학원·장학금", "학업과 재정 경로를 따로 판단합니다.", "각 항목은 공식 원문을 가리킵니다. 마감, RA/장학 조건, 지원 자격은 열기 전에 다시 확인하세요.")}
      <div class="notice">${icon("info")}<span>공고 추천과 학업 경로는 서로 다른 시간축의 의사결정입니다. 이 탭은 공고 상세에 강제로 섞지 않습니다.</span></div><div class="study-list">${routes.map(studyRow).join("")}</div>`;
  }

  function renderTrust() {
    const stats = state.data.stats || {};
    const statusCounts = stats.sourceStatusCounts || {};
    const entries = Object.entries(statusCounts).sort(([a], [b]) => a.localeCompare(b));
    main.innerHTML = `${pageHead("자료 신뢰", "이 화면이 무엇을 알고, 무엇을 모르는지", "GitHub Pages에 올린 정적 스냅샷의 출처·갱신 경계입니다. 최신 수집이나 지원 가능 여부를 보장하지 않습니다.")}
      <div class="trust-grid"><div class="trust-metric"><span>원시 공고</span><strong>${escapeHtml(stats.rawJobs)}</strong><small>로컬 파이프라인의 입력 규모</small></div><div class="trust-metric"><span>점수 공고</span><strong>${escapeHtml(stats.scoredJobs)}</strong><small>점수화된 전체 풀</small></div><div class="trust-metric"><span>공개 스냅샷</span><strong>${escapeHtml(stats.publishedJobs)}</strong><small>이 기기에서 빠르게 읽는 경량 목록</small></div><div class="trust-metric"><span>출처 기록</span><strong>${escapeHtml(stats.sourceRecords)}</strong><small>상태가 기록된 수집원</small></div></div>
      <section class="detail-section"><span class="eyebrow">스냅샷</span><h2>${displayDate(state.data.generatedAt)}</h2><p class="muted">가장 최근 출처 확인: ${escapeHtml(sourceDate(stats.newestSourceCheck))}</p></section>
      <section class="detail-section"><span class="eyebrow">출처 상태</span><h2>수집원이 모두 같은 상태는 아닙니다</h2><div class="status-breakdown">${entries.map(([status, count]) => `<div><span>${escapeHtml(status)}</span><strong>${escapeHtml(count)}개</strong></div>`).join("")}</div></section>
      <section class="detail-section"><span class="eyebrow">안전 경계</span><h2>이 앱이 하지 않는 일</h2><div class="evidence-box">외부 지원·메일·로그인·CRM 변경·실시간 수집을 수행하지 않습니다. 원문을 연 뒤의 행동은 사용자가 직접 확인하고 결정합니다.</div></section>`;
  }

  function renderError(title, detail) {
    main.innerHTML = `<section class="error-state"><span class="eyebrow">불러오기 실패</span><h1>${escapeHtml(title)}</h1><p>${escapeHtml(detail)}</p><button class="primary-button" type="button" data-action="retry">다시 시도</button></section>`;
  }

  function render(focus = true) {
    if (!state.data) return;
    const current = route();
    setActiveTab(current.root);
    if (current.root === "today") renderToday();
    else if (current.root === "jobs") renderJobs();
    else if (current.root === "job") renderDetail(current.id);
    else if (current.root === "sectors") renderSectors();
    else if (current.root === "study") renderStudy();
    else if (current.root === "trust") renderTrust();
    else { go("#/today"); return; }
    if (focus) requestAnimationFrame(() => main.querySelector("h1")?.focus({ preventScroll: true }));
  }

  function openFilters(opener) {
    const sector = document.getElementById("sectorFilter");
    const allSectors = [...new Set(getJobs().map((job) => job.sector))].sort((a, b) => a.localeCompare(b, "ko"));
    sector.innerHTML = `<option value="">모든 분야</option>${allSectors.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("")}`;
    sector.value = state.sector;
    document.getElementById("scoreFilter").value = String(state.minimumScore);
    document.getElementById("statusFilter").value = state.status;
    filterSheet.dataset.opener = opener ? "filter" : "";
    if (typeof filterSheet.showModal === "function") filterSheet.showModal(); else filterSheet.setAttribute("open", "");
    sector.focus();
  }

  function closeFilters() {
    if (filterSheet.open && typeof filterSheet.close === "function") filterSheet.close(); else filterSheet.removeAttribute("open");
    document.querySelector("[data-action='open-filters']")?.focus();
  }

  function resetFilters() {
    state.query = "";
    state.sector = "";
    state.minimumScore = 0;
    state.status = "";
    persistFilters();
    const search = document.getElementById("jobSearch");
    if (search) search.value = "";
    renderJobResults();
  }

  function updateNetworkStatus() {
    offlineBanner.hidden = navigator.onLine;
  }

  function updateSnapshotStatus() {
    const sourceCheck = state.data?.stats?.newestSourceCheck;
    const ageHours = sourceCheck ? (Date.now() - new Date(sourceCheck).getTime()) / 3600000 : Infinity;
    snapshotDot.classList.toggle("is-stale", ageHours > 48 || !navigator.onLine);
    snapshotLabel.textContent = navigator.onLine ? `자료 ${sourceDate(sourceCheck)}` : "오프라인 스냅샷";
  }

  async function loadData() {
    try {
      const response = await fetch("./data/app-data.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (!Array.isArray(payload.jobs) || !Array.isArray(payload.study)) throw new Error("snapshot schema mismatch");
      state.data = payload;
      updateNetworkStatus();
      updateSnapshotStatus();
      render(false);
      if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => undefined);
    } catch (error) {
      snapshotDot.classList.add("is-error");
      snapshotLabel.textContent = "자료 불러오기 실패";
      renderError("스냅샷을 열 수 없습니다", "인터넷 연결 또는 공개 파일을 확인한 뒤 다시 시도하세요.");
      console.error(error);
    }
  }

  document.addEventListener("click", (event) => {
    const routeButton = event.target.closest("[data-route]");
    if (routeButton) { go(`#/` + routeButton.dataset.route); return; }
    const jobButton = event.target.closest("[data-open-job]");
    if (jobButton) {
      state.returnScroll = window.scrollY;
      try { sessionStorage.setItem("career-compass-return-scroll", String(state.returnScroll)); } catch (_) { /* no-op */ }
      go(`#/job/${encodeURIComponent(jobButton.dataset.openJob)}`);
      return;
    }
    const sectorButton = event.target.closest("[data-sector]");
    if (sectorButton) { state.sector = sectorButton.dataset.sector; persistFilters(); go("#/jobs"); return; }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    if (action === "open-filters") openFilters(event.target.closest("button"));
    if (action === "clear-filters") resetFilters();
    if (action === "back-jobs") go("#/jobs");
    if (action === "bookmark") {
      const id = event.target.closest("[data-job-id]").dataset.jobId;
      if (state.bookmarks.has(id)) state.bookmarks.delete(id); else state.bookmarks.add(id);
      saveBookmarks(); render(false);
    }
    if (action === "retry") loadData();
  });

  document.getElementById("filterForm").addEventListener("submit", (event) => {
    event.preventDefault();
    state.sector = document.getElementById("sectorFilter").value;
    state.minimumScore = Number(document.getElementById("scoreFilter").value);
    state.status = document.getElementById("statusFilter").value;
    persistFilters();
    closeFilters();
    renderJobResults();
  });
  document.getElementById("resetFilters").addEventListener("click", () => { resetFilters(); closeFilters(); });
  filterSheet.addEventListener("cancel", () => closeFilters());
  window.addEventListener("hashchange", () => render());
  window.addEventListener("online", () => { updateNetworkStatus(); updateSnapshotStatus(); });
  window.addEventListener("offline", () => { updateNetworkStatus(); updateSnapshotStatus(); });
  document.getElementById("snapshotButton").addEventListener("click", () => go("#/trust"));
  loadData();
})();
