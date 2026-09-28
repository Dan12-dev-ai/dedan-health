"""
Clinical Context Builder — DEDAN Health 2.0

Builds comprehensive clinical context from multimodal patient input
for structured AI reasoning. Separates patient-reported facts from
AI observations and evidence.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from models_v2 import PatientProfile as ClinicalPatientProfile, SymptomInput
from clinical_schema import UrgencyLevel, EvidenceLevel
from visual_education_enhanced import visual_education_service
from medication_safety_enhanced import medication_safety_service
from evidence_retrieval_enhanced import evidence_retriever, EvidenceRetriever


@dataclass
class ImageAnalysisResult:
    """Structured result from image analysis."""
    observations: List[str] = field(default_factory=list)
    possible_explanations: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    requires_better_image: bool = False
    urgency_indicators: List[str] = field(default_factory=list)


@dataclass
class ClinicalContext:
    """Complete clinical context for AI reasoning."""
    patient_profile: ClinicalPatientProfile
    symptoms: SymptomInput
    image_analysis: Optional[ImageAnalysisResult] = None
    voice_transcript: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Evidence and references
    evidence: Dict[str, Any] = field(default_factory=dict)
    guidelines: Dict[str, Any] = field(default_factory=dict)
    
    # Safety
    urgency: UrgencyLevel = UrgencyLevel.SOON
    red_flags: List[str] = field(default_factory=list)
    safety_flags: List[str] = field(default_factory=list)


class ClinicalContextBuilder:
    """Builds clinical context from multimodal inputs."""
    
    def __init__(
        self,
        evidence_retriever: Optional[EvidenceRetriever] = None,
        visual_service = None,
        medication_service = None,
    ):
        # Defer imports to avoid circular import issues
        from evidence_retrieval_enhanced import evidence_retriever as default_evidence_retriever
        from visual_education_enhanced import visual_education_service as default_visual_service
        from medication_safety_enhanced import medication_safety_service as default_medication_service
        
        self.evidence_retriever = evidence_retriever or default_evidence_retriever
        self.visual_service = visual_service or default_visual_service
        self.medication_service = medication_service or default_medication_service
    
    async def build(
        self,
        patient_profile: ClinicalPatientProfile,
        symptoms: SymptomInput,
        image_analysis: Optional[ImageAnalysisResult] = None,
        voice_transcript: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> ClinicalContext:
        """Build complete clinical context."""
        context = ClinicalContext(
            patient_profile=patient_profile,
            symptoms=symptoms,
            image_analysis=image_analysis,
            voice_transcript=voice_transcript,
            conversation_history=conversation_history or [],
            session_id=session_id or str(uuid.uuid4()),
        )
        
        # Retrieve evidence for symptoms and possible conditions
        context.evidence = await self._retrieve_evidence(context)
        
        # Retrieve relevant guidelines
        context.guidelines = await self._retrieve_guidelines(context)
        
        # Determine urgency from symptoms and image
        context.urgency = self._assess_urgency(context)
        
        # Extract red flags
        context.red_flags = self._extract_red_flags(context)
        
        return context
    
    async def _retrieve_evidence(self, context: ClinicalContext) -> Dict[str, Any]:
        """Retrieve medical evidence for symptoms and potential conditions."""
        evidence = {}
        
        # Evidence for main symptoms
        symptom_text = context.symptoms.symptoms or ""
        if symptom_text:
            evidence["symptoms"] = self.evidence_retriever.retrieve(
                symptom_text, 
                EvidenceLevel.MODERATE
            )
        
        # Evidence for image findings
        if context.image_analysis and context.image_analysis.possible_explanations:
            for exp in context.image_analysis.possible_explanations:
                condition = exp.get("condition", "")
                if condition:
                    evidence[f"image_{condition}"] = self.evidence_retriever.retrieve(
                        condition,
                        EvidenceLevel.MODERATE
                    )
        
        return evidence
    
    async def _retrieve_guidelines(self, context: ClinicalContext) -> Dict[str, Any]:
        """Retrieve relevant clinical guidelines."""
        guidelines = {}
        
        # Guidelines for possible conditions from image
        if context.image_analysis and context.image_analysis.possible_explanations:
            for exp in context.image_analysis.possible_explanations:
                condition = exp.get("condition", "")
                if condition:
                    guidelines[condition] = self.evidence_retriever.get_guideline_recommendations(
                        condition,
                        {
                            "patient_age": context.patient_profile.age,
                            "patient_location": context.patient_profile.location,
                            "pregnancy": context.patient_profile.pregnancy_status,
                        }
                    )
        
        return guidelines
    
    def _assess_urgency(self, context: ClinicalContext) -> UrgencyLevel:
        """Assess urgency from all available information."""
        # This integrates with urgency_engine
        # For now, return based on symptoms and image
        return UrgencyLevel.SOON
    
    def _extract_red_flags(self, context: ClinicalContext) -> List[str]:
        """Extract red flags from all sources."""
        red_flags = []
        
        # From symptoms
        symptom_text = (context.symptoms.symptoms or "").lower()
        emergency_keywords = [
            "chest pain", "difficulty breathing", "severe bleeding",
            "loss of consciousness", "stroke", "severe allergic",
            "suicidal", "confusion", "slurred speech", "facial drooping",
            "severe headache", "high fever with rash", "seizure",
            "severe abdominal pain", "vomiting blood", "black tarry stools",
            "severe dehydration", "unable to wake", "coughing blood",
        ]
        for kw in emergency_keywords:
            if kw in symptom_text:
                red_flags.append(f"Symptom: {kw}")
        
        # From image analysis
        if context.image_analysis:
            red_flags.extend(context.image_analysis.urgency_indicators)
        
        # Patient risk factors
        if context.patient_profile.pregnancy_status:
            red_flags.append("Pregnant patient")
        if context.patient_profile.age and (context.patient_profile.age < 5 or context.patient_profile.age > 75):
            red_flags.append(f"Age risk: {context.patient_profile.age}")
        if context.patient_profile.chronic_conditions:
            for cc in context.patient_profile.chronic_conditions:
                red_flags.append(f"Chronic condition: {cc}")
        
        return red_flags


def build_gemini_system_prompt(context: ClinicalContext) -> str:
    """Build the system prompt for Gemini with full clinical context."""
    
    # Build patient context section
    patient_parts = []
    if context.patient_profile.age:
        patient_parts.append(f"Age: {context.patient_profile.age}")
    if context.patient_profile.sex:
        patient_parts.append(f"Sex: {context.patient_profile.sex}")
    if context.patient_profile.location:
        patient_parts.append(f"Location: {context.patient_profile.location}")
    if context.patient_profile.pregnancy_status:
        patient_parts.append("Pregnant: Yes")
    if context.patient_profile.chronic_conditions:
        patient_parts.append(f"Chronic conditions: {', '.join(context.patient_profile.chronic_conditions)}")
    if context.patient_profile.medications:
        patient_parts.append(f"Current medications: {', '.join(context.patient_profile.medications)}")
    if context.patient_profile.allergies:
        patient_parts.append(f"Allergies: {', '.join(context.patient_profile.allergies)}")
    
    patient_context = "\n".join(patient_parts) if patient_parts else "No patient context provided"
    
    # Build symptom context
    symptom_parts = []
    if context.symptoms.symptoms:
        symptom_parts.append(f"Symptoms: {context.symptoms.symptoms}")
    if context.symptoms.duration:
        symptom_parts.append(f"Duration: {context.symptoms.duration}")
    if context.symptoms.severity:
        symptom_parts.append(f"Severity: {context.symptoms.severity}")
    if context.voice_transcript:
        symptom_parts.append(f"Voice input: {context.voice_transcript}")
    
    symptom_context = "\n".join(symptom_parts) if symptom_parts else "No symptoms reported"
    
    # Build image context
    image_context = ""
    if context.image_analysis:
        img_parts = []
        if context.image_analysis.observations:
            img_parts.append("OBSERVATIONS (what is visible):\n" + "\n".join(f"- {o}" for o in context.image_analysis.observations))
        if context.image_analysis.possible_explanations:
            img_parts.append("POSSIBLE EXPLANATIONS (interpretations, not diagnoses):\n" + 
                "\n".join(f"- {e.get('condition', 'Unknown')}: {e.get('reasoning', 'No reasoning provided')} (confidence: {e.get('confidence', 0)})" 
                for e in context.image_analysis.possible_explanations))
        if context.image_analysis.limitations:
            img_parts.append("LIMITATIONS:\n" + "\n".join(f"- {l}" for l in context.image_analysis.limitations))
        if context.image_analysis.quality_score:
            img_parts.append(f"Image quality score: {context.image_analysis.quality_score:.2f}/1.0")
        
        image_context = "\n\nIMAGE ANALYSIS:\n" + "\n\n".join(img_parts)
    
    # Build evidence context
    evidence_context = ""
    if context.evidence:
        ev_parts = []
        for key, ev in context.evidence.items():
            if isinstance(ev, dict) and ev.get("sources"):
                ev_parts.append(f"{key}: {len(ev['sources'])} sources from {', '.join(set(s.type for s in ev['sources']))}")
        if ev_parts:
            evidence_context = "\n\nAVAILABLE EVIDENCE:\n" + "\n".join(ev_parts)
    
    # Build guidelines context
    guidelines_context = ""
    if context.guidelines:
        gl_parts = []
        for condition, gl in context.guidelines.items():
            if isinstance(gl, dict) and gl.get("key_recommendations"):
                gl_parts.append(f"{condition}: {', '.join(gl['key_recommendations'][:3])}")
        if gl_parts:
            guidelines_context = "\n\nRELEVANT GUIDELINES:\n" + "\n".join(gl_parts)
    
    # Build conversation history
    conv_context = ""
    if context.conversation_history:
        recent = context.conversation_history[-6:]  # Last 6 turns
        conv_lines = []
        for turn in recent:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if content:
                conv_lines.append(f"[{role.upper()}]: {content}")
        if conv_lines:
            conv_context = "\n\nCONVERSATION HISTORY:\n" + "\n".join(conv_lines)
    
    return f"""You are DEDAN Health's medical AI assistant. Analyze the patient's input (text, images, voice) and provide structured medical guidance.

PATIENT CONTEXT:
{patient_context}

CURRENT SYMPTOMS:
{symptom_context}
{image_context}
{evidence_context}
{guidelines_context}
{conv_context}

CRITICAL RULES - NEVER VIOLATE:
1. NEVER claim certainty from visual evidence alone. Use "may be consistent with", "cannot be reliably determined", "suggests".
2. Distinguish OBSERVATION (what you see) from INTERPRETATION (what it might mean).
3. Always include uncertainty and limitations.
4. Ground treatment information in verified medical sources (WHO, CDC, national guidelines).
5. Escalate to professional review when uncertain or high-risk.
6. NEVER prescribe specific dosages or brand names.
7. ALWAYS include strong medical disclaimers.
8. NEVER diagnose - only suggest possible conditions with confidence levels.
9. Separate what the patient reported from what AI observed.
10. Explicitly state what is UNKNOWN vs what is KNOWN.

OUTPUT FORMAT (JSON only, no markdown):
{{
  "urgency": "emergency|see_doctor_soon|self_care",
  "recommended_next_step": "specific actionable guidance",
  "urgency_reasoning": "why this urgency level",
  "possible_conditions": [
    {{
      "name": "condition name",
      "confidence": "high|medium|low",
      "confidence_score": 0.0-1.0,
      "reasoning": "why this condition is possible",
      "supporting_evidence": ["finding 1", "finding 2"],
      "contradicting_evidence": ["finding that doesn't fit"],
      "requires_more_info": ["info needed to confirm"]
    }}
  ],
  "symptom_analysis": {{
    "key_symptoms": ["symptom1", "symptom2"],
    "what_they_suggest": "explanation of symptom significance",
    "missing_information": ["info needed for better assessment"],
  }},
  "image_analysis": {{
    "observations": ["visible finding 1", "visible finding 2"],
    "possible_explanations": [
      {{"condition": "condition name", "likelihood": "possible|likely|unlikely", "confidence": 0.0-1.0, "reasoning": "why", "citations": ["source1"]}}
    ],
    "limitations": ["limitation 1", "limitation 2"],
    "requires_better_image": false,
    "quality_issues": []
  }},
  "body_mechanism": [
    {{"step_number": 1, "title": "step title", "description": "what happens in the body", "visual_reference": "optional_reference"}}
  ],
  "treatment_approach": {{
    "goal": "what treatment is trying to achieve",
    "mechanism": "biological mechanism at patient-friendly level",
    "patient_actions": ["what patient can generally do"],
    "professional_actions": ["what requires clinician"],
    "expected_improvement": "what improvement looks like",
    "timeline": "evidence-based timeline",
    "warning_signs": ["deterioration indicators"]
  }},
  "treatment_education": [
    {{
      "category": "self_care|medication|procedure|lifestyle",
      "title": "treatment title",
      "description": "what this treatment involves",
      "why_it_may_help": "mechanism of benefit",
      "expected_timeline": "when to expect improvement",
      "what_to_monitor": "what to watch",
      "when_to_reassess": "when to seek further care",
      "evidence_level": "strong|moderate|limited|expert_opinion",
      "sources": [{{"title": "", "url": "", "type": "guideline|pubmed|textbook", "jurisdiction": ""}}]
    }}
  ],
  "medication_information": [
    {{
      "medication_name": "generic name",
      "medication_class": "class name",
      "general_purpose": "what it treats",
      "common_warnings": ["warning 1"],
      "contraindication_categories": ["when not to use"],
      "potential_interactions": ["interaction 1"],
      "questions_to_ask": ["question for pharmacist"],
      "package_check_items": ["what to check on package"]
    }}
  ],
  "medication_verification": [
    {{"field": "active_ingredient", "description": "what to check", "why_important": "reason"}}
  ],
  "visual_education": [
    {{"title": "visual title", "description": "what it shows", "visual_type": "type", "source": "source name", "medical_context": "context"}}
  ],
  "warning_signs": ["sign 1", "sign 2"],
  "follow_up": {{
    "recommended": true,
    "timeframe": "when to follow up",
    "warning_signs": ["sign 1", "sign 2"]
  }},
  "next_steps": {{
    "immediate": ["do now"],
    "within_hours": ["do within 24h"],
    "within_days": ["do within 3-7 days"],
    "follow_up_with": "who to follow up with"
  }},
  "uncertainty": "explicit uncertainty statement",
  "requires_professional_review": true/false,
  "safety_notice": "standard medical disclaimer",
  "confidence_score": 0.0-1.0,
  "safety_flags": ["flag1", "flag2"]
}}"""


# Global builder instance
clinical_context_builder = ClinicalContextBuilder()