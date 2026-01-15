import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
from indexer import index_document
import time
import re

# ========= SETTINGS ==========
MAX_PAGES = 200
MAX_DEPTH = 2
TIMEOUT = 7
CRAWL_DELAY = 0.5
USER_AGENT = "IndiasearchBot/1.0"
# =============================

visited = set()
count = 0


HEADERS = {
    "User-Agent": USER_AGENT
}


def clean_url(url):
    """Remove #tags from URL"""
    url, _ = urldefrag(url)
    return url


def valid_link(url):
    bad = (
        ".jpg", ".jpeg", ".png", ".gif",
        ".webp", ".svg",
        ".mp4", ".avi", ".mp3",
        ".pdf", ".zip", ".exe",
        "login", "signup"
    )
    return not url.lower().endswith(bad)


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def crawl(url, depth=0):
    global count

    url = clean_url(url)

    if depth > MAX_DEPTH:
        return

    if url in visited:
        return

    if count >= MAX_PAGES:
        return

    visited.add(url)
    count += 1

    print(f"[{count}] Depth={depth}  URL={url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string.strip() if soup.title else "No Title"
        content = clean_text(soup.get_text(" "))

        # -------- SAVE TO ELASTICSEARCH --------
        index_document(url, title, content)

        # -------- FOLLOW LINKS --------
        for a in soup.find_all("a"):
            link = a.get("href")

            if not link:
                continue

            next_url = urljoin(url, link)

            if not next_url.startswith("http"):
                continue

            if not valid_link(next_url):
                continue

            crawl(next_url, depth + 1)

        time.sleep(CRAWL_DELAY)

    except Exception as e:
        print("❌ Error:", e)


# ---------- SEED SITES ----------
SEED_URLS = [
    "https://www.python.org",
    "https://www.bbc.com",
    "https://www.ndtv.com",
    "https://en.wikipedia.org/wiki/India"
]


print("\n🚀 Starting Indiasearch Web Crawler...\n")

for site in SEED_URLS:
    crawl(site)

print("\n✅ DONE — Crawling Completed.\n")