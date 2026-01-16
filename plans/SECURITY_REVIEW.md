# Security Review - doTERRA Essential Oils Recommendations

**Date:** January 16, 2026
**Reviewer:** Security Engineer
**Status:** In Progress

## Executive Summary

This is a development/prototype doTERRA essential oils recommendation system using FastAPI, Qdrant vector database, and sentence-transformers for semantic search. Several security issues were identified that should be addressed before production deployment.

---

## Critical Issues

### 1. Overly Permissive CORS Configuration
**Location:** `backend/main.py:75`
**Severity:** Critical
```python
allow_origins=["*"],  # For dev
```
**Risk:** Allows any origin to access the API, enabling cross-origin attacks, data theft, and CSRF.
**Recommendation:** Restrict to specific origins in production:
```python
allow_origins=["https://yourdomain.com"],  # Production only
```
**Status:** Quick win - TODO

### 2. No Input Validation on Search Queries
**Location:** `backend/main.py:84-86`
**Severity:** Critical
```python
class SearchRequest(BaseModel):
    query: str  # No length limits
```
**Risk:** Unbounded input can lead to:
- Memory exhaustion via extremely long queries
- Potential vectorization performance degradation
- Prompt injection-style attacks against LLM pipelines
**Recommendation:** Add Pydantic field constraints:
```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
```
**Status:** Quick win - TODO

### 3. No API Rate Limiting
**Location:** `backend/main.py`
**Severity:** High
**Risk:** No protection against:
- Denial of Service (DoS) attacks
- Automated scraping
- Resource exhaustion
**Recommendation:** Implement rate limiting using `fastapi-limiter`:
```python
from fastapi_limiter import Limiter
from fastapi_limiter.depends import RateLimiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/search", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
```
**Status:** Deferred - Requires additional dependency

### 4. No Authentication/Authorization
**Location:** `backend/main.py`
**Severity:** Critical
**Risk:** All endpoints (`/search`, `/recommend`, `/random`) are publicly accessible without authentication.
**Recommendation:** Add authentication middleware (OAuth2, JWT, or API key) if this API should be restricted.
**Status:** Deferred - Requires design decision

---

## High Priority Issues

### 5. `trust_remote_code=True` in Model Loading
**Location:** `backend/main.py:39`, `processing/ingest_to_qdrant.py:73`
**Severity:** High
```python
model = SentenceTransformer(MODEL_NAME, device=device, trust_remote_code=True)
```
**Risk:** Executes arbitrary Python code from the model repository. Only safe if you fully trust the model source.
**Recommendation:**
1. Pin model to specific version with known checksum
2. Verify model source integrity before loading
3. Consider using a local model cache with signature verification
**Status:** Deferred - Requires model verification

### 6. Missing Request Size Limits
**Location:** `backend/main.py`
**Severity:** High
**Risk:** No limits on request body sizes can lead to memory exhaustion.
**Recommendation:** Configure uvicorn with body limits:
```python
uvicorn.run(app, limit_max_requests=1000, limit_max_keepalive_connections=100)
```
Or add middleware for request size validation.
**Status:** Deferred

### 7. Hardcoded API URL in Frontend
**Location:** `frontend/src/api.ts:4`
**Severity:** High
```python
const API_URL = 'http://127.0.0.1:8000';
```
**Risk:** Not configurable for different environments (dev/staging/prod).
**Recommendation:** Use environment variables:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
```
**Status:** Quick win - TODO

---

## Medium Priority Issues

### 8. No Security Headers
**Location:** `backend/main.py`
**Severity:** Medium
**Risk:** Missing headers like HSTS, X-Frame-Options, X-Content-Type-Options.
**Recommendation:** Add security headers middleware:
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
```
**Status:** Deferred

### 9. Verbose Error Messages
**Location:** `backend/main.py:138-139`
**Severity:** Medium
```python
except Exception as e:
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Qdrant search failed: {str(e)}")
```
**Risk:** Detailed error traces can leak internal system information (paths, database structures, etc.).
**Recommendation:** Log errors internally, return generic messages to clients:
```python
except Exception as e:
    logger.error(f"Qdrant search failed: {type(e).__name__}")
    raise HTTPException(status_code=500, detail="Internal server error")
```
**Status:** Quick win - TODO

### 10. No Input Sanitization on User IDs
**Location:** `backend/main.py:90`
**Severity:** Medium
```python
positive: list[int]  # Direct use in database queries
```
**Risk:** If IDs are user-controlled without validation, could lead to unexpected behavior or injection attacks.
**Recommendation:** Validate that IDs exist and are within expected ranges before querying.
**Status:** Deferred

---

## Quick Wins Implemented

| Item | Description | Status |
|------|-------------|--------|
| 1 | `.env.example` template created | DONE |
| 2 | Pydantic field constraints added | DONE |
| 3 | CORS configured for production | DONE |
| 4 | Frontend API URL uses environment variables | DONE |
| 5 | Production deployment checklist created | DONE |

---

## Dependency Security

### Python Dependencies
Current Python dependencies appear reasonably up-to-date. Run periodic audits:
```bash
uvx pip-audit
```

### Frontend Dependencies
Run npm audit for frontend:
```bash
cd frontend && npm audit
```

---

## Recommendations Summary

### Immediate (Before Production)
- [ ] Restrict CORS origins
- [ ] Add input validation to request models
- [ ] Create `.env.example` template
- [ ] Configure frontend to use environment variables
- [ ] Add production deployment checklist

### Short-Term (Sprint 1)
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Configure security headers
- [ ] Improve error handling (generic messages)

### Medium-Term (Sprint 2)
- [ ] Verify and pin model versions
- [ ] Add request size limits
- [ ] Implement input sanitization for IDs
- [ ] Add security scanning to CI/CD

---

## Security Checklist for Production

- [ ] CORS restricted to production origins
- [ ] Input validation on all endpoints
- [ ] Rate limiting enabled
- [ ] Authentication configured
- [ ] Environment variables documented (`.env.example`)
- [ ] No hardcoded secrets in code
- [ ] Dependencies audited for vulnerabilities
- [ ] Security headers configured
- [ ] Error messages sanitized
- [ ] HTTPS enforced
- [ ] Logging configured (without sensitive data)
- [ ] Model sources verified
- [ ] Request size limits configured
- [ ] Frontend uses environment-based API URL

---

## References

- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validation/)

---

## Production Deployment Checklist

### Pre-Deployment Security Review

#### Environment Configuration
- [ ] Create `.env` from `.env.example` with production values
- [ ] Set `ALLOWED_ORIGINS` to production frontend domain(s)
- [ ] Set `ENVIRONMENT=production`
- [ ] Ensure no default passwords or secrets remain
- [ ] Rotate any test credentials

#### Infrastructure Security
- [ ] Deploy behind a reverse proxy (nginx, Traefik, or cloud load balancer)
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Configure HSTS headers
- [ ] Set up rate limiting at infrastructure level (nginx, cloud WAF)
- [ ] Configure proper firewall rules
- [ ] Ensure Qdrant is not exposed publicly
- [ ] Use private networks for internal service communication

#### Application Security
- [ ] CORS origins restricted to production domains
- [ ] All endpoints have input validation
- [ ] No debug mode enabled
- [ ] Error messages do not leak stack traces
- [ ] Logging configured without sensitive data
- [ ] Request size limits configured
- [ ] Health check endpoints secured

#### Dependencies
- [ ] Run `uvx pip-audit` and fix high/critical vulnerabilities
- [ ] Run `cd frontend && npm audit` and fix high/critical vulnerabilities
- [ ] Pin all dependency versions in `pyproject.toml`
- [ ] Review model sources and verify integrity

#### Docker Security
- [ ] Run container as non-root user
- [ ] Add health checks to Dockerfile
- [ ] Scan Docker images for vulnerabilities
- [ ] Use specific version tags, not `latest`

### Deployment Steps

```bash
# 1. Create production environment file
cp .env.example .env
# Edit .env with production values

# 2. Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify deployment
curl -I https://yourdomain.com/health

# 4. Check logs for errors
docker-compose logs -f
```

### Post-Deployment Verification

- [ ] API endpoints respond correctly
- [ ] CORS properly enforced (test with curl from different origin)
- [ ] Rate limiting active
- [ ] No sensitive data in logs
- [ ] Health checks passing
- [ ] Monitoring/alerts configured
- [ ] Backup strategy verified

### Rollback Plan

If issues are detected:
```bash
# Quick rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml -f docker-compose.override.yml up -d
```

### Monitoring and Alerting

- [ ] Set up uptime monitoring
- [ ] Configure error rate alerts
- [ ] Monitor resource usage (CPU, memory, disk)
- [ ] Log aggregation configured
- [ ] Security event logging enabled

