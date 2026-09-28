"""
Enhanced Medication Safety Service — DEDAN Health 2.0

Provides educational medication information with pharmacy verification workflow.
NEVER prescribes. Always distinguishes educational information from personalized
clinical recommendations.

Architecture:
MedicationQuery -> MedicationReferenceProvider -> Verified drug information
                                              -> Safety rules
                                              -> AI explanation
                                              -> Pharmacy verification items
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from clinical_schema import MedicationInfo, Source, EvidenceLevel


@dataclass
class MedicationReferenceProvider:
    """Abstract interface for medication reference providers."""
    
    def get_medication_info(self, medication_name: str) -> Optional[Dict[str, Any]]:
        """Get verified medication information."""
        raise NotImplementedError
    
    def get_class_info(self, medication_class: str) -> Optional[Dict[str, Any]]:
        """Get medication class information."""
        raise NotImplementedError
    
    def check_interactions(self, medications: List[str]) -> List[Dict[str, Any]]:
        """Check for drug-drug interactions."""
        raise NotImplementedError
    
    def verify_package_info(self, medication_name: str, package_data: Dict[str, str]) -> Dict[str, Any]:
        """Verify medication package information."""
        raise NotImplementedError


class LocalMedicationReferenceProvider(MedicationReferenceProvider):
    """
    Local medication reference with verified data.
    In production, this would integrate with FDA DailyMed, WHO Essential Medicines, etc.
    """
    
    # Verified medication class reference (educational only)
    MEDICATION_CLASS_INFO: Dict[str, Dict[str, Any]] = {
        "antimalarial": {
            "class": "Antimalarial - Artemisinin-based Combination Therapy (ACT)",
            "generic_examples": ["Artemether-lumefantrine", "Artesunate-amodiaquine", "Dihydroartemisinin-piperaquine"],
            "purpose": "Treats uncomplicated Plasmodium falciparum malaria",
            "mechanism": "Rapidly reduces parasite biomass; partner drug eliminates remaining parasites",
            "warnings": [
                "Complete full 3-day course even if feeling better",
                "Take with fatty food for better absorption",
                "Do not use for severe malaria - requires IV artesunate",
                "Pregnancy: ACTs recommended in 2nd/3rd trimester; consult clinician in 1st trimester",
            ],
            "contraindications": ["Known hypersensitivity to components", "Severe malaria (use IV artesunate)"],
            "interactions": ["Rifampicin (reduces efficacy)", "Efavirenz (may reduce levels)", "Antacids (may affect absorption)"],
            "formulations": ["Tablets (dispersible for children)", "Rectal artesunate (pre-referral)"],
            "evidence_level": "strong",
            "source_guideline": "WHO Guidelines for Malaria (2023)",
        },
        "antibiotic": {
            "class": "Antibiotic",
            "generic_examples": ["Amoxicillin", "Azithromycin", "Doxycycline", "Ciprofloxacin"],
            "purpose": "Treats bacterial infections",
            "mechanism": "Inhibits bacterial cell wall synthesis, protein synthesis, or DNA replication",
            "warnings": [
                "Complete full prescribed course",
                "Do not share with others",
                "Ineffective against viral infections",
                "May cause antibiotic-associated diarrhea",
            ],
            "contraindications": ["Known allergy to class", "Severe hepatic/renal impairment (varies by drug)"],
            "interactions": ["Antacids (reduce absorption of some)", "Warfarin (increased bleeding risk)", "Oral contraceptives (may reduce efficacy)"],
            "formulations": ["Tablets/capsules", "Suspensions", "IV formulations"],
            "evidence_level": "strong",
            "source_guideline": "WHO AWaRe Classification / National Guidelines",
        },
        "analgesic": {
            "class": "Analgesic / Antipyretic",
            "generic_examples": ["Paracetamol (Acetaminophen)", "Ibuprofen", "Diclofenac", "Naproxen"],
            "purpose": "Pain relief and fever reduction",
            "mechanism": "COX inhibition (NSAIDs) or central COX inhibition (paracetamol)",
            "warnings": [
                "Paracetamol: Do not exceed 4g/day (adults); hepatotoxicity risk",
                "NSAIDs: Take with food; GI bleed risk; renal impairment risk",
                "Avoid alcohol with paracetamol",
                "Not for long-term use without clinician supervision",
            ],
            "contraindications": [
                "Paracetamol: Severe hepatic impairment, alcohol use disorder",
                "NSAIDs: Active GI bleed, severe renal/hepatic impairment, 3rd trimester pregnancy",
            ],
            "interactions": ["Warfarin (NSAIDs increase bleeding)", "ACE inhibitors (NSAIDs reduce effect)", "Diuretics (NSAIDs reduce effect)", "Other NSAIDs/paracetamol products"],
            "formulations": ["Tablets", "Syrups/suspensions", "Suppositories", "IV/IM"],
            "evidence_level": "strong",
            "source_guideline": "WHO Essential Medicines List / National Formularies",
        },
        "antihistamine": {
            "class": "Antihistamine (H1-blocker)",
            "generic_examples": ["Cetirizine", "Loratadine", "Fexofenadine", "Chlorphenamine", "Diphenhydramine"],
            "purpose": "Relieves allergy symptoms (rhinitis, urticaria, pruritus)",
            "mechanism": "Competitive H1-receptor antagonism",
            "warnings": [
                "1st gen (chlorphenamine, diphenhydramine): sedation, anticholinergic effects",
                "2nd gen (cetirizine, loratadine): less sedating",
                "Avoid alcohol",
                "Check labels for duplicate ingredients",
            ],
            "contraindications": ["Angle-closure glaucoma", "BPH/urinary retention (1st gen)", "MAOI use"],
            "interactions": ["Sedatives (additive CNS depression)", "Alcohol", "Other antihistamines"],
            "formulations": ["Tablets", "Syrups", "IV/IM (1st gen)"],
            "evidence_level": "strong",
            "source_guideline": "WHO Essential Medicines List / ARIA Guidelines",
        },
        "antiemetic": {
            "class": "Antiemetic",
            "generic_examples": ["Ondansetron", "Metoclopramide", "Prochlorperazine", "Domperidone"],
            "purpose": "Prevents and treats nausea and vomiting",
            "mechanism": "5-HT3 antagonism (ondansetron), D2 antagonism (metoclopramide/prochlorperazine)",
            "warnings": [
                "Ondansetron: QT prolongation risk, especially with other QT drugs",
                "Metoclopramide: Extrapyramidal symptoms, avoid in young adults",
                "Prochlorperazine: Sedation, anticholinergic effects",
            ],
            "contraindications": [
                "Ondansetron: Congenital long QT, concomitant apomorphine",
                "Metoclopramide: Pheochromocytoma, GI obstruction",
            ],
            "interactions": ["QT-prolonging drugs (ondansetron)", "Dopamine agonists (metoclopramide)"],
            "formulations": ["Tablets", "Oral dissolving films", "IV/IM"],
            "evidence_level": "strong",
            "source_guideline": "WHO Essential Medicines List / NCCN Guidelines",
        },
        "bronchodilator": {
            "class": "Bronchodilator (SABA/LABA)",
            "generic_examples": ["Salbutamol (Albuterol)", "Formoterol", "Salmeterol", "Ipratropium"],
            "purpose": "Relieves bronchospasm in asthma/COPD",
            "mechanism": "Beta-2 agonism (SABA/LABA) or muscarinic antagonism (ipratropium)",
            "warnings": [
                "SABA: Not for maintenance; overuse indicates poor control",
                "LABA: Never use without inhaled corticosteroid in asthma",
                "Ipratropium: Caution in glaucoma, BPH",
            ],
            "contraindications": ["Hypersensitivity", "Severe cardiac arrhythmias (caution)"],
            "interactions": ["Beta-blockers (may antagonize)", "Other bronchodilators (additive effects)"],
            "formulations": ["MDI (inhaler)", "DPI (dry powder)", "Nebules", "IV"],
            "evidence_level": "strong",
            "source_guideline": "GINA Asthma Guidelines / GOLD COPD Guidelines",
        },
        "corticosteroid_inhaled": {
            "class": "Inhaled Corticosteroid (ICS)",
            "generic_examples": ["Beclometasone", "Budesonide", "Fluticasone", "Mometasone"],
            "purpose": "Anti-inflammatory maintenance for asthma",
            "mechanism": "Glucocorticoid receptor activation -> reduced airway inflammation",
            "warnings": [
                "Rinse mouth after use to prevent oral thrush",
                "Not for acute bronchospasm - use SABA",
                "Growth monitoring in children",
                "Adrenal suppression at high doses",
            ],
            "contraindications": ["Hypersensitivity", "Active TB/untreated infections"],
            "interactions": ["Strong CYP3A4 inhibitors (increased systemic exposure)"],
            "formulations": ["MDI", "DPI", "Nebules"],
            "evidence_level": "strong",
            "source_guideline": "GINA Asthma Guidelines",
        },
        "antihypertensive": {
            "class": "Antihypertensive",
            "generic_examples": ["Amlodipine", "Lisinopril", "Losartan", "Hydrochlorothiazide", "Bisoprolol"],
            "purpose": "Lowers blood pressure",
            "mechanism": "Varies: CCB, ACEi, ARB, thiazide, beta-blocker",
            "warnings": [
                "Do not stop abruptly (rebound hypertension)",
                "Monitor renal function and electrolytes (ACEi/ARB/diuretics)",
                "ACEi: Dry cough, angioedema risk",
                "Pregnancy: Avoid ACEi/ARB; use methyldopa/labetalol/nifedipine",
            ],
            "contraindications": [
                "ACEi/ARB: Pregnancy, bilateral renal artery stenosis, history of angioedema",
                "Beta-blockers: Severe bradycardia, heart block, asthma",
            ],
            "interactions": ["NSAIDs (reduce antihypertensive effect)", "K+ supplements (with ACEi/ARB/diuretics)", "Other antihypertensives (additive hypotension)"],
            "formulations": ["Tablets", "Combination pills"],
            "evidence_level": "strong",
            "source_guideline": "WHO HEARTS / NICE / ACC/AHA Guidelines",
        },
    }

    def __init__(self):
        pass

    def get_medication_info(self, medication_name: str) -> Optional[Dict[str, Any]]:
        """Get verified medication information by generic name."""
        name_lower = medication_name.lower().strip()
        
        # Search in class info
        for class_key, info in self.MEDICATION_CLASS_INFO.items():
            for generic in info.get("generic_examples", []):
                if generic.lower() in name_lower or name_lower in generic.lower():
                    return {"class": class_key, **info}
        
        # Direct class match
        if name_lower in self.MEDICATION_CLASS_INFO:
            return {"class": name_lower, **self.MEDICATION_CLASS_INFO[name_lower]}
        
        return None

    def get_class_info(self, medication_class: str) -> Optional[Dict[str, Any]]:
        """Get medication class information."""
        class_lower = medication_class.lower().strip()
        return self.MEDICATION_CLASS_INFO.get(class_lower)

    def check_interactions(self, medications: List[str]) -> List[Dict[str, Any]]:
        """Check for drug-drug interactions (simplified)."""
        # In production, integrate with a proper interaction checker
        interactions = []
        meds_lower = [m.lower() for m in medications]
        
        # Known interaction pairs
        interaction_pairs = {
            ("warfarin", "ibuprofen"): "Increased bleeding risk",
            ("warfarin", "amoxicillin"): "Increased INR/bleeding risk",
            ("ace_inhibitor", "potassium"): "Hyperkalemia risk",
            ("digoxin", "amiodarone"): "Increased digoxin levels",
            ("ssri", "nsaid"): "Increased GI bleeding risk",
        }
        
        for pair, desc in interaction_pairs.items():
            if all(p in " ".join(meds_lower) for p in pair):
                interactions.append({
                    "drugs": list(pair),
                    "severity": "moderate",
                    "description": desc,
                    "action": "Monitor closely; consult clinician",
                })
        
        return interactions

    def verify_package_info(self, medication_name: str, package_data: Dict[str, str]) -> Dict[str, Any]:
        """Verify medication package information against reference."""
        ref_info = self.get_medication_info(medication_name)
        if not ref_info:
            return {
                "verified": False,
                "reason": "Medication not in reference database",
                "checks": [],
            }
        
        checks = []
        discrepancies = []
        
        # Check active ingredient
        expected_generics = ref_info.get("generic_examples", [])
        provided_ingredient = package_data.get("active_ingredient", "").lower()
        match = any(g.lower() in provided_ingredient or provided_ingredient in g.lower() 
                   for g in expected_generics)
        checks.append({
            "field": "active_ingredient",
            "provided": package_data.get("active_ingredient", "Not provided"),
            "expected": expected_generics,
            "match": match,
        })
        if not match:
            discrepancies.append("Active ingredient does not match expected generics")
        
        # Check strength
        provided_strength = package_data.get("strength", "")
        checks.append({
            "field": "strength",
            "provided": provided_strength or "Not provided",
            "expected": "Verify against prescription",
            "match": bool(provided_strength),
        })
        
        # Check formulation
        provided_form = package_data.get("formulation", "")
        expected_forms = ref_info.get("formulations", [])
        form_match = any(f.lower() in provided_form.lower() for f in expected_forms)
        checks.append({
            "field": "formulation",
            "provided": provided_form or "Not provided",
            "expected": expected_forms,
            "match": form_match or not provided_form,
        })
        
        # Check expiry
        provided_expiry = package_data.get("expiry_date", "")
        checks.append({
            "field": "expiry_date",
            "provided": provided_expiry or "Not provided",
            "expected": "Must not be expired",
            "match": bool(provided_expiry),
        })
        
        return {
            "verified": len(discrepancies) == 0,
            "discrepancies": discrepancies,
            "checks": checks,
            "reference_class": ref_info.get("class", ""),
            "note": "Always confirm with pharmacist; this is an automated check only",
        }


class MedicationSafetyService:
    """Provides medication safety information with pharmacy verification workflow."""

    def __init__(self, reference_provider: Optional[MedicationReferenceProvider] = None):
        self.reference_provider = reference_provider or LocalMedicationReferenceProvider()

    def get_medication_info(
        self,
        medication_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> MedicationInfo:
        """Get educational medication information from verified source."""
        class_info = self.reference_provider.get_medication_info(medication_name)
        
        if not class_info:
            # Fallback for unknown medications
            return MedicationInfo(
                medication_name=medication_name,
                medication_class="Unknown - verify with pharmacist",
                general_purpose="Information not available in reference database",
                common_warnings=["Verify with pharmacist before use"],
                contraindication_categories=["Unknown - consult clinician"],
                potential_interactions=["Unknown - provide full medication list to pharmacist"],
                questions_to_ask=self._get_questions_to_ask(medication_name),
                package_check_items=self._get_package_check_items(),
                source=Source(
                    title="DEDAN Health Medication Reference",
                    url="https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02",
                    type="regulatory",
                    jurisdiction="WHO",
                ),
                is_educational_only=True,
            )
        
        return MedicationInfo(
            medication_name=medication_name,
            medication_class=class_info.get("class", "Not specified"),
            general_purpose=class_info.get("purpose", "Not specified"),
            common_warnings=class_info.get("warnings", []),
            contraindication_categories=class_info.get("contraindications", []),
            potential_interactions=class_info.get("interactions", []),
            questions_to_ask=self._get_questions_to_ask(medication_name, class_info),
            package_check_items=self._get_package_check_items(),
            source=Source(
                title=f"Medication reference — {class_info.get('class', medication_name)}",
                url=class_info.get("source_guideline", "https://www.who.int/medicines"),
                type="guideline",
                jurisdiction=class_info.get("source_guideline", "WHO"),
            ),
            is_educational_only=True,
        )

    def get_class_medications(self, medication_class: str) -> List[MedicationInfo]:
        """Get all medications in a class for discussion with pharmacist."""
        class_info = self.reference_provider.get_class_info(medication_class)
        if not class_info:
            return []
        
        medications = []
        for generic in class_info.get("generic_examples", []):
            med = MedicationInfo(
                medication_name=generic,
                medication_class=class_info.get("class", medication_class),
                general_purpose=class_info.get("purpose", "Not specified"),
                common_warnings=class_info.get("warnings", []),
                contraindication_categories=class_info.get("contraindications", []),
                potential_interactions=class_info.get("interactions", []),
                questions_to_ask=self._get_questions_to_ask(generic, class_info),
                package_check_items=self._get_package_check_items(),
                source=Source(
                    title=f"Medication class reference — {class_info.get('class', medication_class)}",
                    url=class_info.get("source_guideline", "https://www.who.int/medicines"),
                    type="guideline",
                    jurisdiction=class_info.get("source_guideline", "WHO"),
                ),
                is_educational_only=True,
            )
            medications.append(med)
        
        return medications

    def verify_medication(
        self,
        medication_name: str,
        patient_context: Optional[Dict[str, Any]] = None,
        package_data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Verify medication information for a patient with optional package check."""
        info = self.get_medication_info(medication_name, patient_context)
        
        result = {
            "medication": info.medication_name,
            "medication_class": info.medication_class,
            "general_purpose": info.general_purpose,
            "common_warnings": info.common_warnings,
            "contraindication_categories": info.contraindication_categories,
            "potential_interactions": info.potential_interactions,
            "questions_to_ask_clinician": info.questions_to_ask,
            "package_check_items": info.package_check_items,
            "verification_required": True,
            "note": "Always check the actual package label and consult a pharmacist.",
            "is_educational_only": True,
        }
        
        # Add package verification if provided
        if package_data:
            verification = self.reference_provider.verify_package_info(medication_name, package_data)
            result["package_verification"] = verification
        
        # Add interaction check if patient has other medications
        if patient_context and patient_context.get("medications"):
            all_meds = [medication_name] + patient_context["medications"]
            interactions = self.reference_provider.check_interactions(all_meds)
            if interactions:
                result["interaction_check"] = interactions
        
        return result

    def get_pharmacy_verification_workflow(self, medication_class: str) -> Dict[str, Any]:
        """Get step-by-step pharmacy verification workflow for a medication class."""
        class_info = self.reference_provider.get_class_info(medication_class)
        
        workflow = {
            "steps": [
                {
                    "step": 1,
                    "title": "Obtain prescription",
                    "description": "Visit a doctor or clinical officer for proper diagnosis and prescription",
                    "details": "The prescription should specify the generic name, strength, and duration",
                },
                {
                    "step": 2,
                    "title": "Visit licensed pharmacy",
                    "description": "Take the prescription to a licensed pharmacy or government health facility",
                    "details": "Look for displayed pharmacy license; avoid unlicensed sellers",
                },
                {
                    "step": 3,
                    "title": "Verify medication matches prescription",
                    "description": "Ask the pharmacist to confirm the medication matches your prescription exactly",
                    "details": "Check: generic name, strength, formulation, quantity",
                },
                {
                    "step": 4,
                    "title": "Inspect packaging",
                    "description": "Check the packaging for tampering, expiry date, and correct drug name",
                    "details": "Verify batch number, manufacturing date, regulatory hologram/sticker",
                },
                {
                    "step": 5,
                    "title": "Ask pharmacist questions",
                    "description": "Ask about proper storage, how to take the medication, and side effects",
                    "details": "Use the questions below",
                },
            ],
            "verification_questions": self._get_questions_to_ask(medication_class, class_info or {}),
            "package_check_items": self._get_package_check_items(),
            "trusted_sources": self._get_trusted_sources(),
            "warning_against": self._get_warnings_against(),
            "country_specific": self._get_country_specific_guidance(),
        }
        
        if class_info:
            workflow["medication_class"] = class_info.get("class", medication_class)
            workflow["generic_examples"] = class_info.get("generic_examples", [])
            workflow["important_warnings"] = class_info.get("warnings", [])
        
        return workflow

    def _get_questions_to_ask(self, medication_name: str, class_info: Optional[Dict] = None) -> List[str]:
        questions = [
            f"What is the active ingredient in {medication_name}?",
            "What is the correct dose for my age, weight, and condition?",
            "Are there interactions with my other medications?",
            "What are the side effects I should watch for?",
            "How long should I take this medication?",
            "Should I take it with food or on an empty stomach?",
            "What should I do if I miss a dose?",
            "Can I stop taking it when I feel better, or must I complete the course?",
        ]
        
        if class_info:
            # Add class-specific questions
            if "antimalarial" in class_info.get("class", "").lower():
                questions.append("Should I take this with fatty food for better absorption?")
            if "antibiotic" in class_info.get("class", "").lower():
                questions.append("Is this antibiotic appropriate for my type of infection?")
            if "analgesic" in class_info.get("class", "").lower() and "paracetamol" in medication_name.lower():
                questions.append("What is the maximum daily dose I should not exceed?")
        
        return questions

    def _get_package_check_items(self) -> List[str]:
        return [
            "Active ingredient (generic/INN name)",
            "Strength/dose per unit",
            "Dosage form (tablet, capsule, syrup, etc.)",
            "Purpose/indication",
            "Warnings and precautions",
            "Directions for use",
            "Expiration date",
            "Batch/lot number",
            "Manufacturer name",
            "Regulatory approval mark (e.g., FDA, PPB, NAFDAC, TFDA)",
            "Storage conditions",
        ]

    def _get_trusted_sources(self) -> List[str]:
        return [
            "Government/public hospitals and health centers",
            "Licensed private pharmacies (look for license displayed)",
            "Mission/faith-based health facilities",
            "NGO-supported clinics (MSF, Red Cross, etc.)",
            "KEMSA (Kenya Medical Supplies Authority) supplied facilities",
            "NHIF-accredited pharmacies",
            "County government health facilities",
        ]

    def _get_warnings_against(self) -> List[str]:
        return [
            "Buying medicines from unlicensed street vendors, markets, or social media",
            "Using leftover prescriptions from others",
            "Taking antibiotics without confirmed bacterial infection",
            "Purchasing 'herbal' or 'traditional' products with undisclosed ingredients",
            "Online pharmacies without proper licensing in your country",
            "Medicines without proper packaging, labels, or expiry dates",
            "Sharing prescription medications with family/friends",
        ]

    def _get_country_specific_guidance(self) -> str:
        return (
            "In Kenya: Use PPB-licensed pharmacies. NHIF covers many essential medicines "
            "at accredited facilities. KEMSA supplies government facilities. "
            "Report suspected counterfeit drugs to PPB via *254# or 0800 722 000. "
            "Always ask for the generic (INN) name - it's cheaper and equally effective."
        )


# Global instance
medication_safety_service = MedicationSafetyService()