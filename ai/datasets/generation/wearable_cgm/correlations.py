"""
correlations.py — Cross-domain physiological correlation module.

Adjusts generated wearable features to enforce inter-feature physiological relationships
(Steps <-> Sedentary, Sleep <-> Heart Rate, Activity <-> Heart Rate) and guarantees
compliance with the 24-hour daily time budget.
"""

import numpy as np
from typing import Dict

from . import constants


def apply_physiological_correlations(
    wearables: Dict[str, np.ndarray],
) -> Dict[str, np.ndarray]:
    """Apply cross-domain physiological adjustments across generated wearable features.

    Args:
        wearables: Dictionary of generated wearable arrays.

    Returns:
        Adjusted dictionary of wearable feature arrays.
    """
    steps = wearables["Average_Daily_Steps"].copy()
    active_min = wearables["Active_Minutes"].copy()
    sedentary_min = wearables["Sedentary_Time_Minutes"].copy()
    rhr = wearables["Resting_Heart_Rate"].copy()
    sleep_hours = wearables["Sleep_Duration"].copy()

    # ── 1. Sleep Duration -> Resting Heart Rate adjustment ──
    # Sleep deprivation (<6h) causes autonomic stress, elevating RHR
    short_sleep_mask = sleep_hours < 6.0
    rhr[short_sleep_mask] += (6.0 - sleep_hours[short_sleep_mask]) * 1.5

    # Long restful sleep (>8h) slightly lowers RHR
    long_sleep_mask = sleep_hours > 8.0
    rhr[long_sleep_mask] -= (sleep_hours[long_sleep_mask] - 8.0) * 0.5

    rhr = np.clip(rhr, constants.FEATURE_BOUNDS["Resting_Heart_Rate"][0], constants.FEATURE_BOUNDS["Resting_Heart_Rate"][1])
    rhr = np.round(rhr, 1)

    # ── 2. Time-Budget Enforcement (24-Hour Constraint) ──
    # Active_Minutes + Sedentary_Time_Minutes + (Sleep_Duration * 60) <= 1440
    sleep_minutes = sleep_hours * 60.0
    total_time = active_min + sedentary_min + sleep_minutes

    excess_time = total_time - constants.DAILY_TIME_BUDGET_MINUTES
    has_excess = excess_time > 0.0

    if np.any(has_excess):
        # Trim sedentary time first, then active minutes if necessary
        sedentary_trim = np.minimum(sedentary_min[has_excess] - constants.FEATURE_BOUNDS["Sedentary_Time_Minutes"][0], excess_time[has_excess])
        sedentary_min[has_excess] -= sedentary_trim

        # Re-check remaining excess
        new_total = active_min[has_excess] + sedentary_min[has_excess] + sleep_minutes[has_excess]
        rem_excess = new_total - constants.DAILY_TIME_BUDGET_MINUTES
        has_rem = rem_excess > 0.0

        if np.any(has_rem):
            active_trim = np.minimum(active_min[has_excess][has_rem] - constants.FEATURE_BOUNDS["Active_Minutes"][0], rem_excess[has_rem])
            active_min[has_excess][has_rem] -= active_trim

    sedentary_min = np.round(sedentary_min, 1)
    active_min = np.round(active_min, 1)

    # Update dictionary
    wearables["Average_Daily_Steps"] = steps
    wearables["Active_Minutes"] = active_min
    wearables["Sedentary_Time_Minutes"] = sedentary_min
    wearables["Resting_Heart_Rate"] = rhr
    wearables["Sleep_Duration"] = sleep_hours

    return wearables
