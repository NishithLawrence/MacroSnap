"""
MacroSnap Contextual Nutrition AI Assistant (nutrition_ai.py)
=============================================================
Isolated module for Gemini-powered contextual nutrition chat.

- Uses 'gemini-3.8-flash' (or fallback models if needed) via google-genai.
- Reuses secure API key loading from vision.py.
- Constructs real-time Python context (User Profile, Calorie/Macro Targets,
  Consumed Totals, Remaining Totals, Today's Confirmed Meals).
- Strict Read-Only Policy: AI cannot mutate user profile or tracker data.
- Does NOT replace Python as the source of truth for daily numbers.
"""

from typing import Dict, Any, List, Optional, Tuple
from vision import get_gemini_api_key

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]

SYSTEM_COACH_PROMPT = """You are MacroSnap Coach, an empathetic, scientific, and practical AI nutrition assistant.

CORE MANDATE & RULES:
1. You provide advisory context and personalized nutrition ideas based strictly on the user's current targets, consumed totals, and remaining budgets provided in the context.
2. MacroSnap (Python) is the single source of truth for all calorie and macro calculations. You must NEVER recalculate or state different official daily totals than those provided in the context.
3. You are READ-ONLY. You cannot add, edit, or delete meals from the user's tracker, nor change their goals or profile. If the user asks you to log a meal, politely explain that meals must be logged using the 📸 Snap scanner or manual meal logger.
4. Food nutrition estimates and recommendations are APPROXIMATE. Use language such as "approximately", "estimated", "based on your current targets", or "about".
5. Do NOT invent logged meals or consumed calories that are not listed in the context.
6. MEDICAL SAFETY: Do not diagnose medical conditions, prescribe therapeutic diets, or make dangerous extreme dieting recommendations. Remind users to consult a doctor or registered dietitian for medical needs.
7. Keep responses concise, practical, easy to read on mobile (use short bullet points), and beginner-friendly.
"""


def build_coach_context(user_plan: Dict[str, Any], consumed: Dict[str, int], today_meals: List[Dict[str, Any]]) -> str:
    """
    Constructs a comprehensive, real-time context string from Python state.
    Includes User Profile, Goal, Daily Targets, Consumed, Remaining, and Today's Confirmed Meals.
    """
    if not user_plan:
        user_plan = {}
    if not consumed:
        consumed = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    if not today_meals:
        today_meals = []

    target_cal = user_plan.get("target_calories", 2000)
    target_p = user_plan.get("protein_g", 150)
    target_c = user_plan.get("carbs_g", 200)
    target_f = user_plan.get("fat_g", 65)

    cons_cal = consumed.get("calories", 0)
    cons_p = consumed.get("protein_g", 0)
    cons_c = consumed.get("carbs_g", 0)
    cons_f = consumed.get("fat_g", 0)

    rem_cal = target_cal - cons_cal
    rem_p = target_p - cons_p
    rem_c = target_c - cons_c
    rem_f = target_f - cons_f

    # Format Meals string
    meals_formatted = []
    for idx, m in enumerate(today_meals):
        m_type = m.get("meal_type", "Meal")
        tot = m.get("total", {})
        foods_desc = ", ".join([f"{f.get('name')} ({f.get('portion', '')})" for f in m.get("foods", [])])
        meals_formatted.append(
            f"  - [{m_type}] {tot.get('calories', 0)} kcal (P: {tot.get('protein_g', 0)}g, C: {tot.get('carbs_g', 0)}g, F: {tot.get('fat_g', 0)}g) | Foods: {foods_desc}"
        )

    meals_text = "\n".join(meals_formatted) if meals_formatted else "  (No meals logged yet today)"

    context = f"""=== CURRENT USER NUTRITION CONTEXT (Calculated by Python) ===
USER PROFILE:
- Age: {user_plan.get('age', 25)} yrs
- Sex: {user_plan.get('sex', 'Male')}
- Height: {user_plan.get('height_cm', 178)} cm | Weight: {user_plan.get('weight_kg', 75)} kg
- Activity Level: {user_plan.get('activity_level', 'Moderately Active')}
- Fitness Goal: {user_plan.get('goal', 'Fat Loss')} ({user_plan.get('intensity', 'Moderate')})
- Calculated TDEE (Maintenance): {user_plan.get('tdee', 2400)} kcal

OFFICIAL DAILY TARGETS:
- Calories: {target_cal:,} kcal
- Protein: {target_p} g
- Carbohydrates: {target_c} g
- Fat: {target_f} g

TODAY'S CONSUMED TOTALS (Python Sum):
- Calories Consumed: {cons_cal:,} kcal
- Protein Consumed: {cons_p} g
- Carbohydrates Consumed: {cons_c} g
- Fat Consumed: {cons_f} g

TODAY'S REMAINING BUDGET:
- Calories Remaining: {rem_cal:,} kcal
- Protein Remaining: {rem_p} g
- Carbohydrates Remaining: {rem_c} g
- Fat Remaining: {rem_f} g

TODAY'S CONFIRMED LOGGED MEALS ({len(today_meals)} meals):
{meals_text}
============================================================="""
    return context


def query_nutrition_assistant(
    user_prompt: str,
    user_plan: Dict[str, Any],
    consumed: Dict[str, int],
    today_meals: List[Dict[str, Any]],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Tuple[bool, str]:
    """
    Sends user query and fresh real-time Python context to Gemini API.

    Returns:
        (success: bool, response_text: str)
    """
    if not user_prompt or not user_prompt.strip():
        return False, "Please enter a question or prompt for MacroSnap Coach."

    api_key = get_gemini_api_key()
    if not api_key:
        return (
            False,
            "Gemini API key is not configured on the backend.",
        )

    # Build fresh context from current Python state
    context_str = build_coach_context(user_plan, consumed, today_meals)

    # Format conversation history
    history_str = ""
    if chat_history:
        recent = chat_history[-6:]  # Keep recent 3 turns for context length efficiency
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "MacroSnap Coach"
            history_str += f"{role}: {msg.get('content')}\n"

    full_prompt = f"{SYSTEM_COACH_PROMPT}\n\n{context_str}\n\nRECENT CHAT HISTORY:\n{history_str}\nUser Question: {user_prompt.strip()}\n\nMacroSnap Coach:"

    # Call Gemini via google.genai SDK
    client = None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except Exception:
        pass

    if client:
        models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                if response and response.text:
                    return True, response.text.strip()
            except Exception:
                continue

        return False, "⚠️ MacroSnap Coach is temporarily unavailable. Please try again in a moment."

    # Legacy SDK fallback
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        for model_name in [PRIMARY_MODEL] + FALLBACK_MODELS:
            try:
                model = legacy_genai.GenerativeModel(model_name)
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return True, response.text.strip()
            except Exception:
                continue
    except Exception:
        pass

    return False, "⚠️ MacroSnap Coach is temporarily unavailable. Please try again in a moment."
