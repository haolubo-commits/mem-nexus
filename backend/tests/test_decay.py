"""
Unit tests for Ebbinghaus Memory Decay Engine.
"""

from datetime import datetime, timezone, timedelta
import pytest
from app.services.decay import DecayEngine


def test_compute_decay_immediate():
    now = datetime.now(timezone.utc)
    score = DecayEngine.compute_decay(base_importance=0.8, last_accessed_at=now, access_count=0)
    assert 0.79 <= score <= 0.81


def test_compute_decay_over_time():
    now = datetime.now(timezone.utc)
    past_1d = now - timedelta(days=1)
    past_7d = now - timedelta(days=7)

    score_fresh = DecayEngine.compute_decay(0.8, now, access_count=0, current_time=now)
    score_1d = DecayEngine.compute_decay(0.8, past_1d, access_count=0, current_time=now)
    score_7d = DecayEngine.compute_decay(0.8, past_7d, access_count=0, current_time=now)

    assert score_fresh > score_1d > score_7d
    assert score_7d > 0.01


def test_access_reinforcement_boost():
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=3)

    score_zero_access = DecayEngine.compute_decay(0.7, past, access_count=0, current_time=now)
    score_five_access = DecayEngine.compute_decay(0.7, past, access_count=5, current_time=now)
    score_twenty_access = DecayEngine.compute_decay(0.7, past, access_count=20, current_time=now)

    assert score_twenty_access > score_five_access > score_zero_access


def test_score_clamping():
    now = datetime.now(timezone.utc)
    # Exceedingly high reinforcement should clamp at 1.0
    over_boosted = DecayEngine.compute_decay(1.0, now, access_count=500, current_time=now)
    assert over_boosted == 1.0

    # Very old memory should clamp at lower bound 0.01
    very_old = now - timedelta(days=365)
    decayed_floor = DecayEngine.compute_decay(0.05, very_old, access_count=0, current_time=now)
    assert decayed_floor >= 0.01


def test_apply_to_entity_dict():
    now = datetime.now(timezone.utc)
    entity_doc = {
        "importance_score": 0.9,
        "access_count": 2,
        "last_accessed_at": (now - timedelta(hours=12)).isoformat(),
    }
    score = DecayEngine.apply_to_entity(entity_doc, current_time=now)
    assert 0.8 <= score <= 1.0

