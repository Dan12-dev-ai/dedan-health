import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..models.schemas import (
    AnalyzeResponse,
    PossibleCondition,
    FirstAidStep,
    WhatToTellDoctor,
    RecommendedMedicineClass,
    PharmacyGuidance,
    Disclaimer,
    NextSteps,
    UrgencyLevel,
    ConfidenceLevel,
)
from ..ai_providers.base import AnalysisResult, PatientContext


class ResponseTransformer:
    """Transforms AI provider response into structured API response."""

    # Standard disclaimer
    DISCLAIMER_FULL = (
        "IMPORTANT MEDICAL DISCLAIMER: DEDAN Health provides AI-generated health information "
        "for educational and informational purposes only. This service does not provide medical "
        "diagnoses, treatment recommendations, or professional medical advice. The analysis is "
        "based on the information you provided and may be incomplete or inaccurate. "
        "NEVER use this information as a substitute for professional medical evaluation, diagnosis, "
        "or treatment. ALWAYS consult a qualified healthcare professional (doctor, clinical officer, "
        "nurse, or pharmacist) for any health concerns, especially if symptoms are severe, worsening, "
        "or persistent. In case of medical emergency, call your local emergency number immediately. "
        "DEDAN Health and its providers are not liable for any decisions made based on this information."
    )

    DISCLAIMER_SHORT = (
        "This is AI-generated health information, not a medical diagnosis. "
        "Always consult a qualified healthcare professional for medical concerns."
    )

    def __init__(self, country_code: str = "KE"):
        self.country_code = country_code.upper()

    def transform(
        self,
        ai_result: AnalysisResult,
        request_id: str,
        session_id: str,
        patient_context: Optional[PatientContext] = None,
    ) -> AnalyzeResponse:
        """Transform AI result into structured response."""

        # Parse structured data from medical_information
        parsed_data = self._parse_medical_info(ai_result.medical_information)

        # Build possible conditions
        possible_conditions = self._build_possible_conditions(parsed_data)

        # Build first aid steps
        first_aid_steps = self._build_first_aid_steps(parsed_data)

        # Build doctor communication info
        what_to_tell_doctor = self._build_doctor_info(parsed_data, ai_result)

        # Build medicine class recommendation
        recommended_medicine = self._build_medicine_class(parsed_data)

        # Build pharmacy guidance
        pharmacy_guidance = self._build_pharmacy_guidance(parsed_data, recommended_medicine)

        # Build next steps
        next_steps = self._build_next_steps(ai_result.urgency, ai_result.warning_signs)

        # Determine urgency
        urgency = self._map_urgency(ai_result.urgency)

        # Build disclaimer
        disclaimer = Disclaimer(
            text=self.DISCLAIMER_FULL,
            short_version=self.DISCLAIMER_SHORT,
            must_acknowledge=True,
        )

        return AnalyzeResponse(
            request_id=request_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            possible_conditions=possible_conditions,
            urgency_level=urgency,
            urgency_reasoning=ai_result.urgency_reasoning or self._default_urgency_reasoning(urgency),
            first_aid_steps=first_aid_steps,
            what_to_tell_your_doctor=what_to_tell_doctor,
            recommended_medicine_class=recommended_medicine,
            pharmacy_guidance=pharmacy_guidance,
            disclaimer=disclaimer,
            next_steps=next_steps,
            processing_time_ms=ai_result.processing_time_ms,
            ai_provider=ai_result.provider,
            ai_model=ai_result.model,
            confidence_score=ai_result.confidence_score,
            requires_professional_review=ai_result.requires_professional_review,
            safety_flags=ai_result.safety_flags,
            image_assessment=ai_result.image_assessment,
        )

    def _parse_medical_info(self, medical_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse structured data from medical_information list."""
        result = {
            "possible_conditions": [],
            "first_aid_steps": [],
            "what_to_tell_doctor": {},
            "recommended_medicine_class": None,
            "pharmacy_guidance": None,
        }

        for item in medical_info:
            topic = item.get("topic", "")
            content = item.get("content", "")

            try:
                if topic == "possible_conditions":
                    result["possible_conditions"] = json.loads(content)
                elif topic == "first_aid":
                    result["first_aid_steps"] = json.loads(content)
                elif topic == "doctor_communication":
                    result["what_to_tell_doctor"] = json.loads(content)
                elif topic == "medicine_class":
                    result["recommended_medicine_class"] = json.loads(content)
                elif topic == "pharmacy_guidance":
                    result["pharmacy_guidance"] = json.loads(content)
                elif topic == "full_analysis":
                    # Fallback: parse everything from full analysis
                    full = json.loads(content)
                    result["possible_conditions"] = full.get("possible_conditions", [])
                    result["first_aid_steps"] = full.get("first_aid_steps", [])
                    result["what_to_tell_doctor"] = full.get("what_to_tell_doctor", {})
                    result["recommended_medicine_class"] = full.get("recommended_medicine_class")
                    result["pharmacy_guidance"] = full.get("pharmacy_guidance")
            except (json.JSONDecodeError, TypeError):
                continue

        return result

    def _build_possible_conditions(self, parsed: Dict[str, Any]) -> List[PossibleCondition]:
        conditions = []
        for c in parsed.get("possible_conditions", []):
            if not isinstance(c, dict):
                continue
            
            # Map confidence string to enum
            conf_str = c.get("confidence", "low").lower()
            confidence = ConfidenceLevel.MEDIUM
            if conf_str == "high":
                confidence = ConfidenceLevel.HIGH
            elif conf_str == "low":
                confidence = ConfidenceLevel.LOW

            conditions.append(PossibleCondition(
                name=c.get("name", "Unknown condition"),
                confidence=confidence,
                confidence_score=float(c.get("confidence_score", 0.5)),
                reasoning=c.get("reasoning", "Based on reported symptoms and image analysis"),
                supporting_evidence=c.get("supporting_evidence", []),
                contradicting_evidence=c.get("contradicting_evidence", []),
                requires_more_info=c.get("requires_more_info", []),
            ))

        # If no conditions from AI, add generic entry
        if not conditions:
            conditions.append(PossibleCondition(
                name="Undetermined - requires professional evaluation",
                confidence=ConfidenceLevel.LOW,
                confidence_score=0.3,
                reasoning="Insufficient information to suggest specific conditions",
                supporting_evidence=[],
                contradicting_evidence=[],
                requires_more_info=["Physical examination", "Laboratory tests", "Detailed history"],
            ))

        return conditions

    def _build_first_aid_steps(self, parsed: Dict[str, Any]) -> List[FirstAidStep]:
        steps = []
        for i, step in enumerate(parsed.get("first_aid_steps", []), 1):
            if not isinstance(step, dict):
                continue
            
            priority = step.get("priority", "medium").lower()
            if priority not in ["critical", "high", "medium", "low"]:
                priority = "medium"

            steps.append(FirstAidStep(
                step_number=i,
                title=step.get("title", f"Step {i}"),
                description=step.get("description", ""),
                priority=priority,
                time_sensitive=step.get("time_sensitive", False),
                contraindications=step.get("contraindications", []),
            ))

        # Add default steps if none provided
        if not steps:
            steps = self._get_default_first_aid_steps()

        return steps

    def _get_default_first_aid_steps(self) -> List[FirstAidStep]:
        return [
            FirstAidStep(
                step_number=1,
                title="Assess the situation",
                description="Check if the person is conscious, breathing, and has a pulse. Call emergency services immediately if unconscious, not breathing, or severely injured.",
                priority="critical",
                time_sensitive=True,
                contraindications=[],
            ),
            FirstAidStep(
                step_number=2,
                title="Ensure safety",
                description="Make sure the environment is safe for both you and the patient. Move away from danger if needed.",
                priority="critical",
                time_sensitive=True,
                contraindications=["Do not move patient if spinal injury suspected"],
            ),
            FirstAidStep(
                step_number=3,
                title="Monitor vital signs",
                description="Watch breathing, consciousness level, and any bleeding. Note changes to report to medical professionals.",
                priority="high",
                time_sensitive=False,
                contraindications=[],
            ),
            FirstAidStep(
                step_number=4,
                title="Keep patient comfortable",
                description="Position comfortably, loosen tight clothing, keep warm. Do not give food or drink if surgery might be needed.",
                priority="medium",
                time_sensitive=False,
                contraindications=["Do not give anything by mouth if unconscious or abdominal emergency"],
            ),
        ]

    def _build_doctor_info(self, parsed: Dict[str, Any], ai_result: AnalysisResult) -> WhatToTellDoctor:
        doctor_data = parsed.get("what_to_tell_doctor", {})

        key_points = doctor_data.get("key_points", [])
        if not key_points:
            key_points = [
                "Main symptoms and when they started",
                "Any changes in symptoms over time",
                "Home treatments tried and their effect",
            ]

        # Add urgency-specific key points
        if ai_result.urgency in ["emergency", "urgent"]:
            key_points.insert(0, f"URGENCY: AI assessed as {ai_result.urgency.replace('_', ' ').upper()}")

        return WhatToTellDoctor(
            key_points=key_points,
            symptom_timeline=doctor_data.get("symptom_timeline", "Please provide chronological details to your doctor"),
            image_findings=doctor_data.get("image_findings", []),
            home_treatments_tried=doctor_data.get("home_treatments_tried", []),
            questions_to_ask=doctor_data.get("questions_to_ask", [
                "What is the most likely diagnosis?",
                "What tests are needed?",
                "What treatment do you recommend?",
                "When should I return if not better?",
                "Are there any warning signs to watch for?",
            ]),
        )

    def _build_medicine_class(self, parsed: Dict[str, Any]) -> Optional[RecommendedMedicineClass]:
        med_data = parsed.get("recommended_medicine_class")
        if not med_data:
            return None

        return RecommendedMedicineClass(
            medicine_class=med_data.get("medicine_class", "Not specified"),
            generic_examples=med_data.get("generic_examples", []),
            indication=med_data.get("indication", ""),
            mechanism=med_data.get("mechanism", ""),
            important_warnings=med_data.get("important_warnings", [
                "Only take medications prescribed by a qualified healthcare professional",
                "Follow dosage instructions exactly as prescribed",
                "Inform your doctor of all other medications you are taking",
                "Report any side effects immediately",
            ]),
            contraindications=med_data.get("contraindications", []),
            requires_prescription=med_data.get("requires_prescription", True),
            evidence_level=med_data.get("evidence_level", "moderate"),
            source_guideline=med_data.get("source_guideline", "WHO/National guidelines"),
        )

    def _build_pharmacy_guidance(
        self,
        parsed: Dict[str, Any],
        medicine_class: Optional[RecommendedMedicineClass],
    ) -> Optional[PharmacyGuidance]:
        pharm_data = parsed.get("pharmacy_guidance")
        if not pharm_data:
            # Generate default guidance based on country
            return self._get_default_pharmacy_guidance(medicine_class)

        return PharmacyGuidance(
            how_to_obtain=pharm_data.get("how_to_obtain", "Visit a licensed pharmacy with a valid prescription"),
            trusted_sources=pharm_data.get("trusted_sources", self._get_trusted_sources()),
            verification_tips=pharm_data.get("verification_tips", self._get_verification_tips()),
            country_specific=pharm_data.get("country_specific", self._get_country_specific()),
            cost_considerations=pharm_data.get("cost_considerations", self._get_cost_considerations()),
            warning_against=pharm_data.get("warning_against", self._get_warnings_against()),
        )

    def _get_default_pharmacy_guidance(self, medicine_class: Optional[RecommendedMedicineClass]) -> PharmacyGuidance:
        return PharmacyGuidance(
            how_to_obtain=(
                "1. Consult a doctor or clinical officer for proper diagnosis and prescription\n"
                "2. Take the prescription to a licensed pharmacy or government health facility\n"
                "3. Ask the pharmacist to verify the medication matches your prescription\n"
                "4. Check the packaging for tampering, expiry date, and correct drug name\n"
                "5. Ask about proper storage and how to take the medication"
            ),
            trusted_sources=self._get_trusted_sources(),
            verification_tips=self._get_verification_tips(),
            country_specific=self._get_country_specific(),
            cost_considerations=self._get_cost_considerations(),
            warning_against=self._get_warnings_against(),
        )

    def _get_trusted_sources(self) -> List[str]:
        sources = [
            "Government/public hospitals and health centers",
            "Licensed private pharmacies (look for license displayed)",
            "Mission/faith-based health facilities",
            "NGO-supported clinics (MSF, Red Cross, etc.)",
        ]
        if self.country_code == "KE":
            sources.extend([
                "KEMSA (Kenya Medical Supplies Authority) supplied facilities",
                "NHIF-accredited pharmacies",
                "County government health facilities",
            ])
        return sources

    def _get_verification_tips(self) -> List[str]:
        return [
            "Check packaging for batch number, manufacturing date, and expiry date",
            "Verify the drug name (generic) matches your prescription exactly",
            "Look for regulatory authority hologram/sticker (e.g., PPB in Kenya, FDA in US)",
            "Inspect tablets/capsules for unusual color, smell, crumbling, or sticking",
            "Ensure the pharmacy provides a receipt with drug details",
            "Ask the pharmacist to show you the original manufacturer's pack if repackaged",
        ]

    def _get_country_specific(self) -> str:
        guidance = {
            "KE": (
                "In Kenya: Use PPB-licensed pharmacies. NHIF covers many essential medicines "
                "at accredited facilities. KEMSA supplies government facilities. "
                "Report suspected counterfeit drugs to PPB via *254# or 0800 722 000."
            ),
            "TZ": (
                "In Tanzania: Use TFDA-registered pharmacies. Government facilities provide "
                "subsidized medicines. Report concerns to TFDA."
            ),
            "UG": (
                "In Uganda: Use NDA-licensed pharmacies. Public health facilities provide "
                "free essential medicines. Report issues to NDA."
            ),
            "NG": (
                "In Nigeria: Use NAFDAC-registered pharmacies. Check for NAFDAC registration "
                "number on packaging. Report to NAFDAC."
            ),
            "GH": (
                "In Ghana: Use FDA-licensed pharmacies. NHIS covers many medicines at "
                "accredited facilities. Report to FDA Ghana."
            ),
            "RW": (
                "In Rwanda: Use FDA/Rwanda-licensed pharmacies. Community-based health "
                "insurance (Mutuelle) covers essential medicines. Report to Rwanda FDA."
            ),
            "ET": (
                "In Ethiopia: Use EFDA-licensed pharmacies. Public facilities provide "
                "subsidized essential medicines. Report to EFDA."
            ),
        }
        return guidance.get(self.country_code, guidance["KE"])

    def _get_cost_considerations(self) -> str:
        return (
            "Generic medicines are equally effective and much cheaper than brands. "
            "Ask for the generic (INN) name. Check if your insurance (NHIF, NHIS, Mutuelle, etc.) "
            "covers the medication. Government facilities often provide essential medicines free "
            "or at low cost. Some NGOs provide free medicines for specific conditions (TB, HIV, malaria)."
        )

    def _get_warnings_against(self) -> List[str]:
        return [
            "Buying medicines from unlicensed street vendors, markets, or social media",
            "Using leftover prescriptions from others",
            "Taking antibiotics without confirmed bacterial infection",
            "Purchasing 'herbal' or 'traditional' products with undisclosed ingredients",
            "Online pharmacies without proper licensing in your country",
            "Medicines without proper packaging, labels, or expiry dates",
        ]

    def _build_next_steps(self, urgency: str, warning_signs: List[str]) -> NextSteps:
        if urgency == "emergency":
            return NextSteps(
                immediate=[
                    "Call emergency services or go to nearest emergency department NOW",
                    "Do not wait - time is critical",
                    "Bring any medications you're taking",
                    "Bring identification and insurance info if available",
                ],
                within_hours=["Follow up with admitting physician"],
                within_days=["Attend all follow-up appointments"],
                follow_up_with="Emergency department / admitting physician",
            )
        elif urgency == "see_doctor_soon":
            return NextSteps(
                immediate=[
                    "Contact a doctor or clinical officer today",
                    "If symptoms worsen before appointment, go to emergency department",
                ],
                within_hours=[
                    "Schedule appointment within 24 hours",
                    "Prepare notes on symptoms, timeline, and questions",
                ],
                within_days=[
                    "Complete any recommended tests",
                    "Start prescribed treatment",
                    "Return if not improving in 2-3 days",
                ],
                follow_up_with="Primary care doctor / clinical officer",
            )
        else:  # self_care
            return NextSteps(
                immediate=[
                    "Monitor symptoms closely",
                    "Follow first aid guidance provided",
                ],
                within_hours=[
                    "Rest and stay hydrated",
                    "Use over-the-counter relief only as directed on package",
                ],
                within_days=[
                    "If not better in 3-5 days, see a doctor",
                    "If any warning signs appear, seek care immediately",
                ],
                follow_up_with="Primary care provider if symptoms persist",
            )

    def _map_urgency(self, ai_urgency: str) -> UrgencyLevel:
        mapping = {
            "emergency": UrgencyLevel.EMERGENCY,
            "urgent": UrgencyLevel.SEE_DOCTOR_SOON,
            "see_doctor_soon": UrgencyLevel.SEE_DOCTOR_SOON,
            "routine": UrgencyLevel.SEE_DOCTOR_SOON,
            "self_care": UrgencyLevel.SELF_CARE,
        }
        return mapping.get(ai_urgency.lower(), UrgencyLevel.SEE_DOCTOR_SOON)

    def _default_urgency_reasoning(self, urgency: UrgencyLevel) -> str:
        reasons = {
            UrgencyLevel.EMERGENCY: "Symptoms suggest a potentially life-threatening condition requiring immediate emergency care",
            UrgencyLevel.SEE_DOCTOR_SOON: "Symptoms warrant professional medical evaluation within 24 hours",
            UrgencyLevel.SELF_CARE: "Symptoms appear manageable with self-care but monitor for changes",
        }
        return reasons.get(urgency, "Urgency assessed based on reported symptoms")


# Global transformer instance
response_transformer = ResponseTransformer()