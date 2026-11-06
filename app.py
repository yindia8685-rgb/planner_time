"""Streamlit frontend for the Daily Time Planner.

EDIT THIS FILE to change page text, layout, labels, and input controls.
Put calculation-rule changes in planner_logic.py instead.
Run with: streamlit run app.py
"""

import streamlit as st

from planner_logic import (
    ADJUSTMENT_BASE_HOURS,
    DAY_HOURS,
    FEEL_SCORE_MAX,
    SLEEP_BASE_HOURS,
    calculate_plan,
)

# ======================== EASY-TO-EDIT PAGE TEXT ========================
PAGE_TITLE = "Daily Time Planner"
PAGE_SUBTITLE = "Adjust your study and business targets around an unusual day."
GO_BUTTON = "Go"
# =======================================================================


def format_duration(hours: float) -> str:
    """Show decimal hours as readable hours and minutes (e.g. 6.4 -> 6 hr 24 min)."""
    total_minutes = max(0, int(round(float(hours) * 60)))
    whole_hours, minutes = divmod(total_minutes, 60)
    return f"{whole_hours} hr {minutes} min"


st.set_page_config(page_title=PAGE_TITLE, page_icon="⏱️", layout="centered")
st.title(PAGE_TITLE)
st.caption(PAGE_SUBTITLE)

st.subheader("1. Today's unexpected time loss")
left, right = st.columns(2)
with left:
    lost_hours = st.number_input(
        "Hours lost (or expected)", min_value=0, max_value=int(DAY_HOURS),
        value=0, step=1,
    )
with right:
    max_minutes = 0 if lost_hours >= DAY_HOURS else 59
    lost_minutes = st.number_input(
        "Additional minutes", min_value=0, max_value=max_minutes,
        value=0, step=1,
    )
hours_lost = float(lost_hours) + float(lost_minutes) / 60.0

feel_score = st.slider(
    "How capable do you feel of working after the event?",
    min_value=0, max_value=int(FEEL_SCORE_MAX), value=5,
)

st.subheader("2. Fixed time settings")
sleep_fixed = st.checkbox(
    f"Keep sleep fixed at {format_duration(SLEEP_BASE_HOURS)}", value=True
)
if sleep_fixed:
    custom_sleep = SLEEP_BASE_HOURS
else:
    sleep_left, sleep_right = st.columns(2)
    with sleep_left:
        custom_sleep_hours = st.number_input(
            "Sleep hours", min_value=0, max_value=int(DAY_HOURS), value=int(SLEEP_BASE_HOURS), step=1
        )
    with sleep_right:
        sleep_max_minutes = 0 if custom_sleep_hours >= DAY_HOURS else 59
        custom_sleep_minutes = st.number_input(
            "Sleep minutes", min_value=0, max_value=sleep_max_minutes, value=0, step=1
        )
    custom_sleep = float(custom_sleep_hours) + float(custom_sleep_minutes) / 60.0

adjustment_fixed = st.checkbox(
    f"Keep adjustment / life-management time fixed at {format_duration(ADJUSTMENT_BASE_HOURS)}", value=False
)

st.divider()
if st.button(GO_BUTTON, type="primary", use_container_width=True):
    try:
        result = calculate_plan(
            hours_lost=hours_lost,
            feel_score=float(feel_score),
            sleep_fixed=sleep_fixed,
            custom_sleep_hours=float(custom_sleep),
            adjustment_fixed=adjustment_fixed,
        )
    except ValueError as error:
        st.error(str(error))
    else:
        st.subheader("Your daily allocation")
        st.write(f"**Time lost:** {format_duration(hours_lost)}")
        st.write(f"**Feel score:** {feel_score}/{FEEL_SCORE_MAX:g}")
        st.write(f"**Time score:** {result['time_score']:.2f}")
        st.write(f"**Combined score:** {result['combined_score']:.2f}")

        if not result["feasible"]:
            st.error(result["message"])
            st.write(
                f"Time left after sleep: {format_duration(result['available_before_adjustment'])}. "
                f"Adjustment time required: {format_duration(result['adjustment_required'])}."
            )
        else:
            st.caption(result["method"])
            rows = [
                {"Activity": activity, "Time": format_duration(hours)}
                for activity, hours in result["allocations"].items()
            ]
            st.table(rows)
            st.metric(
                "Total accounted for",
                f"{format_duration(result['total_hours'])} / {format_duration(DAY_HOURS)}",
            )
            st.metric("Extra time", format_duration(result["extra_time"]))
            if abs(result["total_hours"] - DAY_HOURS) > 0.01:
                st.warning("The allocation does not add up to a full day. Check the logic settings.")
