(() => {
  "use strict";

  const FILTER_STORAGE_KEY = "career-compass-filters-v2";
  const DEFAULT_FILTERS = { query: "", sector: "", queue: "", jobMarket: "all", studyMode: "programs", studyMarket: "all", studyReadiness: "all", studyFormat: "all", studyQuery: "" };

  const state = {
    data: null,
    bridge: null,
    refreshTimer: null,
    selectedTrigger: null,
    bookmarks: new Set(readJSON("career-compass-bookmarks", [])),
    ...DEFAULT_FILTERS,
    ...readJSON(FILTER_STORAGE_KEY, {}),
  };

  const main = document.getElementById("mainContent");
  const filterSheet = document.getElementById("filterSheet");
  const dossier = document.getElementById("dossier");
  const snapshotLabel = document.getElementById("snapshotLabel");
  const offlineBanner = document.getElementById("offlineBanner");
  const engineRefresh = document.getElementById("engineRefresh");

  function readJSON(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (_) { return fallback; } }
  function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* local convenience only */ } }
  function saveFilters() { store(FILTER_STORAGE_KEY, { query: state.query, sector: state.sector, queue: state.queue, jobMarket: state.jobMarket, studyMode: state.studyMode, studyMarket: state.studyMarket, studyReadiness: state.studyReadiness, studyFormat: state.studyFormat, studyQuery: state.studyQuery }); }
  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])); }
  function icon(name) { return `<svg aria-hidden="true"><use href="#i-${name}" /></svg>`; }
  function route() { const value = (location.hash || "#/today").replace(/^#\/?/, "").split("/")[0]; return value === "trust" ? "sources" : value || "today"; }
  function go(path) { location.hash = path; }
  function sourceDate(value) { const date = value ? new Date(value) : null; return date && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat("ko-KR", { month: "long", day: "numeric" }).format(date) : "확인 시각 없음"; }
  function displayDate(value) { const date = value ? new Date(value) : null; return date && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "long", timeStyle: "short" }).format(date) : "확인 시각 없음"; }
  function jobs() { return state.data?.jobs || []; }
  function reviewQueue() { return state.data?.reviewQueue || []; }
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
  function marketSwitch(scope, active, records) {
    const selected = (value) => active === value ? "true" : "false";
    return `<div class="market-switch" role="tablist" aria-label="${scope === "job" ? "공고 근무지" : "진학 자료 지역"}"><button type="button" role="tab" aria-selected="${selected("all")}" data-${scope}-market="all">전체 <b>${records.length}</b></button><button type="button" role="tab" aria-selected="${selected("domestic")}" data-${scope}-market="domestic">국내 <b>${marketCount(records, "domestic")}</b></button><button type="button" role="tab" aria-selected="${selected("overseas")}" data-${scope}-market="overseas">해외 <b>${marketCount(records, "overseas")}</b></button></div>`;
  }

  function pageFrame(content, index, total, label) {
    return `<section class="page-frame" data-page-index="${index}" aria-label="${escapeHtml(label)} ${index + 1} / ${total}">${content}</section>`;
  }

  function filteredJobs() {
    const query = String(state.query || "").trim().toLocaleLowerCase("ko");
    return jobs().filter((job) => {
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
    const saved = state.bookmarks.has(job.id);
    return `<article class="opportunity ${compact ? "is-compact" : ""}">
      <button class="opportunity-main" type="button" data-open-job="${escapeHtml(job.id)}">
        <span class="queue-mark"><b>${queueCopy(job)}</b><small>${job.market === "overseas" ? "해외" : "국내"}</small></span>
        <span class="opportunity-copy"><em>${escapeHtml(job.company)}</em><strong>${escapeHtml(job.title)}</strong><small>${escapeHtml(job.location)}</small></span>
        <span class="opportunity-arrow">${icon("arrow")}</span>
      </button>
      <div class="opportunity-foot"><span><i class="source-dot"></i>${escapeHtml(jobSectors(job).join(" · ") || "분야 원문 확인")}</span><span>${escapeHtml(job.sectorEvidence || (job.discoveryTier === "explore" ? "분야 원문 근거" : "공식 원문 · 조건 확인"))}</span></div>
      <button class="save-dot ${saved ? "is-saved" : ""}" type="button" data-action="bookmark" data-job-id="${escapeHtml(job.id)}" aria-label="${saved ? "보관 취소" : "공고 보관"}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}</button>
    </article>`;
  }

  function renderToday() {
    const ranked = state.data?.stats?.recommendationSurface === "ranked";
    const prioritized = ranked ? reviewQueue() : [];
    const dailyCandidates = prioritized.length ? prioritized : diversifiedJobs(jobs()).slice(0, 3);
    const lead = dailyCandidates[0];
    const school = programs()[0];
    const award = funding()[0];
    const candidatePage = dailyCandidates.length ? `<section class="decision-list" aria-labelledby="priorityHeading"><div class="section-heading"><div><span>${ranked ? "개인화 추천" : "관심 탐색"}</span><h2 id="priorityHeading">오늘 열어볼 후보</h2></div><a href="#/jobs">전체 ${jobs().length}개 ${icon("arrow")}</a></div><div class="opportunity-list">${dailyCandidates.map((job) => candidateRow(job)).join("")}</div></section>` : `<section class="decision-list" aria-labelledby="inventoryHeading"><div class="section-heading"><div><span>공고 인벤토리</span><h2 id="inventoryHeading">국내 ${marketCount(jobs(), "domestic")} · 해외 ${marketCount(jobs(), "overseas")}</h2></div><a href="#/jobs">전체 ${jobs().length}개 ${icon("arrow")}</a></div></section>`;
    const researchPage = `<section class="route-callout" aria-labelledby="researchHeading"><div class="route-callout-image"><img src="./assets/study-steps-editorial-v2.webp" alt="책과 종이 계단으로 표현한 학업 경로" /></div><div class="route-callout-copy"><p class="eyebrow">02 · 진학과 장학</p><h2 id="researchHeading">과정과 장학금</h2><a class="ink-link" href="#/study">전체 보기 ${icon("arrow")}</a></div><div class="route-mini-list">${school ? `<button type="button" data-open-record="program:${escapeHtml(school.id)}"><small>${escapeHtml(school.degree)} · ${escapeHtml(programReadinessLabel(school))}</small><b>${escapeHtml(school.university)}</b><span>${escapeHtml(school.program)}</span>${icon("arrow")}</button>` : ""}${award ? `<button type="button" data-open-record="funding:${escapeHtml(award.id)}"><small>${escapeHtml(award.decision)}</small><b>${escapeHtml(award.name)}</b><span>${escapeHtml(award.coverage || "지원 범위 원문 확인")}</span>${icon("arrow")}</button>` : ""}</div></section>`;
    const pages = [
      `<section class="today-cover" aria-labelledby="todayTitle"><div class="cover-meta"><span>오늘의 목록</span><span>${escapeHtml(sourceDate(state.data.stats?.jobDataAsOf))}</span></div><div class="cover-copy"><p>공개 스냅샷</p><h1 id="todayTitle">오늘 볼 것</h1></div>${lead ? `<button class="cover-action" type="button" data-open-job="${escapeHtml(lead.id)}"><span>${ranked ? "우선 후보" : "관심 후보"}</span><b>${escapeHtml(lead.company)}<em>${escapeHtml(lead.title)}</em></b>${icon("arrow")}</button>` : `<a class="cover-action" href="#/jobs"><span>공고 목록</span><b>국내 ${marketCount(jobs(), "domestic")} · 해외 ${marketCount(jobs(), "overseas")}</b>${icon("arrow")}</a>`}</section>`,
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
    const sectors = (state.data.sectors || []).map((sector) => `<button class="sector-chip ${state.sector === sector.name ? "is-active" : ""}" type="button" data-sector="${escapeHtml(sector.name)}">${escapeHtml(sector.name)} <b>${sector.publishedJobs}</b></button>`).join("");
    const total = Math.max(1, chunks(filteredJobs(), 3).length) + 1;
    const ranked = state.data?.stats?.recommendationSurface === "ranked";
    const exploring = state.data?.stats?.recommendationSurface === "exploration_only";
    main.innerHTML = pageFrame(`<section class="browse-head"><p class="eyebrow">${ranked ? "개인화 추천" : (exploring ? "관심 탐색" : "공고 인벤토리")}</p><div class="browse-title-row"><h1>국내·해외 공고</h1><button class="filter-trigger" type="button" data-action="open-filters" aria-label="공고 필터">${icon("filter")}${activeFilters() ? `<b>${activeFilters()}</b>` : ""}</button></div><label class="search-box">${icon("search")}<span class="sr-only">공고 검색</span><input id="jobSearch" type="search" value="${escapeHtml(state.query)}" placeholder="직무, 기관, 지역으로 찾기" autocomplete="off" /></label>${marketSwitch("job", state.jobMarket || "all", jobs())}<div class="sector-scroll"><button class="sector-chip ${!state.sector ? "is-active" : ""}" type="button" data-sector="">전체</button>${sectors}</div></section>`, 0, total, "공고 탐색") + `<div id="jobResults"></div>`;
    document.getElementById("jobSearch").addEventListener("input", (event) => { state.query = event.target.value; saveFilters(); renderJobResults(); });
    renderJobResults();
  }

  function studyRow(item, kind) {
    const isProgram = kind === "program";
    const number = "•";
    const line = isProgram ? `${programReadinessLabel(item)} · ${item.degree || "과정"}${item.deliveryMode === "online" ? " · 온라인" : ""} · ${item.country || "국가 원문 확인"}` : `${item.decision || "장학금"} · ${(item.countries || []).join(", ") || "지역 원문 확인"}`;
    const title = isProgram ? item.program : item.name;
    const subtitle = isProgram ? item.university : item.coverage || item.type;
    const note = isProgram ? item.funding || item.deadline || "마감 원문 확인" : item.deadline || item.verification || "조건 원문 확인";
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
    const openPrograms = programs().filter((item) => programReadiness(item) === "open").length;
    const preparePrograms = programs().filter((item) => programReadiness(item) === "prepare").length;
    const onlinePrograms = programs().filter((item) => item.deliveryMode === "online").length;
    const readinessSwitch = isFunding ? "" : `<div class="market-switch study-readiness" role="tablist" aria-label="대학원 지원 상태"><button type="button" role="tab" aria-selected="${state.studyReadiness === "all"}" data-study-readiness="all">전체 <b>${programs().length}</b></button><button type="button" role="tab" aria-selected="${state.studyReadiness === "open"}" data-study-readiness="open">지원 열림 <b>${openPrograms}</b></button><button type="button" role="tab" aria-selected="${state.studyReadiness === "prepare"}" data-study-readiness="prepare">지금 준비 <b>${preparePrograms}</b></button></div><p class="study-status-note">‘지원 열림’은 현재 공식 원문으로 접수 상태가 확인된 항목만 표시합니다.</p>`;
    const formatSwitch = isFunding ? "" : `<div class="market-switch study-format" role="tablist" aria-label="대학원 수강 방식"><button type="button" role="tab" aria-selected="${state.studyFormat === "all"}" data-study-format="all">전체 <b>${programs().length}</b></button><button type="button" role="tab" aria-selected="${state.studyFormat === "online"}" data-study-format="online">온라인 <b>${onlinePrograms}</b></button></div>`;
    main.innerHTML = pageFrame(`<section class="study-head"><div><p class="eyebrow">진학 · 장학 · 연구</p><h1>대학원 · 장학금</h1></div><p>대학원 ${programs().length} · 온라인 ${onlinePrograms} · 장학금 ${funding().length}</p></section><section class="study-controls"><div class="mode-switch" role="tablist" aria-label="진학 자료 종류"><button type="button" role="tab" aria-selected="${!isFunding}" data-study-mode="programs">대학원 <b>${programs().length}</b></button><button type="button" role="tab" aria-selected="${isFunding}" data-study-mode="funding">장학금 <b>${funding().length}</b></button></div>${readinessSwitch}${formatSwitch}${marketSwitch("study", state.studyMarket || "all", studyRecords)}<label class="search-box">${icon("search")}<span class="sr-only">진학 자료 검색</span><input id="studySearch" type="search" value="${escapeHtml(state.studyQuery)}" placeholder="학교, 과정, 장학금으로 찾기" autocomplete="off" /></label></section>`, 0, total, "진학과 재정") + `<div id="studyResults"></div>`;
    document.getElementById("studySearch").addEventListener("input", (event) => { state.studyQuery = event.target.value; saveFilters(); renderStudyResults(); });
    renderStudyResults();
  }

  function renderSources() {
    const stats = state.data.stats || {};
    const pages = [
      `<section class="sources-head"><p class="eyebrow">자료의 범위</p><h1>무엇을 담고,<br />어디까지 아는가.</h1><p>${escapeHtml(state.data.snapshotBoundary)}</p></section>`,
      `<section class="source-stamp"><span>PUBLIC SNAPSHOT</span><b>${displayDate(state.data.generatedAt)}</b><i>V4<br />FIRST</i></section><section class="stat-strip"><div><small>${stats.recommendationSurface === "exploration_only" ? "관심 후보" : "행동 후보"}</small><b>${escapeHtml(stats.actionCandidates)}</b></div><div><small>대학원</small><b>${escapeHtml(stats.programs)}</b></div><div><small>장학금</small><b>${escapeHtml(stats.funding)}</b></div></section>`,
      `<section class="source-explainer"><p class="eyebrow">검증 경계</p><h2>점수로 결론을 대신하지 않습니다.</h2><p>공고는 최신 V4 행동 큐를, 진학·재정은 현재 대시보드의 연구 목록을 사용합니다. 공개 화면에는 개인 프로필, 지원 이력, CRM 정보가 포함되지 않습니다.</p><div class="status-rows"><div><span>V4 실행 ID</span><b>${escapeHtml(stats.v4RunId || "확인 중")}</b></div><div><span>공고 기준일</span><b>${escapeHtml(stats.jobDataAsOf || "확인 중")}</b></div><div><span>대학원 자료 생성</span><b>${escapeHtml(stats.graduateGeneratedAt || "확인 중")}</b></div></div></section>`,
    ];
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "자료")).join("");
  }

  function detailList(title, values) { return values?.length ? `<section class="detail-list"><small>${escapeHtml(title)}</small><ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>` : ""; }
  function officialLink(url) { return url ? `<a class="official-button" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">공식 원문 열기 ${icon("external")}</a>` : `<span class="official-button is-disabled">공식 원문 주소 없음</span>`; }
  function renderJobDetail(job) {
    const saved = state.bookmarks.has(job.id);
    const discovery = job.discoveryTier === "explore";
    dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${escapeHtml(job.source)} · ${queueCopy(job)}</small><button type="button" data-action="close-dossier" aria-label="상세 닫기">${icon("close")}</button></div></header><div class="detail-body"><p class="detail-kicker">${escapeHtml(jobSectors(job).join(" · ") || "분야 원문 확인")}</p><h2 id="dossierTitle">${escapeHtml(job.title)}</h2><p class="detail-company">${escapeHtml(job.company)} · ${escapeHtml(job.location)}</p><div class="detail-primary">${officialLink(job.url)}</div><div class="detail-facts"><div><small>${discovery ? "분류" : "행동 상태"}</small><b>${queueCopy(job)}</b></div><div><small>마감</small><b>${escapeHtml(job.deadline || "원문 확인")}</b></div><div><small>증거 공백</small><b>${job.evidenceGapCount ?? "원문 확인"}</b></div><div><small>확인 부담</small><b>${escapeHtml(job.evidenceBurden || "원문 확인")}</b></div></div>${discovery ? `<section class="check-note"><small>보여드린 이유</small><p>${escapeHtml(job.discoveryReason)}</p></section>` : ""}<section class="check-note"><small>${discovery ? "원문에서 먼저 볼 것" : "다음 행동"}</small><p>${escapeHtml(job.nextAction)}</p></section>${detailList("공고에서 확인된 조건", job.requirements)}${detailList("추가 확인 항목", job.checks)}${detailList("주의 사항", job.risks)}<div class="detail-actions"><button class="detail-save ${saved ? "is-saved" : ""}" type="button" data-action="bookmark" data-job-id="${escapeHtml(job.id)}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}${saved ? "보관함에 있음" : "나중에 보기"}</button></div></div></article>`;
  }
  function renderRecordDetail(kind, item) {
    const isProgram = kind === "program";
    const title = isProgram ? item.program : item.name;
    const organisation = isProgram ? item.university : item.coverage || item.type;
    const source = isProgram ? "대학원 연구" : "장학금 연구";
    const facts = isProgram ? [["지원 상태", programReadinessLabel(item)], ["국가", item.country], ["과정", item.degree], ["마감", item.deadline], ["검증", item.verification]] : [["지원 범위", item.coverage], ["대상 국가", (item.countries || []).join(", ")], ["마감", item.deadline], ["검증", item.verification]];
    const extra = isProgram ? [["분류 근거", item.applicationStatusReason], ["재정", item.funding], ["영어", item.english], ["확인일", item.verifiedAt]] : [["선발 가능성", item.likelihood], ["유형", item.type]];
    dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${source}</small><button type="button" data-action="close-dossier" aria-label="상세 닫기">${icon("close")}</button></div></header><div class="detail-body"><p class="detail-kicker">${escapeHtml(item.decision || (isProgram ? "연구 목록" : "장학금"))}</p><h2 id="dossierTitle">${escapeHtml(title)}</h2><p class="detail-company">${escapeHtml(organisation)}</p><div class="detail-primary">${officialLink(item.officialUrl)}</div><div class="detail-facts">${facts.map(([label, value]) => `<div><small>${escapeHtml(label)}</small><b>${escapeHtml(value || "원문 확인")}</b></div>`).join("")}</div>${extra.filter(([, value]) => value).map(([label, value]) => `<section class="check-note"><small>${escapeHtml(label)}</small><p>${escapeHtml(value)}</p></section>`).join("")}${isProgram ? detailList(item.englishStatus || "영어 공식 기준", item.englishCriteria) : ""}${isProgram ? detailList("영어 준비", item.englishGapPlan) : ""}${detailList("지원 전 확인할 조건", item.gates)}${detailList("주의 사항", item.risks)}</div></article>`;
  }
  function openJobDetail(id, trigger) { const job = jobById(id); if (!job) return; state.selectedTrigger = trigger || null; renderJobDetail(job); if (!dossier.open) dossier.showModal(); requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus()); }
  function openRecordDetail(kind, id, trigger) { const item = recordById(kind, id); if (!item) return; state.selectedTrigger = trigger || null; renderRecordDetail(kind, item); if (!dossier.open) dossier.showModal(); requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus()); }
  function closeDetail(restore = true) { if (dossier.open) dossier.close(); if (restore && state.selectedTrigger?.isConnected) state.selectedTrigger.focus(); state.selectedTrigger = null; }

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
  function render(focus = true) { if (!state.data) return; closeDetail(false); window.scrollTo(0, 0); main.scrollTop = 0; const current = route(); setActiveTab(current); if (current === "today") renderToday(); else if (current === "jobs") renderJobs(); else if (current === "study") renderStudy(); else if (current === "sources") renderSources(); else { go("#/today"); return; } requestAnimationFrame(() => { window.scrollTo(0, 0); main.scrollTop = 0; if (focus) main.querySelector("h1")?.focus({ preventScroll: true }); }); }
  function isSnapshot(data) { return Boolean(data && Array.isArray(data.jobs) && Array.isArray(data.programs) && Array.isArray(data.funding)); }
  function normalizeFilters() {
    const sectors = new Set(allJobSectors());
    const queues = new Set(jobs().map((job) => job.queue));
    if (!sectors.has(state.sector)) state.sector = "";
    if (!queues.has(state.queue)) state.queue = "";
    if (!["all", "domestic", "overseas"].includes(state.jobMarket)) state.jobMarket = "all";
    if (!["programs", "funding"].includes(state.studyMode)) state.studyMode = "programs";
    if (!["all", "domestic", "overseas"].includes(state.studyMarket)) state.studyMarket = "all";
    if (!["all", "open", "prepare", "research"].includes(state.studyReadiness)) state.studyReadiness = "all";
    if (!["all", "online"].includes(state.studyFormat)) state.studyFormat = "all";
    if (typeof state.query !== "string") state.query = "";
    if (typeof state.studyQuery !== "string") state.studyQuery = "";
    saveFilters();
  }
  function setSnapshot(data, { focus = false } = {}) { if (!isSnapshot(data)) throw new Error("snapshot schema"); state.data = data; normalizeFilters(); updateNetwork(); render(focus); }
  function setEngineBusy(busy) { if (!engineRefresh) return; engineRefresh.disabled = busy; engineRefresh.toggleAttribute("aria-busy", busy); }
  function bridgeUrl(path) { return new URL(path, `${state.bridge.baseUrl}/`).toString(); }
  async function bridgeRequest(path, options = {}) {
    if (!state.bridge) throw new Error("bridge unavailable");
    const response = await fetch(bridgeUrl(path), { cache: "no-store", ...options });
    if (!response.ok) throw new Error(`bridge HTTP ${response.status}`);
    return response;
  }
  async function refreshStatus() { return (await bridgeRequest("api/jobs/refresh")).json(); }
  function stopRefreshPolling() { if (state.refreshTimer) window.clearTimeout(state.refreshTimer); state.refreshTimer = null; }
  async function loadLiveSnapshot() {
    const response = await bridgeRequest("api/jobs/public-snapshot");
    setSnapshot(await response.json());
  }
  async function watchRefresh() {
    try {
      const status = await refreshStatus();
      if (status.state === "running") {
        const completed = Array.isArray(status.stages) ? status.stages.filter((stage) => stage.state === "succeeded").length : 0;
        const total = Array.isArray(status.stages) ? status.stages.length : 0;
        snapshotLabel.textContent = total ? `후보 갱신 ${completed}/${total}` : "후보 갱신 중";
        state.refreshTimer = window.setTimeout(watchRefresh, 4000);
        return;
      }
      stopRefreshPolling();
      setEngineBusy(false);
      if (status.state !== "succeeded") throw new Error(`refresh state: ${status.state || "unknown"}`);
      await loadLiveSnapshot();
    } catch (error) {
      console.error(error);
      stopRefreshPolling();
      setEngineBusy(false);
      snapshotLabel.textContent = "엔진 연결 확인 필요";
    }
  }
  async function refreshEngine() {
    if (!state.bridge || engineRefresh?.disabled) return;
    setEngineBusy(true);
    snapshotLabel.textContent = "후보 갱신 시작";
    try {
      const status = await refreshStatus();
      if (status.state !== "running") await bridgeRequest("api/jobs/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      await watchRefresh();
    } catch (error) {
      console.error(error);
      setEngineBusy(false);
      snapshotLabel.textContent = "엔진 연결 확인 필요";
    }
  }
  async function connectBridge() {
    try {
      const response = await fetch(`./data/refresh-bridge.json?at=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) return;
      const config = await response.json();
      if (config?.enabled !== true || typeof config.baseUrl !== "string") return;
      const url = new URL(config.baseUrl);
      if (url.protocol !== "https:" || url.pathname !== "/" || url.search || url.hash) throw new Error("invalid bridge url");
      state.bridge = { baseUrl: url.origin };
      engineRefresh.hidden = false;
      engineRefresh.disabled = false;
      engineRefresh.title = "후보 추천 엔진 새로 실행";
      const status = await refreshStatus();
      if (status.state === "running") { setEngineBusy(true); await watchRefresh(); }
      else await loadLiveSnapshot();
    } catch (error) {
      console.warn("live refresh bridge unavailable", error);
      state.bridge = null;
      engineRefresh.hidden = false;
      engineRefresh.disabled = true;
      engineRefresh.title = "개인 엔진 연결이 필요합니다";
    }
  }
  async function load({ force = false } = {}) { try { const url = force ? `./data/app-data.json?refresh=${Date.now()}` : "./data/app-data.json"; const response = await fetch(url, { cache: force ? "no-store" : "reload" }); if (!response.ok) throw new Error(response.status); setSnapshot(await response.json()); } catch (error) { console.error(error); snapshotLabel.textContent = "자료를 열 수 없음"; renderError(); } }

  document.addEventListener("click", (event) => {
    const jobButton = event.target.closest("[data-open-job]"); if (jobButton) { openJobDetail(jobButton.dataset.openJob, jobButton); return; }
    const recordButton = event.target.closest("[data-open-record]"); if (recordButton) { const [kind, id] = recordButton.dataset.openRecord.split(":"); openRecordDetail(kind, id, recordButton); return; }
    const sector = event.target.closest("[data-sector]"); if (sector) { state.sector = sector.dataset.sector; saveFilters(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); return; }
    const jobMarket = event.target.closest("[data-job-market]"); if (jobMarket) { state.jobMarket = jobMarket.dataset.jobMarket; saveFilters(); renderJobs(); return; }
    const studyMode = event.target.closest("[data-study-mode]"); if (studyMode) { state.studyMode = studyMode.dataset.studyMode; saveFilters(); renderStudy(); return; }
    const studyReadiness = event.target.closest("[data-study-readiness]"); if (studyReadiness) { state.studyReadiness = studyReadiness.dataset.studyReadiness; saveFilters(); renderStudy(); return; }
    const studyMarket = event.target.closest("[data-study-market]"); if (studyMarket) { state.studyMarket = studyMarket.dataset.studyMarket; saveFilters(); renderStudy(); return; }
    const studyFormat = event.target.closest("[data-study-format]"); if (studyFormat) { state.studyFormat = studyFormat.dataset.studyFormat; saveFilters(); renderStudy(); return; }
    const action = event.target.closest("[data-action]")?.dataset.action; if (!action) return;
    if (action === "refresh-engine") { refreshEngine(); return; }
    if (action === "open-filters") openFilters();
    if (action === "clear-filters") resetFilters();
    if (action === "close-dossier") closeDetail();
    if (action === "bookmark") { const id = event.target.closest("[data-job-id]").dataset.jobId; if (state.bookmarks.has(id)) state.bookmarks.delete(id); else state.bookmarks.add(id); store("career-compass-bookmarks", [...state.bookmarks]); const job = jobById(id); if (job && dossier.open) renderJobDetail(job); else if (route() === "jobs") renderJobResults(); }
    if (action === "retry") load({ force: true });
  });
  document.getElementById("filterForm").addEventListener("submit", (event) => { event.preventDefault(); state.sector = document.getElementById("sectorFilter").value; state.queue = document.getElementById("queueFilter").value; saveFilters(); filterSheet.close(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); });
  document.getElementById("resetFilters").addEventListener("click", () => { resetFilters(); filterSheet.close(); });
  filterSheet.addEventListener("cancel", (event) => { event.preventDefault(); filterSheet.close(); });
  dossier.addEventListener("cancel", (event) => { event.preventDefault(); closeDetail(); });
  dossier.addEventListener("click", (event) => { if (event.target === dossier) closeDetail(); });
  window.addEventListener("hashchange", () => render()); window.addEventListener("online", updateNetwork); window.addEventListener("offline", updateNetwork);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").then((registration) => registration.update()).catch(() => undefined);
  void (async () => { await load(); await connectBridge(); })();
})();
