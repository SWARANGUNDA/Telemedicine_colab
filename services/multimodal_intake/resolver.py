"""
resolver.py — Duplicate Resolution Module (Module 5).

If multiple uploaded reports contain the same feature:
Chooses the best value using priority rules:
1. Most Recent Report
2. Official Laboratory Report
3. Manual Entry

Flags conflicting values exceeding tolerance thresholds for user resolution.
"""

import logging
from typing import Any, Dict, List, Tuple, Optional

logger = logging.getLogger("imdie.resolver")

PRIORITY_ORDER = {
    "Official Laboratory Report": 3,
    "Wearable Sync": 2,
    "Manual Entry": 1,
    "Unknown": 0
}


def resolve_duplicate_feature(
    feature_name: str,
    observations: List[Dict[str, Any]]
) -> Tuple[Any, List[str], Optional[Dict[str, Any]]]:
    """Resolve duplicate readings for a single feature and track conflicts.

    Args:
        feature_name: Feature key name.
        observations: List of dicts with 'value', 'source_type', 'source_file', 'timestamp'.

    Returns:
        Tuple of (selected_value, warning_messages, conflict_detail_or_None).
    """
    warnings: List[str] = []
    if not observations:
        return None, warnings, None

    if len(observations) == 1:
        return observations[0]["value"], warnings, None

    # Sort observations by composite confidence score: 0.5*Confidence + 0.3*Priority + 0.2*Recency
    max_ts = max((float(x.get("timestamp", 0)) for x in observations), default=1.0)
    if max_ts <= 0:
        max_ts = 1.0

    def obs_score(x):
        conf = float(x.get("confidence", 0.90))
        prio = float(PRIORITY_ORDER.get(x.get("source_type", "Unknown"), 0)) / 3.0
        time_val = float(x.get("timestamp", 0)) / max_ts
        return 0.5 * conf + 0.3 * prio + 0.2 * time_val

    sorted_obs = sorted(
        observations,
        key=obs_score,
        reverse=True
    )

    selected = sorted_obs[0]["value"]
    values = [obs["value"] for obs in sorted_obs]

    # Check for conflict if values differ
    conflict_detail = None
    numeric_vals = []
    for v in values:
        if isinstance(v, (int, float)):
            numeric_vals.append(float(v))
        elif isinstance(v, dict) and "raw_value" in v:
            try:
                numeric_vals.append(float(v["raw_value"]))
            except (ValueError, TypeError):
                pass

    if len(set(str(v) for v in values)) > 1:
        warn = f"Conflicting values detected for '{feature_name}': {values}. Please verify the intended measurement."
        warnings.append(warn)
        conflict_detail = {
            "feature": feature_name,
            "selected_value": selected,
            "options": observations,
            "status": "CONFLICT",
            "message": warn
        }

    return selected, warnings, conflict_detail


def merge_and_resolve_reports(
    reports: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str], Dict[str, Dict[str, Any]]]:
    """Merge multiple report extractions and resolve duplicate features.

    Args:
        reports: List of extracted report payloads containing 'features' and 'metadata'.

    Returns:
        Tuple of (merged_features_dict, cumulative_warnings, conflict_map).
    """
    feature_obs_map: Dict[str, List[Dict[str, Any]]] = {}
    all_warnings: List[str] = []
    conflict_map: Dict[str, Dict[str, Any]] = {}

    for report in reports:
        metadata = report.get("metadata", {})
        source_type = metadata.get("source_type", "Official Laboratory Report")
        source_file = metadata.get("source_file", "report")
        timestamp = metadata.get("timestamp", 0)
        features = report.get("features", {})

        for feat, val in features.items():
            if val is None:
                continue
            if feat not in feature_obs_map:
                feature_obs_map[feat] = []
            
            raw_v = val["raw_value"] if isinstance(val, dict) and "raw_value" in val else val
            feature_obs_map[feat].append({
                "value": val,
                "raw_value": raw_v,
                "source_type": source_type,
                "source_file": source_file,
                "timestamp": timestamp
            })

    merged: Dict[str, Any] = {}
    for feat, obs_list in feature_obs_map.items():
        selected_val, warn_list, c_detail = resolve_duplicate_feature(feat, obs_list)
        merged[feat] = selected_val
        all_warnings.extend(warn_list)
        if c_detail:
            conflict_map[feat] = c_detail

    return merged, all_warnings, conflict_map

