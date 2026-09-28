# DEDAN Health API - Production Deployment Guide

## Overview

This guide covers production deployment options for the DEDAN Health API with emphasis on security, scalability, and medical data compliance.

## Architecture Options

### Option 1: Vercel + Railway (Recommended for MVP)
- **Frontend**: Vercel (Next.js)
- **Backend**: Railway (FastAPI)
- **Database**: Railway PostgreSQL
- **Cache**: Railway Redis
- **Cost**: ~$20-50/month for moderate traffic

### Option 2: AWS (Production Scale)
- **Frontend**: Vercel or AWS Amplify
- **Backend**: ECS Fargate or EKS
- **Database**: RDS PostgreSQL (Multi-AZ)
- **Cache**: ElastiCache Redis
- **Storage**: S3 for images
- **CDN**: CloudFront
- **Monitoring**: CloudWatch, X-Ray

### Option 3: Google Cloud
- **Frontend**: Firebase Hosting or Cloud Run
- **Backend**: Cloud Run
- **Database**: Cloud SQL PostgreSQL
- **Cache**: Memorystore Redis
- **Storage**: Cloud Storage

### Option 4: Self-Hosted / VPS
- **Server**: Ubuntu 22.04+ on DigitalOcean, Linode, Hetzner
- **Reverse Proxy**: Nginx + Certbot (SSL)
- **Process Manager**: systemd + gunicorn
- **Database**: PostgreSQL
- **Cache**: Redis

## Security Checklist (Medical Data)

### ✅ Mandatory for Production

1. **HTTPS/TLS Everywhere**
   - Use valid TLS certificates (Let's Encrypt or paid)
   - HSTS headers
   - Secure cookies only

2. **Authentication & Authorization**
   - JWT tokens with short expiry (15-30 min)
   - Refresh token rotation
   - Role-based access (patient, clinician, admin)
   - API key for service-to-service

3. **Data Encryption**
   - At rest: AES-256 (database, file storage)
   - In transit: TLS 1.3
   - Field-level encryption for PII

4. **Input Validation & Sanitization**
   - Strict Pydantic models (already implemented)
   - File type validation (magic bytes + extension)
   - Size limits enforced
   - No direct file serving from upload directory

5. **Audit Logging**
   - All analysis requests logged (no PII in logs)
   - Access logs for 1+ years
   - Immutable log storage

6. **Rate Limiting & DDoS Protection**
   - Per-IP and per-user limits
   - WAF rules (AWS WAF, Cloudflare)
   - Circuit breakers

7. **Medical Compliance**
   - HIPAA (if US patients)
   - GDPR (if EU patients)
   - Local regulations (Kenya Data Protection Act, etc.)
   - Data Processing Agreements with subprocessors
   - Right to deletion implementation

## Deployment: Railway (Quick Start)

### 1. Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli
railway login
railway init
```

### 2. Add Services

```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis
```

### 3. Configure Environment Variables

In Railway dashboard, add:

```env
# App
ENVIRONMENT=production
DEBUG=false
APP_NAME=DEDAN Health API
APP_VERSION=1.0.0

# Database (auto-provided by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (auto-provided)
REDIS_URL=${{Redis.REDIS_URL}}

# AI Providers
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
DEFAULT_AI_PROVIDER=gemini

# Security
ADMIN_API_KEY=generate_strong_random_key
SECRET_KEY=generate_strong_random_key

# CORS - Your Vercel frontend URL
CORS_ORIGINS=["https://your-app.vercel.app"]

# Rate limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# Image storage (use S3 in production)
IMAGE_STORAGE_PATH=/app/data/images
IMAGE_TTL_HOURS=24
```

### 4. Deploy

```bash
# Create railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4"
healthcheckPath = "/api/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
EOF

railway up
```

### 5. Custom Domain

```bash
railway domain your-api.yourdomain.com
```

## Deployment: AWS ECS Fargate (Production)

### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### 2. ECS Task Definition (JSON)

```json
{
  "family": "dedan-health-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/dedanTaskRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/dedan-health-api:latest",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."},
        {"name": "GEMINI_API_KEY", "value": "from_secrets_manager"},
        {"name": "CORS_ORIGINS", "value": "[\"https://app.yourdomain.com\"]"}
      ],
      "secrets": [
        {"name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:dedan/gemini-key"},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:dedan/openai-key"},
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:dedan/secret-key"},
        {"name": "ADMIN_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:dedan/admin-key"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dedan-health-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### 3. Infrastructure (Terraform Example)

```hcl
# main.tf
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  name    = "dedan-vpc"
  cidr_block = "10.0.0.0/16"
  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = false
}

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"
  identifier = "dedan-db"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  max_allocated_storage = 500
  storage_encrypted    = true
  db_name              = "dedan"
  username             = "dedanadmin"
  password             = var.db_password
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.private_subnets
  backup_retention_period = 7
  deletion_protection  = true
  performance_insights_enabled = true
}

module "elasticache" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 3.0"
  cluster_id           = "dedan-cache"
  engine               = "redis"
  node_type            = "cache.t3.medium"
  num_cache_nodes      = 2
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.private_subnets
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token           = var.redis_auth_token
}

module "ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 5.0"
  cluster_name = "dedan-cluster"
  # ... service configuration
}

module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"
  name = "dedan-alb"
  load_balancer_type = "application"
  vpc_id = module.vpc.vpc_id
  subnets = module.vpc.public_subnets
  security_groups = [module.alb_sg.id]
  # HTTPS listener with ACM certificate
  https_listeners = [{
    port            = 443
    protocol        = "HTTPS"
    certificate_arn = var.acm_cert_arn
    target_group_index = 0
  }]
}
```

## Image Storage: S3 (Production)

### 1. Update Image Service for S3

```python
# app/services/image_service.py - add S3 support
import boto3
from botocore.exceptions import ClientError

class S3ImageStorage:
    def __init__(self, bucket: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.s3 = boto3.client('s3', region_name=region)
    
    async def store(self, image_id: str, content: bytes, mime_type: str) -> str:
        key = f"images/{image_id[:2]}/{image_id}"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=mime_type,
            ServerSideEncryption='AES256',
        )
        return f"s3://{self.bucket}/{key}"
    
    async def get(self, image_id: str) -> bytes:
        key = f"images/{image_id[:2]}/{image_id}"
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()
    
    async def delete(self, image_id: str):
        key = f"images/{image_id[:2]}/{image_id}"
        self.s3.delete_object(Bucket=self.bucket, Key=key)
    
    async def generate_presigned_url(self, image_id: str, expiry: int = 3600) -> str:
        key = f"images/{image_id[:2]}/{image_id}"
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expiry
        )
```

### 2. S3 Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAppAccess",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::ACCOUNT:role/dedanTaskRole"},
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::dedan-health-images/*"
    }
  ]
}
```

## Frontend Deployment: Vercel

### 1. vercel.json

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_DEDAN_API_URL": "@dedan-api-url",
    "NEXT_PUBLIC_DEDAN_API_KEY": "@dedan-api-key"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {"key": "X-Content-Type-Options", "value": "nosniff"},
        {"key": "X-Frame-Options", "value": "DENY"},
        {"key": "X-XSS-Protection", "value": "1; mode=block"},
        {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"}
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/analyze/:path*",
      "destination": "https://your-api.railway.app/api/analyze/:path*"
    }
  ]
}
```

### 2. Environment Variables in Vercel

```
NEXT_PUBLIC_DEDAN_API_URL=https://your-api.railway.app
NEXT_PUBLIC_DEDAN_API_KEY=your_frontend_api_key
```

## Monitoring & Observability

### 1. Health Checks
- `/api/health` - Full system health
- `/api/providers` - AI provider status
- Kubernetes/ECS liveness & readiness probes

### 2. Metrics (Prometheus)
```python
# Add to app/main.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency', ['method', 'endpoint'])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(time.time() - start)
    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### 3. Error Tracking (Sentry)
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production",
)
```

### 4. Logging (Structured)
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: dedan-health-api
  ECS_SERVICE: dedan-health-api
  ECS_CLUSTER: dedan-cluster

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-fail-under=80

  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.build-image.outputs.image }}
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment \
            --region $AWS_REGION
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE \
            --region $AWS_REGION
```

## Disaster Recovery

### Backup Strategy
- **Database**: Automated daily snapshots (RDS) + point-in-time recovery
- **Redis**: AOF persistence + replica
- **Images**: S3 versioning + cross-region replication
- **Secrets**: AWS Secrets Manager automatic rotation

### RTO/RPO Targets
- **RTO (Recovery Time Objective)**: < 30 minutes
- **RPO (Recovery Point Objective)**: < 5 minutes

### Runbook
1. Health check fails → Auto-restart (ECS/Healthcheck)
2. Region failure → Failover to secondary region (Route53 health checks)
3. Data corruption → Point-in-time restore from RDS
4. Complete outage → Deploy from latest Docker image to new region

## Cost Optimization

### Development
- Railway: ~$5-10/month
- Use Gemini Flash for cheaper analysis

### Production
- ECS Fargate Spot: 60-70% savings
- RDS Reserved Instances: 30-60% savings
- S3 Intelligent Tiering for images
- CloudFront caching for repeated analyses

## Compliance Documentation

Maintain these for audits:
- [ ] Data Flow Diagram
- [ ] Risk Assessment
- [ ] Business Associate Agreements (BAAs)
- [ ] Incident Response Plan
- [ ] Data Retention Policy
- [ ] Privacy Policy (user-facing)
- [ ] Terms of Service
- [ ] Penetration Test Results (annual)
- [ ] SOC 2 Type II Report (if applicable)

## Support & Escalation

| Severity | Response Time | Contact |
|----------|--------------|---------|
| Critical (API down) | 15 min | PagerDuty → On-call |
| High (AI providers failing) | 1 hour | Slack #alerts → Team |
| Medium (Performance) | 4 hours | Ticket → Sprint |
| Low (Feature request) | Next sprint | GitHub Issues |

---

**Last Updated**: 2026
**Version**: 1.0
**Maintainer**: DEDAN Health Engineering Team