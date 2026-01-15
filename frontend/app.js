// 🔧 Production API URL
const API_BASE = "https://indiasearch-production.up.railway.app";

const searchInput = document.getElementById("searchInput");
const resultsBox = document.getElementById("results");
const aiSummaryBox = document.getElementById("aiSummary");
const micButton = document.getElementById("micButton");
const languageSelect = document.getElementById("languageSelect");

let recognition;
let isListening = false;

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

// Voice Recognition Setup
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'hi-IN'; // Hindi + English support

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
        recognition.start();
    }
}

async function search() {
    let query = searchInput.value.trim();
    if (!query) return;

    const targetLang = languageSelect.value;

    resultsBox.innerHTML = "<div class='loading'>🔍 Searching...</div>";
    aiSummaryBox.innerHTML = "";

    try {
        let res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        let data = await res.json();

        // AI Summary with translation
        if (data.summary) {
            const translatedSummary = await translateText(data.summary, targetLang);
            aiSummaryBox.innerHTML = `
                <div class="summary-box">
                    <span class="badge">🧠 AI Answer</span>
                    <p class="summary-text">${translatedSummary}</p>
                </div>
            `;
        }

        resultsBox.innerHTML = "";

        if (!data.results || data.results.length === 0) {
            const noResultsText = await translateText('No results found', targetLang);
            resultsBox.innerHTML = `<p class='no-results'>❌ ${noResultsText}</p>`;
            return;
        }

        // Translate and display results
        for (const item of data.results) {
            const translatedTitle = await translateText(item.title, targetLang);
            const translatedSnippet = await translateText(item.snippet || '', targetLang);
            const visitText = await translateText('Visit Website', targetLang);
            
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result-item';
            resultDiv.innerHTML = `
                <div class="result-content">
                    <a href="${item.url}" target="_blank" class="result-title">
                        ${translatedTitle}
                    </a>
                    <div class="result-url">${new URL(item.url).hostname}</div>
                    <p class="result-snippet">${translatedSnippet}</p>
                    <a href="${item.url}" target="_blank" class="visit-btn">${visitText} →</a>
                </div>
            `;
            resultsBox.appendChild(resultDiv);
        }
    } catch (e) {
        const errorText = await translateText('Error connecting to server', targetLang);
        resultsBox.innerHTML = `<p class='error'>⚠️ ${errorText}</p>`;
        console.error(e);
    }
}

searchInput.addEventListener("keyup", (e)=>{
    if(e.key === "Enter"){
        search();
    }
});

function toggleMode(){
    document.body.classList.toggle("light");
    const icon = document.body.classList.contains('light') ? '☀️' : '🌙';
    document.querySelector('.mode-btn').innerHTML = icon;
}
