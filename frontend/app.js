// 🔧 Production API URL
const API_BASE = "https://indiasearch-production.up.railway.app";

const searchInput = document.getElementById("searchInput");
const resultsBox = document.getElementById("results");
const aiSummaryBox = document.getElementById("aiSummary");
const micButton = document.getElementById("micButton");

let recognition;
let isListening = false;

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

    resultsBox.innerHTML = "<div class='loading'>🔍 Searching...</div>";
    aiSummaryBox.innerHTML = "";

    try {
        let res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        let data = await res.json();

        // AI Summary
        if (data.summary) {
            aiSummaryBox.innerHTML = `
                <div class="summary-box">
                    <span class="badge">🧠 AI Answer</span>
                    <p class="summary-text">${data.summary}</p>
                </div>
            `;
        }

        resultsBox.innerHTML = "";

        if (!data.results || data.results.length === 0) {
            resultsBox.innerHTML = "<p class='no-results'>❌ No results found</p>";
            return;
        }

        data.results.forEach((item, index) => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result-item';
            resultDiv.innerHTML = `
                <div class="result-content">
                    <a href="${item.url}" target="_blank" class="result-title">
                        ${item.title}
                    </a>
                    <div class="result-url">${new URL(item.url).hostname}</div>
                    <p class="result-snippet">${item.snippet || ''}</p>
                    <a href="${item.url}" target="_blank" class="visit-btn">Visit Website →</a>
                </div>
            `;
            resultsBox.appendChild(resultDiv);
        });
    } catch (e) {
        resultsBox.innerHTML = "<p class='error'>⚠️ Error connecting to server</p>";
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
