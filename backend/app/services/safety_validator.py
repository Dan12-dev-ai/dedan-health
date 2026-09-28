import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..ai_providers.base import AnalysisResult, PatientContext


@dataclass
class SafetyCheckResult:
    is_safe: bool
    urgency_override: Optional[str] = None
    additional_flags: List[str] = field(default_factory=list)
    requires_professional_review: bool = False
    emergency_message: Optional[str] = None


class SafetyValidator:
    """
    Validates AI responses for medical safety.
    Never silently downgrades urgency. Always escalates when uncertain.
    """

    # Emergency keywords that should ALWAYS trigger emergency/urgent
    EMERGENCY_KEYWORDS = [
        "chest pain", "difficulty breathing", "shortness of breath", "severe bleeding",
        "loss of consciousness", "unconscious", "stroke symptoms", "heart attack",
        "severe allergic reaction", "anaphylaxis", "suicidal", "confusion",
        "slurred speech", "facial drooping", "arm weakness", "severe headache",
        "high fever with rash", "seizure", "severe abdominal pain", "vomiting blood",
        "black tarry stools", "severe dehydration", "unable to wake", "coughing blood",
        "sudden vision loss", "severe burns", "electric shock", "drowning",
        "poisoning", "overdose", "severe head injury", "broken bone protruding",
    ]

    URGENT_KEYWORDS = [
        "worsening symptoms", "high fever", "severe pain", "bloody diarrhea",
        "difficulty swallowing", "rapid heartbeat", "stiff neck", "persistent vomiting",
        "unable to keep fluids down", "signs of dehydration", "pregnant with bleeding",
        "newborn with fever", "elderly with confusion", "immunocompromised with fever",
        "spreading redness", "increasing swelling", "pus or foul discharge",
        "fever above 39", "fever above 102", "pain not relieved by otc",
    ]

    HIGH_RISK_PATIENT_FLAGS = [
        "pregnant", "pregnancy",
        "infant", "newborn", "baby", "child", "pediatric",
        "elderly", "geriatric", "over 75", "over 80",
        "immunocompromised", "immunosuppressed", "hiv", "aids", "chemotherapy",
        "cancer", "malignancy",
        "diabetes", "diabetic",
        "heart disease", "heart failure", "hypertension",
        "stroke", "tia",
        "kidney disease", "renal failure",
        "liver disease", "cirrhosis",
        "on blood thinners", "anticoagulant", "warfarin",
    ]

    UNCERTAINTY_INDICATORS = [
        "cannot determine", "unclear", "insufficient", "need better image",
        "blurry", "dark", "poor quality", "not visible", "cannot see",
        "uncertain", "ambiguous", "insufficient information", "limited view",
    ]

    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold

    def validate(
        self,
        response: AnalysisResult,
        context: Optional[PatientContext] = None,
        original_text: str = "",
    ) -> SafetyCheckResult:
        """
        Validate response for safety. Returns safety check result with any overrides.
        """
        result = SafetyCheckResult(is_safe=True)
        combined_text = " ".join(filter(None, [
            original_text,
            response.recommended_next_step,
            response.uncertainty,
            str(response.medical_information),
            str(response.treatment_information),
        ])).lower()

        # 1. Check for emergency keywords - NEVER downgrade
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in combined_text:
                result.additional_flags.append(f"emergency_keyword:{keyword}")
                result.requires_professional_review = True
                if response.urgency not in ["emergency", "urgent"]:
                    result.urgency_override = "emergency"
                    result.emergency_message = (
                        f"⚠️ EMERGENCY DETECTED: '{keyword}' mentioned. "
                        f"Call emergency services ({self._get_emergency_number(context)}) or go to the nearest emergency department IMMEDIATELY."
                    )
                break

        # 2. Check for urgent keywords
        if not result.urgency_override:
            for keyword in self.URGENT_KEYWORDS:
                if keyword in combined_text:
                    result.additional_flags.append(f"urgent_keyword:{keyword}")
                    result.requires_professional_review = True
                    if response.urgency == "self_care":
                        result.urgency_override = "see_doctor_soon"
                    break

        # 3. Check patient risk factors
        if context:
            patient_text = " ".join(filter(None, [
                str(context.chronic_conditions),
                str(context.medications),
                "pregnant" if context.pregnancy_status else "",
                str(context.age) if context.age else "",
            ])).lower()

            for flag in self.HIGH_RISK_PATIENT_FLAGS:
                if flag in patient_text:
                    result.additional_flags.append(f"high_risk_patient:{flag}")
                    result.requires_professional_review = True
                    if response.urgency == "self_care":
                        result.urgency_override = "see_doctor_soon"
                    break

        # 4. Check AI uncertainty
        if response.uncertainty:
            uncertainty_lower = response.uncertainty.lower()
            for indicator in self.UNCERTAINTY_INDICATORS:
                if indicator in uncertainty_lower:
                    result.additional_flags.append(f"ai_uncertainty:{indicator}")
                    result.requires_professional_review = True
                    if response.urgency == "self_care":
                        result.urgency_override = "see_doctor_soon"
                    break

        # 5. Check confidence threshold
        if response.confidence_score < self.confidence_threshold:
            result.additional_flags.append(f"low_confidence:{response.confidence_score:.2f}")
            result.requires_professional_review = True
            if response.urgency == "self_care":
                result.urgency_override = "see_doctor_soon"

        # 6. Ensure safety notice is present
        if not response.safety_notice:
            result.additional_flags.append("missing_safety_notice")

        # 7. Validate medical disclaimer language
        if not self._has_proper_disclaimer(response.safety_notice):
            result.additional_flags.append("inadequate_disclaimer")

        # 8. Check for inappropriate prescriptions
        if self._contains_prescription_details(response):
            result.additional_flags.append("inappropriate_prescription_details")
            result.requires_professional_review = True

        return result

    def apply_safety_result(
        self,
        response: AnalysisResult,
        safety_result: SafetyCheckResult,
    ) -> AnalysisResult:
        """Apply safety check results to the response."""
        if safety_result.urgency_override:
            response.urgency = safety_result.urgency_override

        response.requires_professional_review = (
            response.requires_professional_review or safety_result.requires_professional_review
        )

        response.safety_flags.extend(safety_result.additional_flags)

        if safety_result.emergency_message:
            if response.safety_notice:
                response.safety_notice = safety_result.emergency_message + "\n\n" + response.safety_notice
            else:
                response.safety_notice = safety_result.emergency_message

        return response

    def _get_emergency_number(self, context: Optional[PatientContext]) -> str:
        """Get emergency number based on location."""
        if context and context.location:
            location_lower = context.location.lower()
            # Common emergency numbers by region
            emergency_numbers = {
                "kenya": "999 or 112",
                "ke": "999 or 112",
                "tanzania": "112",
                "tz": "112",
                "uganda": "999",
                "ug": "999",
                "nigeria": "199 or 112",
                "ng": "199 or 112",
                "ghana": "193 or 112",
                "gh": "193 or 112",
                "south africa": "10177 or 112",
                "za": "10177 or 112",
                "ethiopia": "991 or 907",
                "et": "991 or 907",
                "rwanda": "112",
                "rw": "112",
                "us": "911",
                "usa": "911",
                "uk": "999 or 112",
                "gb": "999 or 112",
                "eu": "112",
                "canada": "911",
                "ca": "911",
                "australia": "000",
                "au": "000",
            }
            for key, number in emergency_numbers.items():
                if key in location_lower:
                    return number
        return "your local emergency number (e.g., 911, 999, 112)"

    def _has_proper_disclaimer(self, notice: str) -> bool:
        """Check if safety notice contains required disclaimer elements."""
        if not notice:
            return False
        notice_lower = notice.lower()
        required_elements = [
            "not a diagnosis" in notice_lower or "not a medical diagnosis" in notice_lower,
            "professional" in notice_lower or "healthcare" in notice_lower,
            "emergency" in notice_lower or "urgent" in notice_lower,
        ]
        return all(required_elements)

    def _contains_prescription_details(self, response: AnalysisResult) -> bool:
        """Check if response inappropriately contains specific dosages or brand names."""
        text_to_check = " ".join([
            response.recommended_next_step,
            response.uncertainty,
            str(response.medical_information),
            str(response.treatment_information),
        ]).lower()

        # Check for specific dosages
        dosage_patterns = [
            r"\d+\s*mg", r"\d+\s*ml", r"\d+\s*tablet", r"\d+\s*capsule",
            r"take \d+", r"dose of \d+", r"\d+ times daily", r"\d+ times a day",
            r"every \d+ hours", r"\d+ hourly",
        ]

        for pattern in dosage_patterns:
            if re.search(pattern, text_to_check):
                return True

        # Check for brand names (common ones)
        brand_names = [
            "tylenol", "advil", "motrin", "aleve", "aspirin", "panadol",
            "amoxicillin", "azithromycin", "ciprofloxacin", "metronidazole",
            "coartem", "malarone", "loroquine", "primaquine",
            "paracetamol", "ibuprofen", "diclofenac", "naproxen",
        ]

        # Note: generic names like paracetamol/ibuprofen are OK in medicine class context
        # but specific brand recommendations are not
        for brand in brand_names:
            if f"take {brand}" in text_to_check or f"prescribe {brand}" in text_to_check:
                return True

        return False


# Global validator instance
safety_validator = SafetyValidator()