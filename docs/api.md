# API Reference

Base URL in local development: `http://localhost:8001`

Interactive documentation is served at `/docs` when `DEBUG=true`. When
`DEBUG=false`, `/docs`, `/redoc`, and `/openapi.json` are disabled.

All schemas below are taken from the implementation in `backend-v2/`, and the
example responses are real captures from the offline provider.

## Authentication

> ⛔ **None. This is a production blocker.** Verified by inspection:
> `main_clinical.py` defines no `APIKeyHeader`, no `OAuth2PasswordBearer`, and no
> auth dependency. `ADMIN_API_KEY` is read from settings but used only as the
> `SessionMiddleware` signing secret — it authenticates nothing. Every endpoint
> below is reachable by anyone who can reach the network path. Do not expose
> this service to an untrusted network. See [security.md](security.md).

No endpoint requires or accepts credentials. This is a deliberate, documented
limitation of a prototype — not an oversight in the documentation. What would
be required before any exposure is described in [security.md](security.md).

The only user-facing gate is the `consent` field on `POST /api/analyze`, which
is a request-scoped assertion, not an authenticated authorization.

## Error Envelope

Every error response uses one shape:

```json
{
  "error": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "details": [],
  "timestamp": 1750000000.0
}
```

| Field | Type | Description |
| --- | --- | --- |
| `error` | string | Human-readable message |
| `error_code` | string | Stable machine-readable code |
| `details` | array / object / null | Structured context; `null` when not applicable |
| `timestamp` | float | Unix timestamp of the response |

| Status | `error_code` | When |
| --- | --- | --- |
| `400` | `HTTP_400` | Consent withheld, or image rejected by validation |
| `404` | `HTTP_404` | Unknown image ID |
| `422` | `VALIDATION_ERROR` | Request body failed Pydantic validation |
| `429` | `RATE_LIMIT_EXCEEDED` | Per-IP request limit exceeded |
| `500` | `HTTP_500` | Unhandled error in image handling or analysis |
| `503` | `HTTP_503` | AI providers not initialised (startup failure) |
| `500` | `INTERNAL_ERROR` | Unhandled exception; details only when `DEBUG=true` |

Stack traces are never returned to clients.

## `GET /`

Service metadata.

**Response `200`**

```json
{
  "service": "DEDAN Health Clinical API",
  "version": "1.0.0",
  "status": "operational"
}
```

## `GET /api/health`

Structured health check. Exempt from rate limiting.

**Response `200`** (schema: `HealthCheckResponse`)

```json
{
  "status": "healthy",
  "timestamp": "2026-09-28T09:33:31.139447",
  "version": "1.0.0",
  "components": {
    "api": "operational",
    "image_service": "operational",
    "safety_validator": "operational"
  },
  "ai_providers": {}
}
```

Note: `ai_providers` is currently always an empty object. Provider health is not
yet surfaced here.

## `GET /health`

Legacy alias returning a minimal body, kept stable for probes and load
balancers.

```json
{ "status": "healthy", "service": "DEDAN Health Clinical API" }
```

## `GET /api/providers`

Provider registry.

```json
{ "providers": [], "primary": "gemini", "fallback_order": [] }
```

**Known limitation:** the `providers` and `fallback_order` lists are currently
returned empty regardless of the active mode. The route exists and is
reachable, but does not yet report the resolved provider set.

## `POST /api/analyze`

The primary endpoint. Accepts a patient-described problem plus clinical
context and returns a structured clinical document.

### Request

Schema: `AnalyzeRequest` (`backend-v2/models/models.py`).

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `patient_age` | integer | **Yes** | `0 ≤ age ≤ 150` |
| `patient_sex` | string | **Yes** | `male` \| `female` \| `other` |
| `symptom_description` | string | **Yes** | 10–3000 characters |
| `consent` | boolean | No (default `true`) | Must be `true` |
| `patient_location` | string | No | Used for localised emergency numbers |
| `patient_pregnant` | boolean | No | Default `false` |
| `patient_chronic_conditions` | string[] | No | Default `[]` |
| `patient_medications` | string[] | No | Default `[]` |
| `patient_allergies` | string[] | No | Default `[]` |
| `patient_language` | string | No | Default `en` |
| `symptom_duration` | string | No | Free text |
| `symptom_severity` | string | No | `mild` \| `moderate` \| `severe` |
| `image_ids` | string[] | No | IDs from a prior upload |
| `image_data_list` | string[] | No | Raw base64 or `data:` URLs |
| `voice_transcript` | string | No | Pre-transcribed speech |
| `session_id` | string | No | Generated if omitted |
| `conversation_history` | object[] | No | `{role, content}` turns |

**Example request**

```bash
curl -X POST http://localhost:8001/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "patient_age": 30,
    "patient_sex": "female",
    "symptom_description": "mild headache for two days",
    "symptom_duration": "2 days",
    "symptom_severity": "mild",
    "consent": true
  }'
```

### Response

**Important:** although an `AnalyzeResponse` model exists, this route is declared
`response_model=dict` and returns `ClinicalResponse.to_dict()`. The response
below is the real shape, captured from the offline provider.

Top-level keys: `response_id`, `session_id`, `timestamp`, `health_summary`,
`safety`, `possible_explanations`, `uncertainty`, `treatment_education`,
`medication_information`, `medication_verification`, `visual_education`,
`warning_signs`, `follow_up`, `next_steps`, `professional_review`,
`professional_review_reason`, `sources`, `provider`, `model`,
`confidence_score`, `disclaimer`, `uncertainty`, `safety_flags`.

```json
{
  "response_id": "ddafadca-46ec-444e-8052-5c359b398184",
  "session_id": "333d5277-896f-47de-a6f4-799b7813b5e8",
  "timestamp": "2026-09-28T09:33:31.139447",
  "health_summary": {
    "symptoms": ["mild headache for two days"],
    "duration": "2 days",
    "severity": 3,
    "relevant_history": [],
    "images_provided": false,
    "other_information": { "ai_confidence": 0.55, "processing_time_ms": 2 }
  },
  "safety": {
    "urgency": "routine",
    "red_flags": ["low_confidence:0.55", "inadequate_disclaimer"],
    "requires_immediate_care": false,
    "emergency_message": null,
    "recommended_action": "Schedule a routine appointment with a clinician, or use self-care and re-check if symptoms worsen.",
    "professional_review_required": true
  },
  "possible_explanations": [
    {
      "label": "Undetermined - requires professional evaluation",
      "why_it_fits": "Insufficient information to suggest specific conditions",
      "what_does_not_fit": "No specific findings to support a diagnosis",
      "evidence_level": "theoretical",
      "requires_more_info": ["Physical examination", "Laboratory tests", "Detailed history"]
    }
  ],
  "uncertainty": {
    "message": "Deterministic rules-based assessment; no probabilistic model was consulted.",
    "level": "moderate",
    "missing_information": ["Temperature", "Duration of specific symptoms", "Past medical history"]
  },
  "disclaimer": "This is AI-generated health information, not a diagnosis. Always consult a qualified healthcare professional.",
  "confidence_score": 0.55,
  "provider": "offline",
  "model": "offline-rules-v1"
}
```

### Urgency levels

`routine` · `soon` · `urgent` · `emergency`

Urgency is **never downgraded** by a later pipeline stage. See
[safety.md](security.md).

### Safety considerations

- `consent` must be `true`; `false` returns `400` before any AI processing.
- `safety.requires_immediate_care` and `safety.emergency_message` must be
  surfaced prominently by any client. They indicate that emergency care is
  advised.
- `professional_review_required` is `true` by default.
- `medication_information[].is_educational_only` is always `true`. Clients must
  not present this content as a prescription.
- Symptom text is health data. Do not log request bodies.

## Image Endpoints

### `POST /api/images/upload`

Multipart upload. Field name: `file`. Optional form field: `session_id`.

```bash
curl -X POST http://localhost:8001/api/images/upload \
  -F 'file=@photo.png' \
  -F 'session_id=session-123'
```

**Response `200`** (schema: `ImageUploadResponse`)

```json
{
  "image_id": "0f8c...",
  "filename": "photo.png",
  "size_bytes": 184320,
  "mime_type": "image/png",
  "quality_score": 1.0,
  "is_usable": true,
  "upload_timestamp": "2026-09-28T09:33:31.139447",
  "preview_url": "/api/images/0f8c.../preview"
}
```

**Validation performed before storage** (`image_service.py`):

| Check | Rule | Result on failure |
| --- | --- | --- |
| MIME type | Detected from **magic bytes**, not the client's header | `400` |
| Allowed types | `image/jpeg`, `image/png`, `image/webp`, `image/heic` | `400` |
| File size | ≤ 10 MB (`MAX_IMAGE_SIZE_MB`) | `400` |
| Dimensions | ≥ 224×224 | `400` |
| File size floor | ≥ 1 KiB (corruption check) | `400` |
| Filename | Sanitised to `[A-Za-z0-9._-]`, truncated to 100 chars | Sanitised |

Dimension, aspect-ratio, and file-size floors are **quality gates**, not
security boundaries — an image that fails them is rejected because the analysis
would be unreliable, not because it is hostile.

### `POST /api/images/upload-base64`

```json
{
  "image_data": "<base64 or data:image/png;base64,...>",
  "filename": "image.jpg",
  "session_id": "session-123"
}
```

Returns the same `ImageUploadResponse`. `data:` URL prefixes are parsed to
detect the MIME type. A missing `image_data` returns `400`.

### `GET /api/images/{image_id}`

Returns stored metadata. `404` if unknown.

### `GET /api/images/{image_id}/preview`

Returns `{image_id, content, mime_type}` where `content` is base64. `404` if
unknown.

### `DELETE /api/images/{image_id}`

Returns `{message, image_id}` and removes both the file and the metadata entry.
`404` if unknown.

### Retention

Uploaded images expire after `IMAGE_TTL_HOURS` (default 24). A background task
runs hourly via `periodic_cleanup()`. Expiry is **in-process**: restarting the
API loses the metadata index, and orphan files are not reclaimed on startup.

## Rate Limiting

Per client IP, default 30 requests per 60 seconds (`RATE_LIMIT_REQUESTS`,
`RATE_LIMIT_WINDOW`). Exempt paths: `/api/health`, `/health`, `/docs`, `/redoc`,
`/openapi.json`. Exceeding the limit returns `429`.

**Limitation:** the counter is a process-local dictionary, so limits reset on
restart and do not apply across replicas. `X-Forwarded-For` is trusted without
validation, which is only correct behind a proxy that overwrites it.


