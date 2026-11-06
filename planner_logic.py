"""Calculation logic for the Daily Time Planner.

EDIT THE SETTINGS BELOW to change the planner's rules.
This file has no Streamlit code, so the calculations can be tested separately.
"""

# ======================== EASY-TO-EDIT SETTINGS ========================
DAY_HOURS = 24.0
FEEL_SCORE_MAX = 10.0
TIME_SCORE_START = 10.0       # 1 hour lost reduces the time score by 1 point

STUDY_BASE_HOURS = 8.0
BUSINESS_BASE_HOURS = 8.0
SLEEP_BASE_HOURS = 6.0
ADJUSTMENT_BASE_HOURS = 2.0
MIN_ADJUSTMENT_HOURS = 1.0
FALLBACK_EXTRA_HOURS = 1.0   # Reserved extra time when combined score <= 0

# When the combined score is zero or negative, split the remaining work time
# using these weights. Keep them equal for a 50/50 split.
FALLBACK_STUDY_WEIGHT = 1.0
FALLBACK_BUSINESS_WEIGHT = 1.0
# =======================================================================


def calculate_plan(
    hours_lost: float,
    feel_score: float,
    sleep_fixed: bool = True,
    custom_sleep_hours: float = SLEEP_BASE_HOURS,
    adjustment_fixed: bool = False,
) -> dict:
    """Return a complete daily allocation, or an infeasibility message."""
    if not 0 <= hours_lost <= DAY_HOURS:
        raise ValueError(f"Hours lost must be between 0 and {DAY_HOURS}.")
    if not 0 <= feel_score <= FEEL_SCORE_MAX:
        raise ValueError(f"Feel score must be between 0 and {FEEL_SCORE_MAX}.")

    sleep = SLEEP_BASE_HOURS if sleep_fixed else custom_sleep_hours
    if not 0 <= sleep <= DAY_HOURS:
        raise ValueError(f"Sleep must be between 0 and {DAY_HOURS} hours.")

    time_score = TIME_SCORE_START - hours_lost
    combined_score = (feel_score + time_score) / (2 * FEEL_SCORE_MAX)
    available = DAY_HOURS - hours_lost - sleep

    if adjustment_fixed:
        adjustment = ADJUSTMENT_BASE_HOURS
    else:
        adjustment = max(
            MIN_ADJUSTMENT_HOURS,
            ADJUSTMENT_BASE_HOURS * max(combined_score, 0.0),
        )

    if available < adjustment:
        return {
            "feasible": False,
            "message": "Not enough time remains for the selected sleep and adjustment time.",
            "hours_lost": hours_lost,
            "sleep": sleep,
            "available_before_adjustment": max(0.0, available),
            "adjustment_required": adjustment,
            "time_score": time_score,
            "combined_score": combined_score,
        }

    room_after_adjustment = available - adjustment

    if combined_score <= 0:
        # Zero/negative-score fallback: reserve extra time, then split the rest.
        extra = min(FALLBACK_EXTRA_HOURS, room_after_adjustment)
        work_time = room_after_adjustment - extra
        total_weight = FALLBACK_STUDY_WEIGHT + FALLBACK_BUSINESS_WEIGHT
        if total_weight <= 0:
            raise ValueError("Fallback study and business weights must add up to more than zero.")
        study = work_time * FALLBACK_STUDY_WEIGHT / total_weight
        business = work_time * FALLBACK_BUSINESS_WEIGHT / total_weight
        method = "Fallback allocation"
    else:
        # Positive-score rule: scale the original 8h / 8h targets by the score.
        study_target = STUDY_BASE_HOURS * combined_score
        business_target = BUSINESS_BASE_HOURS * combined_score
        target_total = study_target + business_target

        # Never allocate more time than is actually available.
        scale = min(1.0, room_after_adjustment / target_total) if target_total else 0.0
        study = study_target * scale
        business = business_target * scale
        extra = room_after_adjustment - study - business
        method = "Score-based allocation"

    allocations = {
        "Studies": study,
        "Business exploration": business,
        "Adjustment / life management": adjustment,
        "Sleep": sleep,
        "Unexpected event / lost time": hours_lost,
        "Extra time": extra,
    }
    total = sum(allocations.values())

    return {
        "feasible": True,
        "method": method,
        "allocations": allocations,
        "time_score": time_score,
        "combined_score": combined_score,
        "total_hours": total,
        "extra_time": extra,
    }
