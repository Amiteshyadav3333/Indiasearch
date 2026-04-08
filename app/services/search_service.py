from elasticsearch import Elasticsearch
import asyncio
import re
from urllib.parse import quote

try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

# Mock Data for Fallback
FAMOUS_WEBSITES = [
    # --- GLOBAL GIANTS ---
    {"title": "LinkedIn - Jobs & Networking", "url": "https://www.linkedin.com/jobs", "content": "Search for jobs, connect with professionals, and build your career on LinkedIn. Find internships and full-time roles worldwide."},
    {"title": "Indeed - Job Search", "url": "https://www.indeed.com", "content": "Indeed is the #1 job site in the world. Search millions of jobs online to find the next step in your career."},
    {"title": "Glassdoor - Jobs and Company Reviews", "url": "https://www.glassdoor.com", "content": "Search jobs, read company reviews and salary data, and prepare for interviews on Glassdoor."},
    {"title": "Monster - Job Search", "url": "https://www.monster.com", "content": "Find the job that's right for you on Monster. Search millions of jobs and get career advice."},
    {"title": "ZipRecruiter - Job Search", "url": "https://www.ziprecruiter.com", "content": "The smartest way to get hired. Search for jobs and apply with one tap."},
    {"title": "SimplyHired - Job Search Engine", "url": "https://www.simplyhired.com", "content": "Search millions of jobs from all over the web. Find local jobs, salary comparisons, and employment trends."},
    {"title": "CareerBuilder - Job Search", "url": "https://www.careerbuilder.com", "content": "Find the right job. Helper with resume building and career advice. Search for jobs near you."},

    # --- INDIA SPECIFIC ---
    {"title": "Naukri.com - Jobs in India", "url": "https://www.naukri.com", "content": "India's No. 1 Job Portal. Search and apply for improved job opportunities for freshers and experienced professionals."},
    {"title": "Internshala - Internships & Creating Careers", "url": "https://internshala.com", "content": "Apply to thousands of internships in India. Summer trainings and internships for students."},
    {"title": "Foundit (formerly Monster India)", "url": "https://www.foundit.in", "content": "Search for jobs in India. Find employment opportunities for freshers and experienced candidates."},
    {"title": "Shine.com - Jobs", "url": "https://www.shine.com", "content": "Leading job portal in India. Search and apply for jobs in IT, BPO, Sales, Marketing, and more."},
    {"title": "TimesJobs - Job Search", "url": "https://www.timesjobs.com", "content": "Find the best job opportunities across top companies in India. Search by skill, location, and role."},
    {"title": "Freshersworld - Jobs for Freshers", "url": "https://www.freshersworld.com", "content": "The number 1 job site for freshers in India. Government jobs, private jobs, and walk-in interviews."},
    {"title": "Instahyre - Job Search for Premium Talent", "url": "https://www.instahyre.com", "content": "Zero-hassle hiring platform for top startups and enterprises in India. AI-based job matching."},
    {"title": "Hirist - Premium Tech Jobs", "url": "https://www.hirist.com", "content": "Exclusive job portal for technology professionals in India. Find jobs in Java, Python, Big Data, and more."},
    {"title": "IIMJobs - Management Jobs", "url": "https://www.iimjobs.com", "content": "Exclusive job portal for management professionals in India. MBA jobs, finance, consulting, and marketing roles."},
    {"title": "Cutshort - Tech Jobs & Hiring", "url": "https://cutshort.io", "content": "Hire the best tech talent or find the best tech jobs in India. AI-powered matching platform."},

    # --- REMOTE & FREELANCE ---
    {"title": "Upwork - Freelance Jobs", "url": "https://www.upwork.com", "content": "Find freelance jobs and hire top freelancers. Web development, design, writing, and more."},
    {"title": "Fiverr - Freelance Serevices", "url": "https://www.fiverr.com", "content": "Find the perfect freelance services for your business. Graphics, marketing, programming, and more."},
    {"title": "Freelancer.com - Hire Freelancers", "url": "https://www.freelancer.com", "content": "Hire freelancers for any job. Web design, mobile app development, writing, and data entry."},
    {"title": "Toptal - Hire Top Freelancers", "url": "https://www.toptal.com", "content": "Hire the top 3% of freelance talent. Developers, designers, finance experts, and product managers."},
    {"title": "We Work Remotely - Remote Jobs", "url": "https://weworkremotely.com", "content": "The largest remote work community in the world. Find and list jobs that aren't restricted by commutes or a particular geographic area."},
    {"title": "Remote OK - Remote Jobs", "url": "https://remoteok.com", "content": "Find the best remote jobs in software development, design, marketing, and more."},
    {"title": "FlexJobs - Remote & Flexible Jobs", "url": "https://www.flexjobs.com", "content": "The #1 job site to find vetted remote, work from home, and flexible job opportunities."},

    # --- TECH SPECIFIC ---
    {"title": "Stack Overflow Jobs", "url": "https://stackoverflow.com/jobs", "content": "Find the best developer jobs. Search for jobs by technology, role, and location."},
    {"title": "Dice.com - Tech Jobs", "url": "https://www.dice.com", "content": "The leading career destination for tech experts. Search and apply for technology jobs."},
    {"title": "HackerRank Jobs", "url": "https://www.hackerrank.com/jobs", "content": "Get matched with the best tech companies. Coding challenges and job search for developers."},
    {"title": "AngelList (Wellfound) - Startup Jobs", "url": "https://wellfound.com", "content": "The world's number 1 startup community. Find unique jobs at startups and tech companies."},

    # --- GOVERNMENT JOBS (INDIA) ---
    {"title": "Sarkari Result", "url": "https://www.sarkariresult.com", "content": "Leading job portal for government jobs in India. Sarkari Naukri, admit cards, results, and more."},
    {"title": "FreeJobAlert - Govt Jobs", "url": "https://www.freejobalert.com", "content": "Get free job alerts for all government jobs in India. Bank jobs, railway jobs, police jobs, and defence jobs."},
    {"title": "Jagran Josh - Education & Jobs", "url": "https://www.jagranjosh.com", "content": "Education and career portal. Current affairs, government job notifications, and exam preparation."},

    # --- LEARNING & COURSES (for career growth) ---
    {"title": "Coursera - Online Courses", "url": "https://www.coursera.org", "content": "Build skills with courses from top universities. Professional certificates and degrees."},
    {"title": "Udemy - Online Courses", "url": "https://www.udemy.com", "content": "Learn anything on your schedule. Programming, marketing, data science, and more."},
    {"title": "edX - Free Online Courses", "url": "https://www.edx.org", "content": "Access 2500+ online courses from 140 top institutions. Harvard, MIT, Microsoft, and more."},
    {"title": "Udacity - Tech Skills", "url": "https://www.udacity.com", "content": "Advance your career with online courses in programming, data science, artificial intelligence, and more."},
    {"title": "Pluralsight - Tech Skills", "url": "https://www.pluralsight.com", "content": "The technology skills platform. Learn software development, IT ops, and cyber security."},

    # --- FAMOUS WEBSITES (Previous) ---
    {"title": "Google - Search Engine", "url": "https://www.google.com", "content": "Google is the world's most popular search engine. Search the web, find images, videos, news, and more."},
    {"title": "Facebook - Social Network", "url": "https://www.facebook.com", "content": "Facebook is the world's largest social networking site. Connect with friends and family."},
    {"title": "YouTube - Video Sharing Platform", "url": "https://www.youtube.com", "content": "YouTube is the world's largest video sharing platform. Watch, upload, and share videos."}
]


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_snippet(content, query):
    content = clean_text(content)

    query = query.lower()

    idx = content.lower().find(query)

    if idx == -1:
        return content[:160] + "..."

    start = max(idx - 60, 0)
    end = min(idx + 60, len(content))

    snippet = content[start:end]

    return "... " + snippet + " ..."


def local_search(query):
    """
    Search in local famous websites list if ES fails
    """
    results = []
    query_lower = query.lower()

    for site in FAMOUS_WEBSITES:
        # Check if query matches title or content
        if query_lower in site["title"].lower() or query_lower in site["content"].lower():
            snippet = make_snippet(site["content"], query)
            results.append({
                "title": site["title"],
                "url": site["url"],
                "snippet": snippet,
                "score": 1.0
            })
    
    return results


def curated_thumbnail_url(query: str, title: str, domain: str, category: str) -> str:
    text = f"{query} | {title}".lower()
    domain_label = (domain or "web").replace("www.", "")[:28]

    if category == "Tech":
        palette = ("0f172a", "2563eb", "dbeafe")
        label = "Tech Preview"
        shape_svg = f"""
          <rect x='620' y='120' width='180' height='120' rx='24' fill='rgba(255,255,255,0.12)' />
          <rect x='650' y='150' width='120' height='10' rx='5' fill='rgba(255,255,255,0.55)' />
          <rect x='650' y='176' width='90' height='10' rx='5' fill='rgba(255,255,255,0.35)' />
          <rect x='620' y='490' width='220' height='36' rx='18' fill='rgba(255,255,255,0.1)' />
        """
    elif category == "News":
        palette = ("7f1d1d", "dc2626", "fee2e2")
        label = "News Preview"
        shape_svg = f"""
          <rect x='610' y='120' width='220' height='300' rx='28' fill='rgba(255,255,255,0.1)' />
          <rect x='645' y='160' width='150' height='110' rx='18' fill='rgba(255,255,255,0.18)' />
          <rect x='645' y='300' width='150' height='12' rx='6' fill='rgba(255,255,255,0.5)' />
          <rect x='645' y='326' width='120' height='12' rx='6' fill='rgba(255,255,255,0.34)' />
        """
    elif category == "Jobs":
        palette = ("14532d", "16a34a", "dcfce7")
        label = "Jobs Preview"
        shape_svg = f"""
          <rect x='610' y='128' width='230' height='260' rx='28' fill='rgba(255,255,255,0.1)' />
          <circle cx='725' cy='190' r='38' fill='rgba(255,255,255,0.16)' />
          <rect x='655' y='260' width='140' height='14' rx='7' fill='rgba(255,255,255,0.55)' />
          <rect x='640' y='300' width='170' height='48' rx='24' fill='rgba(255,255,255,0.12)' />
        """
    elif category == "Education":
        palette = ("4c1d95", "7c3aed", "f3e8ff")
        label = "Education Preview"
        shape_svg = f"""
          <rect x='610' y='120' width='220' height='250' rx='28' fill='rgba(255,255,255,0.1)' />
          <path d='M650 205 L720 165 L790 205 L720 245 Z' fill='rgba(255,255,255,0.2)' />
          <rect x='665' y='282' width='110' height='12' rx='6' fill='rgba(255,255,255,0.52)' />
          <rect x='645' y='312' width='150' height='12' rx='6' fill='rgba(255,255,255,0.32)' />
        """
    else:
        palette = ("1f2937", "f59e0b", "fef3c7")
        label = "Web Preview"
        shape_svg = f"""
          <rect x='615' y='132' width='225' height='240' rx='28' fill='rgba(255,255,255,0.1)' />
          <circle cx='728' cy='220' r='56' fill='rgba(255,255,255,0.16)' />
          <rect x='658' y='310' width='140' height='12' rx='6' fill='rgba(255,255,255,0.45)' />
        """

    dark, accent, light = palette
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='960' height='720' viewBox='0 0 960 720'>
      <defs>
        <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0%' stop-color='#{dark}' />
          <stop offset='100%' stop-color='#{accent}' />
        </linearGradient>
      </defs>
      <rect width='960' height='720' rx='42' fill='url(#bg)' />
      <circle cx='770' cy='130' r='110' fill='rgba(255,255,255,0.12)' />
      <circle cx='180' cy='590' r='150' fill='rgba(255,255,255,0.08)' />
      <rect x='70' y='86' width='820' height='548' rx='30' fill='rgba(255,255,255,0.12)' stroke='rgba(255,255,255,0.18)' />
      <rect x='108' y='132' width='210' height='54' rx='27' fill='#{light}' />
      <text x='213' y='166' text-anchor='middle' font-family='Arial, sans-serif' font-size='30' font-weight='700' fill='#{accent}'>{label}</text>
      <rect x='108' y='500' width='220' height='48' rx='24' fill='rgba(255,255,255,0.14)' />
      <text x='218' y='531' text-anchor='middle' font-family='Arial, sans-serif' font-size='22' font-weight='700' fill='white'>{domain_label}</text>
      <text x='108' y='286' font-family='Arial, sans-serif' font-size='54' font-weight='700' fill='white'>{title[:28]}</text>
      <text x='108' y='344' font-family='Arial, sans-serif' font-size='54' font-weight='700' fill='white'>{query[:28]}</text>
      <text x='108' y='438' font-family='Arial, sans-serif' font-size='26' fill='rgba(255,255,255,0.88)'>Curated fallback preview for related web sources</text>
      {shape_svg}
    </svg>
    """
    return f"data:image/svg+xml;charset=UTF-8,{quote(svg)}"


def detect_image_fallback_category(query: str, title: str, url: str) -> str:
    text = f"{query} {title} {url}".lower()

    if any(word in text for word in ["python", "code", "developer", "programming", "github", "ai", "tech", "software"]):
        return "Tech"
    if any(word in text for word in ["news", "india", "ndtv", "times", "hindu", "breaking", "express", "bbc"]):
        return "News"
    if any(word in text for word in ["job", "career", "internship", "naukri", "hiring", "salary", "resume"]):
        return "Jobs"
    if any(word in text for word in ["course", "learn", "education", "university", "tutorial", "school", "academy"]):
        return "Education"
    return "Web"


async def search_query(es: Elasticsearch, index: str, query: str, page: int = 1):
    
    results = []
    total_hits = 0
    size = 10
    from_ = (page - 1) * size

    # 1. Try Elasticsearch
    try:
        if es.ping(): # Check connection first
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title^3",
                            "content"
                        ]
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {}
                    }
                },
                "size": size,
                "from": from_
            }

            res = es.search(index=index, body=body)
            total = res["hits"]["total"]
            total_hits = total["value"] if isinstance(total, dict) else total

            for hit in res["hits"]["hits"]:
                source = hit["_source"]
                title = source.get("title", "No Title")
                url = source.get("url", "")
                content = source.get("content", "")
                snippet = make_snippet(content, query)

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "score": hit["_score"]
                })
    except Exception as e:
        print(f"ES Search Error (falling back to local): {e}")
        pass

    # 2. If no results from ES (or error), use Global Web Search Fallback (DuckDuckGo API)
    if not results:
        print("⚠️ No local ES results, dynamically fetching from GLOBAL WEB via API...")
        try:
            if DDGS is None:
                raise RuntimeError("ddgs is not installed in the active Python environment")

            fetch_limit = from_ + size + 10
            
            def fetch_ddg():
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=fetch_limit))
            
            raw_results = await asyncio.to_thread(fetch_ddg)
            all_results = []
            for r in raw_results:
                all_results.append({
                    "title": r.get('title', 'Global Result'),
                    "url": r.get('href', ''),
                    "snippet": r.get('body', ''),
                    "score": 1.0
                })
            
            # Simulated large hitpool for frontend pagination calculation
            total_hits = max(len(all_results), 50 if len(all_results) > 10 else len(all_results))
            results = all_results[from_:from_ + size]
        except Exception as e:
            print(f"Global API Error: {e}")
            all_results = local_search(query)
            total_hits = len(all_results)
            results = all_results[from_:from_ + size]

    return results, total_hits

async def global_image_search(query: str, page: int = 1):
    size = 10
    from_ = (page - 1) * size
    try:
        if DDGS is None:
            raise RuntimeError("ddgs is not installed in the active Python environment")

        def fetch_img():
            with DDGS() as ddgs:
                return list(ddgs.images(query, max_results=from_ + size + 10))
        
        raw_results = await asyncio.to_thread(fetch_img)
        results = []
        for r in raw_results[from_ : from_ + size]:
            results.append({
                "title": r.get("title", "Image Result"),
                "url": r.get("image", ""),
                "snippet": f"📸 Original Source: {r.get('source', 'Unknown')} | Resolution: {r.get('width')}x{r.get('height')}",
                "score": 1.0
            })
        return results, min(len(raw_results), 100)
    except Exception as e:
        print(f"Image API Error: {e}")
        fallback_sites = local_search(query)
        fallback_results = []

        for site in fallback_sites[from_: from_ + size]:
            domain = ""
            try:
                from urllib.parse import urlparse
                domain = urlparse(site["url"]).netloc
            except Exception:
                domain = ""
            category = detect_image_fallback_category(query, site["title"], site["url"])

            fallback_results.append({
                "title": site["title"],
                "url": curated_thumbnail_url(query, site["title"], domain, category),
                "snippet": f"Fallback Preview | {category} | Related source: {site['url']}",
                "score": 0.5
            })

        return fallback_results, len(fallback_sites)

async def global_video_search(query: str, page: int = 1):
    size = 10
    from_ = (page - 1) * size
    try:
        if DDGS is None:
            raise RuntimeError("ddgs is not installed in the active Python environment")

        def fetch_vid():
            with DDGS() as ddgs:
                return list(ddgs.videos(query, max_results=from_ + size + 10))
            
        raw_results = await asyncio.to_thread(fetch_vid)
        results = []
        for r in raw_results[from_ : from_ + size]:
            content_url = r.get("content") or r.get("href") or ""
            publisher = r.get("publisher", "Video Platform")
            duration = r.get("duration", "N/A")
            
            results.append({
                "title": f"🎥 {r.get('title', 'Video Result')}",
                "url": content_url,
                "snippet": f"⏱️ Duration: {duration} | 🏢 Publisher: {publisher} | Click to stream video instantly.",
                "score": 1.0
            })
        return results, min(len(raw_results), 100)
    except Exception as e:
        print(f"Video API Error: {e}")
        return [], 0
