# ⚡ Quick Start - Deploy in 15 Minutes

## 1. Elasticsearch Cloud (5 min)
👉 https://cloud.elastic.co/registration
- Create free deployment
- Save: URL, username, password

## 2. Push to GitHub (2 min)
```bash
cd /Users/amitesh/Desktop/Indiasearch
git init
git add .
git commit -m "Indiasearch v1"
git remote add origin https://github.com/YOUR_USERNAME/indiasearch.git
git push -u origin main
```

## 3. Deploy Backend - Railway (5 min)
👉 https://railway.app/
- New Project → Deploy from GitHub
- Add env vars: ELASTIC_URL, ELASTIC_USERNAME, ELASTIC_PASSWORD
- Copy Railway URL

## 4. Deploy Frontend - Vercel (3 min)
👉 https://vercel.com/
- Import GitHub repo
- Root Directory: `frontend`
- Update API_BASE in app.js with Railway URL
- Deploy

## 5. Populate Data
```bash
cd Indiasearch
python3 crawler.py
```

## ✅ Done!
Your search engine is live! 🎉
