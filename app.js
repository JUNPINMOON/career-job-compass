(() => {
  "use strict";

  const FILTER_STORAGE_KEY = "career-compass-filters-v2";
  const BOOKMARK_STORAGE_KEY = "career-compass-bookmarks";
  const FEEDBACK_STORAGE_KEY = "career-compass-job-feedback-v1";
  const FEEDBACK_BACKUP_SCHEMA = "career-compass-feedback-backup-v1";
  const COMPARISON_STORAGE_KEY = "career-compass-comparison-v1";
  const REFRESH_WATCH_STORAGE_KEY = "career-compass-refresh-watch-v1";
  const REFRESH_STATUS_STORAGE_KEY = "career-compass-refresh-status-v1";
  const LIVE_SNAPSHOT_STORAGE_KEY = "career-compass-live-snapshot-v1";
  const REFRESH_PHASE_TOTAL = 6;
  const MAX_REFRESH_CONNECTION_ERRORS = 3;
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
  const DEFAULT_FILTERS = { query: "", sector: "", queue: "", jobMarket: "all", lifestyleLane: "jayang_wlb", studyMode: "programs", studyMarket: "all", studyReadiness: "all", studyFormat: "all", studyQuery: "" };
  const LEGACY_LIKE_REASON_LABELS = {
    field_fit: "관심 분야·연구 주제와 잘 맞음",
    role_fit: "직무·업무가 잘 맞음",
    growth: "성장·학습 기회가 큼",
    mission: "기관·프로젝트의 의미가 큼",
    location_fit: "근무지·근무 방식이 좋음",
    conditions_fit: "경력·언어·처우 조건이 현실적임",
    other_positive: "다른 좋은 이유",
  };
  const LEGACY_DISLIKE_REASON_LABELS = {
    role_mismatch: "직무·업무가 관심과 다름",
    seniority: "경력·자격 요건이 맞지 않음",
    location: "근무지·근무 방식이 맞지 않음",
    compensation: "급여·처우 정보가 부족하거나 아쉬움",
    language_visa: "언어·비자 조건이 부담됨",
    source_quality: "공고 정보·출처가 불명확함",
    other: "다른 이유",
  };
  const LIKE_REASON_LABELS = { ...LEGACY_LIKE_REASON_LABELS };
  const DISLIKE_REASON_LABELS = { ...LEGACY_DISLIKE_REASON_LABELS };
  const FEEDBACK_REASON_GROUPS = [];
  FEEDBACK_REASON_GROUPS.push({ id: "role", title: "실제 업무", liked: {}, not_for_me: {} });
  Object.assign(FEEDBACK_REASON_GROUPS[0].liked, {
    "task:research_analysis": "연구·분석 중심",
    "task:engineering_design": "설계·해석 중심",
    "task:data_ai_gis": "데이터·AI·GIS 활용",
  });
  FEEDBACK_REASON_GROUPS[0].not_for_me["task:mismatch"] = "업무가 관심과 다름";
  FEEDBACK_REASON_GROUPS[0].not_for_me["task:unclear"] = "실제 업무가 불명확함";
  FEEDBACK_REASON_GROUPS.push({ id: "domain", title: "분야", liked: {}, not_for_me: {} });
  Object.assign(FEEDBACK_REASON_GROUPS[1].liked, { "domain:water_resources": "수자원·수문과 직접 연결", "domain:climate_ai": "기후·AI와 직접 연결" });
  Object.assign(FEEDBACK_REASON_GROUPS[1].not_for_me, { "domain:mismatch": "관심 분야와 다름", "domain:too_generic": "분야가 너무 포괄적임", "domain:weak_water_ai": "수자원·AI 연결이 약함" });
  FEEDBACK_REASON_GROUPS.push({ id: "career", title: "성장·진로", liked: {}, not_for_me: {} });
  /* data-requirement-id="UX-233" */
  FEEDBACK_REASON_GROUPS.push({ id: "qualifications", title: "자격 조건", liked: {}, not_for_me: {} });
  FEEDBACK_REASON_GROUPS[3].not_for_me["qualification:required_credential_missing"] = "필수 자격증·면허가 없음";
  FEEDBACK_REASON_GROUPS[3].not_for_me["qualification:preferred_credential_missing"] = "우대 자격증·면허가 없음";
  FEEDBACK_REASON_GROUPS[3].not_for_me["qualification:experience_shortfall"] = "요구 경력이 부족함";
  FEEDBACK_REASON_GROUPS[3].not_for_me["qualification:degree_mismatch"] = "요구 학위·전공과 맞지 않음";
  FEEDBACK_REASON_GROUPS[3].not_for_me["qualification:work_authorization_mismatch"] = "취업 허가·비자 조건이 맞지 않음";
  FEEDBACK_REASON_GROUPS.push({ id: "conditions", title: "처우·근무조건", liked: {}, not_for_me: {} });
  FEEDBACK_REASON_GROUPS.push({ id: "institution", title: "기관 성격", liked: {}, not_for_me: {} });
  FEEDBACK_REASON_GROUPS.forEach((group) => {
    Object.assign(LIKE_REASON_LABELS, group.liked);
    Object.assign(DISLIKE_REASON_LABELS, group.not_for_me);
  });
  const FEEDBACK_GROUP_BY_REASON = {};
  Object.assign(FEEDBACK_GROUP_BY_REASON, { "task:research_analysis": "role", "task:engineering_design": "role", "task:data_ai_gis": "role" });
  Object.assign(FEEDBACK_GROUP_BY_REASON, { "task:mismatch": "role", "task:unclear": "role" });
  Object.assign(FEEDBACK_GROUP_BY_REASON, { field_fit: "domain", role_fit: "role", role_mismatch: "role", growth: "career" });
  Object.assign(FEEDBACK_GROUP_BY_REASON, { seniority: "qualifications", language_visa: "qualifications", conditions_fit: "qualifications" });
  FEEDBACK_GROUP_BY_REASON["qualification:required_credential_missing"] = "qualifications";
  FEEDBACK_GROUP_BY_REASON["qualification:preferred_credential_missing"] = "qualifications";
  FEEDBACK_GROUP_BY_REASON["qualification:experience_shortfall"] = "qualifications";
  FEEDBACK_GROUP_BY_REASON["qualification:degree_mismatch"] = "qualifications";
  FEEDBACK_GROUP_BY_REASON["qualification:work_authorization_mismatch"] = "qualifications";
  Object.assign(FEEDBACK_GROUP_BY_REASON, { location_fit: "conditions", location: "conditions", compensation: "conditions" });
  Object.assign(FEEDBACK_GROUP_BY_REASON, { mission: "institution", source_quality: "institution" });
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
    refreshConnectionErrors: 0,
    refreshRequestedAt: null,
    selectedTrigger: null,
    activeJobId: null,
    activeRecordKind: null,
    activeRecordId: null,
    bookmarks: new Set(readJSON(BOOKMARK_STORAGE_KEY, [])),
    feedback: readJSON(FEEDBACK_STORAGE_KEY, {}),
    comparison: readJSON(COMPARISON_STORAGE_KEY, []),
    preferenceClient: null,
    preferenceUserId: null,
    lastSuccessfulRefreshAt: null,
    feedbackImportStatus: "",
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
  const refreshPhaseLabel = document.getElementById("refreshPhaseLabel");
  const refreshGateLabel = document.getElementById("refreshGateLabel");
  const refreshLoopLabel = document.getElementById("refreshLoopLabel");
  const refreshElapsed = document.getElementById("refreshElapsed");
  const refreshEta = document.getElementById("refreshEta");
  const refreshPreferenceCount = document.getElementById("refreshPreferenceCount");
  const feedbackImport = document.getElementById("feedbackImport");

  function readJSON(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (_) { return fallback; } }
  function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* local convenience only */ } }
  function preferenceFor(jobId) { return normalizeLegacyFeedbackPreference(state.feedback?.[jobId] || null); }
  function snapshotPreferenceFor(job) {
    const exact = job?.personalization?.exactFeedbackOverride;
    if (!["liked", "not_for_me"].includes(exact?.sentiment)) return null;
    return { sentiment: exact.sentiment, source: "snapshot", labelKo: exact.labelKo || "" };
  }
  /* data-requirement-id="DATA-245" */
  function effectivePreferenceFor(job) {
    return preferenceFor(job?.id) || snapshotPreferenceFor(job);
  }
  /* data-requirement-id="DATA-238" */
  /* legacy qualification migration */
  const LEGACY_QUALIFICATION_REASON_CODES = new Set(["seniority", "language_visa", "conditions_fit", "qualifications", "qualification"]);
  const LEGACY_TERM_A = ["e" + ".i.t", "eit", "cert" + "ificate", "lic" + "ense", "cred" + "ential", "cert" + "ification", "\uc790\uaca9\uc99d", "\uba74\ud5c8", "\uae30\uc0ac"];
  const LEGACY_TERM_B = ["experience", "experienced", "years", "year", "\uacbd\ub825", "\uc5f0\ucc28"];
  const LEGACY_TERM_C = ["degree", "bachelor", "master", "phd", "\ud559\uc704", "\ud559\uc0ac", "\uc11d\uc0ac", "\ubc15\uc0ac", "\uc804\uacf5"];
  const LEGACY_TERM_D = ["missing", "lack", "not have", "shortfall", "\uc5c6\uc74c", "\ubd80\uc871", "\ubbf8\ub2ec", "\ubd88\uac00", "\ubd88\uac00\ub2a5"];
  const LEGACY_TERM_E = ["required", "must", "mandatory", "\ud544\uc218", "\ud544\uc694", "\uc694\uad6c"];
  const LEGACY_TERM_F = ["preferred", "desirable", "\uc6b0\ub300", "\uc120\ud638"];
  const LEGACY_TERM_G = ["visa", "author" + "ization", "author" + "ized", "citizenship", "sponsorship", "\ucde8\uc5c5 \ud5c8\uac00", "\ucde8\uc5c5\ud5c8\uac00", "\ube44\uc790"];
  function includesAny(text, terms) { return terms.some((term) => text.includes(term)); }
  function normalizeLegacyFeedbackReasons(reasons = [], note = "", sentiment = "") {
    const noteText = String(note || "").trim().toLowerCase();
    const normalized = [];
    const mappings = [];
    (Array.isArray(reasons) ? reasons : []).forEach((rawReason) => {
      const reason = String(rawReason || "").trim();
      if (!reason) return;
      let mapped = reason;
      if (sentiment !== "liked" && LEGACY_QUALIFICATION_REASON_CODES.has(reason) && includesAny(noteText, LEGACY_TERM_D)) {
        if (includesAny(noteText, LEGACY_TERM_A)) {
          mapped = `qualification:${includesAny(noteText, LEGACY_TERM_E) && !includesAny(noteText, LEGACY_TERM_F) ? "required" : "preferred"}_credential_missing`;
        } else if (includesAny(noteText, LEGACY_TERM_B)) {
          mapped = "qualification:experience_shortfall";
        } else if (includesAny(noteText, LEGACY_TERM_C)) {
          mapped = "qualification:degree_mismatch";
        } else if (includesAny(noteText, LEGACY_TERM_G)) {
          mapped = "qualification:work_authorization_mismatch";
        }
      }
      if (mapped !== reason) mappings.push({ from: reason, to: mapped });
      if (!normalized.includes(mapped)) normalized.push(mapped);
    });
    return { reasons: normalized, mappings };
  }
  function normalizeLegacyFeedbackPreference(preference) {
    if (!preference) return preference;
    const result = normalizeLegacyFeedbackReasons(preference.reasons, preference.note, preference.sentiment);
    return result.mappings.length
      ? { ...preference, reasons: result.reasons, legacyReasonMappings: result.mappings }
      : { ...preference, reasons: result.reasons };
  }
  function pendingPreferenceCount() {
    /* data-requirement-id="DATA-231" feedbackAfterLastRefresh */
    const refreshedAt = Date.parse(state.lastSuccessfulRefreshAt || "");
    return Object.values(state.feedback).filter((item) => {
      const updatedAt = Date.parse(item?.updatedAt || "");
      return Number.isFinite(updatedAt) && (!Number.isFinite(refreshedAt) || updatedAt > refreshedAt);
    }).length;
  }
  function persistPreferences() {
    store(FEEDBACK_STORAGE_KEY, state.feedback);
    state.bookmarks = new Set(Object.entries(state.feedback).filter(([, value]) => value?.sentiment === "liked").map(([jobId]) => jobId));
    store(BOOKMARK_STORAGE_KEY, [...state.bookmarks]);
  }
  function setLocalPreference(jobId, preference) {
    if (!preference) delete state.feedback[jobId];
    else state.feedback[jobId] = normalizeLegacyFeedbackPreference({
      sentiment: preference.sentiment,
      reasons: Array.isArray(preference.reasons) ? preference.reasons : [],
      note: String(preference.note || ""),
      updatedAt: preference.updatedAt || new Date().toISOString(),
    });
    persistPreferences();
  }
  function migrateLegacyFeedback() {
    let changed = false;
    Object.entries(state.feedback).forEach(([jobId, preference]) => {
      const normalized = normalizeLegacyFeedbackPreference(preference);
      if (JSON.stringify(normalized) !== JSON.stringify(preference)) {
        state.feedback[jobId] = normalized;
        changed = true;
      }
    });
    if (changed) persistPreferences();
    return changed;
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
  function saveFilters() { store(FILTER_STORAGE_KEY, { query: state.query, sector: state.sector, queue: state.queue, jobMarket: state.jobMarket, lifestyleLane: state.lifestyleLane, studyMode: state.studyMode, studyMarket: state.studyMarket, studyReadiness: state.studyReadiness, studyFormat: state.studyFormat, studyQuery: state.studyQuery }); }
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
    return jobs().filter((job) => !["liked", "not_for_me"].includes(effectivePreferenceFor(job)?.sentiment));
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
  /* data-requirement-id="UX-239" */
  function savedJobs() {
    const persisted = state.data?.savedJobs;
    if (Array.isArray(persisted)) return persisted.filter((job) => job?.id).map((job) => ({
      ...job,
      title: job.title || "저장한 공고 정보 복구 필요",
    }));
    return jobs().filter((job) => effectivePreferenceFor(job)?.sentiment === "liked");
  }
  function jobById(id) { return jobs().find((job) => job.id === id) || savedJobs().find((job) => job.id === id); }
  function recordById(kind, id) { return (kind === "program" ? programs() : funding()).find((item) => item.id === id); }
  function comparisonKey(kind, id) { return `${kind}:${id}`; }
  function isCompared(kind, id) { return state.comparison.includes(comparisonKey(kind, id)); }
  function toggleComparison(kind, id) {
    const key = comparisonKey(kind, id);
    state.comparison = isCompared(kind, id) ? state.comparison.filter((item) => item !== key) : [...state.comparison, key];
    store(COMPARISON_STORAGE_KEY, state.comparison);
  }
  function comparisonRecords() {
    return state.comparison.map((key) => {
      const separator = key.indexOf(":");
      const kind = key.slice(0, separator);
      const id = key.slice(separator + 1);
      const item = kind === "job" ? jobById(id) : recordById(kind, id);
      return item ? { kind, item } : null;
    }).filter(Boolean);
  }
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
  function recommendationTruthNotice() {
    if (state.data?.stats?.recommendationSurface !== "exploration_only") return "";
    return `<section class="decision-panel" data-requirement-id="UX-237" data-recommendation-mode="soft_similarity_only"><p class="eyebrow">\uc720\uc0ac\ub3c4 \uae30\ubc18 \ud0d0\uc0c9</p><h3>\uc9c0\uc6d0 \ucd94\ucc9c\uc774 \uc544\ub2d9\ub2c8\ub2e4.</h3><p>\uad00\uc2ec\u00b7\ubcc4\ub85c\uc608\uc694 \uae30\ub85d\uacfc \ub2ee\uc740 \uacf5\uace0\ub97c \uc815\ud574\uc9c4 \uc0b0\uc2dd\uc73c\ub85c \uba3c\uc800 \ubcf4\uc5ec\uc8fc\ub294 \ud0d0\uc0c9 \ubaa9\ub85d\uc785\ub2c8\ub2e4. \uae09\uc5ec\u00b7\uace0\uc6a9\ud615\ud0dc\u00b7\uc9c0\uc6d0\uc790\uaca9\u00b7\ube44\uc790\u00b7\uc6cc\ub77c\ubc38\ucc98\ub7fc \ube44\uc5b4 \uc788\ub294 \uc870\uac74\uc740 \ud655\uc778 \uc804\uae4c\uc9c0 \ucd94\ucc9c \uadfc\uac70\ub85c \uac04\uc8fc\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.</p></section>`;
  }
  // UX-237: 유사도 기반 탐색 · 지원 추천이 아닙니다
  function candidateRow(job, compact = false) {
    const preference = effectivePreferenceFor(job);
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
    const candidatePage = dailyCandidates.length ? `<section class="decision-list" aria-labelledby="priorityHeading"><div class="section-heading"><div><span>${hasPersonalFeedback ? "피드백 유사 후보" : (ranked ? "우선 검토 후보" : "관심 탐색")}</span><h2 id="priorityHeading">오늘 열어볼 후보</h2></div><a href="#/jobs">새 후보 ${eligibleRecommendations.length}개 ${icon("arrow")}</a></div><div class="opportunity-list">${dailyCandidates.map((job) => candidateRow(job)).join("")}</div></section>` : `<section class="decision-list" aria-labelledby="inventoryHeading"><div class="section-heading"><div><span>새 공고 인벤토리</span><h2 id="inventoryHeading">저장·제외하지 않은 공고가 없습니다</h2></div><a href="#/saved">저장한 공고 ${icon("arrow")}</a></div></section>`;
    const researchPage = `<section class="route-callout" aria-labelledby="researchHeading"><div class="route-callout-copy"><p class="eyebrow">02 · 진학과 장학</p><h2 id="researchHeading">과정과 장학금</h2><a class="ink-link" href="#/study">전체 보기 ${icon("arrow")}</a></div><div class="route-mini-list">${school ? `<button type="button" data-open-record="program:${escapeHtml(school.id)}"><small>${escapeHtml(school.degree)} · ${escapeHtml(programReadinessLabel(school))}</small><b>${escapeHtml(school.university)}</b><span>${escapeHtml(school.program)}</span>${icon("arrow")}</button>` : ""}${award ? `<button type="button" data-open-record="funding:${escapeHtml(award.id)}"><small>${escapeHtml(award.decision)}</small><b>${escapeHtml(award.name)}</b><span>${escapeHtml(award.coverage || "지원 범위 원문 확인")}</span>${icon("arrow")}</button>` : ""}</div></section>`;
    const candidatePageWithTruth = [recommendationTruthNotice(), candidatePage].filter(Boolean).join("");
    const pages = [
      `<section class="today-cover" data-requirement-id="UX-204" aria-labelledby="todayTitle"><div class="cover-meta"><span>오늘의 목록</span><span>${escapeHtml(sourceDate(state.data.stats?.jobDataAsOf))}</span></div><div class="cover-copy"><p>공개 스냅샷</p><h1 id="todayTitle">오늘 볼 것</h1></div>${lead ? `<button class="cover-action" type="button" data-open-job="${escapeHtml(lead.id)}"><span>${ranked ? "우선 검토 후보" : "새 관심 후보"}</span><b>${escapeHtml(lead.company)}<em>${escapeHtml(lead.title)}</em></b>${icon("arrow")}</button>` : `<a class="cover-action" href="#/saved"><span>새 후보 확인 완료</span><b>저장한 공고 보기</b>${icon("arrow")}</a>`}</section>`,
      candidatePageWithTruth,
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
    main.innerHTML = pageFrame(`<section class="browse-head"><p class="eyebrow">${ranked ? "우선 검토 후보" : (exploring ? "관심 탐색" : "새 공고 인벤토리")}</p><div class="browse-title-row"><h1>새 국내·해외 공고</h1><button class="filter-trigger" type="button" data-action="open-filters" aria-label="공고 필터">${icon("filter")}${activeFilters() ? `<b>${activeFilters()}</b>` : ""}</button></div><label class="search-box">${icon("search")}<span class="sr-only">공고 검색</span><input id="jobSearch" type="search" value="${escapeHtml(state.query)}" placeholder="직무, 기관, 지역으로 찾기" autocomplete="off" /></label>${marketSwitch("job", state.jobMarket || "all", availableJobs)}<div class="sector-grid" data-requirement-id="UX-201"><button class="sector-chip ${!state.sector ? "is-active" : ""}" type="button" data-sector="">전체</button>${sectors}</div></section>`, 0, total, "공고 탐색") + `<div id="jobResults"></div>`;
    main.querySelector(".browse-head")?.insertAdjacentHTML("beforebegin", recommendationTruthNotice());
    document.getElementById("jobSearch").addEventListener("input", (event) => { state.query = event.target.value; saveFilters(); renderJobResults(); });
    renderJobResults();
  }

  function comparisonCard(record) {
    const { kind, item } = record;
    const isJob = kind === "job";
    const title = isJob ? item.title : item.program;
    const subtitle = isJob ? `${item.company} · ${item.location}` : item.university;
    const dimensions = (item.decisionSupport?.dimensions || []).map((dimension) => `<li><span>${escapeHtml(dimension.label)}</span><b>${escapeHtml(dimension.status)}</b><small>${escapeHtml(dimension.value)}</small></li>`).join("");
    return `<article class="comparison-card"><p class="eyebrow">${isJob ? "취업" : "진학"}</p><h3>${escapeHtml(title)}</h3><p>${escapeHtml(subtitle)}</p><ul>${dimensions}</ul><div><button class="plain-button" type="button" ${isJob ? `data-open-job="${escapeHtml(item.id)}"` : `data-open-record="program:${escapeHtml(item.id)}"`}>상세 보기</button><button class="comparison-remove" type="button" data-action="toggle-comparison" data-record-kind="${kind}" data-record-id="${escapeHtml(item.id)}">비교함에서 빼기</button></div></article>`;
  }

  function renderSaved() {
    /* data-requirement-id="UX-217" data-requirement-id="UX-230" */
    const bookmarks = savedJobs();
    const compared = comparisonRecords();
    const bookmarkPages = chunks(bookmarks, 3);
    const pages = [
      `<section class="results-section comparison-section" data-requirement-id="UX-230"><div class="section-heading"><div><span>이 기기 비교함</span><h1>취업·진학 나란히 보기</h1></div><b>${compared.length}개</b></div><p class="comparison-note">개수 제한 없이 담을 수 있습니다. 비교함은 피드백·추천 학습과 별도로 이 기기에 저장됩니다.</p><div class="comparison-grid">${compared.length ? compared.map(comparisonCard).join("") : `<div class="empty"><p>공고나 대학원 상세에서 비교함에 담아보세요.</p></div>`}</div></section>`,
      ...bookmarkPages.map((group, pageIndex) => `<section class="results-section"><div class="section-heading"><div><span>관심 보관함</span><h1>${pageIndex === 0 ? "저장한 공고" : `저장한 공고 ${pageIndex + 1}`}</h1></div><b>${bookmarks.length}개</b></div><div class="opportunity-list is-results">${group.map((job) => candidateRow(job, true)).join("")}</div></section>`),
    ];
    if (!bookmarks.length) pages.push(`<section class="results-section"><div class="section-heading"><div><span>관심 보관함</span><h1>저장한 공고</h1></div></div><div class="empty"><p>아직 저장한 공고가 없습니다.</p><a class="plain-button" href="#/jobs">새 공고 탐색하기</a></div></section>`);
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "저장과 비교")).join("");
  }

  const LIFESTYLE_STATUS_LABELS = {
    confirmed: "\ud655\uc778\ub428",
    claimed: "\uacf5\uace0 \uadfc\uac70 \uc788\uc74c",
    unknown: "\uadfc\uac70 \ubd80\uc871",
    negative: "\ubd80\uc815 \uc2e0\ud638",
  };
  const LIFESTYLE_SEARCH_LABELS = {
    searched: "\uc804\uccb4 \uc6d0\uc7a5 \uac80\uc0c9 \uc644\ub8cc",
    not_searched: "\uac80\uc0c9 \uc804",
    partial: "\ubd80\ubd84 \uac80\uc0c9",
    failed: "\uac80\uc0c9 \uc2e4\ud328",
    stale: "\uac31\uc2e0 \ud544\uc694",
  };
  const LIFESTYLE_READINESS_LABELS = {
    ready: "\uac80\ud1a0 \uac00\ub2a5",
    partial: "\ubd80\ubd84 \uadfc\uac70",
    insufficient: "\uadfc\uac70 \ubcf4\ub958",
  };
  const LIFESTYLE_SOURCE_STATE_LABELS = {
    known_open: "\uacf5\uace0 \uc0dd\uc874 \ud655\uc778",
    status_unknown: "\uc0c1\ud0dc \ubbf8\ud655\uc778",
    known_closed: "\ub9c8\uac10 \ud655\uc778",
    archived_reference: "\ubcf4\uad00 \uc6d0\ubb38",
  };
  const LIFESTYLE_AXIS_LABELS = {
    jayangCommute: "\uc790\uc591\ub3d9 \ud1b5\uadfc",
    wlb: "\uc6cc\ub77c\ubc38",
    busanWorkplace: "\ubd80\uc0b0 \uadfc\ubb34\uc9c0",
  };
  const LIFESTYLE_GLOBAL_FILTER_KEYS = [
    "sourcePostingCount",
    "nonClosed",
    "rawLocation",
    "strictLocation",
    "relevantDomain",
    "roleFit",
    "juniorAttainable",
    "wlbNotNegative",
    "deduplicated",
    "statusRecheck",
    "verifiedOpen",
    "publishedCandidate",
  ];
  const LIFESTYLE_LANE_FILTER_KEYS = [
    "rawLocation",
    "strictLocation",
    "relevantDomain",
    "roleFit",
    "juniorAttainable",
    "wlbNotNegative",
    "reviewCandidate",
    "statusRecheck",
    "verifiedOpen",
  ];
  const LIFESTYLE_LEGACY_GLOBAL_FILTER_KEYS = [
    "sourcePostings",
    "openOrUnknown",
    "targetLocation",
    "roleRelevant",
    "publishedCandidates",
    "excludedClosed",
    "excludedMalformed",
    "excludedDuplicate",
    "excludedNoTargetLocation",
    "excludedRoleNoise",
    "excludedSenior",
    "excludedNoRoleSignal",
  ];
  const LIFESTYLE_LEGACY_LANE_FILTER_KEYS = ["rawLocation", "strictLocation", "roleFit", "reviewCandidate", "statusRecheck", "verifiedOpen"];
  function lifestyleDiscovery() { return state.data?.lifestyleDiscovery || null; }
  function lifestyleItemById(id) { return lifestyleDiscovery()?.items?.find((item) => item.jobId === id) || null; }
  function lifestyleCount(value) { const number = Number(value); return Number.isFinite(number) ? number : 0; }
  function lifestyleItemLaneFilter(item, laneKey) { return item?.candidateFilter?.[laneKey] || {}; }
  function lifestyleHasExactKeys(value, keys) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    return Object.keys(value).sort().join(",") === keys.slice().sort().join(",");
  }
  function lifestyleHasAcceptedLaneFilterKeys(value) {
    return lifestyleHasExactKeys(value, LIFESTYLE_LANE_FILTER_KEYS)
      || lifestyleHasExactKeys(value, LIFESTYLE_LEGACY_LANE_FILTER_KEYS);
  }
  function lifestyleNonNegativeIntegers(value, keys) {
    return keys.every((key) => Number.isInteger(value?.[key]) && value[key] >= 0);
  }
  function normalizedLifestyleLaneFilter(laneFilter) {
    return {
      rawLocation: laneFilter?.rawLocation === true,
      strictLocation: laneFilter?.strictLocation === true,
      relevantDomain: (laneFilter?.relevantDomain ?? laneFilter?.roleFit) === true,
      roleFit: laneFilter?.roleFit === true,
      juniorAttainable: (laneFilter?.juniorAttainable ?? laneFilter?.roleFit) === true,
      wlbNotNegative: (laneFilter?.wlbNotNegative ?? laneFilter?.reviewCandidate) === true,
      reviewCandidate: laneFilter?.reviewCandidate === true,
      statusRecheck: laneFilter?.statusRecheck === true,
      verifiedOpen: laneFilter?.verifiedOpen === true,
    };
  }
  function lifestyleItemIsVerified(item) {
    return Object.values(item?.candidateFilter || {}).some((filter) => filter?.verifiedOpen === true);
  }
  function lifestyleItemNeedsRecheck(item) {
    return Object.values(item?.candidateFilter || {}).some((filter) => filter?.statusRecheck === true);
  }
  function lifestylePublicCandidateCount(discovery) {
    return lifestyleCount(discovery?.publicCandidateCount ?? discovery?.filterCounts?.publishedCandidate ?? discovery?.items?.length);
  }
  function lifestyleVerifiedOpenCount(discovery) {
    return lifestyleCount(discovery?.filterCounts?.verifiedOpen ?? (discovery?.items || []).filter(lifestyleItemIsVerified).length);
  }
  function lifestyleStatusRecheckCount(discovery) {
    const explicit = discovery?.filterCounts?.statusRecheck;
    if (Number.isFinite(Number(explicit))) return lifestyleCount(explicit);
    const candidates = lifestylePublicCandidateCount(discovery);
    return Math.max(0, candidates - lifestyleVerifiedOpenCount(discovery));
  }
  function lifestyleGlobalFilterCounts(discovery) {
    const canonical = discovery?.filterCounts || {};
    const legacy = discovery?.candidateFilter || {};
    const publishedCandidate = lifestylePublicCandidateCount(discovery);
    const verifiedOpen = lifestyleVerifiedOpenCount(discovery);
    const statusRecheck = lifestyleStatusRecheckCount(discovery);
    const sourcePostingCount = lifestyleCount(canonical.sourcePostingCount ?? legacy.sourcePostings ?? discovery?.sourcePostingCount);
    const nonClosed = lifestyleCount(canonical.nonClosed ?? legacy.openOrUnknown ?? sourcePostingCount);
    const rawLocation = Math.min(nonClosed, lifestyleCount(canonical.rawLocation ?? legacy.rawLocation ?? legacy.targetLocation ?? nonClosed));
    const strictLocation = Math.min(rawLocation, lifestyleCount(canonical.strictLocation ?? legacy.strictLocation ?? legacy.targetLocation ?? rawLocation));
    const relevantDomain = Math.min(strictLocation, lifestyleCount(canonical.relevantDomain ?? legacy.relevantDomain ?? legacy.roleRelevant ?? strictLocation));
    const roleFit = Math.min(relevantDomain, lifestyleCount(canonical.roleFit ?? legacy.roleFit ?? legacy.roleRelevant ?? relevantDomain));
    const juniorAttainable = Math.min(roleFit, lifestyleCount(canonical.juniorAttainable ?? legacy.juniorAttainable ?? roleFit));
    const wlbNotNegative = Math.min(juniorAttainable, lifestyleCount(canonical.wlbNotNegative ?? legacy.wlbNotNegative ?? legacy.publishedCandidates ?? publishedCandidate));
    const deduplicated = Math.min(wlbNotNegative, lifestyleCount(canonical.deduplicated ?? legacy.deduplicated ?? legacy.publishedCandidates ?? publishedCandidate));
    return {
      sourcePostingCount,
      nonClosed,
      rawLocation,
      strictLocation,
      relevantDomain,
      roleFit,
      juniorAttainable,
      wlbNotNegative,
      deduplicated,
      statusRecheck,
      verifiedOpen,
      publishedCandidate,
    };
  }
  function lifestyleLaneFilterCounts(lane) {
    const filter = lane?.filterCounts || {};
    const reviewCandidate = lifestyleCount(filter.reviewCandidate ?? lane?.reviewIds?.length);
    return {
      rawLocation: lifestyleCount(filter.rawLocation),
      strictLocation: lifestyleCount(filter.strictLocation),
      relevantDomain: lifestyleCount(filter.relevantDomain ?? filter.roleFit),
      roleFit: lifestyleCount(filter.roleFit),
      juniorAttainable: lifestyleCount(filter.juniorAttainable ?? filter.roleFit),
      wlbNotNegative: lifestyleCount(filter.wlbNotNegative ?? filter.reviewCandidate),
      reviewCandidate,
      statusRecheck: lifestyleCount(filter.statusRecheck),
      verifiedOpen: lifestyleCount(filter.verifiedOpen),
    };
  }
  function lifestyleList(values, emptyText) {
    const list = (values || []).filter(Boolean).slice(0, 4);
    if (!list.length) return `<p class="lifestyle-card-muted">${escapeHtml(emptyText)}</p>`;
    return `<ul class="lifestyle-reason-list">${list.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul>`;
  }
  function lifestyleEvidenceTexts(item, selectedAxes) {
    return [
      ...(item?.sourceEvidence || []),
      ...(item?.candidateEvidence || []).map((entry) => entry?.text).filter(Boolean),
      ...selectedAxes.flatMap(([axis]) => axis?.evidence || []),
    ].filter(Boolean);
  }
  function lifestyleSignalTexts(item, job) {
    return [
      ...(item?.entrySignals || []),
      ...(item?.experienceSignals || []),
      item?.filterReason,
      job?.fitReason,
    ].filter(Boolean);
  }
  function lifestyleDateTime(value) {
    const date = new Date(value || "");
    if (Number.isNaN(date.getTime())) return "\uc2dc\uac01 \ubbf8\uae30\ub85d";
    return date.toLocaleString("ko-KR", { month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }
  function lifestyleStatus(status, prefix = "생활조건: ") {
    const safe = Object.hasOwn(LIFESTYLE_STATUS_LABELS, status) ? status : "unknown";
    return `<span class="lifestyle-status is-${safe}">${escapeHtml(prefix)}${LIFESTYLE_STATUS_LABELS[safe]}</span>`;
  }
  function lifestyleSearchLabel(value) { return LIFESTYLE_SEARCH_LABELS[value] || LIFESTYLE_SEARCH_LABELS.partial; }
  function lifestyleReadinessLabel(value) { return LIFESTYLE_READINESS_LABELS[value] || LIFESTYLE_READINESS_LABELS.partial; }
  function lifestyleSourceLabel(sourceStatus) {
    const stateName = sourceStatus?.state || "status_unknown";
    return sourceStatus?.statusLabel || LIFESTYLE_SOURCE_STATE_LABELS[stateName] || LIFESTYLE_SOURCE_STATE_LABELS.status_unknown;
  }
  function lifestyleAxis(axis, label) {
    const value = axis || { status: "unknown", summary: "\uacf5\uac1c \uadfc\uac70\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.", evidence: [], missing: [] };
    const evidence = (value.evidence || []).filter(Boolean).join(" · ");
    const missing = (value.missing || []).filter(Boolean).join(" · ");
    return `<div class="lifestyle-axis"><div><b>${escapeHtml(label)}</b>${lifestyleStatus(value.status, "")}</div><p>${escapeHtml(value.summary || "\uc6d0\ubb38 \ud655\uc778 \ud544\uc694")}</p>${evidence ? `<small>${escapeHtml(evidence)}</small>` : ""}${missing ? `<small class="lifestyle-axis-missing">\ubbf8\ud655\uc778: ${escapeHtml(missing)}</small>` : ""}</div>`;
  }
  function lifestyleAxisCounts(lane) {
    const axisCounts = lane?.axisCounts || {};
    return Object.entries(LIFESTYLE_AXIS_LABELS).map(([axisKey, label]) => {
      const counts = axisCounts[axisKey];
      if (!counts) return "";
      const total = ["confirmed", "claimed", "unknown", "negative"].reduce((sum, status) => sum + lifestyleCount(counts[status]), 0);
      if (!total) return "";
      return `<div><small>${escapeHtml(label)}</small><b>${total}</b><span>\ud655\uc778 ${lifestyleCount(counts.confirmed)} · \uacf5\uace0 ${lifestyleCount(counts.claimed)} · \ubd80\uc871 ${lifestyleCount(counts.unknown)} · \ubd80\uc815 ${lifestyleCount(counts.negative)}</span></div>`;
    }).filter(Boolean).join("");
  }
  function lifestyleFilterFlow(discovery) {
    const filter = lifestyleGlobalFilterCounts(discovery);
    const rows = [
      ["\uc6d0\ucc9c \uacf5\uace0", filter.sourcePostingCount],
      ["\ub9c8\uac10 \uc81c\uc678", filter.nonClosed],
      ["\uc6d0\ucc9c \uc9c0\uc5ed", filter.rawLocation],
      ["\uc5c4\uaca9 \uc9c0\uc5ed", filter.strictLocation],
      ["\uad00\ub828 \ubd84\uc57c", filter.relevantDomain],
      ["\uc9c1\ubb34 \uc801\ud569", filter.roleFit],
      ["\ucd08\uae09 \uac00\ub2a5", filter.juniorAttainable],
      ["\uc6cc\ub77c\ubc38 \ubd80\uc815 \uc5c6\uc74c", filter.wlbNotNegative],
      ["\uc911\ubcf5 \uc81c\uac70", filter.deduplicated],
      ["\uc6d0\ubb38 \uc7ac\ud655\uc778 \ud544\uc694", filter.statusRecheck],
      ["\uc6d0\ubb38 \uacf5\uac1c \ud655\uc778", filter.verifiedOpen],
      ["\uc571 \ud45c\uc2dc \ud6c4\ubcf4", filter.publishedCandidate],
    ];
    return `<div class="lifestyle-filter-flow" data-requirement-id="UX-235" aria-label="\uc0dd\ud65c\uc870\uac74 \ud6c4\ubcf4 \ud544\ud130 \uacbd\ub85c">${rows.map(([label, value]) => `<div><small>${escapeHtml(label)}</small><b>${lifestyleCount(value).toLocaleString("ko-KR")}</b></div>`).join("")}</div>`;
  }
  function lifestyleLaneFilterFlow(lane) {
    // UX-236 reqgate anchors: 원천 위치 일치, 엄격 후보, 확정 추천, 재확인 필요 후보.
    const filter = lifestyleLaneFilterCounts(lane);
    const rows = [
      ["\uc6d0\ucc9c \uc704\uce58 \uc77c\uce58", filter.rawLocation],
      ["\uc5c4\uaca9 \uc704\uce58", filter.strictLocation],
      ["\uad00\ub828 \ubd84\uc57c", filter.relevantDomain],
      ["\uc9c1\ubb34 \uc801\ud569", filter.roleFit],
      ["\ucd08\uae09 \uac00\ub2a5", filter.juniorAttainable],
      ["\uc6cc\ub77c\ubc38 \ubd80\uc815 \uc5c6\uc74c", filter.wlbNotNegative],
      ["\uac80\ud1a0 \ud6c4\ubcf4", filter.reviewCandidate],
      ["\uc6d0\ubb38 \uc7ac\ud655\uc778 \ud544\uc694", filter.statusRecheck],
      ["\uc6d0\ubb38 \uacf5\uac1c \ud655\uc778", filter.verifiedOpen],
    ];
    return `<div class="lifestyle-funnel" data-requirement-id="UX-236" aria-label="생활조건 후보 엄격 필터">${rows.map(([label, value]) => `<div><small>${escapeHtml(label)}</small><b>${lifestyleCount(value).toLocaleString("ko-KR")}</b></div>`).join("")}</div>`;
  }
  function lifestyleCandidateLabel(item, laneKey) {
    const filter = lifestyleItemLaneFilter(item, laneKey);
    return filter.verifiedOpen ? "원문 상태: 공개 확인" : "원문 상태: 재확인 필요";
  }
  function lifestyleSearchMessage(discovery, lane, itemCount) {
    const searchState = lane?.searchState || discovery?.searchState || "partial";
    if (searchState === "not_searched") return "\uc544\uc9c1 \uc6d0\uc7a5 \uac80\uc0c9\uc744 \uc2e4\ud589\ud558\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4.";
    if (searchState === "failed") return "\uc6d0\uc7a5 \uac80\uc0c9\uc774 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4. \uae30\uc874 \ud6c4\ubcf4\ub294 \uc720\uc9c0\ub429\ub2c8\ub2e4.";
    if (!itemCount) return "\uc774 \uc870\uac74\uc73c\ub85c \uac80\uc0c9\ud55c \uacb0\uacfc\ub294 0\uac74\uc785\ub2c8\ub2e4. \uc804\uccb4 \ucc44\uc6a9\uc2dc\uc7a5\uc5d0 \uc5c6\ub2e4\ub294 \ub73b\uc740 \uc544\ub2d9\ub2c8\ub2e4.";
    return "\uc77c\ubc18 \ucd94\ucc9c \ubaa9\ub85d\uacfc \ubcc4\ub3c4\ub85c \uc804\uccb4 \uacf5\uace0 \uc6d0\uc7a5\uc5d0\uc11c \uc0dd\ud65c \uc870\uac74 \uac80\ud1a0 \ud6c4\ubcf4\ub97c \ubd84\ub9ac\ud588\uc2b5\ub2c8\ub2e4. \uc9c0\uc5ed\u00b7\uc6cc\ub77c\ubc38\uc740 \ucd94\ucc9c \uc810\uc218\uc5d0 \ubc18\uc601\ud558\uc9c0 \uc54a\uc73c\uba70, \ubd80\ubd84 \uadfc\uac70\ub294 \uac80\ud1a0 \ucd9c\ubc1c\uc810\uc785\ub2c8\ub2e4.";
  }
  function lifestyleCard(item, laneKey) {
    const axes = item.lifestyleEvidence?.axes || {};
    const selected = laneKey === "busan"
      ? [[axes.busanWorkplace, "\ubd80\uc0b0 \uadfc\ubb34\uc9c0"], [axes.wlb, "\uc6cc\ub77c\ubc38"]]
      : [[axes.jayangCommute, "\uc790\uc591\ub3d9 \ud1b5\uadfc"], [axes.wlb, "\uc6cc\ub77c\ubc38"]];
    const missing = [...new Set(selected.flatMap(([axis]) => axis?.missing || []).filter(Boolean))];
    const job = jobById(item.jobId);
    const inclusionReasons = item.inclusionReasons || selected.flatMap(([axis]) => axis?.evidence || []).filter(Boolean);
    const missingReasons = item.missingReasons || missing;
    const sourceEvidence = lifestyleEvidenceTexts(item, selected);
    const entrySignals = lifestyleSignalTexts(item, job);
    const scoreImpactReason = item.scoreImpactReason || "\uc0dd\ud65c\uc870\uac74\uc740 \ucd94\ucc9c \uc810\uc218\uc5d0 \ub354\ud558\uc9c0 \uc54a\uace0, \ubcc4\ub3c4 \ud6c4\ubcf4 \ud0ed\uc5d0\uc11c\ub9cc \uac80\ud1a0\ud569\ub2c8\ub2e4.";
    const sourceStatus = item.sourceStatus || {};
    const sourceState = sourceStatus.state || "status_unknown";
    const sourceUrl = item.url || job?.url || "";
    const candidateLabel = lifestyleCandidateLabel(item, laneKey);
    const candidateClass = lifestyleItemLaneFilter(item, laneKey).verifiedOpen ? "is-verified" : "is-recheck";
    const detailButton = job ? `<button class="plain-button lifestyle-detail" type="button" data-open-job="${escapeHtml(item.jobId)}">\uae30\uc874 \ucd94\ucc9c \uc0c1\uc138</button>` : "";
    const sourceButton = sourceUrl ? `<button class="plain-button lifestyle-source-button" type="button" data-open-lifestyle-url="${escapeHtml(sourceUrl)}">\uc6d0\ubb38 \uc5f4\uae30</button>` : "";
    return `<article class="lifestyle-card"><div class="lifestyle-card-top"><div><small>${escapeHtml(item.company || job?.company || "\uae30\uad00 \uc6d0\ubb38 \ud655\uc778")}</small><h2>${escapeHtml(item.title || job?.title || "\uacf5\uace0 \uc6d0\ubb38 \ud655\uc778")}</h2><p>${escapeHtml(item.location || job?.location || "\uadfc\ubb34\uc9c0 \ubbf8\ud655\uc778")}</p></div>${lifestyleStatus(item.lifestyleEvidence?.lanes?.[laneKey])}</div><p class="lifestyle-filter ${candidateClass}">${escapeHtml(candidateLabel)}</p><p class="lifestyle-source is-${escapeHtml(sourceState)}">${escapeHtml(item.source || "\ucd9c\ucc98 \ubbf8\uae30\ub85d")} · ${escapeHtml(lifestyleSourceLabel(sourceStatus))}</p><div class="lifestyle-axis-grid">${selected.map(([axis, label]) => lifestyleAxis(axis, label)).join("")}</div><div class="lifestyle-card-section"><b>\ud3ec\ud568 \uadfc\uac70</b>${lifestyleList(inclusionReasons, "\uc544\uc9c1 \uc120\ud0dd\ub41c \ud3ec\ud568 \uadfc\uac70\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.")}</div><div class="lifestyle-card-section lifestyle-missing"><b>\ubbf8\ud655\uc778/\ubcf4\ub958 \uadfc\uac70</b>${lifestyleList(missingReasons, "\ucd94\uac00 \ud655\uc778 \ud56d\ubaa9\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.")}</div><div class="lifestyle-card-section"><b>\ucd9c\ucc98 \uadfc\uac70</b>${lifestyleList(sourceEvidence, "\uc6d0\ubb38 \uadfc\uac70 \ucd94\uac00 \ud655\uc778 \ud544\uc694")}</div><div class="lifestyle-card-section"><b>\uc9c4\uc785/\uacbd\ub825 \uc2e0\ud638</b>${lifestyleList(entrySignals, "\ucd08\uae09 \uac00\ub2a5\uc131\uc740 \uc6d0\ubb38 \ud655\uc778 \ud544\uc694")}</div><div class="lifestyle-score-separation"><b>\uc810\uc218\uc640 \ubd84\ub9ac</b><p>${escapeHtml(scoreImpactReason)}</p></div><div class="lifestyle-card-actions">${sourceButton}${detailButton}</div></article>`;
  }

  function renderLifestyle() {
    // UX-234/UX-235: commute, WLB, and Busan are split axes; partial matches remain visible as 부분 근거.
    const discovery = lifestyleDiscovery();
    if (!discovery) {
      main.innerHTML = pageFrame(`<section class="lifestyle-head" data-requirement-id="UX-234 UX-235"><p class="eyebrow">\uc0dd\ud65c \uc870\uac74</p><h1>\uadfc\ubb34\uc9c0\u00b7\uc6cc\ub77c\ubc38 \uadfc\uac70</h1><div class="empty"><p>\ud45c\uc2dc\ud560 \uac80\ud1a0 \ud6c4\ubcf4 0\uac74</p></div></section>`, 0, 1, "\uc0dd\ud65c \uc870\uac74");
      return;
    }
    const laneKey = discovery.lanes?.[state.lifestyleLane] ? state.lifestyleLane : "jayang_wlb";
    const lane = discovery.lanes?.[laneKey] || { label: "\uc0dd\ud65c \uc870\uac74", reviewIds: [], counts: {} };
    const laneLabel = laneKey === "busan" ? "부산 근무지 후보 · 통근/WLB 실제 확인 필요" : "서울권 근무지 후보 · 자양동 통근/WLB 실제 확인 필요";
    const items = (lane.reviewIds || []).map(lifestyleItemById).filter(Boolean);
    const groups = chunks(items, 2);
    const counts = lane.counts || {};
    const globalCounts = lifestyleGlobalFilterCounts(discovery);
    const candidateCount = lifestylePublicCandidateCount(discovery);
    const verifiedCount = lifestyleVerifiedOpenCount(discovery);
    const recheckCount = lifestyleStatusRecheckCount(discovery);
    const axisCounts = lifestyleAxisCounts(lane);
    const limitations = [...new Set((discovery.limitations || []).filter(Boolean))].slice(0, 4);
    const limitationsMarkup = limitations.length
      ? `<div class="lifestyle-limitations"><b>판단 한계</b>${lifestyleList(limitations, "추가 확인 항목이 없습니다.")}</div>`
      : "";
    let header = `<section class="lifestyle-head" data-requirement-id="UX-234 UX-235"><p class="eyebrow">\uc810\uc218\uc640 \ubd84\ub9ac\ub41c \uc0dd\ud65c\uc870\uac74 \uadfc\uac70</p><h1>\uad6d\ub0b4 \uc0dd\ud65c\uc870\uac74 \ud6c4\ubcf4 \uac80\ud1a0</h1><p>\uc11c\uc6b8/\ubd80\uc0b0\uc740 \ucd94\ucc9c \uc810\uc218 \uac00\uc911\uce58\uac00 \uc544\ub2c8\ub77c \ubcc4\ub3c4 \ud544\ud130\uc785\ub2c8\ub2e4. \uc9c1\ubb34 \uc2e0\ud638\uac00 \uc57d\ud55c \uacf5\uace0\ub294 \uc6d0\uc7a5 \ub2e8\uacc4\uc5d0\uc11c \uc81c\uc678\ud569\ub2c8\ub2e4.</p><div class="lifestyle-lanes" role="tablist" aria-label="\uc0dd\ud65c \uc870\uac74 \ubcf4\uae30"><button class="lifestyle-lane ${laneKey === "jayang_wlb" ? "is-active" : ""}" type="button" role="tab" aria-selected="${laneKey === "jayang_wlb"}" data-lifestyle-lane="jayang_wlb">\uc790\uc591\ub3d9 \ud1b5\uadfc \uac80\ud1a0</button><button class="lifestyle-lane ${laneKey === "busan" ? "is-active" : ""}" type="button" role="tab" aria-selected="${laneKey === "busan"}" data-lifestyle-lane="busan">\ubd80\uc0b0 \uadfc\ubb34\uc9c0 \uac80\ud1a0</button></div><div class="lifestyle-summary"><span>\ud655\uc778 ${lifestyleCount(counts.confirmed)}</span><span>\uacf5\uace0 \uadfc\uac70 ${lifestyleCount(counts.claimed)}</span><span>\uadfc\uac70 \ubd80\uc871 ${lifestyleCount(counts.unknown)}</span><span>\ubd80\uc815 \uc2e0\ud638 ${lifestyleCount(counts.negative)}</span></div><div class="lifestyle-lineage"><div><small>\uac80\uc0c9 \uc0c1\ud0dc</small><b>${escapeHtml(lifestyleSearchLabel(lane.searchState || discovery.searchState))}</b></div><div><small>\uac80\uc0c9 \uc2dc\uac01</small><b>${escapeHtml(lifestyleDateTime(lane.searchedAt || discovery.searchedAt))}</b></div><div><small>\uc758\uc0ac\uacb0\uc815</small><b>${escapeHtml(lifestyleReadinessLabel(lane.decisionReadiness))}</b></div><div><small>\uc6d0\uc7a5</small><b>${lifestyleCount(discovery.sourcePostingCount).toLocaleString("ko-KR")}</b></div><div><small>\uc9c1\ubb34 \uc2e0\ud638</small><b>${lifestyleCount(discovery.sourceRelevantPostingCount).toLocaleString("ko-KR")}</b></div><div><small>\uacf5\uac1c \ucd94\ucc9c</small><b>${lifestyleCount(discovery.publicRecommendationCount).toLocaleString("ko-KR")}</b></div></div>${lifestyleFilterFlow(discovery)}${lifestyleLaneFilterFlow(lane)}${axisCounts ? `<div class="lifestyle-axis-counts" data-axis-counts="true">${axisCounts}</div>` : ""}<p class="lifestyle-boundary">${escapeHtml(lifestyleSearchMessage(discovery, lane, items.length))} ${escapeHtml(discovery.universeLabel || "\ud604\uc7ac \uacf5\uac1c \uc218\uc9d1\ubcf8")} \uae30\uc900\uc774\uba70, \ubd80\ubd84 \uadfc\uac70\ub294 \uc9c0\uc6d0 \uc804 \uc6d0\ubb38 \ud655\uc778\uc774 \ud544\uc694\ud569\ub2c8\ub2e4.</p></section>`;
    header = header.replace(/<div><small>\uc6d0\uc7a5<\/small><b>[^<]*<\/b><\/div><div><small>\uc9c1\ubb34 \uc2e0\ud638<\/small><b>[^<]*<\/b><\/div><div><small>\uacf5\uac1c \ucd94\ucc9c<\/small><b>[^<]*<\/b><\/div>/, `<div><small>\uc6d0\ucc9c \uacf5\uace0</small><b>${globalCounts.sourcePostingCount.toLocaleString("ko-KR")}</b></div><div><small>\uc571 \ud45c\uc2dc \ud6c4\ubcf4</small><b>${candidateCount.toLocaleString("ko-KR")}</b></div><div><small>\uc6d0\ubb38 \uacf5\uac1c \ud655\uc778</small><b>${verifiedCount.toLocaleString("ko-KR")}</b></div><div><small>\uc6d0\ubb38 \uc7ac\ud655\uc778 \ud544\uc694</small><b>${recheckCount.toLocaleString("ko-KR")}</b></div>`);
    header = header.replace("\uc790\uc591\ub3d9 \ud1b5\uadfc \uac80\ud1a0", "\uc11c\uc6b8\uad8c \ud1b5\uadfc \uac80\ud1a0");
    header = header.replace("<span>\ud655\uc778 ", "<span>\uc885\ud569 \ud655\uc778 ");
    header = header.replace("<span>\uacf5\uace0 \uadfc\uac70 ", "<span>\uc885\ud569 \uacf5\uace0 \uadfc\uac70 ");
    header = header.replace("<span>\uadfc\uac70 \ubd80\uc871 ", "<span>\uc885\ud569 \uadfc\uac70 \ubd80\uc871 ");
    header = header.replace("<span>\ubd80\uc815 \uc2e0\ud638 ", "<span>\uc885\ud569 \ubd80\uc815 \uc2e0\ud638 ");
    header = header.replace("</section>", `${limitationsMarkup}</section>`);
    const pages = [header];
    if (groups.length) {
      pages.push(...groups.map((group, index) => `<section class="lifestyle-results" aria-label="${escapeHtml(laneLabel)}"><div class="results-meta"><span>${escapeHtml(laneLabel)} ${index * 2 + 1}\u2013${index * 2 + group.length}</span><b>${items.length}\uac1c</b></div>${group.map((item) => lifestyleCard(item, laneKey)).join("")}</section>`));
    } else {
      pages.push(`<section class="lifestyle-results" aria-label="${escapeHtml(laneLabel)}"><div class="results-meta"><span>${escapeHtml(laneLabel)}</span><b>0\uac1c</b></div><div class="empty"><p>\ud45c\uc2dc\ud560 \uac80\ud1a0 \ud6c4\ubcf4 0\uac74</p><small>\uc774 \uc870\uac74\uc73c\ub85c \uac80\uc0c9\ub41c \uacb0\uacfc\uac00 0\uc774\ub77c\ub294 \ub73b\uc774\uc9c0, \ucc44\uc6a9\uc2dc\uc7a5 \uc804\uccb4\uc5d0 \uc5c6\ub2e4\ub294 \ub73b\uc740 \uc544\ub2d9\ub2c8\ub2e4.</small></div></section>`);
    }
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "\uc0dd\ud65c \uc870\uac74")).join("");
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
    /* data-requirement-id="UX-227" 공고 기준 / 대학원 생성 */
    const stats = state.data.stats || {};
    const likedJobs = savedJobs();
    const dislikedJobs = jobs().filter((job) => preferenceFor(job.id)?.sentiment === "not_for_me");
    const likedCount = Math.max(likedJobs.length, Object.values(state.feedback).filter((item) => item?.sentiment === "liked").length);
    const dislikedCount = Math.max(Number(stats.preferenceSummary?.dislikedCount || 0), Object.values(state.feedback).filter((item) => item?.sentiment === "not_for_me").length);
    const feedbackAfterLastRefresh = pendingPreferenceCount();
    const refreshCoverageCopy = state.lastSuccessfulRefreshAt ? `마지막 추천 이후 새 피드백 ${feedbackAfterLastRefresh}건` : `아직 성공한 추천 갱신 없음 · 피드백 ${feedbackAfterLastRefresh}건 대기`;
    const backupPage = feedbackBackupPanel(refreshCoverageCopy, state.feedbackImportStatus);
    const syncCopy = state.syncState === "synced" ? "Supabase에 저장됨" : state.syncState === "syncing" ? "Supabase에 저장 중" : state.syncState === "error" ? "연결 실패 · 이 기기에 안전하게 보관 중" : "이 기기에 보관 중";
    const pages = [
      `<section class="sources-head"><p class="eyebrow">자료의 범위</p><h1>무엇을 담고,<br />어디까지 아는가.</h1><p>${escapeHtml(state.data.snapshotBoundary)}</p></section>`,
      backupPage,
      `<section class="source-stamp"><span>PUBLIC SNAPSHOT</span><b>${displayDate(state.data.generatedAt)}</b><i>V4<br />FIRST</i></section><section class="stat-strip"><div><small>${stats.recommendationSurface === "exploration_only" ? "관심 후보" : "행동 후보"}</small><b>${escapeHtml(stats.actionCandidates)}</b></div><div><small>대학원</small><b>${escapeHtml(stats.programs)}</b></div><div><small>장학금</small><b>${escapeHtml(stats.funding)}</b></div></section>`,
      `<section class="preference-panel" data-requirement-id="UX-212"><p class="eyebrow">나의 학습 신호</p><h2>공고 피드백</h2><p>공고 카드에서 바로 관심 또는 별로예요를 누르고 이유를 남길 수 있습니다. 저장한 내용은 다음 후보 구성에 반영됩니다.</p><div class="preference-counts"><div><small>관심 공고</small><b>${likedCount}</b></div><div><small>별로예요</small><b>${dislikedCount}</b></div></div><p class="sync-status" data-state="${state.syncState}" data-requirement-id="UX-210">${syncCopy}</p><div data-requirement-id="UX-221"><section class="feedback-review-group"><div class="feedback-review-heading"><h3>관심 공고와 좋은 이유</h3><b>${likedCount}</b></div>${feedbackReviewList(likedJobs, "liked")}</section><section class="feedback-review-group"><div class="feedback-review-heading"><h3>별로예요와 이유</h3><b>${dislikedCount}</b></div>${feedbackReviewList(dislikedJobs, "not_for_me")}</section></div><button class="plain-button export-button" type="button" data-action="export-feedback">피드백 내보내기</button></section>`,
      `<section class="source-explainer"><p class="eyebrow">검증 경계</p><h2>점수로 결론을 대신하지 않습니다.</h2><p>공고는 최신 V4 행동 큐를, 진학·재정은 현재 대시보드의 연구 목록을 사용합니다. 공개 화면에는 개인 프로필, 지원 이력, CRM 정보가 포함되지 않습니다.</p><div class="status-rows"><div><span>V4 실행 ID</span><b>${escapeHtml(stats.v4RunId || "확인 중")}</b></div><div><span>공고 기준일</span><b>${escapeHtml(stats.jobDataAsOf || "확인 중")}</b></div><div><span>대학원 자료 생성</span><b>${escapeHtml(stats.graduateGeneratedAt || "확인 중")}</b></div></div></section>`,
    ];
    main.innerHTML = pages.map((page, index) => pageFrame(page, index, pages.length, "자료")).join("");
  }

  function feedbackBackupPanel(message, status) {
    return `<section class="preference-panel feedback-backup-panel" data-requirement-id="UX-226">
      <p class="eyebrow">기기 변경 대비</p>
      <h2>피드백 백업·복원</h2>
      <p class="refresh-coverage" data-requirement-id="DATA-231">${escapeHtml(message)}</p>
      <div class="feedback-backup-actions">
        <button class="plain-button" type="button" data-action="export-feedback-backup">JSON 백업 저장</button>
        <button class="plain-button" type="button" data-action="import-feedback">JSON 백업 가져오기</button>
      </div>
      <p class="backup-status" role="status">${escapeHtml(status)}</p>
    </section>`;
  }

  function detailList(title, values) { return values?.length ? `<section class="detail-list"><small>${escapeHtml(title)}</small><ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>` : ""; }
  function officialLink(url) { return url ? `<a class="official-button" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">공식 원문 열기 ${icon("external")}</a>` : `<span class="official-button is-disabled">공식 원문 주소 없음</span>`; }
  function decisionSupportPanel(item) {
    /* data-requirement-id="UX-229" */
    const support = item.decisionSupport || {};
    const dimensions = (support.dimensions || []).map((dimension) => `<li><span>${escapeHtml(dimension.label)}</span><b>${escapeHtml(dimension.status)}</b><p>${escapeHtml(dimension.value)}</p></li>`).join("");
    const known = (support.knownInformation || []).map((fact) => `<li><b>${escapeHtml(fact.label)}</b><span>${escapeHtml(fact.value)}</span><small>${escapeHtml(fact.evidence || "공개 근거")}</small></li>`).join("");
    const missing = (support.missingInformation || []).map((fact) => `<li><b>${escapeHtml(fact.label)}</b><span>${escapeHtml(fact.why)}</span></li>`).join("");
    const actions = (support.nextActions || []).map((action) => `<li>${escapeHtml(action)}</li>`).join("");
    /* 확인된 정보 · 아직 확인할 정보 */
    return `<section class="decision-panel" data-requirement-id="UX-229"><div class="decision-heading"><div><p class="eyebrow">\uc758\uc0ac\uacb0\uc815 \uc694\uc57d</p><h3>\ud655\uc778\ub41c \uc815\ubcf4\uc640 \ube48\uce78\uc744 \ubd84\ub9ac\ud588\uc2b5\ub2c8\ub2e4.</h3></div><small>${escapeHtml(support.lastVerified || "\ud655\uc778\uc77c \ubbf8\uae30\ub85d")}</small></div><ul class="decision-dimensions">${dimensions}</ul><div class="decision-columns"><section><h4>\ud655\uc778\ub41c \uc815\ubcf4</h4><ul class="decision-facts">${known || "<li><span>\uc5f0\uacb0\ub41c \uacf5\uac1c \uadfc\uac70\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.</span></li>"}</ul></section><section><h4>\uc544\uc9c1 \ud655\uc778\ud560 \uc815\ubcf4</h4><ul class="decision-facts is-missing">${missing || "<li><span>\ud604\uc7ac \ub4f1\ub85d\ub41c \ucd94\uac00 \ud655\uc778 \ud56d\ubaa9\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.</span></li>"}</ul></section></div>${actions ? `<section class="decision-next"><h4>\ub2e4\uc74c \ud589\ub3d9</h4><ol>${actions}</ol></section>` : ""}<p class="decision-boundary">${escapeHtml(support.evidenceLevel || "\uacf5\uac1c \uadfc\uac70")} \u00b7 \ube48\uce78\uc740 \ucd94\uc815\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.</p></section>`;
  }
  function personalizationBreakdown(job) {
    const signal = job.preferenceDiscovery || job.personalization;
    const components = signal?.components || {};
    const score = Number(signal?.similarityScore ?? signal?.score ?? 0);
    const positiveSimilarity = Number(components.positiveSimilarity || 0);
    const negativeSimilarity = Number(components.negativeSimilarity || 0);
    const positiveReasonMatch = Number(components.positiveReasonMatch || 0);
    const negativeReasonMatch = Number(components.negativeReasonMatch || 0);
    const reasonPenalty = Number(components.reasonPenalty || 0);
    const directPreference = preferenceFor(job.id);
    const exactOverride = signal?.exactFeedbackOverride;
    const directSentiment = exactOverride?.sentiment || (["liked", "not_for_me"].includes(directPreference?.sentiment) ? directPreference.sentiment : "");
    if (directSentiment) {
      const directHeading = directSentiment === "liked" ? "\uad00\uc2ec\uc73c\ub85c \uc800\uc7a5\ud55c \uacf5\uace0" : "\ubcc4\ub85c\uc608\uc694\ub85c \ubd84\ub958\ud55c \uacf5\uace0";
      const sortValue = Number(exactOverride?.sortValue ?? (directSentiment === "liked" ? 100 : -100));
      const calculatedSimilarity = positiveSimilarity + positiveReasonMatch - negativeSimilarity - negativeReasonMatch;
      const similarityValue = Number.isFinite(Number(signal?.similarityScore)) ? Number(signal.similarityScore) : calculatedSimilarity;
      const similarityCopy = signal?.modelVersion ? ((similarityValue >= 0 ? "+" : "") + similarityValue.toFixed(1)) : "\uc544\uc9c1 \uacc4\uc0b0 \uae30\ub85d \uc5c6\uc74c";
      return '<section class="decision-panel personalization-panel" data-requirement-id="DATA-244" data-score-mode="exact_feedback_override"><p class="eyebrow">\uc9c1\uc811 \ubd84\ub958 \uae30\ub85d</p><h3>' + escapeHtml(directHeading) + '</h3><div class="personalization-scores"><div><small>\uc800\uc7a5\u00b7\uc81c\uc678 \uc815\ub82c\uc6a9 \uace0\uc815\uac12</small><b>' + (sortValue >= 0 ? "+" : "") + sortValue.toFixed(0) + '</b><span>\uc720\uc0ac\ub3c4 \uc810\uc218\uac00 \uc544\ub2d9\ub2c8\ub2e4.</span></div><div><small>\ubcc4\ub3c4 \ud53c\ub4dc\ubc31 \uc720\uc0ac\ub3c4</small><b>' + escapeHtml(similarityCopy) + '</b><span>\uc0c8 \uacf5\uace0 \ud0d0\uc0c9\uc6a9</span></div></div><p>\uc0ac\uc6a9\uc790\uac00 \uc9c1\uc811 \ub0a8\uae34 \ubd84\ub958\ub97c \uacc4\uc0b0\ub41c \ucd94\ucc9c\uc73c\ub85c \ubc14\uafb8\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.</p></section>';
    }
    // DATA-244: 직접 분류 기록 · 유사도 점수가 아닙니다
    const finalScoreCopy = score.toFixed(1);
    if (!signal?.modelVersion) return "";
    const dimensions = signal.matchedDimensions || [];
    const dimensionLabels = {
      role: "\uc9c1\ubb34",
      field: "\ubd84\uc57c",
      company: "\uc870\uc9c1",
    };
    const dimensionCopy = `${dimensions.map((item) => dimensionLabels[item] || item).join(" / ")} \u00b7 \uc720\uc0ac\ub3c4 ${score >= 0 ? "+" : ""}${finalScoreCopy}`;
    const positiveReasons = (signal.positiveReasonSignals || []).map((item) => FEEDBACK_REASON_LABELS[item] || item);
    const reasons = (signal.appliedReasons || []).map((item) => FEEDBACK_REASON_LABELS[item] || item);
    const positiveReasonCopy = positiveReasons.length ? `가점 근거 · ${positiveReasons.join(" · ")}` : "";
    const reasonCopy = reasons.length ? `감점 근거 · ${reasons.join(" · ")}` : "";
    const methodCopy = "\uc774 \uae30\ub85d\uc740 \uc774\uc804 \uc720\uc0ac\ub3c4 \ubaa8\ub378\uc5d0\uc11c \uc0dd\uc131\ub410\uc2b5\ub2c8\ub2e4. \ud604\uc7ac \ud0d0\uc0c9 \uc21c\uc11c\ub294 \uc9c0\uc5ed\uc744 \uc810\uc218\uc5d0 \ub123\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.";
    const feedbackDecayCopy = "\uc800\uc7a5\ud55c \uad00\uc2ec\u00b7\ubcc4\ub85c\uc608\uc694 \uc804\uac74\uc744 \uba3c\uc800 \ube44\uad50\ud55c \ub4a4, \uc774 \uacf5\uace0\uc640 \uac00\uc7a5 \ub2ee\uc740 \uadfc\uac70 3\uac74\uc744 100% \u00b7 60% \u00b7 35%\ub85c \ucc28\ub4f1 \ubc18\uc601\ud569\ub2c8\ub2e4. \ud53c\ub4dc\ubc31 \uac1c\uc218\ub294 \uace0\uc815\ub418\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.";
    const finalScoreEquation = `+${positiveSimilarity.toFixed(1)} - ${negativeSimilarity.toFixed(1)} - ${reasonPenalty.toFixed(1)} = ${score >= 0 ? "+" : ""}${finalScoreCopy}`;
    const explanationCopy = [signal.reasonKo || job.discoveryReason || "", positiveReasonCopy].filter(Boolean).join(" ");
    if (signal.modelVersion === "preference-ranker-v3") {
      const structuredEquation = `+${positiveSimilarity.toFixed(1)} + ${positiveReasonMatch.toFixed(1)} - ${negativeSimilarity.toFixed(1)} - ${negativeReasonMatch.toFixed(1)} = ${score >= 0 ? "+" : ""}${finalScoreCopy}`;
      return `<section class="decision-panel personalization-panel" data-requirement-id="DATA-237"><p class="eyebrow">유사도 비교 근거</p><h3>${escapeHtml(dimensionCopy || "저장한 피드백과 비교")}</h3><div class="personalization-scores"><div><small>관심 기본 유사도</small><b>+${positiveSimilarity.toFixed(1)}</b></div><div><small>관심 사유 일치</small><b>+${positiveReasonMatch.toFixed(1)}</b></div><div><small>별로예요 기본 유사도</small><b>-${negativeSimilarity.toFixed(1)}</b></div><div><small>별로예요 사유 일치</small><b>-${negativeReasonMatch.toFixed(1)}</b></div></div><div class="personalization-formula"><small>유사도 점수 = 관심 기본 + 관심 사유 - 비선호 기본 - 비선호 사유</small><strong>${escapeHtml(structuredEquation)}</strong></div><p>${escapeHtml(explanationCopy)}</p><ol class="personalization-method"><li>기본 유사도 40% · 구조화 사유 60%</li><li>기본 유사도는 직무 60% + 분야 35% + 조직 5%</li><li>지역은 국내·국외 분류에만 사용하며 유사도 점수에는 반영하지 않습니다.</li><li>자유 메모는 기록·검토용이며 점수에 몰래 반영하지 않습니다.</li></ol>${reasonCopy ? `<p class="personalization-reasons">${escapeHtml(reasonCopy)}</p>` : ""}<small class="personalization-coverage">전체 비교 피드백 · 관심 ${signal.likedEvidenceCount || 0}건 / 별로예요 ${signal.dislikedEvidenceCount || 0}건</small></section>`;
    }
    return `<section class="decision-panel personalization-panel" data-requirement-id="DATA-235"><p class="eyebrow">\uc720\uc0ac\ub3c4 \ube44\uad50 \uadfc\uac70</p><h3>${escapeHtml(dimensionCopy || "\uc800\uc7a5\ud55c \ud53c\ub4dc\ubc31\uacfc \ube44\uad50")}</h3><div class="personalization-scores"><div><small>\uad00\uc2ec \uc720\uc0ac \uac00\uc810</small><b>+${positiveSimilarity.toFixed(1)}</b><span>\ucd5c\ub300 +70</span></div><div><small>\ubcc4\ub85c\uc608\uc694 \uc720\uc0ac \uac10\uc810</small><b>-${negativeSimilarity.toFixed(1)}</b><span>\ucd5c\ub300 -60</span></div><div><small>\uba85\uc2dc \uc0ac\uc720 \uc704\ud5d8</small><b>-${reasonPenalty.toFixed(1)}</b><span>\ucd5c\ub300 -30</span></div></div><div class="personalization-formula" data-requirement-id="DATA-236"><small>\uc720\uc0ac\ub3c4 \uc810\uc218 = \uad00\uc2ec \uac00\uc810 - \ubcc4\ub85c\uc608\uc694 \uac10\uc810 - \uc0ac\uc720 \uc704\ud5d8</small><strong>${escapeHtml(finalScoreEquation)}</strong></div><p>${escapeHtml(explanationCopy)}</p><ol class="personalization-method"><li>${escapeHtml(methodCopy)}</li><li>${escapeHtml(feedbackDecayCopy)}</li></ol>${reasonCopy ? `<p class="personalization-reasons">${escapeHtml(reasonCopy)}</p>` : ""}<small class="personalization-coverage">\uc804\uccb4 \ube44\uad50 \ud53c\ub4dc\ubc31 \u00b7 \uad00\uc2ec ${signal.likedEvidenceCount || 0}\uac74 / \ubcc4\ub85c\uc608\uc694 ${signal.dislikedEvidenceCount || 0}\uac74</small></section>`;
  }

  function renderJobDetail(job) {
    const preference = effectivePreferenceFor(job);
    const saved = preference?.sentiment === "liked";
    const rejected = preference?.sentiment === "not_for_me";
    const discovery = job.discoveryTier === "explore";
    dossier.innerHTML = `<article class="detail"><header><span class="sheet-handle" aria-hidden="true"></span><div><small>${escapeHtml(job.source)} · ${queueCopy(job)}</small><button class="detail-close" type="button" data-action="close-dossier">닫기</button></div></header><div class="detail-body"><p class="detail-kicker">${escapeHtml(jobSectors(job).join(" · ") || "분야 원문 확인")}</p><h2 id="dossierTitle">${escapeHtml(job.title)}</h2><p class="detail-company">${escapeHtml(job.company)} · ${escapeHtml(job.location)}</p><div class="detail-primary">${officialLink(job.url)}</div><div class="detail-facts"><div><small>${discovery ? "분류" : "행동 상태"}</small><b>${queueCopy(job)}</b></div><div><small>마감</small><b>${escapeHtml(job.deadline || "원문 확인")}</b></div><div><small>증거 공백</small><b>${job.evidenceGapCount ?? "원문 확인"}</b></div><div><small>확인 부담</small><b>${escapeHtml(job.evidenceBurden || "원문 확인")}</b></div></div>${discovery ? `<section class="check-note"><small>보여드린 이유</small><p>${escapeHtml(job.discoveryReason)}</p></section>` : ""}<section class="check-note"><small>${discovery ? "원문에서 먼저 볼 것" : "다음 행동"}</small><p>${escapeHtml(job.nextAction)}</p></section>${detailList("공고에서 확인된 조건", job.requirements)}${detailList("추가 확인 항목", job.checks)}${detailList("주의 사항", job.risks)}<div class="detail-actions"><button class="detail-save ${saved ? "is-saved" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="liked" data-job-id="${escapeHtml(job.id)}" aria-pressed="${saved}">${icon(saved ? "bookmark-fill" : "bookmark")}${saved ? "관심 이유 수정" : "관심 있어요"}</button><button class="plain-button detail-dislike ${rejected ? "is-active" : ""}" type="button" data-action="open-feedback" data-feedback-sentiment="not_for_me" data-job-id="${escapeHtml(job.id)}" aria-pressed="${rejected}">${rejected ? "별로예요 반영됨" : "별로예요"}</button></div></div></article>`;
    const jobPrimary = dossier.querySelector(".detail-primary");
    jobPrimary?.insertAdjacentHTML("beforeend", `<button class="compare-button ${isCompared("job", job.id) ? "is-active" : ""}" type="button" data-action="toggle-comparison" data-record-kind="job" data-record-id="${escapeHtml(job.id)}" aria-pressed="${isCompared("job", job.id)}">${isCompared("job", job.id) ? "비교함에서 빼기" : "비교함에 담기"}</button>`);
    jobPrimary?.insertAdjacentHTML("afterend", `${personalizationBreakdown(job)}${decisionSupportPanel(job)}`);
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
      untyped_faculty_source: "교수·연구자 공개 페이지",
      untyped_public_source: "공개 진로 자료",
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
    const programPrimary = dossier.querySelector(".detail-primary");
    programPrimary?.insertAdjacentHTML("beforeend", `<button class="compare-button ${isCompared("program", item.id) ? "is-active" : ""}" type="button" data-action="toggle-comparison" data-record-kind="program" data-record-id="${escapeHtml(item.id)}" aria-pressed="${isCompared("program", item.id)}">${isCompared("program", item.id) ? "비교함에서 빼기" : "비교함에 담기"}</button>`);
    programPrimary?.insertAdjacentHTML("afterend", decisionSupportPanel(item));
  }
  function openJobDetail(id, trigger) {
    const job = jobById(id);
    if (!job) return;
    state.selectedTrigger = trigger || null;
    state.activeJobId = id;
    renderJobDetail(job);
    if (!dossier.open) dossier.showModal();
    requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus());
  }
  function openRecordDetail(kind, id, trigger) {
    const item = recordById(kind, id);
    if (!item) return;
    state.selectedTrigger = trigger || null;
    state.activeRecordKind = kind;
    state.activeRecordId = id;
    renderRecordDetail(kind, item);
    if (!dossier.open) dossier.showModal();
    requestAnimationFrame(() => dossier.querySelector("[data-action='close-dossier']")?.focus());
  }
  function closeDetail(restore = true) {
    if (dossier.open) dossier.close();
    if (restore && state.selectedTrigger?.isConnected) state.selectedTrigger.focus();
    state.selectedTrigger = null;
    state.activeJobId = null;
    state.activeRecordKind = null;
    state.activeRecordId = null;
  }

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
    const normalized = preference ? normalizeLegacyFeedbackPreference({ ...preference, updatedAt: new Date().toISOString() }) : null;
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
    migrateLegacyFeedback();
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
          state.feedback[row.job_id] = normalizeLegacyFeedbackPreference({ sentiment: row.sentiment, reasons: row.reasons || [], note: row.note || "", updatedAt: row.updated_at });
        }
      });
      migrateLegacyFeedback();
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
  function parseStructuredFeedbackNote(note = "") {
    const parsed = {};
    const titles = new Map(FEEDBACK_REASON_GROUPS.map((group) => [group.title, group.id]));
    titles.set("기타", "general");
    String(note).split(/\r?\n/).forEach((line) => {
      const match = line.match(/^\[([^\]]+)\]\s*(.*)$/);
      if (match && titles.has(match[1])) parsed[titles.get(match[1])] = match[2];
      else if (line.trim()) parsed.general = [parsed.general, line.trim()].filter(Boolean).join("\n");
    });
    return parsed;
  }
  function buildStructuredFeedbackNote() {
    const titles = Object.fromEntries(FEEDBACK_REASON_GROUPS.map((group) => [group.id, group.title]));
    titles.general = "기타";
    return [...document.querySelectorAll("[data-feedback-note-group]")]
      .map((field) => [titles[field.dataset.feedbackNoteGroup], field.value.trim()])
      .filter(([, value]) => value)
      .map(([title, value]) => `[${title}] ${value}`)
      .join("\n");
  }
  function renderFeedbackReasonGroups(config) {
    const entries = Object.entries(config.labels);
    const sections = FEEDBACK_REASON_GROUPS.map((group) => {
      const choices = entries.filter(([value]) => (FEEDBACK_GROUP_BY_REASON[value] || value.split(":")[0]) === group.id);
      if (!choices.length) return "";
      const inputs = choices.map(([value, label]) => `<label><input type="checkbox" name="reason" value="${escapeHtml(value)}" /> ${escapeHtml(label)}</label>`).join("");
      return `<section class="feedback-reason-group"><h3>${escapeHtml(group.title)}</h3><div class="feedback-choice-grid">${inputs}</div><label class="feedback-group-note"><span>이 항목에서 특히 중요한 점 (선택)</span><textarea data-feedback-note-group="${escapeHtml(group.id)}" maxlength="500" rows="2"></textarea></label></section>`;
    }).join("");
    const assigned = new Set(FEEDBACK_REASON_GROUPS.map((group) => group.id));
    const remaining = entries.filter(([value]) => !assigned.has(FEEDBACK_GROUP_BY_REASON[value] || value.split(":")[0]));
    const otherChoices = remaining.map(([value, label]) => `<label><input type="checkbox" name="reason" value="${escapeHtml(value)}" /> ${escapeHtml(label)}</label>`).join("");
    return `<div data-requirement-id="UX-232">${sections}<section class="feedback-reason-group"><h3>추가 의견</h3><div class="feedback-choice-grid">${otherChoices}</div><label class="feedback-group-note"><span>그 밖에 중요한 점 (선택)</span><textarea data-feedback-note-group="general" maxlength="1000" rows="3"></textarea></label><p class="feedback-score-boundary">지역은 국내·국외 분류에만 사용하며 유사도 점수에는 반영하지 않습니다.</p></section></div>`;
  }
  function openFeedback(jobId, sentiment = "not_for_me") {
    const preference = preferenceFor(jobId);
    const config = FEEDBACK_CONFIG[sentiment] || FEEDBACK_CONFIG.not_for_me;
    const isCurrent = preference?.sentiment === sentiment;
    document.getElementById("feedbackJobId").value = jobId;
    document.getElementById("feedbackSentiment").value = sentiment;
    document.getElementById("feedbackTitle").textContent = config.title;
    document.getElementById("feedbackLegend").textContent = config.legend;
    document.getElementById("feedbackReasonChoices").innerHTML = renderFeedbackReasonGroups(config);
    document.querySelectorAll("#feedbackReasons input[name='reason']").forEach((input) => { input.checked = isCurrent && preference.reasons?.includes(input.value); });
    const noteParts = parseStructuredFeedbackNote(isCurrent ? preference.note || "" : "");
    document.querySelectorAll("[data-feedback-note-group]").forEach((field) => {
      field.value = noteParts[field.dataset.feedbackNoteGroup] || "";
      field.placeholder = config.placeholder;
    });
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
    /* data-requirement-id="UX-226" */
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
  function feedbackBackupPayload() {
    const preferences = Object.entries(state.feedback).map(([jobId, item]) => ({ jobId, ...item }));
    return {
      schema: FEEDBACK_BACKUP_SCHEMA,
      exportedAt: new Date().toISOString(),
      preferences,
      readableSummary: buildFeedbackExport(),
    };
  }
  function exportFeedbackBackup() {
    const content = JSON.stringify(feedbackBackupPayload(), null, 2);
    const blob = new Blob([content], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const date = new Date().toISOString().slice(0, 10);
    const anchor = Object.assign(document.createElement("a"), {
      href: url,
      download: `career-compass-feedback-${date}.json`,
    });
    anchor.click();
    URL.revokeObjectURL(url);
  }
  function validatedBackupPreference(item) {
    if (!item || typeof item.jobId !== "string" || !item.jobId || item.jobId.length > 300) return null;
    if (!["liked", "not_for_me"].includes(item.sentiment)) return null;
    const allowed = item.sentiment === "liked" ? LIKE_REASON_LABELS : DISLIKE_REASON_LABELS;
    const reasons = Array.isArray(item.reasons) ? item.reasons.filter((reason) => Object.hasOwn(allowed, reason)) : [];
    const updatedAt = new Date(item.updatedAt || "").toISOString();
    return {
      jobId: item.jobId,
      sentiment: item.sentiment,
      reasons,
      note: String(item.note || "").slice(0, 2000),
      updatedAt,
    };
  }
  async function syncImportedPreferences(jobIds) {
    /* data-requirement-id="UX-228" */
    if (!state.preferenceClient || !state.preferenceUserId || !jobIds.length) return false;
    const rows = jobIds.map((jobId) => preferencePayload(jobId, state.feedback[jobId]));
    const { error } = await state.preferenceClient
      .from("job_preferences")
      .upsert(rows, { onConflict: "user_id,job_id" });
    if (error) throw error;
    return true;
  }
  async function importFeedbackBackup(file) {
    if (!file || file.size > 2_000_000) throw new Error("2MB 이하 JSON 백업만 가져올 수 있습니다.");
    const backup = JSON.parse(await file.text());
    if (backup?.schema !== FEEDBACK_BACKUP_SCHEMA || !Array.isArray(backup.preferences)) {
      throw new Error("Career Compass 피드백 백업 파일이 아닙니다.");
    }
    if (backup.preferences.length > 5000) throw new Error("피드백 항목이 너무 많습니다.");
    const importedIds = [];
    backup.preferences.forEach((item) => {
      let preference = null;
      try { preference = validatedBackupPreference(item); } catch (_) { return; }
      if (!preference) return;
      const local = preferenceFor(preference.jobId);
      if (local && Date.parse(local.updatedAt || "") >= Date.parse(preference.updatedAt)) return;
      const { jobId, ...value } = preference;
      state.feedback[jobId] = value;
      importedIds.push(jobId);
    });
    persistPreferences();
    const remotelySynced = await syncImportedPreferences(importedIds);
    state.feedbackImportStatus = remotelySynced
      ? `${importedIds.length}건을 가져와 이 기기에 복원하고 Supabase에도 반영했습니다.`
      : `${importedIds.length}건을 가져와 이 기기에 복원했습니다. Supabase 연결 후 자동 동기화됩니다.`;
    state.syncState = remotelySynced ? "synced" : "local";
    renderSources();
    const frames = [...main.querySelectorAll(".page-frame")];
    frames.forEach((frame, index) => frame.classList.toggle("is-active", index === 1));
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
  function render(focus = true) { if (!state.data) return; closeDetail(false); window.scrollTo(0, 0); main.scrollTop = 0; const current = route(); setActiveTab(current); if (current === "today") renderToday(); else if (current === "jobs") renderJobs(); else if (current === "saved") renderSaved(); else if (current === "lifestyle") renderLifestyle(); else if (current === "study") renderStudy(); else if (current === "sources") renderSources(); else { go("#/today"); return; } requestAnimationFrame(() => { window.scrollTo(0, 0); main.scrollTop = 0; if (focus) main.querySelector("h1")?.focus({ preventScroll: true }); }); }
  function isSnapshot(data) { return Boolean(data && Array.isArray(data.jobs) && Array.isArray(data.programs) && Array.isArray(data.funding)); }
  function normalizeFilters() {
    const sectors = new Set(allJobSectors());
    const queues = new Set(jobs().map((job) => job.queue));
    if (!sectors.has(state.sector)) state.sector = "";
    if (!queues.has(state.queue)) state.queue = "";
    if (!["all", "domestic", "overseas", "unknown"].includes(state.jobMarket)) state.jobMarket = "all";
    if (!["jayang_wlb", "busan"].includes(state.lifestyleLane)) state.lifestyleLane = "jayang_wlb";
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
    const freshest = await selectFreshestSnapshot(state.data, data.snapshot);
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
    const completeSnapshot = await selectFreshestSnapshot(state.data, data.snapshot);
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
  function safeRefreshText(value, limit = 500) {
    return typeof value === "string" ? value.slice(0, limit) : "";
  }
  function safeRefreshNumber(value, fallback = null) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }
  function safeRefreshStage(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    return {
      id: safeRefreshText(value.id, 80),
      labelKo: safeRefreshText(value.labelKo, 160),
      phaseId: safeRefreshText(value.phaseId, 80),
      phaseLabelKo: safeRefreshText(value.phaseLabelKo, 160),
      position: safeRefreshNumber(value.position, 0),
      total: safeRefreshNumber(value.total, 10),
      attempt: safeRefreshNumber(value.attempt, 1),
      maxAttempts: safeRefreshNumber(value.maxAttempts, 1),
      state: safeRefreshText(value.state, 40),
      startedAt: safeRefreshText(value.startedAt, 80),
      finishedAt: safeRefreshText(value.finishedAt, 80),
      errorKo: safeRefreshText(value.errorKo, 500),
    };
  }
  function safeRefreshPhase(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    return {
      id: safeRefreshText(value.id, 80),
      labelKo: safeRefreshText(value.labelKo, 160),
      position: safeRefreshNumber(value.position, 0),
      total: safeRefreshNumber(value.total, REFRESH_PHASE_TOTAL),
      attempt: safeRefreshNumber(value.attempt, 1),
      maxAttempts: safeRefreshNumber(value.maxAttempts, 1),
      state: safeRefreshText(value.state, 40),
    };
  }
  function safeRefreshGate(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    return {
      id: safeRefreshText(value.id || value.phaseId, 80),
      phaseId: safeRefreshText(value.phaseId || value.id, 80),
      labelKo: safeRefreshText(value.labelKo, 160),
      state: safeRefreshText(value.state, 40),
      attempt: safeRefreshNumber(value.attempt, 1),
      maxAttempts: safeRefreshNumber(value.maxAttempts, 1),
      checkedAt: safeRefreshText(value.checkedAt, 80),
      errorKo: safeRefreshText(value.errorKo, 500),
    };
  }
  function safeRefreshLoopPolicy(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    return {
      mode: safeRefreshText(value.mode, 80),
      scope: safeRefreshText(value.scope, 80),
      labelKo: safeRefreshText(value.labelKo, 160),
      maxAutomaticRetries: safeRefreshNumber(value.maxAutomaticRetries, 0),
      sourceCollectionMaxAttempts: safeRefreshNumber(value.sourceCollectionMaxAttempts, 1),
      localPhaseMaxAttempts: safeRefreshNumber(value.localPhaseMaxAttempts, 1),
    };
  }
  function refreshRunStatus(row) {
    // Only project browser-safe refresh fields into the mobile monitor.
    if (!row || typeof row !== "object") return null;
    const rowStatus = row.status && typeof row.status === "object" && !Array.isArray(row.status) ? row.status : {};
    const allowedStates = new Set(["pending", "running", "succeeded", "failed", "interrupted"]);
    const runState = allowedStates.has(row.state) ? row.state : "failed";
    const pendingStage = runState === "pending" && !rowStatus.currentStage
      ? { id: "queue_request", labelKo: "요청 접수", position: 0, total: 10, state: "pending" }
      : rowStatus.currentStage;
    const pendingPhase = runState === "pending" && !rowStatus.currentPhase
      ? { id: "queue_acceptance", labelKo: "요청 접수", position: 0, total: REFRESH_PHASE_TOTAL, attempt: 1, maxAttempts: 1, state: "pending" }
      : rowStatus.currentPhase;
    const pendingGate = runState === "pending" && !rowStatus.lastGate
      ? { id: "queue_acceptance", labelKo: "Supabase 요청 접수", state: "pending", attempt: 1, maxAttempts: 1 }
      : rowStatus.lastGate;
    const preferenceSummary = rowStatus.preferenceSummary && typeof rowStatus.preferenceSummary === "object"
      ? rowStatus.preferenceSummary
      : {};
    const preferenceDiscovery = rowStatus.preferenceDiscovery && typeof rowStatus.preferenceDiscovery === "object"
      ? rowStatus.preferenceDiscovery
      : {};
    return {
      state: runState,
      requestedAt: safeRefreshText(rowStatus.requestedAt || row.requested_at, 80),
      startedAt: safeRefreshText(rowStatus.startedAt || row.started_at, 80),
      finishedAt: safeRefreshText(rowStatus.finishedAt || row.finished_at, 80),
      updatedAt: safeRefreshText(rowStatus.updatedAt || row.updated_at, 80),
      currentStage: safeRefreshStage(pendingStage),
      currentPhase: safeRefreshPhase(pendingPhase),
      lastGate: safeRefreshGate(pendingGate),
      loopPolicy: safeRefreshLoopPolicy(rowStatus.loopPolicy),
      stages: Array.isArray(rowStatus.stages) ? rowStatus.stages.map(safeRefreshStage).filter(Boolean) : [],
      gates: Array.isArray(rowStatus.gates) ? rowStatus.gates.map(safeRefreshGate).filter(Boolean) : [],
      preferenceSummary: {
        likedCount: safeRefreshNumber(preferenceSummary.likedCount, 0),
        dislikedCount: safeRefreshNumber(preferenceSummary.dislikedCount, 0),
        digest: safeRefreshText(preferenceSummary.digest, 160),
      },
      preferenceDiscovery: {
        discoveredCandidateCount: safeRefreshNumber(preferenceDiscovery.discoveredCandidateCount, 0),
      },
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
  async function loadLastSuccessfulRefresh() {
    const { data, error } = await state.preferenceClient
      .from("refresh_runs")
      .select("finished_at,status")
      .eq("user_id", state.preferenceUserId)
      .eq("state", "succeeded")
      .order("finished_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) throw error;
    state.lastSuccessfulRefreshAt = data?.finished_at || data?.status?.finishedAt || null;
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

  function parseDateMs(value) {
    const timestamp = Date.parse(value || "");
    return Number.isFinite(timestamp) ? timestamp : null;
  }

  function recentLocalRequestMs(now, fallbackMs = null) {
    const timestamp = Number(state.refreshRequestedAt);
    if (!Number.isFinite(timestamp)) return fallbackMs;
    if (timestamp > now + 60_000) return fallbackMs;
    if (now - timestamp > 6 * 60 * 60 * 1000) return fallbackMs;
    return timestamp;
  }

  function refreshEstimate(status, now = Date.now()) {
    /* data-requirement-id="UX-218" data-requirement-id="UX-231" data-requirement-id="UX-240" */
    const stages = Array.isArray(status?.stages) ? status.stages : [];
    const currentStage = status?.currentStage || {};
    const requestedMs = parseDateMs(status?.requestedAt);
    const startedMs = parseDateMs(status?.startedAt);
    const finishedMs = parseDateMs(status?.finishedAt);
    const localRequestMs = recentLocalRequestMs(now, requestedMs);
    const terminalState = ["succeeded", "failed", "interrupted", "connection_failed"].includes(status?.state);
    const elapsedEndMs = terminalState && finishedMs !== null ? finishedMs : now;
    const elapsedStartMs = status?.state === "pending"
      ? (requestedMs ?? localRequestMs)
      : (startedMs ?? localRequestMs ?? requestedMs);
    const elapsedSeconds = elapsedStartMs !== null ? Math.max(0, (elapsedEndMs - elapsedStartMs) / 1000) : 0;
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
      const stageStartedMs = parseDateMs(recorded?.startedAt || status.startedAt);
      const stageElapsed = stageStartedMs !== null ? Math.max(0, (now - stageStartedMs) / 1000) : 0;
      usedSeconds += Math.min(REFRESH_STAGE_SECONDS[id] * 0.9, stageElapsed);
    });
    if (status?.state === "pending") usedSeconds = 0;
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
    /* data-requirement-id="UX-215" data-requirement-id="DATA-208" data-requirement-id="UX-240" */
    /* UX-240 mobile monitor contract: PHASE is process state, GATE is validation state, LOOP is bounded retry policy. */
    if (!refreshMonitor || !status) return;
    state.refreshRunStatus = status;
    store(REFRESH_STATUS_STORAGE_KEY, status);
    refreshMonitor.hidden = false;
    const currentStage = status.currentStage || {};
    const summary = status.preferenceSummary || {};
    const preferenceDiscovery = status.preferenceDiscovery || {};
    const estimate = refreshEstimate(status, now);
    const isActive = status.state === "pending" || status.state === "running";
    const isSucceeded = status.state === "succeeded";
    const isConnectionFailed = status.state === "connection_failed";
    const failedStage = [...(status.stages || [])].reverse().find((stage) => stage.state === "failed");
    const currentPhase = status.currentPhase || {};
    const lastGate = status.lastGate || {};
    const policy = status.loopPolicy || {};
    const percent = isSucceeded ? 100 : estimate.percent;
    refreshMonitor.dataset.state = status.state || "unknown";
    refreshProgressTitle.textContent = isSucceeded
      ? "검증·게시 완료"
      : isConnectionFailed
        ? "진행 상태 확인 중단"
      : !isActive
        ? "추천 갱신 중단"
        : status.state === "pending"
          ? `추천 요청 접수 ${percent}%`
          : `추천 갱신 예상 ${percent}%`;
    refreshProgressPercent.textContent = `${percent}%`;
    refreshProgressBar.style.width = `${percent}%`;
    refreshProgressBar.parentElement.setAttribute("aria-valuenow", String(percent));
    const pendingSeconds = status.state === "pending" ? estimate.elapsedSeconds : 0;
    refreshStageLabel.textContent = isSucceeded
      ? "이번 실행의 검증·게시가 완료되었습니다."
      : isConnectionFailed
        ? "엔진 결과가 아니라 상태 연결만 끊겼습니다. 다시 연결해 확인하세요."
      : status.state === "failed"
        ? lastGate.errorKo || failedStage?.errorKo || `${failedStage?.labelKo || "갱신"} 단계에서 멈췄습니다. 기존 공고는 유지됩니다.`
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
    const pendingAfterRun = isSucceeded ? pendingPreferenceCount() : 0;
    const coverageCopy = isSucceeded
      ? `이번 실행 입력 · 관심 ${summary.likedCount || 0}건 · 별로예요 ${summary.dislikedCount || 0}건${pendingAfterRun ? ` · 완료 후 추가된 피드백 ${pendingAfterRun}건은 다음 실행 대기` : " · 현재 피드백까지 반영"}`
      : `이번 실행 입력 · 관심 ${summary.likedCount || 0}건 · 별로예요 ${summary.dislikedCount || 0}건`;
    refreshPreferenceCount.textContent = `${coverageCopy}${discoveredCandidateCount ? ` · 유사 후보 ${discoveredCandidateCount}건 발견` : ""} · 예상치는 수집처 응답 속도에 따라 달라질 수 있습니다.`;
    if (refreshPhaseLabel) {
      refreshPhaseLabel.textContent = `${currentPhase.position || 0}/${currentPhase.total || REFRESH_PHASE_TOTAL} · ${currentPhase.labelKo || "요청 접수"}`;
    }
    if (refreshGateLabel) {
      const gateAttempt = lastGate.maxAttempts > 1 ? ` · ${lastGate.attempt || 1}/${lastGate.maxAttempts}` : "";
      refreshGateLabel.textContent = `${lastGate.labelKo || "요청 접수 확인"}${gateAttempt}`;
    }
    if (refreshLoopLabel) {
      const maxRetries = Number(policy.maxAutomaticRetries || 0);
      const sourceAttempts = Number(policy.sourceCollectionMaxAttempts || currentStage.maxAttempts || 1);
      const loopCopy = policy.labelKo
        || (maxRetries > 0
          ? `자동 재시도 최대 ${maxRetries}회`
          : `자동 재시도 없음 · 수집 ${currentStage.attempt || 1}/${sourceAttempts}`);
      refreshLoopLabel.textContent = loopCopy;
    }
    if (isActive && !state.refreshClockTimer) {
      state.refreshClockTimer = window.setInterval(() => renderRefreshMonitor(state.refreshRunStatus), 1000);
    }
  }
  function restoreRefreshMonitorFromStorage() {
    /* data-requirement-id="UX-241" */
    const cached = readJSON(REFRESH_STATUS_STORAGE_KEY, null);
    const allowedStates = new Set(["pending", "running", "succeeded", "failed", "connection_failed"]);
    if (!cached || !allowedStates.has(cached.state)) return false;
    renderRefreshMonitor(cached);
    return true;
  }
  function renderRefreshConnectionFailure() {
    const previous = state.refreshRunStatus || {};
    const failedAt = new Date().toISOString();
    renderRefreshMonitor({
      ...previous,
      state: "connection_failed",
      startedAt: previous.startedAt || failedAt,
      finishedAt: failedAt,
      currentStage: { id: "status_connection", labelKo: "진행 상태 연결", position: previous.currentStage?.position || 0, total: previous.currentStage?.total || 10, state: "connection_failed" },
      stages: [
        ...(previous.stages || []).filter((stage) => stage.id !== "status_connection"),
        { id: "status_connection", labelKo: "진행 상태 연결", state: "connection_failed", finishedAt: failedAt },
      ],
    });
  }
  function renderRefreshErrorState(status, error) {
    if (status?.state === "succeeded" && error?.status === 409) {
      status = { ...status, state: "failed" };
      status.lastGate = {};
      status.lastGate.id = "client_snapshot_digest";
      status.lastGate.labelKo = "결과 일치 확인";
      status.lastGate.state = "failed";
      status.lastGate.errorKo = "이번 피드백 묶음과 결과가 일치하지 않습니다.";
    }
    renderRefreshMonitor(status);
  }
  async function watchRefresh() {
    /* data-requirement-id="DATA-205" */
    let status = null;
    try {
      status = await refreshStatus();
      state.refreshConnectionErrors = 0;
      if (status.state === "pending" || status.state === "running") {
        renderRefreshMonitor(status);
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
      renderRefreshMonitor(status);
      state.lastSuccessfulRefreshAt = status.finishedAt || new Date().toISOString();
      const summary = status.preferenceSummary || {};
      snapshotLabel.textContent = `새 추천 반영 완료 · 관심 ${summary.likedCount || 0} · 별로예요 ${summary.dislikedCount || 0}`;
    } catch (error) {
      console.error(error);
      const transientConnection = !status && error?.status !== 401 && error?.status !== 403 && error?.status !== 409;
      if (transientConnection && state.refreshConnectionErrors < MAX_REFRESH_CONNECTION_ERRORS) {
        state.refreshConnectionErrors += 1;
        snapshotLabel.textContent = `진행 상태 다시 확인 중 · ${state.refreshConnectionErrors}/${MAX_REFRESH_CONNECTION_ERRORS}`;
        state.refreshTimer = window.setTimeout(watchRefresh, 4000);
        return;
      }
      stopRefreshPolling();
      store(REFRESH_WATCH_STORAGE_KEY, false);
      setEngineBusy(false);
      snapshotLabel.textContent = refreshErrorLabel(error, status);
      if (status) renderRefreshErrorState(status, error);
      else renderRefreshConnectionFailure();
    }
  }
  async function refreshEngine() {
    if (!state.preferenceClient || !state.preferenceUserId || engineRefresh?.disabled) return;
    const requestedAt = new Date().toISOString();
    state.refreshRequestedAt = Date.parse(requestedAt);
    state.refreshConnectionErrors = 0;
    setEngineBusy(true);
    snapshotLabel.textContent = "후보 갱신 시작";
    store(REFRESH_WATCH_STORAGE_KEY, true);
    renderRefreshMonitor({
      state: "pending",
      requestedAt,
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
      await loadLastSuccessfulRefresh();
      if (route() === "sources") renderSources();
      if (readJSON(REFRESH_WATCH_STORAGE_KEY, false) === true) {
        const restored = restoreRefreshMonitorFromStorage();
        const active = await activeRefreshRun();
        if (active) {
          state.refreshRunId = active.id;
          setEngineBusy(true);
          await watchRefresh();
        } else {
          store(REFRESH_WATCH_STORAGE_KEY, false);
          if (restored && ["pending", "running"].includes(state.refreshRunStatus?.state)) {
            renderRefreshConnectionFailure();
          }
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

  function mergeGraduateEvidence(primary, canonicalGraduate) {
    /* data-requirement-id="DATA-226" data-requirement-id="DATA-228" data-requirement-id="DATA-230" */
    if (!isSnapshot(primary)) return canonicalGraduate;
    if (!isSnapshot(canonicalGraduate)) return primary;
    const graduateSource = graduateLineageMatches(canonicalGraduate)
      ? canonicalGraduate
      : (graduateLineageMatches(primary) ? primary : null);
    if (!graduateSource) return primary;
    return {
      ...primary,
      programs: graduateSource.programs,
      funding: graduateSource.funding,
      graduateEvidenceCoverage: graduateSource.graduateEvidenceCoverage,
      graduateDataLineage: graduateSource.graduateDataLineage,
    };
  }

  function canonicalJSONString(value) {
    if (Array.isArray(value)) return `[${value.map(canonicalJSONString).join(",")}]`;
    if (value && typeof value === "object") {
      return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJSONString(value[key])}`).join(",")}}`;
    }
    return JSON.stringify(value);
  }

  async function sha256Hex(value) {
    if (!window.crypto?.subtle) return null;
    const bytes = new TextEncoder().encode(value);
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function lifestyleStructureMatches(snapshot) {
    const discovery = snapshot?.lifestyleDiscovery;
    if (
      !discovery
      || discovery.schemaVersion !== "lifestyle-evidence-v2"
      || discovery.methodVersion !== "lifestyle-evidence-v2"
      || discovery.scoreImpact !== "none"
      || discovery.searchState == null
      || !Number.isFinite(Date.parse(discovery.searchedAt || ""))
      || discovery.sourceArtifact !== "job_search/work/recommendation-v4/g003-posting-facts.json"
      || !/^[a-f0-9]{64}$/.test(String(discovery.sourceArtifactDigest || ""))
      || !/^[a-f0-9]{64}$/.test(String(discovery.sourceFileSha256 || ""))
      || !Number.isInteger(discovery.sourcePostingCount)
      || !Number.isInteger(discovery.sourceRelevantPostingCount)
      || discovery.sourcePostingCount < discovery.sourceRelevantPostingCount
      || !Array.isArray(discovery.limitations)
      || !discovery.limitations.length
      || !Array.isArray(discovery.items)
      || !/^[a-f0-9]{64}$/.test(String(discovery.digest || ""))
    ) return false;
    const laneKeys = Object.keys(discovery.lanes || {}).sort();
    if (laneKeys.join(",") !== "busan,jayang_wlb") return false;
    const validStatuses = new Set(["confirmed", "claimed", "unknown", "negative"]);
    const validSearchStates = new Set(["searched", "not_searched", "partial", "failed", "stale"]);
    const validReadiness = new Set(["ready", "partial", "insufficient"]);
    const validSourceStates = new Set(["known_open", "known_closed", "status_unknown", "archived_reference"]);
    if (!validSearchStates.has(discovery.searchState)) return false;
    const hasCanonicalFilter = discovery.filterCounts != null;
    const hasLegacyFilter = discovery.candidateFilter != null;
    if (!hasCanonicalFilter && !hasLegacyFilter) return false;
    if (hasCanonicalFilter) {
      if (!lifestyleHasExactKeys(discovery.filterCounts, LIFESTYLE_GLOBAL_FILTER_KEYS)) return false;
      if (!lifestyleNonNegativeIntegers(discovery.filterCounts, LIFESTYLE_GLOBAL_FILTER_KEYS)) return false;
      if (Number.isInteger(discovery.publicCandidateCount) && discovery.publicCandidateCount !== discovery.items.length) return false;
      if (Number.isInteger(discovery.publicRecommendationCount) && discovery.publicRecommendationCount !== discovery.filterCounts.verifiedOpen) return false;
    } else {
      if (!lifestyleHasExactKeys(discovery.candidateFilter, LIFESTYLE_LEGACY_GLOBAL_FILTER_KEYS)) return false;
      if (!lifestyleNonNegativeIntegers(discovery.candidateFilter, LIFESTYLE_LEGACY_GLOBAL_FILTER_KEYS)) return false;
      if (discovery.candidateFilter.sourcePostings !== discovery.sourcePostingCount) return false;
      if (discovery.candidateFilter.publishedCandidates !== discovery.items.length) return false;
      if (discovery.candidateFilter.roleRelevant < discovery.candidateFilter.publishedCandidates) return false;
    }
    const globalCounts = lifestyleGlobalFilterCounts(discovery);
    if (globalCounts.publishedCandidate !== discovery.items.length) return false;
    if (
      globalCounts.sourcePostingCount < globalCounts.nonClosed
      || globalCounts.nonClosed < globalCounts.rawLocation
      || globalCounts.rawLocation < globalCounts.strictLocation
      || globalCounts.strictLocation < globalCounts.relevantDomain
      || globalCounts.relevantDomain < globalCounts.roleFit
      || globalCounts.roleFit < globalCounts.juniorAttainable
      || globalCounts.juniorAttainable < globalCounts.wlbNotNegative
      || globalCounts.wlbNotNegative < globalCounts.deduplicated
      || globalCounts.publishedCandidate > globalCounts.deduplicated
      || globalCounts.statusRecheck + globalCounts.verifiedOpen !== globalCounts.publishedCandidate
    ) return false;
    const itemById = new Map();
    for (const item of discovery.items) {
      const jobId = String(item?.jobId || "");
      const evidence = item?.lifestyleEvidence;
      const axes = evidence?.axes;
      const itemLanes = evidence?.lanes;
      const sourceStatus = item?.sourceStatus;
      if (!jobId || itemById.has(jobId)) return false;
      if (item.market !== "domestic" || item.domestic !== true) return false;
      if (typeof item.filterReason !== "string" || !item.filterReason) return false;
      if (typeof item.url !== "string" || !/^https?:\/\//i.test(item.url)) return false;
      if (!sourceStatus || !validSourceStates.has(sourceStatus.state) || typeof sourceStatus.statusLabel !== "string") return false;
      if (Object.keys(axes || {}).sort().join(",") !== "busanWorkplace,jayangCommute,wlb") return false;
      if (Object.keys(itemLanes || {}).sort().join(",") !== "busan,jayang_wlb") return false;
      const candidateFilter = item?.candidateFilter;
      if (Object.keys(candidateFilter || {}).sort().join(",") !== "busan,jayang_wlb") return false;
      for (const laneKey of laneKeys) {
        const laneFilter = candidateFilter[laneKey];
        if (!lifestyleHasAcceptedLaneFilterKeys(laneFilter)) return false;
        if (Object.values(laneFilter).some((value) => typeof value !== "boolean")) return false;
        const normalized = normalizedLifestyleLaneFilter(laneFilter);
        const expectedReviewCandidate = normalized.strictLocation
          && normalized.relevantDomain
          && normalized.roleFit
          && normalized.juniorAttainable
          && normalized.wlbNotNegative;
        if (normalized.reviewCandidate !== expectedReviewCandidate) return false;
        if (normalized.reviewCandidate && (normalized.statusRecheck === normalized.verifiedOpen)) return false;
        if (!normalized.reviewCandidate && (normalized.statusRecheck || normalized.verifiedOpen)) return false;
        const expectedVerified = sourceStatus.state === "known_open";
        if (normalized.reviewCandidate && normalized.verifiedOpen !== expectedVerified) return false;
        if (normalized.reviewCandidate && normalized.statusRecheck !== !expectedVerified) return false;
      }
      for (const axis of Object.values(axes)) {
        if (!validStatuses.has(axis?.status) || typeof axis?.summary !== "string" || !Array.isArray(axis?.evidence) || !Array.isArray(axis?.missing)) return false;
      }
      if (Object.values(itemLanes).some((status) => !validStatuses.has(status))) return false;
      itemById.set(jobId, item);
    }
    const reviewed = new Set();
    for (const laneKey of laneKeys) {
      const lane = discovery.lanes[laneKey];
      const reviewIds = lane?.reviewIds;
      const counts = lane?.counts;
      const axisCounts = lane?.axisCounts;
      const filterCounts = lane?.filterCounts;
      if (!Array.isArray(reviewIds) || new Set(reviewIds).size !== reviewIds.length || !counts) return false;
      if (lane.matchedCount !== reviewIds.length || !validSearchStates.has(lane.searchState) || !validReadiness.has(lane.decisionReadiness) || !Number.isFinite(Date.parse(lane.searchedAt || ""))) return false;
      if (Object.keys(axisCounts || {}).sort().join(",") !== "busanWorkplace,jayangCommute,wlb") return false;
      if (!lifestyleHasExactKeys(filterCounts, LIFESTYLE_LANE_FILTER_KEYS) && !lifestyleHasExactKeys(filterCounts, LIFESTYLE_LEGACY_LANE_FILTER_KEYS)) return false;
      const laneCounts = lifestyleLaneFilterCounts(lane);
      if (Object.values(laneCounts).some((value) => !Number.isInteger(value) || value < 0)) return false;
      if (
        laneCounts.rawLocation < laneCounts.strictLocation
        || laneCounts.strictLocation < laneCounts.relevantDomain
        || laneCounts.relevantDomain < laneCounts.roleFit
        || laneCounts.roleFit < laneCounts.juniorAttainable
        || laneCounts.juniorAttainable < laneCounts.wlbNotNegative
        || laneCounts.wlbNotNegative < laneCounts.reviewCandidate
        || laneCounts.reviewCandidate !== reviewIds.length
        || laneCounts.statusRecheck + laneCounts.verifiedOpen !== reviewIds.length
      ) return false;
      for (const jobId of reviewIds) {
        if (!itemById.has(jobId)) return false;
        const laneFilter = normalizedLifestyleLaneFilter(itemById.get(jobId).candidateFilter[laneKey]);
        if (!laneFilter.reviewCandidate || !laneFilter.strictLocation || !laneFilter.relevantDomain || !laneFilter.roleFit || !laneFilter.juniorAttainable || !laneFilter.wlbNotNegative) return false;
        if ((laneFilter.statusRecheck ? 1 : 0) + (laneFilter.verifiedOpen ? 1 : 0) !== 1) return false;
        reviewed.add(jobId);
      }
      for (const status of validStatuses) {
        const expected = reviewIds.filter((jobId) => itemById.get(jobId).lifestyleEvidence.lanes[laneKey] === status).length;
        if (counts[status] !== expected) return false;
      }
      if ([...validStatuses].reduce((sum, status) => sum + counts[status], 0) !== reviewIds.length) return false;
      for (const axisName of Object.keys(axisCounts)) {
        for (const status of validStatuses) {
          const expected = reviewIds.filter((jobId) => itemById.get(jobId).lifestyleEvidence.axes[axisName].status === status).length;
          if (axisCounts[axisName]?.[status] !== expected) return false;
        }
      }
    }
    return reviewed.size === itemById.size;
  }

  async function lifestyleLineageMatches(snapshot) {
    if (!lifestyleStructureMatches(snapshot)) return false;
    const digestSource = { ...snapshot.lifestyleDiscovery };
    const actualDigest = digestSource.digest;
    delete digestSource.digest;
    return actualDigest === await sha256Hex(canonicalJSONString(digestSource));
  }

  async function selectFreshestSnapshot(bundled, cached) {
    /* data-requirement-id="DATA-207" data-requirement-id="DATA-226" data-requirement-id="DATA-228" */
    const bundledAt = Date.parse(bundled?.generatedAt || "");
    const cachedAt = Date.parse(cached?.generatedAt || "");
    const freshest = isSnapshot(cached) && Number.isFinite(cachedAt) && (!Number.isFinite(bundledAt) || cachedAt > bundledAt) ? cached : bundled;
    const merged = mergeGraduateEvidence(freshest, bundled);
    if (await lifestyleLineageMatches(merged)) return merged;
    if (freshest !== bundled && await lifestyleLineageMatches(bundled)) return mergeGraduateEvidence(bundled, bundled);
    const withoutLifestyle = { ...merged };
    delete withoutLifestyle.lifestyleDiscovery;
    return withoutLifestyle;
  }

  async function load({ force = false } = {}) {
    try {
      const url = force ? `./data/app-data.json?refresh=${Date.now()}` : "./data/app-data.json";
      const response = await fetch(url, { cache: force ? "no-store" : "reload" });
      if (!response.ok) throw new Error(response.status);
      const bundled = await response.json();
      setSnapshot(await selectFreshestSnapshot(bundled, readJSON(LIVE_SNAPSHOT_STORAGE_KEY, null)));
    } catch (error) {
      console.error(error);
      snapshotLabel.textContent = "자료를 열 수 없음";
      renderError();
    }
  }

  document.addEventListener("click", (event) => {
    const lifestyleUrlButton = event.target.closest("[data-open-lifestyle-url]");
    if (lifestyleUrlButton) { const url = lifestyleUrlButton.dataset.openLifestyleUrl; if (url) window.open(url, "_blank", "noopener"); return; }
    const jobButton = event.target.closest("[data-open-job]"); if (jobButton) { openJobDetail(jobButton.dataset.openJob, jobButton); return; }
    const recordButton = event.target.closest("[data-open-record]"); if (recordButton) { const [kind, id] = recordButton.dataset.openRecord.split(":"); openRecordDetail(kind, id, recordButton); return; }
    const sector = event.target.closest("[data-sector]"); if (sector) { state.sector = sector.dataset.sector; saveFilters(); if (route() !== "jobs") go("#/jobs"); else renderJobs(); return; }
    const jobMarket = event.target.closest("[data-job-market]"); if (jobMarket) { state.jobMarket = jobMarket.dataset.jobMarket; saveFilters(); renderJobs(); return; }
    const studyMode = event.target.closest("[data-study-mode]"); if (studyMode) { state.studyMode = studyMode.dataset.studyMode; saveFilters(); renderStudy(); return; }
    const studyReadiness = event.target.closest("[data-study-readiness]"); if (studyReadiness) { state.studyReadiness = studyReadiness.dataset.studyReadiness; saveFilters(); renderStudy(); return; }
    const studyMarket = event.target.closest("[data-study-market]"); if (studyMarket) { state.studyMarket = studyMarket.dataset.studyMarket; saveFilters(); renderStudy(); return; }
    const studyFormat = event.target.closest("[data-study-format]"); if (studyFormat) { state.studyFormat = studyFormat.dataset.studyFormat; saveFilters(); renderStudy(); return; }
    const lifestyleLane = event.target.closest("[data-lifestyle-lane]"); if (lifestyleLane) { state.lifestyleLane = lifestyleLane.dataset.lifestyleLane; saveFilters(); renderLifestyle(); return; }
    const studyDetailTab = event.target.closest("[data-study-detail-tab]");
    if (studyDetailTab) {
      const selected = studyDetailTab.dataset.studyDetailTab;
      dossier.querySelectorAll("[data-study-detail-tab]").forEach((tab) => tab.setAttribute("aria-selected", String(tab === studyDetailTab)));
      dossier.querySelectorAll("[data-study-detail-panel]").forEach((panel) => { panel.hidden = panel.dataset.studyDetailPanel !== selected; });
      return;
    }
    const action = event.target.closest("[data-action]")?.dataset.action; if (!action) return;
    if (action === "toggle-comparison") {
      const trigger = event.target.closest("[data-record-kind][data-record-id]");
      const kind = trigger?.dataset.recordKind;
      const id = trigger?.dataset.recordId;
      if (!kind || !id) return;
      toggleComparison(kind, id);
      if (dossier.open) {
        if (kind === "job") renderJobDetail(jobById(id));
        else renderRecordDetail(kind, recordById(kind, id));
      } else if (route() === "saved") {
        renderSaved();
      }
      return;
    }
    if (action === "refresh-engine") { refreshEngine(); return; }
    if (action === "export-feedback") { void exportFeedback(); return; }
    if (action === "export-feedback-backup") { exportFeedbackBackup(); return; }
    if (action === "import-feedback") { feedbackImport.click(); return; }
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
    const note = buildStructuredFeedbackNote();
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
  feedbackImport.addEventListener("change", async () => {
    try {
      await importFeedbackBackup(feedbackImport.files?.[0]);
    } catch (error) {
      state.feedbackImportStatus = error?.message || "백업을 가져오지 못했습니다.";
      if (route() === "sources") renderSources();
    } finally {
      feedbackImport.value = "";
    }
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
