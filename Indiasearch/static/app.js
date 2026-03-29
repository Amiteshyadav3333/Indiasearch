// 🔧 Production API URL
const API_BASE = ""; // Connect to same origin (localhost)

const searchInput = document.getElementById("searchInput");
const resultsBox = document.getElementById("results");
const aiSummaryBox = document.getElementById("aiSummary");
const micButton = document.getElementById("micButton");
const languageSelect = document.getElementById("languageSelect");

let recognition;
let isListening = false;

// === THEME PERSISTENCE ===
if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
}

// === HISTORY PERSISTENCE ===
let searchHistory = JSON.parse(localStorage.getItem("searchHistory")) || [];
const historyBox = document.getElementById("searchHistory");

function renderHistory() {
    if (!historyBox) return;
    if (searchHistory.length === 0) {
        historyBox.innerHTML = "";
        return;
    }
    historyBox.innerHTML = searchHistory.map(q => 
        `<div class="history-chip" onclick="searchInput.value='${q.replace(/'/g, "\\'")}'; search();">
            <span>🕒 ${q}</span>
            <span class="remove-history" onclick="removeHistory(event, '${q.replace(/'/g, "\\'")}')">✖</span>
        </div>`
    ).join("");
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
    if (searchHistory.length > 6) searchHistory.pop(); // Keep last 6
    localStorage.setItem("searchHistory", JSON.stringify(searchHistory));
    renderHistory();
}

// === SEARCH FILTERS ===
const searchFiltersDiv = document.getElementById("searchFilters");
let currentFilter = "all";

function setFilter(filterType) {
    currentFilter = filterType;
    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = Array.from(document.querySelectorAll(".filter-btn")).find(btn => btn.innerText.toLowerCase().includes(filterType));
    if (activeBtn) activeBtn.classList.add("active");
    
    // Trigger new search automatically when a filter is clicked
    search(1, false);
}

// === TRENDING SEARCHES ===
const trendingContainer = document.getElementById("trendingContainer");

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
    grid.innerHTML = TRENDING_KEYWORDS.map(keyword => `
        <div class="trending-item" onclick="searchInput.value='${keyword}'; search();">
            <span>🔥</span> ${keyword}
        </div>
    `).join("");
}

document.addEventListener("DOMContentLoaded", () => {
    const isDark = document.body.classList.contains('dark');
    document.querySelector('.mode-btn').innerHTML = isDark ? '☀️' : '🌙';
    renderHistory();
    renderTrending();
});

// Google Translate API (Free)
async function translateText(text, targetLang) {
    if (targetLang === 'en' || !text) return text;

    try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
        const response = await fetch(url);
        const data = await response.json();
        return data[0].map(item => item[0]).join('');
    } catch (e) {
        console.error('Translation error:', e);
        return text;
    }
}

const STT_LOCALES = {
    'en': 'en-IN', 'hi': 'hi-IN', 'as': 'as-IN', 'bn': 'bn-IN', 
    'brx': 'en-IN', 'doi': 'en-IN', 'gu': 'gu-IN', 'kn': 'kn-IN', 
    'ks': 'ur-IN', 'gom': 'mr-IN', 'mai': 'hi-IN', 'ml': 'ml-IN', 
    'mni': 'en-IN', 'mr': 'mr-IN', 'ne': 'ne-NP', 'or': 'or-IN', 
    'pa': 'pa-IN', 'sa': 'hi-IN', 'sat': 'en-IN', 'sd': 'ur-IN', 
    'ta': 'ta-IN', 'te': 'te-IN', 'ur': 'ur-IN'
};

// Voice Recognition Setup
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        isListening = true;
        micButton.classList.add('listening');
        micButton.innerHTML = '🎤';
        searchInput.placeholder = 'सुन रहा हूँ... Listening...';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        searchInput.value = transcript;
        search();
    };

    recognition.onend = () => {
        isListening = false;
        micButton.classList.remove('listening');
        micButton.innerHTML = '🎙️';
        searchInput.placeholder = 'Search anything…';
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        micButton.classList.remove('listening');
        micButton.innerHTML = '🎙️';
    };
}

function toggleVoiceSearch() {
    if (!recognition) {
        alert('Voice search not supported in your browser');
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        const langCode = STT_LOCALES[languageSelect.value] || languageSelect.value;
        recognition.lang = langCode;
        recognition.start();
    }
}

function toggleDownloadMenu() {
    const menu = document.getElementById("downloadMenu");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

async function search(pageNumber = 1, aiMode = false) {
    let query = searchInput.value.trim();
    if (!query) {
        if (searchFiltersDiv) searchFiltersDiv.style.display = "none";
        if (trendingContainer) trendingContainer.style.display = "block";
        historyBox.style.display = "flex";
        resultsBox.innerHTML = "";
        aiSummaryBox.innerHTML = "";
        const pg = document.getElementById("paginationContainer");
        if (pg) pg.innerHTML = "";
        return;
    }

    closeAutocomplete();

    if (searchFiltersDiv) searchFiltersDiv.style.display = "flex";
    if (trendingContainer) trendingContainer.style.display = "none";
    historyBox.style.display = "none"; // Hide history when showing results
    
    // Only save history if it is a new search on page 1
    if (pageNumber === 1) {
        saveHistory(query);
    }

    // Toggle Spinner
    const searchBtn = document.querySelector(".search-btn");
    const originalBtnText = searchBtn ? searchBtn.innerHTML : "Search";
    if (searchBtn) searchBtn.innerHTML = "Search";

    const skeletonHTML = `
        <div class="skeleton-container">
            ${[1, 2, 3].map(() => `
                <div class="skeleton-item">
                    <div class="skeleton-title"></div>
                    <div class="skeleton-url"></div>
                    <div class="skeleton-text"></div>
                    <div class="skeleton-text short"></div>
                </div>
            `).join('')}
        </div>
    `;
    resultsBox.innerHTML = skeletonHTML;
    aiSummaryBox.innerHTML = "";

    const targetLang = languageSelect.value;

    try {
        let res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&page=${pageNumber}&filter=${currentFilter}&ai_mode=${aiMode}`);
        let data = await res.json();

        if (data.error) {
            resultsBox.innerHTML = `<p class='error'>⚠️ ${await translateText(data.error, targetLang)}</p>`;
            if (searchBtn) searchBtn.innerHTML = originalBtnText;
            return;
        }

        // AI Summary with translation (only on page 1)
        if (data.summary && pageNumber === 1) {
            const translatedSummary = await translateText(data.summary, targetLang);
            if (aiMode) {
                aiSummaryBox.innerHTML = `
                    <div class="ai-overview">
                        <div class="ai-overview-text">${translatedSummary.replace(/\n/g, "<br>")}</div>
                    </div>
                `;
            } else {
                aiSummaryBox.innerHTML = `
                    <div class="summary-box">
                        <strong>✨ AI Summary:</strong><br>
                        <span class="summary-text">${translatedSummary}</span>
                    </div>
                `;
            }
        }

        // Wikipedia Knowledge Panel (only on page 1)
        if (data.knowledge_panel && pageNumber === 1 && currentFilter === 'all') {
            const translatedKTitle = await translateText(data.knowledge_panel.title, targetLang);
            const translatedKSnippet = await translateText(data.knowledge_panel.snippet, targetLang);
            
            let imgHtml = "";
            if (data.knowledge_panel.image) {
                // Remove compression parameter for higher resolution on zoom
                const highResImage = data.knowledge_panel.image.replace("400px-", "1024px-");
                imgHtml = `<img src="${data.knowledge_panel.image}" alt="${translatedKTitle}" 
                    title="Click to Zoom & Download"
                    onclick="openImageModal('${highResImage}')"
                    style="float: right; margin-left: 15px; width: 120px; height: 120px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.15); cursor: zoom-in; transition: transform 0.2s;"
                    onmouseover="this.style.transform='scale(1.05)'"
                    onmouseout="this.style.transform='scale(1)'">`;
            }
            
            const wHtml = `
                <div class="knowledge-panel" style="overflow: hidden;">
                    ${imgHtml}
                    <h3>📚 ${translatedKTitle}</h3>
                    <p>${translatedKSnippet}</p>
                    <a href="${data.knowledge_panel.url}" target="_blank">Wikipedia →</a>
                </div>
            `;
            aiSummaryBox.innerHTML = wHtml + aiSummaryBox.innerHTML;
        }

        resultsBox.innerHTML = "";

        if (!data.results || data.results.length === 0) {
            const noResultsText = await translateText('No results found', targetLang);
            resultsBox.innerHTML = `<p class='no-results'>❌ ${noResultsText}</p>`;
            const pg = document.getElementById("paginationContainer");
            if (pg) pg.innerHTML = "";
            return;
        }

        // Translate results in parallel using Promise.all for massively improved speed!
        // Add readArticle global handler
        window.readArticle = async function(e, url, index) {
            e.preventDefault();
            const contentDiv = document.getElementById(`article-content-${index}`);
            if (!contentDiv) return;
            
            if (contentDiv.style.display === "block") {
                contentDiv.style.display = "none";
                return;
            }
            contentDiv.style.display = "block";
            contentDiv.innerHTML = "<p>⏳ Fetching local copy...</p>";
            
            try {
                let r = await fetch(`${API_BASE}/read-article?url=${encodeURIComponent(url)}`);
                let d = await r.json();
                
                if (d.error || !d.content || d.content.length < 50) {
                    contentDiv.innerHTML = `<p style="color:red">⚠️ Publisher blocked direct local access.</p><a href="${url}" target="_blank">Read on Site →</a>`;
                } else {
                    let paras = d.content.split("\\n\\n").map(p => `<p style="margin-bottom:8px;">${p}</p>`).join("");
                    contentDiv.innerHTML = `
                        <div class="inline-article" style="background:var(--inline-bg, #f8f9fa); padding:15px; border-radius:8px; margin-top:10px; border: 1px solid var(--inline-border, #dadce0);">
                            <h4 style="margin-bottom:10px; color:var(--inline-h, #1a0dab);">${d.title}</h4>
                            <div style="max-height: 400px; overflow-y: auto; font-size:14px; color:var(--inline-text, #202124);">
                                ${paras}
                            </div>
                            <a href="${url}" target="_blank" style="display:inline-block; margin-top:15px; font-weight:bold; color:var(--inline-h, #1a0dab);">🔗 Browse Original Layout</a>
                        </div>
                    `;
                }
            } catch {
                contentDiv.innerHTML = `<p style="color:red">⚠️ Network Error.</p>`;
            }
        };

        const resultPromises = data.results.map(async (item, index) => {
            const [translatedTitle, translatedSnippet, visitText] = await Promise.all([
                translateText(item.title, targetLang),
                translateText(item.snippet || '', targetLang),
                translateText('Visit Website', targetLang)
            ]);

            const isNews = (currentFilter === 'news');
            const targetAttr = isNews ? '' : 'target="_blank"';
            const onclickAttr = isNews ? `onclick="readArticle(event, '${item.url}', ${index})"` : '';
            
            let hostname = item.url;
            try { hostname = new URL(item.url).hostname; } catch(e){}

            return `
                <div class="result-item">
                    <div class="result-content">
                        <a href="${item.url}" ${targetAttr} ${onclickAttr} class="result-title">
                            ${translatedTitle}
                        </a>
                        <div class="result-url">${hostname}</div>
                        <p class="result-snippet">${translatedSnippet}</p>
                        <a href="${item.url}" ${targetAttr} ${onclickAttr} class="visit-btn">${isNews ? 'Read Here ↓' : visitText + ' →'}</a>
                        ${isNews ? `<div id="article-content-${index}" style="display:none; margin-top:15px; margin-bottom:15px;"></div>` : ''}
                    </div>
                </div>
            `;
        });

        const translatedHtmlItems = await Promise.all(resultPromises);
        resultsBox.innerHTML = translatedHtmlItems.join('');
        
        // Render Pagination UI
        renderPagination(data.total_hits || 0, pageNumber);

        if (searchBtn) searchBtn.innerHTML = originalBtnText;

    } catch (e) {
        const errorText = await translateText('Oops! Could not connect to the server right now. Please check your internet.', targetLang);
        resultsBox.innerHTML = `<p class='error'>⚠️ ${errorText}</p>`;
        console.error(e);
        if (searchBtn) searchBtn.innerHTML = originalBtnText;
    }
}

// Automatically translate placeholder when language changes
languageSelect.addEventListener("change", async () => {
    const targetLang = languageSelect.value;
    const newPlaceholder = await translateText("Search anything...", targetLang);
    searchInput.placeholder = newPlaceholder;
});

// === AUTOCOMPLETE ===
const autocompleteDropdown = document.getElementById("autocompleteDropdown");
const searchBox = document.querySelector(".search-box");

searchInput.addEventListener("input", (e) => {
    const val = e.target.value.trim().toLowerCase();
    if (!val) {
        closeAutocomplete();
        if (trendingContainer) trendingContainer.style.display = "block";
        historyBox.style.display = "flex";
        return;
    }
    if (trendingContainer) trendingContainer.style.display = "none";
    historyBox.style.display = "none";
    
    const db = [...new Set([...searchHistory, ...TRENDING_KEYWORDS, "sarkari result", "latest news india", "ind vs pak", "tech jobs bangalore"])];
    const matches = db.filter(item => item.toLowerCase().includes(val)).slice(0, 6);
    
    if (matches.length > 0) {
        autocompleteDropdown.innerHTML = matches.map(match => {
            const regex = new RegExp("(" + val + ")", "gi");
            const bolded = match.replace(regex, "<b>$1</b>");
            return `<div class="autocomplete-item" onclick="searchInput.value='${match.replace(/'/g, "\\'")}'; closeAutocomplete(); search(1);">
                🔍 <span>${bolded}</span>
            </div>`;
        }).join("");
        autocompleteDropdown.style.display = "block";
        searchBox.classList.add("has-suggestions");
    } else {
        closeAutocomplete();
    }
});

function closeAutocomplete() {
    if (autocompleteDropdown) {
        autocompleteDropdown.innerHTML = "";
        autocompleteDropdown.style.display = "none";
        if (searchBox) searchBox.classList.remove("has-suggestions");
    }
}

document.addEventListener("click", (e) => {
    if (searchBox && !searchBox.contains(e.target)) {
        closeAutocomplete();
    }
});

// === PAGINATION PARSER ===
const paginationContainer = document.getElementById("paginationContainer");
function renderPagination(totalHits, currentPage) {
    if (!paginationContainer) return;
    if (totalHits <= 10) {
        paginationContainer.innerHTML = "";
        return;
    }
    
    const totalPages = Math.ceil(totalHits / 10);
    let html = '';
    
    if (currentPage > 1) {
        html += `<button class="page-btn" onclick="search(${currentPage - 1})">←</button>`;
    } else {
        html += `<button class="page-btn" disabled>←</button>`;
    }
    
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="search(${i})">${i}</button>`;
        }
    }
    
    if (currentPage < totalPages) {
        html += `<button class="page-btn" onclick="search(${currentPage + 1})">→</button>`;
    } else {
        html += `<button class="page-btn" disabled>→</button>`;
    }
    
    paginationContainer.innerHTML = html;
}

searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
        closeAutocomplete();
        search(1, false);
    } else if (searchInput.value.trim() === "") {
        // Show trending and history when input is cleared
        if (searchFiltersDiv) searchFiltersDiv.style.display = "none";
        if (trendingContainer) trendingContainer.style.display = "block";
        historyBox.style.display = "flex";
        resultsBox.innerHTML = "";
        aiSummaryBox.innerHTML = "";
    }
});

function toggleMode() {
    document.body.classList.toggle("dark");
    const isDark = document.body.classList.contains('dark');
    document.querySelector('.mode-btn').innerHTML = isDark ? '☀️' : '🌙';
    localStorage.setItem("theme", isDark ? "dark" : "light");
}

// === IMAGE ZOOM MODAL ===
function openImageModal(imgUrl) {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("zoomedImage");
    const btn = document.getElementById("downloadBtn");
    
    modal.style.display = "block";
    modalImg.src = imgUrl;
    
    btn.onclick = async function(e) {
        e.preventDefault();
        try {
            btn.innerHTML = "⏳ Downloading...";
            const response = await fetch(imgUrl);
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = blobUrl;
            a.download = "Indiasearch_Image.jpg";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(blobUrl);
            a.remove();
            btn.innerHTML = "✅ Downloaded";
            setTimeout(() => btn.innerHTML = "📥 Download Image", 2000);
        } catch(err) {
            window.open(imgUrl, '_blank');
            btn.innerHTML = "📥 Download Image";
        }
    };
}

function toggleDownloadMenu() {
    const menu = document.getElementById("downloadMenu");
    if (menu.style.display === "none") {
        menu.style.display = "block";
    } else {
        menu.style.display = "none";
    }
}

function closeImageModal() {
    document.getElementById("imageModal").style.display = "none";
    document.getElementById("downloadMenu").style.display = "none";
}
