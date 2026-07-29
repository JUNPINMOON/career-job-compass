(() => {
  "use strict";

  const FILTER_STORAGE_KEY = "career-compass-filters-v2";
  const BOOKMARK_STORAGE_KEY = "career-compass-bookmarks";
  const FEEDBACK_STORAGE_KEY = "career-compass-job-feedback-v1";
  const REFRESH_WATCH_STORAGE_KEY = "career-compass-refresh-watch-v1";
  const LIVE_SNAPSHOT_STORAGE_KEY = "career-compass-live-snapshot-v1";
  const REFRESH_STAGE_SECONDS = {
    startup: 5,
    preference_binding: 5,
    collection_and_v3: 600,
    posting_facts: 45,
    feasibility: 45,
    sector_relevance: 90,
    preference_discovery: 45,
    review_evidence: 90,
    sector_labels: 45,
    feedback: 15,
    actions: 45,
  };
  const DEFAULT_FILTERS = { query: "", sector: "", queue: "", jobMarket: "all", studyMode: "programs", studyMarket: "all", studyReadiness: "all", studyFormat: "all", studyQuery: "" };
  const LIKE_REASON_LABELS = {
    field_fit: "관심 분야·연구 주제와 잘 맞음",
    role_fit: "직무·업무가 잘 맞음",
    growth: "성장·학습 기회가 큼",
    mission: "기관·프로젝트의 의미가 큼",
    location_fit: "근무지·근무 방식이 좋음",
    conditions_fit: "경력·언어·처우 조건이 현실적임",
    other_positive: "다른 좋은 이유",
  };
  const DISLIKE_REASON_LABELS = {
    role_mismatch: "직무·업무가 관심과 다름",
    seniority: "경력·자격 요건이 맞지 않음",
    location: "근무지·근무 방식이 맞지 않음",
    compensation: "급여·처우 정보가 부족하거나 아쉬움",
    language_visa: "언어·비자 조건이 부담됨",
    source_quality: "공고 정보·출처가 불명확함",
    other: "다른 이유",
  };
  const FEEDBACK_REASON_LABELS = { ...LIKE_REASON_LABELS, ...DISLIKE_REASON_LABELS };
  const FEEDBACK_CONFIG = {
    liked: { title: "왜 관심 있나요?", legend: "가치 있다고 느낀 이유를 모두 골라주세요", placeholder: "비슷한 공고를 찾을 때 반영할 구체적인 점", labels: LIKE_REASON_LABELS },
    not_for_me: { title: "왜 별로였나요?", legend: "해당하는 이유를 모두 골라주세요", placeholder: "다음 공고를 피할 때 참고할 구체적인 점", labels: DISLIKE_REASON_LABELS },
  };

  const state = {
    data: null,
    refreshRunId: null,
    refreshTimer: null,
    refreshClockTimer: null,
    refreshRunStatus: null,
    refreshRequestedAt: null,
    selectedTrigger: null,
    activeJobId: null,
    bookmarks: new Set(readJSON(BOOKMARK_STORAGE_KEY, [])),
    feedback: readJSON(FEEDBACK_STORAGE_KEY, {}),
    preferenceClient: null,
    preferenceUserId: null,
    syncState: "local",
    ...DEFAULT_FILTERS,
    ...readJSON(FILTER_STORAGE_KEY, {}),
  };

  const main = document.getElementById("mainContent");
  const filterSheet = document.getElementById("filterSheet");
  const dossier = document.getElementById("dossier");
  const feedbackSheet = document.getElementById("feedbackSheet");
  const snapshotLabel = document.getElementById("snapshotLabel");
  const offlineBanner = document.getElementById("offlineBanner");
  const engineRefresh = document.getElementById("engineRefresh");
  const refreshMonitor = document.getElementById("refreshMonitor");
  const refreshProgressTitle = document.getElementById("refreshProgressTitle");
  const refreshProgressPercent = document.getElementById("refreshProgressPercent");
  const refreshProgressBar = document.getElementById("refreshProgressBar");
  const refreshStageLabel = document.getElementById("refreshStageLabel");
  const refreshElapsed = document.getElementById("refreshElapsed");
  const refreshEta = document.getElementById("refreshEta");
  const refreshPreferenceCount = document.getElementById("refreshPreferenceCount");

  function readJSON(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (_) { return fallback; } }
  function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* local convenience only */ } }
  function preferenceFor(jobId) { return state.feedback?.[jobId] || null; }
  function persistPreferences() {
    store(FEEDBACK_STORAGE_KEY, state.feedback);
    state.bookmarks = new Set(Object.entries(state.feedback).filter(([, value]) => value?.sentiment === "liked").map(([jobId]) => jobId));
    store(BOOKMARK_STORAGE_KEY, [...state.bookmarks]);
  }
  function setLocalPreference(jobId, preference) {
    if (!preference) delete state.feedback[jobId];
    else state.feedback[jobId] = {
      sentiment: preference.sentiment,
      reasons: Array.isArray(preference.reasons) ? preference.reasons : [],
      note: String(preference.note || ""),
      updatedAt: preference.updatedAt || new Date().toISOString(),
    };
    persistPreferences();
  }
  function migrateLocalBookmarks() {
    /* data-requirement-id="DATA-202" */
    let changed = false;
    state.bookmarks.forEach((jobId) => {
      if (preferenceFor(jobId)) return;
      state.feedback[jobId] = { sentiment: "liked", reasons: [], note: "", updatedAt: new Date().toISOString() };
      changed = true;
    });
    if (changed) persistPreferences();
  }
  function saveFilters() { store(FILTER_STORAGE_KEY, { query: state.query, sector: state.sector, queue: state.queue, jobMarket: state.jobMarket, studyMode: state.studyMode, studyMarket: state.studyMarket, studyReadiness: state.studyReadiness, studyFormat: state.studyFormat, studyQuery: state.studyQuery }); }
  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])); }
  function icon(name) { return `<svg aria-hidden="true"><use href="#i-${name}" /></svg>`; }
  function route() { const value = (location.hash || "#/today").replace(/^#\/?/, "").split("/")[0]; return value === "trust" ? "sources" : value || "today"; }
  function go(path) { location.hash = path; }
  function sourceDate(value) { const date = value ? new Date(value) : null; return date && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat("ko-KR", { month: "long", day: "numeric" }).format(date) : "확인 시각 없음"; }
  function displayDate(value) { const date = value ? new Date(value) : null; return date && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "long", timeStyle: "short" }).format(date) : "확인 시각 없음"; }
  function requiredExperienceYears(job) {
    const years = Number(job?.minimumExperienceYears);
    return Number.isFinite(years) && years > 0 ? years : 0;
  }
  function isEligiblePublicJob(job) { return requiredExperienceYears(job) < 2 && job?.publicEligibility !== "excluded"; }
  function jobs() { return (state.data?.jobs || []).filter(isEligiblePublicJob); }
  function reviewQueue() { return (state.data?.reviewQueue || []).filter(isEligiblePublicJob); }
  function recommendationJobs() {
    /* data-requirement-id="DATA-212" */
    return jobs().filter((job) => !["liked", "not_for_me"].includes(preferenceFor(job.id)?.sentiment));
  }
  function programs() { return state.data?.programs || []; }
  function funding() { return state.data?.funding || []; }
  function jobSectors(job) { return [...new Set((Array.isArray(job.sectors) ? job.sectors : [job.sector]).filter(Boolean))]; }
  function allJobSectors() { return (state.data?.sectors || []).map((sector) => sector.name).filter(Boolean); }
  function programReadiness(item) { return item.applicationStatus || (item.decision === "Use now" ? "prepare" : "research"); }
  function programReadinessLabel(item) { return item.applicationStatusLabel || (programReadiness(item) === "prepare" ? "지금 준비" : "추가 조사"); }
  function chunks(items, size) { return Array.from({ length: Math.ceil(items.length / size) }, (_, index) => items.slice(index * size, index * size + size)); }
  function setActiveTab(current) {
    document.documentElement.dataset.route = current;
    document.querySelectorAll("[data-tab]").forEach((tab) => tab.toggleAttribute("aria-current", tab.dataset.tab === current));
    document.querySelector("[data-action='open-filters']")?.toggleAttribute("hidden", current !== "jobs");
  }
  function activeFilters() { return Number(Boolean(state.query)) + Number(Boolean(state.sector)) + Number(Boolean(state.queue)) + Number(state.jobMarket !== "all"); }
  function jobById(id) { return jobs().find((job) => job.id === id); }
  function recordById(kind, id) { return (kind === "program" ? programs() : funding()).find((item) => item.id === id); }
  function marketCount(records, market) { return records.filter((record) => record.market === market).length; }
  function marketLabel(market) { return market === "domestic" ? "국내" : market === "overseas" ? "해외" : "확인 필요"; }
  function marketSwitch(scope, active, records) {
    const selected = (value) => active === value ? "true" : "false";
    return `<div class="market-switch" role="tablist" aria-label="${scope === "job" ? "공고 근무지" : "진학 자료 지역"}"><button type="button" role="tab" aria-selected="${selected("all")}" data-${scope}-market="all">전체 <b>${records.length}</b></button><button type="button" role="tab" aria-selected="${selected("domestic")}" data-${scope}-market="domestic">국내 <b>${marketCount(records, "domestic")}</b></button><button type="button" role="tab" aria-selected="${selected("overseas")}" data-${scope}-market="overseas">해외 <b>${marketCount(records, "overseas")}</b></button><button type="button" role="tab" aria-selected="${selected("unknown")}" data-${scope}-market="unknown">확인 필요 <b>${marketCount(records, "unknown")}</b></button></div>`;
  }

  function pageFrame(content, index, total, label) {
    /* data-requirement-id="UX-216" */
    const previous = index > 0 ? `<button class="page-turn-prev" type="button" data-action="page-prev" aria-label="이전 화면">이전</button>` : `<span aria-hidden="true"></span>`;
    const next = index < total - 1 ? `<button class="page-turn-next" type="button" data-action="page-next" aria-label="다음 화면">다음 ${icon("arrow")}</button>` : `<span class="page-finish">끝</span>`;
    return `<section class="page-frame ${index === 0 ? "is-active" : ""}" data-page-index="${index}" aria-label="${escapeHtml(label)} ${index + 1} / ${total}"><div class="page-frame-content">${content}</div><nav class="page-turn" aria-label="${escapeHtml(label)} 화면 이동">${previous}<span class="page-counter">${String(index + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}</span>${next}</nav></section>`;
  }

  function movePage(trigger, direction) {
    const frame = trigger.closest(".page-frame");
    const frames = [...main.querySelectorAll(".page-frame")];
    const currentIndex = frames.indexOf(frame);
    const target = frames[currentIndex + (direction === "next" ? 1 : -1)];
    if (!target) return;
    frame.classList.remove("is-active");
    target.classList.add("is-active");
    target.querySelector(".page-frame-content")?.scrollTo({ top: 0, behavior: "auto" });
    target.querySelector("h1, h2, [data-open-job], button, a")?.focus({ preventScroll: true });
    navigator.vibrate?.(8);
  }

  function filteredJobs() {
    const query = String(state.query || "").trim().toLocaleLowerCase("ko");
    return recommendationJobs().filter((job) => {
      const sectors = jobSectors(job);
      const haystack = [job.title, job.company, job.location, ...sectors, job.source, job.nextAction, ...(job.requirements || [])].join(" ").toLocaleLowerCase("ko");
      return (!query || haystack.includes(query)) && (!state.sector || sectors.includes(state.sector)) && (!state.queue || job.queue === state.queue) && (state.jobMarket === "all" || job.market === state.jobMarket);
    });
  }

  function diversifiedJobs(records) {
    if (state.jobMarket !== "all" || state.query || state.sector || state.queue) return records;
    const buckets = ["domestic", "overseas", "unknown"].map((market) => records.filter((job) => job.market === market));
    const ordered = [];
    while (buckets.some((bucket) => bucket.length)) {
      buckets.forEach((bucket) => { if (bucket.length) ordered.push(bucket.shift()); });
    }
    return ordered;
  }

  function filteredStudy() {
    const query = String(state.studyQuery || "").trim().toLocaleLowerCase("ko");
    const records = state.studyMode === "funding" ? funding() : programs();
    return records.filter((item) => (state.studyMarket === "all" || item.market === state.studyMarket) && (state.studyMode === "funding" || state.studyReadiness === "all" || programReadiness(item) === state.studyReadiness) && (state.studyMode === "funding" || state.studyFormat === "all" || item.deliveryMode === state.studyFormat) && (!query || Object.values(item).flat().join(" ").toLocaleLowerCase("ko").includes(query)));
  }

  function queueCopy(job) { return escapeHtml(job.discoveryLabel || job.queueLabel || "검토 후보"); }
  function candidateRow(job, compact = false) {
    const preference = preferenceFor(job.id);
    const saved = preference?.sentiment === "liked";
    const rejected = preference?.sentiment === "not_for_me";
    return `<article class="opportunity ${compact ? "is-compact" : ""}" data-requirement-id="UX-211" data-requirement-id-market="DATA-206">
      <button class="opportunity-main" type="button" data-open-job="${escapeHtml(job.id)}">
        <span class="queue-mark"><b>${queueCopy(job)}</b><small>${marketLabel(job.market)}</small></span>
        <span class="opportunity-copy"><em>${escapeHtml(job.company)}</em><strong>${escapeHtml(job.title)}</strong><small>${escapeHtml(job.location)}</small></span>
        <span class="opportunity-arrow">${icon("arrow")}</span>
      </button>
      <div class="opportunity-foot"><span><i class="source-dot"></i>${escapeHtml(jobSectors(job).join(" · ") || "분야 원문 확인")}</span><span>${rejected ? "별로예요 · 개인화에 반영됨" : escapeHtml(job.sectorEvidence || (job.discoveryTier === "explore" ? "분야 원문 근거" : "공식 원문 · 조건 확인"))}</span></div>
      <div class="card-preference-actions" aria-label="이 공고에 대한 피드백">
        <button class="card-preference is-like ${saved ? "is-active" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="liked" data-job-id="${escapeHtml(job.id)}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}<span>${saved ? "관심 이유 수정" : "관심"}</span></button>
        <button class="card-preference is-dislike ${rejected ? "is-active" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="not_for_me" data-job-id="${escapeHtml(job.id)}" aria-pressed="${rejected}"><span>${rejected ? "이유 수정" : "별로예요"}</span></button>
      </div>
    </article>`;
  }

  function renderToday() {
    const ranked = state.data?.stats?.recommendationSurface === "ranked";
    const eligibleRecommendations = recommendationJobs();
    const eligibleIds = new Set(eligibleRecommendations.map((job) => job.id));
    const prioritized = ranked ? reviewQueue().filter((job) => eligibleIds.has(job.id)) : [];
    const baseCandidates = prioritized.length ? prioritized : diversifiedJobs(eligibleRecommendations);
    const dailyCandidates = baseCandidates
      .filter((job, index, records) => records.findIndex((item) => item.id === job.id) === index)
      .slice(0, 4);
    const hasPersonalFeedback = Object.keys(state.feedback).length > 0;
    const lead = dailyCandidates[0];
    const school = programs()[0];
    const award = funding()[0];
    const candidatePage = dailyCandidates.length ? `<section class="decision-list" aria-labelledby="priorityHeading"><div class="section-heading"><div><span>${hasPersonalFeedback ? "내 피드백으로 찾은 새 후보" : (ranked ? "개인화 추천" : "관심 탐색")}</span><h2 id="priorityHeading">오늘 열어볼 후보</h2></div><a href="#/jobs">새 후보 ${eligibleRecommendations.length}개 ${icon("arrow")}</a></div><div class="opportunity-list">${dailyCandidates.map((job) => candidateRow(job)).join("")}</div></section>` : `<section class="decision-list" aria-labelledby="inventoryHeading"><div class="section-heading"><div><span>새 공고 인벤토리</span><h2 id="inventoryHeading">저장·제외하지 않은 공고가 없습니다</h2></div><a href="#/saved">저장한 공고 ${icon("arrow")}</a></div></section>`;
    const researchPage = `<section class="route-callout" aria-labelledby="researchHeading"><div class="route-callout-copy"><p class="eyebrow">02 · 진학과 장학</p><h2 id="researchHeading">과정과 장학금</h2><a class="ink-link" href="#/study">전체 보기 ${icon("arrow")}</a></div><div class="route-mini-list">${school ? `<button type="button" data-open-record="program:${escapeHtml(school.id)}"><small>${escapeHtml(school.degree)} · ${escapeHtml(programReadinessLabel(school))}</small><b>${escapeHtml(school.university)}</b><span>${escapeHtml(school.program)}</span>${icon("arrow")}</button>` : ""}${award ? `<button type="button" data-open-record="funding:${escapeHtml(award.id)}"><small>${escapeHtml(award.decision)}</small><b>${escapeHtml(award.name)}</b><span>${escapeHtml(award.coverage || "지원 범위 원문 확인")}</span>${icon("arrow")}</button>` : ""}</div></section>`;
    const pages = [
      `<section class="today-cover" data-requirement-id="UX-204" aria-labelledby="todayTitle"><div class="cover-meta"><span>오늘의 목록</span><span>${escapeHtml(sourceDate(state.data.stats?.jobDataAsOf))}</span></div><div class="cover-copy"><p>공개 스냅샷</p><h1 id="todayTitle">오늘 볼 것</h1></div>${lead ? `<button class="cover-action" type="button" data-open-job="${escapeHtml(lead.id)}"><span>${ranked ? "새 우선 후보" : "새 관심 후보"}</span><b>${escapeHtml(lead.company)}<em>${escapeHtml(lead.title)}</em></b>${icon("arrow")}</button>` : `<a class="cover-action" href="#/saved"><span>새 후보 확인 완료</span><b>저장한 공고 보기</b>${icon("arrow")}</a>`}</section>`,
      candidatePage,
      researchPage,
    ];
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "오늘")).join("");
  }

  function renderJobResults() {
    const target = document.getElementById("jobResults");
    if (!target) return;
    const results = diversifiedJobs(filteredJobs());
    const pages = chunks(results, 3);
    target.innerHTML = results.length ? pages.map((group, pageIndex) => pageFrame(`<section class="results-section"><div class="results-meta"><span>${state.data?.stats?.recommendationSurface === "exploration_only" ? "관심 탐색" : "검토 항목"} ${pageIndex * 3 + 1}–${Math.min((pageIndex + 1) * 3, results.length)}</span><b>${results.length}개</b></div><div class="opportunity-list is-results">${group.map((job) => candidateRow(job, true)).join("")}</div></section>`, pageIndex + 1, pages.length + 1, "공고 탐색")).join("") : pageFrame(`<section class="results-section"><div class="empty"><p>해당 조건의 공고가 없습니다.</p><button class="plain-button" type="button" data-action="clear-filters">필터 초기화</button></div></section>`, 1, 2, "공고 탐색");
  }

  function renderJobs() {
    const availableJobs = recommendationJobs();
    const sectors = (state.data.sectors || []).map((sector) => `<button class="sector-chip ${state.sector === sector.name ? "is-active" : ""}" type="button" data-sector="${escapeHtml(sector.name)}">${escapeHtml(sector.name)} <b>${availableJobs.filter((job) => jobSectors(job).includes(sector.name)).length}</b></button>`).join("");
    const total = Math.max(1, chunks(filteredJobs(), 3).length) + 1;
    const ranked = state.data?.stats?.recommendationSurface === "ranked";
    const exploring = state.data?.stats?.recommendationSurface === "exploration_only";
    main.innerHTML = pageFrame(`<section class="browse-head"><p class="eyebrow">${ranked ? "개인화 새 추천" : (exploring ? "관심 탐색" : "새 공고 인벤토리")}</p><div class="browse-title-row"><h1>새 국내·해외 공고</h1><button class="filter-trigger" type="button" data-action="open-filters" aria-label="공고 필터">${icon("filter")}${activeFilters() ? `<b>${activeFilters()}</b>` : ""}</button></div><label class="search-box">${icon("search")}<span class="sr-only">공고 검색</span><input id="jobSearch" type="search" value="${escapeHtml(state.query)}" placeholder="직무, 기관, 지역으로 찾기" autocomplete="off" /></label>${marketSwitch("job", state.jobMarket || "all", availableJobs)}<div class="sector-grid" data-requirement-id="UX-201"><button class="sector-chip ${!state.sector ? "is-active" : ""}" type="button" data-sector="">전체</button>${sectors}</div></section>`, 0, total, "공고 탐색") + `<div id="jobResults"></div>`;
    document.getElementById("jobSearch").addEventListener("input", (event) => { state.query = event.target.value; saveFilters(); renderJobResults(); });
    renderJobResults();
  }

  function renderSaved() {
    /* data-requirement-id="UX-217" */
    const savedJobs = jobs().filter((job) => preferenceFor(job.id)?.sentiment === "liked");
    const pages = chunks(savedJobs, 3);
    if (!savedJobs.length) {
      main.innerHTML = pageFrame(`<section class="results-section"><div class="section-heading"><div><span>관심 보관함</span><h1>저장한 공고</h1></div></div><div class="empty"><p>아직 저장한 공고가 없습니다.</p><a class="plain-button" href="#/jobs">새 공고 탐색하기</a></div></section>`, 0, 1, "저장한 공고");
      return;
    }
    main.innerHTML = pages.map((group, pageIndex) => pageFrame(`<section class="results-section"><div class="section-heading"><div><span>관심 보관함</span><h1>${pageIndex === 0 ? "저장한 공고" : `저장한 공고 ${pageIndex + 1}`}</h1></div><b>${savedJobs.length}개</b></div><div class="opportunity-list is-results">${group.map((job) => candidateRow(job, true)).join("")}</div></section>`, pageIndex, pages.length, "저장한 공고")).join("");
  }

  function studyRow(item, kind) {
    const isProgram = kind === "program";
    const research = item.publicResearch || {};
    const paperCount = (research.faculty || []).reduce((total, person) => total + (person.recentPapers || []).length, 0);
    const evidenceCount = (research.faculty || []).length + paperCount + (research.recentProjects || []).length + (research.graduateDestinations || []).length;
    const number = "•";
    const line = isProgram ? `${programReadinessLabel(item)} · ${item.degree || "과정"}${item.deliveryMode === "online" ? " · 온라인" : ""} · ${item.country || "국가 원문 확인"}` : `${item.decision || "장학금"} · ${(item.countries || []).join(", ") || "지역 원문 확인"}`;
    const title = isProgram ? item.program : item.name;
    const subtitle = isProgram ? item.university : item.coverage || item.type;
    const note = isProgram && evidenceCount
      ? `교수 ${(research.faculty || []).length} · 논문 ${paperCount} · 용역 ${(research.recentProjects || []).length} · 진로 ${(research.graduateDestinations || []).length}`
      : (isProgram ? item.funding || item.deadline || "마감 원문 확인" : item.deadline || item.verification || "조건 원문 확인");
    return `<button class="study-row" type="button" data-open-record="${kind}:${escapeHtml(item.id)}"><span>${escapeHtml(number)}</span><div><small>${escapeHtml(line)}</small><h2>${escapeHtml(title)}</h2><p>${escapeHtml(subtitle)}</p><em>${escapeHtml(note)}</em></div>${icon("arrow")}</button>`;
  }

  function renderStudyResults() {
    const target = document.getElementById("studyResults");
    if (!target) return;
    const records = filteredStudy();
    const kind = state.studyMode === "funding" ? "funding" : "program";
    const pages = chunks(records, 3);
    target.innerHTML = records.length ? pages.map((group, pageIndex) => pageFrame(`<section class="study-list" aria-label="${kind === "program" ? "대학원 과정" : "장학금"}"><div class="results-meta"><span>${kind === "program" ? "대학원" : "장학금"} ${pageIndex * 3 + 1}–${Math.min((pageIndex + 1) * 3, records.length)}</span><b>${records.length}개</b></div>${group.map((item) => studyRow(item, kind)).join("")}</section>`, pageIndex + 1, pages.length + 1, "진학과 재정")).join("") : pageFrame(`<section class="study-list"><div class="empty"><p>검색어와 맞는 항목이 없습니다.</p></div></section>`, 1, 2, "진학과 재정");
  }

  function renderStudy() {
    const isFunding = state.studyMode === "funding";
    const total = Math.max(1, chunks(filteredStudy(), 3).length) + 1;
    const studyRecords = isFunding ? funding() : programs();
    const coverage = state.data.graduateEvidenceCoverage || {};
    const coverageTotal = coverage.totalPrograms || programs().length;
    const openPrograms = programs().filter((item) => programReadiness(item) === "open").length;
    const preparePrograms = programs().filter((item) => programReadiness(item) === "prepare").length;
    const onlinePrograms = programs().filter((item) => item.deliveryMode === "online").length;
    const readinessSwitch = isFunding ? "" : `<div class="market-switch study-readiness" role="tablist" aria-label="대학원 지원 상태"><button type="button" role="tab" aria-selected="${state.studyReadiness === "all"}" data-study-readiness="all">전체 <b>${programs().length}</b></button><button type="button" role="tab" aria-selected="${state.studyReadiness === "open"}" data-study-readiness="open">지원 열림 <b>${openPrograms}</b></button><button type="button" role="tab" aria-selected="${state.studyReadiness === "prepare"}" data-study-readiness="prepare">지금 준비 <b>${preparePrograms}</b></button></div><p class="study-status-note">‘지원 열림’은 현재 공식 원문으로 접수 상태가 확인된 항목만 표시합니다.</p>`;
    const formatSwitch = isFunding ? "" : `<div class="market-switch study-format" role="tablist" aria-label="대학원 수강 방식"><button type="button" role="tab" aria-selected="${state.studyFormat === "all"}" data-study-format="all">전체 <b>${programs().length}</b></button><button type="button" role="tab" aria-selected="${state.studyFormat === "online"}" data-study-format="online">온라인 <b>${onlinePrograms}</b></button></div>`;
    const coveragePanel = isFunding ? "" : `<section class="graduate-coverage" data-requirement-id="UX-224"><div class="graduate-coverage-heading"><div><p class="eyebrow">대학원 근거 현황</p><h2>전체 ${coverageTotal}개 과정 기준</h2></div><p>빈칸은 추정하지 않고 미조사로 남깁니다.</p></div><div class="graduate-coverage-grid"><div><small>교수 근거</small><b>${coverage.programsWithFaculty || 0}<i>/${coverageTotal}</i></b></div><div><small>최근 5년 논문</small><b>${coverage.programsWithRecentPapers || 0}<i>/${coverageTotal}</i></b></div><div><small>연구용역</small><b>${coverage.programsWithFundedProjects || 0}<i>/${coverageTotal}</i></b></div><div><small>취업 근거</small><b>${coverage.programsWithGraduateDestinations || 0}<i>/${coverageTotal}</i></b></div><div><small>동문 후기</small><b>${coverage.programsWithTestimonials || 0}<i>/${coverageTotal}</i></b></div><div><small>근거 미연결</small><b>${coverage.unresearchedPrograms || 0}<i>/${coverageTotal}</i></b></div></div></section>`;
    main.innerHTML = pageFrame(`<section class="study-head"><div><p class="eyebrow">진학 · 장학 · 연구</p><h1>대학원 · 장학금</h1></div><p>대학원 ${programs().length} · 온라인 ${onlinePrograms} · 장학금 ${funding().length}</p></section>${coveragePanel}<section class="study-controls"><div class="mode-switch" role="tablist" aria-label="진학 자료 종류"><button type="button" role="tab" aria-selected="${!isFunding}" data-study-mode="programs">대학원 <b>${programs().length}</b></button><button type="button" role="tab" aria-selected="${isFunding}" data-study-mode="funding">장학금 <b>${funding().length}</b></button></div>${readinessSwitch}${formatSwitch}${marketSwitch("study", state.studyMarket || "all", studyRecords)}<label class="search-box">${icon("search")}<span class="sr-only">진학 자료 검색</span><input id="studySearch" type="search" value="${escapeHtml(state.studyQuery)}" placeholder="학교, 과정, 장학금으로 찾기" autocomplete="off" /></label></section>`, 0, total, "진학과 재정") + `<div id="studyResults"></div>`;
    document.getElementById("studySearch").addEventListener("input", (event) => { state.studyQuery = event.target.value; saveFilters(); renderStudyResults(); });
    renderStudyResults();
  }

  function feedbackReviewList(records, sentiment) {
    if (!records.length) {
      return `<p class="feedback-review-empty">${sentiment === "liked" ? "아직 관심 공고가 없습니다." : "아직 별로예요 기록이 없습니다. 공고 카드의 별로예요를 누르면 이유를 남길 수 있습니다."}</p>`;
    }
    return `<div class="feedback-review-list">${records.map((job) => {
      const preference = preferenceFor(job.id);
      const reasons = (preference?.reasons || []).map((reason) => FEEDBACK_REASON_LABELS[reason] || reason);
      const reasonCopy = reasons.join(" · ") || "이유 미기록";
      return `<article class="feedback-review-item">
        <button class="feedback-review-job" type="button" data-open-job="${escapeHtml(job.id)}">
          <small>${escapeHtml(job.company)}</small><strong>${escapeHtml(job.title)}</strong>
        </button>
        <div class="feedback-review-reason ${sentiment === "liked" ? "is-liked" : ""}"><span>${escapeHtml(reasonCopy)}</span>${preference?.note ? `<p>${escapeHtml(preference.note)}</p>` : ""}</div><button class="feedback-edit ${sentiment === "liked" ? "is-liked" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="${sentiment}" data-job-id="${escapeHtml(job.id)}">${reasonCopy === "이유 미기록" ? "이유 추가" : "이유 수정"}</button>
      </article>`;
    }).join("")}</div>`;
  }

  function renderSources() {
    const stats = state.data.stats || {};
    const likedJobs = jobs().filter((job) => preferenceFor(job.id)?.sentiment === "liked");
    const dislikedJobs = jobs().filter((job) => preferenceFor(job.id)?.sentiment === "not_for_me");
    const likedCount = Object.values(state.feedback).filter((item) => item?.sentiment === "liked").length;
    const dislikedCount = Object.values(state.feedback).filter((item) => item?.sentiment === "not_for_me").length;
    const syncCopy = state.syncState === "synced" ? "Supabase에 저장됨" : state.syncState === "syncing" ? "Supabase에 저장 중" : state.syncState === "error" ? "연결 실패 · 이 기기에 안전하게 보관 중" : "이 기기에 보관 중";
    const pages = [
      `<section class="sources-head"><p class="eyebrow">자료의 범위</p><h1>무엇을 담고,<br />어디까지 아는가.</h1><p>${escapeHtml(state.data.snapshotBoundary)}</p></section>`,
      `<section class="source-stamp"><span>PUBLIC SNAPSHOT</span><b>${displayDate(state.data.generatedAt)}</b><i>V4<br />FIRST</i></section><section class="stat-strip"><div><small>${stats.recommendationSurface === "exploration_only" ? "관심 후보" : "행동 후보"}</small><b>${escapeHtml(stats.actionCandidates)}</b></div><div><small>대학원</small><b>${escapeHtml(stats.programs)}</b></div><div><small>장학금</small><b>${escapeHtml(stats.funding)}</b></div></section>`,
      `<section class="preference-panel" data-requirement-id="UX-212"><p class="eyebrow">나의 학습 신호</p><h2>공고 피드백</h2><p>공고 카드에서 바로 관심 또는 별로예요를 누르고 이유를 남길 수 있습니다. 저장한 내용은 다음 후보 구성에 반영됩니다.</p><div class="preference-counts"><div><small>관심 공고</small><b>${likedCount}</b></div><div><small>별로예요</small><b>${dislikedCount}</b></div></div><p class="sync-status" data-state="${state.syncState}" data-requirement-id="UX-210">${syncCopy}</p><div data-requirement-id="UX-221"><section class="feedback-review-group"><div class="feedback-review-heading"><h3>관심 공고와 좋은 이유</h3><b>${likedCount}</b></div>${feedbackReviewList(likedJobs, "liked")}</section><section class="feedback-review-group"><div class="feedback-review-heading"><h3>별로예요와 이유</h3><b>${dislikedCount}</b></div>${feedbackReviewList(dislikedJobs, "not_for_me")}</section></div><button class="plain-button export-button" type="button" data-action="export-feedback">피드백 내보내기</button></section>`,
      `<section class="source-explainer"><p class="eyebrow">검증 경계</p><h2>점수로 결론을 대신하지 않습니다.</h2><p>공고는 최신 V4 행동 큐를, 진학·재정은 현재 대시보드의 연구 목록을 사용합니다. 공개 화면에는 개인 프로필, 지원 이력, CRM 정보가 포함되지 않습니다.</p><div class="status-rows"><div><span>V4 실행 ID</span><b>${escapeHtml(stats.v4RunId || "확인 중")}</b></div><div><span>공고 기준일</span><b>${escapeHtml(stats.jobDataAsOf || "확인 중")}</b></div><div><span>대학원 자료 생성</span><b>${escapeHtml(stats.graduateGeneratedAt || "확인 중")}</b></div></div></section>`,
    ];
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "자료")).join("");
  }

  function detailList(title, values) { return values?.length ? `<section class="detail-list"><small>${escapeHtml(title)}</small><ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>` : ""; }
  function officialLink(url) { return url ? `<a class="official-button" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">공식 원문 열기 ${icon("external")}</a>` : `<span class="official-button is-disabled">공식 원문 주소 없음</span>`; }
  function renderJobDetail(job) {
    const preference = preferenceFor(job.id);
    const saved = preference?.sentiment === "liked";
    const rejected = preference?.sentiment === "not_for_me";
    const discovery = job.discoveryTier === "explore";
    dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${escapeHtml(job.source)} · ${queueCopy(job)}</small><button class="detail-close" type="button" data-action="close-dossier">닫기</button></div></header><div class="detail-body"><p class="detail-kicker">${escapeHtml(jobSectors(job).join(" · ") || "분야 원문 확인")}</p><h2 id="dossierTitle">${escapeHtml(job.title)}</h2><p class="detail-company">${escapeHtml(job.company)} · ${escapeHtml(job.location)}</p><div class="detail-primary">${officialLink(job.url)}</div><div class="detail-facts"><div><small>${discovery ? "분류" : "행동 상태"}</small><b>${queueCopy(job)}</b></div><div><small>마감</small><b>${escapeHtml(job.deadline || "원문 확인")}</b></div><div><small>증거 공백</small><b>${job.evidenceGapCount ?? "원문 확인"}</b></div><div><small>확인 부담</small><b>${escapeHtml(job.evidenceBurden || "원문 확인")}</b></div></div>${discovery ? `<section class="check-note"><small>보여드린 이유</small><p>${escapeHtml(job.discoveryReason)}</p></section>` : ""}<section class="check-note"><small>${discovery ? "원문에서 먼저 볼 것" : "다음 행동"}</small><p>${escapeHtml(job.nextAction)}</p></section>${detailList("공고에서 확인된 조건", job.requirements)}${detailList("추가 확인 항목", job.checks)}${detailList("주의 사항", job.risks)}<div class="detail-actions"><button class="detail-save ${saved ? "is-saved" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="liked" data-job-id="${escapeHtml(job.id)}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}${saved ? "관심 이유 수정" : "관심 있어요"}</button><button class="plain-button detail-dislike ${rejected ? "is-active" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="not_for_me" data-job-id="${escapeHtml(job.id)}" aria-pressed="${rejected}">${rejected ? "별로예요 반영됨" : "별로예요"}</button></div></div></article>`;
  }

  function evidenceItem(title, meta, note, url) {
    const tag = url ? "a" : "div";
    const attributes = url ? ` href="${escapeHtml(url)}" target="_blank" rel="noreferrer"` : "";
    return `<${tag} class="evidence-item"${attributes}><small>${escapeHtml(meta || "공개 원문")}</small><strong>${escapeHtml(title)}</strong>${note ? `<span>${escapeHtml(note)}</span>` : ""}</${tag}>`;
  }

  function sourceTypeLabel(sourceType) {
    const labels = {
      official_faculty_profile: "대학 공식 교수 페이지",
      official_faculty_directory: "대학 공식 교수 명단",
      official_research_profile: "대학 공식 연구자 페이지",
      official_program_page: "대학 공식 과정 페이지",
      official_alumni_outcome: "대학 공식 동문 자료",
      public_linkedin_profile: "LinkedIn 공개 프로필",
      public_alumni_review: "공개 동문 후기",
      untyped_faculty_source: "기존 교수 근거 · 유형 재검증 필요",
      untyped_public_source: "기존 공개 근거 · 유형 재검증 필요",
    };
    return labels[sourceType] || sourceType || "공개 원문";
  }

  function evidenceSources(sources) {
    if (!sources?.length) return `<p class="evidence-empty">연결된 공개 원문이 없습니다.</p>`;
    return `<div class="evidence-source-list">${sources.map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer"><small>근거 유형 · ${escapeHtml(sourceTypeLabel(source.sourceType))}</small><span>${escapeHtml(source.label || "원문 열기")}</span></a>`).join("")}</div>`;
  }

  function graduateResearchPanels(item) {
    /* data-requirement-id="UX-222" */
    /* data-requirement-id="UX-223" */
    const research = item.publicResearch || {};
    const faculty = research.faculty || [];
    const projects = research.recentProjects || [];
    const destinations = research.graduateDestinations || [];
    const graduateOutcomeSources = research.graduateOutcomeSources || [];
    const graduateTestimonials = research.graduateTestimonials || [];
    const papers = faculty.flatMap((person) => person.recentPapers || []);
    const summary = `<div class="research-summary"><span>교수 ${faculty.length}</span><span>최근 5년 논문 ${papers.length}</span><span>연구용역 ${projects.length}</span><span>취업 근거 ${destinations.length}</span><span>동문 후기 ${graduateTestimonials.length}</span></div>`;
    const facultyHtml = faculty.length ? faculty.map((person) => {
      const personPapers = (person.recentPapers || []).map((paper) => evidenceItem(paper.title, [paper.year, paper.venue].filter(Boolean).join(" · "), "", paper.url)).join("");
      const profileSources = person.profileSources || (person.profileUrls || []).map((url) => ({ url, sourceType: "official_faculty_profile", label: "교수 공식 프로필" }));
      return `<section class="evidence-card"><h3>${escapeHtml(person.name || "교수 프로필")}</h3><p>${escapeHtml([person.title, person.labOrGroup].filter(Boolean).join(" · ") || "소속 원문 확인")}</p>${evidenceSources(profileSources)}${personPapers ? `<div class="evidence-items">${personPapers}</div>` : `<p class="evidence-empty">최근 5년 논문 원문을 추가 확인해야 합니다.</p>`}</section>`;
    }).join("") : `<p class="evidence-empty">이 과정은 공개 교수·논문 근거가 아직 연결되지 않았습니다.</p>`;
    const projectHtml = projects.length ? `<div class="evidence-items">${projects.map((project) => evidenceItem(project.title, [project.period, project.funder].filter(Boolean).join(" · "), `공개 금액: ${project.amount || "미확인"}`, project.url)).join("")}</div>` : `<p class="evidence-empty">최근 5년 연구용역의 공개 원문과 금액을 확인하지 못했습니다. 금액은 추정하지 않습니다.</p>`;
    const destinationHtml = `<section class="outcome-evidence-section"><h3>취업 근거</h3>${destinations.length ? destinations.map((record) => `<article class="evidence-card"><strong>${escapeHtml(record.destination)}</strong><p>${escapeHtml([record.period, record.role].filter(Boolean).join(" · "))}</p>${evidenceSources(record.sources || [])}</article>`).join("") : `<p class="evidence-empty">졸업생 취업처를 뒷받침하는 공개 원문을 확인하지 못했습니다.</p>`}</section><section class="outcome-evidence-section"><h3>동문 후기</h3>${graduateTestimonials.length ? graduateTestimonials.map((record) => `<article class="evidence-card"><strong>${escapeHtml(record.person || "공개 동문")}</strong><p>${escapeHtml(record.summary)}</p>${record.context ? `<small>${escapeHtml(record.context)}</small>` : ""}${evidenceSources(record.sources || [])}</article>`).join("") : `<p class="evidence-empty">공개 동문 후기를 아직 연결하지 못했습니다.</p>`}</section><span hidden>${graduateOutcomeSources.length}</span>`;
    return {
      summary,
      facultyHtml,
      projectHtml,
      destinationHtml,
      boundary: `<p class="detail-boundary">${escapeHtml(research.evidenceStatus || "공개 연구자료 추가 확인 필요")}${research.lastVerified ? ` · ${escapeHtml(research.lastVerified)}` : ""}</p>`,
    };
  }

  function renderRecordDetail(kind, item) {
    const isProgram = kind === "program";
    const title = isProgram ? item.program : item.name;
    const organisation = isProgram ? item.university : item.coverage || item.type;
    const source = isProgram ? "대학원 연구" : "장학금 연구";
    const facts = isProgram ? [["지원 상태", programReadinessLabel(item)], ["국가", item.country], ["과정", item.degree], ["마감", item.deadline], ["검증", item.verification]] : [["지원 범위", item.coverage], ["대상 국가", (item.countries || []).join(", ")], ["마감", item.deadline], ["검증", item.verification]];
    const extra = isProgram ? [["분류 근거", item.applicationStatusReason], ["재정", item.funding], ["영어", item.english], ["확인일", item.verifiedAt]] : [["선발 가능성", item.likelihood], ["유형", item.type]];
    const overview = `<div class="detail-facts">${facts.map(([label, value]) => `<div><small>${escapeHtml(label)}</small><b>${escapeHtml(value || "원문 확인")}</b></div>`).join("")}</div>${extra.filter(([, value]) => value).map(([label, value]) => `<section class="check-note"><small>${escapeHtml(label)}</small><p>${escapeHtml(value)}</p></section>`).join("")}${isProgram ? detailList(item.englishStatus || "영어 공식 기준", item.englishCriteria) : ""}${isProgram ? detailList("영어 준비", item.englishGapPlan) : ""}${detailList("지원 전 확인할 조건", item.gates)}${detailList("주의 사항", item.risks)}`;
    if (!isProgram) {
      dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${source}</small><button class="detail-close" type="button" data-action="close-dossier">닫기</button></div></header><div class="detail-body"><p class="detail-kicker">${escapeHtml(item.decision || "장학금")}</p><h2 id="dossierTitle">${escapeHtml(title)}</h2><p class="detail-company">${escapeHtml(organisation)}</p><div class="detail-primary">${officialLink(item.officialUrl)}</div>${overview}</div></article>`;
      return;
    }
    /* data-requirement-id="UX-220" */
    const researchPanels = graduateResearchPanels(item);
    dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${source}</small><button class="detail-close" type="button" data-action="close-dossier">닫기</button></div></header><div class="detail-body"><p class="detail-kicker">${escapeHtml(item.decision || "연구 목록")}</p><h2 id="dossierTitle">${escapeHtml(title)}</h2><p class="detail-company">${escapeHtml(organisation)}</p><div class="detail-primary">${officialLink(item.officialUrl)}</div><div class="study-detail-tabs" role="tablist" aria-label="대학원 상세 자료"><button type="button" role="tab" aria-selected="true" data-study-detail-tab="overview">개요</button><button type="button" role="tab" aria-selected="false" data-study-detail-tab="faculty">교수·논문</button><button type="button" role="tab" aria-selected="false" data-study-detail-tab="projects">연구용역</button><button type="button" role="tab" aria-selected="false" data-study-detail-tab="outcomes">졸업 후</button></div><section class="study-detail-panel" data-study-detail-panel="overview">${researchPanels.summary}${overview}${researchPanels.boundary}</section><section class="study-detail-panel" data-study-detail-panel="faculty" hidden>${researchPanels.facultyHtml}${researchPanels.boundary}</section><section class="study-detail-panel" data-study-detail-panel="projects" hidden>${researchPanels.projectHtml}${researchPanels.boundary}</section><section class="study-detail-panel" data-study-detail-panel="outcomes" hidden>${researchPanels.destinationHtml}${researchPanels.boundary}</section></div></article>`;
  }
  function openJobDetail(id, trigger) { const job = jobById(id); if (!job) return; state.selectedTrigger = trigger || null; state.activeJobId = id; renderJobDetail(job); if (!dossier.open) dossier.showModal(); requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus()); }
  function openRecordDetail(kind, id, trigger) { const item = recordById(kind, id); if (!item) return; state.selectedTrigger = trigger || null; renderRecordDetail(kind, item); if (!dossier.open) dossier.showModal(); requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus()); }
  function closeDetail(restore = true) { if (dossier.open) dossier.close(); if (restore && state.selectedTrigger?.isConnected) state.selectedTrigger.focus(); state.selectedTrigger = null; state.activeJobId = null; }

  function jobSnapshot(jobId) {
    const job = jobById(jobId);
    if (!job) return {};
    return { title: job.title, company: job.company, location: job.location, sectors: jobSectors(job), source: job.source, url: job.url };
  }
  function preferencePayload(jobId, preference) {
    return {
      user_id: state.preferenceUserId,
      job_id: jobId,
      sentiment: preference.sentiment,
      reasons: preference.reasons || [],
      note: preference.note || "",
      job_snapshot: jobSnapshot(jobId),
      updated_at: preference.updatedAt,
    };
  }
  function refreshPreferenceUI(jobId) {
    const job = jobById(jobId);
    if (dossier.open && state.activeJobId === jobId && job) renderJobDetail(job);
    else if (route() === "today") renderToday();
    else if (route() === "jobs") renderJobs();
    else if (route() === "saved") renderSaved();
    else if (route() === "sources") renderSources();
  }
  async function syncPreference(jobId, preference) {
    /* data-requirement-id="DATA-203" */
    const normalized = preference ? { ...preference, updatedAt: new Date().toISOString() } : null;
    setLocalPreference(jobId, normalized);
    refreshPreferenceUI(jobId);
    if (!state.preferenceClient || !state.preferenceUserId) {
      state.syncState = "local";
      if (route() === "sources") renderSources();
      return;
    }
    state.syncState = "syncing";
    if (route() === "sources") renderSources();
    try {
      const query = normalized
        ? state.preferenceClient.from("job_preferences").upsert(preferencePayload(jobId, normalized), { onConflict: "user_id,job_id" })
        : state.preferenceClient.from("job_preferences").delete().eq("user_id", state.preferenceUserId).eq("job_id", jobId);
      const { error } = await query;
      if (error) throw error;
      state.syncState = "synced";
    } catch (error) {
      console.warn("preference sync unavailable", error);
      state.syncState = "error";
    }
    if (route() === "sources") renderSources();
  }
  async function connectPreferences() {
    migrateLocalBookmarks();
    const config = window.CAREER_COMPASS_SUPABASE;
    if (!config?.url || !config?.publishableKey || !window.supabase?.createClient) {
      state.syncState = "local";
      return;
    }
    state.syncState = "syncing";
    try {
      state.preferenceClient = window.supabase.createClient(config.url, config.publishableKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
      });
      let { data: sessionData, error: sessionError } = await state.preferenceClient.auth.getSession();
      if (sessionError) throw sessionError;
      if (!sessionData.session?.user) {
        const anonymous = await state.preferenceClient.auth.signInAnonymously();
        if (anonymous.error) throw anonymous.error;
        sessionData = { session: anonymous.data.session };
      }
      state.preferenceUserId = sessionData.session.user.id;
      const { data: remoteRows, error: readError } = await state.preferenceClient.from("job_preferences").select("job_id,sentiment,reasons,note,updated_at");
      if (readError) throw readError;
      const remoteById = new Map((remoteRows || []).map((row) => [row.job_id, row]));
      (remoteRows || []).forEach((row) => {
        const local = preferenceFor(row.job_id);
        if (!local || Date.parse(row.updated_at) > Date.parse(local.updatedAt || 0)) {
          state.feedback[row.job_id] = { sentiment: row.sentiment, reasons: row.reasons || [], note: row.note || "", updatedAt: row.updated_at };
        }
      });
      const localRows = Object.entries(state.feedback)
        .filter(([jobId, item]) => !remoteById.has(jobId) || Date.parse(item.updatedAt || 0) > Date.parse(remoteById.get(jobId).updated_at || 0))
        .map(([jobId, item]) => preferencePayload(jobId, item));
      if (localRows.length) {
        const { error: writeError } = await state.preferenceClient.from("job_preferences").upsert(localRows, { onConflict: "user_id,job_id" });
        if (writeError) throw writeError;
      }
      persistPreferences();
      await loadCloudSnapshot();
      state.syncState = "synced";
      render(false);
    } catch (error) {
      console.warn("preference connection unavailable", error);
      state.syncState = "error";
      state.preferenceClient = null;
      state.preferenceUserId = null;
      if (route() === "sources") renderSources();
    }
  }
  function openFeedback(jobId, sentiment = "not_for_me") {
    const preference = preferenceFor(jobId);
    const config = FEEDBACK_CONFIG[sentiment] || FEEDBACK_CONFIG.not_for_me;
    const isCurrent = preference?.sentiment === sentiment;
    document.getElementById("feedbackJobId").value = jobId;
    document.getElementById("feedbackSentiment").value = sentiment;
    document.getElementById("feedbackTitle").textContent = config.title;
    document.getElementById("feedbackLegend").textContent = config.legend;
    document.getElementById("feedbackReasonChoices").innerHTML = Object.entries(config.labels).map(([value, label]) => `<label><input type="checkbox" name="reason" value="${escapeHtml(value)}" /> ${escapeHtml(label)}</label>`).join("");
    document.querySelectorAll("#feedbackReasons input[name='reason']").forEach((input) => { input.checked = isCurrent && preference.reasons?.includes(input.value); });
    const note = document.getElementById("feedbackNote");
    note.value = isCurrent ? preference.note || "" : "";
    note.placeholder = config.placeholder;
    document.getElementById("feedbackError").textContent = "";
    document.getElementById("feedbackClear").hidden = !isCurrent;
    if (dossier.open) dossier.close();
    if (!feedbackSheet.open) feedbackSheet.showModal();
    requestAnimationFrame(() => document.querySelector("#feedbackReasons input")?.focus());
  }
  function closeFeedback() { if (feedbackSheet.open) feedbackSheet.close(); }
  function buildFeedbackExport() {
    /* data-requirement-id="UX-209" */
    const likedJobs = jobs().filter((job) => preferenceFor(job.id)?.sentiment === "liked");
    const dislikedJobs = jobs().filter((job) => preferenceFor(job.id)?.sentiment === "not_for_me");
    const likedLines = likedJobs.length ? likedJobs.map((job) => {
      const preference = preferenceFor(job.id);
      const reasons = (preference.reasons || []).map((reason) => FEEDBACK_REASON_LABELS[reason] || reason).join(", ") || "이유 미기록";
      return `- ${job.company} — ${job.title}\n  좋은 이유: ${reasons}${preference.note ? `\n  메모: ${preference.note}` : ""}\n  ${job.url || "원문 주소 없음"}`;
    }).join("\n") : "- 없음";
    const dislikedLines = dislikedJobs.length ? dislikedJobs.map((job) => {
      const preference = preferenceFor(job.id);
      const reasons = (preference.reasons || []).map((reason) => FEEDBACK_REASON_LABELS[reason] || reason).join(", ") || "이유 미기록";
      return `- ${job.company} — ${job.title}\n  이유: ${reasons}${preference.note ? `\n  메모: ${preference.note}` : ""}\n  ${job.url || "원문 주소 없음"}`;
    }).join("\n") : "- 없음";
    return `Career Compass 공고 피드백\n내보낸 날짜: ${new Intl.DateTimeFormat("ko-KR", { dateStyle: "long" }).format(new Date())}\n\n관심 공고 (${likedJobs.length})\n${likedLines}\n\n별로예요 (${dislikedJobs.length})\n${dislikedLines}`;
  }
  async function exportFeedback() {
    const text = buildFeedbackExport();
    if (navigator.share) {
      try { await navigator.share({ title: "Career Compass 공고 피드백", text }); return; }
      catch (error) { if (error?.name === "AbortError") return; }
    }
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = Object.assign(document.createElement("a"), { href: url, download: `career-compass-feedback-${new Date().toISOString().slice(0, 10)}.txt` });
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function openFilters() {
    const sectorSelect = document.getElementById("sectorFilter");
    const queueSelect = document.getElementById("queueFilter");
    const sectors = allJobSectors();
    sectorSelect.innerHTML = `<option value="">전체 분야</option>${sectors.map((sector) => `<option value="${escapeHtml(sector)}">${escapeHtml(sector)}</option>`).join("")}`;
    sectorSelect.value = state.sector; queueSelect.value = state.queue;
    if (!filterSheet.open) filterSheet.showModal(); sectorSelect.focus();
  }
  function resetFilters() { state.query = ""; state.sector = ""; state.queue = ""; state.jobMarket = "all"; saveFilters(); if (route() === "jobs") renderJobs(); }
  function updateNetwork() { offlineBanner.hidden = navigator.onLine; const asOf = state.data?.stats?.jobDataAsOf; snapshotLabel.textContent = navigator.onLine ? `공고 ${sourceDate(asOf)}` : "오프라인 스냅샷"; }
  function renderError() { main.innerHTML = `<section class="loading"><span>LOAD ERROR</span><b>자료를 열 수 없어요.</b><button class="plain-button" type="button" data-action="retry">다시 시도</button></section>`; }
  function render(focus = true) { if (!state.data) return; closeDetail(false); window.scrollTo(0, 0); main.scrollTop = 0; const current = route(); setActiveTab(current); if (current === "today") renderToday(); else if (current === "jobs") renderJobs(); else if (current === "saved") renderSaved(); else if (current === "study") renderStudy(); else if (current === "sources") renderSources(); else { go("#/today"); return; } requestAnimationFrame(() => { window.scrollTo(0, 0); main.scrollTop = 0; if (focus) main.querySelector("h1")?.focus({ preventScroll: true }); }); }
  function isSnapshot(data) { return Boolean(data && Array.isArray(data.jobs) && Array.isArray(data.programs) && Array.isArray(data.funding)); }
  function normalizeFilters() {
    const sectors = new Set(allJobSectors());
    const queues = new Set(jobs().map((job) => job.queue));
    if (!sectors.has(state.sector)) state.sector = "";
    if (!queues.has(state.queue)) state.queue = "";
    if (!["all", "domestic", "overseas", "unknown"].includes(state.jobMarket)) state.jobMarket = "all";
    if (!["programs", "funding"].includes(state.studyMode)) state.studyMode = "programs";
    if (!["all", "domestic", "overseas", "unknown"].includes(state.studyMarket)) state.studyMarket = "all";
    if (!["all", "open", "prepare", "research"].includes(state.studyReadiness)) state.studyReadiness = "all";
    if (!["all", "online"].includes(state.studyFormat)) state.studyFormat = "all";
    if (typeof state.query !== "string") state.query = "";
    if (typeof state.studyQuery !== "string") state.studyQuery = "";
    saveFilters();
  }
  function setSnapshot(data, { focus = false } = {}) { if (!isSnapshot(data)) throw new Error("snapshot schema"); state.data = data; normalizeFilters(); updateNetwork(); render(focus); }
  function setEngineBusy(busy) { if (!engineRefresh) return; engineRefresh.disabled = busy; engineRefresh.toggleAttribute("aria-busy", busy); }
  class BridgeError extends Error {
    constructor(message, status = 0, payload = null) {
      super(message);
      this.name = "BridgeError";
      this.status = status;
      this.payload = payload;
    }
  }
  async function authenticatedRefreshHeaders() {
    /* data-requirement-id="DATA-204" data-requirement-id="GOV-204" */
    if (!state.preferenceClient || !state.preferenceUserId) {
      throw new BridgeError("personalized refresh requires an authenticated preference session", 401);
    }
    const { data, error } = await state.preferenceClient.auth.getSession();
    const access_token = data?.session?.access_token;
    const config = window.CAREER_COMPASS_SUPABASE;
    if (error || !access_token || !config?.publishableKey) {
      throw new BridgeError("personalized refresh requires an authenticated preference session", 401);
    }
    return {
      apikey: config.publishableKey,
      Authorization: `Bearer ${access_token}`,
      "Content-Type": "application/json",
      Prefer: "return=representation",
    };
  }
  async function authenticatedRefreshRequest(path, options = {}) {
    const config = window.CAREER_COMPASS_SUPABASE;
    if (!config?.url) throw new BridgeError("Supabase refresh endpoint unavailable");
    const response = await fetch(`${config.url}/rest/v1/${path}`, {
      cache: "no-store",
      ...options,
      headers: { ...(await authenticatedRefreshHeaders()), ...(options.headers || {}) },
    });
    if (!response.ok) {
      let payload = null;
      try { payload = await response.json(); } catch (_) { /* HTTP status remains authoritative */ }
      throw new BridgeError(payload?.message || payload?.error || `refresh queue HTTP ${response.status}`, response.status, payload);
    }
    return response.status === 204 ? null : response.json();
  }
  async function loadCloudSnapshot() {
    /* data-requirement-id="DATA-209" A clean mobile session reads only its authenticated Supabase row. */
    if (!state.preferenceClient || !state.preferenceUserId) return;
    const { data, error } = await state.preferenceClient
      .from("personalized_snapshots")
      .select("snapshot,generated_at")
      .eq("user_id", state.preferenceUserId)
      .maybeSingle();
    if (error) throw error;
    if (!isSnapshot(data?.snapshot)) return;
    const freshest = selectFreshestSnapshot(state.data, data.snapshot);
    if (freshest !== state.data) {
      store(LIVE_SNAPSHOT_STORAGE_KEY, freshest);
      setSnapshot(freshest);
    }
  }
  async function loadMatchingCompletedSnapshot(status) {
    /* data-requirement-id="DATA-211" */
    if (status?.state !== "succeeded" || !state.preferenceClient || !state.preferenceUserId) return false;
    const expectedDigest = status.preferenceSummary?.digest;
    const { data, error } = await state.preferenceClient
      .from("personalized_snapshots")
      .select("snapshot,preference_digest")
      .eq("user_id", state.preferenceUserId)
      .maybeSingle();
    if (error) throw error;
    if (!expectedDigest || data?.preference_digest !== expectedDigest || !isSnapshot(data?.snapshot)) {
      throw new BridgeError("completed snapshot does not match this refresh preference digest", 409, {
        expectedDigest,
        actualDigest: data?.preference_digest || null,
      });
    }
    const completeSnapshot = selectFreshestSnapshot(state.data, data.snapshot);
    store(LIVE_SNAPSHOT_STORAGE_KEY, completeSnapshot);
    setSnapshot(completeSnapshot);
    return true;
  }
  function refreshErrorLabel(error, status = null) {
    /* data-requirement-id="UX-213" */
    const httpStatus = error?.status || 0;
    if (httpStatus === 401 || String(error?.message).includes("authenticated preference session")) return "피드백 인증이 필요합니다";
    if (httpStatus === 403) return "이 계정은 개인 추천 엔진을 실행할 수 없습니다";
    if (httpStatus === 409) return "이번 피드백 묶음과 결과가 일치하지 않아 반영을 중단했습니다";
    const failedStage = [...(status?.stages || [])].reverse().find((stage) => stage.state === "failed");
    if (failedStage?.labelKo) return `${failedStage.labelKo} 단계 실패 · 기존 공고는 유지됩니다`;
    if (error instanceof TypeError || httpStatus === 0 || !navigator.onLine) return "Supabase 작업 큐 연결 실패 · 인터넷 연결을 확인하세요";
    return "추천 갱신 실패 · 잠시 후 다시 시도하세요";
  }
  function refreshRunStatus(row) {
    if (!row) return null;
    return {
      ...(row.status || {}),
      state: row.state,
      startedAt: row.status?.startedAt || row.started_at || row.requested_at,
      finishedAt: row.status?.finishedAt || row.finished_at,
      updatedAt: row.status?.updatedAt || row.updated_at,
    };
  }
  async function activeRefreshRun() {
    if (!state.preferenceClient || !state.preferenceUserId) return null;
    const { data, error } = await state.preferenceClient
      .from("refresh_runs")
      .select("id,state,status,requested_at,started_at,finished_at,updated_at")
      .eq("user_id", state.preferenceUserId)
      .in("state", ["pending", "running"])
      .order("requested_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) throw error;
    return data || null;
  }
  async function enqueueRefreshRun() {
    /* data-requirement-id="DATA-223" */
    if (!state.preferenceClient || !state.preferenceUserId) {
      throw new Error("personalized refresh requires an authenticated preference session");
    }
    const active = await activeRefreshRun();
    if (active) return active;
    try {
      const rows = await authenticatedRefreshRequest(
        "refresh_runs?select=id%2Cstate%2Cstatus%2Crequested_at%2Cstarted_at%2Cfinished_at%2Cupdated_at",
        { method: "POST", body: JSON.stringify({ user_id: state.preferenceUserId }) },
      );
      if (!Array.isArray(rows) || !rows[0]) throw new BridgeError("refresh queue returned no run");
      return rows[0];
    } catch (error) {
      if (error?.status !== 409 && error?.payload?.code !== "23505") throw error;
      const raced = await activeRefreshRun();
      if (raced) return raced;
      throw error;
    }
  }
  async function refreshStatus() {
    if (!state.preferenceClient || !state.preferenceUserId || !state.refreshRunId) {
      throw new Error("personalized refresh requires an authenticated preference session");
    }
    const { data, error } = await state.preferenceClient
      .from("refresh_runs")
      .select("id,state,status,requested_at,started_at,finished_at,updated_at")
      .eq("user_id", state.preferenceUserId)
      .eq("id", state.refreshRunId)
      .maybeSingle();
    if (error) throw error;
    if (!data) throw new Error("refresh run not found");
    return refreshRunStatus(data);
  }
  function stopRefreshPolling() {
    if (state.refreshTimer) window.clearTimeout(state.refreshTimer);
    if (state.refreshClockTimer) window.clearInterval(state.refreshClockTimer);
    state.refreshTimer = null;
    state.refreshClockTimer = null;
  }
  function formatRuntime(seconds) {
    const safeSeconds = Math.max(0, Math.round(seconds || 0));
    if (safeSeconds < 60) return `${safeSeconds}초`;
    const minutes = Math.floor(safeSeconds / 60);
    const remainder = safeSeconds % 60;
    return remainder ? `${minutes}분 ${remainder}초` : `${minutes}분`;
  }
  function refreshEstimate(status, now = Date.now()) {
    /* data-requirement-id="UX-218" */
    const stages = Array.isArray(status?.stages) ? status.stages : [];
    const currentStage = status?.currentStage || {};
    const startedMs = Date.parse(status?.startedAt || "");
    const finishedMs = Date.parse(status?.finishedAt || "");
    const requestStartedMs = Number(state.refreshRequestedAt);
    const completedDuringThisRequest = status?.state === "succeeded" && Number.isFinite(requestStartedMs);
    const elapsedEndMs = completedDuringThisRequest ? now : (status?.state === "succeeded" && Number.isFinite(finishedMs) ? finishedMs : now);
    const elapsedStartMs = completedDuringThisRequest ? requestStartedMs : startedMs;
    const elapsedSeconds = Number.isFinite(elapsedStartMs) ? Math.max(0, (elapsedEndMs - elapsedStartMs) / 1000) : 0;
    const stageIds = ["preference_binding", "collection_and_v3", "posting_facts", "feasibility", "sector_relevance", "preference_discovery", "review_evidence", "sector_labels", "feedback", "actions"];
    const totalSeconds = stageIds.reduce((sum, id) => sum + REFRESH_STAGE_SECONDS[id], 0);
    let usedSeconds = 0;
    stageIds.forEach((id) => {
      const recorded = stages.find((stage) => stage.id === id);
      if (recorded?.state === "succeeded") {
        usedSeconds += REFRESH_STAGE_SECONDS[id];
        return;
      }
      if (id !== currentStage.id || status?.state !== "running") return;
      const stageStartedMs = Date.parse(recorded?.startedAt || status.startedAt || "");
      const stageElapsed = Number.isFinite(stageStartedMs) ? Math.max(0, (now - stageStartedMs) / 1000) : 0;
      usedSeconds += Math.min(REFRESH_STAGE_SECONDS[id] * 0.9, stageElapsed);
    });
    if (status?.state === "succeeded") usedSeconds = totalSeconds;
    const percent = Math.max(0, Math.min(100, Math.round((usedSeconds / totalSeconds) * 100)));
    const remainingSeconds = Math.max(0, totalSeconds - usedSeconds);
    return {
      elapsedSeconds,
      percent,
      remainingLow: Math.round(remainingSeconds * 0.7),
      remainingHigh: Math.round(remainingSeconds * 1.7),
    };
  }
  function renderRefreshMonitor(status, now = Date.now()) {
    /* data-requirement-id="UX-215" data-requirement-id="DATA-208" */
    if (!refreshMonitor || !status) return;
    state.refreshRunStatus = status;
    refreshMonitor.hidden = false;
    const currentStage = status.currentStage || {};
    const summary = status.preferenceSummary || {};
    const preferenceDiscovery = status.preferenceDiscovery || {};
    const estimate = refreshEstimate(status, now);
    const isActive = status.state === "pending" || status.state === "running";
    const isSucceeded = status.state === "succeeded";
    const failedStage = [...(status.stages || [])].reverse().find((stage) => stage.state === "failed");
    const percent = isSucceeded ? 100 : estimate.percent;
    refreshMonitor.dataset.state = status.state || "unknown";
    refreshProgressTitle.textContent = isSucceeded ? "새 추천 반영 완료" : status.state === "failed" ? "추천 갱신 중단" : `추천 갱신 예상 ${percent}%`;
    refreshProgressPercent.textContent = `${percent}%`;
    refreshProgressBar.style.width = `${percent}%`;
    refreshProgressBar.parentElement.setAttribute("aria-valuenow", String(percent));
    const pendingSeconds = status.state === "pending" ? estimate.elapsedSeconds : 0;
    refreshStageLabel.textContent = isSucceeded
      ? "새 공고 검색·분류 결과를 앱에 반영했습니다."
      : status.state === "failed"
        ? `${failedStage?.labelKo || "갱신"} 단계에서 멈췄습니다. 기존 공고는 유지됩니다.`
        : status.state === "pending" && pendingSeconds >= 60
          ? "리프레시 엔진이 꺼져 있습니다 · 요청은 저장됐으며 로컬 엔진 연결을 기다립니다."
        : `${currentStage.labelKo || "갱신 준비"} · ${currentStage.position || 0}/${currentStage.total || 10}단계`;
    refreshElapsed.textContent = `경과 ${formatRuntime(estimate.elapsedSeconds)}`;
    refreshEta.textContent = isSucceeded
      ? "예상 남은 시간 0분"
      : status.state === "failed"
        ? "예상 남은 시간 없음"
        : `예상 남은 시간 ${formatRuntime(estimate.remainingLow)}~${formatRuntime(estimate.remainingHigh)}`;
    const discoveredCandidateCount = Number(preferenceDiscovery.discoveredCandidateCount || 0);
    refreshPreferenceCount.textContent = `관심 ${summary.likedCount || 0}건 · 별로예요 ${summary.dislikedCount || 0}건 전부 반영${discoveredCandidateCount ? ` · 유사 후보 ${discoveredCandidateCount}건 발견` : ""} · 예상치는 수집처 응답 속도에 따라 달라질 수 있습니다.`;
    if (isActive && !state.refreshClockTimer) {
      state.refreshClockTimer = window.setInterval(() => renderRefreshMonitor(state.refreshRunStatus), 1000);
    }
  }
  function renderRefreshConnectionFailure() {
    const previous = state.refreshRunStatus || {};
    renderRefreshMonitor({
      ...previous,
      state: "failed",
      startedAt: previous.startedAt || new Date().toISOString(),
      currentStage: { id: "status_connection", labelKo: "진행 상태 연결", position: previous.currentStage?.position || 0, total: previous.currentStage?.total || 10 },
      stages: [
        ...(previous.stages || []).filter((stage) => stage.id !== "status_connection"),
        { id: "status_connection", labelKo: "진행 상태 연결", state: "failed" },
      ],
    });
  }
  async function watchRefresh() {
    /* data-requirement-id="DATA-205" */
    let status = null;
    try {
      status = await refreshStatus();
      renderRefreshMonitor(status);
      if (status.state === "pending" || status.state === "running") {
        store(REFRESH_WATCH_STORAGE_KEY, true);
        const preferenceSummary = status.preferenceSummary || {};
        const currentStage = status.currentStage || {};
        const counts = `관심 ${preferenceSummary.likedCount || 0} · 별로예요 ${preferenceSummary.dislikedCount || 0} 반영`;
        const progress = status.state === "pending"
          ? "작업 큐에서 로컬 엔진 연결 대기"
          : currentStage.total ? `${currentStage.labelKo || "갱신 중"} ${currentStage.position}/${currentStage.total}` : "갱신 준비";
        snapshotLabel.textContent = `${counts} · ${progress}`;
        state.refreshTimer = window.setTimeout(watchRefresh, 4000);
        return;
      }
      stopRefreshPolling();
      store(REFRESH_WATCH_STORAGE_KEY, false);
      setEngineBusy(false);
      if (status.state !== "succeeded") throw new Error(`refresh state: ${status.state || "unknown"}`);
      await loadMatchingCompletedSnapshot(status);
      const summary = status.preferenceSummary || {};
      snapshotLabel.textContent = `새 추천 반영 완료 · 관심 ${summary.likedCount || 0} · 별로예요 ${summary.dislikedCount || 0}`;
    } catch (error) {
      console.error(error);
      stopRefreshPolling();
      store(REFRESH_WATCH_STORAGE_KEY, false);
      setEngineBusy(false);
      snapshotLabel.textContent = refreshErrorLabel(error, status);
      if (status) renderRefreshMonitor(status);
      else renderRefreshConnectionFailure();
    }
  }
  async function refreshEngine() {
    if (!state.preferenceClient || !state.preferenceUserId || engineRefresh?.disabled) return;
    state.refreshRequestedAt = Date.now();
    setEngineBusy(true);
    snapshotLabel.textContent = "후보 갱신 시작";
    store(REFRESH_WATCH_STORAGE_KEY, true);
    renderRefreshMonitor({
      state: "running",
      startedAt: new Date().toISOString(),
      currentStage: { id: "startup", labelKo: "갱신 준비", position: 0, total: 10 },
      stages: [],
      preferenceSummary: {
        likedCount: Object.values(state.feedback).filter((item) => item?.sentiment === "liked").length,
        dislikedCount: Object.values(state.feedback).filter((item) => item?.sentiment === "not_for_me").length,
      },
    });
    try {
      const run = await enqueueRefreshRun();
      state.refreshRunId = run.id;
      renderRefreshMonitor(refreshRunStatus(run));
      await watchRefresh();
    } catch (error) {
      console.error(error);
      stopRefreshPolling();
      store(REFRESH_WATCH_STORAGE_KEY, false);
      setEngineBusy(false);
      snapshotLabel.textContent = refreshErrorLabel(error);
      renderRefreshConnectionFailure();
    }
  }
  async function connectRefreshQueue() {
    try {
      if (!state.preferenceClient || !state.preferenceUserId) throw new Error("preference session unavailable");
      engineRefresh.hidden = false;
      engineRefresh.disabled = false;
      engineRefresh.title = "후보 추천 엔진 새로 실행";
      if (readJSON(REFRESH_WATCH_STORAGE_KEY, false) === true) {
        const active = await activeRefreshRun();
        if (active) {
          state.refreshRunId = active.id;
          setEngineBusy(true);
          await watchRefresh();
        } else {
          store(REFRESH_WATCH_STORAGE_KEY, false);
        }
      }
    } catch (error) {
      console.warn("Supabase refresh queue unavailable", error);
      engineRefresh.hidden = false;
      engineRefresh.disabled = true;
      engineRefresh.title = "개인 엔진 연결이 필요합니다";
    }
  }
  function graduateLineageMatches(snapshot) {
    /* data-requirement-id="DATA-228" */
    const lineage = snapshot?.graduateDataLineage;
    return Boolean(
      isSnapshot(snapshot)
      && lineage
      && /^[a-f0-9]{64}$/.test(String(lineage.payloadSha256 || ""))
      && lineage.programCount === snapshot.programs.length
      && lineage.fundingCount === snapshot.funding.length
    );
  }

  function mergeGraduateEvidence(primary, fallback) {
    /* data-requirement-id="DATA-226" data-requirement-id="DATA-228" */
    if (!isSnapshot(primary)) return fallback;
    if (!isSnapshot(fallback)) return primary;
    const graduateSource = graduateLineageMatches(primary)
      ? primary
      : (graduateLineageMatches(fallback) ? fallback : null);
    if (!graduateSource) return primary;
    return {
      ...primary,
      programs: graduateSource.programs,
      funding: graduateSource.funding,
      graduateEvidenceCoverage: graduateSource.graduateEvidenceCoverage,
      graduateDataLineage: graduateSource.graduateDataLineage,
    };
  }

  function selectFreshestSnapshot(bundled, cached) {
    /* data-requirement-id="DATA-207" data-requirement-id="DATA-226" data-requirement-id="DATA-228" */
    if (!isSnapshot(cached)) return bundled;
    const bundledAt = Date.parse(bundled?.generatedAt || "");
    const cachedAt = Date.parse(cached.generatedAt || "");
    const freshest = Number.isFinite(cachedAt) && (!Number.isFinite(bundledAt) || cachedAt > bundledAt) ? cached : bundled;
    const fallback = freshest === cached ? bundled : cached;
    return mergeGraduateEvidence(freshest, fallback);
  }

  async function load({ force = false } = {}) {
    try {
      const url = force ? `./data/app-data.json?refresh=${Date.now()}` : "./data/app-data.json";
      const response = await fetch(url, { cache: force ? "no-store" : "reload" });
      if (!response.ok) throw new Error(response.status);
      const bundled = await response.json();
      setSnapshot(selectFreshestSnapshot(bundled, readJSON(LIVE_SNAPSHOT_STORAGE_KEY, null)));
    } catch (error) {
      console.error(error);
      snapshotLabel.textContent = "자료를 열 수 없음";
      renderError();
    }
  }

  document.addEventListener("click", (event) => {
    const jobButton = event.target.closest("[data-open-job]"); if (jobButton) { openJobDetail(jobButton.dataset.openJob, jobButton); return; }
    const recordButton = event.target.closest("[data-open-record]"); if (recordButton) { const [kind, id] = recordButton.dataset.openRecord.split(":"); openRecordDetail(kind, id, recordButton); return; }
    const sector = event.target.closest("[data-sector]"); if (sector) { state.sector = sector.dataset.sector; saveFilters(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); return; }
    const jobMarket = event.target.closest("[data-job-market]"); if (jobMarket) { state.jobMarket = jobMarket.dataset.jobMarket; saveFilters(); renderJobs(); return; }
    const studyMode = event.target.closest("[data-study-mode]"); if (studyMode) { state.studyMode = studyMode.dataset.studyMode; saveFilters(); renderStudy(); return; }
    const studyReadiness = event.target.closest("[data-study-readiness]"); if (studyReadiness) { state.studyReadiness = studyReadiness.dataset.studyReadiness; saveFilters(); renderStudy(); return; }
    const studyMarket = event.target.closest("[data-study-market]"); if (studyMarket) { state.studyMarket = studyMarket.dataset.studyMarket; saveFilters(); renderStudy(); return; }
    const studyFormat = event.target.closest("[data-study-format]"); if (studyFormat) { state.studyFormat = studyFormat.dataset.studyFormat; saveFilters(); renderStudy(); return; }
    const studyDetailTab = event.target.closest("[data-study-detail-tab]");
    if (studyDetailTab) {
      const selected = studyDetailTab.dataset.studyDetailTab;
      dossier.querySelectorAll("[data-study-detail-tab]").forEach((tab) => tab.setAttribute("aria-selected", String(tab === studyDetailTab)));
      dossier.querySelectorAll("[data-study-detail-panel]").forEach((panel) => { panel.hidden = panel.dataset.studyDetailPanel !== selected; });
      return;
    }
    const action = event.target.closest("[data-action]")?.dataset.action; if (!action) return;
    if (action === "refresh-engine") { refreshEngine(); return; }
    if (action === "export-feedback") { void exportFeedback(); return; }
    if (action === "page-next") { movePage(event.target.closest("[data-action]"), "next"); return; }
    if (action === "page-prev") { movePage(event.target.closest("[data-action]"), "prev"); return; }
    if (action === "open-filters") openFilters();
    if (action === "clear-filters") resetFilters();
    if (action === "close-dossier") closeDetail();
    if (action === "open-feedback") {
      const trigger = event.target.closest("[data-job-id]");
      openFeedback(trigger.dataset.jobId, trigger.dataset.feedbackSentiment || "not_for_me");
      return;
    }
    if (action === "retry") load({ force: true });
  });
  document.getElementById("filterForm").addEventListener("submit", (event) => { event.preventDefault(); state.sector = document.getElementById("sectorFilter").value; state.queue = document.getElementById("queueFilter").value; saveFilters(); filterSheet.close(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); });
  document.getElementById("resetFilters").addEventListener("click", () => { resetFilters(); filterSheet.close(); });
  document.getElementById("feedbackForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const jobId = document.getElementById("feedbackJobId").value;
    const sentiment = document.getElementById("feedbackSentiment").value;
    const reasons = [...document.querySelectorAll("#feedbackReasons input[name='reason']:checked")].map((input) => input.value);
    const note = document.getElementById("feedbackNote").value.trim();
    if (!reasons.length && !note) {
      const error = document.getElementById("feedbackError");
      error.textContent = "이유를 하나 이상 선택하거나 메모를 입력해 주세요.";
      document.querySelector("#feedbackReasons input")?.focus();
      return;
    }
    closeFeedback();
    void syncPreference(jobId, { sentiment, reasons, note });
  });
  document.getElementById("feedbackClear").addEventListener("click", () => {
    const jobId = document.getElementById("feedbackJobId").value;
    closeFeedback();
    void syncPreference(jobId, null);
  });
  filterSheet.addEventListener("cancel", (event) => { event.preventDefault(); filterSheet.close(); });
  feedbackSheet.addEventListener("cancel", (event) => { event.preventDefault(); closeFeedback(); });
  feedbackSheet.addEventListener("click", (event) => { if (event.target === feedbackSheet) closeFeedback(); });
  dossier.addEventListener("cancel", (event) => { event.preventDefault(); closeDetail(); });
  dossier.addEventListener("click", (event) => { if (event.target === dossier) closeDetail(); });
  window.addEventListener("hashchange", () => render()); window.addEventListener("online", updateNetwork); window.addEventListener("offline", updateNetwork);
  if ("serviceWorker" in navigator) {
    /* data-requirement-id="GOV-215" */
    const shellReloadGuard = "career-compass-shell-reload";
    let shellReloading = false;
    if (sessionStorage.getItem(shellReloadGuard) === "pending") {
      sessionStorage.removeItem(shellReloadGuard);
    }
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (shellReloading) return;
      shellReloading = true;
      sessionStorage.setItem(shellReloadGuard, "pending");
      window.location.reload();
    });
    navigator.serviceWorker.register("./sw.js").then((registration) => registration.update()).catch(() => undefined);
  }
  void (async () => { await load(); await connectPreferences(); await connectRefreshQueue(); })();
})();
