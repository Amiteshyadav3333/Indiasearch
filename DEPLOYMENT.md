# 🚀 Indiasearch Deployment Guide

## ✅ Pre-Deployment Checklist

- [x] Code fixed and tested locally
- [x] requirements.txt created
- [x] Production config added
- [x] Frontend separated
- [x] CORS enabled

---

## 📋 Step-by-Step Deployment

### 1️⃣ Elasticsearch Cloud (5 minutes)

1. Go to: https://cloud.elastic.co/registration
2. Sign up (free trial available)
3. Create Deployment:
   - Name: `indiasearch`
   - Version: Latest
   - Region: Choose closest to you
4. **SAVE THESE CREDENTIALS:**
   ```
   ELASTIC_URL=https://xxxxx.es.cloud:443
   ELASTIC_USERNAME=elastic
   ELASTIC_PASSWORD=xxxxxxxxxx
   ```

### 2️⃣ GitHub Setup (2 minutes)

```bash
cd /Users/amitesh/Desktop/Indiasearch
git init
git add .
git commit -m "Initial commit - Indiasearch"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/indiasearch.git
git push -u origin main
```

### 3️⃣ Backend Deploy - Railway (5 minutes)

1. Go to: https://railway.app/
2. Sign in with GitHub
3. Click: **New Project** → **Deploy from GitHub repo**
4. Select: `indiasearch` repository
5. Add Environment Variables:
   ```
   ELASTIC_URL=your_elastic_cloud_url
   ELASTIC_USERNAME=elastic
   ELASTIC_PASSWORD=your_password
   ```
6. Railway will auto-detect and deploy
7. **Copy your Railway URL**: `https://indiasearch-production.up.railway.app`

### 4️⃣ Frontend Deploy - Vercel (3 minutes)

1. Go to: https://vercel.com/
2. Sign in with GitHub
3. Click: **Add New** → **Project**
4. Import: `indiasearch` repository
5. Settings:
   - Root Directory: `frontend`
   - Framework Preset: Other
6. Before deploy, update `frontend/app.js`:
   ```javascript
   const API_BASE = "https://your-railway-url.up.railway.app";
   ```
7. Click **Deploy**
8. Your site will be live at: `https://indiasearch.vercel.app`

---

## 🧪 Testing Production

1. Visit your Vercel URL
2. Search: "India cricket"
3. Check AI summary appears
4. Verify results load

---

## 🔧 Run Crawler (One-time)

After deployment, populate Elasticsearch:

```bash
cd Indiasearch
python3 crawler.py
```

This will index ~200 pages from seed sites.

---

## 🎯 Custom Domain (Optional)

### Buy Domain:
- Namecheap: `indiasearch.in` (~₹500/year)
- GoDaddy: `indiasearch.ai` (~₹2000/year)

### Connect to Vercel:
1. Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Update DNS records as shown

---

## 📊 Monitor Your App

**Railway Dashboard:**
- View logs
- Check CPU/Memory usage
- Monitor requests

**Elasticsearch Cloud:**
- Check index size
- View search queries
- Monitor performance

---

## 🐛 Common Issues

**Issue: "Connection refused"**
- Check Elasticsearch credentials
- Verify Railway environment variables

**Issue: "No results found"**
- Run crawler to populate data
- Check Elasticsearch index exists

**Issue: CORS error**
- Verify CORS middleware in api.py
- Check API_BASE URL in frontend

---

## 🎉 You're Live!

Your search engine is now:
✅ Publicly accessible
✅ Scalable
✅ Production-ready
✅ Resume-worthy

Share your link! 🚀
