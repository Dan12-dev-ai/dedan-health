import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai

# Try to import langchain, but make it optional so the engine works without it
try:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

import numpy as np

from models import (
    TriageRequest, TriageResponse, TriageLevel, RiskFlag, 
    PatientProfile, SymptomInput, ClinicalGuideline, Language
)

class DEDANHealthEngine:
    """
    Digital Empathy-Driven AI Navigator - Core AI Engine
    """
    
    def __init__(self):
        self.openai_client = None
        self.embeddings = None
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key and api_key != "dummy-key-for-development":
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
            except Exception:
                self.openai_client = None
        
        if LANGCHAIN_AVAILABLE:
            try:
                self.embeddings = OpenAIEmbeddings(openai_api_key=api_key or "dummy")
            except Exception:
                self.embeddings = None
        
        self.vector_store = None
        self.emergency_keywords = self._load_emergency_keywords()
        self.clinical_guidelines = {}
        self._initialize_knowledge_base()
    
    def _load_emergency_keywords(self) -> Dict[str, List[str]]:
        """Load emergency symptom keywords across languages"""
        return {
            "en": [
                "chest pain", "heart attack", "difficulty breathing", "shortness of breath",
                "severe bleeding", "unconscious", "fainting", "seizure", "stroke symptoms",
                "pregnancy emergency", "labor", "severe headache", "vision loss",
                "suicidal", "self harm", "overdose"
            ],
            "sw": [
                "maumivu ya kifua", "shida ya kupumua", "kuchoka kupumua",
                "kuumwa kichwa sana", "kutopata fahamu", "matatizo ya uzazi"
            ],
            "am": [
                "እግረኛ ህመም", "እስከ ሞት የሚያስከትል", "እስከ ሞት የሚያስከትል ህመም",
                "ከፍተኛ ደም መፍሰስ", "ማስታወሻ መቀዘቅ", "የልጅ ማረግ አደጋ"
            ]
        }
    
    def _initialize_knowledge_base(self):
        """Initialize the RAG knowledge base with clinical guidelines"""
        if not LANGCHAIN_AVAILABLE:
            print("Warning: langchain not available, skipping vector store initialization")
            self.vector_store = None
            return
            
        try:
            # Load clinical guidelines from data directory
            guidelines_path = os.getenv("CLINICAL_GUIDELINES_PATH", "../data/clinical_guidelines/")
            if os.path.exists(guidelines_path):
                self._load_clinical_guidelines(guidelines_path)
            
            # Initialize vector store with sample guidelines
            sample_documents = self._create_sample_guidelines()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(sample_documents)
            
            self.vector_store = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings,
                collection_name="dedan_clinical_guidelines"
            )
        except Exception as e:
            print(f"Warning: Could not initialize knowledge base: {e}")
            self.vector_store = None
    
    def _load_clinical_guidelines(self, path: str):
        """Load clinical guidelines from files"""
        for filename in os.listdir(path):
            if filename.endswith('.json'):
                with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                    guidelines = json.load(f)
                    for guideline in guidelines:
                        self.clinical_guidelines[guideline['condition']] = guideline
    
    def _create_sample_guidelines(self) -> List[Document]:
        """Create sample clinical guidelines for demonstration"""
        sample_texts = [
            Document(
                page_content="WHO Guidelines: Chest pain requires immediate emergency evaluation. Possible causes include heart attack, pulmonary embolism, or aortic dissection.",
                metadata={"source": "WHO", "condition": "chest_pain", "urgency": "emergency"}
            ),
            Document(
                page_content="Fever in adults: Self-care for mild fever (<38.5°C). Seek medical attention if fever >39°C or persists >3 days.",
                metadata={"source": "WHO", "condition": "fever", "urgency": "routine"}
            ),
            Document(
                page_content="Pregnancy emergencies: Vaginal bleeding, severe abdominal pain, decreased fetal movement require immediate medical attention.",
                metadata={"source": "WHO", "condition": "pregnancy_emergency", "urgency": "emergency"}
            ),
            Document(
                page_content="Diabetes management: Hypoglycemia (low blood sugar) requires immediate glucose intake. Hyperglycemia may need medical attention if severe.",
                metadata={"source": "WHO", "condition": "diabetes", "urgency": "urgent"}
            )
        ]
        return sample_texts
    
    def _check_emergency_keywords(self, symptoms: str, language: str) -> List[RiskFlag]:
        """Check for emergency keywords in symptoms"""
        risk_flags = []
        symptoms_lower = symptoms.lower()
        
        # Check emergency keywords
        emergency_words = self.emergency_keywords.get(language, self.emergency_keywords["en"])
        
        for keyword in emergency_words:
            if keyword in symptoms_lower:
                risk_flags.append(RiskFlag(
                    type="emergency_symptom",
                    severity="high",
                    description=f"Emergency symptom detected: {keyword}",
                    keywords=[keyword]
                ))
        
        return risk_flags
    
    def _retrieve_relevant_guidelines(self, symptoms: str) -> List[Dict[str, Any]]:
        """Retrieve relevant clinical guidelines using RAG"""
        if not self.vector_store:
            return []
        
        try:
            # Search for relevant guidelines
            docs = self.vector_store.similarity_search(symptoms, k=3)
            return [doc.metadata for doc in docs]
        except Exception as e:
            print(f"Error retrieving guidelines: {e}")
            return []
    
    def _generate_triage_prompt(self, request: TriageRequest, relevant_guidelines: List[Dict]) -> str:
        """Generate prompt for LLM triage decision"""
        language = request.patient.language.value
        
        prompt = f"""
You are DEDAN (Digital Empathy-Driven AI Navigator), an AI medical triage assistant for underserved regions.

PATIENT PROFILE:
- Age: {request.patient.age}
- Sex: {request.patient.sex}
- Location: {request.patient.location or 'Unknown'}
- Pregnancy Status: {request.patient.pregnancy_status}
- Chronic Conditions: {', '.join(request.patient.chronic_conditions)}
- Language: {language}

SYMPTOMS:
{request.symptoms.symptoms}
Duration: {request.symptoms.duration or 'Not specified'}
Severity: {request.symptoms.severity or 'Not specified'}

RELEVANT CLINICAL GUIDELINES:
{json.dumps(relevant_guidelines, indent=2) if relevant_guidelines else 'No specific guidelines found'}

TASK:
Analyze the symptoms and patient profile to determine triage level and next steps.

RESPOND WITH JSON:
{{
    "triage_level": "emergency|urgent|routine|self_care",
    "suggested_next_step": "Clear, actionable next step in patient's language",
    "patient_summary": "Simple explanation of the situation in patient's language",
    "confidence_score": 0.0-1.0,
    "follow_up_timeframe": "Recommended follow-up timeframe",
    "risk_analysis": "Brief analysis of key risk factors"
}}

SAFETY RULES:
1. Any chest pain + breathing difficulty = EMERGENCY
2. Pregnancy complications = EMERGENCY  
3. Severe bleeding = EMERGENCY
4. Unconsciousness = EMERGENCY
5. Suicidal thoughts = EMERGENCY
6. When in doubt, err on side of caution

IMPORTANT: Always include medical disclaimer. This is not a replacement for professional medical care.
"""
        return prompt
    
    def _call_llm_for_triage(self, prompt: str) -> Dict[str, Any]:
        """Call LLM for triage decision"""
        if self.openai_client is None:
            print("LLM call skipped: no OpenAI client available")
            return {
                "triage_level": "urgent",
                "suggested_next_step": "Please seek medical attention for proper evaluation.",
                "patient_summary": "Your symptoms require medical evaluation.",
                "confidence_score": 0.5,
                "follow_up_timeframe": "24 hours",
                "risk_analysis": "AI analysis unavailable. Please consult a healthcare provider."
            }
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("DEDAN_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are a medical AI triage assistant. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(os.getenv("DEDAN_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("DEDAN_MAX_TOKENS", "500"))
            )
            
            content = response.choices[0].message.content.strip()
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"LLM call failed: {e}")
            # Return safe default
            return {
                "triage_level": "urgent",
                "suggested_next_step": "Please seek medical attention for proper evaluation.",
                "patient_summary": "Your symptoms require medical evaluation.",
                "confidence_score": 0.5,
                "follow_up_timeframe": "24 hours",
                "risk_analysis": "Unable to complete full analysis due to technical issues."
            }
    
    def _get_localized_response(self, response_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Get localized response based on language"""
        # Simple localization - in production, use proper translation service
        if language == "sw":
            translations = {
                "emergency": "dharura",
                "urgent": "haraka", 
                "routine": "kawaida",
                "self_care": "ujitegemezi"
            }
            response_data["triage_level"] = translations.get(response_data["triage_level"], response_data["triage_level"])
        
        elif language == "am":
            # Amharic translations would go here
            pass
        
        return response_data
    
    def _determine_emergency_contacts(self, location: Optional[str]) -> List[str]:
        """Determine local emergency contacts"""
        # In production, this would use a location-based service
        default_contacts = [
            "Emergency: 911 or local emergency number",
            "Nearest hospital emergency department"
        ]
        
        if location and "ethiopia" in location.lower():
            return [
                "Ethiopia Emergency: 911",
                "Ambulance: 907"
            ]
        
        return default_contacts
    
    async def triage_patient(self, request: TriageRequest) -> TriageResponse:
        """Main triage function"""
        try:
            # Step 1: Check for emergency keywords
            risk_flags = self._check_emergency_keywords(
                request.symptoms.symptoms, 
                request.patient.language.value
            )
            
            # Step 2: Retrieve relevant guidelines
            relevant_guidelines = self._retrieve_relevant_guidelines(request.symptoms.symptoms)
            
            # Step 3: Generate triage prompt
            prompt = self._generate_triage_prompt(request, relevant_guidelines)
            
            # Step 4: Get LLM decision
            llm_response = self._call_llm_for_triage(prompt)
            
            # Step 5: Localize response
            localized_response = self._get_localized_response(
                llm_response, 
                request.patient.language.value
            )
            
            # Step 6: Determine triage level (override to emergency if risk flags present)
            triage_level = TriageLevel.EMERGENCY if risk_flags else TriageLevel(localized_response["triage_level"])
            
            # Step 7: Get emergency contacts if needed
            emergency_contacts = self._determine_emergency_contacts(request.patient.location) if triage_level == TriageLevel.EMERGENCY else None
            
            # Step 8: Create response
            response = TriageResponse(
                triage_level=triage_level,
                suggested_next_step=localized_response["suggested_next_step"],
                risk_flags=risk_flags,
                patient_summary=localized_response["patient_summary"],
                confidence_score=float(localized_response["confidence_score"]),
                emergency_contacts=emergency_contacts,
                follow_up_timeframe=localized_response.get("follow_up_timeframe"),
                disclaimer="DEDAN is not a replacement for professional medical care. Seek immediate medical attention for emergencies."
            )
            
            return response
            
        except Exception as e:
            print(f"Triage error: {e}")
            # Return safe default response
            return TriageResponse(
                triage_level=TriageLevel.URGENT,
                suggested_next_step="Please seek medical attention for proper evaluation.",
                risk_flags=[RiskFlag(
                    type="system_error",
                    severity="medium",
                    description="System error occurred during triage",
                    keywords=[]
                )],
                patient_summary="We encountered a technical issue. Please consult with a healthcare provider.",
                confidence_score=0.3,
                follow_up_timeframe="24 hours"
            )
    
    def get_supported_conditions(self, language: Language = Language.ENGLISH) -> List[str]:
        """Get list of supported conditions"""
        conditions = list(self.clinical_guidelines.keys())
        if not conditions:
            # Return sample conditions
            return [
                "Chest pain", "Fever", "Headache", "Abdominal pain", 
                "Pregnancy concerns", "Diabetes management", "Hypertension"
            ]
        return conditions
