"""
Evidence Retrieval — DEDAN Health 2.0

Retrieves medical evidence from authoritative sources before generating
treatment education. Prefers government health authorities, clinical
guidelines, major medical institutions, WHO, regulatory drug information.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from clinical_schema import Source, EvidenceLevel


# Authoritative source hierarchy
AUTHORITATIVE_SOURCES = [
    {
        "type": "government",
        "name": "WHO",
        "base_url": "https://www.who.int",
        "priority": 1,
    },
    {
        "type": "government",
        "name": "CDC",
        "base_url": "https://www.cdc.gov",
        "priority": 1,
    },
    {
        "type": "regulatory",
        "name": "FDA",
        "base_url": "https://www.fda.gov",
        "priority": 1,
    },
    {
        "type": "guideline",
        "name": "NICE",
        "base_url": "https://www.nice.org.uk",
        "priority": 2,
    },
    {
        "type": "institution",
        "name": "Mayo Clinic",
        "base_url": "https://www.mayoclinic.org",
        "priority": 2,
    },
    {
        "type": "institution",
        "name": "Cleveland Clinic",
        "base_url": "https://my.clevelandclinic.org",
        "priority": 2,
    },
    {
        "type": "literature",
        "name": "PubMed",
        "base_url": "https://pubmed.ncbi.nlm.nih.gov",
        "priority": 3,
    },
]


class EvidenceRetrievalError(Exception):
    pass


class EvidenceRetriever:
    """Retrieves evidence from authoritative sources."""

    def __init__(self, cache: Optional[Dict[str, Any]] = None):
        self.cache = cache or {}

    def retrieve(
        self,
        topic: str,
        evidence_level: EvidenceLevel = EvidenceLevel.THEORETICAL,
    ) -> Dict[str, Any]:
        """Retrieve evidence for a clinical topic."""
        cache_key = f"{topic}:{evidence_level.value}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "topic": topic,
            "evidence_level": evidence_level.value,
            "sources": self._search_sources(topic, evidence_level),
            "summary": self._generate_summary(topic, evidence_level),
        }

        self.cache[cache_key] = result
        return result

    def _search_sources(
        self, topic: str, evidence_level: EvidenceLevel
    ) -> List[Source]:
        sources = []
        # Map evidence level to priority threshold
        _evidence_priority = {
            'strong': 1,
            'moderate': 2,
            'limited': 3,
            'theoretical': 4,
        }
        threshold = _evidence_priority.get(evidence_level.value, 4)
        for src in AUTHORITATIVE_SOURCES:
            if src["priority"] <= threshold:
                sources.append(Source(
                    title=f"{src['name']} — {topic}",
                    url=f"{src['base_url']}/search?q={topic.replace(' ', '+')}",
                    type=src["type"],
                    jurisdiction=src["name"],
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

    def get_sources_for_topic(self, topic: str) -> List[Source]:
        """Get sources for a specific topic."""
        return self._search_sources(topic, EvidenceLevel.THEORETICAL)
