import uuid
import time
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ImageUploadResponse,
    HealthCheckResponse,
    ErrorResponse,
    UrgencyLevel,
)
from ..services.ai_providers import (
    ProviderFactory,
    ImageInput,
    PatientContext,
    ConversationTurn,
)
from ..services.image_service import image_service, ImageValidationError
from ..services.safety_validator import safety_validator, SafetyCheckResult
from ..services.response_transformer import response_transformer
from ..core.config import get_settings, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyze"])

# Global provider factory (initialized on startup)
provider_factory: Optional[ProviderFactory] = None


def get_provider_factory() -> ProviderFactory:
    if provider_factory is None:
        raise HTTPException(status_code=503, detail="AI providers not initialized")
    return provider_factory


async def initialize_providers(settings: Settings) -> ProviderFactory:
    """Initialize the provider factory with settings."""
    global provider_factory
    factory = ProviderFactory()
    factory.initialize(settings)
    provider_factory = factory
    return factory


@router.post("/images/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """
    Upload a medical image for analysis.
    
    Validates image quality, type, and size before storing temporarily.
    Returns an image_id to use in the analyze endpoint.
    """
    try:
        content = await file.read()
        result = image_service.validate_and_store(content, file.filename or "image.jpg", session_id)
        return result
    except ImageValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "errors": e.errors,
                "warnings": e.warnings,
            }
        )
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/images/upload-base64", response_model=ImageUploadResponse)
async def upload_image_base64(
    request: dict,
):
    """
    Upload a base64-encoded image.
    
    Accepts either raw base64 or data URL format.
    """
    try:
        base64_data = request.get("image_data", "")
        filename = request.get("filename", "image.jpg")
        session_id = request.get("session_id")
        
        if not base64_data:
            raise HTTPException(status_code=400, detail="image_data is required")
        
        result = image_service.validate_and_store_base64(base64_data, filename, session_id)
        return result
    except ImageValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "errors": e.errors,
                "warnings": e.warnings,
            }
        )
    except Exception as e:
        logger.error(f"Base64 image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/images/{image_id}")
async def get_image_metadata(image_id: str):
    """Get image metadata by ID."""
    metadata = image_service.get_metadata(image_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Image not found")
    return metadata


@router.get("/images/{image_id}/preview")
async def get_image_preview(image_id: str):
    """Get image as base64 for preview/display."""
    base64_data = image_service.get_image_base64(image_id)
    if not base64_data:
        raise HTTPException(status_code=404, detail="Image not found")
    
    metadata = image_service.get_metadata(image_id)
    return {
        "image_id": image_id,
        "content": base64_data,
        "mime_type": metadata.get("mime_type", "image/jpeg") if metadata else "image/jpeg",
    }


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an uploaded image."""
    if image_service.delete_image(image_id):
        return {"message": "Image deleted", "image_id": image_id}
    raise HTTPException(status_code=404, detail="Image not found")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    factory: ProviderFactory = Depends(get_provider_factory),
):
    """
    Main analysis endpoint for multi-modal medical triage.
    
    Accepts text symptoms, images, and patient context.
    Returns structured clinical guidance with safety classification.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Validate consent
        if not request.consent:
            raise HTTPException(
                status_code=400,
                detail="Patient consent is required for AI analysis"
            )

        logger.info(f"Starting analysis {request_id} for session {request.session_id or 'new'}")

        # Prepare images
        images: List[ImageInput] = []
        
        # From pre-uploaded image IDs
        for img_id in request.image_ids:
            metadata = image_service.get_metadata(img_id)
            if metadata:
                base64_data = image_service.get_image_base64(img_id)
                if base64_data:
                    images.append(ImageInput(
                        image_data=base64_data,
                        mime_type=metadata["mime_type"],
                        filename=metadata["original_filename"],
                    ))

        # From base64 data in request
        for b64_data in request.image_data_list:
            try:
                mime_type = "image/jpeg"
                if b64_data.startswith("data:"):
                    header, b64_data = b64_data.split(",", 1)
                    mime_type = header.split(":")[1].split(";")[0]
                
                images.append(ImageInput(
                    image_data=b64_data,
                    mime_type=mime_type,
                ))
            except Exception as e:
                logger.warning(f"Failed to process base64 image: {e}")
                continue

        # Prepare patient context
        patient_context = PatientContext(
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
        conversation_history = []
        for turn in request.conversation_history:
            conversation_history.append(ConversationTurn(
                role=turn.get("role", "user"),
                content=turn.get("content", ""),
            ))

        # Combine text inputs
        combined_text = request.symptom_description
        if request.symptom_duration:
            combined_text += f"\nDuration: {request.symptom_duration}"
        if request.symptom_severity:
            combined_text += f"\nSeverity: {request.symptom_severity}"

        # Run AI analysis with fallback
        ai_result = await factory.analyze_with_fallback(
            text=combined_text,
            images=images if images else None,
            voice_transcript=request.voice_transcript,
            conversation_history=conversation_history if conversation_history else None,
            patient_context=patient_context,
            require_vision=len(images) > 0,
        )

        # Safety validation
        safety_result = safety_validator.validate(
            ai_result,
            patient_context,
            original_text=combined_text,
        )
        ai_result = safety_validator.apply_safety_result(ai_result, safety_result)

        # Transform to structured response
        session_id = request.session_id or str(uuid.uuid4())
        response = response_transformer.transform(
            ai_result,
            request_id=request_id,
            session_id=session_id,
            patient_context=patient_context,
        )

        # Log for audit
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(
            f"Analysis {request_id} completed in {processing_time}ms: "
            f"urgency={response.urgency_level}, confidence={response.confidence_score:.2f}"
        )

        # Background task for data collection
        background_tasks.add_task(
            log_analysis_data,
            request_id=request_id,
            session_id=session_id,
            request=request,
            response=response,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error {request_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(factory: ProviderFactory = Depends(get_provider_factory)):
    """Health check endpoint for monitoring."""
    settings = get_settings()
    provider_health = await factory.health_check_all()
    
    all_healthy = all(provider_health.values()) if provider_health else False
    status = "healthy" if all_healthy else "degraded"
    if not provider_health:
        status = "unhealthy"

    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        components={
            "api": "operational",
            "image_service": "operational",
            "safety_validator": "operational",
        },
        ai_providers=provider_health,
    )


@router.get("/providers")
async def list_providers(factory: ProviderFactory = Depends(get_provider_factory)):
    """List configured AI providers and their capabilities."""
    return {
        "providers": factory.list_providers(),
        "primary": factory._primary_provider,
        "fallback_order": factory._fallback_order,
    }


async def log_analysis_data(
    request_id: str,
    session_id: str,
    request: AnalyzeRequest,
    response: AnalyzeResponse,
):
    """Background task to log analysis data for audit/improvement."""
    try:
        # In production, this would write to a database or message queue
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "session_id": session_id,
            "patient_age": request.patient_age,
            "patient_sex": request.patient_sex,
            "patient_location": request.patient_location,
            "has_images": len(request.image_ids) > 0 or len(request.image_data_list) > 0,
            "urgency": response.urgency_level.value,
            "confidence": response.confidence_score,
            "provider": response.ai_provider,
            "model": response.ai_model,
            "processing_time_ms": response.processing_time_ms,
            "safety_flags": response.safety_flags,
        }
        logger.info(f"AUDIT: {log_entry}")
    except Exception as e:
        logger.error(f"Failed to log analysis data: {e}")