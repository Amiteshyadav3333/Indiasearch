// ═══════════════════════════════════════════
//  INDIASEARCH — app.js (Refactored)
// ═══════════════════════════════════════════

const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const LOCAL_API_BASE = "http://127.0.0.1:8000";
const PROD_API_BASES = [
  "https://indiasearch.onrender.com",
  "https://indiasearch-production.up.railway.app"
];
let activeApiBase = isLocalHost ? LOCAL_API_BASE : PROD_API_BASES[0];

// ── Settings State ──
const SETTINGS_STORAGE_KEY = "indiasearchSettings";
let appSettings = {
  safeSearch: localStorage.getItem("safeSearch") || "moderate",
  resultsCount: parseInt(localStorage.getItem("resultsCount") || "10", 10),
  autoPlayVoice: localStorage.getItem("autoPlayVoice") === "true"
};

// ── DOM Refs ──
const searchInput = document.getElementById("searchInput");
const resultsBox = document.getElementById("results");
const aiSummaryBox = document.getElementById("aiSummary");
const micButton = document.getElementById("micButton");
const languageSelect = document.getElementById("languageSelect");
const cameraInput = document.getElementById("cameraInput");
const scanStatus = document.getElementById("scanStatus");

const aiSearchInput = document.getElementById("aiSearchInput");
const searchBoxStandard = document.getElementById("searchBoxStandard");
const searchBoxAi = document.getElementById("searchBoxAi");
const aiPdfPreview = document.getElementById("aiPdfPreview");
const micButtonAi = document.getElementById("micButtonAi");
const mainWrap = document.querySelector(".main-wrap");

const heroSection = document.getElementById("heroSection");
const searchFiltersDiv = document.getElementById("searchFilters");
const trendingContainer = document.getElementById("trendingContainer");
const historyBox = document.getElementById("searchHistory");
const paginationContainer = document.getElementById("pagination");
const siteHeader = document.getElementById("siteHeader");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const aboutSection = document.getElementById("aboutSection");

// ── Clear Search Button (Google-style ✕) ──
function updateClearBtn() {
  if (clearSearchBtn) {
    clearSearchBtn.style.display = searchInput.value.trim() ? "flex" : "none";
  }
}

function clearSearchInput() {
  searchInput.value = "";
  updateClearBtn();
  searchInput.focus();
}

if (searchInput) {
  // Fires on user typing
  searchInput.addEventListener("input", updateClearBtn);
  searchInput.addEventListener("keyup", updateClearBtn);
  searchInput.addEventListener("focus", updateClearBtn);
  searchInput.addEventListener("change", updateClearBtn);

  // Catch programmatic .value = "..." changes (trending clicks, voice, history, etc.)
  const nativeDescriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  Object.defineProperty(searchInput, 'value', {
    get() { return nativeDescriptor.get.call(this); },
    set(val) {
      nativeDescriptor.set.call(this, val);
      updateClearBtn();
    }
  });
}

let advancedMode = false;
let chatHistory = []; // Global chat history for AI Mode

/** ── AI Mode Manager ── **/

function enterAiMode() {
    if (searchBoxStandard) searchBoxStandard.style.display = "none";
    if (searchBoxAi) {
        searchBoxAi.style.display = "flex";
        if (mainWrap) mainWrap.classList.add("ai-active");
        if (aiSearchInput) {
            aiSearchInput.focus();
            if (searchInput && searchInput.value) aiSearchInput.value = searchInput.value;
        }
    }
}

function exitAiModePanel() { exitAiMode(); }

function enterAdvancedSearch() {
    advancedMode = true;
    enterAiMode();
    if (aiSearchInput) aiSearchInput.placeholder = "Advanced AI Search: Only 2-4 verified sources...";
}

function enterNutritionScan() {
    if (resultsBox) resultsBox.innerHTML = "";
    if (aiSummaryBox) aiSummaryBox.innerHTML = "";
    if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
    if (heroSection) heroSection.classList.add("hidden");
    startLiveScan();
}

function exitAiMode() {
    advancedMode = false;
    if (aiSearchInput) aiSearchInput.placeholder = "Puchho jo aapke mann mein hai... (AI Mode)";
    if (searchBoxStandard) searchBoxStandard.style.display = "flex";
    if (searchBoxAi) {
        searchBoxAi.style.display = "none";
        if (mainWrap) mainWrap.classList.remove("ai-active");
    }
    if (searchInput) searchInput.focus();
}

function aiFollowup(question) {
    if (searchInput) searchInput.value = question;
    chatHistory.push({ role: 'user', content: question });
    search(1, true);
}

function generateFollowUps(query) {
    const q = (query || '').toLowerCase();
    if (q.includes('what is') || q.includes('kya hai')) {
        return [`How does ${query} work?`, `${query} examples`, `${query} vs alternatives`];
    } else if (q.includes('how') || q.includes('kaise')) {
        return [`Why is ${query} important?`, `Best way to ${query}`, `${query} tips`];
    } else {
        return [`More about ${query}`, `Latest on ${query}`, `${query} in India`];
    }
}

function autoExpand(t) {
    t.style.height = 'auto';
    t.style.height = (t.scrollHeight) + 'px';
}

function searchAI() {
    if (!aiSearchInput || !aiSearchInput.value.trim()) return;
    const val = aiSearchInput.value.trim();
    if (searchInput) searchInput.value = val;
    chatHistory.push({ role: "user", content: val });
    aiSearchInput.value = "";
    aiSearchInput.style.height = "auto";
    aiSearchInput.focus();
    search(1, true);
}

if (aiSearchInput) {
    aiSearchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            searchAI();
        }
    });
}


let recognition;
let isListening = false;
let activeSpeechButton = null;
let activeSpeechText = "";
let attachedScan = null;

// Guest-only session state for search context and local preferences.
let appState = {
  guestId: localStorage.getItem("guestSession") || `guest_${Math.random().toString(36).substr(2, 9)}`,
  location: JSON.parse(localStorage.getItem("userLocation")) || null,
  locationChoiceMade: localStorage.getItem("locationChoiceMade") === "true"
};

let activeQuery = ""; // Persistent query for pagination and filter switches
let restoringBrowserState = false;

if (!localStorage.getItem("guestSession")) {
  localStorage.setItem("guestSession", appState.guestId);
}

const LANGUAGE_STORAGE_KEY = "indiasearchLanguage";
const LANGUAGE_NAMES = {
  en: "English",
  hi: "Hindi",
  as: "Assamese",
  bn: "Bengali",
  brx: "Bodo",
  doi: "Dogri",
  gu: "Gujarati",
  kn: "Kannada",
  ks: "Kashmiri",
  gom: "Konkani",
  mai: "Maithili",
  ml: "Malayalam",
  mni: "Manipuri",
  mr: "Marathi",
  ne: "Nepali",
  or: "Odia",
  pa: "Punjabi",
  sa: "Sanskrit",
  sat: "Santali",
  sd: "Sindhi",
  ta: "Tamil",
  te: "Telugu",
  ur: "Urdu",
  bho: "Bhojpuri"
};
const UI_TRANSLATIONS = {
  en: {
    title: "IndiaSearch - AI Voice Search Engine",
    placeholder: "Search anything...",
    aiPlaceholder: "Ask anything on your mind... (AI Mode)",
    languageTitle: "Choose your language",
    languageSubtitle: "IndiaSearch will open in your selected language.",
    trending: "Trending in India",
    askAi: "Ask AI",
    visitWebsite: "Visit Website",
    noResults: "No results found",
    filters: { advanced: "Advanced", nutrition: "Nutrition", all: "All", news: "News", images: "Images", videos: "Videos", weather: "Weather", score: "Live Score", stock: "Stock", sarkari: "Sarkari", jobs: "Jobs", mandi: "Mandi", irctc: "IRCTC", aadhaar: "Aadhaar/PAN", jugaad: "Jugaad", courts: "Courts" }
  },
  hi: {
    title: "IndiaSearch - AI वॉइस सर्च इंजन",
    placeholder: "कुछ भी सर्च करें...",
    aiPlaceholder: "जो मन में है पूछें... (AI मोड)",
    languageTitle: "अपनी भाषा चुनें",
    languageSubtitle: "IndiaSearch आपकी चुनी हुई भाषा में खुलेगा।",
    trending: "भारत में ट्रेंडिंग",
    askAi: "AI से पूछें",
    visitWebsite: "वेबसाइट खोलें",
    noResults: "कोई परिणाम नहीं मिला",
    filters: { advanced: "एडवांस्ड", nutrition: "न्यूट्रिशन", all: "सब", news: "समाचार", images: "इमेज", videos: "वीडियो", weather: "मौसम", score: "लाइव स्कोर", stock: "स्टॉक", sarkari: "सरकारी", jobs: "नौकरियां", mandi: "मंडी", irctc: "IRCTC", aadhaar: "आधार/PAN", jugaad: "जुगाड़", courts: "कोर्ट्स" }
  }
};
// ── Auto-detect browser/system language ──
function detectBrowserLanguage() {
  // navigator.language returns e.g. "hi-IN", "en-US", "bn-BD", "ta"
  const browserLang = (navigator.language || navigator.userLanguage || "en").toLowerCase();
  // Extract the primary language code (before the dash)
  const primary = browserLang.split("-")[0];
  
  // Map of browser language codes to our supported codes
  const BROWSER_TO_APP_LANG = {
    en: "en", hi: "hi", as: "as", bn: "bn", gu: "gu", kn: "kn",
    ks: "ks", ml: "ml", mr: "mr", ne: "ne", or: "or", pa: "pa",
    sa: "sa", sd: "sd", ta: "ta", te: "te", ur: "ur",
    bho: "bho", mai: "mai", sat: "sat", mni: "mni", brx: "brx",
    doi: "doi", gom: "gom",
    // Common aliases
    bh: "bho",  // Bhojpuri
    kok: "gom"  // Konkani
  };
  
  return BROWSER_TO_APP_LANG[primary] || BROWSER_TO_APP_LANG[browserLang] || "en";
}

let currentLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY) || detectBrowserLanguage();

function getSearchStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const query = (params.get("q") || "").trim();
  const page = Math.max(1, parseInt(params.get("page") || "1", 10) || 1);
  const filter = params.get("filter") || params.get("type") || "all";
  const aiMode = params.get("ai") === "1" || params.get("ai_mode") === "true";
  return { query, page, filter, aiMode };
}

function applyFilterActiveState(type = "all") {
  document.querySelectorAll(".filter-pill").forEach(b => b.classList.remove("active"));
  const btn = document.querySelector(`.filter-pill[data-filter="${type}"]`);
  if (btn) btn.classList.add("active");
}

function writeBrowserSearchState({ query, page = 1, filter = "all", aiMode = false }, replace = false) {
  if (restoringBrowserState) return;
  const url = new URL(window.location.href);
  url.search = "";

  if (query) {
    url.searchParams.set("q", query);
    url.searchParams.set("filter", filter || "all");
    if (page > 1) url.searchParams.set("page", String(page));
    if (aiMode) url.searchParams.set("ai", "1");
  }

  const state = query
    ? { view: "search", query, page, filter: filter || "all", aiMode: Boolean(aiMode) }
    : { view: "home" };

  const currentState = history.state || {};
  const sameState = currentState.view === state.view
    && currentState.query === state.query
    && currentState.page === state.page
    && currentState.filter === state.filter
    && currentState.aiMode === state.aiMode;
  const sameUrl = `${window.location.pathname}${window.location.search}` === `${url.pathname}${url.search}`;

  if (sameState && sameUrl) return;
  history[replace ? "replaceState" : "pushState"](state, "", url);
}

function clearHistoryUI() {
  if (confirm("Are you sure you want to clear your local history?")) {
    searchHistory = [];
    localStorage.removeItem("searchHistory");
    renderHistory();
    alert("History cleared!");
  }
}

// ── Header scroll effect ──
window.addEventListener("scroll", () => {
  siteHeader.classList.toggle("scrolled", window.scrollY > 10);
});

// ── Fetch helpers ──
async function fetchWithApiFallback(path, options = {}) {
  const candidates = isLocalHost
    ? [LOCAL_API_BASE, ...PROD_API_BASES]
    : [...PROD_API_BASES];
    
  candidates.sort((x, y) => x === activeApiBase ? -1 : y === activeApiBase ? 1 : 0);
  
  let lastError = null;
  for (const base of candidates) {
    try {
      const r = await fetch(`${base}${path}`, options);
      if (!r.ok && (r.status === 502 || r.status === 503 || r.status === 504 || r.status === 500)) {
         throw new Error(`Server ${base} returned ${r.status}`);
      }
      activeApiBase = base;
      return r;
    } catch (e) { lastError = e; }
  }
  throw lastError || new Error("Failed to reach any backend service");
}

async function apiJsonRequest(path, payload, method = "POST") {
  return fetchWithApiFallback(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : undefined
  });
}

// ═══════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════
function toggleMode() {
  const currentTheme = document.documentElement.getAttribute("data-theme") || 
                       (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}

// Apply saved theme or detect system preference
(function applyTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) {
    document.documentElement.setAttribute("data-theme", saved);
  } else {
    // If no manual setting, listen to system preference
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleSystemTheme = (e) => {
      if (!localStorage.getItem("theme")) {
        document.documentElement.setAttribute("data-theme", e.matches ? "dark" : "light");
      }
    };
    mediaQuery.addEventListener("change", handleSystemTheme);
    // Initial set
    document.documentElement.setAttribute("data-theme", mediaQuery.matches ? "dark" : "light");
  }
})();

// ═══════════════════════════════════════════
// HISTORY
// ═══════════════════════════════════════════
let searchHistory = JSON.parse(localStorage.getItem("searchHistory")) || [];

function renderHistory() {
  if (!historyBox) return;
  if (searchHistory.length === 0) { historyBox.innerHTML = ""; return; }
  historyBox.innerHTML = searchHistory.map(q => `
    <div class="history-chip" onclick="searchInput.value='${q.replace(/'/g, "\\'")}'; search();">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/></svg>
      <span>${q}</span>
      <span class="remove-history" onclick="removeHistory(event,'${q.replace(/'/g, "\\'")}')">✕</span>
    </div>`).join("");
}

function removeHistory(e, query) {
  e.stopPropagation();
  searchHistory = searchHistory.filter(q => q !== query);
  localStorage.setItem("searchHistory", JSON.stringify(searchHistory));
  renderHistory();
}

function saveHistory(query) {
  query = query.trim();
  if (!query) return;
  searchHistory = searchHistory.filter(q => q !== query);
  searchHistory.unshift(query);
  if (searchHistory.length > 6) searchHistory.pop();
  localStorage.setItem("searchHistory", JSON.stringify(searchHistory));
  renderHistory();
}

// ═══════════════════════════════════════════
// TRENDING
// ═══════════════════════════════════════════
const TRENDING_KEYWORDS = [
  "Latest tech jobs in India 2026",
  "Generative AI free courses",
  "Cricket Live Score",
  "Best smartphones under 20000",
  "Python Developer salaries",
  "Top startups in Bangalore"
];

function renderTrending() {
  const grid = document.querySelector(".trending-grid");
  if (!grid) return;
  grid.innerHTML = TRENDING_KEYWORDS.map(k => `
    <div class="trending-item" onclick="searchInput.value='${k}'; search();">
      <span class="trending-icon">📈</span>${k}
    </div>`).join("");
}

// ═══════════════════════════════════════════
// SEARCH FILTERS
// ═══════════════════════════════════════════
let currentFilter = "all";

function setFilter(type) {
  currentFilter = type;
  
  if (type === "advanced") {
      advancedMode = true;
      enterAiMode();
  } else if (type === "nutrition") {
      advancedMode = false;
      enterNutritionScan();
  } else {
      advancedMode = false;
  }

  applyFilterActiveState(type);

  const defaultQueries = {
    news: "latest india news",
    weather: "weather in Delhi",
    score: "live cricket score",
    stock: "reliance stock price",
    sarkari: "latest government schemes and portals",
    jobs: "latest sarkari and private jobs",
    mandi: "latest crop mandi prices",
    irctc: "irctc train running status",
    aadhaar: "aadhaar pan link status",
    jugaad: "plumber electrician mechanic near me",
    courts: "high court supreme court case status",
    nutrition: "calories and nutrition calculator"
  };
  if (searchInput && !searchInput.value.trim()) {
    searchInput.value = activeQuery || defaultQueries[type] || "";
  }

  if (type === "nutrition") {
    return;
  }

  search(1, false);
}

// ═══════════════════════════════════════════
// TRANSLATION
// ═══════════════════════════════════════════
async function translateText(text, targetLang) {
  if (targetLang === "en" || !text) return text;
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
    const r = await fetch(url);
    const d = await r.json();
    return d[0].map(i => i[0]).join("");
  } catch { return text; }
}

function getUiCopy(lang = currentLanguage) {
  return UI_TRANSLATIONS[lang] || UI_TRANSLATIONS.en;
}

async function uiText(key, fallback) {
  const localCopy = getUiCopy();
  if (localCopy[key]) return localCopy[key];
  return translateText(fallback, currentLanguage);
}

function setElementTextKeepingIcon(element, text) {
  if (!element) return;
  [...element.childNodes].forEach(node => {
    if (node.nodeType === Node.TEXT_NODE) node.remove();
  });
  element.appendChild(document.createTextNode(` ${text}`));
}

function setFilterLabel(filter, label) {
  document.querySelectorAll(`.filter-pill[data-filter="${filter}"]`).forEach(button => {
    setElementTextKeepingIcon(button, label);
  });
}

async function applySelectedLanguage(lang = currentLanguage) {
  currentLanguage = lang || "en";
  localStorage.setItem(LANGUAGE_STORAGE_KEY, currentLanguage);
  if (languageSelect) languageSelect.value = currentLanguage;

  document.documentElement.lang = currentLanguage;
  document.documentElement.dir = currentLanguage === "ur" ? "rtl" : "ltr";

  const copy = getUiCopy(currentLanguage);
  document.title = copy.title || await translateText(UI_TRANSLATIONS.en.title, currentLanguage);

  if (searchInput) searchInput.placeholder = copy.placeholder || await translateText(UI_TRANSLATIONS.en.placeholder, currentLanguage);
  if (aiSearchInput) aiSearchInput.placeholder = copy.aiPlaceholder || await translateText(UI_TRANSLATIONS.en.aiPlaceholder, currentLanguage);
  if (languageSelect) languageSelect.title = await uiText("languageTitle", UI_TRANSLATIONS.en.languageTitle);

  document.querySelectorAll("[data-i18n]").forEach(async (el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = await uiText(key, UI_TRANSLATIONS.en[key] || el.textContent);
  });

  const filterLabels = copy.filters || {};
  for (const [filter, englishLabel] of Object.entries(UI_TRANSLATIONS.en.filters)) {
    const translatedLabel = filterLabels[filter] || await translateText(englishLabel, currentLanguage);
    setFilterLabel(filter, translatedLabel);
  }

  document.querySelectorAll(".btn-ai-toggle, .filter-pill.ai-tab").forEach(btn => {
    setElementTextKeepingIcon(btn, copy.askAi || UI_TRANSLATIONS.en.askAi);
  });

  const sectionLabel = document.querySelector(".section-label");
  if (sectionLabel && sectionLabel.closest("#trendingContainer")) {
    setElementTextKeepingIcon(sectionLabel, copy.trending || await translateText(UI_TRANSLATIONS.en.trending, currentLanguage));
  }
}

function showLanguageModalIfNeeded() {
  const modal = document.getElementById("languageModal");
  if (!modal || localStorage.getItem(LANGUAGE_STORAGE_KEY)) return;
  modal.style.display = "flex";
}

function closeLanguageModal() {
  const modal = document.getElementById("languageModal");
  if (modal) modal.style.display = "none";
}

document.addEventListener("click", async (event) => {
  const choice = event.target.closest(".language-choice[data-lang]");
  if (!choice) return;
  await applySelectedLanguage(choice.getAttribute("data-lang"));
  closeLanguageModal();
});

if (languageSelect) {
  languageSelect.addEventListener("change", async () => {
    try {
      const newLang = languageSelect.value;
      if (!newLang) return;
      await applySelectedLanguage(newLang);
      // Re-search with the new language if user has an active search
      if (activeQuery) {
        const isAiMode = searchBoxAi && searchBoxAi.style.display !== "none";
        search(1, isAiMode, { replaceHistory: true });
      }
    } catch (err) {
      console.error("Language change error:", err);
    }
  });
}

// ═══════════════════════════════════════════
// VOICE SEARCH
// ═══════════════════════════════════════════
const STT_LOCALES = {
  en: "en-IN", hi: "hi-IN", as: "as-IN", bn: "bn-IN", brx: "en-IN", doi: "en-IN",
  gu: "gu-IN", kn: "kn-IN", ks: "ur-IN", gom: "mr-IN", mai: "hi-IN", ml: "ml-IN",
  mni: "en-IN", mr: "mr-IN", ne: "ne-NP", or: "or-IN", pa: "pa-IN", sa: "hi-IN",
  sat: "en-IN", sd: "ur-IN", ta: "ta-IN", te: "te-IN", ur: "ur-IN", bh: "hi-IN", bho: "hi-IN"
};

// Track which mode triggered voice recognition ("ai" or "search")
let voiceModeTarget = "search";

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    isListening = true;
    updateMicUI();
    const target = voiceModeTarget === "ai" ? aiSearchInput : searchInput;
    if (target) {
      target.placeholder = "सुन रहा हूँ… Listening…";
      target.value = ""; // Clear for new voice input
    }
  };

  recognition.onresult = e => {
    let interimTranscript = "";
    let finalTranscript = "";

    for (let i = e.resultIndex; i < e.results.length; ++i) {
      if (e.results[i].isFinal) {
        finalTranscript += e.results[i][0].transcript;
      } else {
        interimTranscript += e.results[i][0].transcript;
      }
    }

    const target = voiceModeTarget === "ai" ? aiSearchInput : searchInput;
    if (target) {
      target.value = finalTranscript || interimTranscript;
      if (target === aiSearchInput) autoExpand(target);
    }

    if (finalTranscript) {
      recognition.stop();
      if (voiceModeTarget === "ai") {
        searchAI();
      } else {
        search();
      }
    }
  };

  recognition.onend = () => {
    isListening = false;
    updateMicUI();
    resetPlaceholders();
  };

  recognition.onerror = (e) => {
    console.error("Speech Recognition Error:", e.error);
    isListening = false;
    updateMicUI();
    resetPlaceholders();
    
    if (e.error === 'not-allowed') {
      alert("Microphone permission denied. Please allow mic access in your browser settings to use voice search.");
    } else if (e.error === 'no-speech') {
      console.log("No speech detected.");
    } else if (e.error === 'network') {
      alert("Network error. Voice recognition requires an active internet connection.");
    }
  };
}

function updateMicUI() {
  if (isListening) {
    micButton?.classList.add("listening");
    micButtonAi?.classList.add("listening");
  } else {
    micButton?.classList.remove("listening");
    micButtonAi?.classList.remove("listening");
  }
}

function resetPlaceholders() {
  const copy = getUiCopy();
  const stdPlaceholder = copy.placeholder || "Search anything...";
  const aiPlaceholder = copy.aiPlaceholder || "Puchho jo aapke mann mein hai... (AI Mode)";
  
  if (searchInput) {
    searchInput.placeholder = stdPlaceholder;
    if (searchInput.value === "") { /* keep it empty */ }
  }
  if (aiSearchInput) {
    aiSearchInput.placeholder = aiPlaceholder;
  }
}

function toggleVoiceSearch(mode) {
  if (!recognition) {
    alert("Voice search is not supported in this browser. Please try Chrome or Edge.");
    return;
  }

  try {
    if (isListening) {
      recognition.stop();
    } else {
      // Determine mode: explicit arg > current visible box
      if (mode) {
        voiceModeTarget = mode;
      } else {
        voiceModeTarget = (searchBoxAi && searchBoxAi.style.display !== "none") ? "ai" : "search";
      }
      recognition.lang = STT_LOCALES[currentLanguage] || "en-IN";
      recognition.start();
    }
  } catch (err) {
    console.error("Voice Toggle Error:", err);
    if (err.name !== 'InvalidStateError') {
      isListening = false;
      updateMicUI();
    }
  }
}

// ═══════════════════════════════════════════
// RESULT VOICE PLAYBACK (Browser Speech)
// ═══════════════════════════════════════════
const TTS_LOCALES = {
  en: "en-IN", hi: "hi-IN", as: "as-IN", bn: "bn-IN", brx: "hi-IN", doi: "hi-IN",
  gu: "gu-IN", kn: "kn-IN", ks: "ur-IN", gom: "mr-IN", mai: "hi-IN", ml: "ml-IN",
  mni: "hi-IN", mr: "mr-IN", ne: "hi-IN", or: "or-IN", pa: "pa-IN", sa: "hi-IN",
  sat: "hi-IN", sd: "ur-IN", ta: "ta-IN", te: "te-IN", ur: "ur-IN", bho: "hi-IN"
};

function supportsSpeechPlayback() {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

function setSpeechButtonState(button, speaking) {
  if (!button) return;
  button.classList.toggle("speaking", speaking);
  button.setAttribute("aria-pressed", speaking ? "true" : "false");
  button.title = speaking ? "Stop voice" : "Listen";
}

function stopSpeechPlayback() {
  if (supportsSpeechPlayback()) window.speechSynthesis.cancel();
  setSpeechButtonState(activeSpeechButton, false);
  activeSpeechButton = null;
  activeSpeechText = "";
}

function normalizeSpeechText(text = "") {
  return String(text)
    .replace(/\s+/g, " ")
    .replace(/https?:\/\/\S+/g, "")
    .trim()
    .slice(0, 1600);
}

function speakText(text, button = null) {
  if (!supportsSpeechPlayback()) {
    alert("Voice playback is not supported in this browser. Please try Chrome, Edge, or Safari.");
    return;
  }

  const cleanText = normalizeSpeechText(text);
  if (!cleanText) return;

  // If same request is already playing, stop it
  if (activeSpeechButton === button && activeSpeechText === cleanText && window.speechSynthesis.speaking) {
    stopSpeechPlayback();
    return;
  }

  stopSpeechPlayback();

  const utterance = new SpeechSynthesisUtterance(cleanText);
  // Determine language locale
  utterance.lang = TTS_LOCALES[currentLanguage || languageSelect?.value] || "en-IN";
  // Attempt to select a matching voice for better quality
  const voices = window.speechSynthesis.getVoices();
  const matchingVoice = voices.find(v => v.lang && v.lang.startsWith(utterance.lang));
  if (matchingVoice) utterance.voice = matchingVoice;
  utterance.rate = 0.95;
  utterance.pitch = 1;
  utterance.volume = 1;
  utterance.onend = stopSpeechPlayback;
  utterance.onerror = (e) => {
    console.error("SpeechSynthesis error:", e);
    stopSpeechPlayback();
  };

  activeSpeechButton = button;
  activeSpeechText = cleanText;
  setSpeechButtonState(button, true);
  window.speechSynthesis.speak(utterance);
}

// ── Search UI Mode (Google-style) ──
let isSearchFocused = false;

function enterSearchMode() {
  isSearchFocused = true;
  const box = document.getElementById('searchBoxStandard');
  if (box) box.classList.add('search-focused');
  // Also show trending suggestions panel
  if (trendingContainer) trendingContainer.style.display = "block";
}

function exitSearchMode() {
  // Small delay to allow clicks on buttons inside the search box to register
  setTimeout(() => {
    // Don't exit if the active element is still inside the search box
    const box = document.getElementById('searchBoxStandard');
    if (box && box.contains(document.activeElement)) return;
    // Don't exit if search input has text
    if (searchInput && searchInput.value.trim()) return;
    isSearchFocused = false;
    if (box) box.classList.remove('search-focused');
    // Also hide trending suggestions panel
    if (trendingContainer) trendingContainer.style.display = "none";
  }, 150);
}

// Also hide camera/AI when user starts typing (Google-style)
if (searchInput) {
  searchInput.addEventListener('input', () => {
    const box = document.getElementById('searchBoxStandard');
    if (!box) return;
    if (searchInput.value.trim()) {
      box.classList.add('search-focused');
    } else if (!isSearchFocused) {
      box.classList.remove('search-focused');
    }
  });
}


function getSearchResultsSpeechText() {
  const parts = [];
  const summaryText = aiSummaryBox?.innerText || "";
  const resultsText = Array.from(resultsBox?.querySelectorAll(".result-item, .news-card-premium, .video-card") || [])
    .slice(0, 5)
    .map((el, idx) => `Result ${idx + 1}. ${el.innerText}`)
    .join(". ");

  if (summaryText) parts.push(summaryText);
  if (resultsText) parts.push(resultsText);
  return parts.join(". ");
}

function renderVoiceButton(label = "Listen", extraClass = "") {
  return `
    <button type="button" class="tts-toggle-btn ${extraClass}" aria-pressed="false" title="${label}">
      <svg class="tts-icon-play" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
      </svg>
      <svg class="tts-icon-stop" width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <rect x="7" y="7" width="10" height="10" rx="2"></rect>
      </svg>
    </button>`;
}

function renderSponsoredAd(ad) {
  if (!ad) return "";
  const url = escapeHtml(ad.url || "#");
  const title = escapeHtml(ad.title || "Sponsored result");
  const description = escapeHtml(ad.description || "");
  const advertiser = escapeHtml(ad.advertiser || "Sponsored");
  const cta = escapeHtml(ad.cta || "Learn more");
  const category = escapeHtml(ad.category || "recommended");

  return `
    <div class="sponsored-result" data-ad-id="${escapeHtml(ad.id || "")}">
      <div class="sponsored-topline">
        <span class="sponsored-badge">Sponsored</span>
        <span class="sponsored-advertiser">${advertiser}</span>
        <span class="sponsored-category">${category}</span>
      </div>
      <a href="${url}" target="_blank" rel="noopener noreferrer" class="sponsored-title">${title}</a>
      <p class="sponsored-description">${description}</p>
      <a href="${url}" target="_blank" rel="noopener noreferrer" class="sponsored-cta">${cta} →</a>
    </div>`;
}

function injectSponsoredAds(htmlItems, ads = []) {
  if (!ads || ads.length === 0) return htmlItems.join("");
  const items = [...htmlItems];
  const firstAd = renderSponsoredAd(ads[0]);
  const secondAd = renderSponsoredAd(ads[1]);

  if (firstAd) items.splice(Math.min(2, items.length), 0, firstAd);
  if (secondAd && items.length > 6) items.splice(Math.min(7, items.length), 0, secondAd);

  return items.join("");
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(".tts-toggle-btn");
  if (!button) return;
  event.preventDefault();
  event.stopPropagation();

  if (button.classList.contains("tts-all-results")) {
    speakText(getSearchResultsSpeechText(), button);
    return;
  }

  const resultCard = button.closest(".result-item, .news-card-premium, .summary-card, .ai-chat-container");
  if (resultCard) speakText(resultCard.innerText, button);
});

// ── Location Services ──
function requestLocation() {
    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser");
        return;
    }

    const btn = document.getElementById("locationButton");
    if (btn) btn.classList.add("loading-loc");

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            appState.location = { lat: latitude, lon: longitude };
            localStorage.setItem("userLocation", JSON.stringify(appState.location));
            
            if (btn) {
                btn.classList.remove("loading-loc");
                btn.classList.add("loc-active");
                btn.style.color = "var(--accent-green)";
            }
            
            console.log("Location updated:", appState.location);
            // Optional: Show a small toast or update UI to show city name
            if (activeQuery) search(1, false, { replaceHistory: true });
        },
        (error) => {
            console.error("Location error:", error);
            if (btn) btn.classList.remove("loading-loc");
            alert("Unable to retrieve your location. Please check your browser permissions.");
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
}

// Auto-load location if already granted in this session
if (appState.location) {
    const btn = document.getElementById("locationButton");
    if (btn) {
        btn.classList.add("loc-active");
        btn.style.color = "var(--accent-green)";
    }
}

function closeLocationPopup() {
    const modal = document.getElementById("locationPopup");
    if (modal) modal.style.display = "none";
}

function handleLocationChoice(enabled) {
    appState.locationChoiceMade = true;
    localStorage.setItem("locationChoiceMade", "true");
    closeLocationPopup();
    
    if (enabled) {
        requestLocation();
    } else {
        // Just proceed with search without location
        search(1, false, { replaceHistory: true });
    }
}

// ── Camera ──
let scannerStream = null;
let scannerActive = false;
let nutritionScanInProgress = false;
async function startLiveScan() {
  const liveScanner = document.getElementById("liveScanner");
  const video = document.getElementById("scannerVideo");
  const status = document.getElementById("liveScanStatus");
  const nutritionCaptureBtn = document.getElementById("nutritionCaptureBtn");

  try {
    if (scannerStream) stopLiveScan();
    scannerStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    video.srcObject = scannerStream;
    liveScanner.style.display = "block";
    scannerActive = true;
    nutritionScanInProgress = false;

    if (nutritionCaptureBtn) {
      nutritionCaptureBtn.style.display = "inline-flex";
      nutritionCaptureBtn.disabled = false;
      if (currentFilter === "nutrition") {
        nutritionCaptureBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v8M8 12h8" />
          </svg>
          Analyze Food
        `;
        nutritionCaptureBtn.setAttribute("onclick", "captureLiveNutritionFrame()");
      } else {
        nutritionCaptureBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v8M8 12h8" />
          </svg>
          Capture Photo
        `;
        nutritionCaptureBtn.setAttribute("onclick", "captureLivePhoto()");
      }
    }

    requestAnimationFrame(tick);
    status.innerHTML = currentFilter === "nutrition"
      ? "Frame the food item, then tap Analyze Food."
      : "🔍 Align QR Code in frame or tap Capture Photo below.";
  } catch (err) {
    alert("Camera Error: " + err.message);
  }
}

function stopLiveScan() {
  if (scannerStream) {
    scannerStream.getTracks().forEach(track => track.stop());
    scannerStream = null;
  }
  scannerActive = false;
  nutritionScanInProgress = false;
  const nutritionCaptureBtn = document.getElementById("nutritionCaptureBtn");
  if (nutritionCaptureBtn) nutritionCaptureBtn.style.display = "none";
  document.getElementById("liveScanner").style.display = "none";
}

function tick() {
  if (!scannerActive) return;

  const video = document.getElementById("scannerVideo");
  const status = document.getElementById("liveScanStatus");

  if (video.readyState === video.HAVE_ENOUGH_DATA) {
    if (currentFilter === "nutrition") {
      requestAnimationFrame(tick);
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: "dontInvert" });

    if (code) {
      status.innerHTML = `✅ <b>FOUND:</b> ${code.data}`;
      searchInput.value = code.data;
      
      // Visual Feedback
      video.style.border = "4px solid var(--accent-green)";
      
      setTimeout(() => {
        stopLiveScan();
        search(1, false);
      }, 500);
      return;
    }
  }
  requestAnimationFrame(tick);
}

async function captureLiveNutritionFrame() {
  if (!scannerActive || nutritionScanInProgress) return;

  const video = document.getElementById("scannerVideo");
  const status = document.getElementById("liveScanStatus");
  const nutritionCaptureBtn = document.getElementById("nutritionCaptureBtn");

  if (!video || video.readyState < video.HAVE_CURRENT_DATA || !video.videoWidth || !video.videoHeight) {
    if (status) status.textContent = "Camera is still getting ready. Try again in a moment.";
    return;
  }

  nutritionScanInProgress = true;
  if (nutritionCaptureBtn) nutritionCaptureBtn.disabled = true;
  if (status) status.innerHTML = `<div class="dna-spinner"></div> Analyzing food nutrition...`;

  try {
    const maxWidth = 800;
    const ratio = Math.min(maxWidth / video.videoWidth, 1);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * ratio);
    canvas.height = Math.round(video.videoHeight * ratio);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];

    const data = await analyzeNutritionByImage(b64, "image/jpeg");
    if (!data.name && !data.food_name) {
      throw new Error(data.detail || data.error || "Food nutrition result nahi mila");
    }

    stopLiveScan();
    if (scanStatus) scanStatus.innerHTML = `✨ <b>Food Identified:</b> ${data.name || data.food_name}`;
    if (searchInput) searchInput.value = data.name || data.food_name;
    if (resultsBox) resultsBox.innerHTML = "";
    if (aiSummaryBox) aiSummaryBox.innerHTML = renderNutritionPanel(data);
    if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
    if (trendingContainer) trendingContainer.style.display = "none";
    if (historyBox) historyBox.style.display = "none";
    if (heroSection) heroSection.classList.add("hidden");
  } catch (e) {
    nutritionScanInProgress = false;
    if (nutritionCaptureBtn) nutritionCaptureBtn.disabled = false;
    if (status) status.textContent = `Nutrition scan failed: ${e.message}`;
    if (scanStatus) scanStatus.textContent = `❌ Recognition Error: ${e.message}`;
  }
}

async function captureLivePhoto() {
  if (!scannerActive || nutritionScanInProgress) return;

  const video = document.getElementById("scannerVideo");
  const status = document.getElementById("liveScanStatus");
  const nutritionCaptureBtn = document.getElementById("nutritionCaptureBtn");

  if (!video || video.readyState < video.HAVE_CURRENT_DATA || !video.videoWidth || !video.videoHeight) {
    if (status) status.textContent = "Camera is still getting ready. Try again in a moment.";
    return;
  }

  nutritionScanInProgress = true;
  if (nutritionCaptureBtn) nutritionCaptureBtn.disabled = true;
  if (status) status.innerHTML = `<div class="dna-spinner"></div> Capturing & analyzing frame...`;

  try {
    const maxWidth = 800;
    const ratio = Math.min(maxWidth / video.videoWidth, 1);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * ratio);
    canvas.height = Math.round(video.videoHeight * ratio);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(async (blob) => {
      const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
      stopLiveScan();
      await triggerVisualSearch(file);
    }, "image/jpeg", 0.8);
  } catch (e) {
    nutritionScanInProgress = false;
    if (nutritionCaptureBtn) nutritionCaptureBtn.disabled = false;
    if (status) status.textContent = `Capture failed: ${e.message}`;
  }
}

function toggleAboutAccordion() {
  const content = document.getElementById("aboutAccordionContent");
  const container = document.querySelector(".setting-about-accordion");
  if (content && container) {
    if (content.style.display === "none") {
      content.style.display = "block";
      container.classList.add("active");
    } else {
      content.style.display = "none";
      container.classList.remove("active");
    }
  }
}

function openImagePicker() { if (cameraInput) cameraInput.click(); }
if (cameraInput) {
  cameraInput.addEventListener("change", async () => {
    const f = cameraInput.files?.[0];
    if (!f) return;
    
    attachedScan = f;
    if (scanStatus) scanStatus.innerHTML = `⏳ Analyzing <b>${f.name}</b>...`;

    // 1. Try QR/Barcode Scan locally first
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          
          if (code) {
            const isUrl = code.data.startsWith("http://") || code.data.startsWith("https://");
            if (scanStatus) {
                scanStatus.innerHTML = `
                    <div class="scan-result-card">
                        <span class="scan-label">✅ QR Code Detected</span>
                        <div class="scan-data">${code.data}</div>
                        ${isUrl ? `<a href="${code.data}" target="_blank" class="scan-link-btn">Visit Website →</a>` : ''}
                    </div>
                `;
            }
            searchInput.value = code.data;
            // Trigger search automatically for immediate "output"
            search(1, false);
          } else {
            // 2. If no QR, trigger Advanced Visual Search via backend
            triggerVisualSearch(f);
          }
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(f);
    } catch (err) {
      console.error("Local scan error:", err);
      triggerVisualSearch(f);
    }
  });
}


/** ── Triggering Advanced AI Visual Recognition ── **/
async function triggerVisualSearch(file) {
  if (scanStatus) scanStatus.innerHTML = `🔍 Advanced Scan: Searching "Whole Internet" for ${file.name}...`;
  
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_token", appState.guestId);

  try {
    if (currentFilter === "nutrition") {
        if (scanStatus) scanStatus.innerHTML = `<div class="dna-spinner"></div> 🧬 Gemini 1.5 Flash: Scanning for Nutritional DNA...`;
        const b64 = await compressImage(file);
        const data = await analyzeNutritionByImage(b64, "image/jpeg");
        if (data.name || data.food_name) {
            const foodName = data.name || data.food_name;
            if (scanStatus) scanStatus.innerHTML = `✨ <b>Food Identified:</b> ${foodName}`;
            searchInput.value = foodName;
            resultsBox.innerHTML = "";
            aiSummaryBox.innerHTML = renderNutritionPanel(data);
            
            // Layout adjustments for "Direct" feel
            if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
            if (trendingContainer) trendingContainer.style.display = "none";
            if (historyBox) historyBox.style.display = "none";
            if (heroSection) heroSection.classList.add("hidden");
            if (mainWrap) mainWrap.scrollTop = 0;
            return;
        }
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_token", appState.guestId);

    const res = await fetchWithApiFallback(`/visual-search`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      const identityStr = data.identity || "";
      // ... rest of the recognition logic (keeping for non-nutrition)
      
      // Check if it's Nutrition AI JSON response
      let nutritionData = null;
      if (identityStr.includes("```json")) {
         try {
           const jsonStr = identityStr.split("```json")[1].split("```")[0];
           const parsed = JSON.parse(jsonStr);
           if (parsed.intent === "nutrition") {
               nutritionData = parsed;
           }
         } catch(e){}
      }

      if (nutritionData) {
         if (scanStatus) scanStatus.innerHTML = `✨ <b>Nutrition Analyzed:</b> ${nutritionData.food_name}`;
         searchInput.value = `Nutrition info for ${nutritionData.food_name}`;
         // Render the nutrition panel directly
         resultsBox.innerHTML = "";
         aiSummaryBox.innerHTML = renderNutritionPanel(nutritionData);
         if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
         if (trendingContainer) trendingContainer.style.display = "none";
         if (historyBox) historyBox.style.display = "none";
         if (heroSection) heroSection.classList.add("hidden");
      } else {
         if (scanStatus) scanStatus.innerHTML = `✨ <b>Recognition Complete:</b> ${data.identity || "Possible matches found below."}`;
         // Put recognition result in search bar and trigger AI Mode with social keywords
         const identityQuery = data.identity || `Search for details about ${file.name}`;
         searchInput.value = `${identityQuery} official social media links instagram facebook twitter x`;
         search(1, true); // Automatic Ask AI trigger
      }
    } else {
      throw new Error(data.error || "Recognition failed");
    }
  } catch (e) {
    if (scanStatus) scanStatus.textContent = `❌ Recognition Error: ${e.message}`;
  }
}

// ── PDF Upload ──
const pdfInput = document.getElementById("pdfInput");
function openPdfPicker() { if (pdfInput) pdfInput.click(); }
if (pdfInput) {
  pdfInput.addEventListener("change", async () => {
    const f = pdfInput.files?.[0];
    if (!f) return;
    
    if (scanStatus) scanStatus.textContent = `⏳ Processing PDF: ${f.name}...`;
    
    const formData = new FormData();
    formData.append("file", f);
    formData.append("session_token", appState.guestId);

    try {
      const res = await fetchWithApiFallback(`/upload-pdf`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        // If in AI mode, show in AI box. Otherwise show standard scanStatus.
        const activeAi = document.getElementById("searchBoxAi").style.display === "flex";
        
        const pillHtml = `
            <div class="pdf-status-pill">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16m16-4V8l-6-6"/></svg>
                <span>${f.name} (Ready)</span>
            </div>
        `;

        if (activeAi && aiPdfPreview) {
            aiPdfPreview.innerHTML = pillHtml;
            aiPdfPreview.style.display = "inline-flex";
            if (scanStatus) scanStatus.textContent = "";
        } else if (scanStatus) {
            scanStatus.innerHTML = pillHtml;
        }

        searchInput.value = ""; 
        if (aiSearchInput) {
            aiSearchInput.placeholder = "PDF Analysis active. Ask anything...";
            aiSearchInput.focus();
        }
        searchInput.placeholder = "Puchho iss PDF ke baare mein...";
        searchInput.focus();
      } else {
        throw new Error(data.error || "Upload failed");
      }
    } catch (e) {
      if (scanStatus) scanStatus.textContent = `❌ Error: ${e.message}`;
    }
  });
}

// ═══════════════════════════════════════════
// HOME RESET & CLEANUP
// ═══════════════════════════════════════════
async function resetToHome(options = {}) {
  const { replaceHistory = false, skipHistory = false } = options;
  stopSpeechPlayback();
  chatHistory = [];
  activeQuery = "";
  currentFilter = "all";
  advancedMode = false;
  searchInput.value = "";
  updateClearBtn();
  resultsBox.innerHTML = "";
  aiSummaryBox.innerHTML = "";
  if (paginationContainer) paginationContainer.innerHTML = "";
  if (searchFiltersDiv) searchFiltersDiv.style.display = "none";
  if (trendingContainer) trendingContainer.style.display = "block";
  if (historyBox) historyBox.style.display = "flex";
  if (heroSection) heroSection.classList.remove("hidden");
  if (aboutSection) aboutSection.style.display = "block";
  if (scanStatus) scanStatus.textContent = "";
  
  // Clear file inputs and visual previews
  if (pdfInput) pdfInput.value = "";
  if (cameraInput) cameraInput.value = "";
  if (aiPdfPreview) {
      aiPdfPreview.style.display = "none";
      aiPdfPreview.innerHTML = "";
  }
  
  applyFilterActiveState("all");
  document.documentElement.setAttribute("data-ai-mode", "false");
  // Restore full search UI (camera, Ask AI buttons)
  const searchBox = document.getElementById('searchBoxStandard');
  if (searchBox) searchBox.classList.remove('search-focused');
  isSearchFocused = false;
  closeAutocomplete();
  if (!skipHistory) writeBrowserSearchState({ query: "" }, replaceHistory);
  
  // Clear backend memory context for this session
  try {
      await apiJsonRequest("/clear-context", { session_token: appState.guestId });
  } catch(e) { console.error("Failed to clear context"); }
}

// ═══════════════════════════════════════════
// SOURCE BADGE
// ═══════════════════════════════════════════
function getSourceBadge(url, fallback = "Source") {
  try {
    const h = new URL(url).hostname.replace(/^www\./, "").toLowerCase();
    if (h.includes(".gov") || h.includes(".nic.in") || h.includes("rbi.org.in")) return "Official";
    if (h.includes("ndtv") || h.includes("bbc.") || h.includes("hindustantimes") || h.includes("indianexpress") || h.includes("thehindu") || h.includes("timesofindia") || h.includes("news.google")) return "News";
    if (h.includes("docs.") || h.includes("readthedocs") || h.includes("mdn")) return "Docs";
    if (h.includes("github") || h.includes("stackoverflow") || h.includes("reddit") || h.includes("medium") || h.includes("wikipedia")) return "Community";
    if (h.includes("youtube") || h.includes("youtu.be") || h.includes("vimeo")) return "Video";
    const base = h.split(".")[0];
    return base ? base.charAt(0).toUpperCase() + base.slice(1) : fallback;
  } catch { return fallback; }
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[ch]));
}

function getReadableHost(url, fallback = "Source") {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return fallback;
  }
}

function getFaviconUrl(url = "") {
  try {
    const host = new URL(url).hostname;
    return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=32`;
  } catch {
    return "favicon-32x32.png";
  }
}

function mediaFallbackImage(title = "IndiaSearch", type = "Preview") {
  const safeTitle = escapeHtml(String(title).slice(0, 42));
  const accent = type === "Video" ? "#ef4444" : "#1a73e8";
  const bg = type === "Video" ? "#111827" : "#eef4ff";
  const text = type === "Video" ? "#ffffff" : "#202124";
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
      <rect width="960" height="540" fill="${bg}"/>
      <rect x="56" y="56" width="848" height="428" rx="28" fill="${accent}" opacity="0.12"/>
      <circle cx="480" cy="242" r="76" fill="${accent}"/>
      <path d="M456 202v80l70-40z" fill="#fff"/>
      <text x="480" y="365" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" font-weight="700" fill="${text}">${safeTitle}</text>
      <text x="480" y="414" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" fill="${text}" opacity="0.72">IndiaSearch ${type}</text>
    </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function getYoutubeVideoId(url = "") {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]{6,})/,
    /youtube\.com\/embed\/([A-Za-z0-9_-]{6,})/,
    /youtube\.com\/shorts\/([A-Za-z0-9_-]{6,})/
  ];
  for (const pattern of patterns) {
    const match = String(url).match(pattern);
    if (match) return match[1];
  }
  return "";
}

function getVideoThumbnail(item = {}, title = "") {
  const provided = item.image || item.thumbnail || item.thumbnailUrl || "";
  if (provided) return provided;
  const videoId = getYoutubeVideoId(item.url || "");
  if (videoId) return `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
  return mediaFallbackImage(title || item.title || "Video", "Video");
}

// ─── renderAiSources: Minimal circular favicon row for top-left of AI card ───
function renderAiSources(sources = []) {
  if (!sources || sources.length === 0) return "";

  // Deduplicate by host
  const seen = new Set();
  const unique = sources.filter(src => {
    const h = src.host || src.url || "";
    if (seen.has(h)) return false;
    seen.add(h);
    return true;
  });

  const icons = unique.slice(0, 8).map((src) => {
    const url   = escapeHtml(src.url);
    const host  = escapeHtml(src.host || getReadableHost(src.url) || "source");
    const siteName = host.split('.')[0];
    const displayName = siteName.charAt(0).toUpperCase() + siteName.slice(1);
    const faviconUrl = `https://www.google.com/s2/favicons?sz=32&domain=${host}`;
    const initials = displayName.slice(0, 2);

    return `
      <a class="ai-source-favicon-link" href="${url}" target="_blank" rel="noopener noreferrer" title="${displayName}">
        <img src="${faviconUrl}" alt="${initials}"
          onerror="this.onerror=null;this.src='data:image/svg+xml;charset=utf-8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2214%22 height=%2214%22 viewBox=%220 0 14 14%22><rect width=%2214%22 height=%2214%22 rx=%227%22 fill=%22%234285f4%22/><text x=%227%22 y=%2210.5%22 font-size=%228%22 font-family=%22sans-serif%22 fill=%22white%22 text-anchor=%22middle%22 font-weight=%22bold%22>${initials}</text></svg>'"
        >
      </a>
    `;
  }).join("");

  return `<div class="ai-sources-minimal-row">
    <span class="ai-sources-label">Sources</span>
    ${icons}
  </div>`;
}

function renderAiSourcesIcons(sources = []) {
  return renderAiSources(sources);
}

function renderMarkdownWithCitations(markdown = "", sources = []) {
  const linkedText = String(markdown).replace(/\[(\d+)\]/g, (match, number) => {
    const src = sources[Number(number) - 1];
    if (!src || !src.url) {
      return `<span class="ai-citation ai-citation-missing" title="Source ${number} is not available in this response">[${number}]</span>`;
    }

    const url = escapeHtml(src.url);
    const title = escapeHtml(src.title || "Open source");
    return `<a class="ai-citation" href="${url}" target="_blank" rel="noopener noreferrer" title="${title}" data-source-url="${url}">[${number}]</a>`;
  });

  return marked.parse(linkedText);
}

document.addEventListener("click", (event) => {
  const link = event.target.closest(".ai-citation[data-source-url], .ai-source-card[data-source-url]");
  if (!link) return;

  const url = link.getAttribute("data-source-url") || link.getAttribute("href");
  if (!url) return;

  event.preventDefault();
  event.stopPropagation();
  window.open(url, "_blank", "noopener,noreferrer");
});

// ═══════════════════════════════════════════
// MAIN SEARCH
// ═══════════════════════════════════════════
async function search(pageNumber = 1, aiMode = false, options = {}) {
  const { replaceHistory = false, skipHistory = false } = options;
  let query = searchInput ? searchInput.value.trim() : "";
  stopSpeechPlayback();
  
  if (!query && activeQuery) {
    query = activeQuery;
    if (searchInput) searchInput.value = query;
  }

  if (!query) {
    resetToHome({ replaceHistory, skipHistory });
    return;
  }

  activeQuery = query;
  updateClearBtn();
  closeAutocomplete();

  if (heroSection) heroSection.classList.add("hidden");
  if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
  if (trendingContainer) trendingContainer.style.display = "none";
  if (historyBox) historyBox.style.display = "none";
  if (aboutSection) aboutSection.style.display = "none";

  if (aiMode) {
      if (searchBoxStandard) searchBoxStandard.style.display = "none";
      if (searchBoxAi) searchBoxAi.style.display = "flex";
      if (mainWrap) mainWrap.classList.add("ai-active");
  } else {
      if (searchBoxStandard) searchBoxStandard.style.display = "flex";
      if (searchBoxAi) searchBoxAi.style.display = "none";
      if (mainWrap) mainWrap.classList.remove("ai-active");
  }

  if (pageNumber === 1) saveHistory(query);
  applyFilterActiveState(currentFilter);
  if (!skipHistory) {
    writeBrowserSearchState({ query, page: pageNumber, filter: currentFilter, aiMode }, replaceHistory);
  }

  const targetLang = currentLanguage || languageSelect.value || "en";

  // Skeleton loader
  resultsBox.innerHTML = `
    <div class="skeleton-wrap">
      ${[1, 2, 3].map(() => `
        <div class="skeleton-item">
          <div class="skel skel-host"></div>
          <div class="skel skel-title"></div>
          <div class="skel skel-text"></div>
          <div class="skel skel-text skel-text-short"></div>
        </div>`).join("")}
    </div>`;

  // Perplexity-style skeleton when in AI mode
  if (aiMode) {
    aiSummaryBox.innerHTML = `
      <div class="prx-skeleton">
        <div class="prx-sk-row">
          <div class="prx-sk-src"></div><div class="prx-sk-src"></div><div class="prx-sk-src"></div>
        </div>
        <div class="prx-sk-line" style="width:96%"></div>
        <div class="prx-sk-line" style="width:86%"></div>
        <div class="prx-sk-line" style="width:92%"></div>
        <div class="prx-sk-line" style="width:74%"></div>
        <div class="prx-sk-line" style="width:82%"></div>
      </div>`;
  } else {
    aiSummaryBox.innerHTML = "";
  }

  try {
    if (currentFilter === "nutrition" && pageNumber === 1) {
      if (aiSummaryBox) aiSummaryBox.innerHTML = `<div class="loading-ai">🔍 IndiaSearch is analyzing ${query}...</div>`;
      const data = await analyzeNutritionByText(query);
      if (data.name || data.food_name) {
          resultsBox.innerHTML = "";
          aiSummaryBox.innerHTML = renderNutritionPanel(data);
          return;
      }
    }

    document.documentElement.setAttribute("data-ai-mode", aiMode ? "true" : "false");
    
    // Use new /ai-mode endpoint for true AI mode
    if (aiMode) {
      const aiRes = await fetchWithApiFallback(`/ai-mode?q=${encodeURIComponent(query)}&lang=${targetLang}`);
      const aiData = await aiRes.json();

      if (aiData.answer) {
        aiSummaryBox.innerHTML = renderGoogleStyleAIMode(aiData);
        resultsBox.innerHTML = "";
        if (paginationContainer) paginationContainer.innerHTML = "";
        chatHistory.push({ role: "assistant", content: aiData.answer });
        if (searchInput) searchInput.value = query;
        if (aiSearchInput) { aiSearchInput.value = ""; aiSearchInput.style.height = "auto"; }
        window.scrollTo({ top: 0, behavior: "smooth" });
        return;
      }
    }

    const params = new URLSearchParams({ 
        q: query, 
        page: String(pageNumber), 
        filter: currentFilter, 
        lang: targetLang,
        output_lang: LANGUAGE_NAMES[targetLang] || "English",
        ai_mode: String(aiMode),
        advanced_mode: String(advancedMode),
        history: aiMode ? JSON.stringify(chatHistory) : "",
        limit: String(appSettings.resultsCount),
        age_verified: String(appSettings.safeSearch === "off")
    });
    params.set("session_token", appState.guestId);
    
    if (appState.location) {
        params.set("lat", String(appState.location.lat));
        params.set("lon", String(appState.location.lon));
    }

    const res = await fetchWithApiFallback(`/search?${params}`);
    let data;
    try { data = await res.json(); } catch {
      throw new Error(`Backend returned non-JSON (status ${res.status})`);
    }

    if (!res.ok) {
      throw new Error(data.error || `Backend error (status ${res.status})`);
    }

    if (data.error) {
      if (data.requires_age_verification) {
        resultsBox.innerHTML = `
          <div class="age-verification-card" style="text-align: center; padding: 40px; background: var(--bg-card); border-radius: 16px; border: 1px solid var(--border); margin-top: 20px;">
            <div style="font-size: 48px; margin-bottom: 15px;">🔞</div>
            <h2 style="color: var(--text-primary); margin-bottom: 10px;">Age Verification Required</h2>
            <p style="color: var(--text-secondary); margin-bottom: 25px;">The content you are searching for requires you to be 18 years or older. Are you 18 or older?</p>
            <div style="display: flex; gap: 15px; justify-content: center;">
              <button onclick="confirmAgeAndSearch('${query}', ${pageNumber}, ${aiMode})" class="btn-primary" style="background: #ef4444; border-color: #ef4444; padding: 10px 30px;">Yes, I am 18+</button>
              <button id="askAiButton" onclick="enterAiMode()" class="btn-ai-toggle" title="Switch to AI Mode" style="background: var(--bg-alt); color: var(--text-primary); border-color: var(--border); padding: 10px 30px;">No, take me back</button>
            </div>
          </div>
        `;
        if (paginationContainer) paginationContainer.innerHTML = "";
        return;
      }
      resultsBox.innerHTML = `<div class="state-error"><span class="state-error-icon">⚠️</span>${await translateText(data.error, targetLang)}</div>`;
      return;
    }

    // ── AI Summary / Overview ──
    let summaryHtml = "";
    let shouldAnimate = false;
    let rawText = "";
    const aiSources = data.ai_sources || [];
    const aiSourcesHtml = renderAiSources(aiSources);

    if (data.ai_summary && pageNumber === 1) {
      rawText = typeof data.ai_summary === 'string' ? data.ai_summary : (data.ai_summary.answer || String(data.ai_summary));
      if (aiMode || data.intent === 'ai') {
        shouldAnimate = true;
        
        // Render FULL HISTORY for AI Mode — plain, no bubbles
        let historyHtml = chatHistory.slice(0, -1).map(msg => `
            <div class="ai-${msg.role === 'user' ? 'q' : 'a'}-block">
              ${ msg.role === 'user'
                 ? `<p class="ai-q-text">${escapeHtml(msg.content)}</p>`
                 : `<div class="ai-answer-body">${renderMarkdownWithCitations(msg.content)}</div>`
              }
            </div>
        `).join("");

        summaryHtml = `
          <div class="ai-conversation">
            ${historyHtml}
            <div class="ai-q-block">
              <p class="ai-q-text">${escapeHtml(query)}</p>
            </div>
            <div class="ai-a-block">
              <div class="ai-answer-meta">
                ${aiSourcesHtml}
                ${renderVoiceButton("Listen to answer", "tts-card-btn")}
              </div>
              <div class="ai-answer-body" id="streamingAI"></div>
            </div>
          </div>`;

      } else {
        summaryHtml = `
          <div class="summary-card">
            <div class="ai-card-header">
              <div class="ai-card-header-left">
                <div class="ai-query-header">
                  <div class="ai-query-avatar">✨</div>
                  <span class="ai-query-text">${escapeHtml(query)}</span>
                </div>
                ${aiSourcesHtml}
              </div>
              ${renderVoiceButton("Listen to answer")}
            </div>
            <div class="summary-text">${renderMarkdownWithCitations(rawText, aiSources)}</div>
          </div>`;
      }
    }

    // ── Pre-render Smart Panels (Wikipedia) ──
    let wikiHtml = "";
    if (!aiMode && data.knowledge_panel && pageNumber === 1 && currentFilter === "all") {
      const kp = data.knowledge_panel;
      const [kt, ks] = await Promise.all([translateText(kp.title, targetLang), translateText(kp.snippet, targetLang)]);
      
      const cleanImg = kp.image ? kp.image.replace(/'/g, "%27") : "";
      const imgTag = kp.image
        ? `<img src="${kp.image}" alt="${kt}" style="float:right;margin:0 0 12px 16px;width:110px;height:110px;object-fit:cover;border-radius:10px;cursor:zoom-in;box-shadow: 0 4px 10px rgba(0,0,0,0.1);" onclick="openImageModal('${cleanImg}')">`
        : "";
        
      const shortSnippet = ks.length > 180 ? ks.substring(0, 180) + '...' : ks;

      wikiHtml = `
        <div class="knowledge-card" style="overflow:hidden; padding: 18px; border-radius: 14px; background: var(--bg-card); box-shadow: var(--shadow-md); margin-bottom: 20px; border: 1px solid var(--border);">
          ${imgTag}
          <h3 style="margin-top:0; color: var(--text-primary); font-size: 20px;">📚 ${kt}</h3>
          <p class="knowledge-preview" style="color: var(--text-secondary); line-height: 1.5; font-size: 14px; margin-bottom: 12px;">${shortSnippet}</p>
          <details class="knowledge-overview" style="margin-top: 10px; background: rgba(0,0,0,0.03); padding: 10px; border-radius: 8px;">
            <summary style="cursor: pointer; font-weight: 600; color: var(--accent-blue); font-size: 13px;">View More</summary>
            <p class="knowledge-full" style="margin-top:10px; color: var(--text-main); font-size: 14px; line-height: 1.6;">${ks}</p>
            <a href="${kp.url}" target="_blank" class="knowledge-link" style="display:inline-block; margin-top: 10px; font-weight: bold; color: var(--accent);">Read on Wikipedia →</a>
          </details>
        </div>`;
    }

    // Initialize the box with AI and Wiki
    aiSummaryBox.innerHTML = summaryHtml + wikiHtml;

    // Auto-play voice if enabled and not in animated typing mode
    if (data.ai_summary && pageNumber === 1 && !shouldAnimate && appSettings.autoPlayVoice) {
      setTimeout(() => {
        const ttsBtn = aiSummaryBox.querySelector('.tts-toggle-btn');
        speakText(rawText, ttsBtn);
      }, 500);
    }

    // Trigger Animation if needed
    if (shouldAnimate) {
      const target = document.getElementById("streamingAI");
      if (target) {
        let i = 0;
        const speed = 10; // Fast typing speed
        function typeWriter() {
           if (i < rawText.length) {
              const chunk = rawText.substr(i, 5); // Type 5 chars at a time
              target.innerHTML += chunk.replace(/\n/g, "<br>");
              i += 5;
              setTimeout(typeWriter, speed);
              if (mainWrap) mainWrap.scrollTop = mainWrap.scrollHeight;
           } else {
              if (rawText.includes("```json") && rawText.includes('"intent": "nutrition"')) {
                  try {
                      const jsonStr = rawText.split("```json")[1].split("```")[0];
                      const parsed = JSON.parse(jsonStr);
                      target.innerHTML = renderNutritionPanel(parsed);
                  } catch(e) {
                      target.innerHTML = renderMarkdownWithCitations(rawText, aiSources);
                  }
              } else {
               const finalMd = renderMarkdownWithCitations(rawText, aiSources);
               target.innerHTML = finalMd; // Run through markdown parser once done
               
               // After typing is done, push to history if not already there
               if (aiMode) {
                   chatHistory.push({ role: "assistant", content: rawText });
               }
               // Auto play speech if enabled
               if (appSettings.autoPlayVoice) {
                   const ttsBtn = document.querySelector('.tts-card-btn');
                   speakText(rawText, ttsBtn);
               }
            }
           }
        }
        typeWriter();
      }
    }

    // ── Special Panels Integration (Weather, Sports, Finance) ──
    if (data.special_data && pageNumber === 1 && !aiMode) {
      let specialHtml = "";
      if (data.intent === 'weather') {
        specialHtml = renderWeatherPanel(data.special_data);
      } else if (data.intent === 'sports') {
        specialHtml = renderSportsPanel(data.special_data);
      } else if (data.intent === 'finance') {
        specialHtml = renderStockPanel(data.special_data);
      }
      
      if (specialHtml) {
        // Insert special panels BEFORE the AI summary
        aiSummaryBox.innerHTML = specialHtml + aiSummaryBox.innerHTML;
      }
    }

    if (currentFilter === "images" && data.warning) {
      const tw = await translateText(data.warning, targetLang);
      aiSummaryBox.innerHTML = `<div class="image-warning-bar">${tw}</div>` + aiSummaryBox.innerHTML;
    }

    // ── Smart Image Gallery ──
    if (data.top_images && data.top_images.length > 0 && currentFilter === "all") {
        aiSummaryBox.innerHTML = renderSmartImageGallery(data.top_images) + aiSummaryBox.innerHTML;
    }

    // If NO results at all (no web results AND no weather/summary/sports/stocks)
    const hasResults = (data.results && data.results.length > 0);
    const hasSmartAnswer = Boolean(data.special_data || data.weather || data.summary || data.knowledge_panel || data.sports || data.stocks);

    if (!hasResults && !hasSmartAnswer) {
      const noRes = getUiCopy(targetLang).noResults || await translateText("No results found", targetLang);
      resultsBox.innerHTML = `<div class="state-empty"><span class="state-empty-icon">🔍</span>${noRes}</div>`;
      if (paginationContainer) paginationContainer.innerHTML = "";
      return;
    }

    resultsBox.innerHTML = ""; // Clear results but keep header (aiSummaryBox)

    // ── Inline Article Reader ──
    window.readArticle = async function (e, url, index) {
      e.preventDefault();
      const box = document.getElementById(`article-inline-${index}`);
      if (!box) return;
      if (box.style.display === "block") { box.style.display = "none"; return; }
      box.style.display = "block";
      box.innerHTML = "<p style='color:var(--text-muted);padding:12px 0;'>⏳ Fetching article…</p>";
      try {
        const r = await fetchWithApiFallback(`/read-article?url=${encodeURIComponent(url)}`);
        const d = await r.json();
        if (d.error || !d.content || d.content.length < 50) {
          box.innerHTML = `<div class="inline-article-box"><p style="color:#d93025;">⚠️ Publisher blocked direct access.</p><a href="${url}" target="_blank" class="inline-article-link">Read on site →</a></div>`;
        } else {
          const paras = d.content.split("\n\n").map(p => `<p style="margin-bottom:10px;">${p}</p>`).join("");
          box.innerHTML = `<div class="inline-article-box"><h4>${d.title}</h4><div class="inline-article-scroll">${paras}</div><a href="${url}" target="_blank" class="inline-article-link">🔗 Open original →</a></div>`;
        }
      } catch {
        box.innerHTML = `<div class="inline-article-box" style="color:#d93025;">⚠️ Network error.</div>`;
      }
    };

    const visibleResults = aiMode ? data.results.slice(0, 2) : data.results;

    const resultPromises = visibleResults.map(async (item, i) => {
      const [tt, ts, visitT] = await Promise.all([
        translateText(item.title, targetLang),
        translateText(item.snippet || "", targetLang),
        Promise.resolve(getUiCopy(targetLang).visitWebsite || "Visit Website")
      ]);

      // News detection: either filter is news OR item has is_news flag
      const isNews = (currentFilter === "news") || item.is_news === true;
      const isImages = currentFilter === "images";
      const isVideos = currentFilter === "videos";
      let host = item.url;
      try { host = new URL(item.url).hostname.replace(/^www\./, ""); } catch { }
      const sourceName = getSourceBadge(item.url, host);
      const faviconUrl = getFaviconUrl(item.url);

      if (aiMode) {
        return ""; // In true AI Mode, don't show normal results
      }

      if (isVideos) {
        const thumb = getVideoThumbnail(item, tt);
        const fallback = mediaFallbackImage(tt, "Video");
        return `
          <a class="video-card" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer" style="cursor: pointer; text-decoration:none;">
            <div class="video-thumbnail" style="position: relative; border-radius: 12px; overflow: hidden; margin-bottom: 10px; background: #111827; aspect-ratio: 16 / 9;">
              <img src="${escapeHtml(thumb)}" alt="${tt}" style="width: 100%; height: 100%; object-fit: cover; display:block;" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='${fallback}'">
              <div class="play-icon" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.62); border-radius: 50%; width: 54px; height: 54px; display: flex; align-items: center; justify-content: center;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
              </div>
            </div>
            <div class="video-meta">
              <div class="video-title" style="font-weight: 700; font-size: 16px; color: var(--text-primary); display: block; margin-bottom: 4px; line-height: 1.4;">${tt}</div>
              <div class="video-source" style="font-size: 13px; color: var(--text-secondary);">${ts}</div>
            </div>
          </a>`;
      }

      if (isImages) {
        const isFallback = (item.snippet || "").includes("Fallback Preview");
        const imageUrl = item.image || item.url || "";
        const sourceUrl = item.source_url || item.pageUrl || item.url || "";
        const fallback = mediaFallbackImage(tt, "Image");
        return `
          <div class="image-card">
            <div class="image-frame" onclick="openImageModal(decodeURIComponent('${encodeURIComponent(imageUrl)}'))">
              <img src="${escapeHtml(imageUrl)}" alt="${tt}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='${fallback}'">
            </div>
            <div class="image-meta">
              ${isFallback ? `<span class="image-badge">Fallback</span>` : ""}
              <div class="image-title">${tt}</div>
              <div class="image-source">${ts}</div>
              <div class="image-actions-row">
                <button type="button" class="image-download-link" onclick="event.stopPropagation(); downloadImageUrl(decodeURIComponent('${encodeURIComponent(imageUrl)}'), this)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download
                </button>
                <a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer" class="image-open-link">Open →</a>
              </div>
            </div>
          </div>`;
      }

      // ── PREMIUM NEWS CARD with Image ──
      if (isNews) {
        const hasImg = item.image && item.image.length > 5;
        return `
          <div class="news-card-premium" onclick="window.open('${item.url}', '_blank')">
            ${hasImg ? `
              <div class="news-card-img-wrap">
                <img src="${item.image}" alt="${tt}" class="news-card-img" loading="lazy"
                     onerror="this.parentElement.style.display='none'">
              </div>` : `
              <div class="news-card-img-wrap news-card-no-img">
                <span style="font-size:36px;">📰</span>
              </div>`}
            <div class="news-card-body">
              <div class="news-card-meta">
                <img class="result-favicon-img news-favicon" src="${escapeHtml(faviconUrl)}" alt="" loading="lazy" onerror="this.style.display='none'">
                <span class="news-source-chip">${sourceName}</span>
                <span class="news-dot">·</span>
                <span class="news-card-host">${host}</span>
              </div>
              <h3 class="news-card-title">${tt}</h3>
              <p class="news-card-snippet">${ts.substring(0, 130)}${ts.length > 130 ? '…' : ''}</p>
              <div class="news-card-footer">
                <button class="read-here-btn news-read-btn" onclick="event.stopPropagation(); readArticle(event,'${item.url}',${i})">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a4 4 0 0 1-4-4V6"/></svg>
                  Read Here
                </button>
                ${renderVoiceButton("Listen to news", "tts-card-btn")}
                <a href="${item.url}" target="_blank" class="news-open-link" onclick="event.stopPropagation()">Open →</a>
              </div>
              <div id="article-inline-${i}" style="display:none;" onclick="event.stopPropagation()"></div>
            </div>
          </div>`;
      }

      // ── Custom About IndiaSearch Card ──
      if (item.source === "direct_hit" && item.title.includes("About IndiaSearch")) {
        return `
          <div class="about-indiasearch-card animate-slide-up" style="animation-delay: ${i * 0.05}s; margin-bottom: 24px;">
            <div class="about-card-inner">
                <div class="about-card-image">
                    <img src="${item.image}" alt="IndiaSearch Team" onerror="this.src='https://via.placeholder.com/150?text=Team+IndiaSearch'">
                </div>
                <div class="about-card-content">
                    <div class="result-title-row">
                    <a href="${escapeHtml(item.url)}" target="_blank" class="result-title" style="font-size: 22px;">${tt}</a>
                    ${renderVoiceButton("Listen to result", "tts-card-btn")}
                    </div>
                    <p class="result-snippet" style="margin: 10px 0 20px;">${ts}</p>
                    <div class="about-links">
                        <a href="https://downloader.indiasearch.site" target="_blank" class="about-link-btn">⬇️ Downloader</a>
                        <a href="https://chat.indiasearch.site" target="_blank" class="about-link-btn">💬 Chat App</a>
                    </div>
                </div>
            </div>
          </div>`;
      }

      // ── Standard Web Result ──
      return `
        <div class="result-item">
          <div class="result-site-line">
            <div class="result-favicon">
              <img class="result-favicon-img" src="${escapeHtml(faviconUrl)}" alt="" loading="lazy" onerror="this.parentElement.textContent='🌐'">
            </div>
            <span class="result-host">${host}</span>
          </div>
          <div class="result-title-row">
          <a href="${item.url}" target="_blank" class="result-title">${tt}</a>
          ${renderVoiceButton("Listen to result", "tts-card-btn")}
          </div>
          <p class="result-snippet">${ts}</p>
          <a href="${item.url}" target="_blank" class="read-here-btn">${visitT} →</a>
        </div>`;
    });

    const htmlItems = await Promise.all(resultPromises);
    const sponsoredHtml = injectSponsoredAds(htmlItems, data.ad_slots || []);

    if (aiMode) {
      resultsBox.innerHTML = "";
      if (paginationContainer) paginationContainer.innerHTML = "";
    } else if (currentFilter === "images") {
      resultsBox.innerHTML = `<div class="image-grid">${htmlItems.join("")}</div>`;
      renderPagination(data.total_hits || 0, pageNumber);
    } else if (currentFilter === "videos") {
      resultsBox.innerHTML = `<div class="video-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px;">${htmlItems.join("")}</div>`;
      renderPagination(data.total || 0, pageNumber);
    } else if (currentFilter === "news") {
      resultsBox.innerHTML = `
        <div class="listen-results-bar">
          <span>Search results</span>
          ${renderVoiceButton("Listen to results", "tts-all-results")}
        </div>
        <div class="news-grid-premium">${sponsoredHtml}</div>`;
      renderPagination(data.total || 0, pageNumber);
    } else {
      const listenBar = `
        <div class="listen-results-bar">
          <span>Search results</span>
          ${renderVoiceButton("Listen to results", "tts-all-results")}
        </div>`;
      resultsBox.innerHTML = listenBar + sponsoredHtml;
      renderPagination(data.total || 0, pageNumber);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });

    // Keep searched query visible so users can switch tabs from the same bar.
    if (searchInput) searchInput.value = query;
    if (aiSearchInput) {
        aiSearchInput.value = "";
        aiSearchInput.style.height = "auto";
    }

  } catch (e) {
    const fallback = isLocalHost
      ? "Local backend not running on port 8000."
      : "Could not connect to the server. Please try again.";
    const msg = await translateText(e?.message || fallback, targetLang);
    resultsBox.innerHTML = `<div class="state-error"><span class="state-error-icon">⚠️</span>${msg}</div>`;
    console.error(e);
  }
}

// ═══════════════════════════════════════════
// PAGINATION
// ═══════════════════════════════════════════
function renderPagination(totalHits, currentPage) {
  if (!paginationContainer) return;
  if (totalHits <= 10) { paginationContainer.innerHTML = ""; return; }
  const totalPages = Math.ceil(totalHits / 10);
  let html = "";
  html += `<button class="page-btn" onclick="search(${currentPage - 1})" ${currentPage <= 1 ? "disabled" : ""}>←</button>`;
  const start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, currentPage + 2);
  for (let i = start; i <= end; i++) {
    html += `<button class="page-btn${i === currentPage ? " active" : ""}" ${i !== currentPage ? `onclick="search(${i})"` : ""}>${i}</button>`;
  }
  html += `<button class="page-btn" onclick="search(${currentPage + 1})" ${currentPage >= totalPages ? "disabled" : ""}>→</button>`;
  paginationContainer.innerHTML = html;
}

// ═══════════════════════════════════════════
// AUTOCOMPLETE
// ═══════════════════════════════════════════
const autocompleteDropdown = document.getElementById("autocompleteDropdown");
const searchBox = document.querySelector(".search-box");

// NOTE: enterSearchMode / exitSearchMode are defined earlier (line ~782) and
// already handle both the search-focused CSS class and the trending panel.
// Do NOT redefine them here.

if (searchInput) {
  searchInput.addEventListener("input", e => {
    const val = e.target.value.trim().toLowerCase();
    if (!val) { closeAutocomplete(); return; }

    const db = [...new Set([...searchHistory, ...TRENDING_KEYWORDS, "sarkari result", "latest news india", "ind vs pak", "tech jobs bangalore"])];
    const matches = db.filter(item => item.toLowerCase().includes(val)).slice(0, 6);

    if (matches.length > 0) {
      autocompleteDropdown.innerHTML = matches.map(m => {
        const bolded = m.replace(new RegExp(`(${val})`, "gi"), "<strong>$1</strong>");
        return `<div class="autocomplete-item" onclick="searchInput.value='${m.replace(/'/g, "\\'")}'; closeAutocomplete(); search(1);">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span>${bolded}</span>
        </div>`;
      }).join("");
      autocompleteDropdown.style.display = "block";
      if (searchBox) searchBox.classList.add("has-suggestions");
    } else {
      closeAutocomplete();
    }
  });

  searchInput.addEventListener("keyup", e => {
    if (e.key === "Enter") { closeAutocomplete(); search(1, false); }
    else if (!searchInput.value.trim()) resetToHome();
  });
}

function closeAutocomplete() {
  if (autocompleteDropdown) { autocompleteDropdown.innerHTML = ""; autocompleteDropdown.style.display = "none"; }
  if (searchBox) searchBox.classList.remove("has-suggestions");
}

document.addEventListener("click", e => { if (searchBox && !searchBox.contains(e.target)) closeAutocomplete(); });

window.addEventListener("popstate", async (event) => {
  restoringBrowserState = true;
  try {
    const urlState = getSearchStateFromUrl();
    const state = event.state || (urlState.query ? { view: "search", ...urlState } : { view: "home" });

    if (state.view === "search" && state.query) {
      currentFilter = state.filter || "all";
      advancedMode = false;
      if (searchInput) searchInput.value = state.query;
      applyFilterActiveState(currentFilter);
      await search(state.page || 1, Boolean(state.aiMode), { skipHistory: true });
    } else {
      await resetToHome({ skipHistory: true });
    }
  } finally {
    restoringBrowserState = false;
  }
});

// ═══════════════════════════════════════════
// IMAGE MODAL
// ═══════════════════════════════════════════
function getImageDownloadUrl(imgUrl) {
  return `${activeApiBase}/download-image?url=${encodeURIComponent(imgUrl)}`;
}

function resetDownloadButton(btn) {
  if (!btn) return;
  btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Download Image`;
}

async function downloadImageUrl(imgUrl, btn = null) {
  if (!imgUrl) return;
  const originalHtml = btn ? btn.innerHTML : "";
  try {
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = "Downloading...";
    }

    const a = document.createElement("a");
    a.href = getImageDownloadUrl(imgUrl);
    a.download = "IndiaSearch_Image.jpg";
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();

    if (btn) {
      btn.innerHTML = "Downloaded";
      setTimeout(() => {
        btn.innerHTML = originalHtml || "Download";
        btn.disabled = false;
      }, 1600);
    }
  } catch (err) {
    window.open(imgUrl, "_blank");
    if (btn) {
      btn.innerHTML = originalHtml || "Download";
      btn.disabled = false;
    }
  }
}

function openImageModal(imgUrl) {
  const modal = document.getElementById("imageModal");
  const modalImg = document.getElementById("zoomedImage");
  const btn = document.getElementById("downloadBtn");
  modal.style.display = "flex";
  modalImg.src = imgUrl;
  resetDownloadButton(btn);
  btn.onclick = function (e) {
    e.preventDefault();
    downloadImageUrl(imgUrl, btn);
  };
}

function toggleDownloadMenu() {
  const menu = document.getElementById("downloadMenu");
  menu.style.display = menu.style.display === "none" ? "block" : "none";
}

function closeImageModal() {
  document.getElementById("imageModal").style.display = "none";
  document.getElementById("downloadMenu").style.display = "none";
}
// ═══════════════════════════════════════════
// HOME WIDGETS
// ═══════════════════════════════════════════
function setSearchFocus(q) {
  const input = document.getElementById("searchInput");
  if (input) {
    input.value = q;
    input.focus();
  }
}

async function initHomeWidgets() {
  // Logic removed as per user request to use real-time search intent instead.
}

function renderSmartImageGallery(images) {
    if (!images || images.length === 0) return "";
    
    const items = images.map(img => {
        const cleanUrl = img.image.replace(/'/g, "%27");
        const fallback = mediaFallbackImage(img.title, "Image");
        return `
            <div class="image-card" style="margin-bottom: 0;">
                <div class="image-frame" onclick="openImageModal('${cleanUrl}')">
                    <img src="${img.image}" alt="${escapeHtml(img.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='${fallback}'">
                </div>
                <button type="button" class="image-download-link image-download-mini" onclick="event.stopPropagation(); downloadImageUrl('${cleanUrl}', this)">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download
                </button>
            </div>
        `;
    }).join("");

    return `
        <div class="smart-image-section" style="margin-bottom: 30px;">
            <div class="section-label" style="display:flex; align-items:center; gap:8px; margin-bottom:12px; font-weight:800; font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                Instant Image Gallery
            </div>
            <div class="image-grid" style="grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px;">
                ${items}
            </div>
            <div style="margin-top: 12px; border-bottom: 1px solid var(--border);"></div>
        </div>
    `;
}

function renderWeatherPanel(w) {
  return `
    <div class="weather-card animate-slide-up">
        <div class="weather-main">
            <div class="weather-info">
                <h3 class="weather-city">${w.city}, ${w.country}</h3>
                <p class="weather-label">Localized Climate Report</p>
                <div class="weather-temp">${w.temp}°C</div>
                <p class="weather-desc">${w.desc}</p>
            </div>
            <div class="weather-visual">
                <img src="https://openweathermap.org/img/wn/${w.icon}@4x.png" alt="Weather">
            </div>
        </div>
        <div class="weather-details">
            <div class="w-det-item"><span>Feels like</span><strong>${w.feels_like}°C</strong></div>
            <div class="w-det-item"><span>Humidity</span><strong>${w.humidity}%</strong></div>
            <div class="w-det-item"><span>Wind</span><strong>${w.wind} m/s</strong></div>
        </div>
    </div>
  `;
}

function renderStockPanel(s) {
    if (!s) return "";
    return `
      <div class="stock-card animate-slide-up">
        <h3>${s.symbol || "Stock"}</h3>
        <p class="stock-price">₹${s.price || "N/A"}</p>
        <p class="stock-change ${s.change > 0 ? "positive" : "negative"}">${s.change > 0 ? "▲" : "▼"} ${Math.abs(s.change)}%</p>
      </div>`;
}

function renderNutritionPanel(n) {
    if (!n) return "";
    
    const name = n.name || n.food_name || "Food Item";
    const desc = n.description || "";
    const cals = n.calories || "N/A";
    const nutrients = n.nutrients || {
        protein: n.protein || "0", 
        carbs: n.carbs || "0", 
        fat: n.fat || "0",
        fiber: n.fiber || "0", 
        sugar: n.sugar || "0", 
        sodium: n.sodium || "0"
    };
    const dv = n.daily_values || {
        protein: 0, carbs: 0, fat: 0
    };
    const tags = n.tags || n.health_tags || [];
    const colors = n.tag_colors || tags.map(() => "green");
    const tip = (currentLanguage === 'en' ? n.tip : n.hindi_tip) || "";

    const tagsHtml = tags.map((t, i) => {
        const color = colors[i] || "green";
        const colorMap = { green: "#10b981", amber: "#f59e0b", red: "#ef4444" };
        const bgMap = { green: "rgba(16,185,129,0.1)", amber: "rgba(245,158,11,0.1)", red: "rgba(239,68,68,0.1)" };
        const activeColor = colorMap[color] || colorMap.green;
        const activeBg = bgMap[color] || bgMap.green;
        return `<span class="health-tag" style="background:${activeBg}; color:${activeColor}; border:1px solid ${activeColor}33; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;">${t}</span>`;
    }).join("");
    
    const pPercent = dv.protein || 0;
    const cPercent = dv.carbs || 0;
    const fPercent = dv.fat || 0;

    return `
      <div class="nutrition-card animate-slide-up" style="background:var(--bg-card); border:1px solid var(--border); border-radius:24px; padding:24px; box-shadow:0 10px 30px rgba(0,0,0,0.1); margin-bottom:20px;">
        <div class="nutrition-header" style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
            <div>
                <h3 style="font-size:22px; margin:0;">${name}</h3>
                <p style="font-size: 12px; color: var(--text-muted); font-weight:500; margin-top:4px;">
                    ${desc}
                </p>
            </div>
            <div class="nutrition-calories" style="font-size:26px; font-weight:800; color:#f59e0b;">${cals} <span style="font-size:12px; font-weight:400; color:var(--text-muted);">kcal</span></div>
        </div>
        
        <div class="nutrition-tags" style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">${tagsHtml}</div>

        <div class="nutrition-bars" style="margin: 25px 0;">
            <div class="nut-bar-item" style="margin-bottom:15px;">
                <div class="nut-bar-label" style="display:flex; justify-content:space-between; font-size:12px; font-weight:700; margin-bottom:6px;">
                    <span>Protein</span><span style="color:#10b981;">${nutrients.protein}g</span>
                </div>
                <div class="nut-bar-bg" style="height:10px; background:rgba(0,0,0,0.05); border-radius:10px; overflow:hidden;">
                    <div class="nut-bar-fill" style="width: ${pPercent}%; height:100%; background:#10b981; border-radius:10px; transition: width 1s ease;"></div>
                </div>
            </div>
            <div class="nut-bar-item" style="margin-bottom:15px;">
                <div class="nut-bar-label" style="display:flex; justify-content:space-between; font-size:12px; font-weight:700; margin-bottom:6px;">
                    <span>Carbs</span><span style="color:#f59e0b;">${nutrients.carbs}g</span>
                </div>
                <div class="nut-bar-bg" style="height:10px; background:rgba(0,0,0,0.05); border-radius:10px; overflow:hidden;">
                    <div class="nut-bar-fill" style="width: ${cPercent}%; height:100%; background:#f59e0b; border-radius:10px; transition: width 1s ease;"></div>
                </div>
            </div>
            <div class="nut-bar-item">
                <div class="nut-bar-label" style="display:flex; justify-content:space-between; font-size:12px; font-weight:700; margin-bottom:6px;">
                    <span>Fat</span><span style="color:#ef4444;">${nutrients.fat}g</span>
                </div>
                <div class="nut-bar-bg" style="height:10px; background:rgba(0,0,0,0.05); border-radius:10px; overflow:hidden;">
                    <div class="nut-bar-fill" style="width: ${fPercent}%; height:100%; background:#ef4444; border-radius:10px; transition: width 1s ease;"></div>
                </div>
            </div>
        </div>

        <div class="nutrition-grid mini" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:12px; margin-bottom:25px;">
            <div class="nut-item" style="background:var(--bg-alt); padding:12px; border-radius:16px; text-align:center; border:1px solid var(--border);">
                <span style="display:block; font-size:11px; color:var(--text-muted); margin-bottom:4px;">Fiber</span>
                <strong style="font-size:16px;">${nutrients.fiber || "0"}g</strong>
            </div>
            <div class="nut-item" style="background:var(--bg-alt); padding:12px; border-radius:16px; text-align:center; border:1px solid var(--border);">
                <span style="display:block; font-size:11px; color:var(--text-muted); margin-bottom:4px;">Sugar</span>
                <strong style="font-size:16px;">${nutrients.sugar || "0"}g</strong>
            </div>
            <div class="nut-item" style="background:var(--bg-alt); padding:12px; border-radius:16px; text-align:center; border:1px solid var(--border);">
                <span style="display:block; font-size:11px; color:var(--text-muted); margin-bottom:4px;">Sodium</span>
                <strong style="font-size:16px;">${nutrients.sodium || "0"}mg</strong>
            </div>
        </div>

        ${tip ? `<div class="nutrition-tip" style="background:rgba(59,130,246,0.08); padding:18px; border-radius:18px; font-size:14px; line-height:1.6; border-left:5px solid #3b82f6; color:var(--text-primary);">
            💡 <b>Expert AI Tip:</b> ${tip}
        </div>` : ""}
      </div>`;
}

// ═══════════════════════════════════════════
// GOOGLE AI MODE RENDERER (aim-* system)
// ═══════════════════════════════════════════
function renderGoogleStyleAIMode(data) {
    if (!data || !data.answer) return '';

    const query = data.query || '';
    const answer = data.answer || '';
    const sources = data.sources || [];

    // ── Right-side sources HTML (simple clean links with favicon) ──
    const rightSourcesHtml = sources.slice(0, 6).map((src, idx) => {
        let domain = 'source';
        try { domain = new URL(src.url || '').hostname.replace(/^www\./, ''); } catch(e) {}
        const fav = `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
        return `
        <a href="${src.url || '#'}" target="_blank" rel="noopener" class="prx-right-source">
          <span class="prx-right-source-n">${idx + 1}</span>
          <img src="${fav}" class="prx-right-source-fav" onerror="this.style.display='none'" alt="">
          <span class="prx-right-source-title" title="${escapeHtml(src.title || domain)}">${escapeHtml(src.title || domain)}</span>
        </a>`;
    }).join('');

    // ── Follow-up chips ──
    const followUps = generateFollowUps(query);
    const chipsHtml = followUps.map(q =>
        `<button class="prx-followup-chip" onclick="aiFollowup('${q.replace(/'/g, "\\'")}')">
           <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
           <span>${escapeHtml(q)}</span>
         </button>`
    ).join('');

    const answeredHtml = renderMarkdownWithCitations(answer, sources);
    const uid = `prx_${Date.now()}`;

    const html = `
    <div class="prx-answer-container" id="${uid}">
      <!-- Query Title -->
      <h1 class="prx-query-title">${escapeHtml(query)}</h1>

      <!-- Split Layout (Answer on Left, Links on Right) -->
      <div class="prx-split-layout">
        <div class="prx-answer-column">
          <div class="prx-answer-body">${answeredHtml}</div>
        </div>
        
        ${sources.length > 0 ? `
          <div class="prx-sidebar-column">
            <div class="prx-sidebar-title">References</div>
            <div class="prx-right-sources-list">
              ${rightSourcesHtml}
            </div>
          </div>
        ` : ''}
      </div>

      <!-- Related Section -->
      ${chipsHtml ? `
        <div class="prx-section-header" style="margin-top:24px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:6px; vertical-align:middle;"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          Related
        </div>
        <div class="prx-chips-container">${chipsHtml}</div>
      ` : ''}
      
      <div class="prx-footer">
        <span>IndiaSearch AI</span> • <span>AI answers may contain errors</span>
      </div>
    </div>`;

    setTimeout(() => {
        const el = document.getElementById(uid);
        if (el) el.classList.add('prx-visible');
    }, 60);

    return html;
}

function renderSportsPanel(matches) {

  if (!matches || matches.length === 0) return "";
  
  const matchHtml = matches.map(m => {
    const teamParts = m.name.split(" vs ");
    const teamA = teamParts[0] || "T1";
    const teamB = teamParts[1] || "T2";
    
    const s = m.score || { r: 0, w: 0, o: 0, inning: "Live" };
    const liveScore = `${s.r}/${s.w}`;
    const details = `${s.o} overs • ${s.inning}`;
    
    // Date & Updated Timestamp for Trust
    const matchDate = m.date || "Today";
    const syncTime = m.updated_at || "Just now";
    
    return `
      <div class="score-card elite-card animate-slide-up">
          <div class="sc-trust-bar">
              <span class="sc-date">📅 ${matchDate}</span>
              <span class="sc-sync-badge">✅ Verified Sync: ${syncTime}</span>
          </div>

          <div class="sc-header" style="margin-top:10px;">
              <span class="sc-badge ipl-badge">${m.matchType || 'LIVE'}</span>
              <span class="sc-live-dot"></span>
              <span class="sc-status">${m.status}</span>
          </div>
          
          <div class="sc-teams flex-row">
              <div class="sc-team-side">
                  <div class="team-initials">${teamA.charAt(0)}</div>
                  <span class="sc-team-name">${teamA.split(',')[0]}</span>
              </div>
              <div class="sc-vs-circle">VS</div>
              <div class="sc-team-side">
                  <div class="team-initials secondary">${teamB.charAt(0)}</div>
                  <span class="sc-team-name">${teamB.split(',')[0]}</span>
              </div>
          </div>
          
          <div class="sc-main-details">
              <div class="sc-score-big">${liveScore}</div>
              <div class="sc-overs-small">${details}</div>
          </div>
          
          <div class="sc-player-stats">
              <div class="player-stat">
                  <span class="ps-label">🏏 Striker</span>
                  <span class="ps-val highlighted">${m.striker || '---'}</span>
              </div>
              <div class="player-stat">
                  <span class="ps-label">Non-Stk</span>
                  <span class="ps-val">${m.non_striker || '---'}</span>
              </div>
              <div class="player-stat">
                  <span class="ps-label">🎳 Bowler</span>
                  <span class="ps-val highlighted">${m.bowler || '---'}</span>
              </div>
          </div>
          
          <div class="sc-footer-venue">🏟️ ${m.venue}</div>
      </div>
    `;
  }).join("");

  return `
    <div class="sports-section">
      <div class="section-label">⚡ Real-Time Live Scoreboard</div>
      <div class="score-grid-elite">${matchHtml}</div>
    </div>
  `;
}

function renderStockPanel(s) {
  if (!s) return "";
  const isUp = parseFloat(s.change) >= 0;
  const colorClass = isUp ? "stock-up" : "stock-down";
  const arrow = isUp ? "▲" : "▼";

  return `
    <div class="finance-panel">
      <div class="fin-header">📈 Market Summary</div>
      <div class="fin-content">
        <div class="fin-symbol">${s.symbol}</div>
        <div class="fin-main">
          <div class="fin-price">${parseFloat(s.price).toFixed(2)}</div>
          <div class="fin-delta ${colorClass}">${arrow} ${parseFloat(s.change).toFixed(2)} (${s.change_percent})</div>
        </div>
        <div class="fin-extra">
          <div class="fin-item"><span>High</span> ${parseFloat(s.high).toFixed(2)}</div>
          <div class="fin-item"><span>Low</span> ${parseFloat(s.low).toFixed(2)}</div>
          <div class="fin-item"><span>Vol</span> ${parseInt(s.volume || 0).toLocaleString()}</div>
        </div>
        <div class="fin-footer">As of ${s.last_trading_day} (Real-time data)</div>
      </div>
    </div>
  `;
}

// ═══════════════════════════════════════════
// DOM READY
// ═══════════════════════════════════════════
function confirmAgeAndSearch(query, pageNumber, aiMode) {
  // Store confirmation in session storage so we don't ask again this session
  sessionStorage.setItem("age_verified", "true");
  search(pageNumber, aiMode);
}

// Ensure the age_verified flag is sent if present
const originalFetchWithApiFallback = fetchWithApiFallback;
fetchWithApiFallback = async function(path, options = {}) {
  if (sessionStorage.getItem("age_verified") === "true") {
    const url = new URL(path, window.location.origin);
    url.searchParams.set("age_verified", "true");
    path = url.pathname + url.search;
  }
  return originalFetchWithApiFallback(path, options);
}

document.addEventListener("DOMContentLoaded", async () => {
  const hasSavedLanguage = Boolean(localStorage.getItem(LANGUAGE_STORAGE_KEY));
  
  // If no saved language, auto-detected language is already in currentLanguage
  // Save it so future visits remember it
  if (!hasSavedLanguage) {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, currentLanguage);
  }
  
  // Sync dropdown to current language
  if (languageSelect) languageSelect.value = currentLanguage;
  
  renderHistory();
  renderTrending();
  initHomeWidgets();
  await applySelectedLanguage(currentLanguage);
  
  // Show language modal only on first ever visit so user can override auto-detection
  if (!hasSavedLanguage) {
    const modal = document.getElementById("languageModal");
    if (modal) modal.style.display = "flex";
  }

  const initialState = getSearchStateFromUrl();
  if (initialState.query) {
    currentFilter = initialState.filter || "all";
    activeQuery = initialState.query;
    if (searchInput) searchInput.value = initialState.query;
    applyFilterActiveState(currentFilter);
    writeBrowserSearchState(initialState, true);
    search(initialState.page, initialState.aiMode, { skipHistory: true });
  } else {
    writeBrowserSearchState({ query: "" }, true);
  }
});



// ===== CALORY SCANNER (IndiaSearch AI Powered) =====

function showCaloryScanner() {
  const results = document.getElementById('results');
  const calSection = document.getElementById('calory-section');
  if (results) results.style.display = 'none';
  if (calSection) calSection.style.display = 'block';
}

async function analyzeNutritionByText(query) {
  const res = await fetchWithApiFallback('/api/nutrition/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || "Nutrition analysis failed");
  return data;
}

async function analyzeNutritionByImage(base64, mediaType = 'image/jpeg') {
  const res = await fetchWithApiFallback('/api/nutrition/image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_base64: base64, media_type: mediaType })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || "Nutrition image analysis failed");
  return data;
}

function compressImage(file, maxWidth = 800) {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    const img = new Image();
    img.onload = () => {
      const ratio = Math.min(maxWidth / img.width, 1);
      canvas.width = img.width * ratio;
      canvas.height = img.height * ratio;
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
      const base64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
      resolve(base64);
    };
    img.src = URL.createObjectURL(file);
  });
}

// ── ABOUT PAGE CONTROLS ──
function openAboutPage(e) {
  if (e) e.preventDefault();
  const overlay = document.getElementById("aboutOverlay");
  if (overlay) {
    overlay.style.display = "flex";
    document.body.style.overflow = "hidden"; // Prevent background scroll
  }
}

function closeAboutPage() {
  const overlay = document.getElementById("aboutOverlay");
  if (overlay) {
    overlay.style.display = "none";
    document.body.style.overflow = "auto";
  }
}

// ── ABOUT PAGE CONTROLS & DYNAMIC CONTENT ──
const ADMIN_IDENTIFIER = "amitesh@indiasearch.site";

async function openAboutPage(e) {
  if (e) e.preventDefault();
  const overlay = document.getElementById("aboutOverlay");
  if (overlay) {
    const founderVideo = overlay.querySelector("iframe[data-src]");
    if (founderVideo && !founderVideo.src) {
      founderVideo.src = founderVideo.dataset.src;
    }
    overlay.style.display = "flex";
    document.body.style.overflow = "hidden";
    checkAdminStatus();
    loadAboutContent();
  }
}

function closeAboutPage() {
  const overlay = document.getElementById("aboutOverlay");
  if (overlay) {
    overlay.style.display = "none";
    document.body.style.overflow = "auto";
  }
}

function checkAdminStatus() {
  const panel = document.getElementById("aboutAdminPanel");
  const mediaForm = document.getElementById("mediaUploadForm");
  if (!panel) return;
  panel.style.display = "block";
  if (mediaForm) mediaForm.style.display = "none";
}

function getAboutOwnerToken() {
  return appState.guestId || localStorage.getItem("guestSession") || "";
}

async function loadAboutContent() {
  try {
    const res = await fetchWithApiFallback('/about-content');
    const data = await res.json();
    renderAboutPublications(data.publications);
    renderAboutMedia(data.media);
  } catch (err) {
    console.error("Failed to load about content:", err);
  }
}

function renderAboutPublications(pubs) {
  const container = document.querySelector(".publication-list");
  if (!container) return;
  
  if (!pubs || pubs.length === 0) {
    container.innerHTML = `
      <div class="pub-empty-state">
        <strong>No research papers yet</strong>
        <span>Submitted papers will appear here with topic, duration, abstract, and PDF access.</span>
      </div>`;
    return;
  }

  const ownerToken = getAboutOwnerToken();
  const currentIdentifier = "";
  const isAdminUser = false;

  container.innerHTML = pubs.map(p => {
    const canDelete = isAdminUser || (ownerToken && p.owner_session_token === ownerToken) || (currentIdentifier && p.owner_identifier === currentIdentifier);
    const topic = p.topic ? `<span><b>Topic:</b> ${escapeHtml(p.topic)}</span>` : "";
    const duration = p.research_duration ? `<span><b>Research time:</b> ${escapeHtml(p.research_duration)}</span>` : "";
    const unique = p.unique_points ? `<p class="pub-unique"><b>Unique:</b> ${escapeHtml(p.unique_points)}</p>` : "";
    const author = p.owner_identifier ? `<span><b>Uploaded by:</b> ${escapeHtml(p.owner_identifier)}</span>` : "";

    return `
    <div class="pub-item">
      <span class="pub-icon">${p.pub_type === 'book' ? 'B' : 'PDF'}</span>
      <div class="pub-info">
        <div class="pub-title-row">
          <h4>${escapeHtml(p.title)}</h4>
          ${canDelete ? `<button class="pub-delete-btn" onclick="deletePublication(${p.id})" title="Delete paper">Delete</button>` : ""}
        </div>
        <div class="pub-meta">${topic}${duration}${author}</div>
        ${unique}
        <p>${escapeHtml(p.description || "")}</p>
        <a href="${activeApiBase}${p.file_url}" target="_blank" class="view-link">Open ${p.pub_type === 'book' ? 'Book' : 'Paper'} PDF →</a>
      </div>
    </div>
  `}).join("");
}

function renderAboutMedia(media) {
  const container = document.querySelector(".media-grid-mini");
  if (!container) return;
  
  if (!media || media.length === 0) {
    container.innerHTML = `<div class="media-placeholder"><span>Gallery Empty</span></div>`;
    return;
  }

  container.innerHTML = media.map(m => {
    let thumb = m.thumbnail_url ? `${activeApiBase}${m.thumbnail_url}` : "https://via.placeholder.com/150";
    if (!m.thumbnail_url && m.video_url.includes("youtube.com")) {
       const id = m.video_url.split("v=")[1]?.split("&")[0];
       if (id) thumb = `https://img.youtube.com/vi/${id}/mqdefault.jpg`;
    }

    return `
    <div class="media-item-wrap" onclick="window.open('${m.video_url}', '_blank')">
      <img src="${thumb}" alt="${m.title}" class="media-thumb-img">
      <div class="media-title-overlay">${m.title}</div>
    </div>
  `}).join("");
}

async function handleAboutUpload(event, type) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  formData.append("session_token", getAboutOwnerToken());

  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = "Uploading...";

  try {
    const endpoint = type === 'publication' ? '/about-content/publication' : '/about-content/media';
    const res = await fetchWithApiFallback(endpoint, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      alert(data.message);
      form.reset();
      loadAboutContent();
    } else {
      alert(data.error || "Upload failed");
    }
  } catch (err) {
    alert("Server error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

async function deletePublication(pubId) {
  if (!confirm("Delete this research paper?")) return;
  try {
    const token = encodeURIComponent(getAboutOwnerToken());
    const res = await fetchWithApiFallback(`/about-content/publication/${pubId}?session_token=${token}`, {
      method: "DELETE"
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Delete failed");
    loadAboutContent();
  } catch (err) {
    alert(err.message);
  }
}

// ── Settings & Legal Modals Controller ──
function openSettingsModal(e) {
  if (e) e.preventDefault();
  
  // Load current settings into DOM inputs
  const selectSafe = document.getElementById("settingsSafeSearch");
  const selectCount = document.getElementById("settingsResultsCount");
  const checkAutoPlay = document.getElementById("settingsAutoPlayVoice");
  
  if (selectSafe) selectSafe.value = appSettings.safeSearch;
  if (selectCount) selectCount.value = String(appSettings.resultsCount);
  if (checkAutoPlay) checkAutoPlay.checked = appSettings.autoPlayVoice;
  
  const modal = document.getElementById("settingsModal");
  if (modal) modal.style.display = "flex";
}

function closeSettingsModal() {
  const modal = document.getElementById("settingsModal");
  if (modal) modal.style.display = "none";
}

function saveAndCloseSettings() {
  const selectSafe = document.getElementById("settingsSafeSearch");
  const selectCount = document.getElementById("settingsResultsCount");
  const checkAutoPlay = document.getElementById("settingsAutoPlayVoice");
  
  if (selectSafe) {
    appSettings.safeSearch = selectSafe.value;
    localStorage.setItem("safeSearch", selectSafe.value);
  }
  if (selectCount) {
    const countVal = parseInt(selectCount.value, 10) || 10;
    appSettings.resultsCount = countVal;
    localStorage.setItem("resultsCount", String(countVal));
  }
  if (checkAutoPlay) {
    appSettings.autoPlayVoice = checkAutoPlay.checked;
    localStorage.setItem("autoPlayVoice", String(checkAutoPlay.checked));
  }
  
  closeSettingsModal();
  alert("Settings saved successfully!");
  
  // Re-run search if there is an active search query to apply new settings
  if (activeQuery) {
    const isAiMode = searchBoxAi && searchBoxAi.style.display !== "none";
    search(1, isAiMode, { replaceHistory: true });
  }
}

function openTermsModal(e) {
  if (e) e.preventDefault();
  const modal = document.getElementById("termsModal");
  if (modal) modal.style.display = "flex";
}

function closeTermsModal() {
  const modal = document.getElementById("termsModal");
  if (modal) modal.style.display = "none";
}

function openPrivacyModal(e) {
  if (e) e.preventDefault();
  const modal = document.getElementById("privacyModal");
  if (modal) modal.style.display = "flex";
}

function closePrivacyModal() {
  const modal = document.getElementById("privacyModal");
  if (modal) modal.style.display = "none";
}
