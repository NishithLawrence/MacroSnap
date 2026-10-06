"""
MacroSnap Analytics Engine (analytics.py)
========================================
Pure deterministic Python module for processing historical meal records,
calculating period averages, adherence rates, nutrition consistency scores,
and neutral goal-aware progress metrics.

- Zero Gemini dependence for numerical calculations.
- Missing days are explicitly tagged as 'no data' (NOT 0 calories eaten).
- Evaluates historical days against historical target snapshots (target_storage.py).
"""

import datetime
from typing import Dict, Any, List, Optional
import meal_storage
import weight_storage
import target_storage


def get_daily_nutrition_history(
    days: int = 7,
    fallback_target_cal: int = 2000,
    fallback_target_p: int = 150,
    fallback_target_c: int = 200,
    fallback_target_f: int = 65,
) -> List[Dict[str, Any]]:
    """
    Retrieves daily nutrition records for the past `days` dates ending today.
    Resolves historical target snapshots applicable to each date.
    Identifies tracked days vs missing days. Missing days are NOT assigned 0 intake.
    """
    today = datetime.date.today()
    history = []

    for i in range(days - 1, -1, -1):
        date_obj = today - datetime.timedelta(days=i)
        date_str = date_obj.isoformat()

        day_meals = meal_storage.get_meals_for_date(date_str)
        day_totals = meal_storage.get_daily_totals(date_str)

        # Resolve historical target applicable to date_str
        target_snap = target_storage.get_target_for_date(date_str)
        if target_snap:
            t_cal = target_snap.get("calorie_target", fallback_target_cal)
            t_p = target_snap.get("protein_target", fallback_target_p)
            t_c = target_snap.get("carbs_target", fallback_target_c)
            t_f = target_snap.get("fat_target", fallback_target_f)
            t_goal = target_snap.get("goal", "Fat Loss")
        else:
            t_cal = fallback_target_cal
            t_p = fallback_target_p
            t_c = fallback_target_c
            t_f = fallback_target_f
            t_goal = "Fat Loss"

        is_tracked = len(day_meals) > 0

        history.append({
            "date": date_str,
            "day_name": date_obj.strftime("%a"),
            "date_formatted": date_obj.strftime("%b %d"),
            "tracked": is_tracked,
            "calories": day_totals["calories"] if is_tracked else 0,
            "protein_g": day_totals["protein_g"] if is_tracked else 0,
            "carbs_g": day_totals["carbs_g"] if is_tracked else 0,
            "fat_g": day_totals["fat_g"] if is_tracked else 0,
            "target_calories": t_cal,
            "target_protein": t_p,
            "target_carbs": t_c,
            "target_fat": t_f,
            "target_goal": t_goal,
            "meal_count": len(day_meals),
        })

    return history


def calculate_period_averages(history_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates average daily calories and macros ONLY over tracked days.
    """
    if not history_records:
        return {
            "total_days": 0,
            "tracked_days": 0,
            "avg_calories": 0,
            "avg_protein": 0,
            "avg_carbs": 0,
            "avg_fat": 0,
            "total_meals": 0,
        }

    tracked_records = [r for r in history_records if r.get("tracked", False)]
    tracked_count = len(tracked_records)
    total_count = len(history_records)

    if tracked_count == 0:
        return {
            "total_days": total_count,
            "tracked_days": 0,
            "avg_calories": 0,
            "avg_protein": 0,
            "avg_carbs": 0,
            "avg_fat": 0,
            "total_meals": 0,
        }

    tot_cals = sum(r["calories"] for r in tracked_records)
    tot_p = sum(r["protein_g"] for r in tracked_records)
    tot_c = sum(r["carbs_g"] for r in tracked_records)
    tot_f = sum(r["fat_g"] for r in tracked_records)
    tot_meals = sum(r["meal_count"] for r in tracked_records)

    return {
        "total_days": total_count,
        "tracked_days": tracked_count,
        "avg_calories": round(tot_cals / tracked_count),
        "avg_protein": round(tot_p / tracked_count),
        "avg_carbs": round(tot_c / tracked_count),
        "avg_fat": round(tot_f / tracked_count),
        "total_meals": tot_meals,
    }


def calculate_calorie_adherence(history_records: List[Dict[str, Any]], default_target_calories: int) -> Dict[str, Any]:
    """
    Calculates calorie adherence over tracked days evaluating each day against its applicable date target.
    Target range: 90% - 110% of target.
    """
    tracked_records = [r for r in history_records if r.get("tracked", False)]
    tracked_count = len(tracked_records)

    if tracked_count == 0:
        return {
            "on_target_count": 0,
            "below_count": 0,
            "above_count": 0,
            "tracked_days": 0,
            "ratio_str": "0 / 0 days",
            "adherence_pct": 0,
        }

    on_target = 0
    below = 0
    above = 0

    for r in tracked_records:
        t_cal = r.get("target_calories", default_target_calories)
        cals = r["calories"]
        low_bound = round(0.90 * t_cal)
        high_bound = round(1.10 * t_cal)

        if low_bound <= cals <= high_bound:
            on_target += 1
            r["adherence_category"] = "On target"
        elif cals < low_bound:
            below += 1
            r["adherence_category"] = "Below target"
        else:
            above += 1
            r["adherence_category"] = "Above target"

    pct = round((on_target / tracked_count) * 100)
    return {
        "on_target_count": on_target,
        "below_count": below,
        "above_count": above,
        "tracked_days": tracked_count,
        "ratio_str": f"{on_target} / {tracked_count} days on target",
        "adherence_pct": pct,
    }


def calculate_protein_adherence(history_records: List[Dict[str, Any]], default_target_protein: int) -> Dict[str, Any]:
    """
    Calculates protein target adherence over tracked days evaluating each day against its applicable protein target.
    """
    tracked_records = [r for r in history_records if r.get("tracked", False)]
    tracked_count = len(tracked_records)

    if tracked_count == 0:
        return {
            "reached_count": 0,
            "tracked_days": 0,
            "ratio_str": "0 / 0 days",
            "adherence_pct": 0,
        }

    reached = 0
    for r in tracked_records:
        t_p = r.get("target_protein", default_target_protein)
        threshold = round(0.90 * t_p)
        if r["protein_g"] >= threshold:
            reached += 1

    pct = round((reached / tracked_count) * 100)
    return {
        "reached_count": reached,
        "tracked_days": tracked_count,
        "ratio_str": f"{reached} / {tracked_count} days target reached",
        "adherence_pct": pct,
    }


def calculate_consistency(history_records: List[Dict[str, Any]], default_target_calories: int, default_target_protein: int) -> int:
    """
    Calculates a deterministic 'Nutrition Consistency' percentage score (0-100%)
    evaluating each day against its applicable date target.
    """
    tracked_records = [r for r in history_records if r.get("tracked", False)]
    if not tracked_records:
        return 0

    day_scores = []

    for r in tracked_records:
        t_cal = r.get("target_calories", default_target_calories)
        t_p = r.get("target_protein", default_target_protein)
        if t_cal <= 0 or t_p <= 0:
            continue

        cals = r["calories"]
        p_g = r["protein_g"]

        # Calorie Score
        if 0.90 * t_cal <= cals <= 1.10 * t_cal:
            cal_score = 100.0
        else:
            diff_pct = abs(cals - t_cal) / float(t_cal)
            cal_score = max(0.0, 100.0 - (diff_pct * 100.0))

        # Protein Score
        p_threshold = 0.90 * t_p
        if p_g >= p_threshold:
            p_score = 100.0
        else:
            p_score = max(0.0, (p_g / p_threshold) * 100.0)

        day_scores.append((cal_score + p_score) / 2.0)

    if not day_scores:
        return 0

    avg_score = sum(day_scores) / len(day_scores)
    return max(0, min(100, round(avg_score)))


def get_goal_interpretation(goal: str, avg_calories: int, target_calories: int, tdee: int) -> str:
    """
    Returns a neutral, descriptive interpretation based on user goal and intake.
    """
    if avg_calories <= 0:
        return "Log more meals to generate goal trend insights."

    diff = avg_calories - target_calories
    goal_norm = goal.strip().capitalize()

    if "Fat loss" in goal_norm or "Fat" in goal_norm:
        if avg_calories < tdee:
            return "Your average calorie intake is below your maintenance level, supporting your fat loss target."
        else:
            return "Your average calorie intake is currently around or above maintenance."
    elif "Lean bulk" in goal_norm or "Bulk" in goal_norm:
        if avg_calories > tdee:
            return "Your average calorie intake is above your maintenance level, supporting your lean bulk target."
        else:
            return "Your average calorie intake is currently at or below maintenance."
    elif "Recomposition" in goal_norm or "Recomp" in goal_norm:
        return "Your average intake is being compared with your active body recomposition target."
    else:  # Maintenance
        if abs(diff) <= 150:
            return "Your average calorie intake is close to your current maintenance target."
        elif diff > 150:
            return "Your average calorie intake is slightly above your maintenance target."
        else:
            return "Your average calorie intake is slightly below your maintenance target."


def get_period_summary(
    days: int,
    target_calories: int,
    target_protein: int,
    target_carbs: int,
    target_fat: int,
    goal: str = "Fat Loss",
    tdee: int = 2400,
) -> Dict[str, Any]:
    """
    High-level analytics engine function that aggregates history, averages, adherence,
    consistency score, and weight trends using historical target resolution.
    """
    history = get_daily_nutrition_history(
        days=days,
        fallback_target_cal=target_calories,
        fallback_target_p=target_protein,
        fallback_target_c=target_carbs,
        fallback_target_f=target_fat,
    )

    averages = calculate_period_averages(history)
    cal_adherence = calculate_calorie_adherence(history, target_calories)
    p_adherence = calculate_protein_adherence(history, target_protein)
    consistency = calculate_consistency(history, target_calories, target_protein)
    weight_change = weight_storage.get_weight_change()
    interpretation = get_goal_interpretation(goal, averages["avg_calories"], target_calories, tdee)

    return {
        "days_period": days,
        "history": history,
        "averages": averages,
        "cal_adherence": cal_adherence,
        "p_adherence": p_adherence,
        "consistency_pct": consistency,
        "weight_change": weight_change,
        "interpretation": interpretation,
    }
