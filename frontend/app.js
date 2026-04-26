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

// ── Firebase Config (Update with your own keys) ──
const firebaseConfig = {
  apiKey: "AIzaSyAz-DUMMY-KEY-REPLACE-ME",
  authDomain: "indiasearch-975e1.firebaseapp.com",
  projectId: "indiasearch-975e1",
  storageBucket: "indiasearch-975e1.appspot.com",
  messagingSenderId: "367253459142",
  appId: "1:367253459142:web:7f6f1a8e1a1e1a1e1a1e1a"
};

if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}
const auth = firebase.auth();

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
const mainWrap = document.querySelector(".main-wrap");

const heroSection = document.getElementById("heroSection");
const searchFiltersDiv = document.getElementById("searchFilters");
const trendingContainer = document.getElementById("trendingContainer");
const historyBox = document.getElementById("searchHistory");
const paginationContainer = document.getElementById("pagination");
const siteHeader = document.getElementById("siteHeader");

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


let recognition;
let isListening = false;
let attachedScan = null;

// Combined Identity & Session Management
let authState = {
  user: null,
  isGuest: true,
  sessionToken: localStorage.getItem("sessionToken") || "",
  guestId: localStorage.getItem("guestSession") || `guest_${Math.random().toString(36).substr(2, 9)}`
};

let activeQuery = ""; // Persistent query for pagination after input is cleared

if (!localStorage.getItem("guestSession")) {
  localStorage.setItem("guestSession", authState.guestId);
}

// ── Auth Logic ──
const authModal = document.getElementById("authModal");
const userDropdown = document.getElementById("userDropdown");
let currentAuthMode = "signin"; 
let currentAuthMethod = "email"; 
let confirmationResult = null; 

function toggleUserMenu() {
  const dropdown = document.getElementById("userDropdown");
  if (!dropdown) return;
  const isHidden = dropdown.style.display !== "flex";
  
  if (isHidden) {
    updateUserUI(); // Fill content first
    dropdown.style.display = "flex";
  } else {
    dropdown.style.display = "none";
  }
}

function openAuthModal(mode = "signin") {
  currentAuthMode = mode;
  if (authModal) {
    authModal.style.display = "flex";
    document.getElementById("authTitle").innerText = mode === "signin" ? "Sign In" : "Sign Up";
    document.getElementById("authSwitchText").innerHTML = mode === "signin" 
      ? `Don't have an account? <a href="#" onclick="toggleAuthMode()">Sign Up</a>`
      : `Already have an account? <a href="#" onclick="toggleAuthMode()">Sign In</a>`;
  }
}

function closeAuthModal() {
  if (authModal) authModal.style.display = "none";
}

function toggleAuthMode() {
  openAuthModal(currentAuthMode === "signin" ? "signup" : "signin");
}

function setAuthMethod(method) {
  currentAuthMethod = method;
  document.getElementById("emailTab").classList.toggle("active", method === "email");
  document.getElementById("phoneTab").classList.toggle("active", method === "phone");
  document.getElementById("emailForm").style.display = method === "email" ? "flex" : "none";
  document.getElementById("phoneForm").style.display = method === "phone" ? "flex" : "none";
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("authEmail").value;
  const password = document.getElementById("authPassword").value;
  try {
    if (currentAuthMode === "signin") {
      await auth.signInWithEmailAndPassword(email, password);
    } else {
      await auth.createUserWithEmailAndPassword(email, password);
    }
    closeAuthModal();
  } catch (err) {
    alert(err.message);
  }
}

window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', { 'size': 'invisible' });

async function handlePhoneSubmit(e) {
  e.preventDefault();
  const phone = "+91" + document.getElementById("authPhone").value;
  const otpGroup = document.getElementById("otpGroup");
  const submitBtn = document.getElementById("phoneSubmitBtn");
  if (!confirmationResult) {
    try {
      confirmationResult = await auth.signInWithPhoneNumber(phone, window.recaptchaVerifier);
      otpGroup.style.display = "block";
      submitBtn.innerText = "Verify OTP";
    } catch (err) {
      alert(err.message);
    }
  } else {
    const code = document.getElementById("authOtp").value;
    try {
      await confirmationResult.confirm(code);
      closeAuthModal();
    } catch (err) {
      alert("Invalid OTP");
    }
  }
}

function handleLogout() {
  auth.signOut();
  const dropdown = document.getElementById("userDropdown");
  if (dropdown) dropdown.style.display = "none";
}

function updateUserUI() {
  const dropdown = document.getElementById("userDropdown");
  if (!dropdown) return;

  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const modeText = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";

  if (authState.user) {
    const emailStr = authState.user.email || authState.user.phoneNumber || "User";
    const initial = emailStr.charAt(0).toUpperCase();
    dropdown.innerHTML = `
      <div class="user-dropdown-header">
        <div class="mini-avatar">${initial}</div>
        <div style="font-size:14px; font-weight:700; color:var(--text-primary); text-overflow:ellipsis; overflow:hidden;">${emailStr}</div>
      </div>
      <div class="dropdown-sep"></div>
      <button class="dropdown-item" onclick="alert('Profile saving history feature active.')">👤 My Profile</button>
      <button class="dropdown-item" onclick="toggleMode(); toggleUserMenu();">${modeText}</button>
      <button class="dropdown-item" onclick="clearHistoryUI()">🗑️ Clear History</button>
      <div class="dropdown-sep"></div>
      <button class="dropdown-item" onclick="window.location.reload()">🔄 Refresh</button>
      <button class="dropdown-item danger" onclick="handleLogout()">🚪 Logout</button>
    `;
  } else {
    dropdown.innerHTML = `
      <div class="user-dropdown-header">
        <div style="font-size:14px; font-weight:700; color:var(--text-secondary);">Guest Mode (Active)</div>
      </div>
      <div class="dropdown-sep"></div>
      <button class="dropdown-item primary-item" onclick="openAuthModal('signin'); toggleUserMenu();">🔑 Sign In</button>
      <button class="dropdown-item" onclick="openAuthModal('signup'); toggleUserMenu();">📝 Sign Up</button>
      <div class="dropdown-sep"></div>
      <button class="dropdown-item" onclick="toggleMode(); toggleUserMenu();">${modeText}</button>
      <button class="dropdown-item" onclick="alert('Settings feature coming soon')">⚙️ Settings</button>
    `;
  }
}

function clearHistoryUI() {
  if (confirm("Are you sure you want to clear your local history?")) {
    searchHistory = [];
    localStorage.removeItem("searchHistory");
    renderHistory();
    alert("History cleared!");
  }
}

auth.onAuthStateChanged((user) => {
  if (user) {
    authState.user = user;
    authState.isGuest = false;
    user.getIdToken().then(token => {
      authState.sessionToken = token;
      localStorage.setItem("sessionToken", token);
    });
    localStorage.setItem("authUser", JSON.stringify(user));
  } else {
    authState.user = null;
    authState.isGuest = true;
    authState.sessionToken = "";
    localStorage.removeItem("sessionToken");
    localStorage.removeItem("authUser");
  }
  updateUserUI();
});

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
  // Only save history if user is logged in
  if (!authState.user) {
    console.log("Guest mode: history not saved.");
    return;
  }
  
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
  const btn = document.querySelector(`.filter-pill[data-filter="${type}"]`);
  if (btn) btn.classList.add("active");

  const defaultQueries = {
    news: "latest india news",
    weather: "weather in Delhi",
    score: "live cricket score",
    stock: "reliance stock price"
  };
  if (searchInput && !searchInput.value.trim() && defaultQueries[type]) {
    searchInput.value = defaultQueries[type];
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
let scannerStream = null;
let scannerActive = false;

async function startLiveScan() {
  const liveScanner = document.getElementById("liveScanner");
  const video = document.getElementById("scannerVideo");
  const status = document.getElementById("liveScanStatus");

  try {
    scannerStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    video.srcObject = scannerStream;
    liveScanner.style.display = "block";
    scannerActive = true;
    requestAnimationFrame(tick);
    status.innerHTML = "🔍 Looking for QR Code...";
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
  document.getElementById("liveScanner").style.display = "none";
}

function tick() {
  if (!scannerActive) return;

  const video = document.getElementById("scannerVideo");
  const status = document.getElementById("liveScanStatus");

  if (video.readyState === video.HAVE_ENOUGH_DATA) {
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
  if (authState.sessionToken) formData.append("session_token", authState.sessionToken);

  try {
    const res = await fetchWithApiFallback(`/visual-search`, {
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
async function resetToHome() {
  searchInput.value = "";
  resultsBox.innerHTML = "";
  aiSummaryBox.innerHTML = "";
  if (paginationContainer) paginationContainer.innerHTML = "";
  if (searchFiltersDiv) searchFiltersDiv.style.display = "none";
  if (trendingContainer) trendingContainer.style.display = "block";
  if (historyBox) historyBox.style.display = "flex";
  if (heroSection) heroSection.classList.remove("hidden");
  if (scanStatus) scanStatus.textContent = "";
  
  // Clear file inputs and visual previews
  if (pdfInput) pdfInput.value = "";
  if (cameraInput) cameraInput.value = "";
  if (aiPdfPreview) {
      aiPdfPreview.style.display = "none";
      aiPdfPreview.innerHTML = "";
  }
  
  closeAutocomplete();
  
  // Clear backend memory context for this session
  const finalSess = authState.sessionToken || authState.guestSession;
  try {
      await apiJsonRequest("/clear-context", { session_token: finalSess });
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

function renderAiSources(sources = []) {
  return "";
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
async function search(pageNumber = 1, aiMode = false) {
  let query = searchInput ? searchInput.value.trim() : "";
  
  // If no query in input, but we're on a non-first page, use activeQuery
  if (!query && pageNumber > 1) {
    query = activeQuery;
  }

  if (!query) {
    resetToHome();
    return;
  }

  // Update activeQuery on new search
  if (pageNumber === 1) activeQuery = query;

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
      // Auth check disabled for now
      // if (res.status === 401) {
      //   openAuthModal();
      //   setAuthMessage("Please login to use IndiaSearch.", true);
      //   resultsBox.innerHTML = "";
      //   if (paginationContainer) paginationContainer.innerHTML = "";
      //   return;
      // }
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
              <button onclick="resetToHome()" class="btn-primary" style="background: var(--bg-alt); color: var(--text-primary); border-color: var(--border); padding: 10px 30px;">No, take me back</button>
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
        summaryHtml = `
          <div class="ai-overview-card">
            <div class="ai-overview-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="url(#ai-grad)" stroke-width="2.5"><defs><linearGradient id="ai-grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6" /><stop offset="100%" stop-color="#8b5cf6" /></linearGradient></defs><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <span style="background: linear-gradient(90deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">IndiaSearch AI</span>
            </div>
            <div class="ai-overview-text" id="streamingAI"></div>
            ${aiSourcesHtml}
          </div>`;
      } else {
        summaryHtml = `
          <div class="summary-card">
            <div class="summary-label">✨ Instant AI Answer</div>
            <div class="summary-text">${renderMarkdownWithCitations(rawText, aiSources)}</div>
            ${aiSourcesHtml}
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
              target.innerHTML = renderMarkdownWithCitations(rawText, aiSources); // Run through markdown parser once done
           }
        }
        typeWriter();
      }
    }

    // ── Special Panels Integration (Weather, Sports, Finance) ──
    if (data.special_data && pageNumber === 1) {
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

    // If NO results at all (no web results AND no weather/summary/sports/stocks)
    const hasResults = (data.results && data.results.length > 0);
    const hasSmartAnswer = Boolean(data.special_data || data.weather || data.summary || data.knowledge_panel || data.sports || data.stocks);

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

      // News detection: either filter is news OR item has is_news flag
      const isNews = (currentFilter === "news") || item.is_news === true;
      const isImages = currentFilter === "images";
      const isVideos = currentFilter === "videos";
      let host = item.url;
      try { host = new URL(item.url).hostname.replace(/^www\./, ""); } catch { }
      const sourceName = getSourceBadge(item.url, host);

      if (aiMode) {
        return ""; // In true AI Mode, don't show normal results
      }

      if (isVideos) {
        let videoId = "";
        if (item.url.includes("youtube.com/watch?v=")) {
          videoId = item.url.split("v=")[1].split("&")[0];
        } else if (item.url.includes("youtu.be/")) {
          videoId = item.url.split("youtu.be/")[1].split("?")[0];
        }

        if (videoId) {
          return `
            <div class="video-card">
              <div class="video-frame-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; background: #000; margin-bottom: 10px;">
                <iframe src="https://www.youtube.com/embed/${videoId}" 
                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
              </div>
              <div class="video-meta">
                <a href="${item.url}" target="_blank" class="video-title" style="font-weight: 600; font-size: 16px; color: var(--text-primary); text-decoration: none; display: block; margin-bottom: 4px; line-height: 1.4;">${tt}</a>
                <div class="video-source" style="font-size: 13px; color: var(--text-secondary);">${ts}</div>
              </div>
            </div>`;
        } else {
          return `
            <div class="video-card" onclick="window.open('${item.url}', '_blank')" style="cursor: pointer;">
              <div class="video-thumbnail" style="position: relative; border-radius: 12px; overflow: hidden; margin-bottom: 10px;">
                <img src="${item.image || ''}" alt="${tt}" style="width: 100%; height: 200px; object-fit: cover; background: #1a1a1a;" loading="lazy">
                <div class="play-icon" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.6); border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
              <div class="video-meta">
                <div class="video-title" style="font-weight: 600; font-size: 16px; color: var(--text-primary); display: block; margin-bottom: 4px; line-height: 1.4;">${tt}</div>
                <div class="video-source" style="font-size: 13px; color: var(--text-secondary);">${ts}</div>
              </div>
            </div>`;
        }
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
                <a href="${item.url}" target="_blank" class="news-open-link" onclick="event.stopPropagation()">Open →</a>
              </div>
              <div id="article-inline-${i}" style="display:none;" onclick="event.stopPropagation()"></div>
            </div>
          </div>`;
      }

      // ── Standard Web Result ──
      return `
        <div class="result-item">
          <div class="result-site-line">
            <div class="result-favicon">🌐</div>
            <span class="result-host">${host}</span>
          </div>
          <a href="${item.url}" target="_blank" class="result-title">${tt}</a>
          <p class="result-snippet">${ts}</p>
          <a href="${item.url}" target="_blank" class="read-here-btn">${visitT} →</a>
        </div>`;
    });

    const htmlItems = await Promise.all(resultPromises);

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
      resultsBox.innerHTML = `<div class="news-grid-premium">${htmlItems.join("")}</div>`;
      renderPagination(data.total || 0, pageNumber);
    } else {
      resultsBox.innerHTML = htmlItems.join("");
      renderPagination(data.total || 0, pageNumber);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });

    // ── Clear Search Boxes as per User Request ──
    // "Answer aaye remove ho jay"
    if (searchInput) searchInput.value = "";
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
// ADVANCED AUTHENTICATION (LINK-BASED)
// ═══════════════════════════════════════════
let currentAuthToken = "";

function setAuthMessage(msg, isError = false) {
  const authMessage = document.getElementById("authMessage");
  if (!authMessage) return;
  authMessage.textContent = msg || "";
  authMessage.className = "auth-msg" + (msg ? (isError ? " error" : " success") : "");
}

function openAuthModal(initialMode = 'signin') {
  const authModal = document.getElementById("authModal");
  if (authModal) authModal.style.display = "flex";
  switchAuthMode(initialMode);
}

function closeAuthModal() {
  const authModal = document.getElementById("authModal");
  if (authModal) authModal.style.display = "none";
  setAuthMessage("");
}

function switchAuthMode(mode) {
  const signinForm = document.getElementById("signinForm");
  const signupForm = document.getElementById("signupForm");
  const verifyForm = document.getElementById("verifySuccessForm");
  const tabSignin = document.getElementById("tabSignin");
  const tabSignup = document.getElementById("tabSignup");

  if (!signinForm || !signupForm) return;

  setAuthMessage("");
  
  if (mode === 'signin') {
    signinForm.style.display = "grid";
    signupForm.style.display = "none";
    verifyForm.style.display = "none";
    tabSignin.classList.add("active");
    tabSignup.classList.remove("active");
  } else if (mode === 'signup') {
    signinForm.style.display = "none";
    signupForm.style.display = "grid";
    verifyForm.style.display = "none";
    tabSignin.classList.remove("active");
    tabSignup.classList.add("active");
  } else if (mode === 'verify') {
    signinForm.style.display = "none";
    signupForm.style.display = "none";
    verifyForm.style.display = "grid";
  }
}

async function submitSignin() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  const captcha = document.getElementById("loginCaptcha").value.trim();

  if (!email || !password || !captcha) {
    setAuthMessage("Email, Password, and Captcha are required.", true);
    return;
  }

  try {
    setAuthMessage("Authenticating with IndiaSearch...");
    const res = await apiJsonRequest(`/auth/login`, { 
      identifier: email, 
      password, 
      captcha_code: captcha 
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");

    authState.sessionToken = data.session_token;
    authState.user = data.user;
    localStorage.setItem("sessionToken", data.session_token);
    localStorage.setItem("authUser", JSON.stringify(data.user));
    
    setAuthMessage("Login successful! Redirecting...", false);
    setTimeout(() => {
      renderAuthState();
      closeAuthModal();
      // Also close the dropdown if it was open
      const dropdown = document.getElementById("userDropdown");
      if (dropdown) dropdown.style.display = "none";
    }, 800);
  } catch (err) {
    setAuthMessage(err.message, true);
  }
}

async function requestSignupLink() {
  const email = document.getElementById("signupEmail").value.trim();
  if (!email || !email.includes("@")) {
    setAuthMessage("Please enter a valid email address.", true);
    return;
  }

  try {
    setAuthMessage("Sending secure verification link...");
    const res = await apiJsonRequest(`/auth/signup/request`, { 
      email: email
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");

    // Simulator: Show the link for the user to "click"
    currentAuthToken = data.debug_token;
    document.getElementById("verifyEmailDisplay").value = email;
    
    setAuthMessage("Verification link generated! In a real scenario, this goes to your inbox.", false);
    
    // Add Simulation Button
    const simDiv = document.createElement("div");
    simDiv.style.marginTop = "15px";
    simDiv.innerHTML = `
      <button class="btn-primary full-w" style="background: #34a853; border-color: #34a853;" 
              onclick="switchAuthMode('verify')">Simulate Email Link Click</button>
    `;
    document.getElementById("authMessage").appendChild(simDiv);

  } catch (err) {
    setAuthMessage(err.message, true);
  }
}

async function completeSignupVerification() {
  const password = document.getElementById("verifyPassword").value;
  const verificationEmail = document.getElementById("verifyEmailDisplay").value;
  const code = currentAuthToken;
  if (!password || password.length < 8) {
    setAuthMessage("Password must be at least 8 characters for security.", true);
    return;
  }

  try {
    setAuthMessage("Finalizing your account...");
    const res = await apiJsonRequest(`/auth/signup/verify`, { 
      token: currentAuthToken, password
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Setup failed");

    authState.sessionToken = data.session_token;
    authState.user = data.user;
    localStorage.setItem("sessionToken", data.session_token);
    localStorage.setItem("authUser", JSON.stringify(data.user));
    
    setAuthMessage("Account created successfully! Welcome to IndiaSearch.", false);
    setTimeout(() => {
      renderAuthState();
      closeAuthModal();
    }, 1000);
  } catch (err) {
    setAuthMessage(err.message, true);
  }
}

function renderAuthState() {
  const guestMenu = document.getElementById("guestMenu");
  const loggedMenu = document.getElementById("loggedMenu");
  const userEmail = document.getElementById("userEmail");
  const userAvatarMini = document.getElementById("userAvatarMini");

  if (authState.user && authState.sessionToken) {
    if (guestMenu) guestMenu.style.display = "none";
    if (loggedMenu) loggedMenu.style.display = "block";
    
    const id = authState.user.identifier || "";
    if (userEmail) userEmail.textContent = id.split('@')[0];
    if (userAvatarMini) userAvatarMini.textContent = (id[0] || "U").toUpperCase();
    
    closeAuthModal();
  } else {
    if (guestMenu) guestMenu.style.display = "block";
    if (loggedMenu) loggedMenu.style.display = "none";
  }
}

function toggleUserDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById("userDropdown");
  if (!dropdown) return;
  const isShown = dropdown.style.display === "flex" || dropdown.style.display === "block";
  dropdown.style.display = isShown ? "none" : "flex";
}

window.addEventListener("click", () => {
  const dropdown = document.getElementById("userDropdown");
  if (dropdown && dropdown.style.display !== "none") {
    dropdown.style.display = "none";
  }
});

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

async function logout() {
  try {
    if (authState.sessionToken) {
      await fetchWithApiFallback("/auth/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_token: authState.sessionToken }),
      });
    }
  } catch (err) {
    console.warn("Logout request failed:", err);
  }
  localStorage.removeItem("sessionToken");
  localStorage.removeItem("authUser");
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

document.addEventListener("DOMContentLoaded", () => {
  renderHistory();
  renderTrending();
  renderAuthState();
  hydrateSession();
  initHomeWidgets();
});
// Final Initialization
updateUserUI();
