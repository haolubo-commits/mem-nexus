"""
Unit tests for Triplet & Entity Extractor.
"""

import pytest
from app.services.extractor import TripletExtractor
from app.models.entity import EntityType


def test_extract_user_preference():
    text = "User prefers Python over JavaScript."
    triplets = TripletExtractor.extract(text)
    assert len(triplets) == 1
    t = triplets[0]
    assert t.source == "User"
    assert t.predicate == "prefers"
    assert t.target == "Python"
    assert t.source_type == EntityType.PERSON
    assert t.confidence >= 0.90


def test_extract_dependency():
    text = "The application relies on FastAPI for API services."
    triplets = TripletExtractor.extract(text)
    assert len(triplets) == 1
    t = triplets[0]
    assert t.predicate == "depends_on"
    assert t.target == "FastAPI"
    assert t.target_type == EntityType.TOOL


def test_extract_author():
    text = "Dr. Aris created the distributed consensus engine."
    triplets = TripletExtractor.extract(text)
    assert len(triplets) == 1
    t = triplets[0]
    assert t.source == "Dr. Aris"
    assert t.predicate == "authored"


def test_extract_affiliation():
    text = "Alice works at OpenAI."
    triplets = TripletExtractor.extract(text)
    assert len(triplets) == 1
    t = triplets[0]
    assert t.source == "Alice"
    assert t.predicate == "works_at"
    assert t.target == "OpenAI"
    assert t.target_type == EntityType.ORGANIZATION


def test_extract_location():
    text = "Production database is located in us-east-1."
    triplets = TripletExtractor.extract(text)
    assert len(triplets) == 1
    t = triplets[0]
    assert t.predicate == "located_in"
    assert t.target == "us-east-1"
    assert t.target_type == EntityType.LOCATION


def test_clean_and_normalize_name():
    raw = "  `PostgreSQL`., "
    cleaned = TripletExtractor.clean_entity_name(raw)
    assert cleaned == "PostgreSQL"
    normalized = TripletExtractor.normalize_name("PostgreSQL 16")
    assert normalized == "postgresql_16"


def test_suppress_self_loops():
    text = "Python relies on Python."
    triplets = TripletExtractor.extract(text)
    assert len(triplets) == 0

