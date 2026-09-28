import re
from typing import Dict, Any, List
from datetime import datetime
import json

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .base_agent import BaseDEDANAgent
try:
    from models_v2 import (
    AgentInput, AgentOutput, AgentType, TriageLevel, 
    TriageAgentInput, TriageAgentOutput, ChronicCondition
    )
except ImportError:  # pragma: no cover - package-relative fallback
    from ..models_v2 import (
    AgentInput, AgentOutput, AgentType, TriageLevel, 
    TriageAgentInput, TriageAgentOutput, ChronicCondition
    )

class TriageAgent(BaseDEDANAgent):
    """
    DEDAN Triage Agent - Core triage classification agent.
    Responsible for initial symptom assessment and triage level determination.
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_type=AgentType.TRIAGE, **kwargs)
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build specialized prompt template for triage assessment."""
        
        template = """
You are a medical triage AI assistant for DEDAN Health, serving underserved regions.
Your role is to assess patient symptoms and determine appropriate triage level.

MEDICAL TRIAGE LEVELS:
- EMERGENCY: Life-threatening conditions requiring immediate medical attention
- URGENT: Serious conditions needing medical attention within 24 hours  
- ROUTINE: Non-urgent conditions that can wait for scheduled appointment
- SELF_CARE: Minor conditions suitable for home treatment

ASSESSMENT CRITERIA:
1. Symptom severity and duration
2. Patient age and risk factors
3. Chronic conditions and medications
4. Regional disease patterns
5. Language and cultural context

PATIENT INFORMATION:
{patient_info}

SYMPTOMS:
{symptoms}

{language_context}

{region_context}

ANALYSIS INSTRUCTIONS:
1. Identify key symptoms and patterns
2. Consider patient demographics and chronic conditions
3. Apply regional disease knowledge
4. Determine appropriate triage level
5. List possible differential diagnoses
6. Recommend appropriate next steps

RESPONSE FORMAT:
Provide your analysis in this exact JSON format:
{{
    "triage_level": "emergency|urgent|routine|self_care",
    "differential_diagnoses": ["diagnosis1", "diagnosis2", "diagnosis3"],
    "recommended_tests": ["test1", "test2"],
    "next_step": "Specific recommended action",
    "reasoning": "Detailed medical reasoning",
    "confidence": 0.85
}}

IMPORTANT SAFETY RULES:
- Any chest pain + breathing difficulty = EMERGENCY
- Any loss of consciousness = EMERGENCY  
- Any severe bleeding = EMERGENCY
- Pregnancy + concerning symptoms = URGENT minimum
- Fever > 39°C + chronic illness = URGENT minimum

{chronic_care_info}

{home_measurements}

Respond with ONLY the JSON format above. Be thorough but concise.
"""
        
        return ChatPromptTemplate.from_template(template)
    
    def _process_agent_specific_logic(self, input_data: TriageAgentInput) -> Dict[str, Any]:
        """Process triage-specific logic and extract structured results."""
        
        # This will be populated by the LLM response
        # The actual processing happens in the LLM chain
        # This method can be used for additional rule-based processing
        
        import re  # ensure re is available in this scope
        symptoms_text = input_data.symptoms.symptoms.lower()
        patient = input_data.patient
        
        # Apply safety rules as fallback
        triage_level = self._apply_safety_rules(symptoms_text, patient)
        
        # Extract differential diagnoses based on symptoms
        differential_diagnoses = self._extract_differential_diagnoses(symptoms_text)
        
        # Recommended tests based on symptoms
        recommended_tests = self._recommend_tests(symptoms_text, triage_level)
        
        # Determine next step
        next_step = self._determine_next_step(triage_level, symptoms_text)
        
        return {
            "triage_level": triage_level,
            "differential_diagnoses": differential_diagnoses,
            "recommended_tests": recommended_tests,
            "next_step": next_step
        }
    
    def _apply_safety_rules(self, symptoms_text: str, patient) -> str:
        """Apply critical safety rules to determine minimum triage level."""
        
        import re  # ensure re is available in this scope
        
        # Emergency rules
        emergency_patterns = [
            r'chest\s*pain.*breath',
            r'breathing.*difficulty',
            r'shortness.*breath',
            r'unconscious',
            r'faint',
            r'seizure',
            r'stroke',
            r'bleeding.*severe',
            r'blood.*lot',
            r'head.*injury',
            r'broken.*bone'
        ]
        
        for pattern in emergency_patterns:
            if re.search(pattern, symptoms_text):
                return TriageLevel.EMERGENCY
        
        # Urgent rules
        urgent_patterns = [
            r'fever.*high',
            r'temperature.*39',
            r'pain.*severe',
            r'vomiting.*blood',
            r'diarrhea.*blood',
            r'pregnant.*pain',
            r'diabetes.*complication'
        ]
        
        for pattern in urgent_patterns:
            if re.search(pattern, symptoms_text):
                return TriageLevel.URGENT
        
        # Age-based urgency
        if patient.age > 75 and any(symptom in symptoms_text for symptom in ['confusion', 'fall', 'weakness']):
            return TriageLevel.URGENT
        
        # Pregnancy-based urgency
        if patient.pregnancy_status and any(symptom in symptoms_text for symptom in ['pain', 'bleeding', 'fever']):
            return TriageLevel.URGENT
        
        # Chronic condition urgency
        urgent_chronic_patterns = {
            ChronicCondition.DIABETES: ['confusion', 'breathing', 'sweet', 'fruity'],
            ChronicCondition.HYPERTENSION: ['headache', 'vision', 'chest', 'shortness'],
            ChronicCondition.HEART_DISEASE: ['chest', 'breathing', 'swelling'],
            ChronicCondition.ASTHMA: ['breathing', 'wheezing', 'shortness']
        }
        
        for condition in patient.chronic_conditions:
            patterns = urgent_chronic_patterns.get(condition, [])
            if any(pattern in symptoms_text for pattern in patterns):
                return TriageLevel.URGENT
        
        return TriageLevel.ROUTINE.value  # Default when no safety rules match
    
    def _extract_differential_diagnoses(self, symptoms_text: str) -> List[str]:
        """Extract possible differential diagnoses based on symptoms."""
        
        # Symptom to diagnosis mapping
        symptom_diagnosis_map = {
            'chest pain': ['Heart Attack', 'Angina', 'Pulmonary Embolism', 'Costochondritis'],
            'headache': ['Migraine', 'Tension Headache', 'Sinusitis', 'Meningitis'],
            'fever': ['Malaria', 'Typhoid', 'Flu', 'COVID-19', 'Dengue'],
            'cough': ['Bronchitis', 'Pneumonia', 'COVID-19', 'Asthma'],
            'stomach pain': ['Gastritis', 'Appendicitis', 'Food Poisoning', 'Ulcer'],
            'diarrhea': ['Gastroenteritis', 'Food Poisoning', 'IBS', 'Infection'],
            'breathing difficulty': ['Asthma', 'Pneumonia', 'Heart Failure', 'Anxiety'],
            'dizziness': ['Anemia', 'Dehydration', 'Vertigo', 'Low Blood Pressure'],
            'rash': ['Allergic Reaction', 'Viral Infection', 'Eczema', 'Fungal Infection']
        }
        
        diagnoses = []
        for symptom, possible_diagnoses in symptom_diagnosis_map.items():
            if symptom in symptoms_text:
                diagnoses.extend(possible_diagnoses)
        
        # Remove duplicates and limit to top 5
        return list(set(diagnoses))[:5]
    
    def _recommend_tests(self, symptoms_text: str, triage_level: str) -> List[str]:
        """Recommend appropriate diagnostic tests."""
        
        test_recommendations = {
            'emergency': ['ECG', 'Blood Tests', 'Chest X-ray', 'CT Scan'],
            'urgent': ['Blood Tests', 'X-ray', 'Urine Test', 'ECG'],
            'routine': ['Blood Tests', 'Urine Test', 'Basic Imaging'],
            'self_care': ['Home Monitoring', 'Follow-up if worsens']
        }
        
        # Symptom-specific tests
        symptom_tests = {
            'chest pain': ['ECG', 'Troponin Test', 'Chest X-ray'],
            'headache': ['CT Scan', 'MRI', 'Blood Pressure Check'],
            'fever': ['Blood Culture', 'Malaria Test', 'COVID-19 Test'],
            'stomach pain': ['Abdominal X-ray', 'Ultrasound', 'Blood Tests'],
            'breathing difficulty': ['Pulse Oximetry', 'Chest X-ray', 'Blood Tests']
        }
        
        base_tests = test_recommendations.get(triage_level, [])
        
        # Add symptom-specific tests
        for symptom, tests in symptom_tests.items():
            if symptom in symptoms_text:
                base_tests.extend(tests)
        
        # Remove duplicates and limit to 6
        return list(set(base_tests))[:6]
    
    def _determine_next_step(self, triage_level: str, symptoms_text: str) -> str:
        """Determine appropriate next step based on triage level."""
        
        next_steps = {
            'emergency': "Go to nearest emergency department immediately. Call emergency services if available.",
            'urgent': "Seek medical attention within 24 hours. Contact your local clinic or hospital.",
            'routine': "Schedule appointment with healthcare provider within 1-2 weeks.",
            'self_care': "Monitor symptoms at home. Seek medical care if symptoms worsen or persist."
        }
        
        base_step = next_steps.get(triage_level, next_steps['routine'])
        
        # Add specific advice based on symptoms
        if 'fever' in symptoms_text:
            base_step += " Take fever-reducing medication if available and stay hydrated."
        elif 'pain' in symptoms_text:
            base_step += " Take pain medication if available and rest."
        elif 'breathing' in symptoms_text:
            base_step += " Sit upright and ensure good air circulation."
        
        return base_step
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate triage agent output."""
        
        required_fields = ['triage_level', 'differential_diagnoses', 'recommended_tests', 'next_step']
        
        for field in required_fields:
            if field not in output:
                return False
        
        # Validate triage level
        valid_levels = [level.value for level in TriageLevel]
        if output['triage_level'] not in valid_levels:
            return False
        
        # Validate lists
        if not isinstance(output['differential_diagnoses'], list):
            return False
        
        if not isinstance(output['recommended_tests'], list):
            return False
        
        # Validate next step is not empty
        if not output['next_step'] or len(output['next_step'].strip()) == 0:
            return False
        
        return True
