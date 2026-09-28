# Multimodal Frontend Integration — Verified Backend Contract

## Verified Backend Endpoints

All endpoints below are verified by reading source code in `backend-v2/main_v2.py` and `backend-v2/providers/`.

### 1. Image Upload
```
POST /dedan/v2/images/upload
Content-Type: multipart/form-data
```
- Field: `file` (UploadFile, required)
- Field: `session_id` (Form, optional)
- Supported MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/heic`, `image/heif`
- Max file size: 20 MB
- Returns: `ImageUploadResponse` with `image_id`, `filename`, `size`, `mime_type`, `quality_score`, `is_usable`, `upload_timestamp`

### 2. Multimodal Analysis
```
POST /dedan/v2/multimodal-analyze
Content-Type: application/json
```
- Accepts: `text`, `voice_transcript` (pre-transcribed text, NOT raw audio), `image_ids`, `image_data_list` (base64), `patient`, `session_id`, `conversation_history`, `consent`
- Returns: `MultimodalAnalyzeResponse` with `urgency`, `recommended_next_step`, `image_assessment`, `medical_information`, `treatment_information`, `warning_signs`, `follow_up_questions`, `sources`, `requires_professional_review`, `safety_notice`, `confidence_score`, `processing_time_ms`, `provider`, `model`

### 3. Image Management
```
GET /dedan/v2/images/{image_id}
GET /dedan/v2/images/{image_id}/content
DELETE /dedan/v2/images/{image_id}
```

### 4. Health Check
```
GET /dedan/v2/multimodal/health
GET /dedan/v2/config
```

## Modality Combinations

| Combination | Backend Support |
|-------------|-----------------|
| Text only | ✅ |
| Image only | ✅ |
| Text + Image | ✅ |
| Voice transcript + Image | ✅ |
| Text + Voice transcript + Image | ✅ |

**Important:** Backend accepts `voice_transcript` (text), not raw audio files. Speech-to-text must happen client-side.

## Authentication

No authentication required for multimodal endpoints. Session tracking via `session_id` parameter.

## Differences from Specification

| Spec Claim | Actual Implementation |
|------------|----------------------|
| Audio file upload | Backend accepts `voice_transcript` (text), not raw audio |
| `POST /ai/analyze-image` | Implemented as `POST /dedan/v2/images/upload` + `POST /dedan/v2/multimodal-analyze` |
| Audio field in multimodal request | Not present; only `voice_transcript` |

## Frontend Implementation

### Web Portal (`web-portal/`)

**Components created:**
- `src/components/assessment/MultimodalInput.tsx` — Unified text + image + voice input
- `src/components/assessment/TextComposer.tsx` — Text input with character limit
- `src/components/assessment/VoiceRecorder.tsx` — Voice-to-text using Web Speech API
- `src/components/assessment/AttachmentPreview.tsx` — Image preview with remove/replace
- `src/components/assessment/UploadProgress.tsx` — Upload progress indicator
- `src/components/assessment/MultimodalMessage.tsx` — AI response with safety-first rendering

**Services updated:**
- `src/services/multimodalService.ts` — Already had uploadImage, submitMultimodalAnalysis, etc.
- `src/pages/TriagePage.tsx` — Updated to use MultimodalInput

**Safety UI:**
- Emergency/urgent states render with red/warning banners
- Professional review requirement displayed prominently
- Safety notices shown for emergency/urgent cases
- Warning signs listed explicitly

**No API keys exposed:** All provider credentials remain server-side. The frontend communicates only with the DEDAN Health backend.

### Mobile App (`mobile-app/`)

**Updated `TriageChatScreen.tsx`:**
- Added image attachment (gallery + camera) with permission handling
- Added voice transcript display
- Added multimodal submit with text + voice + image
- Added safety alert rendering for emergency/urgent responses
- Added image preview with remove button

**Permissions:** Camera and storage permissions requested when user attempts photo action, not at startup.

## Backend Startup Required

The v2 backend (`backend-v2/main_v2.py`) must be started for full multimodal support:
```bash
cd backend-v2 && python3 -m uvicorn main_v2:app --host 0.0.0.0 --port 8001
```

The v1 backend (port 8000) handles legacy triage only.

## Testing

Run lint and build:
```bash
cd web-portal && npm run lint
cd web-portal && npm run build
```

## Known Limitations

1. Voice recording uses browser Web Speech API (web) / react-native-voice (mobile) — transcription quality depends on device/browser
2. Image compression not applied — follows backend 20 MB limit
3. Mobile image picker requires `react-native-image-picker` dependency
4. v2 backend not currently running on port 8000 (only v1 is running)
