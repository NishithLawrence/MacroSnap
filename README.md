# 📸 MACROSNAP

> **Snap your meal. Track your macros. Reach your goal.**

MacroSnap is a mobile-first AI nutrition and calorie tracking application designed to deliver deterministic, science-backed calorie and macro targets alongside Gemini Vision AI meal scanning, Contextual AI Nutrition Assistant (**MacroSnap Coach**), Analytics & Progress tracking, and Smart Profile recalculation with Target Snapshots.

---

## 🌟 Architecture & Data Flow

MacroSnap enforces a strict distinction between **Deterministic Science** and **Advisory AI**:

```
PROFILE & WEIGHT (profile_storage.py / weight_storage.py)
       │
       ▼
calculations.py (Mifflin-St Jeor Equation, TDEE, Goal Adjustments, Macro Allocation)
       │
       ▼
TARGET SNAPSHOTS (target_storage.py -> data/target_history.json)
       │
       ▼
OFFICIAL TARGETS (Calories, Protein, Carbs, Fat)
       │
       ▼
vision.py (Gemini Vision Meal Scanner) ──► USER REVIEW & EDIT
                                                       │
                                                       ▼
                                           meal_storage.py (data/meals.json)
                                                       │
                                                       ▼
                                           PYTHON DAILY TOTALS (Consumed & Remaining)
                                                       │
                                                       ├──► analytics.py (Progress & Historical Target Resolution)
                                                       │
                                                       ▼
                                           nutrition_ai.py (MacroSnap Coach)
```

- **Deterministic Python Engine**: Calculates official BMR, TDEE, Calorie targets, Macro targets, Meal sums, Consumed totals, and Remaining budgets.
- **Gemini AI Vision & Coach**: Provides food item estimates and contextual nutrition recommendations. The AI is **100% Read-Only** and can never alter tracker data or official calculations.
- **Historical Target Snapshots**: Target changes create immutable snapshots (`data/target_history.json`). Past meal logs are evaluated against the target in effect on that exact day.

---

## 📱 Application Flow & Features

1. **Mobile-First Onboarding Flow**:
   - Age, Sex, Height (cm), Current Weight (kg).
   - Activity Level (Sedentary, Lightly Active, Moderately Active, Very Active, Extremely Active).
   - Fitness Goal (Fat Loss, Body Recomposition, Lean Bulk, Maintenance).
   - Goal Intensity & Plan Confirmation Card.

2. **Main Mobile Navigation Tabs**:
   - 🏠 **Home**: Real-time Calorie budget bar, Macronutrient cards, Today's Logged Meals list with expandable details, Edit (✏️) and Delete (🗑️) controls.
   - 📸 **Snap Meal**: Camera/Upload scanner powered by Gemini Vision (`gemini-3.8-flash`), portion estimator, interactive food editor, meal type selector, and manual logging fallback.
   - 🧠 **MacroSnap Coach**: Contextual AI nutrition chat providing personalized meal recommendations, high-protein advice, and remaining calorie guidance based on live Python context.
   - 📅 **History**: Historical date picker and daily log summaries with full CRUD operations.
   - 📊 **Progress**: 7d/30d analytics dashboard, adherence rates, consistency scoring, goal interpretations, and weight history tracking.
   - 👤 **Profile**: Editable profile parameters, dynamic plan recalculation modal ("Your updated plan"), target snapshot history, and latest weight sync controls.

---

## 🧮 Science & Formulas

### 1. Basal Metabolic Rate (Mifflin-St Jeor)
- **Male**: $\text{BMR} = 10 \times \text{weight}_{\text{kg}} + 6.25 \times \text{height}_{\text{cm}} - 5 \times \text{age} + 5$
- **Female**: $\text{BMR} = 10 \times \text{weight}_{\text{kg}} + 6.25 \times \text{height}_{\text{cm}} - 5 \times \text{age} - 161$

### 2. Maintenance Calories & Goal Targets
- $\text{TDEE} = \text{BMR} \times \text{Activity Multiplier}$
- **Fat Loss**: Target = $\text{TDEE} \times (1 - \text{Deficit})$ (10%, 15%, 20%)
- **Lean Bulk**: Target = $\text{TDEE} \times (1 + \text{Surplus})$ (5%, 10%)
- **Recomposition**: Target = $\text{TDEE} \times (1 - \text{Deficit})$ (5%, 0%)

### 3. Macro Allocations
- **Protein**: Fat Loss (1.8g/kg), Recomp (2.0g/kg), Lean Bulk (1.8g/kg), Maintenance (1.6g/kg).
- **Fat**: ~25% of target calories ($\text{Fat}_{\text{g}} = \text{Fat Cals} / 9$).
- **Carbohydrates**: Remaining calorie balance ($\text{Carbs}_{\text{g}} = (\text{Target} - P_{\text{cals}} - F_{\text{cals}}) / 4$).

---

## 🛠 Project Structure

```
MacroSnap/
│
├── app.py                      # Streamlit mobile application shell & UI navigation
├── calculations.py             # Deterministic BMR, TDEE, and macro target engine
├── prompts.py                  # System prompts for Vision AI and safety disclaimers
├── vision.py                   # Gemini Vision API scanner & JSON validator
├── meal_storage.py             # Local JSON file persistence (data/meals.json)
├── weight_storage.py           # Body weight entry persistence (data/weight_history.json)
├── profile_storage.py          # User profile persistence (data/profile.json)
├── target_storage.py           # Target snapshot history engine (data/target_history.json)
├── analytics.py                # Deterministic progress analytics & target resolution engine
├── nutrition_ai.py             # Contextual AI Nutrition Assistant (MacroSnap Coach)
│
├── test_calculations.py        # BMR & Macro engine unit test suite
├── test_vision.py              # Vision scanner & JSON validation test suite
├── test_meal_storage.py        # Meal storage CRUD test suite
├── test_weight_storage.py      # Weight tracking storage test suite
├── test_profile_storage.py     # Profile persistence test suite
├── test_target_storage.py      # Target snapshot test suite
├── test_analytics.py          # Analytics engine test suite
├── test_nutrition_ai.py        # Nutrition AI test suite
├── test_integration.py         # End-to-end integration test suite
│
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
└── .streamlit/
    └── secrets.toml.example    # Secrets template for Gemini API key
```

---

## 🚀 How to Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Gemini API Key** (Optional for Vision & Coach):
   Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your-actual-api-key-here"
   ```

3. **Run All Test Suites**:
   ```bash
   python test_calculations.py
   python test_vision.py
   python test_meal_storage.py
   python test_nutrition_ai.py
   python test_analytics.py
   python test_weight_storage.py
   python test_profile_storage.py
   python test_target_storage.py
   python test_integration.py
   ```

4. **Launch Application**:
   ```bash
   streamlit run app.py
   ```

---

## 🛡 Security & Production Readiness

- **Zero Hardcoded Secrets**: All API keys are loaded securely from `.streamlit/secrets.toml`. `.gitignore` excludes `.streamlit/secrets.toml` and user data files (`data/*.json`).
- **Atomic File Storage**: All persistence modules write to temporary `.tmp` files before replacing target JSON files, guaranteeing data integrity.
- **Fail-Safe Error Handling**: Corrupted storage files or missing Gemini API keys degrade gracefully without crashing the Streamlit interface.
- **100% Read-Only AI Policy**: Gemini cannot alter tracker data, meal logs, user profiles, or target snapshots.
- **Medical Disclaimer**: AI advice is strictly non-medical and advisory.
