# HuggingFace Spaces Deployment Guide

## Setup Instructions

### 1. Create Space
The space has been created at: `Aaron-test/doTERRA_essential_oil_recos_backend`

### 2. Repository Setup
Clone the space repo:
```bash
git clone https://huggingface.co/spaces/Aaron-test/doTERRA_essential_oil_recos_backend
cd doTERRA_essential_oil_recos_backend
```

### 3. Add GitHub Remote
```bash
git remote add github https://github.com/aaronspring/doTERRA_essential_oils_recos.git
git fetch github main
git merge github/main
git push
```

### 4. Configure Environment Variables
In the HF Spaces UI:
1. Go to **Settings** → **Repository secrets**
2. Add the following variables from your `.env` file:
   - `QDRANT_HOST`
   - `QDRANT_PORT`
   - `QDRANT_API_KEY`
   - `QDRANT_COLLECTION`
   - `MODEL_NAME`
   - `PERPLEXITY_API_KEY`
   - `OPENAI_API_KEY` (if using)
   - `LANGFUSE_PUBLIC_KEY` (if using)
   - `LANGFUSE_SECRET_KEY` (if using)
   - `LANGFUSE_HOST` (if using)
   - `ALLOWED_ORIGINS` (update with your frontend URL)

### 5. Build & Deploy
- Space will auto-build from Dockerfile
- Status visible in Logs tab
- App runs on port 7860 (HF standard)

## Dockerfile Details
- **Python**: 3.11-slim (balance of size & compatibility)
- **Entry Point**: `backend.main:app` on port 7860
- **Layer Optimization**: 
  - Requirements copied first for better caching
  - Slim image reduces build time & storage

## Troubleshooting

### Build Failures
1. Check **Logs** tab for errors
2. Common issues:
   - Missing `requirements.txt`
   - Incompatible Python version (use 3.11+)
   - Missing environment variables

### Runtime Issues
- **Model Loading Slow**: First request triggers model download (~500MB for Jina)
- **Qdrant Connection**: Verify `QDRANT_HOST` & `QDRANT_API_KEY` are correct
- **CORS Issues**: Add frontend URL to `ALLOWED_ORIGINS`

### Memory Constraints
- Free tier: ~16GB RAM
- Jina embeddings model: ~500MB
- Consider `SKIP_MODEL_LOAD=true` for cold starts if needed

## Sync with GitHub

### Automatic Sync (GitHub Actions)
The project is configured with a GitHub Actions workflow that automatically pushes `main` branch to HF Spaces on every commit.

**Setup Required:**
1. Go to GitHub repo Settings → Secrets and variables → Actions
2. Add `HF_TOKEN` secret:
   - Get token from [HuggingFace Settings](https://huggingface.co/settings/tokens)
   - Create a token with `write` access to spaces
   - Add as `HF_TOKEN` secret in GitHub

Once configured, every push to `main` will automatically deploy to HF Spaces.

### Manual Sync
To manually pull latest changes from GitHub:
```bash
git fetch github main
git merge github/main
git push
```

## API Endpoint
Once deployed, access at:
```
https://Aaron-test-doTERRA-essential-oil-recos-backend.hf.space
```

Health check:
```bash
curl https://Aaron-test-doTERRA-essential-oil-recos-backend.hf.space/
```
