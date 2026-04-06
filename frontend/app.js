// ═══════════════════════════════════════════
//  INDIASEARCH — app.js (Refactored)
// ═══════════════════════════════════════════

const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const LOCAL_API_BASE = "http://127.0.0.1:8000";
const PROD_API_BASE = "https://indiasearch-production.up.railway.app";
let activeApiBase = isLocalHost ? LOCAL_API_BASE : PROD_API_BASE;

// ── DOM Refs ──
const searchInput = document.getElementById("searchInput");
const resultsBox = document.getElementById("results");
const aiSummaryBox = document.getElementById("aiSummary");
const micButton = document.getElementById("micButton");
const languageSelect = document.getElementById("languageSelect");
const cameraInput = document.getElementById("cameraInput");
const scanStatus = document.getElementById("scanStatus");
const authModal = document.getElementById("authModal");
const authMessage = document.getElementById("authMessage");
const authButton = document.getElementById("authButton");

const aiSearchInput = document.getElementById("aiSearchInput");
const searchBoxStandard = document.getElementById("searchBoxStandard");
const searchBoxAi = document.getElementById("searchBoxAi");
const aiPdfPreview = document.getElementById("aiPdfPreview");
const mainWrap = document.querySelector(".main-wrap");

/** ── AI Mode Manager ── **/
function enterAiMode() {
    if (searchBoxStandard) searchBoxStandard.style.display = "none";
    if (searchBoxAi) {
        searchBoxAi.style.display = "flex";
        if (mainWrap) mainWrap.classList.add("ai-active");
        if (aiSearchInput) {
            aiSearchInput.focus();
            if (searchInput.value) aiSearchInput.value = searchInput.value;
        }
    }
}

function exitAiMode() {
    if (searchBoxStandard) searchBoxStandard.style.display = "flex";
    if (searchBoxAi) {
        searchBoxAi.style.display = "none";
        if (mainWrap) mainWrap.classList.remove("ai-active");
    }
    if (searchInput) searchInput.focus();
}

function autoExpand(t) {
    t.style.height = 'auto';
    t.style.height = (t.scrollHeight) + 'px';
}

function searchAI() {
    if (!aiSearchInput || !aiSearchInput.value.trim()) return;
    searchInput.value = aiSearchInput.value;
    
    // Clear and reset AI input immediately for next question
    aiSearchInput.value = "";
    aiSearchInput.style.height = "auto";
    aiSearchInput.focus();
    
    search(1, true); // Trigger AI Mode search
}

if (aiSearchInput) {
    aiSearchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            searchAI();
        }
    });
}
const userPill = document.getElementById("userPill");
const userEmail = document.getElementById("userEmail");
const userAvatar = document.getElementById("userAvatar");
const profileModal = document.getElementById("profileModal");
const profileSummary = document.getElementById("profileSummary");
const profileHistory = document.getElementById("profileHistory");
const heroSection = document.getElementById("heroSection");
const searchFiltersDiv = document.getElementById("searchFilters");
const trendingContainer = document.getElementById("trendingContainer");
const historyBox = document.getElementById("searchHistory");
const paginationContainer = document.getElementById("pagination");
const siteHeader = document.getElementById("siteHeader");

let recognition;
let isListening = false;
let attachedScan = null;
let authState = {
  sessionToken: localStorage.getItem("sessionToken") || "",
  user: JSON.parse(localStorage.getItem("authUser") || "null"),
  guestSession: localStorage.getItem("guestSession") || `guest_${Math.random().toString(36).substr(2, 9)}`
};
if (!localStorage.getItem("guestSession")) {
  localStorage.setItem("guestSession", authState.guestSession);
}

// ── Header scroll effect ──
window.addEventListener("scroll", () => {
  siteHeader.classList.toggle("scrolled", window.scrollY > 10);
});

// ── Fetch helpers ──
async function fetchWithApiFallback(path) {
  const candidates = isLocalHost
    ? [activeApiBase, PROD_API_BASE].filter((b, i, a) => a.indexOf(b) === i)
    : [activeApiBase];
  let lastError = null;
  for (const base of candidates) {
    try {
      const r = await fetch(`${base}${path}`);
      activeApiBase = base;
      return r;
    } catch (e) { lastError = e; }
  }
  throw lastError || new Error("Failed to reach the backend service");
}

async function apiJsonRequest(path, payload, method = "POST") {
  const candidates = isLocalHost
    ? [activeApiBase, PROD_API_BASE].filter((b, i, a) => a.indexOf(b) === i)
    : [activeApiBase];
  let lastError = null;
  for (const base of candidates) {
    try {
      const r = await fetch(`${base}${path}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: payload ? JSON.stringify(payload) : undefined
      });
      activeApiBase = base;
      return r;
    } catch (e) { lastError = e; }
  }
  throw lastError || new Error("Failed to reach the backend service");
}

// ═══════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════
function toggleMode() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const next = isDark ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}

// Apply saved theme on load
(function applyTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) document.documentElement.setAttribute("data-theme", saved);
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
  "Ind VS Aus Live Score",
  "Best smartphones under 20000",
  "Python Developer salaries",
  "Top startups in Bangalore"
];

function renderTrending() {
  const grid = document.querySelector(".trending-grid");
  if (!grid) return;
  grid.innerHTML = TRENDING_KEYWORDS.map(k => `
    <div class="trending-item" onclick="searchInput.value='${k}'; search();">
      <span class="trending-icon">🔥</span>${k}
    </div>`).join("");
}

// ═══════════════════════════════════════════
// SEARCH FILTERS
// ═══════════════════════════════════════════
let currentFilter = "all";

function setFilter(type) {
  currentFilter = type;
  document.querySelectorAll(".filter-pill").forEach(b => b.classList.remove("active"));
  const labels = { all: "All", news: "News", images: "Images", videos: "Videos" };
  const btn = Array.from(document.querySelectorAll(".filter-pill")).find(b => b.textContent.trim().includes(labels[type]));
  if (btn) btn.classList.add("active");
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

languageSelect.addEventListener("change", async () => {
  searchInput.placeholder = await translateText("Kuch bhi search karo…", languageSelect.value);
});

// ═══════════════════════════════════════════
// VOICE SEARCH
// ═══════════════════════════════════════════
const STT_LOCALES = {
  en: "en-IN", hi: "hi-IN", as: "as-IN", bn: "bn-IN", brx: "en-IN", doi: "en-IN",
  gu: "gu-IN", kn: "kn-IN", ks: "ur-IN", gom: "mr-IN", mai: "hi-IN", ml: "ml-IN",
  mni: "en-IN", mr: "mr-IN", ne: "ne-NP", or: "or-IN", pa: "pa-IN", sa: "hi-IN",
  sat: "en-IN", sd: "ur-IN", ta: "ta-IN", te: "te-IN", ur: "ur-IN"
};

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.onstart = () => {
    isListening = true;
    micButton.classList.add("listening");
    searchInput.placeholder = "सुन रहा हूँ… Listening…";
  };
  recognition.onresult = e => {
    searchInput.value = e.results[0][0].transcript;
    search();
  };
  recognition.onend = () => {
    isListening = false;
    micButton.classList.remove("listening");
    searchInput.placeholder = "Kuch bhi search karo…";
  };
  recognition.onerror = () => {
    isListening = false;
    micButton.classList.remove("listening");
  };
}

function toggleVoiceSearch() {
  if (!recognition) { alert("Voice search not supported in your browser"); return; }
  isListening ? recognition.stop() : (() => {
    recognition.lang = STT_LOCALES[languageSelect.value] || "en-IN";
    recognition.start();
  })();
}

// ── Camera ──
function openCameraPicker() { if (cameraInput) cameraInput.click(); }
if (cameraInput) {
  cameraInput.addEventListener("change", async () => {
    const f = cameraInput.files?.[0];
    if (!f) return;
    
    attachedScan = f;
    if (scanStatus) scanStatus.innerHTML = `⏳ Analyzing Image: <b>${f.name}</b>...`;

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
            if (scanStatus) scanStatus.innerHTML = `✅ <b>SCAN RESULT:</b> <a href="${code.data}" target="_blank" style="color:var(--neon-glow)">${code.data}</a>`;
            searchInput.value = code.data;
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
  if (authState.sessionToken) formData.append("session_token", authState.sessionToken);

  try {
    const res = await fetch(`${activeApiBase}/visual-search`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      if (scanStatus) scanStatus.innerHTML = `✨ <b>Recognition Complete:</b> ${data.identity || "Possible matches found below."}`;
      // Put recognition result in search bar and trigger AI Mode with social keywords
      const identityQuery = data.identity || `Search for details about ${file.name}`;
      searchInput.value = `${identityQuery} official social media links instagram facebook twitter x`;
      search(1, true); // Automatic Ask AI trigger
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
    // Prefer sessionToken, fallback to persistent guestSession
    const finalSess = authState.sessionToken || authState.guestSession;
    formData.append("session_token", finalSess);

    try {
      const res = await fetch(`${activeApiBase}/upload-pdf`, {
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
// HOME RESET
// ═══════════════════════════════════════════
function resetToHome() {
  searchInput.value = "";
  resultsBox.innerHTML = "";
  aiSummaryBox.innerHTML = "";
  if (paginationContainer) paginationContainer.innerHTML = "";
  if (searchFiltersDiv) searchFiltersDiv.style.display = "none";
  if (trendingContainer) trendingContainer.style.display = "block";
  if (historyBox) historyBox.style.display = "flex";
  if (heroSection) heroSection.classList.remove("hidden");
  if (scanStatus) scanStatus.textContent = "";
  closeAutocomplete();
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

// ═══════════════════════════════════════════
// MAIN SEARCH
// ═══════════════════════════════════════════
async function search(pageNumber = 1, aiMode = false) {
  let query = searchInput.value.trim();

  if (!query) {
    resetToHome();
    return;
  }

  closeAutocomplete();

  // Transition to search state
  if (heroSection) heroSection.classList.add("hidden");
  if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
  if (trendingContainer) trendingContainer.style.display = "none";
  if (historyBox) historyBox.style.display = "none";
  if (pageNumber === 1) saveHistory(query);

  const targetLang = languageSelect.value;

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
  aiSummaryBox.innerHTML = "";

  try {
    document.documentElement.setAttribute("data-ai-mode", aiMode ? "true" : "false");
    const params = new URLSearchParams({ q: query, page: String(pageNumber), filter: currentFilter, ai_mode: String(aiMode) });
    const finalSess = authState.sessionToken || authState.guestSession;
    params.set("session_token", finalSess);

    const res = await fetchWithApiFallback(`/search?${params}`);
    let data;
    try { data = await res.json(); } catch {
      throw new Error(`Backend returned non-JSON (status ${res.status})`);
    }

    if (!res.ok) {
      if (res.status === 401) {
        openAuthModal();
        setAuthMessage("Please login to use IndiaSearch.", true);
        resultsBox.innerHTML = "";
        if (paginationContainer) paginationContainer.innerHTML = "";
        return;
      }
      throw new Error(data.error || `Backend error (status ${res.status})`);
    }

    if (data.error) {
      resultsBox.innerHTML = `<div class="state-error"><span class="state-error-icon">⚠️</span>${await translateText(data.error, targetLang)}</div>`;
      return;
    }

    // ── Weather Card Integration ──
    let weatherHtml = "";
    if (data.weather_data && pageNumber === 1) {
      const w = data.weather_data;
      const wLabel = await translateText("Weather in", targetLang);
      const feeLabel = await translateText("Feels like", targetLang);
      const humLabel = await translateText("Humidity", targetLang);
      const windLabel = await translateText("Wind", targetLang);
      
      weatherHtml = `
        <div class="weather-card animate-slide-up">
            <div class="weather-main">
                <div class="weather-info">
                    <h3 class="weather-city">${w.city}, ${w.country}</h3>
                    <p class="weather-label">${wLabel}</p>
                    <div class="weather-temp">${w.temp}°C</div>
                    <p class="weather-desc">${w.desc}</p>
                </div>
                <div class="weather-visual">
                    <img src="https://openweathermap.org/img/wn/${w.icon}@4x.png" alt="Weather Icon">
                </div>
            </div>
            <div class="weather-details">
                <div class="w-det-item"><span>${feeLabel}</span><strong>${w.feels_like}°C</strong></div>
                <div class="w-det-item"><span>${humLabel}</span><strong>${w.humidity}%</strong></div>
                <div class="w-det-item"><span>${windLabel}</span><strong>${w.wind} m/s</strong></div>
            </div>
        </div>
      `;
    }

    // ── AI Summary / Overview ──
    let summaryHtml = "";
    let shouldAnimate = false;
    let rawText = "";

    if (data.summary && pageNumber === 1) {
      rawText = data.summary;
      if (aiMode) {
        shouldAnimate = true;
        summaryHtml = `
          <div class="ai-overview-card">
            <div class="ai-overview-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <span>Ask AI</span>
            </div>
            <div class="ai-overview-text" id="streamingAI"></div>
            <div class="ai-source-strip" id="aiSources"></div>
          </div>`;
      } else {
        summaryHtml = `
          <div class="summary-card">
            <div class="summary-label">✨ AI Summary</div>
            <div class="summary-text">${rawText}</div>
          </div>`;
      }
    }

    // ── Pre-render Smart Panels (Weather, AI Summary, Wikipedia) ──
    let wikiHtml = "";
    if (!aiMode && data.knowledge_panel && pageNumber === 1 && currentFilter === "all") {
      const kp = data.knowledge_panel;
      const [kt, ks] = await Promise.all([translateText(kp.title, targetLang), translateText(kp.snippet, targetLang)]);
      const imgTag = kp.image
        ? `<img src="${kp.image}" alt="${kt}" style="float:right;margin:0 0 12px 16px;width:110px;height:110px;object-fit:cover;border-radius:10px;cursor:zoom-in;" onclick="openImageModal('${kp.image.replace("400px-", "1024px-")}')">`
        : "";
      wikiHtml = `
        <div class="knowledge-card" style="overflow:hidden;">
          ${imgTag}
          <h3>📚 ${kt}</h3>
          <p class="knowledge-preview">${ks}</p>
          <details class="knowledge-overview">
            <summary>Overview</summary>
            <p class="knowledge-full" style="margin-top:10px;">${ks}</p>
          </details>
          <a href="${kp.url}" target="_blank">Wikipedia →</a>
        </div>`;
    }

    // Set AI Summary and AI Link Section
    aiSummaryBox.innerHTML = summaryHtml + wikiHtml;

    // Trigger Animation if needed
    if (shouldAnimate) {
      const target = document.getElementById("streamingAI");
      if (target) {
        let i = 0;
        const speed = 15; // ms
        function typeWriter() {
           if (i < rawText.length) {
              const char = rawText.charAt(i);
              target.innerHTML += char === "\n" ? "<br>" : char;
              i++;
              setTimeout(typeWriter, speed);
              if (mainWrap) mainWrap.scrollTop = mainWrap.scrollHeight;
           }
        }
        typeWriter();
      }
    }

    // ── Weather Panel (Smart Answer) ──
    if (data.weather) {
      aiSummaryBox.innerHTML = renderWeatherPanel(data.weather) + aiSummaryBox.innerHTML;
    }

    if (data.sports) {
      aiSummaryBox.innerHTML = renderSportsPanel(data.sports) + aiSummaryBox.innerHTML;
    }

    if (data.stocks) {
      aiSummaryBox.innerHTML = renderStockPanel(data.stocks) + aiSummaryBox.innerHTML;
    }

    if (currentFilter === "images" && data.warning) {
      const tw = await translateText(data.warning, targetLang);
      aiSummaryBox.innerHTML = `<div class="image-warning-bar">${tw}</div>` + aiSummaryBox.innerHTML;
    }

    // If NO results at all (no web results AND no weather/summary/sports/stocks)
    const hasResults = (data.results && data.results.length > 0);
    const hasSmartAnswer = (data.weather || data.summary || data.knowledge_panel || data.sports || data.stocks);

    if (!hasResults && !hasSmartAnswer) {
      const noRes = await translateText("No results found", targetLang);
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
        translateText("Visit Website", targetLang)
      ]);

      const isNews = (currentFilter === "news") || (data.is_news_routing === true);
      const isImages = currentFilter === "images";
      let host = item.url;
      try { host = new URL(item.url).hostname.replace(/^www\./, ""); } catch { }

      if (aiMode) {
        // Render Source Badges for AI
        const sourceHtml = `
          <div class="ai-link-item">
            <span class="host-name">${host}</span>
            <a href="${item.url}" target="_blank" class="ai-link-title">${tt}</a>
          </div>`;
        
        // Append to source strip if on page 1
        if (pageNumber === 1) {
             const strip = document.getElementById("aiSources");
             if (strip) strip.innerHTML += sourceHtml;
        }
        return ""; // Don't return regular results in full AI mode?
        // Actually, user said chat mode, so we hide normal results or show them below.
        // Let's show only top 3 as small references.
      }

      if (isImages) {
        const isFallback = (item.snippet || "").includes("Fallback Preview");
        return `
          <div class="image-card">
            <div class="image-frame" onclick="openImageModal('${item.url}')">
              <img src="${item.url}" alt="${tt}" loading="lazy" referrerpolicy="no-referrer">
            </div>
            <div class="image-meta">
              ${isFallback ? `<span class="image-badge">Fallback</span>` : ""}
              <div class="image-title">${tt}</div>
              <div class="image-source">${ts}</div>
              <a href="${item.url}" target="_blank" class="image-open-link">Open →</a>
            </div>
          </div>`;
      }

      const newsImageHtml = (isNews && item.image) ? `<img src="${item.image}" class="news-snapshot" alt="news" onerror="this.style.display='none'">` : '';

      return `
        <div class="result-item">
          ${newsImageHtml}
          <div class="result-site-line">
            <div class="result-favicon">🌐</div>
            <span class="result-host">${host}</span>
          </div>
          <a href="${item.url}" ${isNews ? "" : 'target="_blank"'} ${isNews ? `onclick="readArticle(event,'${item.url}',${i})"` : ""} class="result-title">${tt}</a>
          <p class="result-snippet">${ts}</p>
          ${isNews
          ? `<button class="read-here-btn" onclick="readArticle(event,'${item.url}',${i})">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a4 4 0 0 1-4-4V6"/></svg>
                Read Here
              </button>
              <div id="article-inline-${i}" style="display:none;"></div>`
          : `<a href="${item.url}" target="_blank" class="read-here-btn">${visitT} →</a>`}
        </div>`;
    });

    const htmlItems = await Promise.all(resultPromises);

    if (aiMode) {
      resultsBox.innerHTML = `<div class="ai-links-card"><h3>Sources</h3>${htmlItems.join("")}</div>`;
      if (paginationContainer) paginationContainer.innerHTML = "";
    } else if (currentFilter === "images") {
      resultsBox.innerHTML = `<div class="image-grid">${htmlItems.join("")}</div>`;
      renderPagination(data.total_hits || 0, pageNumber);
    } else {
      resultsBox.innerHTML = htmlItems.join("");
      renderPagination(data.total_hits || 0, pageNumber);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });

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
    searchBox.classList.add("has-suggestions");
  } else {
    closeAutocomplete();
  }
});

function closeAutocomplete() {
  if (autocompleteDropdown) { autocompleteDropdown.innerHTML = ""; autocompleteDropdown.style.display = "none"; }
  if (searchBox) searchBox.classList.remove("has-suggestions");
}

document.addEventListener("click", e => { if (searchBox && !searchBox.contains(e.target)) closeAutocomplete(); });

searchInput.addEventListener("keyup", e => {
  if (e.key === "Enter") { closeAutocomplete(); search(1, false); }
  else if (!searchInput.value.trim()) resetToHome();
});

// ═══════════════════════════════════════════
// IMAGE MODAL
// ═══════════════════════════════════════════
function openImageModal(imgUrl) {
  const modal = document.getElementById("imageModal");
  const modalImg = document.getElementById("zoomedImage");
  const btn = document.getElementById("downloadBtn");
  modal.style.display = "flex";
  modalImg.src = imgUrl;
  btn.onclick = async function (e) {
    e.preventDefault();
    try {
      btn.innerHTML = "⏳ Downloading…";
      const r = await fetch(imgUrl);
      const blob = await r.blob();
      const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "IndiaSearch_Image.jpg", style: "display:none" });
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(a.href);
      btn.innerHTML = "✅ Downloaded";
      setTimeout(() => { btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Download Image`; }, 2500);
    } catch { window.open(imgUrl, "_blank"); }
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
// FIREBASE & AUTH
// ═══════════════════════════════════════════
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAA13C5VErrxh8GLyoYMIUSvMpMBKCkZ98",
  authDomain: "indiasearch-975e1.firebaseapp.com",
  projectId: "indiasearch-975e1",
  storageBucket: "indiasearch-975e1.firebasestorage.app",
  messagingSenderId: "770251048171",
  appId: "1:770251048171:web:35b6f1af9057259321eaae",
  measurementId: "G-F17M30EDGG"
};

if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

const auth = firebase.auth();
window.recaptchaVerifier = null;
window.confirmationResult = null;

function setAuthMessage(msg, isError = false) {
  if (!authMessage) return;
  authMessage.textContent = msg || "";
  authMessage.className = "auth-msg" + (msg ? (isError ? " error" : " success") : "");
}

function openAuthModal() {
  if (authModal) authModal.style.display = "flex";
  document.getElementById("firebaseAuthForm").style.display = "grid";
  document.getElementById("firebaseOtpForm").style.display = "none";
  document.getElementById("firebaseEmailForm").style.display = "none";
}

function closeAuthModal() {
  if (authModal) authModal.style.display = "none";
  setAuthMessage("");
}

function renderAuthState() {
  if (authState.user && authState.sessionToken) {
    if (authButton) authButton.style.display = "none";
    if (userPill) userPill.style.display = "inline-flex";
    const id = authState.user.identifier || authState.user.email || "";
    if (userEmail) userEmail.textContent = id;
    if (userAvatar) userAvatar.textContent = (id[0] || "U").toUpperCase();
    closeAuthModal();
  } else {
    if (authButton) authButton.style.display = "none";
    if (userPill) userPill.style.display = "none";
    openAuthModal();
  }
}

async function hydrateSession() {
  if (!authState.sessionToken) return;
  try {
    const res = await fetchWithApiFallback(`/auth/me?session_token=${encodeURIComponent(authState.sessionToken)}`);
    if (!res.ok) throw new Error("Session invalid");
    const data = await res.json();
    authState.user = data.user;
    localStorage.setItem("authUser", JSON.stringify(data.user));
    renderAuthState();
  } catch {
    localStorage.removeItem("sessionToken"); localStorage.removeItem("authUser");
    authState = { sessionToken: "", user: null };
    renderAuthState();
  }
}

function isPhoneNumber(val) {
  return /^\+?\d{10,15}$/.test(val.replace(/[\s-]/g, ''));
}

async function requestFirebaseAuth() {
  let val = document.getElementById("firebaseIdentifier").value.trim();
  if (!val) {
    setAuthMessage("Please enter email or mobile number.", true);
    return;
  }

  if (isPhoneNumber(val)) {
    if (!val.startsWith('+')) {
      if (val.length === 10) val = '+91' + val; // Default to India if 10 digits
      else { setAuthMessage("Please include country code, e.g., +91", true); return; }
    }

    // Setup recaptcha if not already set
    if (!window.recaptchaVerifier) {
      window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
        'size': 'normal',
        'callback': (response) => {
          // reCAPTCHA solved, allow signInWithPhoneNumber.
        }
      });
    }

    try {
      setAuthMessage("Sending OTP... Please verify reCAPTCHA if prompted.");
      window.confirmationResult = await auth.signInWithPhoneNumber(val, window.recaptchaVerifier);
      document.getElementById("firebaseAuthForm").style.display = "none";
      document.getElementById("firebaseOtpForm").style.display = "grid";
      setAuthMessage("OTP sent to your phone. Valid for 5 minutes.");
    } catch (err) {
      console.error(err);
      setAuthMessage("Error sending OTP: " + err.message, true);
    }
  } else {
    // Email Flow
    document.getElementById("firebaseAuthForm").style.display = "none";
    document.getElementById("firebaseEmailForm").style.display = "grid";
    setAuthMessage("");
  }
}

async function submitFirebaseOtp() {
  const code = document.getElementById("firebaseOtpCode").value.trim();
  if (!code) {
    setAuthMessage("Please enter the OTP.", true);
    return;
  }

  try {
    setAuthMessage("Verifying...");
    const result = await window.confirmationResult.confirm(code);
    const token = await result.user.getIdToken();
    await verifyTokenWithBackend(token);
  } catch (err) {
    setAuthMessage("Invalid OTP: " + err.message, true);
  }
}

async function submitFirebaseEmail() {
  const email = document.getElementById("firebaseIdentifier").value.trim();
  const password = document.getElementById("firebaseEmailPassword").value;
  if (!password) {
    setAuthMessage("Password is required.", true);
    return;
  }

  try {
    setAuthMessage("Signing in...");
    const userCredential = await auth.signInWithEmailAndPassword(email, password);
    const token = await userCredential.user.getIdToken();
    await verifyTokenWithBackend(token);
  } catch (err) {
    if (err.code === 'auth/user-not-found' || err.code === 'auth/invalid-credential' || err.code === 'auth/invalid-login-credentials') {
      try {
        setAuthMessage("Creating new account...");
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        await userCredential.user.sendEmailVerification();
        setAuthMessage("Wait... verification email sent. Proceeding to login...");
        const token = await userCredential.user.getIdToken();
        await verifyTokenWithBackend(token);
      } catch (signupErr) {
        setAuthMessage(signupErr.message, true);
      }
    } else {
      setAuthMessage(err.message, true);
    }
  }
}

function togglePasswordVisibility(inputId, btn) {
  const inp = document.getElementById(inputId);
  if (!inp || !btn) return;
  const showing = inp.type === "text";
  inp.type = showing ? "password" : "text";
  btn.textContent = showing ? "Show" : "Hide";
}

async function sendResetEmail() {
  const email = document.getElementById("firebaseIdentifier").value.trim();
  if (!email || !email.includes("@")) {
    setAuthMessage("Please enter your email in the identifier field first.", true);
    return;
  }
  try {
    setAuthMessage("Sending reset link...");
    await auth.sendPasswordResetEmail(email);
    setAuthMessage("Password reset link sent to your email!", false);
  } catch (err) {
    setAuthMessage(err.message, true);
  }
}

function toggleUserDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById("userDropdown");
  if (!dropdown) return;
  const isShown = dropdown.style.display === "flex";
  dropdown.style.display = isShown ? "none" : "flex";
}

// Close dropdown when clicking outside
window.addEventListener("click", () => {
  const dropdown = document.getElementById("userDropdown");
  if (dropdown && dropdown.style.display === "flex") {
    dropdown.style.display = "none";
  }
});

async function verifyTokenWithBackend(firebaseToken) {
  try {
    const res = await apiJsonRequest("/auth/firebase-login", { id_token: firebaseToken });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed via backend.");

    authState.sessionToken = data.session_token;
    authState.user = data.user;
    localStorage.setItem("sessionToken", data.session_token);
    localStorage.setItem("authUser", JSON.stringify(data.user));
    renderAuthState();
    closeAuthModal();
    setAuthMessage("Login Successful!", false);
  } catch (err) {
    setAuthMessage(err.message, true);
  }
}

// ── Profile ──
function formatHistoryMeta(item) {
  return `${item.ai_mode ? "Ask AI" : "Search"} · ${(item.filter_type || "all").replace(/^./, c => c.toUpperCase())}`;
}

async function openProfileModal() {
  if (!authState.sessionToken) { openAuthModal(); return; }
  if (profileModal) profileModal.style.display = "flex";
  if (profileSummary) profileSummary.innerHTML = "<p class='profile-empty'>Loading…</p>";
  if (profileHistory) profileHistory.innerHTML = "";

  try {
    const res = await fetchWithApiFallback(`/auth/profile?session_token=${encodeURIComponent(authState.sessionToken)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not load profile.");

    authState.user = data.user;
    localStorage.setItem("authUser", JSON.stringify(data.user));
    renderAuthState();

    profileSummary.innerHTML = `
      <div class="profile-stat">
        <span class="profile-label">Account (${data.user.identifier_type || "Unknown"})</span>
        <strong>${data.user.identifier || data.user.email || data.user.phone}</strong>
      </div>`;

    if (!data.history || data.history.length === 0) {
      profileHistory.innerHTML = `<p class="profile-empty">Your recent searches will appear here.</p>`;
      return;
    }

    profileHistory.innerHTML = data.history.map(item => `
      <button class="profile-history-item" onclick="useProfileHistory(decodeURIComponent('${encodeURIComponent(item.query)}'), ${item.ai_mode ? "true" : "false"})">
        <span class="profile-history-query">${item.query}</span>
        <span class="profile-history-meta">${formatHistoryMeta(item)}</span>
      </button>`).join("");
  } catch (err) {
    if (profileSummary) profileSummary.innerHTML = `<p class="profile-empty">${err.message}</p>`;
  }
}

function closeProfileModal() {
  if (profileModal) profileModal.style.display = "none";
}

function useProfileHistory(query, aiMode = false) {
  closeProfileModal();
  searchInput.value = query;
  search(1, aiMode);
}

async function logoutUser() {
  try {
    if (authState.sessionToken) await apiJsonRequest("/auth/logout", { session_token: authState.sessionToken });
  } catch { }
  localStorage.removeItem("sessionToken"); localStorage.removeItem("authUser");
  authState = { sessionToken: "", user: null };
  renderAuthState();
  closeProfileModal();
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
document.addEventListener("DOMContentLoaded", () => {
  renderHistory();
  renderTrending();
  renderAuthState();
  hydrateSession();
  initHomeWidgets();
});