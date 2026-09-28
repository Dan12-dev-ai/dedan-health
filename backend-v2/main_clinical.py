"""
Minimal FastAPI app for Clinical Guidance endpoint only.
Excludes agents module which requires deprecated langchain 0.x.
"""

import os
os.environ.setdefault('GEMINI_API_KEY', 'test-key')
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
os.environ.setdefault('DEFAULT_AI_PROVIDER', 'gemini')

import logging
import time
import base64
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, status, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from clinical_context_builder import clinical_context_builder
from evidence_retrieval_enhanced import evidence_retriever
from medication_safety_enhanced import medication_safety_service
from visual_education_enhanced import visual_education_service
from conversation_memory import ConversationMemoryManager
from urgency_engine import UrgencyEngine
from response_transformer import response_transformer
from safety_validator import safety_validator
from image_service import image_service, ImageValidationError
from models.schemas import (
    AnalyzeRequest, AnalyzeResponse, ImageUploadResponse,
    HealthCheckResponse, ErrorResponse, UrgencyLevel,
)
from app.core.config import get_settings, Settings
from providers import (
    ProviderFactory,
    ImageInput,
    MultimodalOrchestrator,
    PatientProfile as ProviderPatientProfile,
    ConversationTurn as ProviderConversationTurn,
    Modality,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limit_storage: dict = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/api/health", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        now = time.time()
        window_start = now - self.window_seconds

        if client_ip in rate_limit_storage:
            rate_limit_storage[client_ip] = [
                ts for ts in rate_limit_storage[client_ip] if ts > window_start
            ]
        else:
            rate_limit_storage[client_ip] = []

        if len(rate_limit_storage[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "limit": self.requests_per_minute,
                        "window_seconds": self.window_seconds,
                        "retry_after": self.window_seconds,
                    },
                    "timestamp": time.time(),
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        rate_limit_storage[client_ip].append(now)
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"REQUEST: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"RESPONSE: {request.method} {request.url.path} status={response.status_code} time={process_time:.1f}ms")
        response.headers["X-Process-Time"] = f"{process_time:.1f}"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting DEDAN Health Clinical API v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode")
    
    # Initialize AI providers
    try:
        factory = ProviderFactory()
        app.state.provider_factory = factory
        app.state.multimodal_orchestrator = MultimodalOrchestrator(provider_factory=factory)
        logger.info("AI providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI providers: {e}")
    
    # Start cleanup task
    import asyncio
    asyncio.create_task(periodic_cleanup())
    
    yield
    
    logger.info(f"Shutting down DEDAN Health Clinical API")


async def periodic_cleanup():
    import asyncio
    while True:
        await asyncio.sleep(3600)
        try:
            deleted = image_service.cleanup_expired()
            if deleted:
                logger.info(f"Periodic cleanup: removed {deleted} expired images")
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")


def create_app(settings = None) -> FastAPI:
    settings = settings or get_settings()
    
    app = FastAPI(
        title="DEDAN Health Clinical API",
        version=settings.APP_VERSION,
        description="AI-powered medical triage clinical guidance for underserved regions",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )

    # Trusted hosts
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.dedanhealth.org", "dedanhealth.org", "localhost", "127.0.0.1"],
        )

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.ADMIN_API_KEY or "dev-secret-change-in-production",
        https_only=settings.ENVIRONMENT == "production",
    )

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP error",
                "error_code": f"HTTP_{exc.status_code}",
                "details": exc.detail if isinstance(exc.detail, dict) else None,
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "details": {"type": type(exc).__name__} if settings.DEBUG else None,
                "timestamp": time.time(),
            },
        )

    # Dependency for provider factory
    def get_provider_factory() -> ProviderFactory:
        if not hasattr(app.state, 'provider_factory'):
            raise HTTPException(status_code=503, detail="AI providers not initialized")
        return app.state.provider_factory

    def get_orchestrator() -> MultimodalOrchestrator:
        if not hasattr(app.state, 'multimodal_orchestrator'):
            raise HTTPException(status_code=503, detail="Multimodal orchestrator not initialized")
        return app.state.multimodal_orchestrator

    # ============ ENDPOINTS ============
    
    @app.post("/api/images/upload", response_model=ImageUploadResponse)
    async def upload_image(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
        try:
            content = await file.read()
            result = image_service.validate_and_store(content, file.filename or "image.jpg", session_id)
            return result
        except ImageValidationError as e:
            raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.errors, "warnings": e.warnings})
        except Exception as e:
            logger.error(f"Image upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @app.post("/api/images/upload-base64", response_model=ImageUploadResponse)
    async def upload_image_base64(request: dict):
        try:
            base64_data = request.get("image_data", "")
            filename = request.get("filename", "image.jpg")
            session_id = request.get("session_id")
            if not base64_data:
                raise HTTPException(status_code=400, detail="image_data is required")
            file_content = base64.b64decode(base64_data)
            result = image_service.validate_and_store(file_content, filename, session_id)
            return result
        except ImageValidationError as e:
            raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.errors, "warnings": e.warnings})
        except Exception as e:
            logger.error(f"Base64 image upload error: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @app.get("/api/images/{image_id}")
    async def get_image_metadata(image_id: str):
        metadata = image_service.get_metadata(image_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Image not found")
        return metadata

    @app.get("/api/images/{image_id}/preview")
    async def get_image_preview(image_id: str):
        base64_data = image_service.get_image_base64(image_id)
        if not base64_data:
            raise HTTPException(status_code=404, detail="Image not found")
        metadata = image_service.get_metadata(image_id)
        return {"image_id": image_id, "content": base64_data, "mime_type": metadata.get("mime_type", "image/jpeg")}

    @app.delete("/api/images/{image_id}")
    async def delete_image(image_id: str):
        if image_service.delete_image(image_id):
            return {"message": "Image deleted", "image_id": image_id}
        raise HTTPException(status_code=404, detail="Image not found")

    @app.post("/api/analyze", response_model=dict)
    async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            if not request.consent:
                raise HTTPException(status_code=400, detail="Patient consent is required for AI analysis")

            logger.info(f"Starting analysis {request_id} for session {request.session_id or 'new'}")

            # Prepare images
            images = []
            for img_id in request.image_ids:
                metadata = image_service.get_metadata(img_id)
                if metadata:
                    base64_data = image_service.get_image_base64(img_id)
                    if base64_data:
                        images.append(ImageInput(image_data=base64_data, mime_type=metadata["mime_type"], filename=metadata["original_filename"]))

            for b64_data in request.image_data_list:
                try:
                    mime_type = "image/jpeg"
                    if b64_data.startswith("data:"):
                        header, b64_data = b64_data.split(",", 1)
                        mime_type = header.split(":")[1].split(";")[0]
                    images.append(ImageInput(image_data=b64_data, mime_type=mime_type))
                except Exception as e:
                    logger.warning(f"Failed to process base64 image: {e}")
                    continue

            # Prepare patient context
            from providers.models import PatientProfile as ProviderPatientProfile
            patient_context = ProviderPatientProfile(
                age=request.patient_age,
                sex=request.patient_sex,
                location=request.patient_location,
                pregnancy_status=request.patient_pregnant,
                chronic_conditions=request.patient_chronic_conditions,
                medications=request.patient_medications,
                allergies=request.patient_allergies,
                language=request.patient_language,
            )

            # Prepare conversation history
            from providers.models import ConversationTurn as ProviderConversationTurn
            conversation_history = [
                ProviderConversationTurn(role=turn.get("role", "user"), content=turn.get("content", ""))
                for turn in request.conversation_history
            ]

            # Combine text inputs
            combined_text = request.symptom_description
            if request.symptom_duration:
                combined_text += f"\nDuration: {request.symptom_duration}"
            if request.symptom_severity:
                combined_text += f"\nSeverity: {request.symptom_severity}"

            # Run AI analysis
            from providers import MultimodalOrchestrator
            orchestrator = MultimodalOrchestrator()
            ai_result = await orchestrator.process(
                text=combined_text,
                images=images if images else None,
                voice_transcript=request.voice_transcript,
                conversation_history=conversation_history if conversation_history else None,
                patient_profile=patient_context,
                session_id=request.session_id,
            )

            # Safety validation
            # NOTE: `validate_async` / `apply_safety_result_async` are coroutine
            # functions; both must be awaited. Calling them without `await`
            # rebinds `ai_result` to a coroutine object, which later fails in
            # the response transformer with a confusing attribute error.
            safety_result = await safety_validator.validate_async(
                ai_result, patient_context, original_text=combined_text
            )
            ai_result = await safety_validator.apply_safety_result_async(ai_result, safety_result)

            # Build clinical context
            from models_v2 import PatientProfile as ClinicalPatientProfile, SymptomInput
            clinical_patient = ClinicalPatientProfile(
                age=request.patient_age,
                sex=request.patient_sex,
                language=request.patient_language,
                location=request.patient_location,
                pregnancy_status=request.patient_pregnant,
                chronic_conditions=request.patient_chronic_conditions,
                medications=request.patient_medications,
                allergies=request.patient_allergies,
            )
            clinical_symptoms = SymptomInput(
                symptoms=request.symptom_description,
                duration=request.symptom_duration,
                severity={"mild": 3, "moderate": 5, "severe": 8}.get(request.symptom_severity, 5),
            )
            clinical_context = await clinical_context_builder.build(
                patient_profile=clinical_patient,
                symptoms=clinical_symptoms,
                voice_transcript=request.voice_transcript,
                conversation_history=request.conversation_history,
                session_id=request.session_id or str(uuid.uuid4()),
            )

            # Transform to structured response
            session_id = request.session_id or str(uuid.uuid4())
            structured_response = response_transformer.transform(ai_result, clinical_context, request_id, session_id)

            # Enhance with visual education
            conditions = [c.label for c in structured_response.possible_explanations]
            body_systems = _extract_body_systems(conditions, combined_text)
            treatment_approaches = _extract_treatment_approaches(structured_response)
            medication_classes = _extract_medication_classes(structured_response)
            visual_education_items = visual_education_service.get_visuals_for_response(
                conditions=conditions, body_systems=body_systems,
                treatment_approaches=treatment_approaches, medication_classes=medication_classes
            )
            structured_response.visual_education = visual_education_items

            # Enhance medication with pharmacy verification
            from clinical_schema import MedicationVerificationItem
            for med in structured_response.medication_information:
                verification = medication_safety_service.get_pharmacy_verification_workflow(med.medication_class)
                structured_response.medication_verification.extend([
                    MedicationVerificationItem(field=item["field"], description=item["description"], why_important=item.get("why_important", "Important for safety"))
                    for item in verification.get("package_check_items", [])
                ])

            # Build final clinical response
            from clinical_schema import ClinicalResponse
            clinical = ClinicalResponse(
                response_id=request_id, session_id=session_id, timestamp=datetime.utcnow().isoformat(),
                health_summary=structured_response.health_summary, safety=structured_response.safety,
                possible_explanations=structured_response.possible_explanations, uncertainty=structured_response.uncertainty,
                treatment_education=structured_response.treatment_education, medication_information=structured_response.medication_information,
                visual_education=structured_response.visual_education, follow_up=structured_response.follow_up,
                sources=structured_response.sources, professional_review=structured_response.professional_review,
                provider=ai_result.provider, model=ai_result.model, confidence_score=ai_result.confidence_score,
                disclaimer=structured_response.disclaimer,
            )

            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Analysis {request_id} completed in {processing_time}ms: urgency={clinical.safety.urgency.value}")

            return clinical.to_dict()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Analysis error {request_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    @app.get("/api/health", response_model=HealthCheckResponse)
    async def health_check():
        settings = get_settings()
        return HealthCheckResponse(
            status="healthy", timestamp=datetime.utcnow(),
            version=settings.APP_VERSION,
            components={"api": "operational", "image_service": "operational", "safety_validator": "operational"},
            ai_providers={},
        )

    @app.get("/api/providers")
    async def list_providers():
        return {"providers": [], "primary": "gemini", "fallback_order": []}

    @app.get("/")
    async def root():
        return {"service": "DEDAN Health Clinical API", "version": "1.0.0", "status": "operational"}

    @app.get("/health")
    async def legacy_health():
        return {"status": "healthy", "service": "DEDAN Health Clinical API"}

    return app


def _extract_body_systems(conditions: list, symptoms: str) -> list:
    systems = set()
    text = " ".join(conditions + [symptoms]).lower()
    system_keywords = {
        "respiratory": ["respiratory", "lung", "breathing", "cough", "pneumonia", "asthma"],
        "cardiovascular": ["heart", "cardiac", "chest pain", "hypertension", "blood pressure"],
        "gastrointestinal": ["abdominal", "stomach", "diarrhea", "vomiting", "nausea", "liver", "hepatitis"],
        "neurological": ["headache", "seizure", "confusion", "stroke", "brain", "migraine"],
        "dermatological": ["rash", "skin", "lesion", "bite", "dermatitis", "eczema"],
        "infectious": ["fever", "infection", "malaria", "dengue", "tb", "tuberculosis", "hiv"],
        "musculoskeletal": ["joint", "muscle", "bone", "pain", "arthritis", "fracture"],
        "genitourinary": ["urinary", "kidney", "bladder", "uti", "renal"],
        "endocrine": ["diabetes", "thyroid", "hormone", "glucose", "insulin"],
    }
    for system, keywords in system_keywords.items():
        if any(kw in text for kw in keywords):
            systems.add(system)
    return list(systems)


def _extract_treatment_approaches(response) -> list:
    approaches = []
    for te in response.treatment_education:
        approaches.append(te.title)
    return approaches


def _extract_medication_classes(response) -> list:
    classes = []
    for med in response.medication_information:
        classes.append(med.medication_class)
    return classes


async def log_analysis_data(request_id: str, session_id: str, request, response):
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id, "session_id": session_id,
            "patient_age": request.patient_age, "patient_sex": request.patient_sex,
            "patient_location": request.patient_location,
            "has_images": len(request.image_ids) > 0 or len(request.image_data_list) > 0,
            "urgency": response.safety.urgency.value, "confidence": response.confidence_score,
            "provider": response.provider, "model": response.model,
            "processing_time_ms": response.processing_time_ms, "safety_flags": response.safety_flags,
        }
        logger.info(f"AUDIT: {log_entry}")
    except Exception as e:
        logger.error(f"Failed to log analysis data: {e}")


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("main_clinical:app", host=settings.HOST, port=settings.PORT, log_level=settings.LOG_LEVEL.lower(), reload=settings.DEBUG)
