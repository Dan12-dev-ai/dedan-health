"""
Urgency Engine — DEDAN Health 2.0

Safety classification that NEVER silently downgrades emergency states.
"""

from __future__ import annotations

import re
from typing import List, Optional

from clinical_schema import (
    UrgencyLevel, SafetyClassification, UncertaintyStatement,
    EMERGENCY_KEYWORDS, URGENT_KEYWORDS, ROUTINE_KEYWORDS,
)


class UrgencyEngine:
    """Classifies urgency from patient-reported text. Never downgrades emergency."""

    def __init__(self):
        self.emergency_patterns = self._compile(EMERGENCY_KEYWORDS)
        self.urgent_patterns = self._compile(URGENT_KEYWORDS)
        self.routine_patterns = self._compile(ROUTINE_KEYWORDS)

    @staticmethod
    def _compile(keywords: List[str]) -> List[re.Pattern]:
        return [re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE) for k in keywords]

    def classify(
        self,
        symptoms: str,
        severity: Optional[str] = None,
        duration: Optional[str] = None,
        red_flags: Optional[List[str]] = None,
    ) -> SafetyClassification:
        text = f"{symptoms} {severity or ''} {duration or ''}".lower()

        # Check explicit red flags first — these override everything
        explicit_red_flags = list(red_flags or [])
        for pattern in self.emergency_patterns:
            if pattern.search(text):
                return SafetyClassification(
                    urgency=UrgencyLevel.EMERGENCY,
                    red_flags=explicit_red_flags + [f"Detected emergency indicator: {pattern.pattern}"],
                    requires_immediate_care=True,
                    emergency_message=(
                        "EMERGENCY: Based on your reported symptoms, you may need "
                        "immediate emergency care. Call emergency services now or go to the nearest ER."
                    ),
                    recommended_action="Seek emergency care immediately. Do not wait.",
                    professional_review_required=True,
                )

        for pattern in self.urgent_patterns:
            if pattern.search(text):
                return SafetyClassification(
                    urgency=UrgencyLevel.URGENT,
                    red_flags=explicit_red_flags,
                    requires_immediate_care=False,
                    emergency_message=None,
                    recommended_action="Seek medical care within 24 hours.",
                    professional_review_required=True,
                )

        for pattern in self.routine_patterns:
            if pattern.search(text):
                return SafetyClassification(
                    urgency=UrgencyLevel.ROUTINE,
                    red_flags=explicit_red_flags,
                    requires_immediate_care=False,
                    emergency_message=None,
                    recommended_action="Monitor symptoms. Schedule routine follow-up if they persist.",
                    professional_review_required=False,
                )

        # Default: uncertain
        return SafetyClassification(
            urgency=UrgencyLevel.SOON,
            red_flags=explicit_red_flags,
            requires_immediate_care=False,
            emergency_message=None,
            recommended_action="More information needed. Consult a healthcare professional if symptoms worsen.",
            professional_review_required=True,
        )

    def requires_emergency_display(self, urgency: UrgencyLevel) -> bool:
        return urgency == UrgencyLevel.EMERGENCY
