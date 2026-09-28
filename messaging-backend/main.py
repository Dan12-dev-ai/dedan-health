from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import os
import logging
import asyncio
from datetime import datetime, timedelta
import re
import httpx
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import redis
import json
import phonenumbers
from pycountry import countries

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="DEDAN Messaging Backend",
    description="WhatsApp/SMS integration for DEDAN Health AI triage",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Settings:
    def __init__(self):
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.dedan_api_url = os.getenv("DEDAN_API_URL", "http://localhost:8000")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH", "160"))
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
        self.rate_limit_messages = int(os.getenv("RATE_LIMIT_MESSAGES", "10"))  # 10 messages per hour

settings = Settings()

# Initialize Twilio client
twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

# Initialize Redis for session management
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Models
class IncomingMessage(BaseModel):
    From: str = Field(..., description="Sender phone number")
    Body: str = Field(..., description="Message body")
    MessageSid: Optional[str] = Field(None, description="Twilio message SID")
    AccountSid: Optional[str] = Field(None, description="Twilio account SID")

class OutgoingMessage(BaseModel):
    to: str = Field(..., description="Recipient phone number")
    body: str = Field(..., description="Message body")
    media_url: Optional[str] = Field(None, description="Optional media URL")

class PatientSession(BaseModel):
    phone_number: str
    patient_profile: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    message_count: int = 0
    language: str = "en"

class TriageRequest(BaseModel):
    patient: Dict[str, Any]
    symptoms: Dict[str, Any]
    session_id: Optional[str] = None
    consent: bool = True

# Emergency keywords in multiple languages
EMERGENCY_KEYWORDS = {
    "en": [
        "chest pain", "heart attack", "difficulty breathing", "shortness of breath",
        "severe bleeding", "unconscious", "fainting", "seizure", "stroke",
        "suicidal", "self harm", "overdose", "emergency"
    ],
    "sw": [
        "maumivu ya kifua", "shida ya kupumua", "kuchoka kupumua",
        "kuumwa kichwa sana", "kutopata fahamu", "matatizo ya uzazi"
    ],
    "am": [
        "እግረኛ ህመም", "እስከ ሞት የሚያስከትል", "እስከ ሞት የሚያስከትል ህመም",
        "ከፍተኛ ደም መፍሰስ", "ማስታወሪ መቀዘቅ", "የልጅ ማረግ አደጋ"
    ]
}

# Helper functions
def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    try:
        # Remove all non-digit characters
        phone_digits = re.sub(r'\D', '', phone)
        
        # Add country code if missing (assuming US/Canada for simplicity)
        if len(phone_digits) == 10:
            phone_digits = '1' + phone_digits
        
        # Parse and format
        parsed_number = phonenumbers.parse(phone_digits, "US")
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except:
        pass
    
    return phone

def detect_language(text: str) -> str:
    """Simple language detection based on keywords"""
    text_lower = text.lower()
    
    # Swahili indicators
    swahili_words = ['na', 'kwa', 'ya', 'ni', 'tuna', 'mimi', 'wewe', 'hivyo']
    if any(word in text_lower for word in swahili_words):
        return "sw"
    
    # Amharic indicators (simplified)
    if any(ord(char) > 127 for char in text):  # Non-ASCII characters
        return "am"
    
    return "en"

def check_emergency_keywords(text: str, language: str) -> bool:
    """Check if message contains emergency keywords"""
    text_lower = text.lower()
    keywords = EMERGENCY_KEYWORDS.get(language, EMERGENCY_KEYWORDS["en"])
    
    return any(keyword in text_lower for keyword in keywords)

def truncate_message(message: str, max_length: int = 160) -> str:
    """Truncate message to fit SMS limits"""
    if len(message) <= max_length:
        return message
    
    return message[:max_length-3] + "..."

async def get_or_create_session(phone_number: str) -> PatientSession:
    """Get or create patient session"""
    if not redis_client:
        # Fallback to memory-based session
        return PatientSession(
            phone_number=phone_number,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            language=detect_language("")  # Will detect from first message
        )
    
    session_key = f"session:{phone_number}"
    session_data = redis_client.get(session_key)
    
    if session_data:
        session_dict = json.loads(session_data)
        session = PatientSession(**session_dict)
        session.last_activity = datetime.utcnow()
    else:
        session = PatientSession(
            phone_number=phone_number,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            language=detect_language("")  # Will detect from first message
        )
    
    # Save updated session
    redis_client.setex(
        session_key,
        settings.session_timeout,
        json.dumps(session.dict(), default=str)
    )
    
    return session

async def update_session(session: PatientSession):
    """Update patient session"""
    if not redis_client:
        return
    
    session_key = f"session:{session.phone_number}"
    redis_client.setex(
        session_key,
        settings.session_timeout,
        json.dumps(session.dict(), default=str)
    )

async def check_rate_limit(phone_number: str) -> bool:
    """Check if user has exceeded rate limit"""
    if not redis_client:
        return True  # Skip rate limiting if Redis is unavailable
    
    rate_key = f"rate_limit:{phone_number}"
    current_count = redis_client.get(rate_key)
    
    if current_count and int(current_count) >= settings.rate_limit_messages:
        return False
    
    # Increment counter
    redis_client.incr(rate_key)
    redis_client.expire(rate_key, settings.rate_limit_window)
    return True

async def call_dedan_api(session: PatientSession, symptoms: str) -> Dict[str, Any]:
    """Call DEDAN HealthEngine API"""
    try:
        # Create minimal patient profile for messaging
        patient_profile = {
            "age": 30,  # Default age - will ask for clarification if needed
            "sex": "other",  # Default - will ask for clarification if needed
            "language": session.language,
            "chronic_conditions": session.patient_profile.get("chronic_conditions", []) if session.patient_profile else []
        }
        
        triage_request = {
            "patient": patient_profile,
            "symptoms": {
                "symptoms": symptoms,
                "voice_input": False
            },
            "session_id": session.session_id,
            "consent": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.dedan_api_url}/dedan/v1/triage",
                json=triage_request
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"DEDAN API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error calling DEDAN API: {e}")
        return None

def format_response_for_sms(triage_response: Dict[str, Any], language: str) -> str:
    """Format triage response for SMS-friendly output"""
    triage_level = triage_response.get("triage_level", "routine")
    summary = triage_response.get("patient_summary", "")
    next_step = triage_response.get("suggested_next_step", "")
    
    # Create SMS-friendly response
    if triage_level == "emergency":
        response = f"🚨 DEDAN says: EMERGENCY. {next_step} Go to nearest hospital immediately."
    elif triage_level == "urgent":
        response = f"⚠️ DEDAN says: URGENT. {next_step} See a doctor within 24 hours."
    elif triage_level == "routine":
        response = f"🟢 DEDAN says: ROUTINE. {next_step} Monitor symptoms."
    else:
        response = f"🔵 DEDAN says: SELF-CARE. {next_step}"
    
    # Add disclaimer
    response += " This is not medical advice. See a doctor if symptoms persist."
    
    return truncate_message(response, settings.max_message_length)

def get_welcome_message(language: str) -> str:
    """Get welcome message in appropriate language"""
    messages = {
        "en": "Welcome to DEDAN Health! I'm your AI medical assistant. Please describe your symptoms (e.g., 'I have headache and fever').",
        "sw": "Karibu DEDAN Health! Msaada wako wa matibabu ya AI. Tafadhali eleza dalili zako (k.m., 'Nina maumivu ya kichwa na homa').",
        "am": "እንኳል ወደ ዴዳን ሃልጥ! የሕክምነት እገዛ ነፃ። እባክሮ የህመምዎን ይግለጹ።"
    }
    
    return truncate_message(messages.get(language, messages["en"]), settings.max_message_length)

def get_clarification_message(language: str) -> str:
    """Get message asking for more information"""
    messages = {
        "en": "I need more information. Please tell me: 1) Your age 2) Your sex (M/F) 3) Main symptoms",
        "sw": "Nahitaji maelezo zaidi. Tafadhali niambie: 1) Umri wako 2) Jinsia yako (M/F) 3) Dalili kuu",
        "am": "ተጨማሪ መረጃ ይፈለጋል። እባክሮ: 1) ዕድመህ 2) ጾታህ 3) ዋናዎችዎ"
    }
    
    return truncate_message(messages.get(language, messages["en"]), settings.max_message_length)

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "DEDAN Messaging Backend",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "connected" if redis_client else "disconnected"
    twilio_status = "configured" if settings.twilio_account_sid else "not_configured"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "twilio": twilio_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp messages via Twilio"""
    try:
        # Parse form data
        form_data = await request.form()
        
        message = IncomingMessage(
            From=form_data.get("From", ""),
            Body=form_data.get("Body", ""),
            MessageSid=form_data.get("MessageSid"),
            AccountSid=form_data.get("AccountSid")
        )
        
        # Normalize phone number
        phone_number = normalize_phone_number(message.From)
        
        # Check rate limit
        if not await check_rate_limit(phone_number):
            response = MessagingResponse()
            response.message("You've reached the message limit. Please try again later.")
            return {"Content-Type": "text/xml", "body": str(response)}
        
        # Get or create session
        session = await get_or_create_session(phone_number)
        
        # Detect language if first message
        if session.message_count == 0:
            session.language = detect_language(message.Body)
        
        session.message_count += 1
        await update_session(session)
        
        # Check for emergency keywords
        if check_emergency_keywords(message.Body, session.language):
            emergency_response = "🚨 EMERGENCY DETECTED! Call emergency services immediately or go to nearest hospital. Emergency: 911"
            response = MessagingResponse()
            response.message(emergency_response)
            return {"Content-Type": "text/xml", "body": str(response)}
        
        # Handle message based on session state
        if session.message_count == 1:
            # First message - send welcome
            welcome_msg = get_welcome_message(session.language)
            response = MessagingResponse()
            response.message(welcome_msg)
            return {"Content-Type": "text/xml", "body": str(response)}
        
        elif not session.patient_profile and session.message_count == 2:
            # Second message - try to extract basic info
            # Simple pattern matching for age/sex
            age_match = re.search(r'(\d+)\s*(years?|yrs?|y)?', message.Body.lower())
            sex_match = re.search(r'\b(male|female|m|f)\b', message.Body.lower())
            
            if age_match or sex_match:
                # Extract info
                age = int(age_match.group(1)) if age_match else None
                sex = "male" if sex_match and sex_match.group(1) in ["male", "m"] else "female" if sex_match and sex_match.group(1) in ["female", "f"] else None
                
                session.patient_profile = {
                    "age": age or 30,  # Default if not found
                    "sex": sex or "other"
                }
                await update_session(session)
                
                # Now process the actual symptoms
                symptoms_text = message.Body
                triage_result = await call_dedan_api(session, symptoms_text)
                
                if triage_result:
                    response_text = format_response_for_sms(triage_result, session.language)
                else:
                    response_text = "Sorry, I'm having trouble processing your request. Please try again later."
                
                response = MessagingResponse()
                response.message(response_text)
                return {"Content-Type": "text/xml", "body": str(response)}
            else:
                # Ask for clarification
                clarification_msg = get_clarification_message(session.language)
                response = MessagingResponse()
                response.message(clarification_msg)
                return {"Content-Type": "text/xml", "body": str(response)}
        
        else:
            # Process symptoms normally
            symptoms_text = message.Body
            triage_result = await call_dedan_api(session, symptoms_text)
            
            if triage_result:
                response_text = format_response_for_sms(triage_result, session.language)
            else:
                response_text = "Sorry, I'm having trouble processing your request. Please try again later."
            
            response = MessagingResponse()
            response.message(response_text)
            return {"Content-Type": "text/xml", "body": str(response)}
    
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        response = MessagingResponse()
        response.message("Sorry, an error occurred. Please try again.")
        return {"Content-Type": "text/xml", "body": str(response)}

@app.post("/webhook/sms")
async def sms_webhook(request: Request):
    """Handle incoming SMS messages (similar to WhatsApp)"""
    # Similar logic to WhatsApp webhook
    return await whatsapp_webhook(request, BackgroundTasks())

@app.post("/send")
async def send_message(message: OutgoingMessage):
    """Send outgoing message via Twilio"""
    try:
        twilio_message = twilio_client.messages.create(
            body=message.body,
            from_=settings.twilio_phone_number,
            to=message.to,
            media_url=message.media_url
        )
        
        return {
            "success": True,
            "message_sid": twilio_message.sid,
            "status": twilio_message.status
        }
    
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@app.get("/sessions/{phone_number}")
async def get_session(phone_number: str):
    """Get session information for a phone number"""
    normalized_phone = normalize_phone_number(phone_number)
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Session storage unavailable")
    
    session_key = f"session:{normalized_phone}"
    session_data = redis_client.get(session_key)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return json.loads(session_data)

@app.delete("/sessions/{phone_number}")
async def delete_session(phone_number: str):
    """Delete session for a phone number"""
    normalized_phone = normalize_phone_number(phone_number)
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Session storage unavailable")
    
    session_key = f"session:{normalized_phone}"
    redis_client.delete(session_key)
    
    return {"success": True, "message": "Session deleted"}

@app.get("/stats")
async def get_stats():
    """Get messaging service statistics"""
    if not redis_client:
        return {"error": "Session storage unavailable"}
    
    try:
        # Count active sessions
        session_keys = redis_client.keys("session:*")
        active_sessions = len(session_keys)
        
        # Count rate limited users
        rate_keys = redis_client.keys("rate_limit:*")
        rate_limited_users = len(rate_keys)
        
        return {
            "active_sessions": active_sessions,
            "rate_limited_users": rate_limited_users,
            "supported_languages": list(EMERGENCY_KEYWORDS.keys()),
            "max_message_length": settings.max_message_length,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"error": "Failed to get statistics"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
