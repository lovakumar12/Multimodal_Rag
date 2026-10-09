# Scalable AWS Production Deployment & CI/CD Guide

This guide covers deploying the **Multimodal RAG Platform** on AWS in a highly scalable, fault-tolerant, and secure architecture using **AWS ECS Fargate**, **Amazon RDS PostgreSQL (pgvector)**, **Amazon S3**, **Application Load Balancer (ALB)**, and **GitHub Actions CI/CD**.

---

## 1. High-Level AWS Architecture

```
                                  Internet
                                     │
                                     ▼
                      [Application Load Balancer (ALB)]
                         Port 80 (HTTP) / 443 (HTTPS)
                                     │
                ┌────────────────────┴────────────────────┐
                │ Path: /*                                │ Path: /api/*, /docs, /health
                ▼                                         ▼
      [Frontend ECS Fargate]                    [Backend ECS Fargate]
     (React / Vite + Nginx)                     (FastAPI + Python 3.12)
    Auto-scales: 2-8 tasks                     Auto-scales: 2-10 tasks
                                                          │
                                ┌─────────────────────────┼─────────────────────────┐
                                ▼                         ▼                         ▼
                      [Amazon RDS PG 16]          [Amazon S3 Bucket]        [External LLMs]
                    PostgreSQL + pgvector       Documents, Assets, Pages     Gemini / OpenAI
                     Auto-scales to 100GB            Encrypted + CORS
```

### Key Architectural Strengths:
1. **Serverless Compute (ECS Fargate)**: No EC2 instances to patch or manage. Replicas scale up on traffic spikes and scale down during idle periods.
2. **Unified Single-Domain Routing**: The ALB handles path-based routing (`/api/*` to Backend, `/*` to Frontend). Eliminates cross-origin CORS issues in production.
3. **Multi-AZ High Availability**: Deployed across 2 Availability Zones with public and private subnets, NAT Gateway, and strict Security Groups.
4. **Persistent Multi-Modal Assets**: Uploaded documents, rendered page previews, extracted tables, and images are stored in Amazon S3 with presigned URLs.
5. **Zero-Downtime Rolling Updates**: GitHub Actions deploys new container versions using rolling task updates with health checks.

---

## 2. What Is Needed From You (Checklist)

Before deploying, ensure you have the following information and credentials ready:

### 2.1. AWS Account Credentials
Choose one of the two authentication methods for GitHub Actions:
- **Option A (Recommended: OIDC Role)**:
  - AWS IAM Role ARN configured for GitHub Actions OIDC (`arn:aws:iam::<ACCOUNT_ID>:role/GitHubActionsECSRole`).
- **Option B (Static IAM User Credentials)**:
  - `AWS_ACCESS_KEY_ID`: IAM user with permissions for ECS, ECR, S3, RDS, IAM, and CloudWatch.
  - `AWS_SECRET_ACCESS_KEY`: Secret access key for the above user.
  - `AWS_REGION`: Target AWS region (e.g., `us-east-1` or `us-west-2`).

### 2.2. API Keys
- `GEMINI_API_KEY`: Google AI Studio API key for Gemini multimodal vision & generation.
- (Optional) `GROQ_API_KEY`: Groq API key for chat generation when `LLM_PROVIDER=groq`.
- (Optional) `OPENAI_API_KEY`: OpenAI API key for chat generation when `LLM_PROVIDER=openai`.
- Set `LLM_MODEL` to a model supported by the selected provider. Groq and OpenAI GPT models require their respective API keys.

### 2.3. GitHub Repository Secrets
In your GitHub repository, navigate to **Settings > Secrets and variables > Actions** and add:

| Secret Name | Description | Example / Default |
|-------------|-------------|-------------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM Access Key (if using Option B) | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Secret Key (if using Option B) | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_ROLE_TO_ASSUME` | IAM Role ARN (if using Option A OIDC) | `arn:aws:iam::123456789012:role/github-actions-role` |
| `AWS_REGION` | Target AWS region (can also be a Repo Variable) | `us-east-1` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |

*(Optional Repository Variables under **Settings > Secrets and variables > Actions > Variables**)*:
- `ECS_CLUSTER`: `multimodal-rag-cluster-production`
- `ECS_SERVICE_BACKEND`: `multimodal-rag-backend`
- `ECS_SERVICE_FRONTEND`: `multimodal-rag-frontend`
- `ECR_REPOSITORY_BACKEND`: `multimodal-rag-backend`
- `ECR_REPOSITORY_FRONTEND`: `multimodal-rag-frontend`

---

## 3. Step 1: Provision Infrastructure with Terraform

The infrastructure is defined in [infrastructure/terraform/](file:///infrastructure/terraform).

### 3.1. Configure Variables
1. Navigate to the terraform directory:
   ```bash
   cd infrastructure/terraform
   ```
2. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
3. Edit `terraform.tfvars` with your secure database password and API keys:
   ```hcl
   aws_region     = "us-east-1"
   project_name   = "multimodal-rag"
   environment    = "production"
   db_name        = "multimodal_rag"
   db_username    = "ragadmin"
   db_password    = "YourVerySecurePassword123!"
   gemini_api_key = "your_gemini_api_key"
   ```

### 3.2. Initialize & Apply
Run:
```bash
terraform init
terraform plan
terraform apply -auto-approve
```

### 3.3. Outputs
Once completed, Terraform outputs:
- `alb_dns_name`: The live public web application URL! (e.g. `http://multimodal-rag-alb-12345.us-east-1.elb.amazonaws.com`)
- `backend_ecr_url`: The backend container registry.
- `frontend_ecr_url`: The frontend container registry.
- `s3_assets_bucket`: The created S3 assets bucket.
- `rds_endpoint`: PostgreSQL RDS endpoint.

---

## 4. Step 2: Automated CI/CD via GitHub Actions

The automated pipeline is defined in [.github/workflows/deploy.yml](file:///.github/workflows/deploy.yml).

### Workflow Pipeline Stages:
1. **Quality & Validation**:
   - Spawns an Ubuntu runner with Python 3.12 and Node.js 20.
   - Installs OCR packages (`tesseract-ocr`) and backend requirements.
   - Runs full unit and integration test suite (`pytest backend/tests`).
   - Runs frontend production build check (`npm ci && npm run build`).
2. **AWS ECR Build & Push**:
   - Authenticates with Amazon ECR.
   - Builds multi-stage production Docker images for Backend and Frontend.
   - Tags each image with both git commit SHA (`${{ github.sha }}`) and `:latest`.
   - Pushes images to Amazon ECR.
3. **Zero-Downtime ECS Rolling Deployment**:
   - Triggers `aws ecs update-service --force-new-deployment` on both backend and frontend Fargate services.
   - AWS ECS drains existing tasks and spawns new tasks with health check validation (`/health`).
   - Waits for services to stabilize before completing the workflow.

### Triggering Deployments:
- Simply push to the `main` branch:
  ```bash
  git add .
  git commit -m "Deploy latest changes"
  git push origin main
  ```
- Or trigger manually anytime via GitHub: **Actions > Production CI/CD Deployment to AWS ECS > Run workflow**.

---

## 5. Horizontal Scaling & Monitoring

### Auto-Scaling Policies
- **Backend Service**:
  - Automatically scales between **2 and 10 container tasks**.
  - Scales out if average CPU exceeds **70%** or Memory exceeds **80%**.
- **Frontend Service**:
  - Automatically scales between **2 and 8 container tasks**.
  - Scales out if average CPU exceeds **70%**.
- **Database (RDS)**:
  - Starts at 20GB gp3 storage and automatically expands up to **100GB** as document embeddings and extraction records grow.

### Health Endpoints
- **HTTP GET `/health`**: Returns application status (`{"status":"healthy"}`).
- **HTTP GET `/ready`**: Validates active PostgreSQL connection, vector index status, and S3 storage accessibility.
- **HTTP GET `/stats`**: Real-time stats on indexed documents, total visual assets, chunks, and vector count.

### CloudWatch Logs
- Backend container logs: `/ecs/multimodal-rag-backend-production`
- Frontend container logs: `/ecs/multimodal-rag-frontend-production`
