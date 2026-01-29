# Deployment Guide

This project is configured for:
- **Frontend**: Vercel (SPA hosting)
- **Backend**: Render (Python FastAPI + Qdrant Vector DB)

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account
- GitHub repository connected to Vercel

### Setup
1. Go to https://vercel.com and connect your GitHub repo
2. Select the `doTERRA_essential_oils_recos` project
3. Configure settings:
   - **Root Directory**: `frontend`
   - **Framework**: Vite
   - **Build Command**: Already configured in `vercel.json`
   - **Output Directory**: Already configured in `vercel.json`

4. Add environment variable:
   - `VITE_API_URL`: Set to your Render backend URL (e.g., `https://doterra-backend.onrender.com`)

5. Deploy by pushing to main branch or manually trigger in Vercel dashboard

### Troubleshooting
- If builds fail, ensure `frontend/package.json` has correct dependencies
- Clear Vercel cache and rebuild if needed

---

## Backend Deployment (Render)

### Prerequisites
- Render account
- GitHub repository connected to Render

### Option 1: Using `render.yaml` (Recommended)

1. Go to Render Dashboard
2. Click "New+" → "Web Service"
3. Connect your GitHub repository
4. Select branch (main) and set root directory to project root
5. Render will auto-detect `render.yaml`

### Option 2: Manual Setup

1. Create Web Service:
   - Name: `doterra-backend`
   - Runtime: Python 3.12
   - Build Command: `pip install uv && uv pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

2. Create Private Service for Qdrant:
   - Name: `qdrant-service`
   - Image: `docker.io/qdrant/qdrant:latest`
   - Port: 6333
   - Disk: Create persistent disk at `/qdrant/storage` (10GB minimum)

3. Add Environment Variables to Backend:
   - `QDRANT_HOST`: Use Render's internal service name (e.g., `qdrant-service`)
   - `QDRANT_PORT`: `6333`
   - `QDRANT_COLLECTION`: `essential_oils`
   - `MODEL_NAME`: `jinaai/jina-embeddings-v2-base-de`
   - `ALLOWED_ORIGINS`: `https://<your-vercel-domain>,https://localhost:5173`
   - `PERPLEXITY_API_KEY`: (add your key)
   - `LANGFUSE_PUBLIC_KEY`: (add your key)
   - `LANGFUSE_SECRET_KEY`: (add your key)
   - `LANGFUSE_HOST`: `https://cloud.langfuse.com`

### Post-Deployment

1. **Initialize Qdrant Collection**:
   - Run ingestion script to populate the vector database
   - You'll need to SSH into Render or run locally and sync data

2. **Update Frontend Environment**:
   - Set `VITE_API_URL` in Vercel to match your Render backend URL

3. **Test Endpoints**:
   ```bash
   curl https://doterra-backend.onrender.com/
   curl -X POST https://doterra-backend.onrender.com/search \
     -H "Content-Type: application/json" \
     -d '{"query": "relaxation", "limit": 5}'
   ```

---

## Environment Variables Reference

### Render Backend
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_HOST` | Yes | localhost | Qdrant server hostname |
| `QDRANT_PORT` | Yes | 6333 | Qdrant server port |
| `QDRANT_COLLECTION` | Yes | essential_oils | Qdrant collection name |
| `MODEL_NAME` | No | jinaai/jina-embeddings-v2-base-de | Embedding model name |
| `ALLOWED_ORIGINS` | No | localhost URLs | CORS allowed origins |
| `PERPLEXITY_API_KEY` | No | - | Perplexity AI API key |
| `LANGFUSE_PUBLIC_KEY` | No | - | Langfuse tracing key |
| `LANGFUSE_SECRET_KEY` | No | - | Langfuse secret key |

### Vercel Frontend
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | http://127.0.0.1:8000 | Backend API URL |

---

## Local Development

### Backend
```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 (frontend will proxy to backend at localhost:8000)

---

## Monitoring & Logs

- **Vercel**: Check logs in Dashboard → Project → Deployments
- **Render**: Check logs in Dashboard → Service → Logs tab

---

## Troubleshooting

### Backend won't start on Render
- Check Python version matches (3.12)
- Verify all dependencies in `requirements.txt` install successfully
- Check Qdrant service is running and accessible

### CORS errors
- Update `ALLOWED_ORIGINS` env var to include frontend URL
- Frontend URL should be HTTPS in production

### Model loading timeout
- The embedding model is ~500MB and may timeout on first load
- Set `SKIP_MODEL_LOAD=true` during Render build (will lazy-load on first request)
- Consider using a smaller model for production

