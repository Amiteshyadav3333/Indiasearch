# 🔍 Indiasearch - AI-Powered Search Engine

Multi-language search engine with AI summaries, spam detection, and fake news filtering.

## 🚀 Features
- Multi-language support (English, Hindi)
- AI-powered search summaries
- Spam & fake news detection
- Elasticsearch-powered search
- Clean, responsive UI

## 📦 Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Elasticsearch (required)
elasticsearch

# Run server
cd Indiasearch
python3 -m uvicorn api:app --reload
```

Visit: http://localhost:8000

## 🌐 Production Deployment

### 1. Elasticsearch Cloud Setup
1. Go to https://cloud.elastic.co/
2. Create free deployment
3. Save credentials:
   - ELASTIC_URL
   - ELASTIC_USERNAME
   - ELASTIC_PASSWORD

### 2. Backend Deploy (Railway)
1. Push to GitHub
2. Go to https://railway.app/
3. New Project → Deploy from GitHub
4. Add Environment Variables:
   ```
   ELASTIC_URL=your_elastic_url
   ELASTIC_USERNAME=your_username
   ELASTIC_PASSWORD=your_password
   ```
5. Deploy!

### 3. Frontend Deploy (Vercel)
1. Create `frontend` folder with HTML/CSS/JS
2. Update API_BASE URL in app.js
3. Deploy to https://vercel.com/

## 🛠 Tech Stack
- FastAPI
- Elasticsearch
- Python 3.13
- HTML/CSS/JavaScript

## 📝 Environment Variables

```env
ELASTIC_URL=https://your-deployment.es.cloud
ELASTIC_USERNAME=elastic
ELASTIC_PASSWORD=your_password
```

## 🔧 Crawler Usage

```bash
cd Indiasearch
python3 crawler.py
```

## 📄 License
MIT
