"""
Medication Safety — DEDAN Health 2.0

Educational medication information only. Never prescribes.
Always distinguishes educational information from personalized
clinical recommendations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from clinical_schema import MedicationInfo, Source


# Common medication class reference (educational only)
MEDICATION_CLASS_INFO: Dict[str, Dict[str, Any]] = {
    "antibiotic": {
        "class": "Antibiotic",
        "purpose": "Treats bacterial infections",
        "warnings": ["Complete full course", "Do not share with others", "May cause diarrhea"],
        "contraindications": ["Known allergy", "Liver/kidney disease"],
        "interactions": ["Antacids", "Warfarin", "Oral contraceptives"],
    },
    "amoxicillin": {
        "class": "Antibiotic (Penicillin)",
        "purpose": "Treats bacterial infections",
        "warnings": ["Complete full course", "Do not share with others", "May cause diarrhea", "Allergy risk"],
        "contraindications": ["Known penicillin allergy", "Liver/kidney disease"],
        "interactions": ["Antacids", "Warfarin", "Oral contraceptives"],
    },
    "acetaminophen": {
        "class": "Analgesic / antipyretic",
        "purpose": "Pain relief and fever reduction",
        "warnings": ["Do not exceed recommended dose", "Avoid alcohol", "Check with doctor if pregnant"],
        "contraindications": ["Liver disease", "Alcohol use disorder"],
        "interactions": ["Warfarin", "Alcohol", "Other acetaminophen products"],
    },
    "analgesic": {
        "class": "Pain reliever",
        "purpose": "Relieves pain and reduces fever",
        "warnings": ["Do not exceed recommended dose", "Avoid alcohol", "Check with doctor if pregnant"],
        "contraindications": ["Stomach ulcers", "Kidney disease", "Allergy to NSAIDs"],
        "interactions": ["Blood thinners", "ACE inhibitors", "Diuretics"],
    },
    "antihistamine": {
        "class": "Antihistamine",
        "purpose": "Relieves allergy symptoms",
        "warnings": ["May cause drowsiness", "Avoid alcohol", "Check labels for duplicates"],
        "contraindications": ["Glaucoma", "Enlarged prostate", "MAOI use"],
        "interactions": ["Sedatives", "Alcohol", "Other antihistamines"],
    },
}


class MedicationSafetyError(Exception):
    pass


class MedicationSafetyService:
    """Provides medication safety information — never prescriptions."""

    def __init__(self):
        self._reference_data = MEDICATION_CLASS_INFO

    def get_medication_info(
        self,
        medication_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> MedicationInfo:
        """Get educational medication information."""
        # Look up known class info
        class_info = self._find_class_info(medication_name)

        return MedicationInfo(
            medication_name=medication_name,
            medication_class=class_info.get("class", "Unknown"),
            general_purpose=class_info.get("purpose", "Unknown purpose"),
            common_warnings=class_info.get("warnings", []),
            contraindication_categories=class_info.get("contraindications", []),
            potential_interactions=class_info.get("interactions", []),
            questions_to_ask=self._get_questions_to_ask(medication_name),
            package_check_items=self._get_package_check_items(),
            source=Source(
                title=f"Medication reference — {medication_name}",
                url="https://www.fda.gov/drugs",
                type="regulatory",
                jurisdiction="FDA",
            ),
            is_educational_only=True,
        )

    def verify_medication(
        self,
        medication_name: str,
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Verify medication information for a patient."""
        info = self.get_medication_info(medication_name, patient_context)

        return {
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
        }

    def _find_class_info(self, medication_name: str) -> Dict[str, Any]:
        """Find medication class info by name."""
        name_lower = medication_name.lower()
        for key, info in self._reference_data.items():
            if key in name_lower:
                return info
        return {}

    def _get_questions_to_ask(self, medication_name: str) -> List[str]:
        return [
            f"What is the active ingredient in {medication_name}?",
            "What is the correct dose for my age and condition?",
            "Are there interactions with my other medications?",
            "What are the side effects I should watch for?",
            "How long should I take this?",
        ]

    def _get_package_check_items(self) -> List[str]:
        return [
            "Active ingredient",
            "Strength/dose",
            "Purpose",
            "Warnings",
            "Directions",
            "Expiration date",
            "Lot number",
        ]
