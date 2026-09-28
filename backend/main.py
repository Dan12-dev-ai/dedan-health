from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import re
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from models import (
    TriageRequest, TriageResponse, TriageLevel, Language, 
    Condition, TriageSession, DataConsent
)
from dedan_engine import DEDANHealthEngine

# The data-flywheel module requires scikit-learn + SQLAlchemy. If those
# aren't installed in this environment, we degrade gracefully: the /feedback
# and /metrics routes return a clear "unavailable" error instead of failing
# the entire backend import.
try:
    from data_flywheel import data_flywheel
    _FLYWHEEL_AVAILABLE = True
except Exception as _flywheel_err:
    data_flywheel = None
    _FLYWHEEL_AVAILABLE = False
    # logger may not be configured yet; use print for this pre-startup warning.
    print(f"WARNING: Data flywheel not available (reason: {_flywheel_err}); /feedback and /metrics routes will be degraded.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DEDAN HealthEngine API",
    description="Digital Empathy-Driven AI Navigator - Primary Care Triage API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DEDAN Engine
dedan_engine = DEDANHealthEngine()

# In-memory session storage (in production, use Redis or database)
active_sessions = {}

# Data storage (in production, use proper database)
triage_data = []

@app.get("/")
async def root():
    """DEDAN HealthEngine API Root"""
    return {
        "message": "DEDAN HealthEngine - Digital Empathy-Driven AI Navigator",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine_status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/dedan/v1/triage", response_model=TriageResponse)
async def triage_patient(
    request: TriageRequest,
    background_tasks: BackgroundTasks
):
    """
    Perform AI-powered medical triage
    
    Analyzes patient symptoms and profile to determine triage level,
    recommended next steps, and risk factors.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Log the triage request (anonymized)
        logger.info(f"Triage request - Session: {session_id}, Age: {request.patient.age}, Language: {request.patient.language}")
        
        # Perform triage
        triage_result = await dedan_engine.triage_patient(request)
        
        # Store anonymized data for improvement
        background_tasks.add_task(
            store_triage_data,
            session_id=session_id,
            request=request,
            response=triage_result
        )
        
        # Update session
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                "patient_profile": request.patient,
                "symptoms_history": [request.symptoms],
                "triage_responses": [triage_result],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "active"
            }
        else:
            active_sessions[session_id]["symptoms_history"].append(request.symptoms)
            active_sessions[session_id]["triage_responses"].append(triage_result)
            active_sessions[session_id]["updated_at"] = datetime.utcnow()
        
        return triage_result
        
    except Exception as e:
        logger.error(f"Triage error: {str(e)}")
        raise HTTPException(status_code=500, detail="Triage processing failed")

@app.get("/dedan/v1/conditions", response_model=List[str])
async def get_supported_conditions(
    language: Language = Language.ENGLISH
):
    """
    Get list of medical conditions DEDAN can triage
    
    Returns conditions supported in the specified language.
    """
    try:
        conditions = dedan_engine.get_supported_conditions(language)
        return conditions
    except Exception as e:
        logger.error(f"Error getting conditions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conditions")

@app.get("/dedan/v1/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]

@app.post("/dedan/v1/session/{session_id}/consent")
async def update_consent(session_id: str, consent: DataConsent):
    """Update data consent for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    active_sessions[session_id]["consent"] = consent.dict()
    return {"message": "Consent updated successfully"}

@app.get("/dedan/v1/emergency-contacts")
async def get_emergency_contacts(location: Optional[str] = None):
    """Get emergency contacts for a location.
    
    Returns a list of {label, number, note} objects matching the frontend
    EmergencyContact type so the Settings page displays them correctly.
    """
    try:
        raw_contacts = dedan_engine._determine_emergency_contacts(location)
        contacts: List[Dict[str, Any]] = []
        for entry in raw_contacts:
            contacts.append(_parse_emergency_contact(entry))
        return contacts
    except Exception as e:
        logger.error(f"Error getting emergency contacts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emergency contacts")

def _parse_emergency_contact(text: str) -> Dict[str, Any]:
    """Parse a contact string into {label, number, note}.
    
    Handles patterns like:
      - "Ethiopia Emergency: 911"
      - "Ambulance: 907"
      - "Nearest hospital emergency department"
    """
    entry = text.strip()
    # Extract phone number (sequence of digits, possibly with spaces/dashes)
    num_match = re.search(r'(\d[\d\s\-]{2,14}\d|\d{3,4})', entry)
    number = ""
    label = entry
    note = None
    
    if num_match:
        number = num_match.group(0).strip()
        # Remove the number from the text to get the label
        remainder = entry.replace(number, "").strip()
        # Split on ":" to separate label from note
        if ":" in remainder:
            parts = remainder.split(":", 1)
            label = parts[0].strip()
            extra = parts[1].strip()
            if extra:
                note = extra
        else:
            label = remainder
    else:
        # No phone number found — the whole string is the label
        label = entry
    
    return {"label": label, "number": number, "note": note}

@app.post("/dedan/v1/feedback")
async def submit_feedback(feedback: Dict[str, Any]):
    """
    Submit clinician feedback on a triage assessment.
    
    This closes the data-flywheel loop (audit gap R4): doctors can correct
    triage decisions, feeding the continuous-improvement pipeline. The request
    body should contain:
      - triage_data: anonymized triage record (session_id, triage_level, confidence, etc.)
      - doctor_feedback: correction (triage_level, diagnosis, treatment, outcome, etc.)
    """
    if not _FLYWHEEL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Feedback collection requires scikit-learn and SQLAlchemy, which are not installed in this environment.",
        )
    try:
        triage_data = feedback.get("triage_data", {})
        doctor_feedback = feedback.get("doctor_feedback", {})
        if not triage_data or not doctor_feedback:
            raise HTTPException(
                status_code=400,
                detail="Both 'triage_data' and 'doctor_feedback' are required."
            )
        # Validate required fields for the feedback record.
        required_triage = ["session_id", "triage_level", "symptoms_description"]
        required_feedback = ["triage_level"]
        missing = []
        for f in required_triage:
            if not triage_data.get(f):
                missing.append(f"triage_data.{f}")
        for f in required_feedback:
            if not doctor_feedback.get(f):
                missing.append(f"doctor_feedback.{f}")
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )
        # Fill in defaults for non-critical NOT NULL fields so partial records succeed.
        defaults = {
            "patient_age_group": "unknown",
            "patient_sex": "unknown",
            "patient_language": "en",
            "symptoms_keywords": "[]",
            "symptoms_description": triage_data.get("symptoms_description", ""),
            "confidence_score": triage_data.get("confidence_score", 0.0),
            "suggested_next_step": triage_data.get("suggested_next_step", "Please seek medical attention."),
            "patient_summary": triage_data.get("patient_summary", "Symptoms require evaluation."),
        }
        for key, val in defaults.items():
            if key not in triage_data or triage_data.get(key) is None:
                triage_data[key] = val
        # Ensure symptoms_keywords and risk_flags are JSON strings
        if isinstance(triage_data.get("symptoms_keywords"), (list, dict)):
            triage_data["symptoms_keywords"] = json.dumps(triage_data["symptoms_keywords"])
        if isinstance(triage_data.get("risk_flags"), (list, dict)):
            triage_data["risk_flags_detected"] = json.dumps(triage_data["risk_flags"])
            triage_data.pop("risk_flags", None)
        success = await data_flywheel.collect_feedback(triage_data, doctor_feedback)
        if success:
            logger.info(f"Feedback collected for session {triage_data.get('session_id')}")
            return {"success": True, "message": "Feedback recorded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record feedback")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")

@app.get("/dedan/v1/metrics")
async def get_metrics(days: int = 30):
    """Get performance metrics from the data flywheel."""
    if not _FLYWHEEL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Metrics require scikit-learn and SQLAlchemy, which are not installed in this environment.",
        )
    try:
        metrics = await data_flywheel.get_performance_metrics(days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@app.get("/dedan/v1/stats")
async def get_platform_stats():
    """Get platform usage statistics"""
    return {
        "total_sessions": len(active_sessions),
        "total_triages": len(triage_data),
        "active_sessions": len([s for s in active_sessions.values() if s["status"] == "active"]),
        "supported_languages": ["en", "sw", "am", "es", "fr"],
        "triage_levels": ["emergency", "urgent", "routine", "self_care"]
    }

# Background task for storing triage data
async def store_triage_data(session_id: str, request: TriageRequest, response: TriageResponse):
    """Store anonymized triage data for continuous improvement"""
    try:
        # Create anonymized record
        anonymized_record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "patient_age_group": categorize_age(request.patient.age),
            "patient_sex": request.patient.sex,
            "language": request.patient.language.value,
            "location_region": request.patient.location,
            "chronic_conditions": request.patient.chronic_conditions,
            "symptoms_keywords": extract_keywords(request.symptoms.symptoms),
            "triage_level": response.triage_level.value,
            "risk_flags_count": len(response.risk_flags),
            "confidence_score": response.confidence_score,
            "has_emergency_flags": any(flag.type == "emergency_symptom" for flag in response.risk_flags)
        }
        
        triage_data.append(anonymized_record)
        logger.info(f"Stored triage data for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to store triage data: {str(e)}")

def categorize_age(age: int) -> str:
    """Categorize age for analytics"""
    if age < 1:
        return "infant"
    elif age < 12:
        return "child"
    elif age < 18:
        return "adolescent"
    elif age < 65:
        return "adult"
    else:
        return "elderly"

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from symptom text"""
    # Simple keyword extraction - in production, use NLP
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common words
    stop_words = {'i', 'me', 'my', 'have', 'has', 'been', 'is', 'are', 'was', 'were', 'the', 'a', 'an'}
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords[:10]  # Limit to 10 keywords

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
