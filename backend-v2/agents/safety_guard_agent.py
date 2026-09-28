import re
from typing import Dict, Any, List
import json

from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseDEDANAgent
try:
    from models_v2 import (
    AgentInput, AgentOutput, AgentType,
    SafetyGuardAgentInput, SafetyGuardAgentOutput,
    TriageAgentOutput
    )
except ImportError:  # pragma: no cover - package-relative fallback
    from ..models_v2 import (
    AgentInput, AgentOutput, AgentType,
    SafetyGuardAgentInput, SafetyGuardAgentOutput,
    TriageAgentOutput
    )

class SafetyGuardAgent(BaseDEDANAgent):
    """
    DEDAN Safety Guard Agent - Emergency detection and safety validation.
    Re-checks triage decisions using strict safety rules.
    """
    
    def __init__(self, **kwargs):
        # The safety guard is deliberately low-temperature for deterministic
        # re-checking. The coordinator forwards its own temperature via
        # **kwargs, which would collide with an explicit `temperature=0.1`
        # argument, so consume it here rather than letting it through.
        kwargs.pop("temperature", None)
        super().__init__(agent_type=AgentType.SAFETY_GUARD, temperature=0.1, **kwargs)
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build specialized prompt template for safety assessment."""
        
        template = """
You are a medical safety guard AI for DEDAN Health.
Your role is to re-check triage decisions and identify any missed emergencies or safety concerns.

SAFETY PRIORITY RULES:
1. ANY chest pain + breathing difficulty = EMERGENCY (possible heart attack)
2. ANY loss of consciousness = EMERGENCY (possible stroke, head injury)
3. ANY severe bleeding = EMERGENCY (hemorrhage risk)
4. ANY seizure activity = EMERGENCY (status epilepticus)
5. Pregnancy + concerning symptoms = URGENT minimum
6. Elderly (>65) + confusion/weakness = URGENT minimum
7. Chronic disease + new severe symptoms = URGENT minimum

EMERGENCY SYMPTOM PATTERNS:
- Chest pain radiating to arm/jaw + sweating + nausea
- Sudden severe headache + confusion + vision changes
- Difficulty breathing + inability to speak
- Uncontrolled bleeding
- Loss of consciousness
- Seizure lasting >5 minutes

HIGH-RISK COMBINATIONS:
- Fever + chronic illness (diabetes, HIV, heart disease)
- Pain + swelling + redness (possible infection)
- Weakness + numbness + confusion (possible stroke)
- Shortness of breath + chest pain (possible heart failure)

PATIENT INFORMATION:
{patient_info}

SYMPTOMS:
{symptoms}

TRIAGE ASSESSMENT TO VERIFY:
{triage_output}

{language_context}

{region_context}

SAFETY ANALYSIS INSTRUCTIONS:
1. Cross-check symptoms against ALL safety rules
2. Look for red flag combinations
3. Consider patient age and chronic conditions
4. Verify emergency detection accuracy
5. Identify any missed safety concerns

RESPONSE FORMAT:
Provide your analysis in this exact JSON format:
{{
    "emergency_detected": true/false,
    "emergency_type": "heart_attack|stroke|bleeding|seizure|respiratory|other|null",
    "safety_concerns": ["concern1", "concern2", "concern3"],
    "requires_immediate_action": true/false,
    "recommended_action": "Specific safety action",
    "reasoning": "Detailed safety reasoning",
    "confidence": 0.95
}}

CRITICAL: If ANY emergency pattern is detected, you MUST set emergency_detected=true and requires_immediate_action=true.
Never downgrade a potential emergency to a lower priority.

{chronic_care_info}

{home_measurements}

Respond with ONLY JSON format above. Prioritize patient safety above all else.
"""
        
        return ChatPromptTemplate.from_template(template)
    
    def _process_agent_specific_logic(self, input_data: SafetyGuardAgentInput) -> Dict[str, Any]:
        """Process safety guard specific logic."""
        
        symptoms_text = input_data.symptoms.symptoms.lower()
        patient = input_data.patient
        triage_output = input_data.triage_output
        
        # Apply comprehensive safety rules
        emergency_result = self._check_emergency_patterns(symptoms_text, patient)
        
        # Additional safety concerns
        safety_concerns = self._identify_safety_concerns(symptoms_text, patient, triage_output)
        
        # Determine if immediate action is required
        requires_immediate_action = emergency_result['detected'] or self._requires_immediate_action(safety_concerns)
        
        # Recommended action
        recommended_action = self._get_recommended_action(emergency_result, safety_concerns)
        
        return {
            "emergency_detected": emergency_result['detected'],
            "emergency_type": emergency_result['type'],
            "safety_concerns": safety_concerns,
            "requires_immediate_action": requires_immediate_action,
            "recommended_action": recommended_action
        }
    
    def _check_emergency_patterns(self, symptoms_text: str, patient) -> Dict[str, Any]:
        """Check for emergency symptom patterns."""
        
        emergency_patterns = {
            'heart_attack': {
                'patterns': [
                    r'chest.*pain.*arm',
                    r'chest.*pain.*jaw',
                    r'chest.*pain.*sweat',
                    r'chest.*pain.*nausea',
                    r'pressure.*chest'
                ],
                'description': 'Possible heart attack'
            },
            'stroke': {
                'patterns': [
                    r'sudden.*headache',
                    r'headache.*vision',
                    r'headache.*confusion',
                    r'weakness.*numbness',
                    r'slurred.*speech',
                    r'face.*droop'
                ],
                'description': 'Possible stroke'
            },
            'respiratory': {
                'patterns': [
                    r'breathing.*difficulty',
                    r'shortness.*breath',
                    r'cannot.*breathe',
                    r'chest.*tightness',
                    r'wheezing.*severe'
                ],
                'description': 'Respiratory emergency'
            },
            'bleeding': {
                'patterns': [
                    r'bleeding.*severe',
                    r'blood.*lot',
                    r'uncontrolled.*bleed',
                    r'vomit.*blood',
                    r'cough.*blood'
                ],
                'description': 'Severe bleeding'
            },
            'seizure': {
                'patterns': [
                    r'seizure',
                    r'convulsion',
                    r'fit',
                    r'unconscious.*shaking'
                ],
                'description': 'Seizure activity'
            },
            'head_injury': {
                'patterns': [
                    r'head.*injury',
                    r'fall.*head',
                    r'hit.*head',
                    r'confusion.*head'
                ],
                'description': 'Head injury'
            }
        }
        
        for emergency_type, details in emergency_patterns.items():
            for pattern in details['patterns']:
                if re.search(pattern, symptoms_text):
                    return {
                        'detected': True,
                        'type': emergency_type,
                        'description': details['description']
                    }
        
        # Additional emergency checks
        if 'unconscious' in symptoms_text or 'faint' in symptoms_text:
            return {
                'detected': True,
                'type': 'unconscious',
                'description': 'Loss of consciousness'
            }
        
        return {'detected': False, 'type': None, 'description': None}
    
    def _identify_safety_concerns(self, symptoms_text: str, patient, triage_output: TriageAgentOutput) -> List[str]:
        """Identify additional safety concerns."""
        
        concerns = []
        
        # Age-related concerns
        if patient.age > 75 and any(symptom in symptoms_text for symptom in ['confusion', 'fall', 'weakness']):
            concerns.append('elderly_fall_risk')
        
        # Pregnancy concerns
        if patient.pregnancy_status:
            if any(symptom in symptoms_text for symptom in ['bleeding', 'pain', 'fever', 'dizziness']):
                concerns.append('pregnancy_complication')
        
        # Chronic disease concerns
        chronic_concerns = {
            'diabetes': ['confusion', 'sweet', 'fruity', 'breathing'],
            'hypertension': ['headache', 'vision', 'chest', 'shortness'],
            'heart_disease': ['chest', 'breathing', 'swelling'],
            'asthma': ['breathing', 'wheezing', 'shortness'],
            'hiv': ['fever', 'weight_loss', 'opportunistic']
        }
        
        for condition in patient.chronic_conditions:
            if condition.value in chronic_concerns:
                symptoms = chronic_concerns[condition.value]
                if any(symptom in symptoms_text for symptom in symptoms):
                    concerns.append(f'chronic_{condition.value}_exacerbation')
        
        # Fever concerns
        if 'fever' in symptoms_text or 'temperature' in symptoms_text:
            if patient.age < 5 or patient.age > 65:
                concerns.append('fever_extreme_age')
            
            # High fever
            if any(temp in symptoms_text for temp in ['39', '40', '102', '103']):
                concerns.append('high_fever')
        
        # Pain concerns
        if 'pain' in symptoms_text:
            if any(severity in symptoms_text for severity in ['severe', 'worst', 'unbearable']):
                concerns.append('severe_pain')
        
        # Medication concerns
        if any(med in symptoms_text.lower() for med in ['missed', 'forgot', 'ran out']):
            concerns.append('medication_nonadherence')
        
        # Triage validation concerns
        if triage_output.triage_level == 'self_care':
            # Check if any emergency symptoms were missed
            emergency_symptoms = ['chest', 'breathing', 'unconscious', 'seizure', 'bleeding']
            if any(symptom in symptoms_text for symptom in emergency_symptoms):
                concerns.append('possible_undertriage')
        
        return list(set(concerns))
    
    def _requires_immediate_action(self, safety_concerns: List[str]) -> bool:
        """Determine if immediate action is required."""
        
        immediate_concerns = [
            'possible_undertriage',
            'pregnancy_complication',
            'elderly_fall_risk',
            'high_fever',
            'severe_pain',
            'chronic_disease_exacerbation'
        ]
        
        return any(concern in immediate_concerns for concern in safety_concerns)
    
    def _get_recommended_action(self, emergency_result: Dict[str, Any], safety_concerns: List[str]) -> str:
        """Get recommended safety action."""
        
        if emergency_result['detected']:
            return f"EMERGENCY: {emergency_result['description']}. Go to nearest emergency department immediately. Call emergency services if available."
        
        # Specific concern-based actions
        concern_actions = {
            'possible_undertriage': "IMMEDIATE: Symptoms suggest possible emergency. Re-evaluate triage level immediately.",
            'pregnancy_complication': "URGENT: Pregnancy-related symptoms require immediate medical evaluation.",
            'elderly_fall_risk': "URGENT: Elderly patient with fall symptoms needs medical evaluation.",
            'high_fever': "URGENT: High fever requires medical attention, especially in extreme ages.",
            'severe_pain': "URGENT: Severe pain needs medical evaluation.",
            'medication_nonadherence': "MONITOR: Address medication adherence issues with healthcare provider."
        }
        
        for concern in safety_concerns:
            if concern in concern_actions:
                return concern_actions[concern]
        
        return "MONITOR: Continue monitoring for worsening symptoms. Seek care if condition deteriorates."
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate safety guard agent output."""
        
        required_fields = [
            'emergency_detected', 'emergency_type', 'safety_concerns',
            'requires_immediate_action', 'recommended_action'
        ]
        
        for field in required_fields:
            if field not in output:
                return False
        
        # Validate boolean fields
        if not isinstance(output['emergency_detected'], bool):
            return False
        
        if not isinstance(output['requires_immediate_action'], bool):
            return False
        
        # Validate lists
        if not isinstance(output['safety_concerns'], list):
            return False
        
        # Validate emergency type
        if output['emergency_detected'] and not output['emergency_type']:
            return False
        
        # Validate recommended action
        if not output['recommended_action'] or len(output['recommended_action'].strip()) == 0:
            return False
        
        return True
