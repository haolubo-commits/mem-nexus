"""
Semantic Triplet & Entity Extractor for MemNexus.
Extracts (Subject -> Predicate -> Object) triplets and classifies entities from conversation turns.
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from app.models.entity import EntityType

logger = logging.getLogger("mem_nexus.extractor")


class ExtractedTriplet:
    def __init__(
        self,
        source: str,
        predicate: str,
        target: str,
        confidence: float,
        source_type: EntityType = EntityType.CONCEPT,
        target_type: EntityType = EntityType.CONCEPT,
        evidence: str = "",
    ):
        self.source = source
        self.predicate = predicate
        self.target = target
        self.confidence = confidence
        self.source_type = source_type
        self.target_type = target_type
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "predicate": self.predicate,
            "target": self.target,
            "confidence": self.confidence,
            "source_type": self.source_type.value,
            "target_type": self.target_type.value,
            "evidence": self.evidence,
        }


class TripletExtractor:
    """
    Heuristic and rule-based semantic extractor designed to turn agent/user statements
    into structured entity nodes and relational graph edges.
    """

    PATTERNS: List[Tuple[re.Pattern, str, EntityType, EntityType, float]] = [
        # Preferences: "User prefers Python over JavaScript", "I love dark mode"
        (
            re.compile(r"(?i)\b(i|user|developer|we)\s+(?:strongly\s+)?(prefers?|likes?|loves?|favor[s]?)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\s+over|\s+to|\.|$)", re.IGNORECASE),
            "prefers",
            EntityType.PERSON,
            EntityType.PREFERENCE,
            0.92,
        ),
        # Dependencies / Tech Stack: "Project uses FastAPI", "We rely on MongoDB"
        (
            re.compile(r"(?i)\b([a-zA-Z0-9_\-\.]+)\s+(?:heavily\s+)?(uses|relies\s+on|depends\s+on|utilizes|implements)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\s+for|\s+in|\.|$)", re.IGNORECASE),
            "depends_on",
            EntityType.TOOL,
            EntityType.TOOL,
            0.88,
        ),
        # Author / Creator: "Guido created Python", "Alice authored the spec"
        (
            re.compile(r"(?i)\b([a-zA-Z0-9_\-\.]+)\s+(created|authored|designed|built|developed|leads?)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\s+using|\.|$)", re.IGNORECASE),
            "authored",
            EntityType.PERSON,
            EntityType.TASK,
            0.90,
        ),
        # Affiliation / Work: "Bob works at OpenAI", "Carol is employed by Google"
        (
            re.compile(r"(?i)\b([a-zA-Z0-9_\-\.]+)\s+(?:currently\s+)?(works\s+at|is\s+employed\s+by|joined|consults\s+for)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\s+as|\.|$)", re.IGNORECASE),
            "works_at",
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            0.94,
        ),
        # Location: "Server is located in us-east-1", "HQ is based in Berlin"
        (
            re.compile(r"(?i)\b([a-zA-Z0-9_\-\.]+)\s+(?:is\s+)?(located\s+in|based\s+in|hosted\s+in|deployed\s+to)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\.|$)", re.IGNORECASE),
            "located_in",
            EntityType.TOOL,
            EntityType.LOCATION,
            0.87,
        ),
        # Attribute / Configuration: "Postgres version is 16", "Timeout is set to 30s"
        (
            re.compile(r"(?i)\b([a-zA-Z0-9_\-\.]+)\s+(?:version\s+|timeout\s+|setting\s+)?(is|is\s+configured\s+as|equals|has\s+attribute)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\.|$)", re.IGNORECASE),
            "has_attribute",
            EntityType.TOOL,
            EntityType.ATTRIBUTE,
            0.82,
        ),
        # Interaction / Connection: "Agent interacts with User", "Service connects to Database"
        (
            re.compile(r"(?i)\b([a-zA-Z0-9_\-\.]+)\s+(interacts\s+with|connects\s+to|communicates\s+with|queries)\s+([a-zA-Z0-9_\-\.\s]+?)(?:\.|$)", re.IGNORECASE),
            "interacts_with",
            EntityType.TOOL,
            EntityType.TOOL,
            0.85,
        ),
    ]

    KNOWN_ENTITY_MAP: Dict[str, Tuple[str, EntityType]] = {
        "fastapi": ("FastAPI", EntityType.TOOL),
        "python": ("Python", EntityType.TOOL),
        "mongodb": ("MongoDB", EntityType.TOOL),
        "postgres": ("PostgreSQL", EntityType.TOOL),
        "postgresql": ("PostgreSQL", EntityType.TOOL),
        "react": ("React", EntityType.TOOL),
        "docker": ("Docker", EntityType.TOOL),
        "kubernetes": ("Kubernetes", EntityType.TOOL),
        "redis": ("Redis", EntityType.TOOL),
        "openai": ("OpenAI", EntityType.ORGANIZATION),
        "google": ("Google", EntityType.ORGANIZATION),
        "anthropic": ("Anthropic", EntityType.ORGANIZATION),
        "user": ("User", EntityType.PERSON),
        "agent": ("Agent", EntityType.TOOL),
    }

    @classmethod
    def clean_entity_name(cls, raw: str) -> str:
        s = raw.strip().strip(",.;:'\"`()[]{}")
        # Remove trailing articles or prepositions
        s = re.sub(r"\s+(and|or|with|at|in|by)$", "", s, flags=re.IGNORECASE).strip()
        return s

    @classmethod
    def normalize_name(cls, name: str) -> str:
        return re.sub(r"[^a-z0-9_]+", "_", name.lower().strip()).strip("_")

    @classmethod
    def infer_type(cls, name: str, fallback: EntityType) -> Tuple[str, EntityType]:
        key = name.lower().strip()
        if key in cls.KNOWN_ENTITY_MAP:
            return cls.KNOWN_ENTITY_MAP[key]
        return name, fallback

    @classmethod
    def extract(cls, text: str) -> List[ExtractedTriplet]:
        triplets: List[ExtractedTriplet] = []
        if not text:
            return triplets

        # Split into sentences
        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            for pattern, pred, src_type, tgt_type, conf in cls.PATTERNS:
                matches = pattern.finditer(sentence)
                for m in matches:
                    groups = m.groups()
                    if len(groups) >= 3:
                        src_raw = cls.clean_entity_name(groups[0])
                        target_raw = cls.clean_entity_name(groups[2])

                        if not src_raw or not target_raw:
                            continue
                        if len(src_raw) > 50 or len(target_raw) > 50:
                            continue

                        src_display, s_type = cls.infer_type(src_raw, src_type)
                        tgt_display, t_type = cls.infer_type(target_raw, tgt_type)

                        # Avoid trivial self loops
                        if src_display.lower() == tgt_display.lower():
                            continue

                        triplet = ExtractedTriplet(
                            source=src_display,
                            predicate=pred,
                            target=tgt_display,
                            confidence=conf,
                            source_type=s_type,
                            target_type=t_type,
                            evidence=sentence,
                        )
                        triplets.append(triplet)

        return triplets
