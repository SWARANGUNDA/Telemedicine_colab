"""
adaptive_strategy.py — Adaptive Prediction Protocol Module (Module 13).

Determines which expert models are active for prediction.
The Fusion Engine dynamically combines predictions from available experts:
- Clinical + Wearable + Gut (Full Tri-Modal)
- Clinical + Wearable
- Clinical + Gut
- Wearable + Gut
- Single Modality Fallback (Clinical-only, Wearable-only, Gut-only)

Ensures the system never fails because one modality is unavailable.
"""

from typing import Dict, List
from .availability import ExpertStatus


class AdaptivePredictionStrategy:
    """Strategy dictating which expert models will be executed."""

    def __init__(self, availability_map: Dict[str, ExpertStatus]):
        self.availability_map = availability_map
        self.active_experts: List[str] = [
            expert for expert, status in availability_map.items()
            if status in [ExpertStatus.READY, ExpertStatus.PARTIAL]
        ]
        self.skipped_experts: List[str] = [
            expert for expert, status in availability_map.items()
            if status == ExpertStatus.UNAVAILABLE
        ]

    def get_strategy_name(self) -> str:
        if len(self.active_experts) == 3:
            return "Full Tri-Modal Fusion (Clinical + Wearable + Gut)"
        elif len(self.active_experts) == 2:
            return f"Bi-Modal Fusion ({' + '.join(self.active_experts)})"
        elif len(self.active_experts) == 1:
            return f"Single-Modality Fallback ({self.active_experts[0]})"
        else:
            return "Insufficient Data (No Expert Models Active)"

    def is_executable(self) -> bool:
        return len(self.active_experts) > 0

    def to_dict(self) -> Dict:
        return {
            "strategy_name": self.get_strategy_name(),
            "active_experts": self.active_experts,
            "skipped_experts": self.skipped_experts,
            "is_executable": self.is_executable()
        }
