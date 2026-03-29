
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from elasticsearch import Elasticsearch

# Use the exact same credential loading as api.py
ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_USER = os.getenv("ELASTIC_USERNAME")
ELASTIC_PASS = os.getenv("ELASTIC_PASSWORD")

INDEX_NAME = "indiasearch"

es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASS))

# Jobs & Internships Websites
JOB_SITES = [
    # --- GLOBAL GIANTS ---
    {"title": "LinkedIn - Jobs & Networking", "url": "https://www.linkedin.com/jobs", "snippet": "Search for jobs, connect with professionals, and build your career on LinkedIn. Find internships and full-time roles worldwide."},
    {"title": "Indeed - Job Search", "url": "https://www.indeed.com", "snippet": "Indeed is the #1 job site in the world. Search millions of jobs online to find the next step in your career."},
    {"title": "Glassdoor - Jobs and Company Reviews", "url": "https://www.glassdoor.com", "snippet": "Search jobs, read company reviews and salary data, and prepare for interviews on Glassdoor."},
    {"title": "Monster - Job Search", "url": "https://www.monster.com", "snippet": "Find the job that's right for you on Monster. Search millions of jobs and get career advice."},
    {"title": "ZipRecruiter - Job Search", "url": "https://www.ziprecruiter.com", "snippet": "The smartest way to get hired. Search for jobs and apply with one tap."},
    {"title": "SimplyHired - Job Search Engine", "url": "https://www.simplyhired.com", "snippet": "Search millions of jobs from all over the web. Find local jobs, salary comparisons, and employment trends."},
    {"title": "CareerBuilder - Job Search", "url": "https://www.careerbuilder.com", "snippet": "Find the right job. Helper with resume building and career advice. Search for jobs near you."},

    # --- INDIA SPECIFIC ---
    {"title": "Naukri.com - Jobs in India", "url": "https://www.naukri.com", "snippet": "India's No. 1 Job Portal. Search and apply for improved job opportunities for freshers and experienced professionals."},
    {"title": "Internshala - Internships & Creating Careers", "url": "https://internshala.com", "snippet": "Apply to thousands of internships in India. Summer trainings and internships for students."},
    {"title": "Foundit (formerly Monster India)", "url": "https://www.foundit.in", "snippet": "Search for jobs in India. Find employment opportunities for freshers and experienced candidates."},
    {"title": "Shine.com - Jobs", "url": "https://www.shine.com", "snippet": "Leading job portal in India. Search and apply for jobs in IT, BPO, Sales, Marketing, and more."},
    {"title": "TimesJobs - Job Search", "url": "https://www.timesjobs.com", "snippet": "Find the best job opportunities across top companies in India. Search by skill, location, and role."},
    {"title": "Freshersworld - Jobs for Freshers", "url": "https://www.freshersworld.com", "snippet": "The number 1 job site for freshers in India. Government jobs, private jobs, and walk-in interviews."},
    {"title": "Instahyre - Job Search for Premium Talent", "url": "https://www.instahyre.com", "snippet": "Zero-hassle hiring platform for top startups and enterprises in India. AI-based job matching."},
    {"title": "Hirist - Premium Tech Jobs", "url": "https://www.hirist.com", "snippet": "Exclusive job portal for technology professionals in India. Find jobs in Java, Python, Big Data, and more."},
    {"title": "IIMJobs - Management Jobs", "url": "https://www.iimjobs.com", "snippet": "Exclusive job portal for management professionals in India. MBA jobs, finance, consulting, and marketing roles."},
    {"title": "Cutshort - Tech Jobs & Hiring", "url": "https://cutshort.io", "snippet": "Hire the best tech talent or find the best tech jobs in India. AI-powered matching platform."},

    # --- REMOTE & FREELANCE ---
    {"title": "Upwork - Freelance Jobs", "url": "https://www.upwork.com", "snippet": "Find freelance jobs and hire top freelancers. Web development, design, writing, and more."},
    {"title": "Fiverr - Freelance Serevices", "url": "https://www.fiverr.com", "snippet": "Find the perfect freelance services for your business. Graphics, marketing, programming, and more."},
    {"title": "Freelancer.com - Hire Freelancers", "url": "https://www.freelancer.com", "snippet": "Hire freelancers for any job. Web design, mobile app development, writing, and data entry."},
    {"title": "Toptal - Hire Top Freelancers", "url": "https://www.toptal.com", "snippet": "Hire the top 3% of freelance talent. Developers, designers, finance experts, and product managers."},
    {"title": "We Work Remotely - Remote Jobs", "url": "https://weworkremotely.com", "snippet": "The largest remote work community in the world. Find and list jobs that aren't restricted by commutes or a particular geographic area."},
    {"title": "Remote OK - Remote Jobs", "url": "https://remoteok.com", "snippet": "Find the best remote jobs in software development, design, marketing, and more."},
    {"title": "FlexJobs - Remote & Flexible Jobs", "url": "https://www.flexjobs.com", "snippet": "The #1 job site to find vetted remote, work from home, and flexible job opportunities."},

    # --- TECH SPECIFIC ---
    {"title": "Stack Overflow Jobs", "url": "https://stackoverflow.com/jobs", "snippet": "Find the best developer jobs. Search for jobs by technology, role, and location."},
    {"title": "Dice.com - Tech Jobs", "url": "https://www.dice.com", "snippet": "The leading career destination for tech experts. Search and apply for technology jobs."},
    {"title": "HackerRank Jobs", "url": "https://www.hackerrank.com/jobs", "snippet": "Get matched with the best tech companies. Coding challenges and job search for developers."},
    {"title": "AngelList (Wellfound) - Startup Jobs", "url": "https://wellfound.com", "snippet": "The world's number 1 startup community. Find unique jobs at startups and tech companies."},

    # --- GOVERNMENT JOBS (INDIA) ---
    {"title": "Sarkari Result", "url": "https://www.sarkariresult.com", "snippet": "Leading job portal for government jobs in India. Sarkari Naukri, admit cards, results, and more."},
    {"title": "FreeJobAlert - Govt Jobs", "url": "https://www.freejobalert.com", "snippet": "Get free job alerts for all government jobs in India. Bank jobs, railway jobs, police jobs, and defence jobs."},
    {"title": "Jagran Josh - Education & Jobs", "url": "https://www.jagranjosh.com", "snippet": "Education and career portal. Current affairs, government job notifications, and exam preparation."},

    # --- LEARNING & COURSES (for career growth) ---
    {"title": "Coursera - Online Courses", "url": "https://www.coursera.org", "snippet": "Build skills with courses from top universities. Professional certificates and degrees."},
    {"title": "Udemy - Online Courses", "url": "https://www.udemy.com", "snippet": "Learn anything on your schedule. Programming, marketing, data science, and more."},
    {"title": "edX - Free Online Courses", "url": "https://www.edx.org", "snippet": "Access 2500+ online courses from 140 top institutions. Harvard, MIT, Microsoft, and more."},
    {"title": "Udacity - Tech Skills", "url": "https://www.udacity.com", "snippet": "Advance your career with online courses in programming, data science, artificial intelligence, and more."},
    {"title": "Pluralsight - Tech Skills", "url": "https://www.pluralsight.com", "snippet": "The technology skills platform. Learn software development, IT ops, and cyber security."},
]

def add_jobs():
    print(f"🚀 Adding {len(JOB_SITES)} job & internship websites to IndiaSearch...")
    
    count = 0
    for site in JOB_SITES:
        doc = {
            "title": site["title"],
            "url": site["url"],
            "snippet": site["snippet"],
            "content": site["title"] + " " + site["snippet"], # Simple content for search
            "language": "en"
        }
        try:
            es.index(index=INDEX_NAME, document=doc)
            print(f"✅ Added: {site['title']}")
            count += 1
        except Exception as e:
            print(f"❌ Failed: {site['title']} - {e}")

    print(f"\n🎉 Successfully added {count} job/internship websites!")

if __name__ == "__main__":
    try:
        if es.ping():
            add_jobs()
            print("\n✅ DONE! Jobs added.")
        else:
            print("❌ Could not connect to Elasticsearch. Check your credentials.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")