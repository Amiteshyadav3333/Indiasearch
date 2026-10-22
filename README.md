# 🔍 Indiasearch - AI-Powered Search Engine

Multi-language search engine with AI summaries, spam detection, and fake news filtering.

## 🚀 Features
- Multi-language support (English, Hindi)
- AI-powered search summaries
- Spam & fake news detection
- Elasticsearch-powered search
- Clean, responsive UI

## 📦 Local Setup

### Run with Docker (recommended)

Docker Compose runs the FastAPI app and Redis locally. Elasticsearch can use the
configured Elasticsearch Cloud deployment; if it is not configured, the app's
existing fallback search providers are still available.

```bash
cp -n .env.example .env
# Add your Elasticsearch and optional API credentials to .env
docker compose up --build
```

Open http://localhost:8000. Stop the services with `docker compose down`; Redis
data is kept in a named Docker volume. The `.env` file stays on your machine and
is excluded from the Docker build context. The Compose setup disables the
automatic crawler to keep local startup lightweight.

### Run without Docker

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
5. Railway uses `railway.json` to build the backend with `docker/Dockerfile`.
   Render uses the same Dockerfile through `render.yaml`.

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
