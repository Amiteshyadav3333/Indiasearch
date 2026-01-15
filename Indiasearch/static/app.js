const searchInput = document.getElementById("searchInput");
const resultsBox = document.getElementById("results");
const aiSummaryBox = document.getElementById("aiSummary");
const trendingBox = document.getElementById("trending");

// ===============================
// SEARCH FUNCTION
// ===============================
async function search() {
    let query = searchInput.value.trim();
    if (!query) return;

    resultsBox.innerHTML = "Searching...";
    aiSummaryBox.innerHTML = "";

    let res = await fetch(`/search?q=${encodeURIComponent(query)}`);
    let data = await res.json();

    if (data.summary) {
        aiSummaryBox.innerHTML = `
            <div class="summary-box">
                <span class="badge">AI Summary</span>
                <p>${data.summary}</p>
            </div>
        `;
    }

    resultsBox.innerHTML = "";

    if (!data.results || data.results.length === 0) {
        resultsBox.innerHTML = "<p>No results found</p>";
        return;
    }

    data.results.forEach(item => {
        resultsBox.innerHTML += `
            <div class="result-item">
                <a href="${item.url}" target="_blank">
                    <b>${item.title}</b>
                </a><br>
                <small>${item.url}</small><br>
                <p>${item.snippet || ''}</p>
            </div>
        `;
    });
}


// ===============================
// ENTER KEY SUPPORT
// ===============================
searchInput.addEventListener("keyup", (e)=>{
    if(e.key === "Enter"){
        search();
    }
});


// ===============================
// THEME TOGGLE
// ===============================
function toggleMode(){
    document.body.classList.toggle("light");
}