async function loadHtmlPartials() {
  const slots = Array.from(document.querySelectorAll('[data-partial]'));

  await Promise.all(slots.map(async (slot) => {
    const partialPath = slot.getAttribute('data-partial');
    const response = await fetch(partialPath);

    if (!response.ok) {
      throw new Error(`Could not load ${partialPath}`);
    }

    slot.outerHTML = await response.text();
  }));
}

function loadMainApp() {
  const script = document.createElement('script');
  script.src = 'app.js?v=google-ai-overview-v2';
  document.body.appendChild(script);
}

loadHtmlPartials()
  .then(loadMainApp)
  .catch((error) => {
    console.error('IndiaSearch partial load failed:', error);
    document.body.innerHTML = '<main class="main-wrap"><p>Page load nahi ho paaya. Please local server ya deployed site se open karein.</p></main>';
  });
