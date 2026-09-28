# DEDAN Health API - Local Development Guide

## Prerequisites

- Python 3.11+
- uv (recommended) or pip
- Git
- At least one AI provider API key (Gemini, OpenAI, or Anthropic)

## Quick Start

### 1. Clone and Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or with uv (faster)
uv pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required:** At least one AI provider key:
- `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

### 3. Run Development Server

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main module
python -m app.main
```

Server starts at http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory & entry point
│   ├── core/
│   │   └── config.py        # Settings & environment config
│   ├── api/
│   │   └── analyze.py       # Main API endpoints
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   ├── services/
│   │   ├── ai_providers/    # AI provider implementations
│   │   │   ├── base.py      # Abstract base class
│   │   │   ├── factory.py   # Provider factory with fallback
│   │   │   ├── gemini_provider.py
│   │   │   ├── openai_provider.py
│   │   │   └── anthropic_provider.py (optional)
│   │   ├── image_service.py # Image upload & validation
│   │   ├── safety_validator.py  # Medical safety checks
│   │   └── response_transformer.py  # Response formatting
│   └── utils/
├── tests/
├── frontend-integration/    # TypeScript client & React hooks
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints

### Health & Info
- `GET /api/health` - System health check
- `GET /api/providers` - List configured AI providers
- `GET /` - Service info

### Image Upload
- `POST /api/images/upload` - Upload image file (multipart/form-data)
- `POST /api/images/upload-base64` - Upload base64 image
- `GET /api/images/{image_id}` - Get image metadata
- `GET /api/images/{image_id}/preview` - Get image as base64
- `DELETE /api/images/{image_id}` - Delete image

### Analysis
- `POST /api/analyze` - Main multi-modal analysis endpoint

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/api/health

# Text-only analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "patient_age": 25,
    "patient_sex": "female",
    "patient_location": "Kenya",
    "symptom_description": "High fever, chills, headache for 2 days. Recent mosquito bites.",
    "symptom_duration": "2 days",
    "symptom_severity": "moderate",
    "consent": true
  }'

# With image (upload first, then analyze)
# 1. Upload image
curl -X POST http://localhost:8000/api/images/upload \
  -F "file=@mosquito_bite.jpg" \
  -F "session_id=test_session"

# 2. Analyze with image_id
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "patient_age": 25,
    "patient_sex": "female",
    "patient_location": "Kenya",
    "symptom_description": "High fever, chills, headache for 2 days. Recent mosquito bites.",
    "image_ids": ["<image_id_from_upload>"],
    "consent": true
  }'
```

### Using the Swagger UI

Visit http://localhost:8000/docs for interactive API documentation.

## Frontend Integration

### Next.js Setup

1. Copy `frontend-integration/dedan-api.ts` and `frontend-integration/dedan-hooks.ts` to your Next.js project (e.g., `lib/` folder)

2. Set environment variable:
```bash
# .env.local
NEXT_PUBLIC_DEDAN_API_URL=http://localhost:8000
NEXT_PUBLIC_DEDAN_API_KEY=your_api_key_if_needed
```

3. Use in components:
```tsx
import { useTriageFlow, useUrgencyDisplay } from '@/lib/dedan-hooks';

export default function TriagePage() {
  const { state, actions, result, loading, error } = useTriageFlow();
  const urgencyDisplay = useUrgencyDisplay(result);

  return (
    <div>
      {/* Form steps based on state.step */}
      {state.step === 'results' && urgencyDisplay && (
        <div className={`p-4 rounded-lg border ${urgencyDisplay.color}`}>
          <h2>{urgencyDisplay.icon} {urgencyDisplay.label}</h2>
          <p>{urgencyDisplay.description}</p>
          <p>{urgencyDisplay.reasoning}</p>
        </div>
      )}
    </div>
  );
}
```

## Development Tips

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_analyze.py -v
```

### Code Quality

```bash
# Format
black app/
isort app/

# Lint
ruff app/
mypy app/
```

### Adding a New AI Provider

1. Create `app/services/ai_providers/your_provider.py` extending `AIProvider`
2. Implement required methods: `analyze()`, `health_check()`, properties
3. Register in `app/services/ai_providers/factory.py`
4. Add config to `app/core/config.py` and `.env.example`

### Debugging

- Check logs: `tail -f logs/app.log` (if configured)
- Use `/api/providers` to verify AI provider status
- Enable DEBUG in `.env` for verbose logging

## Common Issues

### "No AI providers available"
- Check `.env` has valid API keys
- Check provider health: `curl http://localhost:8000/api/providers`

### "Image validation failed"
- Ensure image is JPEG, PNG, WebP, or HEIC
- Max size: 10MB (configurable)
- Min dimensions: 224x224

### CORS errors
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Restart server after changes

### Rate limiting
- Default: 30 requests/minute per IP
- Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` in `.env`

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes* | - | Google Gemini API key |
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `DEFAULT_AI_PROVIDER` | No | gemini | Primary provider |
| `CORS_ORIGINS` | No | localhost:3000 | Allowed origins |
| `MAX_IMAGE_SIZE_MB` | No | 10 | Max upload size |
| `RATE_LIMIT_REQUESTS` | No | 30 | Requests per minute |
| `DEBUG` | No | false | Debug mode |

*At least one AI provider key required.

## Next Steps

1. **Add authentication** - JWT/OAuth for production
2. **Add database** - PostgreSQL for persistent storage
3. **Add caching** - Redis for rate limiting & sessions
4. **Add monitoring** - Prometheus/Grafana, Sentry
5. **Deploy** - See DEPLOYMENT.md