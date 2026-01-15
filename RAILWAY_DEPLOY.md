# 🚂 Railway Deployment - Step by Step

## Step 1: Sign Up & Connect GitHub

1. Go to: **https://railway.app/**
2. Click: **Login** → **Login with GitHub**
3. Authorize Railway to access your GitHub

## Step 2: Create New Project

1. Click: **New Project** (top right)
2. Select: **Deploy from GitHub repo**
3. Choose: **indiasearch** repository
4. Click: **Deploy Now**

Railway will automatically:
- ✅ Detect Python
- ✅ Install dependencies from requirements.txt
- ✅ Start your app using Procfile

## Step 3: Add Environment Variables

1. Click on your deployed service
2. Go to: **Variables** tab
3. Click: **+ New Variable**
4. Add these 3 variables:

```
ELASTIC_URL
https://606ffdc0ae1d4bd1901e6b4b9d84df28.ap-south-1.aws.elastic-cloud.com:443

ELASTIC_USERNAME
elastic

ELASTIC_PASSWORD
mRxpkXduHB0A0MvOLS2IABmX
```

5. Railway will auto-redeploy

## Step 4: Get Your Backend URL

1. Go to: **Settings** tab
2. Scroll to: **Networking** section
3. Click: **Generate Domain**
4. Copy your URL (e.g., `indiasearch-production.up.railway.app`)

## Step 5: Test Backend

Open in browser:
```
https://YOUR-RAILWAY-URL.up.railway.app/search?q=india
```

You should see JSON response with results!

---

## ✅ Railway Deployment Complete!

Your backend is now live at:
**https://YOUR-RAILWAY-URL.up.railway.app**

Save this URL - you'll need it for Vercel frontend!

---

## 🐛 Troubleshooting

**Deployment failed?**
- Check Logs tab for errors
- Verify requirements.txt exists
- Check Procfile syntax

**No results?**
- Verify environment variables are correct
- Check Elasticsearch connection in logs
- Run crawler to populate data

**500 Error?**
- Check deployment logs
- Verify Elasticsearch credentials
- Test Elasticsearch connection

---

**Next:** Deploy frontend on Vercel (see VERCEL_DEPLOY.md)
