# ▲ Vercel Deployment - Step by Step

## Prerequisites
✅ Railway backend deployed and URL copied

## Step 1: Update Frontend API URL

1. Open: `frontend/app.js`
2. Line 2, change:
```javascript
const API_BASE = "http://localhost:8000";
```
To:
```javascript
const API_BASE = "https://YOUR-RAILWAY-URL.up.railway.app";
```
Example:
```javascript
const API_BASE = "https://indiasearch-production.up.railway.app";
```

3. Save file
4. Commit and push:
```bash
cd /Users/amitesh/Desktop/Indiasearch
git add frontend/app.js
git commit -m "Update API URL for production"
git push
```

## Step 2: Sign Up & Connect GitHub

1. Go to: **https://vercel.com/**
2. Click: **Sign Up** → **Continue with GitHub**
3. Authorize Vercel

## Step 3: Import Project

1. Click: **Add New...** → **Project**
2. Find: **indiasearch** repository
3. Click: **Import**

## Step 4: Configure Project

**Framework Preset:** Other

**Root Directory:** Click **Edit** → Select `frontend` folder

**Build Settings:**
- Build Command: (leave empty)
- Output Directory: (leave empty)
- Install Command: (leave empty)

## Step 5: Deploy

1. Click: **Deploy**
2. Wait 1-2 minutes
3. You'll see: 🎉 Congratulations!

## Step 6: Get Your URL

Your site is live at:
```
https://indiasearch.vercel.app
```
(or similar Vercel URL)

## Step 7: Test Your Search Engine

1. Visit your Vercel URL
2. Search: "India"
3. Check AI summary appears
4. Verify results load

---

## ✅ Vercel Deployment Complete!

Your frontend is now live!

**Frontend:** https://indiasearch.vercel.app
**Backend:** https://YOUR-RAILWAY-URL.up.railway.app

---

## 🎨 Optional: Custom Domain

1. Buy domain (e.g., indiasearch.in)
2. Vercel Dashboard → Project → Settings → Domains
3. Add your domain
4. Update DNS records as shown

---

## 🐛 Troubleshooting

**CORS Error?**
- Check API_BASE URL in app.js
- Verify Railway backend is running
- Check browser console for errors

**No results showing?**
- Test backend directly: `https://YOUR-RAILWAY-URL/search?q=test`
- Check Railway logs
- Verify Elasticsearch has data (run crawler)

**Blank page?**
- Check browser console for errors
- Verify frontend/index.html exists
- Check Vercel deployment logs

---

## 🎉 You're Live!

Share your search engine:
- Frontend: Your Vercel URL
- API: Your Railway URL

Add to resume, portfolio, LinkedIn! 💼
