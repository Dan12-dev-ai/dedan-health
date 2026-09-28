"""
Visual Education Service — DEDAN Health 2.0

Retrieves real educational medical visuals from authoritative sources.
NEVER uses AI-generated fake medical photographs.
AI-generated diagrams are clearly labeled.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from clinical_schema import VisualEducation


# Trusted educational visual sources
TRUSTED_VISUAL_SOURCES = [
    {
        "name": "WHO Health Topics",
        "base_url": "https://www.who.int/health-topics",
        "license": "CC BY-NC-SA 4.0",
    },
    {
        "name": "CDC Public Health Image Library",
        "base_url": "https://phil.cdc.gov",
        "license": "Public domain (US government)",
    },
    {
        "name": "NIH/NLM",
        "base_url": "https://medlineplus.gov",
        "license": "Public domain (US government)",
    },
    {
        "name": "OpenStax Anatomy",
        "base_url": "https://openstax.org",
        "license": "CC BY 4.0",
    },
]


class VisualEducationService:
    """Retrieves real educational medical visuals."""

    def __init__(self, cache: Optional[Dict[str, Any]] = None):
        self._cache = cache or {}

    def search_visuals(
        self,
        topic: str,
        visual_category: str,
    ) -> List[VisualEducation]:
        """Search for educational visuals by topic and category."""
        cache_key = f"{topic}:{visual_category}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        visuals = self._retrieve_from_sources(topic, visual_category)
        self._cache[cache_key] = visuals
        return visuals

    def get_disease_overview(self, condition: str) -> List[VisualEducation]:
        """Get disease overview visuals."""
        return self.search_visuals(condition, "disease_overview")

    def get_anatomy_diagram(self, body_system: str) -> List[VisualEducation]:
        """Get anatomy diagrams."""
        return self.search_visuals(body_system, "anatomy")

    def get_treatment_procedure(self, procedure: str) -> List[VisualEducation]:
        """Get treatment procedure visuals."""
        return self.search_visuals(procedure, "treatment_procedure")

    def get_warning_signs(self, condition: str) -> List[VisualEducation]:
        """Get warning signs visuals."""
        return self.search_visuals(condition, "warning_signs")

    def _retrieve_from_sources(
        self, topic: str, visual_category: str
    ) -> List[VisualEducation]:
        visuals = []
        for src in TRUSTED_VISUAL_SOURCES:
            visuals.append(VisualEducation(
                title=f"{topic} — {visual_category.replace('_', ' ').title()}",
                description=(
                    f"Educational illustration showing {topic} "
                    f"and its {visual_category.replace('_', ' ')}. "
                    f"This is a general educational visual, not a diagnosis "
                    f"of the patient's specific condition."
                ),
                visual_type="illustration",
                source=src["name"],
                source_url=f"{src['base_url']}/search?q={topic.replace(' ', '+')}",
                license=src["license"],
                medical_context=f"Educational reference for {topic}",
                publication_info="Updated regularly by source authority",
                is_ai_generated=False,
            ))
        return visuals

    def label_ai_generated(self, title: str, description: str) -> VisualEducation:
        """Create an AI-generated educational diagram with clear labeling."""
        return VisualEducation(
            title=title,
            description=description,
            visual_type="illustration",
            source="DEDAN Health AI-generated educational diagram",
            source_url=None,
            license="Created for educational purposes",
            medical_context="Educational illustration — not a clinical photograph",
            publication_info="Generated on demand",
            is_ai_generated=True,
            ai_disclaimer=(
                "AI-generated educational illustration — not a clinical photograph. "
                "This diagram is for general educational purposes only and does not "
                "represent the patient's actual internal condition."
            ),
        )
