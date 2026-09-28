import json
import math
import os
import re
from typing import Dict, Any, List, Optional
import numpy as np

from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------------
# Optional heavy dependencies.
#
# chromadb + sentence-transformers (torch) are NOT installed in this
# environment. When unavailable we degrade to a deterministic in-memory
# lexical retriever backed by the bundled WHO guideline JSON, so the agent
# still returns sourced, relevant guidance instead of failing to import.
# ---------------------------------------------------------------------------
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in this environment
    chromadb = None
    Settings = None
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in this environment
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class _HashingEmbedder:
    """Deterministic hashed bag-of-words embedder (chroma-compatible subset).

    Implements `encode(List[str]) -> np.ndarray` so call sites that expect a
    SentenceTransformer keep working. Cosine similarity over these vectors
    approximates lexical overlap, which is sufficient for guideline retrieval
    over a small curated corpus.
    """

    DIM = 512

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in re.findall(r"[a-z0-9']+", (text or "").lower()):
                # Stable hash -> bucket; sign reduces collisions.
                h = int.from_bytes(
                    __import__("hashlib").sha1(token.encode("utf-8")).digest()[:4],
                    "big",
                )
                vectors[row, h % self.DIM] += 1.0 if (h >> 16) & 1 else -1.0
            norm = float(np.linalg.norm(vectors[row]))
            if norm > 0:
                vectors[row] /= norm
        return vectors


class _InMemoryCollection:
    """Minimal Chroma-compatible collection backed by process-local storage."""

    def __init__(self, name: str = "guidelines"):
        self.name = name
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []

    def add(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

    def query(self, query_embeddings, n_results: int = 5, include=None) -> Dict[str, Any]:
        if not self.documents:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        embedder = _HashingEmbedder()
        corpus = embedder.encode(self.documents)
        scored = []
        for q in np.atleast_2d(np.asarray(query_embeddings, dtype=np.float32)):
            qn = q / (np.linalg.norm(q) or 1.0)
            sims = corpus @ qn
            scored.append(sorted(range(len(sims)), key=lambda i: -sims[i])[:n_results])

        return {
            "documents": [[self.documents[i] for i in idxs] for idxs in scored],
            "metadatas": [[self.metadatas[i] for i in idxs] for idxs in scored],
            "distances": [[1.0 - float(corpus[i] @ (q / (np.linalg.norm(q) or 1.0)))
                           for i in idxs]
                          for q, idxs in zip(np.atleast_2d(np.asarray(query_embeddings,
                                                                     dtype=np.float32)), scored)],
        }

    def count(self) -> int:
        return len(self.documents)

from .base_agent import BaseDEDANAgent
try:
    from models_v2 import (
    AgentInput, AgentOutput, AgentType,
    GuidelineAgentInput, GuidelineAgentOutput,
    TriageAgentOutput, SafetyGuardAgentOutput, Language
    )
except ImportError:  # pragma: no cover - package-relative fallback
    from ..models_v2 import (
    AgentInput, AgentOutput, AgentType,
    GuidelineAgentInput, GuidelineAgentOutput,
    TriageAgentOutput, SafetyGuardAgentOutput, Language
    )

class GuidelineAgent(BaseDEDANAgent):
    """
    DEDAN Guideline Agent - Clinical guideline retrieval and context.
    Pulls relevant guidelines from local clinical knowledge base.
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_type=AgentType.GUIDELINE, **kwargs)
        self.using_chroma = CHROMA_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE
        if self.using_chroma:
            self.chroma_client = chromadb.PersistentClient(
                path="./data/clinical_guidelines_db",
                settings=Settings(allow_reset=False)
            )
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            # Degrade to in-memory lexical retrieval over bundled WHO JSON.
            self.chroma_client = None
            self.embeddings_model = _HashingEmbedder()
            self._corpus_loaded = False
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections for different guideline types."""
        
        # Create collections for different languages and regions
        self.collections = {}
        
        languages = [lang.value for lang in Language]
        
        for lang in languages:
            try:
                if not self.using_chroma:
                    self.collections[lang] = _InMemoryCollection(f"guidelines_{lang}")
                    continue
                collection_name = f"guidelines_{lang}"
                self.collections[lang] = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"Error creating collection for {lang}: {e}")
                # Fallback to English collection
                if lang != 'en':
                    self.collections[lang] = self.collections.get('en')

        if not self.using_chroma:
            self._load_bundled_guidelines()

    def _load_bundled_guidelines(self):
        """Seed the in-memory collections from data/clinical_guidelines/*.json.

        ChromaDB is optional; without it we still want real, sourced guidance
        rather than an empty corpus. Idempotent (guarded by _corpus_loaded).
        """
        if getattr(self, "_corpus_loaded", False):
            return
        self._corpus_loaded = True

        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "clinical_guidelines")
        )
        if not os.path.isdir(base_dir):
            print(f"Guideline directory not found: {base_dir}")
            return

        for filename in sorted(os.listdir(base_dir)):
            if not filename.endswith(".json"):
                continue
            stem = filename.rsplit(".", 1)[0]
            lang = "en"
            if stem.startswith("swahili"):
                lang = "sw"
            elif stem.startswith("amharic"):
                lang = "am"
            self.load_guidelines_to_database(
                os.path.join(base_dir, filename), language=lang
            )
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build specialized prompt template for guideline analysis."""
        
        template = """
You are a clinical guideline specialist for DEDAN Health.
Your role is to analyze triage decisions against local clinical guidelines and provide evidence-based recommendations.

CLINICAL GUIDELINE SOURCES:
- WHO guidelines for primary care
- Local Ministry of Health guidelines
- Regional disease prevalence data
- Evidence-based practice guidelines

GUIDELINE ANALYSIS CRITERIA:
1. Evidence level and quality
2. Regional disease patterns
3. Local resource availability
4. Cultural and language considerations
5. Cost-effectiveness for underserved regions

PATIENT INFORMATION:
{patient_info}

SYMPTOMS:
{symptoms}

TRIAGE ASSESSMENT:
{triage_output}

SAFETY ASSESSMENT:
{safety_output}

{language_context}

{region_context}

RETRIEVED GUIDELINES:
{guidelines}

GUIDELINE ANALYSIS INSTRUCTIONS:
1. Compare triage decision against retrieved guidelines
2. Consider regional disease prevalence
3. Account for local resource constraints
4. Evaluate evidence quality
5. Provide specific recommendations

RESPONSE FORMAT:
Provide your analysis in this exact JSON format:
{{
    "relevant_guidelines": [
        {{
            "source": "WHO/Local MoH/etc",
            "condition": "specific condition",
            "recommendation": "specific recommendation",
            "evidence_level": "A/B/C/D",
            "relevance_score": 0.85
        }}
    ],
    "local_considerations": ["consideration1", "consideration2"],
    "evidence_level": "A/B/C/D",
    "recommendations": ["recommendation1", "recommendation2"],
    "reasoning": "Detailed guideline analysis",
    "confidence": 0.90
}}

IMPORTANT LOCAL CONSIDERATIONS:
- Malaria endemic regions: Consider malaria testing for fever
- Limited diagnostics: Emphasize clinical assessment
- Resource constraints: Recommend cost-effective approaches
- Cultural factors: Consider traditional medicine use

{chronic_care_info}

{home_measurements}

Respond with ONLY JSON format above. Ensure recommendations are practical for underserved regions.
"""
        
        return ChatPromptTemplate.from_template(template)
    
    def _process_agent_specific_logic(self, input_data: GuidelineAgentInput) -> Dict[str, Any]:
        """Process guideline agent specific logic."""
        
        # Retrieve relevant guidelines
        relevant_guidelines = self._retrieve_guidelines(input_data)
        
        # Extract local considerations
        local_considerations = self._extract_local_considerations(input_data)
        
        # Determine overall evidence level
        evidence_level = self._determine_evidence_level(relevant_guidelines)
        
        # Generate specific recommendations
        recommendations = self._generate_guideline_recommendations(
            input_data, relevant_guidelines, local_considerations
        )
        
        return {
            "relevant_guidelines": relevant_guidelines,
            "local_considerations": local_considerations,
            "evidence_level": evidence_level,
            "recommendations": recommendations
        }
    
    def _retrieve_guidelines(self, input_data: GuidelineAgentInput) -> List[Dict[str, Any]]:
        """Retrieve relevant clinical guidelines using semantic search."""
        
        try:
            # Get appropriate collection based on language
            language = input_data.symptoms.language.value
            collection = self.collections.get(language, self.collections.get('en'))
            
            if not collection:
                return []
            
            # Create search query from symptoms
            symptoms_text = input_data.symptoms.symptoms
            triage_output = input_data.triage_output
            
            search_query = f"{symptoms_text} {triage_output.triage_level}"
            
            # Generate embedding for search
            query_embedding = self.embeddings_model.encode([search_query])
            
            # Search for relevant guidelines
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            guidelines = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                guidelines.append({
                    "source": metadata.get('source', 'Unknown'),
                    "condition": metadata.get('condition', 'Unknown'),
                    "recommendation": doc,
                    "evidence_level": metadata.get('evidence_level', 'C'),
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                    "region": metadata.get('region', 'Global'),
                    "language": metadata.get('language', language)
                })
            
            return guidelines
            
        except Exception as e:
            print(f"Error retrieving guidelines: {e}")
            return []
    
    def _extract_local_considerations(self, input_data: GuidelineAgentInput) -> List[str]:
        """Extract local and regional considerations."""
        
        considerations = []
        patient = input_data.patient
        symptoms_text = input_data.symptoms.symptoms.lower()
        location = patient.location.lower() if patient.location else ""
        
        # Regional disease considerations
        if any(country in location for country in ["kenya", "tanzania", "uganda"]):
            if "fever" in symptoms_text:
                considerations.append("High malaria prevalence - consider malaria testing")
            if "cough" in symptoms_text:
                considerations.append("High TB prevalence - consider TB screening")
        
        elif any(country in location for country in ["ethiopia", "eritrea"]):
            if "fever" in symptoms_text:
                considerations.append("High malaria and typhoid prevalence")
            if "malnutrition" in symptoms_text or "weight loss" in symptoms_text:
                considerations.append("Consider nutritional deficiencies")
        
        elif any(country in location for country in ["nigeria", "ghana", "senegal"]):
            if "fever" in symptoms_text:
                considerations.append("Consider malaria, Lassa fever, and typhoid")
            if "pain" in symptoms_text and "joint" in symptoms_text:
                considerations.append("High sickle cell disease prevalence")
        
        # Resource constraint considerations
        considerations.append("Limited diagnostic imaging available")
        considerations.append("Prioritize clinical examination over tests")
        considerations.append("Consider cost-effectiveness of recommendations")
        
        # Age-specific considerations
        if patient.age < 5:
            considerations.append("Pediatric dosing adjustments needed")
            considerations.append("Higher risk of severe malaria")
        elif patient.age > 65:
            considerations.append("Multiple comorbidities likely")
            considerations.append("Medication interaction risks higher")
        
        # Chronic disease considerations
        if patient.chronic_conditions:
            considerations.append("Chronic disease management may affect acute presentation")
            considerations.append("Consider medication side effects")
        
        # Pregnancy considerations
        if patient.pregnancy_status:
            considerations.append("Pregnancy-safe medication options only")
            considerations.append("Higher risk of malaria complications")
            considerations.append("Consider obstetric emergencies")
        
        # Seasonal considerations (simplified)
        import datetime
        current_month = datetime.datetime.now().month
        if current_month in [11, 12, 1, 2]:  # Rainy season in many regions
            considerations.append("Peak malaria transmission season")
        
        return list(set(considerations))
    
    def _determine_evidence_level(self, guidelines: List[Dict[str, Any]]) -> str:
        """Determine overall evidence level from retrieved guidelines."""
        
        if not guidelines:
            return "D"  # No evidence available
        
        # Count evidence levels
        evidence_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
        
        for guideline in guidelines:
            level = guideline.get('evidence_level', 'D')
            if level in evidence_counts:
                evidence_counts[level] += 1
        
        # Determine overall level based on highest quality evidence
        if evidence_counts["A"] > 0:
            return "A"
        elif evidence_counts["B"] > 0:
            return "B"
        elif evidence_counts["C"] > 0:
            return "C"
        else:
            return "D"
    
    def _generate_guideline_recommendations(
        self, 
        input_data: GuidelineAgentInput,
        guidelines: List[Dict[str, Any]],
        local_considerations: List[str]
    ) -> List[str]:
        """Generate specific recommendations based on guidelines and local context."""
        
        recommendations = []
        symptoms_text = input_data.symptoms.symptoms.lower()
        triage_level = input_data.triage_output.triage_level
        safety_output = input_data.safety_output
        
        # Base recommendations from guidelines
        for guideline in guidelines[:3]:  # Top 3 most relevant
            rec = guideline.get('recommendation', '')
            if rec and len(rec) > 10:
                recommendations.append(rec[:200])  # Limit length
        
        # Symptom-specific recommendations
        if "fever" in symptoms_text:
            recommendations.append("Monitor temperature every 4 hours")
            recommendations.append("Maintain hydration with oral rehydration solution")
            
        if "cough" in symptoms_text:
            recommendations.append("Monitor breathing rate and difficulty")
            recommendations.append("Consider TB screening if >2 weeks duration")
        
        if "diarrhea" in symptoms_text:
            recommendations.append("Maintain hydration with ORS")
            recommendations.append("Monitor for signs of dehydration")
        
        if "pain" in symptoms_text:
            recommendations.append("Use paracetamol for mild to moderate pain")
            recommendations.append("Avoid NSAIDs in pregnancy or with stomach issues")
        
        # Triage level specific recommendations
        if triage_level == "emergency":
            recommendations.append("Immediate referral to emergency care")
            recommendations.append("Arrange transport if available")
        elif triage_level == "urgent":
            recommendations.append("Seek medical care within 24 hours")
            recommendations.append("Monitor for deterioration")
        elif triage_level == "routine":
            recommendations.append("Schedule appointment within 1-2 weeks")
            recommendations.append("Self-monitor for worsening symptoms")
        
        # Safety-specific recommendations
        if safety_output.emergency_detected:
            recommendations.append("Emergency protocol activated")
            recommendations.append("Prepare for rapid transport")
        
        # Remove duplicates and limit
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:8]  # Limit to 8 recommendations
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate guideline agent output."""
        
        required_fields = [
            'relevant_guidelines', 'local_considerations', 
            'evidence_level', 'recommendations'
        ]
        
        for field in required_fields:
            if field not in output:
                return False
        
        # Validate lists
        if not isinstance(output['relevant_guidelines'], list):
            return False
        
        if not isinstance(output['local_considerations'], list):
            return False
        
        if not isinstance(output['recommendations'], list):
            return False
        
        # Validate evidence level
        valid_levels = ['A', 'B', 'C', 'D']
        if output['evidence_level'] not in valid_levels:
            return False
        
        return True
    
    def load_guidelines_to_database(self, guidelines_file: str, language: str = 'en'):
        """Load guidelines from JSON file into ChromaDB."""
        
        try:
            with open(guidelines_file, 'r', encoding='utf-8') as f:
                guidelines = json.load(f)
            
            collection = self.collections.get(language, self.collections.get('en'))
            if not collection:
                print(f"No collection available for language: {language}")
                return
            
            # Prepare documents for insertion
            documents = []
            metadatas = []
            ids = []
            
            for i, guideline in enumerate(guidelines):
                doc = f"{guideline['condition']}: {guideline['recommendations']}"
                documents.append(doc)
                
                metadata = {
                    'source': guideline.get('source', 'Unknown'),
                    'condition': guideline.get('condition', 'Unknown'),
                    'evidence_level': guideline.get('evidence_level', 'C'),
                    'region': guideline.get('region', 'Global'),
                    'language': language
                }
                metadatas.append(metadata)
                ids.append(f"{language}_{i}")
            
            # Add to collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Loaded {len(guidelines)} guidelines for {language}")
            
        except Exception as e:
            print(f"Error loading guidelines: {e}")
