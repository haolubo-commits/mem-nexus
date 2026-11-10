"""
Ebbinghaus Temporal Memory Decay and Reinforcement Service for MemNexus.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.config import settings


class DecayEngine:
    """
    Computes time-decayed memory retention curves based on the Ebbinghaus forgetting formulation
    with reinforcement boosts on repeated associative recall:
      R(t) = I_0 * exp(-lambda * delta_t_hours) + beta * ln(1 + access_count)
    """

    @classmethod
    def compute_decay(
        cls,
        base_importance: float,
        last_accessed_at: datetime,
        access_count: int = 0,
        current_time: Optional[datetime] = None,
        decay_rate: Optional[float] = None,
        boost_factor: Optional[float] = None,
    ) -> float:
        rate = decay_rate if decay_rate is not None else settings.DEFAULT_DECAY_RATE
        beta = boost_factor if boost_factor is not None else settings.REINFORCEMENT_BOOST_FACTOR
        now = current_time or datetime.now(timezone.utc)

        # Ensure timezone-aware
        if last_accessed_at.tzinfo is None:
            last_accessed_at = last_accessed_at.replace(tzinfo=timezone.utc)

        delta_seconds = max(0.0, (now - last_accessed_at).total_seconds())
        delta_hours = delta_seconds / 3600.0

        # Base exponential decay
        decay_factor = math.exp(-rate * (delta_hours / 24.0))  # normalize delta to days
        base_decayed = base_importance * decay_factor

        # Access reinforcement reward
        reinforcement = beta * math.log(1.0 + max(0, access_count))

        final_score = min(1.0, max(0.01, base_decayed + reinforcement))
        return round(final_score, 4)

    @classmethod
    def apply_to_entity(
        cls,
        entity_doc: Dict[str, Any],
        current_time: Optional[datetime] = None,
        decay_rate: Optional[float] = None,
    ) -> float:
        base_imp = float(entity_doc.get("importance_score", 0.7))
        last_acc = entity_doc.get("last_accessed_at")
        if isinstance(last_acc, str):
            try:
                last_acc = datetime.fromisoformat(last_acc)
            except Exception:
                last_acc = datetime.now(timezone.utc)
        elif not isinstance(last_acc, datetime):
            last_acc = datetime.now(timezone.utc)

        count = int(entity_doc.get("access_count", 0))
        decayed = cls.compute_decay(
            base_importance=base_imp,
            last_accessed_at=last_acc,
            access_count=count,
            current_time=current_time,
            decay_rate=decay_rate,
        )
        return decayed

