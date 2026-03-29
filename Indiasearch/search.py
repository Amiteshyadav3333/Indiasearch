from elasticsearch import Elasticsearch
from ddgs import DDGS
import asyncio
import re

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
            fetch_limit = from_ + size + 10
            
            def fetch_ddg():
                return list(DDGS().text(query, max_results=fetch_limit))
            
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
        def fetch_img():
            return list(DDGS().images(query, max_results=from_ + size + 10))
        
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
        return [], 0

async def global_video_search(query: str, page: int = 1):
    size = 10
    from_ = (page - 1) * size
    try:
        def fetch_vid():
            return list(DDGS().videos(query, max_results=from_ + size + 10))
            
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