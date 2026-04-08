import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlparse
import re

try:
    from app.services.index_service import index_document
except ImportError:
    try:
        from indexer import index_document
    except ImportError:
        from Indiasearch.indexer import index_document

class Crawler:
    def __init__(self, max_pages=300, max_depth=2, max_concurrency=15, timeout=7):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.user_agent = "IndiasearchBot/3.0-Class-Async"
        self.headers = {"User-Agent": self.user_agent}
        
        self.visited = set()
        self.count = 0
        self.queue = asyncio.Queue()

    @staticmethod
    def clean_url(url):
        url, _ = urldefrag(url)
        return url

    @staticmethod
    def valid_link(url):
        parsed = urlparse(url)
        path = parsed.path.lower()
        bad = (
            ".jpg", ".jpeg", ".png", ".gif",
            ".webp", ".svg",
            ".mp4", ".avi", ".mp3",
            ".pdf", ".zip", ".exe",
            "login", "signup"
        )
        return not path.endswith(bad)

    @staticmethod
    def clean_text(text):
        return re.sub(r"\s+", " ", text).strip()

    async def fetch_page(self, url, session):
        try:
            async with session.get(url, timeout=self.timeout) as response:
                if response.status != 200:
                    return None
                if "text/html" not in response.headers.get("Content-Type", ""):
                    return None
                return await response.text()
        except Exception:
            return None

    async def worker(self, session):
        while True:
            url, depth = await self.queue.get()
            try:
                if url in self.visited or self.count >= self.max_pages or depth > self.max_depth:
                    continue

                self.visited.add(url)
                self.count += 1
                print(f"[{self.count}] Depth={depth}  URL={url}")

                html = await self.fetch_page(url, session)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                title = soup.title.string.strip() if soup.title else "No Title"
                content = self.clean_text(soup.get_text(" "))

                # Blocking ES call inside thread
                await asyncio.to_thread(index_document, url, title, content)

                if depth < self.max_depth:
                    for a in soup.find_all("a"):
                        link = a.get("href")
                        if not link:
                            continue

                        next_url = urljoin(url, link)
                        if not next_url.startswith("http"):
                            continue

                        next_url = self.clean_url(next_url)
                        if self.valid_link(next_url) and next_url not in self.visited:
                            await self.queue.put((next_url, depth + 1))
            finally:
                self.queue.task_done()

    async def run(self, seed_urls):
        for site in seed_urls:
            await self.queue.put((site, 0))

        async with aiohttp.ClientSession(headers=self.headers) as session:
            workers = [
                asyncio.create_task(self.worker(session))
                for _ in range(self.max_concurrency)
            ]
            
            while not self.queue.empty() and self.count < self.max_pages:
                await asyncio.sleep(1)
                
            for w in workers:
                w.cancel()

if __name__ == "__main__":
    SEED_URLS = [
        # Government & Official
        "https://www.india.gov.in/",
        "https://en.wikipedia.org/wiki/India",
        "https://www.isro.gov.in/",
        "https://www.rbi.org.in/",
        
        # News & Information
        "https://www.thehindu.com/",
        "https://www.ndtv.com/",
        "https://timesofindia.indiatimes.com/",
        "https://indianexpress.com/",
        "https://www.hindustantimes.com/",
        
        # Jobs & Education
        "https://www.naukri.com/",
        "https://internshala.com/",
        "https://www.sarkariresult.com/",
        "https://www.bhu.ac.in/",
        "https://www.ignou.ac.in/",
        
        # Technology & Startups
        "https://www.tcs.com/",
        "https://www.infosys.com/",
        "https://www.flipkart.com/",
        "https://www.zomato.com/"
    ]
    
    crawler = Crawler(max_pages=500, max_depth=3, max_concurrency=20)
    print(f"\n🚀 Starting Indiasearch Async Web Crawler (Max {crawler.max_pages} pages)...\n")
    try:
        asyncio.run(crawler.run(SEED_URLS))
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        pass
    print(f"\n✅ DONE — Crawled {crawler.count} pages successfully.\n")
