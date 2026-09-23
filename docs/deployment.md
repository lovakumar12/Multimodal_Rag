# Production Cloud Deployment Guide

This guide covers deploying the **Multimodal RAG Platform** using containerized infrastructure and managed cloud services (AWS, GCP, or Azure).

---

## 1. Cloud Architecture Overview

```
                      Internet
                         │
                         ▼
             [CloudFront / CDN / DNS]
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
[Vercel / S3 Web Hosting]     [Application Load Balancer]
     Frontend SPA                         │
                                          ▼
                             [AWS ECS / Fargate Tasks]
                                  Backend API Service
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
          [Amazon Aurora PG]         [Amazon ElastiCache]     [Amazon S3]
         PostgreSQL + pgvector           Redis Queue         Assets Storage
```

---

## 2. Infrastructure Components

### 2.1. Managed PostgreSQL with `pgvector`
- Recommended: **Amazon Aurora PostgreSQL** (v16+) or **Google Cloud SQL for PostgreSQL**.
- Enable vector extension:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- Configure connection string in environment:
  ```bash
  DATABASE_URL=postgresql+asyncpg://<user>:<password>@<db-host>:5432/<db_name>
  ```

### 2.2. Object Storage (Amazon S3)
- Create an S3 bucket: `multimodal-rag-production`.
- Enable CORS for your frontend domain:
  ```json
  [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
      "AllowedOrigins": ["https://your-frontend-domain.com"],
      "ExposeHeaders": ["ETag"]
    }
  ]
  ```
- Configure environment:
  ```bash
  STORAGE_BACKEND=s3
  OBJECT_STORAGE_BUCKET=multimodal-rag-production
  AWS_REGION=us-east-1
  ```

---

## 3. Containerized Backend Deployment (AWS ECS / Fargate)

1. **Build and Tag Image**:
   ```bash
   docker build -t multimodal-rag-backend:latest ./backend
   docker tag multimodal-rag-backend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/multimodal-rag-backend:latest
   ```

2. **Push to Amazon ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/multimodal-rag-backend:latest
   ```

3. **Task Definition Configuration**:
   - CPU: 2 vCPU
   - Memory: 4 GB
   - Container Port: `8000`
   - Health Check Path: `/health` (Interval: 30s, Timeout: 5s, Retries: 3)
   - Environment Variables:
     - `DATABASE_URL`
     - `GEMINI_API_KEY` or `OPENAI_API_KEY`
     - `ENVIRONMENT=production`
     - `LOG_LEVEL=INFO`

---

## 4. Frontend Deployment (Vercel / Cloudflare Pages)

1. Configure Build Settings:
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
2. Environment Variables:
   - `VITE_API_URL=https://api.yourdomain.com`

---

## 5. Local Production Stack via Docker Compose

To test the entire production topology locally:

```bash
# 1. Copy and configure environment variables
cp .env.example .env

# 2. Build and launch all services in detached mode
docker compose up --build -d

# 3. Verify health
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 4. Open Frontend in browser
http://localhost:3000
```
