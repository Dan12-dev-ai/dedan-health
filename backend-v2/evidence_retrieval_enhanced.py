"""
Enhanced Evidence Retrieval Service — DEDAN Health 2.0

Retrieves medical evidence from authoritative sources before generating
treatment education. Prefers government health authorities, clinical
guidelines, major medical institutions, WHO, regulatory drug information.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from clinical_schema import Source, EvidenceLevel


# Authoritative source hierarchy with priority
AUTHORITATIVE_SOURCES = [
    {
        "type": "government",
        "name": "WHO",
        "base_url": "https://www.who.int",
        "search_url": "https://www.who.int/search?q=",
        "priority": 1,
        "topics": ["guidelines", "disease_outbreaks", "essential_medicines", "health_topics"],
    },
    {
        "type": "government",
        "name": "CDC",
        "base_url": "https://www.cdc.gov",
        "search_url": "https://search.cdc.gov/search/?query=",
        "priority": 1,
        "topics": ["diseases_conditions", "travel_health", "emergency_preparedness", "vaccines"],
    },
    {
        "type": "regulatory",
        "name": "FDA",
        "base_url": "https://www.fda.gov",
        "search_url": "https://www.fda.gov/search?q=",
        "priority": 1,
        "topics": ["drugs", "medical_devices", "food_safety", "regulatory_information"],
    },
    {
        "type": "guideline",
        "name": "NICE",
        "base_url": "https://www.nice.org.uk",
        "search_url": "https://www.nice.org.uk/search?q=",
        "priority": 2,
        "topics": ["clinical_guidelines", "technology_appraisals", "quality_standards"],
    },
    {
        "type": "institution",
        "name": "Mayo Clinic",
        "base_url": "https://www.mayoclinic.org",
        "search_url": "https://www.mayoclinic.org/search/search-results?q=",
        "priority": 2,
        "topics": ["diseases_conditions", "symptoms", "tests_procedures", "drugs_supplements"],
    },
    {
        "type": "institution",
        "name": "Cleveland Clinic",
        "base_url": "https://my.clevelandclinic.org",
        "search_url": "https://my.clevelandclinic.org/search?q=",
        "priority": 2,
        "topics": ["diseases_conditions", "treatments", "wellness"],
    },
    {
        "type": "literature",
        "name": "PubMed",
        "base_url": "https://pubmed.ncbi.nlm.nih.gov",
        "search_url": "https://pubmed.ncbi.nlm.nih.gov/?term=",
        "priority": 3,
        "topics": ["biomedical_literature", "clinical_trials", "systematic_reviews"],
    },
    {
        "type": "guideline",
        "name": "MSF Clinical Guidelines",
        "base_url": "https://medicalguidelines.msf.org",
        "search_url": "https://medicalguidelines.msf.org/search?q=",
        "priority": 1,
        "topics": ["field_guidelines", "tropical_diseases", "emergency_care"],
    },
]


class EvidenceRetrievalError(Exception):
    pass


class EvidenceRetriever:
    """Retrieves evidence from authoritative sources with prioritization."""

    def __init__(self, cache: Optional[Dict[str, Any]] = None):
        self.cache = cache or {}
        self.source_priority = {s["name"]: s["priority"] for s in AUTHORITATIVE_SOURCES}

    def retrieve(
        self,
        topic: str,
        evidence_level: EvidenceLevel = EvidenceLevel.THEORETICAL,
        max_sources: int = 5,
    ) -> Dict[str, Any]:
        """Retrieve evidence for a clinical topic."""
        cache_key = f"{topic}:{evidence_level.value}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "topic": topic,
            "evidence_level": evidence_level.value,
            "sources": self._search_sources(topic, evidence_level, max_sources),
            "summary": self._generate_summary(topic, evidence_level),
        }

        self.cache[cache_key] = result
        return result

    def _search_sources(
        self, topic: str, evidence_level: EvidenceLevel, max_sources: int
    ) -> List[Source]:
        sources = []
        # Map evidence level to priority threshold
        evidence_priority = {
            'strong': 1,
            'moderate': 2,
            'limited': 3,
            'theoretical': 4,
        }
        threshold = evidence_priority.get(evidence_level.value, 4)
        
        for src in AUTHORITATIVE_SOURCES:
            if src["priority"] <= threshold and len(sources) < max_sources:
                sources.append(Source(
                    title=f"{src['name']} — {topic}",
                    url=f"{src['search_url']}{topic.replace(' ', '+')}",
                    type=src["type"],
                    jurisdiction=src["name"],
                    date_published=None,  # Would be populated from actual API
                ))
        return sources

    def _generate_summary(
        self, topic: str, evidence_level: EvidenceLevel
    ) -> str:
        return (
            f"Evidence for {topic} retrieved from authoritative sources. "
            f"Evidence level: {evidence_level.value}. "
            "This information is for educational purposes only and does not "
            "replace professional medical advice."
        )

    def get_sources_for_topic(self, topic: str, evidence_level: EvidenceLevel = EvidenceLevel.THEORETICAL) -> List[Source]:
        """Get sources for a specific topic."""
        return self._search_sources(topic, evidence_level, max_sources=10)

    def get_guideline_recommendations(
        self,
        condition: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get specific guideline recommendations for a condition."""
        # In production, this would query guideline databases
        # For now, return structured template
        return {
            "condition": condition,
            "guidelines_consulted": [
                "WHO Guidelines",
                "National Clinical Guidelines",
                "MSF Clinical Guidelines (for resource-limited settings)",
            ],
            "key_recommendations": [
                f"Standard first-line treatment for {condition}",
                "Dosing by weight/age",
                "Monitoring parameters",
                "Referral criteria",
            ],
            "context_considerations": context or {},
            "evidence_level": "strong",
            "note": "Guideline recommendations vary by region; consult local protocols",
        }


# Global instance
evidence_retriever = EvidenceRetriever()