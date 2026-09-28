#!/usr/bin/env python
"""
Test mode runner - uses mock AI providers for testing without real API keys.
"""
import os
os.environ['GEMINI_API_KEY'] = 'test-key'
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['ANTHROPIC_API_KEY'] = 'test-key'
os.environ['DEFAULT_AI_PROVIDER'] = 'gemini'

import sys
import types

# Mock agent modules BEFORE importing main
for mod_name in [
    'agents.coordinator_agent', 'agents.triage_agent', 'agents.safety_guard_agent',
    'agents.guideline_agent', 'agents.risk_prediction_agent', 'agents.base_agent',
    'data_flywheel'
]:
    mod = types.ModuleType(mod_name)
    if 'coordinator' in mod_name:
        class MockCoordinatorAgent:
            def __init__(self, **kwargs): pass
            def get_agent_capabilities(self): return {}
        mod.CoordinatorAgent = MockCoordinatorAgent
    if 'flywheel' in mod_name:
        class MockDataFlywheel:
            def __init__(self): pass
        mod.DEDANDataFlywheel = MockDataFlywheel
    sys.modules[mod_name] = mod

# Patch clinical_context_builder BEFORE importing main
import clinical_context_builder
clinical_context_builder.evidence_retriever = types.SimpleNamespace(
    retrieve=lambda topic, evidence_level=None, max_sources=5: {
        "topic": topic,
        "evidence_level": evidence_level.value if evidence_level else "moderate",
        "sources": [{"id": "who", "title": f"WHO - {topic}", "type": "guideline", "url": f"https://who.int/search?q={topic}", "jurisdiction": "WHO"}],
        "summary": f"Evidence for {topic} from authoritative sources."
    }
)

# Patch enhanced services
import evidence_retrieval_enhanced
evidence_retrieval_enhanced.evidence_retriever = clinical_context_builder.evidence_retriever

import medication_safety_enhanced
medication_safety_enhanced.medication_safety_service = types.SimpleNamespace(
    get_medication_info=lambda med, ctx=None: {
        "medication": med, "medication_class": "Antimalarial - ACT", "general_purpose": "Treats malaria",
        "common_warnings": ["Complete full course", "Take with food"], "contraindication_categories": ["Hypersensitivity"],
        "potential_interactions": ["Rifampicin"], "questions_to_ask_clinician": ["Correct dose?", "Interactions?"],
        "package_check_items": ["Active ingredient", "Strength", "Expiry"], "verification_required": True,
        "note": "Always check with pharmacist.", "is_educational_only": True,
    },
    get_class_medications=lambda cls: [{
        "medication_name": "Artemether-lumefantrine", "medication_class": "Antimalarial - ACT",
        "general_purpose": "Treats malaria", "common_warnings": ["Complete full course", "Take with food"],
        "contraindication_categories": ["Hypersensitivity"], "potential_interactions": ["Rifampicin"],
        "questions_to_ask": ["Correct dose?", "Interactions?"], "package_check_items": ["Active ingredient", "Strength", "Expiry"],
        "is_educational_only": True,
    }],
    get_pharmacy_verification_workflow=lambda cls: {
        "package_check_items": [
            {"field": "active_ingredient", "description": "Active ingredient (generic/INN name)", "why_important": "Confirms correct medication"},
            {"field": "strength", "description": "Strength/dose per unit", "why_important": "Ensures correct dosage"},
            {"field": "expiry", "description": "Expiration date", "why_important": "Expired medications can be ineffective or harmful"},
            {"field": "batch", "description": "Batch/lot number", "why_important": "Enables traceability and recall tracking"},
        ],
    },
    verify_medication=lambda med, ctx=None: {"medication": med, "medication_class": "Antimalarial - ACT", "general_purpose": "Treats malaria"}
)

import visual_education_enhanced
visual_education_enhanced.visual_education_service = types.SimpleNamespace(
    get_visuals_for_response=lambda conditions, body_systems, treatment_approaches, medication_classes: [
        types.SimpleNamespace(
            title=f"{conditions[0]} Overview" if conditions else "Medical Overview",
            description=f"Educational illustration of {conditions[0] if conditions else 'condition'}",
            visual_type="illustration", source="WHO Health Topics", source_url="https://who.int/health-topics",
            license="CC BY-NC-SA 4.0", medical_context=f"Educational reference for {conditions[0] if conditions else 'condition'}",
            is_ai_generated=False, ai_disclaimer=None,
        )
    ],
    get_disease_overview=lambda topic: [], get_anatomy_diagram=lambda system: [],
    get_treatment_procedure=lambda proc: [], get_warning_signs=lambda cond: [],
)

# Mock agent modules
for mod_name in [
    'agents.coordinator_agent', 'agents.triage_agent', 'agents.safety_guard_agent',
    'agents.guideline_agent', 'agents.risk_prediction_agent', 'agents.base_agent',
    'data_flywheel'
]:
    mod = types.ModuleType(mod_name)
    if 'coordinator' in mod_name:
        class MockCoordinatorAgent:
            def __init__(self, **kwargs): pass
            def get_agent_capabilities(self): return {}
        mod.CoordinatorAgent = MockCoordinatorAgent
    if 'flywheel' in mod_name:
        class MockDataFlywheel:
            def __init__(self): pass
        mod.DEDANDataFlywheel = MockDataFlywheel
    sys.modules[mod_name] = mod

# Patch clinical_context_builder
import clinical_context_builder
clinical_context_builder.clinical_context_builder.evidence_retriever = clinical_context_builder.evidence_retriever

# NOW import main
import main_clinical
print('main_clinical imported OK')

# Mock AI provider
from providers.models import AnalysisResponse, Modality
from unittest.mock import MagicMock, AsyncMock

class DictWithGet(dict):
    def get(self, key, default=None):
        return super().get(key, default)

async def mock_analyze(*args, **kwargs):
    return AnalysisResponse(
        request_id="test-123",
        urgency="see_doctor_soon",
        recommended_next_step="Please consult a healthcare professional for proper evaluation.",
        urgency_reasoning="Symptoms suggest need for professional evaluation",
        confidence_score=0.75,
        uncertainty="Based on reported symptoms, specific diagnosis requires clinical examination.",
        requires_professional_review=True,
        safety_notice="DEDAN Health provides health guidance for informational purposes only. This is not a medical diagnosis. Seek professional medical care for any concerning symptoms or emergencies.",
        medical_information=[
            {"topic": "possible_conditions", "content": '[{"name": "Malaria", "confidence": "medium", "confidence_score": 0.65, "reasoning": "Fever and chills in endemic area with mosquito exposure", "supporting_evidence": ["fever", "chills", "headache", "mosquito bites"], "contradicting_evidence": [], "requires_more_info": ["blood smear", "rapid diagnostic test"]}]', "source": "AI analysis", "source_type": "ai_analysis", "relevance_score": 0.65},
            {"topic": "doctor_communication", "content": '{"key_points": ["Fever for 2 days", "Chills and headache", "Mosquito bites reported"], "symptom_timeline": "Day 1: Fever onset with chills. Day 2: Headache developed.", "image_findings": [], "home_treatments_tried": [], "questions_to_ask": ["What is the most likely diagnosis?", "What tests are needed?"]}', "source": "AI analysis", "source_type": "ai_analysis", "relevance_score": 0.9},
            {"topic": "medicine_class", "content": '{"medicine_class": "Antimalarial - Artemisinin-based Combination Therapy (ACT)", "generic_examples": ["Artemether-lumefantrine", "Artesunate-amodiaquine"], "indication": "Uncomplicated Plasmodium falciparum malaria", "mechanism": "Rapidly reduces parasite biomass", "important_warnings": ["Complete full 3-day course", "Take with fatty food"], "contraindications": ["Known hypersensitivity"], "requires_prescription": true, "evidence_level": "strong", "source_guideline": "WHO Guidelines for Malaria"}', "source": "AI analysis", "source_type": "ai_analysis", "relevance_score": 0.8},
        ],
        treatment_information=[],
        warning_signs=["Persistent high fever >39°C", "Severe headache", "Confusion", "Difficulty breathing"],
        follow_up_questions=["Have you taken any antimalarials recently?", "Have you traveled to other endemic areas?"],
        sources=[{"id": "who_malaria", "title": "WHO Guidelines for Malaria", "type": "guideline", "url": "https://www.who.int/publications/i/item/9789240042479"}],
        processing_time_ms=1250,
        provider="gemini",
        model="gemini-1.5-pro",
        modality="text",
    )

# Patch the orchestrator and provider factory
from providers.orchestrator import MultimodalOrchestrator
from providers.provider_factory import ProviderFactory
from unittest.mock import AsyncMock

MultimodalOrchestrator.process = mock_analyze
ProviderFactory.get_provider_for_modalities = lambda self, **kwargs: MagicMock()
ProviderFactory.get_text_provider = lambda self: MagicMock()
ProviderFactory.get_vision_provider = lambda self: MagicMock()
ProviderFactory.get_multimodal_provider = lambda self: MagicMock()
ProviderFactory.health_check_all = AsyncMock(return_value={"gemini": True, "openai": False})

# Run the test
from fastapi.testclient import TestClient
from main_clinical import app
client = TestClient(app)
print('FastAPI app created OK')

response = client.get('/health')
print(f'Health: {response.status_code} - {response.json()}')

response = client.post('/api/analyze', json={
    "patient_age": 25,
    "patient_sex": "female",
    "patient_location": "Kenya",
    "patient_pregnant": False,
    "patient_chronic_conditions": [],
    "patient_medications": [],
    "patient_allergies": [],
    "patient_language": "en",
    "symptom_description": "High fever, chills, headache for 2 days. Recent mosquito bites.",
    "symptom_duration": "2 days",
    "symptom_severity": "moderate",
    "consent": True
})
print(f'Clinical guidance: {response.status_code}')
if response.status_code != 200:
    print(f'Response: {response.json()}')
else:
    data = response.json()
    print(f'Response keys: {list(data.keys())}')
    cr = data.get('clinical_response', data)
    print(f'Clinical response keys: {list(cr.keys())}')
    print(f'Possible explanations: {len(cr.get("possible_explanations", []))}')
    print(f'Visual education: {len(cr.get("visual_education", []))}')
    print(f'Medication info: {len(cr.get("medication_information", []))}')
    print(f'Body mechanism: {len(cr.get("body_mechanism", []))}')
    print(f'Treatment approach: {cr.get("treatment_approach") is not None}')
    print(f'Medication verification: {len(cr.get("medication_verification", []))}')
    print(f'Next steps: {list(cr.get("next_steps", {}).keys())}')
    print('SUCCESS: Backend returns complete structured response!')
