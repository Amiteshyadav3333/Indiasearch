# 🚂 Railway Deployment - Complete Guide (Hindi)

## ✅ Prerequisites Check
- [x] GitHub account hai
- [x] GitHub pe indiasearch repo upload hai
- [x] Elasticsearch credentials ready hain

---

## 📋 STEP-BY-STEP PROCESS

### STEP 1: Railway Account Banao (2 min)

1. **Browser mein open karo:** https://railway.app/

2. **"Login" button pe click karo** (top right corner)

3. **"Login with GitHub" select karo**

4. **GitHub authorization:**
   - GitHub popup aayega
   - "Authorize Railway" pe click karo
   - Password enter karo if asked

5. ✅ Railway dashboard open ho jayega

---

### STEP 2: New Project Create Karo (1 min)

1. **Dashboard pe "New Project" button pe click karo**
   (Purple button, top right)

2. **"Deploy from GitHub repo" option select karo**

3. **Repository list mein se "indiasearch" dhundo aur select karo**
   - Agar list mein nahi dikh raha:
     - "Configure GitHub App" pe click karo
     - Repositories access do
     - Wapas aao

4. **"Deploy Now" pe click karo**

5. ✅ Deployment start ho jayega (1-2 minutes lagenge)

---

### STEP 3: Environment Variables Add Karo (3 min)

**IMPORTANT:** Ye 3 variables add karne ZAROORI hain!

1. **Deployed service pe click karo**
   (Purple box with your project name)

2. **"Variables" tab pe jao**
   (Top menu mein)

3. **"+ New Variable" button pe click karo**

4. **Pehla Variable add karo:**
   ```
   Variable Name: ELASTIC_URL
   
   Value: https://606ffdc0ae1d4bd1901e6b4b9d84df28.ap-south-1.aws.elastic-cloud.com:443
   ```
   - "Add" pe click karo

5. **Dusra Variable add karo:**
   ```
   Variable Name: ELASTIC_USERNAME
   
   Value: elastic
   ```
   - "Add" pe click karo

6. **Teesra Variable add karo:**
   ```
   Variable Name: ELASTIC_PASSWORD
   
   Value: mRxpkXduHB0A0MvOLS2IABmX
   ```
   - "Add" pe click karo

7. ✅ Railway automatically redeploy karega (1-2 min wait karo)

---

### STEP 4: Public URL Generate Karo (1 min)

1. **"Settings" tab pe jao**
   (Top menu mein)

2. **Neeche scroll karo "Networking" section tak**

3. **"Generate Domain" button pe click karo**

4. **Railway tumhe ek URL dega, jaise:**
   ```
   indiasearch-production.up.railway.app
   ```
   Ya
   ```
   indiasearch-production-a1b2.up.railway.app
   ```

5. **✅ IS URL KO COPY KARO! 📋**
   (Ye tumhara backend API URL hai)

---

### STEP 5: Test Karo Backend (1 min)

1. **Browser mein apna Railway URL open karo:**
   ```
   https://YOUR-RAILWAY-URL.up.railway.app/search?q=india
   ```

2. **Agar sab theek hai to JSON response dikhega:**
   ```json
   {
     "query": "india",
     "page": 1,
     "results_count": 0,
     "results": []
   }
   ```
   (Results 0 honge kyunki abhi data nahi hai - ye normal hai!)

3. ✅ Backend successfully deploy ho gaya!

---

## 🎯 Railway Deployment Complete!

Tumhara backend ab live hai:
```
https://YOUR-RAILWAY-URL.up.railway.app
```

**Is URL ko save karo - Vercel deployment mein chahiye hoga!**

---

## 📊 Railway Dashboard Features

### Logs Dekhna:
- "Deployments" tab → Latest deployment → "View Logs"
- Errors ya issues yahan dikhenge

### Resource Usage:
- Dashboard pe CPU/Memory usage dikhai dega
- Free tier: $5/month credit milta hai

### Redeploy Karna:
- "Deployments" tab → "Deploy" button
- Ya GitHub pe code push karo (auto-deploy hoga)

---

## 🐛 Common Issues & Solutions

### Issue 1: "Build Failed"
**Solution:**
- Logs check karo
- Verify `requirements.txt` GitHub pe hai
- Verify `Procfile` GitHub pe hai

### Issue 2: "Application Error"
**Solution:**
- Variables tab check karo - 3 variables add hain?
- Variable names exactly match karte hain?
- Redeploy karo

### Issue 3: "502 Bad Gateway"
**Solution:**
- Wait karo 2-3 minutes (deployment complete hone do)
- Logs check karo errors ke liye
- Elasticsearch credentials verify karo

### Issue 4: Repository nahi dikh raha
**Solution:**
- Settings → GitHub App → Configure
- Repository access do
- Wapas Railway dashboard pe jao

---

## ✅ Checklist - Sab kuch ho gaya?

- [ ] Railway account bana liya
- [ ] GitHub se connect ho gaya
- [ ] indiasearch repo deploy ho gaya
- [ ] 3 environment variables add ho gaye:
  - [ ] ELASTIC_URL
  - [ ] ELASTIC_USERNAME
  - [ ] ELASTIC_PASSWORD
- [ ] Public domain generate ho gaya
- [ ] Backend URL copy kar liya
- [ ] Test kar liya: `/search?q=india` works

---

## 🎉 Next Step

Ab Vercel pe frontend deploy karo!

**Railway URL ready hai?** ✅
**Toh ab `VERCEL_DEPLOY_HINDI.md` follow karo!**

---

## 💡 Pro Tips

1. **Free Tier:** Railway $5/month credit deta hai - small projects ke liye kaafi hai
2. **Auto Deploy:** GitHub pe push karo, Railway automatically deploy karega
3. **Logs:** Koi issue ho to pehle logs check karo
4. **Environment Variables:** Kabhi bhi change kar sakte ho Variables tab se

---

## 📞 Help Chahiye?

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Check deployment logs for errors

---

**Railway deployment complete! 🚀**
**Ab Vercel pe frontend deploy karo!**
