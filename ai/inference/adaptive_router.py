"""
adaptive_router.py — Adaptive Missing-Modality Pathway Router.

Routes incoming patient data to the correct pre-trained fusion pathway
based on which modalities are available. Each pathway has its own
dedicated meta-learner, calibrator, and thresholds.

Does NOT zero-pad, fabricate, or invent missing modality data.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

try:
    from ai.config import fusion_config as config
except (ImportError, ValueError):
    from ..config import fusion_config as config

logger = logging.getLogger("fusion_engine.adaptive_router")


def detect_available_modalities(
    expert_outputs: Dict[str, Optional[Dict[str, Any]]],
) -> Tuple[str, Tuple[str, ...]]:
    """Detect which modalities are available and select the correct pathway.

    Args:
        expert_outputs: Dict mapping modality key -> expert prediction dict
            (or None if modality is unavailable).

    Returns:
        Tuple of (pathway_key, active_modality_keys).

    Raises:
        ValueError: If no modalities are available.
    """
    active = []
    for mod_key in config.MODALITY_KEYS:
        output = expert_outputs.get(mod_key)
        if output is not None and len(output) > 0:
            active.append(mod_key)

    if not active:
        raise ValueError(
            "No modalities available. At least one expert output "
            "(Clinical, Wearable, or Gut) is required for fusion prediction."
        )

    active_tuple = tuple(active)

    # Find matching pathway key
    for pathway_key, pathway_mods in config.PATHWAY_DEFINITIONS.items():
        if pathway_mods == active_tuple:
            logger.info("Routed to pathway: %s (modalities: %s)", pathway_key, active_tuple)
            return pathway_key, active_tuple

    raise ValueError(
        f"No valid pathway found for modality combination: {active_tuple}"
    )


def assemble_fusion_input(
    expert_outputs: Dict[str, Dict[str, Any]],
    active_modalities: Tuple[str, ...],
) -> np.ndarray:
    """Assemble the fusion probability feature vector from available expert outputs.

    Args:
        expert_outputs: Dict mapping modality_key -> expert prediction dict
            (containing disease -> {probability, prediction, threshold}).
        active_modalities: Tuple of active modality keys in order.

    Returns:
        1D numpy array of concatenated probabilities.
    """
    prob_vector = []

    for mod_key in active_modalities:
        output = expert_outputs[mod_key]
        for disease in config.TARGET_DISEASES:
            prob = output[disease]["probability"]
            prob_vector.append(float(prob))

    return np.array(prob_vector).reshape(1, -1)
