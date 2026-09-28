# DEDAN Health — Multimodal AI Extension Implementation Plan

## Executive Summary

This plan implements multimodal AI capabilities (text + voice + image) as an **extensible capability layer** on top of the existing DEDAN Health architecture, without breaking any current functionality.

**Current State:**
- Backend v1: Simple FastAPI + OpenAI GPT-3.5 + basic RAG (LIVE at `/dedan/v1/triage`)
- Backend v2: Agent-orchestrated (Coordinator, Triage, Safety, Guideline, Risk) + GPT-4-turbo (BROKEN imports)
- Frontend: React + TypeScript + MUI, talks to v1 API
- Mobile: React Native
- Input: Text only (voice_input flag exists but not wired end-to-end)

**Target State:**
- Unified multimodal input: Text, Voice, Image, and any combination
- Provider abstraction: `MultimodalAIProvider` → `GeminiProvider`, `OpenAIProvider`, etc.
- Secure image upload + validation + processing
- Structured medical image analysis output with RAG grounding
- Backward-compatible API extensions
- Frontend + Mobile multimodal UI

---

## Phase 1: Foundation & Provider Abstraction (Backend)

### 1.1 Create Provider Abstraction Layer

**New Files:**
```
backend-v2/providers/
├── __init__.py
├── base.py                 # Abstract base classes
├── gemini_provider.py      # Gemini 1.5 Pro/Flash integration
├── openai_provider.py      # GPT-4o vision integration
├── provider_factory.py     # Configuration-driven provider selection
└── models.py               # Provider-agnostic request/response models
```

**Key Classes:**
```python
# base.py
class MultimodalAIProvider(ABC):
    @abstractmethod
    async def analyze_text(self, request: TextAnalysisRequest) -> AnalysisResponse
    @abstractmethod
    async def analyze_image(self, request: ImageAnalysisRequest) -> AnalysisResponse
    @abstractmethod
    async def analyze_multimodal(self, request: MultimodalAnalysisRequest) -> AnalysisResponse
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities

class ProviderCapabilities:
    supports_text: bool
    supports_vision: bool
    supports_audio: bool
    max_image_size_mb: int
    supported_formats: List[str]
    context_window: int
```

### 1.2 Gemini Provider Implementation

**Requirements:**
- Use `google-generativeai` SDK (current, not obsolete)
- Support gemini-1.5-pro and gemini-1.5-flash
- Structured output via Pydantic schemas
- Safety settings for medical content
- Token counting for cost tracking

### 1.3 Configuration-Driven Provider Selection

```python
# config.py additions
AI_TEXT_PROVIDER = os.getenv("AI_TEXT_PROVIDER", "openai")
AI_VISION_PROVIDER = os.getenv("AI_VISION_PROVIDER", "gemini")
AI_MULTIMODAL_PROVIDER = os.getenv("AI_MULTIMODAL_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
---

## Phase 2: Secure Image Handling (Backend)

### 2.1 Image Upload Endpoint

**New Endpoint:** `POST /dedan/v1/analyze-image` (or extend existing `/dedan/v1/triage`)

**Request:**
```python
class ImageAnalysisRequest(BaseModel):
    image: UploadFile
    text: Optional[str] = None
    conversation_id: Optional[str] = None
    assessment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 2.2 Image Validation Pipeline

```python
class ImageValidator:
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSION = 4096
    
    async def validate(self, file: UploadFile) -> ValidationResult
    async def assess_quality(self, image: Image.Image) -> QualityAssessment
```

**Quality Assessment:**
- Resolution check (min 256x256 for medical relevance)
- Brightness/contrast analysis
- Blur detection (Laplacian variance)
- Orientation detection (EXIF)
- Relevance scoring (skin/medical content detection)

### 2.3 Secure Storage

- **Storage:** S3-compatible (MinIO for dev, AWS S3/GCS for prod)
- **Naming:** UUID + content hash (no guessable URLs)
- **Access:** Pre-signed URLs with short TTL (15 min)
- **Retention:** Configurable (default 30 days, purge on consent withdrawal)
- **Audit:** Log all access (who, when, what) without storing image bytes
```
---

## Phase 3: Multimodal Orchestration (Backend)

### 3.1 Multimodal Context Builder

```python
class MultimodalContextBuilder:
    def build_context(
        self,
        text: Optional[str],
        voice_transcript: Optional[str],
        image_analysis: Optional[ImageAnalysisResult],
        conversation_history: List[ConversationTurn],
        patient_profile: PatientProfile
    ) -> MultimodalClinicalContext
```

### 3.2 Unified Orchestrator

```python
class MultimodalOrchestrator:
    def __init__(
        self,
        provider_factory: ProviderFactory,
        rag_service: RAGService,
        safety_validator: SafetyValidator,
        audit_logger: AuditLogger
    )
    
    async def process(
        self,
        request: MultimodalRequest
    ) -> MultimodalResponse
```

**Routing Logic:**
| Input Modalities | Provider Route |
|-----------------|----------------|
| Text only | Text provider (existing) |
| Voice only | STT → Text provider |
| Image only | Vision provider |
| Text + Image | Multimodal provider |
| Voice + Image | STT → Multimodal provider |
| Text + Voice + Image | STT → Multimodal provider |

### 3.3 Structured Medical Output Schema

```python
class ImageAssessment(BaseModel):
    observations: List[str]
    possible_explanations: List[PossibleExplanation]
    limitations: List[str]
    image_quality: ImageQuality

class PossibleExplanation(BaseModel):
    condition: str
    likelihood: str  # "possible" | "likely" | "unlikely"
    reasoning: str
    citations: List[str]

class MultimodalResponse(BaseModel):
    image_assessment: Optional[ImageAssessment]
    urgency: TriageLevel
    recommended_next_step: str
    medical_information: List[MedicalInformation]
    treatment_information: List[TreatmentInformation]
    warning_signs: List[str]
    follow_up_questions: List[str]
    sources: List[Source]
    uncertainty: str
    requires_professional_review: bool
    safety_notice: str
```
---

## Phase 4: RAG Integration for Image Analysis

### 4.1 Visual Observation → Clinical Query

```python
class ImageRAGPipeline:
    async def retrieve_evidence(
        self,
        observations: List[str],
        possible_conditions: List[str]
    ) -> List[ClinicalEvidence]
```

### 4.2 Evidence-Grounded Response

- Convert visual observations to clinical queries
- Retrieve from clinical guidelines vector store
- Filter by relevance and authority
- Cite sources in final response

---

## Phase 5: API Layer (Backend)

### 5.1 New/Extended Endpoints

```python
# Extend existing triage endpoint (backward compatible)
POST /dedan/v1/triage
  - Add optional: image_ids: List[str], voice_transcript: str

# New dedicated multimodal endpoint
POST /dedan/v1/multimodal-analyze
  - Full multimodal input support

# Image management
POST   /dedan/v1/images/upload
GET    /dedan/v1/images/{image_id}
DELETE /dedan/v1/images/{image_id}
GET    /dedan/v1/images/{image_id}/presigned-url
```

### 5.2 Request/Response Models

Extend `TriageRequest` with optional multimodal fields (backward compatible):
```python
class TriageRequestV2(TriageRequest):
    image_ids: List[str] = []
    voice_transcript: Optional[str] = None
    voice_audio_id: Optional[str] = None
    modalities: List[str] = ["text"]  # ["text", "image", "voice"]
```
---

## Phase 6: Frontend Implementation (Web Portal)

### 6.1 Multimodal Input Component

**New Component:** `src/components/assessment/MultimodalInput.tsx`

```tsx
interface MultimodalInputProps {
  onSubmit: (data: MultimodalInputData) => Promise<void>;
  loading: boolean;
  error?: string;
}

interface MultimodalInputData {
  text: string;
  duration?: string;
  severity?: SymptomSeverity;
  image?: File;
  imagePreview?: string;
  voiceTranscript?: string;
  isRecording?: boolean;
}
```

**UI Layout:**
```
┌─────────────────────────────────────┐
│ Tell DEDAN Health what is happening │
│                                     │
│ [ Type your symptoms...           ] │
│                                     │
│ [ 🎤 Mic ] [ 📷 Add image ]        │
│                                     │
│ [Image preview with ✕ remove]      │
│                                     │
│      [ Analyze / Continue ]         │
└─────────────────────────────────────┘
```

### 6.2 Image Upload Flow

1. User clicks 📷 → file picker
2. Client-side validation (type, size)
3. Show preview + remove button
4. On submit: upload to `/dedan/v1/images/upload` → get `image_id`
5. Include `image_id` in triage request

### 6.3 Voice Input (Future-Ready)

- Web Speech API for browser-based STT
- Show recording state + live transcript
- Send transcript as `voice_transcript` field

### 6.4 Integration with TriagePage

- Replace current text-only form with `MultimodalInput`
- Maintain existing progress stages
- Add image upload progress indicator
- Handle multimodal error states

---

## Phase 7: Mobile Implementation (React Native)

### 7.1 Multimodal Input Screen

- Camera/photo library access (`react-native-image-picker`)
- Microphone access (`react-native-voice` or `expo-audio`)
- Same API contracts as web

### 7.2 Image Upload

- Compress on device before upload
- Show upload progress
- Handle background upload

---

## Phase 8: Safety & Compliance

### 8.1 Medical Image Safety Rules

- Never claim certainty from visual evidence alone
- Use "may be consistent with" / "cannot be reliably determined" language
- Explicit uncertainty field in every response
- Escalation triggers for high-risk visual patterns

### 8.2 Privacy & Consent

- Explicit consent for image upload
- Clear disclosure: which AI provider receives images
- Right to delete images immediately
- No images in logs or analytics

### 8.3 Audit Logging

```python
class AIAuditRecord:
    request_id: str
    conversation_id: str
    input_modalities: List[str]
    provider: str
    model: str
    prompt_version: str
    response_schema_version: str
    latency_ms: int
    token_usage: TokenUsage
    safety_result: SafetyResult
    timestamp: datetime
```

## Phase 9: Testing Strategy

### 9.1 Unit Tests

- Provider abstraction contract tests
- Image validation pipeline
- Quality assessment accuracy
- Structured output parsing

### 9.2 Integration Tests

- Text → AI → Response
- Voice → STT → AI → Response
- Image → Gemini → Structured Response
- Text + Image → Multimodal → Response
- Voice + Image → STT + Multimodal → Response
- All three modalities

### 9.3 Failure Mode Tests

- Invalid image format/size
- Blurry/dark/unusable images
- Gemini timeout / rate limit
- Malformed AI response
- Unauthorized image access
- Provider unavailable fallback

### 9.4 Medical Safety Tests

- Hallucination detection
- Inappropriate certainty
- Treatment grounding verification
- Emergency escalation accuracy
- Irrelevant image handling

---

## Phase 10: Deployment & Observability

### 10.1 Environment Variables

```bash
# Provider Configuration
AI_TEXT_PROVIDER=openai
AI_VISION_PROVIDER=gemini
AI_MULTIMODAL_PROVIDER=gemini

# API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Model Selection
GEMINI_MODEL=gemini-1.5-pro
OPENAI_VISION_MODEL=gpt-4o

# Image Storage
IMAGE_STORAGE_BACKEND=s3  # or minio
S3_BUCKET=dedan-health-images
S3_REGION=us-east-1
IMAGE_RETENTION_DAYS=30
IMAGE_MAX_SIZE_MB=10

# Safety
IMAGE_QUALITY_THRESHOLD=0.6
REQUIRE_PROFESSIONAL_REVIEW_THRESHOLD=0.7
```

### 10.2 Monitoring

- Request latency by modality
- Provider success/error rates
- Image quality distribution
- Safety escalation rate
- Cost per modality

---

## Implementation Sequence

| Phase | Priority | Est. Effort | Dependencies |
|-------|----------|-------------|--------------|
| 1. Provider Abstraction | P0 | 3 days | None |
| 2. Gemini Provider | P0 | 2 days | Phase 1 |
| 3. Image Validation/Storage | P0 | 3 days | None |
| 4. Multimodal Orchestrator | P0 | 3 days | Phases 1-3 |
| 5. RAG Integration | P1 | 2 days | Phase 4 |
| 6. API Endpoints | P0 | 2 days | Phases 1-4 |
| 7. Frontend Multimodal UI | P0 | 3 days | Phase 6 |
| 8. Mobile Multimodal UI | P1 | 3 days | Phase 6 |
| 9. Safety/Compliance | P0 | 2 days | Phases 1-4 |
| 10. Testing | P0 | 3 days | All |
| 11. Deployment Config | P1 | 1 day | All |

**Total: ~27 days for full implementation**

---

## Non-Regression Checklist

- [ ] `POST /dedan/v1/triage` (text-only) works identically
- [ ] Existing v1 frontend works without changes
- [ ] Existing v2 agent orchestration untouched
- [ ] RAG system unchanged
- [ ] Safety layer unchanged
- [ ] Authentication/authorization unchanged
- [ ] Database schema additions only (no breaking changes)
- [ ] Mobile app API contracts maintained

---

## Definition of Done

```text
[ ] Text input works (existing)
[ ] Voice input works (STT → existing pipeline)
[ ] Image upload works (validation + storage)
[ ] Image validation works (MIME, size, quality)
[ ] Gemini integration works with real credentials
[ ] Text + image works (multimodal provider)
[ ] Voice + image works (STT + multimodal)
[ ] Combined multimodal interaction works
[ ] AI output is schema validated
[ ] Medical evidence retrieval works for image findings
[ ] Treatment information is evidence-grounded
[ ] Safety validation works for multimodal
[ ] Emergency escalation works
[ ] Image privacy controls work (access, retention, deletion)
[ ] Authorization works (image access control)
[ ] Frontend works (unified multimodal input)
[ ] Mobile works (camera + mic + text)
[ ] Tests pass (unit + integration + safety)
[ ] Failure handling works (provider fallback, timeouts)
[ ] Observability works (audit logs, metrics)
[ ] Production deployment works
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gemini API changes | Provider abstraction isolates changes |
| Image storage costs | Configurable retention, compression, tiered storage |
| Medical liability | Explicit uncertainty, professional review flags, disclaimers |
| Performance (multimodal latency) | Parallel processing, provider fallback, caching |
| Privacy breach | Encrypted storage, pre-signed URLs, audit logs, no PHI in logs |
| Provider lock-in | Abstract interface, multiple providers from day 1 |

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up development environment** with Gemini API access
3. **Create feature branch** for multimodal work
4. **Start Phase 1** (Provider Abstraction + Gemini Provider)
5. **Weekly sync** on progress and blockers

---

*This plan is a living document. Update as implementation reveals new constraints or opportunities.*