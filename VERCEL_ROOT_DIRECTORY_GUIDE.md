# 📸 Vercel Root Directory - Step by Step Screenshots Guide

## ⚠️ SABSE IMPORTANT STEP!

Root Directory set karna ZAROORI hai, warna deployment fail hogi!

---

## 🎯 Root Directory Kaise Edit Kare:

### STEP 1: Import Project Screen

Jab tum "indiasearch" repository import karoge, ye screen dikhega:

```
┌─────────────────────────────────────────────────────┐
│  Configure Project                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Project Name: indiasearch                          │
│                                                     │
│  Framework Preset: [Other ▼]                        │
│                                                     │
│  Root Directory: ./                [Edit] ←─────────┐
│                                                     │
│  Build and Output Settings                          │
│    Build Command: (empty)                           │
│    Output Directory: (empty)                        │
│    Install Command: (empty)                         │
│                                                     │
│  Environment Variables                              │
│    [+ Add]                                          │
│                                                     │
│                              [Deploy] ←─────────────┤
└─────────────────────────────────────────────────────┘
```

### STEP 2: "Edit" Button Pe Click Karo

**Root Directory** ke saamne **"Edit"** button dikhega
👆 Us pe click karo!

```
Root Directory: ./    [Edit] ← YE BUTTON
```

---

### STEP 3: Dropdown Open Hoga

Click karne ke baad ek dropdown menu open hoga:

```
┌─────────────────────────────────┐
│ Select Root Directory           │
├─────────────────────────────────┤
│ ○ ./                            │  ← Default (WRONG!)
│ ○ frontend                      │  ← YE SELECT KARO! ✅
│ ○ Indiasearch                   │
└─────────────────────────────────┘
```

---

### STEP 4: "frontend" Select Karo

**"frontend"** option pe click karo ✅

Ab screen aisi dikhegi:

```
┌─────────────────────────────────────────────────────┐
│  Configure Project                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Root Directory: frontend/     [Edit]               │
│                  ^^^^^^^^                           │
│                  ✅ YE HO GAYA!                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### STEP 5: Verify Karo

**Check karo:**
- ✅ Root Directory: `frontend/` dikhai de raha hai
- ✅ Framework Preset: `Other` hai
- ✅ Build Command: Empty hai

**Sab theek hai? Deploy karo!**

---

## 🎯 Alternative Method (Agar Edit Button Nahi Dikha)

Agar "Edit" button nahi dikh raha:

### Method 1: Manual Type Karo

1. Root Directory field pe click karo
2. Delete karo `./`
3. Type karo: `frontend`
4. Enter press karo

### Method 2: After Deployment

Agar galti se deploy ho gaya without setting:

1. Project Settings pe jao
2. General tab
3. Root Directory section
4. "frontend" enter karo
5. Save karo
6. Redeploy karo

---

## ✅ Correct Configuration:

```
Project Name:        indiasearch
Framework Preset:    Other
Root Directory:      frontend/          ← MUST BE THIS!
Build Command:       (empty)
Output Directory:    (empty)
Install Command:     (empty)
```

---

## ❌ Common Mistakes:

### WRONG ❌
```
Root Directory: ./
```
Ya
```
Root Directory: Indiasearch
```

### CORRECT ✅
```
Root Directory: frontend
```
Ya
```
Root Directory: frontend/
```

---

## 🐛 Agar Galti Ho Gayi?

### Symptom: 404 Error ya Blank Page

**Fix:**

1. Vercel Dashboard pe jao
2. Project select karo
3. Settings → General
4. Root Directory section mein:
   - Current: `./`
   - Change to: `frontend`
5. Save karo
6. Deployments tab → Redeploy

---

## 📸 Visual Reference:

```
BEFORE (Wrong):
┌──────────────────────────┐
│ Root Directory: ./       │  ❌
└──────────────────────────┘

AFTER (Correct):
┌──────────────────────────┐
│ Root Directory: frontend │  ✅
└──────────────────────────┘
```

---

## 🎯 Quick Checklist:

Before clicking "Deploy":

- [ ] Root Directory = "frontend" ✅
- [ ] Framework Preset = "Other" ✅
- [ ] Build Command = Empty ✅
- [ ] Output Directory = Empty ✅

**Sab check? Deploy karo!** 🚀

---

## 💡 Why "frontend"?

Tumhara project structure:
```
indiasearch/
├── frontend/          ← YE FOLDER DEPLOY KARNA HAI
│   ├── index.html
│   ├── app.js
│   └── style.css
├── Indiasearch/       ← Backend (Railway pe hai)
└── README.md
```

Vercel ko sirf `frontend/` folder chahiye!

---

**Ab deploy karo! 🚀**
