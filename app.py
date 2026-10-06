"""
MacroSnap — Mobile-First Dark Anime Fitness Calorie & Macro Tracker
===================================================================
Stage 11: Final Mobile Presentation, Centered Phone Frame & 6-Item Bottom Navigation

Main application entry point.
"""

import os
import time
import uuid
import datetime
import textwrap
import base64
from PIL import Image

import streamlit as st
from calculations import (
    calculate_full_plan,
    ACTIVITY_MULTIPLIERS,
    ACTIVITY_DESCRIPTIONS,
    GOAL_CONFIG,
)
from prompts import (
    PLAN_DISCLAIMER_TEXT,
    AI_DISCLAIMER_HEADER,
    AI_DISCLAIMER_TEXT,
)
from vision import analyze_meal_image, get_gemini_api_key
import meal_storage
import weight_storage
import analytics
import nutrition_ai
import profile_storage
import target_storage

# --- Page Configuration ---
st.set_page_config(
    page_title="MacroSnap | Fuel Your Discipline",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Asset Base64 Helper ---
def get_asset_base64(filename: str) -> str:
    path = os.path.join("assets", "anime", filename)
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""


# --- Custom Dark Anime Fitness Design System & Presentation CSS ---
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after {
    box-sizing: border-box !important;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #F8FAFC;
}

/* Hide Streamlit Chrome, Status Indicators & Floating Deployment Artifacts */
#MainMenu, 
footer, 
header, 
.stDeployButton, 
[data-testid="stHeader"], 
[data-testid="stDecoration"], 
[data-testid="stToolbar"], 
[data-testid="stStatusWidget"], 
[data-testid="stSidebarCollapseButton"], 
[data-testid="stActionButtonIcon"], 
[data-testid="stAppHeader"], 
[data-testid="stElementToolbar"],
[data-testid="stConnectionStatus"],
.stAppHeader, 
button[kind="header"], 
.stApp > header, 
div[data-testid="stHeader"], 
button[title="View fullscreen"], 
button[title*="Stop"],
button[title*="Rerun"],
div[class*="stStatusWidget"], 
div[class*="stDeployButton"], 
div[class*="stToolbar"],
div[class*="stDecoration"],
div[class*="stConnectionStatus"],
div[class*="stElementToolbar"] {
    visibility: hidden !important;
    display: none !important;
    height: 0 !important;
    width: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

.stApp {
    background-color: #07090D !important;
    position: relative !important;
}

.stAppViewContainer, .main {
    position: relative !important;
    z-index: 10 !important;
}

.main .block-container {
    width: 100% !important;
    max-width: 440px !important;
    margin: 0 auto !important;
    padding-top: 0.5rem !important;
    padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px)) !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    position: relative !important;
    z-index: 10 !important;
    box-sizing: border-box !important;
}

/* Ensure no element or card exceeds container width */
div, section, form, input, select, textarea, button, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], [data-testid="column"] {
    max-width: 100% !important;
    box-sizing: border-box !important;
    min-width: 0 !important;
    overflow-wrap: anywhere;
    word-break: break-word;
}

/* Streamlit Flex Layout & Column Overrides for Mobile */
[data-testid="stVerticalBlock"] {
    gap: 0.75rem !important;
}

[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 0.5rem !important;
    width: 100% !important;
}

[data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: 0 !important;
    flex: 1 1 0% !important;
    width: 100% !important;
}

/* Top Hero Header Bar */
.hero-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.3rem 0;
    height: 64px;
    margin-bottom: 0.35rem;
    width: 100%;
}

.logo-box {
    text-align: left;
}

.logo-title {
    font-size: 2.1rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    line-height: 1;
    text-transform: uppercase;
}

.logo-macro {
    color: #FFFFFF;
    text-shadow: 0 0 16px rgba(255, 255, 255, 0.35);
}

.logo-snap {
    color: #FF2B3A;
    margin-left: 3px;
    text-shadow: 0 0 22px rgba(255, 43, 58, 0.65);
}

.logo-tagline {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.3em;
    color: #94A3B8;
    margin-top: 4px;
    text-transform: uppercase;
}

.hero-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.icon-btn-glass {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    cursor: pointer;
}

/* Hero Greeting Box */
.greeting-box {
    margin: 0.2rem 0 1.25rem 0;
}

.greeting-time {
    font-size: 1rem;
    font-weight: 600;
    color: #94A3B8;
}

.greeting-name {
    font-size: 2.2rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin: 2px 0 4px 0;
    text-shadow: 0 4px 24px rgba(0, 0, 0, 0.85);
}

.greeting-quote {
    font-size: 0.82rem;
    font-style: italic;
    color: #FF2B3A;
    font-weight: 600;
    letter-spacing: 0.01em;
}

/* Glass Card Architecture */
.glass-card, .plan-card {
    background: rgba(10, 14, 22, 0.72) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 18px !important;
    padding: 1rem 1rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

.glass-card-hero, .plan-card-hero {
    background: linear-gradient(145deg, rgba(20, 24, 35, 0.76) 0%, rgba(10, 14, 22, 0.85) 100%) !important;
    border: 1px solid rgba(255, 43, 58, 0.35) !important;
    box-shadow: 0 12px 36px rgba(255, 43, 58, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

/* Calorie Ring Budget Card */
.card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.card-header-title {
    font-size: 0.8rem;
    color: #FF2B3A;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.card-header-date {
    font-size: 0.78rem;
    font-weight: 600;
    color: #94A3B8;
}

.calorie-card-body {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.85rem;
}

.ring-wrapper {
    position: relative;
    width: 130px;
    height: 130px;
    flex-shrink: 0;
}

.ring-center-content {
    position: absolute;
    top: 0;
    left: 0;
    width: 130px;
    height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}

.ring-cals {
    font-size: 1.45rem;
    font-weight: 900;
    color: #F8FAFC;
    line-height: 1;
}

.ring-target {
    font-size: 0.65rem;
    color: #94A3B8;
    font-weight: 600;
    margin-top: 2px;
}

.ring-pct {
    font-size: 0.78rem;
    color: #FF2B3A;
    font-weight: 800;
    margin-top: 2px;
}

.calorie-stats-list {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    flex: 1;
    min-width: 0;
}

.stat-item {
    display: flex;
    flex-direction: column;
}

.stat-lbl {
    font-size: 0.62rem;
    color: #94A3B8;
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: 0.06em;
}

.stat-val {
    font-size: 1.05rem;
    font-weight: 900;
    color: #F8FAFC;
}

.stat-blue { color: #38BDF8; }
.stat-green { color: #22C55E; }
.stat-red { color: #FF2B3A; }

/* 3 Macro Cards Grid Layout */
.section-title {
    font-size: 0.82rem;
    font-weight: 800;
    color: #F8FAFC;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.6rem;
}

.macro-cards-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.45rem;
    margin-bottom: 1.25rem;
    width: 100%;
}

.macro-glass-card {
    background: rgba(10, 14, 22, 0.72);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 0.75rem 0.35rem;
    text-align: center;
    min-width: 0;
}

.macro-protein { border-color: rgba(255, 59, 77, 0.3); }
.macro-carbs { border-color: rgba(56, 189, 248, 0.3); }
.macro-fat { border-color: rgba(251, 191, 36, 0.3); }

.macro-card-title {
    font-size: 0.75rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.macro-card-val {
    font-size: 0.92rem;
    font-weight: 900;
    color: #F8FAFC;
}

.macro-progress-bar {
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin: 0.4rem 0 0.3rem 0;
}

.macro-progress-fill {
    height: 100%;
    border-radius: 8px;
}

.fill-protein { background: linear-gradient(90deg, #FF3B4D 0%, #FF6B00 100%); }
.fill-carbs { background: linear-gradient(90deg, #38BDF8 0%, #0284C7 100%); }
.fill-fat { background: linear-gradient(90deg, #FBBF24 0%, #D97706 100%); }

.macro-card-sub {
    font-size: 0.62rem;
    color: #94A3B8;
    font-weight: 600;
}

/* Insight Box */
.insight-glass-card {
    background: rgba(10, 14, 22, 0.72) !important;
    backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 43, 58, 0.25) !important;
}

.insight-content-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
}

.insight-icon {
    font-size: 1.3rem;
}

.insight-title {
    font-weight: 800;
    color: #FF2B3A;
    margin-bottom: 0.25rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.insight-body {
    font-size: 0.84rem;
    color: #F8FAFC;
    line-height: 1.45;
}

/* Touch Friendly Mobile Buttons */
div[data-testid="stButton"] > button {
    width: 100% !important;
    height: 50px !important;
    min-height: 50px !important;
    border-radius: 14px !important;
    padding: 0 0.5rem !important;
    font-weight: 800 !important;
    font-size: 0.86rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: normal !important;
    line-height: 1.2 !important;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #FF2B3A 0%, #CC1122 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 20px rgba(255, 43, 58, 0.45) !important;
    border: none !important;
}

div[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(15, 20, 28, 0.8) !important;
    backdrop-filter: blur(12px) !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
}

/* Meals Section Header & Empty State */
.meals-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0.5rem 0 0.65rem 0;
}

.meals-header-title {
    font-size: 0.85rem;
    font-weight: 800;
    color: #F8FAFC;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.meals-header-link {
    font-size: 0.78rem;
    font-weight: 700;
    color: #FF2B3A;
    cursor: pointer;
}

.empty-meals-card {
    text-align: center;
    padding: 1.8rem 1.25rem !important;
    border: 1px dashed rgba(255, 43, 58, 0.35) !important;
}

.empty-meals-icon {
    font-size: 2.8rem;
    margin-bottom: 0.4rem;
}

.empty-meals-title {
    font-size: 1.15rem;
    font-weight: 900;
    color: #F8FAFC;
    margin-bottom: 0.3rem;
}

.empty-meals-sub {
    font-size: 0.82rem;
    color: #94A3B8;
    max-width: 260px;
    margin: 0 auto;
}

/* COMPACT INTEGRATED TOP MOBILE NAVIGATION BAR */
div[data-testid="stRadio"]:has(div[role="radiogroup"][aria-label*="Navigation"]) {
    margin: 0 0 20px 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

div[data-testid="stRadio"]:has(div[role="radiogroup"][aria-label*="Navigation"]) > label {
    display: none !important;
}

div[role="radiogroup"][aria-label*="Navigation"] {
    position: relative !important;
    width: 100% !important;
    max-width: 440px !important;
    height: 58px !important;
    z-index: 100 !important;
    display: grid !important;
    grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
    gap: 0 !important;
    align-items: center !important;
    justify-items: center !important;
    background: rgba(8, 10, 15, 0.88) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
    padding: 0 !important;
    margin: 0 0 20px 0 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

/* Hide native radio input and circle icons */
div[role="radiogroup"][aria-label*="Navigation"] input[type="radio"],
div[role="radiogroup"][aria-label*="Navigation"] [data-testid="stRadioButtonCustomIcon"],
div[role="radiogroup"][aria-label*="Navigation"] [class*="eqiohyi4"],
div[role="radiogroup"][aria-label*="Navigation"] [class*="eqiohyi5"],
div[role="radiogroup"][aria-label*="Navigation"] label > span {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    visibility: hidden !important;
}

div[role="radiogroup"][aria-label*="Navigation"] label > div,
div[role="radiogroup"][aria-label*="Navigation"] label > div > div {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* EVERY Navigation Cell has EXACTLY the same dimensions and width */
div[role="radiogroup"][aria-label*="Navigation"] label {
    width: 100% !important;
    height: 58px !important;
    max-height: 58px !important;
    min-height: 58px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    background: transparent !important;
    border-radius: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    border-bottom: 2.5px solid transparent !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 0 !important;
    flex: 1 1 0% !important;
}

div[role="radiogroup"][aria-label*="Navigation"] label div[data-testid="stMarkdownContainer"] {
    width: 100% !important;
    text-align: center !important;
    min-width: 0 !important;
}

/* Inactive Nav Labels: Grey text, grey icon */
div[role="radiogroup"][aria-label*="Navigation"] label div[data-testid="stMarkdownContainer"] p {
    font-size: 0.58rem !important; /* ~9.5px */
    font-weight: 600 !important;
    color: #94A3B8 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.15 !important;
    text-align: center !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

div[role="radiogroup"][aria-label*="Navigation"] label div[data-testid="stMarkdownContainer"] p::first-line {
    font-size: 1.15rem !important; /* ~18-20px icon */
    line-height: 1.2 !important;
}

div[role="radiogroup"][aria-label*="Navigation"] label:hover div[data-testid="stMarkdownContainer"] p {
    color: #F8FAFC !important;
}

/* ACTIVE ITEM: Identical cell size, subtle red background & red underline indicator */
div[role="radiogroup"][aria-label*="Navigation"] label[data-checked="true"],
div[role="radiogroup"][aria-label*="Navigation"] label:has(input:checked) {
    background: rgba(255, 43, 58, 0.12) !important;
    border-bottom: 2.5px solid #FF2B3A !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

div[role="radiogroup"][aria-label*="Navigation"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] p,
div[role="radiogroup"][aria-label*="Navigation"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
    color: #FF2B3A !important;
    font-weight: 800 !important;
    text-shadow: 0 0 10px rgba(255, 43, 58, 0.4) !important;
}

/* Coach Chat Bubbles */
.chat-bubble-user {
    background: linear-gradient(135deg, #FF2B3A 0%, #CC1122 100%);
    color: #FFFFFF;
    border-radius: 18px 18px 4px 18px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0 0.5rem auto;
    max-width: 88%;
    font-size: 0.88rem;
    font-weight: 600;
    box-shadow: 0 4px 14px rgba(255, 43, 58, 0.3);
}

.chat-bubble-assistant {
    background-color: rgba(15, 18, 25, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #F8FAFC;
    border-radius: 18px 18px 18px 4px;
    padding: 0.85rem 1rem;
    margin: 0.5rem auto 0.5rem 0;
    max-width: 92%;
    font-size: 0.86rem;
    line-height: 1.5;
}

/* Coach Chat Input Integration */
div[data-testid="stChatInput"] {
    width: 100% !important;
    max-width: 440px !important;
    margin: 0 auto !important;
    border-radius: 16px !important;
    background: rgba(10, 14, 22, 0.92) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 43, 58, 0.35) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
}

div[data-testid="stChatInput"] button {
    background: #FF2B3A !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    border: none !important;
}

/* Expanders & Form Controls */
div[data-testid="stExpander"] {
    background: rgba(10, 14, 22, 0.72) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 16px !important;
    color: #F8FAFC !important;
    overflow: hidden !important;
}

div[data-testid="stExpander"] summary {
    font-weight: 700 !important;
    color: #F8FAFC !important;
    padding: 0.75rem 1rem !important;
}

input, select, textarea, div[data-baseweb="select"] {
    background-color: rgba(15, 20, 30, 0.8) !important;
    color: #F8FAFC !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
}

div[data-baseweb="select"] > div {
    background-color: rgba(15, 20, 30, 0.8) !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
    color: #F8FAFC !important;
}

/* Badges */
.badge-high {
    background-color: rgba(34, 197, 94, 0.2);
    color: #22C55E;
    border: 1px solid #22C55E;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-medium {
    background-color: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    border: 1px solid #F59E0B;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-low {
    background-color: rgba(255, 43, 58, 0.2);
    color: #FF2B3A;
    border: 1px solid #FF2B3A;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
}

.trend-bar-bg {
    background-color: rgba(11, 15, 21, 0.9);
    border-radius: 8px;
    height: 10px;
    width: 100%;
    overflow: hidden;
    margin-top: 0.25rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- State & Persistence Initialization ---
def init_session_state():
    stored_profile = profile_storage.load_profile()

    if "onboarding_complete" not in st.session_state:
        st.session_state.onboarding_complete = stored_profile is not None

    if "step" not in st.session_state:
        st.session_state.step = 1

    if "onboarding_data" not in st.session_state:
        if stored_profile:
            st.session_state.onboarding_data = stored_profile
        else:
            st.session_state.onboarding_data = {
                "age": 25,
                "sex": "Male",
                "height_cm": 178.0,
                "weight_kg": 75.0,
                "activity_level": "Moderately Active",
                "goal": "Fat Loss",
                "intensity": "Moderate",
            }

    if "user_plan" not in st.session_state:
        d = st.session_state.onboarding_data
        plan = calculate_full_plan(
            age=d["age"],
            sex=d["sex"],
            height_cm=d["height_cm"],
            weight_kg=d["weight_kg"],
            activity_level=d["activity_level"],
            goal=d["goal"],
            intensity=d["intensity"],
        )
        st.session_state.user_plan = plan

        # Ensure initial target snapshot exists
        if not target_storage.load_target_snapshots():
            target_storage.create_target_snapshot(plan, effective_date=get_today_str())

    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Home"

    if "scan_analysis" not in st.session_state:
        st.session_state.scan_analysis = None

    if "scan_image" not in st.session_state:
        st.session_state.scan_image = None

    if "scan_meal_type" not in st.session_state:
        st.session_state.scan_meal_type = "Lunch"

    if "editing_meal_id" not in st.session_state:
        st.session_state.editing_meal_id = None

    if "deleting_meal_id" not in st.session_state:
        st.session_state.deleting_meal_id = None

    if "nutrition_chat" not in st.session_state:
        st.session_state.nutrition_chat = [
            {
                "role": "assistant",
                "content": "Hello! I'm **MacroSnap Coach**. Ask me anything about your nutrition, high-protein meal options, dinner recommendations, or staying on track today!",
            }
        ]

    if "progress_days" not in st.session_state:
        st.session_state.progress_days = 7

    if "pending_plan_preview" not in st.session_state:
        st.session_state.pending_plan_preview = None


def get_today_str() -> str:
    return datetime.date.today().isoformat()


init_session_state()


def clean_html(raw_html: str) -> str:
    """Strips leading/trailing whitespace per line and joins with spaces to avoid attribute concatenation and code blocks."""
    if not raw_html:
        return ""
    lines = [line.strip() for line in raw_html.splitlines() if line.strip()]
    return " ".join(lines)


def render_html(raw_html: str):
    """Renders raw HTML/SVG cleanly into Streamlit without Markdown code block parsing or DOMPurify SVG stripping."""
    cleaned = clean_html(raw_html)
    if cleaned:
        st.markdown(cleaned, unsafe_allow_html=True)


# --- Header Component ---
def render_header():
    render_html(
        """
        <div class="hero-top-bar">
            <div class="logo-box">
                <div class="logo-title"><span class="logo-macro">MACRO</span><span class="logo-snap">SNAP</span></div>
                <div class="logo-tagline">FUEL YOUR DISCIPLINE</div>
            </div>
            <div class="hero-actions">
                <div class="icon-btn-glass" title="Notifications">🔔</div>
                <div class="icon-btn-glass" title="Profile">👤</div>
            </div>
        </div>
        """
    )


# --- Progress Indicator Component ---
def render_progress_indicator(current_step: int, total_steps: int = 5):
    dots_html = '<div class="progress-container">'
    for i in range(1, total_steps + 1):
        if i == current_step:
            dots_html += '<div class="step-dot active"></div>'
        elif i < current_step:
            dots_html += '<div class="step-dot completed"></div>'
        else:
            dots_html += '<div class="step-dot"></div>'
    dots_html += "</div>"
    render_html(dots_html)


# ==================================================
# ONBOARDING FLOW SCREENS (STABLE ENGINE)
# ==================================================

def render_screen_1_basic_info():
    render_progress_indicator(1, 5)
    render_html('<div class="onboarding-title" style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; text-align: center;">BUILD YOUR PLAN</div>')
    render_html('<div class="onboarding-subtitle" style="font-size: 0.85rem; color: #94A3B8; text-align: center; margin-bottom: 1rem;">Step 1: Personal Profile Setup</div>')

    data = st.session_state.onboarding_data

    col_age, col_sex = st.columns(2)
    with col_age:
        age_val = st.number_input(
            "Age",
            min_value=14,
            max_value=100,
            value=int(data.get("age", 25)),
            step=1,
            help="Age in years",
        )

    with col_sex:
        sex_options = ["Male", "Female"]
        current_sex = data.get("sex", "Male")
        sex_index = sex_options.index(current_sex) if current_sex in sex_options else 0
        sex_val = st.radio("Sex", options=sex_options, index=sex_index, horizontal=True)

    col_h, col_w = st.columns(2)
    with col_h:
        height_val = st.number_input(
            "Height (cm)",
            min_value=100.0,
            max_value=250.0,
            value=float(data.get("height_cm", 178.0)),
            step=0.5,
        )

    with col_w:
        weight_val = st.number_input(
            "Current Weight (kg)",
            min_value=30.0,
            max_value=300.0,
            value=float(data.get("weight_kg", 75.0)),
            step=0.5,
        )

    render_html("<br>")

    if st.button("Next: Activity Level ➔", type="primary", use_container_width=True):
        st.session_state.onboarding_data["age"] = int(age_val)
        st.session_state.onboarding_data["sex"] = sex_val
        st.session_state.onboarding_data["height_cm"] = float(height_val)
        st.session_state.onboarding_data["weight_kg"] = float(weight_val)
        st.session_state.step = 2
        st.rerun()


def render_screen_2_activity_level():
    render_progress_indicator(2, 5)
    render_html('<div class="onboarding-title" style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; text-align: center;">Activity Level</div>')
    render_html('<div class="onboarding-subtitle" style="font-size: 0.85rem; color: #94A3B8; text-align: center; margin-bottom: 1rem;">Select your typical daily activity</div>')

    data = st.session_state.onboarding_data
    act_keys = list(ACTIVITY_MULTIPLIERS.keys())
    current_act = data.get("activity_level", "Moderately Active")
    act_index = act_keys.index(current_act) if current_act in act_keys else 2

    selected_act = st.radio(
        "Select Activity",
        options=act_keys,
        index=act_index,
        format_func=lambda k: f"**{k}** — _{ACTIVITY_DESCRIPTIONS[k]}_",
    )

    render_html("<br>")

    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

    with col_next:
        if st.button("Next: Fitness Goal ➔", type="primary", use_container_width=True):
            st.session_state.onboarding_data["activity_level"] = selected_act
            st.session_state.step = 3
            st.rerun()


def render_screen_3_fitness_goal():
    render_progress_indicator(3, 5)
    render_html('<div class="onboarding-title" style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; text-align: center;">Fitness Goal</div>')
    render_html('<div class="onboarding-subtitle" style="font-size: 0.85rem; color: #94A3B8; text-align: center; margin-bottom: 1rem;">What is your primary target?</div>')

    data = st.session_state.onboarding_data
    goal_keys = list(GOAL_CONFIG.keys())
    current_goal = data.get("goal", "Fat Loss")
    goal_index = goal_keys.index(current_goal) if current_goal in goal_keys else 0

    selected_goal = st.radio(
        "Select Goal",
        options=goal_keys,
        index=goal_index,
        format_func=lambda k: f"{GOAL_CONFIG[k]['emoji']} **{k}** — _{GOAL_CONFIG[k]['description']}_",
    )

    render_html("<br>")

    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    with col_next:
        if st.button("Next: Goal Intensity ➔", type="primary", use_container_width=True):
            st.session_state.onboarding_data["goal"] = selected_goal
            st.session_state.step = 4
            st.rerun()


def render_screen_4_goal_intensity():
    render_progress_indicator(4, 5)
    goal = st.session_state.onboarding_data.get("goal", "Fat Loss")
    goal_emoji = GOAL_CONFIG.get(goal, {}).get("emoji", "🎯")
    render_html(f'<div class="onboarding-title" style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; text-align: center;">{goal_emoji} Goal Intensity</div>')
    render_html(f'<div class="onboarding-subtitle" style="font-size: 0.85rem; color: #94A3B8; text-align: center; margin-bottom: 1rem;">Choose your preferred pace for {goal}</div>')

    data = st.session_state.onboarding_data
    intensities = GOAL_CONFIG.get(goal, {}).get("intensities", {})
    intensity_keys = list(intensities.keys())

    if not intensity_keys:
        intensity_keys = ["Moderate"]

    current_int = data.get("intensity", "Moderate")
    int_index = intensity_keys.index(current_int) if current_int in intensity_keys else 0

    selected_int = st.radio(
        "Select Intensity Pace",
        options=intensity_keys,
        index=int_index,
        format_func=lambda k: f"**{k}** — _{intensities.get(k, {}).get('desc', '')}_",
    )

    render_html("<br>")

    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

    with col_next:
        if st.button("Calculate Plan ➔", type="primary", use_container_width=True):
            st.session_state.onboarding_data["intensity"] = selected_int
            d = st.session_state.onboarding_data
            plan = calculate_full_plan(
                age=d["age"],
                sex=d["sex"],
                height_cm=d["height_cm"],
                weight_kg=d["weight_kg"],
                activity_level=d["activity_level"],
                goal=d["goal"],
                intensity=d["intensity"],
            )
            st.session_state.user_plan = plan
            st.session_state.step = 5
            st.rerun()


def render_screen_5_plan_confirmation():
    render_progress_indicator(5, 5)
    plan = st.session_state.user_plan

    if not plan:
        d = st.session_state.onboarding_data
        plan = calculate_full_plan(
            age=d["age"],
            sex=d["sex"],
            height_cm=d["height_cm"],
            weight_kg=d["weight_kg"],
            activity_level=d["activity_level"],
            goal=d["goal"],
            intensity=d["intensity"],
        )
        st.session_state.user_plan = plan

    render_html('<div class="onboarding-title" style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; text-align: center;">YOUR MACROSNAP PLAN</div>')
    render_html('<div class="onboarding-subtitle" style="font-size: 0.85rem; color: #94A3B8; text-align: center; margin-bottom: 1rem;">Custom science-backed nutrition blueprint</div>')

    adj_symbol = "-" if plan["adjustment_type"] == "Deficit" else ("+" if plan["adjustment_type"] == "Surplus" else "")
    adj_text = f"{adj_symbol}{plan['adjustment_kcal']} kcal" if plan["adjustment_kcal"] > 0 else "None (Maintenance)"

    card_html = f"""
    <div class="glass-card glass-card-hero">
        <div style="text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF2B3A; font-weight: 800; margin-bottom: 0.4rem;">CALCULATED TARGETS</div>
        <div style="text-align: center; font-size: 1.3rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.85rem;">{plan['goal_emoji']} {plan['goal']} ({plan['intensity']})</div>
        
        <div style="display: flex; justify-content: space-between; padding: 0.55rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
            <span style="color: #94A3B8;">Estimated Maintenance (TDEE)</span>
            <span style="color: #F8FAFC; font-weight: 700;">{plan['tdee']:,} kcal</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.55rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
            <span style="color: #94A3B8;">{plan['adjustment_type']} Adjustment</span>
            <span style="color: #F8FAFC; font-weight: 700;">{adj_text}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; padding-top: 0.75rem; border-top: 1px solid rgba(255, 43, 58, 0.3);">
            <span style="font-weight: 700; color: #F8FAFC;">Daily Calorie Target</span>
            <span style="font-size: 1.35rem; color: #FF2B3A; font-weight: 900;">{plan['target_calories']:,} kcal</span>
        </div>

        <div class="macro-cards-grid" style="margin-top: 0.85rem; margin-bottom: 0;">
            <div class="macro-glass-card macro-protein">
                <div class="macro-card-val" style="color: #FF3B4D;">{plan['protein_g']}g</div>
                <div class="macro-card-sub">Protein</div>
            </div>
            <div class="macro-glass-card macro-carbs">
                <div class="macro-card-val" style="color: #38BDF8;">{plan['carbs_g']}g</div>
                <div class="macro-card-sub">Carbs</div>
            </div>
            <div class="macro-glass-card macro-fat">
                <div class="macro-card-val" style="color: #FBBF24;">{plan['fat_g']}g</div>
                <div class="macro-card-sub">Fat</div>
            </div>
        </div>
    </div>
    """
    render_html(card_html)

    render_html(f'<div style="background-color: rgba(30, 41, 59, 0.6); border-left: 3px solid #FF2B3A; border-radius: 10px; padding: 0.7rem 0.85rem; font-size: 0.78rem; color: #CBD5E1; line-height: 1.4; margin: 1rem 0;">⚠️ <strong>Disclaimer:</strong> {PLAN_DISCLAIMER_TEXT}</div>')

    col_recalc, col_start = st.columns([1, 2])
    with col_recalc:
        if st.button("✏️ Edit", type="secondary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

    with col_start:
        if st.button("⚡ Start Tracking", type="primary", use_container_width=True):
            profile_storage.save_profile(st.session_state.onboarding_data)
            target_storage.create_target_snapshot(plan, effective_date=get_today_str())
            st.session_state.onboarding_complete = True
            st.session_state.active_tab = "Home"
            st.rerun()


# ==================================================
# MAIN SHELL & ROUTER
# ==================================================

def render_main_app(plan):
    # Inject full-viewport dark anime background per active tab with fixed centered container
    bg_map = {
        "Home": "home-bg.png",
        "Snap": "snap-bg.png",
        "Coach": "coach-bg.png",
        "History": "history-bg.png",
        "Progress": "progress-bg.png",
        "Profile": "profile-bg.png",
    }
    current_bg_file = bg_map.get(st.session_state.active_tab, "home-bg.png")
    bg_b64 = get_asset_base64(current_bg_file)

    if bg_b64:
        st.markdown(
            f"""
            <style>
            .stApp::before {{
                content: "";
                position: fixed;
                top: 0;
                left: 50%;
                transform: translateX(-50%);
                width: 100vw;
                max-width: 440px;
                height: 100vh;
                z-index: 0;
                pointer-events: none;
                background-color: #07090D !important;
                background-image: 
                    linear-gradient(180deg, rgba(7, 9, 13, 0.15) 0%, rgba(7, 9, 13, 0.45) 45%, rgba(7, 9, 13, 0.90) 100%),
                    url("data:image/png;base64,{bg_b64}") !important;
                background-size: 100% auto !important;
                background-position: center top !important;
                background-repeat: no-repeat !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    render_header()

    tabs = [
        "🏠\nHome",
        "📸\nSnap",
        "🧠\nCoach",
        "📅\nHistory",
        "📊\nProgress",
        "👤\nProfile",
    ]

    nav_map = {
        "Home": "🏠\nHome",
        "Snap": "📸\nSnap",
        "Coach": "🧠\nCoach",
        "History": "📅\nHistory",
        "Progress": "📊\nProgress",
        "Profile": "👤\nProfile",
    }
    current_nav_label = nav_map.get(st.session_state.active_tab, "🏠\nHome")
    current_index = tabs.index(current_nav_label) if current_nav_label in tabs else 0

    selected_nav = st.radio(
        "Navigation",
        options=tabs,
        index=current_index,
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav_radio",
    )

    if "Home" in selected_nav and st.session_state.active_tab != "Home":
        st.session_state.active_tab = "Home"
        st.rerun()
    elif "Snap" in selected_nav and st.session_state.active_tab != "Snap":
        st.session_state.active_tab = "Snap"
        st.rerun()
    elif "Coach" in selected_nav and st.session_state.active_tab != "Coach":
        st.session_state.active_tab = "Coach"
        st.rerun()
    elif "History" in selected_nav and st.session_state.active_tab != "History":
        st.session_state.active_tab = "History"
        st.rerun()
    elif "Progress" in selected_nav and st.session_state.active_tab != "Progress":
        st.session_state.active_tab = "Progress"
        st.rerun()
    elif "Profile" in selected_nav and st.session_state.active_tab != "Profile":
        st.session_state.active_tab = "Profile"
        st.rerun()

    if st.session_state.active_tab == "Home":
        render_home_tab(plan)
    elif st.session_state.active_tab == "Snap":
        render_snap_tab(plan)
    elif st.session_state.active_tab == "Coach":
        render_coach_tab(plan)
    elif st.session_state.active_tab == "History":
        render_history_tab(plan)
    elif st.session_state.active_tab == "Progress":
        render_progress_tab(plan)
    elif st.session_state.active_tab == "Profile":
        render_profile_tab(plan)


# ==================================================
# TAB 1: HOME DASHBOARD (PRESENTATION LAYER)
# ==================================================

def render_home_tab(plan):
    today_str = get_today_str()
    today_formatted = datetime.date.today().strftime("%A, %b %d")

    consumed = meal_storage.get_daily_totals(today_str)
    today_meals = meal_storage.get_meals_for_date(today_str)

    rem_cal = plan["target_calories"] - consumed["calories"]
    rem_p = plan["protein_g"] - consumed["protein_g"]
    rem_c = plan["carbs_g"] - consumed["carbs_g"]
    rem_f = plan["fat_g"] - consumed["fat_g"]

    cal_pct = min(100.0, max(0.0, (consumed["calories"] / plan["target_calories"]) * 100)) if plan["target_calories"] > 0 else 0

    now_hour = datetime.datetime.now().hour
    if now_hour < 12:
        greeting_txt = "Good morning,"
    elif now_hour < 18:
        greeting_txt = "Good afternoon,"
    else:
        greeting_txt = "Good evening,"

    # 1. Top Hero Greeting
    greeting_html = f"""
    <div class="greeting-box">
        <div class="greeting-time">{greeting_txt}</div>
        <div class="greeting-name">CHAMP 👑</div>
        <div class="greeting-quote">"Discipline today for a stronger tomorrow."</div>
    </div>
    """
    render_html(greeting_html)

    # 2. Daily Calorie Budget Glass Card
    ring_html = f"""
    <div class="glass-card glass-card-hero">
        <div class="card-header-row">
            <span class="card-header-title">🔥 DAILY CALORIE BUDGET</span>
            <span class="card-header-date">{today_formatted}</span>
        </div>
        <div class="calorie-card-body">
            <div class="ring-wrapper">
                <svg width="130" height="130" viewBox="0 0 130 130">
                    <defs>
                        <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#FF2B3A" />
                            <stop offset="100%" stop-color="#FF6B00" />
                        </linearGradient>
                    </defs>
                    <circle cx="65" cy="65" r="52" stroke="rgba(255, 255, 255, 0.1)" stroke-width="11" fill="none" />
                    <circle cx="65" cy="65" r="52" stroke="url(#ringGradient)" stroke-width="11" fill="none"
                            stroke-dasharray="326.72" stroke-dashoffset="{326.72 * (1.0 - cal_pct / 100.0):.2f}"
                            stroke-linecap="round" transform="rotate(-90 65 65)" />
                </svg>
                <div class="ring-center-content">
                    <div class="ring-cals">{consumed['calories']:,}</div>
                    <div class="ring-target">/ {plan['target_calories']:,} kcal</div>
                    <div class="ring-pct">{int(cal_pct)}%</div>
                </div>
            </div>
            <div class="calorie-stats-list">
                <div class="stat-item">
                    <div class="stat-lbl">TARGET BUDGET</div>
                    <div class="stat-val">{plan['target_calories']:,} kcal</div>
                </div>
                <div class="stat-item">
                    <div class="stat-lbl">CONSUMED INTAKE</div>
                    <div class="stat-val stat-blue">{consumed['calories']:,} kcal</div>
                </div>
                <div class="stat-item">
                    <div class="stat-lbl">REMAINING</div>
                    <div class="stat-val {'stat-green' if rem_cal >= 0 else 'stat-red'}">{abs(rem_cal):,} kcal {'left' if rem_cal >= 0 else 'over'}</div>
                </div>
            </div>
        </div>
    </div>
    """
    render_html(ring_html)

    # 3. 3 Macro Cards Grid
    p_pct = min(100, int((consumed["protein_g"] / plan["protein_g"]) * 100)) if plan["protein_g"] > 0 else 0
    c_pct = min(100, int((consumed["carbs_g"] / plan["carbs_g"]) * 100)) if plan["carbs_g"] > 0 else 0
    f_pct = min(100, int((consumed["fat_g"] / plan["fat_g"]) * 100)) if plan["fat_g"] > 0 else 0

    macro_cards_html = f"""
    <div class="section-title">MACRONUTRIENTS PROGRESS</div>

    <div class="macro-cards-grid">
        <div class="macro-glass-card macro-protein">
            <div class="macro-card-title" style="color: #FF3B4D;">🥩 Protein</div>
            <div class="macro-card-val">{consumed['protein_g']} / {plan['protein_g']}g</div>
            <div class="macro-progress-bar">
                <div class="macro-progress-fill fill-protein" style="width: {p_pct}%;"></div>
            </div>
            <div class="macro-card-sub">{rem_p:,}g left</div>
        </div>
        <div class="macro-glass-card macro-carbs">
            <div class="macro-card-title" style="color: #38BDF8;">🍚 Carbs</div>
            <div class="macro-card-val">{consumed['carbs_g']} / {plan['carbs_g']}g</div>
            <div class="macro-progress-bar">
                <div class="macro-progress-fill fill-carbs" style="width: {c_pct}%;"></div>
            </div>
            <div class="macro-card-sub">{rem_c:,}g left</div>
        </div>
        <div class="macro-glass-card macro-fat">
            <div class="macro-card-title" style="color: #FBBF24;">🥑 Fat</div>
            <div class="macro-card-val">{consumed['fat_g']} / {plan['fat_g']}g</div>
            <div class="macro-progress-bar">
                <div class="macro-progress-fill fill-fat" style="width: {f_pct}%;"></div>
            </div>
            <div class="macro-card-sub">{rem_f:,}g left</div>
        </div>
    </div>
    """
    render_html(macro_cards_html)

    # 4. Today's Insight Card
    insight_text = analytics.get_goal_interpretation(goal=plan["goal"], avg_calories=consumed["calories"], target_calories=plan["target_calories"], tdee=int(plan["tdee"]))
    insight_html = f"""
    <div class="glass-card insight-glass-card">
        <div class="insight-content-row">
            <div class="insight-icon">💡</div>
            <div class="insight-text-box">
                <div class="insight-title">TODAY'S INSIGHT</div>
                <div class="insight-body">{insight_text}</div>
            </div>
        </div>
    </div>
    """
    render_html(insight_html)

    # 5. Primary Action Buttons
    col_snap_btn, col_quick_btn = st.columns([1.2, 1.0])
    with col_snap_btn:
        if st.button("📷 SNAP YOUR MEAL", type="primary", use_container_width=True):
            st.session_state.active_tab = "Snap"
            st.rerun()

    with col_quick_btn:
        if st.button("+ QUICK ADD", type="secondary", use_container_width=True):
            st.session_state.show_quick_add = not st.session_state.get("show_quick_add", False)

    if st.session_state.get("show_quick_add", False):
        render_quick_add_form(plan)

    render_html(
        """
        <div class="meals-header-row">
            <span class="meals-header-title">🍴 TODAY'S MEALS</span>
            <span class="meals-header-link">View All →</span>
        </div>
        """
    )

    if not today_meals:
        empty_html = """
        <div class="glass-card empty-meals-card">
            <div class="empty-meals-icon">🥣</div>
            <div class="empty-meals-title">Nothing logged yet.</div>
            <div class="empty-meals-sub">Snap your first meal to start tracking today's nutrition.</div>
        </div>
        """
        render_html(empty_html)
        if st.button("📷 SNAP YOUR MEAL", type="primary", key="empty_snap_btn", use_container_width=True):
            st.session_state.active_tab = "Snap"
            st.rerun()
    else:
        for meal in today_meals:
            m_id = meal.get("meal_id")
            m_type = meal.get("meal_type", "Meal")
            m_icon = "🥣" if m_type == "Breakfast" else ("🍱" if m_type == "Lunch" else ("🥗" if m_type == "Dinner" else "🍎"))
            tot = meal.get("total", {})
            cals = tot.get("calories", 0)

            p = tot.get("protein_g", 0)
            c = tot.get("carbs_g", 0)
            f = tot.get("fat_g", 0)

            time_str = ""
            if "timestamp" in meal:
                try:
                    dt = datetime.datetime.fromisoformat(meal["timestamp"])
                    time_str = dt.strftime("%I:%M %p")
                except Exception:
                    time_str = ""

            with st.expander(f"{m_icon} {m_type} • {cals:,} kcal ({time_str if time_str else 'Today'})", expanded=False):
                st.markdown(f"**Time:** {time_str if time_str else 'Today'} | **Macros:** P: {p}g | C: {c}g | F: {f}g")
                st.markdown("---")
                for food in meal.get("foods", []):
                    st.markdown(
                        f"• **{food.get('name')}** ({food.get('portion', '')}) — {food.get('calories')} kcal "
                        f"_(P: {food.get('protein_g')}g, C: {food.get('carbs_g')}g, F: {food.get('fat_g')}g)_"
                    )
                render_html("<br>")
                col_m_edit, col_m_del = st.columns(2)
                with col_m_edit:
                    if st.button("✏️ Edit Meal", key=f"medit_btn_{m_id}", type="secondary", use_container_width=True):
                        st.session_state.editing_meal_id = m_id
                        st.session_state.deleting_meal_id = None
                with col_m_del:
                    if st.button("🗑️ Delete Meal", key=f"mdel_btn_{m_id}", type="secondary", use_container_width=True):
                        st.session_state.deleting_meal_id = m_id
                        st.session_state.editing_meal_id = None

                if st.session_state.get("editing_meal_id") == m_id:
                    render_inline_meal_editor(meal)

                if st.session_state.get("deleting_meal_id") == m_id:
                    st.warning("Are you sure you want to delete this meal?")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("Yes, Delete", key=f"confirm_del_{m_id}", type="primary"):
                            meal_storage.delete_meal(m_id)
                            st.session_state.deleting_meal_id = None
                            st.rerun()
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_del_{m_id}", type="secondary"):
                            st.session_state.deleting_meal_id = None
                            st.rerun()


def render_quick_add_form(plan):
    render_html("<hr style='border-color: rgba(255, 43, 58, 0.3); margin: 0.75rem 0;'>")
    render_html("<div style='font-size: 0.9rem; font-weight: 800; color: #FF2B3A; margin-bottom: 0.5rem;'>＋ Quick Add Meal (Manual)</div>")

    with st.form("quick_add_meal_form", clear_on_submit=True):
        meal_type = st.selectbox("Meal Type", options=["Breakfast", "Lunch", "Dinner", "Snack"], index=1)
        food_name = st.text_input("Food Item Name", value="", placeholder="e.g., Grilled Chicken Breast & Rice")
        portion_desc = st.text_input("Portion / Serving Size", value="", placeholder="e.g., 200g chicken, 150g rice")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cals = st.number_input("Calories", min_value=0, value=500, step=10)
        with col2:
            prot = st.number_input("Protein (g)", min_value=0, value=40, step=1)
        with col3:
            carbs = st.number_input("Carbs (g)", min_value=0, value=50, step=1)
        with col4:
            fat = st.number_input("Fat (g)", min_value=0, value=10, step=1)

        submitted = st.form_submit_button("⚡ Save Meal To Log", type="primary")
        if submitted:
            if not food_name.strip():
                st.error("Please enter a food item name.")
            else:
                food_item = {
                    "name": food_name.strip(),
                    "portion": portion_desc.strip() if portion_desc.strip() else "1 serving",
                    "calories": int(cals),
                    "protein_g": int(prot),
                    "carbs_g": int(carbs),
                    "fat_g": int(fat),
                }
                new_meal = {
                    "meal_id": str(uuid.uuid4())[:8],
                    "date": get_today_str(),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "meal_type": meal_type,
                    "foods": [food_item],
                    "total": {
                        "calories": int(cals),
                        "protein_g": int(prot),
                        "carbs_g": int(carbs),
                        "fat_g": int(fat),
                    },
                }
                meal_storage.add_meal(new_meal)
                st.session_state.show_quick_add = False
                st.success("Meal added successfully!")
                st.rerun()


def render_inline_meal_editor(meal):
    render_html("<hr style='border-color: rgba(255, 43, 58, 0.3); margin: 1rem 0;'>")
    st.markdown("### ✏️ Edit Confirmed Meal")

    m_id = meal["meal_id"]
    new_type = st.selectbox(
        "Meal Type",
        options=["Breakfast", "Lunch", "Dinner", "Snack"],
        index=["Breakfast", "Lunch", "Dinner", "Snack"].index(meal.get("meal_type", "Lunch")),
        key=f"etype_{m_id}",
    )

    edited_foods = []
    for idx, f in enumerate(meal.get("foods", [])):
        st.markdown(f"**Food Item #{idx+1}**")
        fname = st.text_input("Name", value=f.get("name", ""), key=f"efname_{m_id}_{idx}")
        fport = st.text_input("Portion", value=f.get("portion", ""), key=f"efport_{m_id}_{idx}")
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            fcals = st.number_input("Cals", min_value=0, value=int(f.get("calories", 0)), key=f"efcals_{m_id}_{idx}")
        with ec2:
            fprot = st.number_input("Prot", min_value=0, value=int(f.get("protein_g", 0)), key=f"efprot_{m_id}_{idx}")
        with ec3:
            fcarbs = st.number_input("Carbs", min_value=0, value=int(f.get("carbs_g", 0)), key=f"efcarbs_{m_id}_{idx}")
        with ec4:
            ffat = st.number_input("Fat", min_value=0, value=int(f.get("fat_g", 0)), key=f"effat_{m_id}_{idx}")

        edited_foods.append({
            "name": fname.strip() if fname.strip() else f.get("name", "Food Item"),
            "portion": fport.strip() if fport.strip() else "1 serving",
            "calories": int(fcals),
            "protein_g": int(fprot),
            "carbs_g": int(fcarbs),
            "fat_g": int(ffat),
        })

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save Changes", key=f"esave_{m_id}", type="primary"):
            updated_tot = {
                "calories": sum(item["calories"] for item in edited_foods),
                "protein_g": sum(item["protein_g"] for item in edited_foods),
                "carbs_g": sum(item["carbs_g"] for item in edited_foods),
                "fat_g": sum(item["fat_g"] for item in edited_foods),
            }
            updated_meal = {
                "meal_id": m_id,
                "timestamp": meal.get("timestamp", datetime.datetime.now().isoformat()),
                "meal_type": new_type,
                "foods": edited_foods,
                "total": updated_tot,
            }
            meal_storage.update_meal(m_id, updated_meal)
            st.session_state.editing_meal_id = None
            st.success("Meal updated successfully!")
            st.rerun()

    with col_cancel:
        if st.button("Cancel", key=f"ecancel_{m_id}", type="secondary"):
            st.session_state.editing_meal_id = None
            st.rerun()


# ==================================================
# TAB 2: SNAP MEAL (GEMINI VISION AI SCANNER)
# ==================================================

def render_snap_tab(plan):
    render_html('<div class="section-title" style="font-size: 1.25rem; font-weight: 900; color: #F8FAFC;">📷 SNAP YOUR MEAL</div>')
    render_html('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;">Take a photo and let MacroSnap estimate the nutrition</div>')

    render_html(
        f"""
        <div class="glass-card" style="border-left: 3px solid #FF2B3A; background: rgba(255, 43, 58, 0.08);">
            ℹ️ <strong>AI Vision Scanner:</strong> Take or upload a photo of your meal. You can review and edit all detected foods before saving.
        </div>
        """
    )

    meal_type_option = st.selectbox(
        "Meal Category",
        options=["Breakfast", "Lunch", "Dinner", "Snack"],
        index=["Breakfast", "Lunch", "Dinner", "Snack"].index(st.session_state.scan_meal_type),
    )
    st.session_state.scan_meal_type = meal_type_option

    input_mode = st.radio("Photo Source", options=["Upload Photo", "Camera"], horizontal=True)

    uploaded_file = None
    if input_mode == "Upload Photo":
        uploaded_file = st.file_uploader("Choose a meal image...", type=["jpg", "jpeg", "png", "webp"])
    else:
        uploaded_file = st.camera_input("Take a photo of your meal")

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Meal Image", use_column_width=True)

            api_key = get_gemini_api_key()
            if not api_key:
                st.warning("🔑 GEMINI_API_KEY is not set in secrets or environment. Cannot run live Vision scan.")
            else:
                if st.button("🧠 Analyze Meal With Gemini AI", type="primary", use_container_width=True):
                    with st.spinner("Analyzing meal ingredients and calculating macros..."):
                        start_time = time.time()
                        analysis_result = analyze_meal_image(image)
                        latency = time.time() - start_time
                        analysis_result["_latency_sec"] = round(latency, 2)
                        st.session_state.scan_analysis = analysis_result
                        st.session_state.scan_image = image
                        st.rerun()
        except Exception as e:
            st.error(f"Error loading image: {e}")

    render_html("<br>")
    render_html("<div style='font-size: 0.8rem; font-weight: 700; color: #94A3B8;'>DEMO & TESTING ASSISTANT</div>")
    if st.button("🧪 Load Sample Meal Analysis (Demo)", type="secondary", use_container_width=True):
        st.session_state.scan_analysis = {
            "overall_confidence": "high",
            "detected_foods": [
                {
                    "name": "Grilled Chicken Breast",
                    "portion": "180g",
                    "calories": 290,
                    "protein_g": 56,
                    "carbs_g": 0,
                    "fat_g": 6,
                },
                {
                    "name": "Steamed White Rice",
                    "portion": "150g",
                    "calories": 195,
                    "protein_g": 4,
                    "carbs_g": 43,
                    "fat_g": 1,
                },
                {
                    "name": "Roasted Broccoli",
                    "portion": "100g",
                    "calories": 55,
                    "protein_g": 4,
                    "carbs_g": 10,
                    "fat_g": 2,
                }
            ],
            "total_estimated": {
                "calories": 540,
                "protein_g": 64,
                "carbs_g": 53,
                "fat_g": 9,
            },
            "notes": "Healthy balanced fitness meal rich in lean protein.",
            "_latency_sec": 0.45,
        }
        st.rerun()

    if st.session_state.scan_analysis:
        render_html("<hr style='border-color: #FF2B3A; margin: 1.5rem 0;'>")
        render_editable_meal_analysis_ui()


def render_editable_meal_analysis_ui():
    analysis = st.session_state.scan_analysis
    if not analysis:
        return

    render_html('<div class="section-title" style="font-size: 1.2rem; font-weight: 900; color: #F8FAFC;">🍛 MEAL ANALYSIS</div>')

    conf = analysis.get("overall_confidence", "medium")
    badge_class = "badge-high" if conf == "high" else ("badge-medium" if conf == "medium" else "badge-low")

    render_html(
        f"""
        <div style="text-align: center; margin-bottom: 1rem;">
            <span class="{badge_class}">AI Confidence: {overall_confidence_label(conf)}</span>
        </div>
        """
    )

    if "_latency_sec" in analysis:
        st.caption(f"⚡ Gemini Vision latency: {analysis['_latency_sec']} seconds")

    if analysis.get("notes"):
        render_html(
            f"""
            <div class="glass-card" style="font-size: 0.82rem; color: #CBD5E1;">
                📝 <strong>AI Chef Note:</strong> {analysis['notes']}
            </div>
            """
        )

    render_html("<div style='font-size: 0.9rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.75rem;'>Detected Foods (Review & Edit)</div>")

    foods = analysis.get("detected_foods", [])
    edited_foods = []
    to_delete_idx = None

    for idx, food in enumerate(foods):
        render_html(f"<div class='glass-card' style='padding: 0.85rem; margin-bottom: 0.75rem;'>")
        c1, c2, c3 = st.columns([2, 2, 0.5])
        with c1:
            f_name = st.text_input("Food Item", value=food.get("name", ""), key=f"fname_{idx}")
        with c2:
            f_portion = st.text_input("Portion", value=food.get("portion", ""), key=f"fport_{idx}")
        with c3:
            render_html("<div style='margin-top: 1.7rem;'></div>")
            if st.button("🗑️", key=f"fdel_{idx}", help="Remove item"):
                to_delete_idx = idx

        fc1, fc2 = st.columns(2)
        with fc1:
            f_cals = st.number_input("Calories", min_value=0, value=int(food.get("calories", 0)), key=f"fcals_{idx}")
        with fc2:
            f_p = st.number_input("Prot (g)", min_value=0, value=int(food.get("protein_g", 0)), key=f"fp_{idx}")

        fc3, fc4 = st.columns(2)
        with fc3:
            f_c = st.number_input("Carbs (g)", min_value=0, value=int(food.get("carbs_g", 0)), key=f"fc_{idx}")
        with fc4:
            f_f = st.number_input("Fat (g)", min_value=0, value=int(food.get("fat_g", 0)), key=f"ff_{idx}")

        render_html("</div>")

        edited_foods.append({
            "name": f_name,
            "portion": f_portion,
            "calories": f_cals,
            "protein_g": f_p,
            "carbs_g": f_c,
            "fat_g": f_f,
        })

    if to_delete_idx is not None:
        edited_foods.pop(to_delete_idx)
        st.session_state.scan_analysis["detected_foods"] = edited_foods
        st.rerun()

    if st.button("＋ Add Another Item", type="secondary"):
        edited_foods.append({
            "name": "New Item",
            "portion": "1 serving",
            "calories": 100,
            "protein_g": 5,
            "carbs_g": 10,
            "fat_g": 2,
        })
        st.session_state.scan_analysis["detected_foods"] = edited_foods
        st.rerun()

    # Recalculate Totals
    tot_cals = sum(item["calories"] for item in edited_foods)
    tot_p = sum(item["protein_g"] for item in edited_foods)
    tot_c = sum(item["carbs_g"] for item in edited_foods)
    tot_f = sum(item["fat_g"] for item in edited_foods)

    render_html(
        f"""
        <div class="glass-card glass-card-hero" style="margin-top: 1.25rem;">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF2B3A; font-weight: 800;">TOTAL MEAL ESTIMATE</div>
            <div style="text-align: center; font-size: 1.6rem; font-weight: 900; color: #FF2B3A; margin: 0.3rem 0;">{tot_cals:,} kcal</div>
            <div class="macro-cards-grid" style="margin-bottom: 0;">
                <div class="macro-glass-card macro-protein">
                    <div class="macro-card-val" style="color: #FF3B4D;">{tot_p}g</div>
                    <div class="macro-card-sub">Protein</div>
                </div>
                <div class="macro-glass-card macro-carbs">
                    <div class="macro-card-val" style="color: #38BDF8;">{tot_c}g</div>
                    <div class="macro-card-sub">Carbs</div>
                </div>
                <div class="macro-glass-card macro-fat">
                    <div class="macro-card-val" style="color: #FBBF24;">{tot_f}g</div>
                    <div class="macro-card-sub">Fat</div>
                </div>
            </div>
        </div>
        """
    )

    col_confirm, col_discard = st.columns([2, 1])
    with col_confirm:
        if st.button("⚡ Confirm & Log Meal", type="primary", use_container_width=True):
            new_meal = {
                "meal_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.datetime.now().isoformat(),
                "meal_type": st.session_state.scan_meal_type,
                "foods": edited_foods,
                "total": {
                    "calories": tot_cals,
                    "protein_g": tot_p,
                    "carbs_g": tot_c,
                    "fat_g": tot_f,
                },
            }
            meal_storage.add_meal(new_meal)
            st.session_state.scan_analysis = None
            st.session_state.scan_image = None
            st.success("Meal confirmed and saved to today's log!")
            st.session_state.active_tab = "Home"
            st.rerun()

    with col_discard:
        if st.button("Discard Scan", type="secondary", use_container_width=True):
            st.session_state.scan_analysis = None
            st.session_state.scan_image = None
            st.rerun()


def overall_confidence_label(conf: str) -> str:
    if conf == "high":
        return "HIGH CONFIDENCE"
    elif conf == "medium":
        return "MEDIUM CONFIDENCE"
    else:
        return "LOW CONFIDENCE — REVIEW EDITABLE FIELDS"


# ==================================================
# TAB 3: COACH (CONTEXTUAL NUTRITION AI ASSISTANT)
# ==================================================

def render_coach_tab(plan):
    render_html('<div class="section-title" style="font-size: 1.25rem; font-weight: 900; color: #F8FAFC;">🧠 MACROSNAP COACH</div>')
    render_html('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;">Your personalized contextual nutrition assistant</div>')

    today_str = get_today_str()
    consumed = meal_storage.get_daily_totals(today_str)
    rem_cal = plan["target_calories"] - consumed["calories"]
    rem_p = plan["protein_g"] - consumed["protein_g"]

    # Context Summary Card
    render_html(
        f"""
        <div class="glass-card glass-card-hero">
            <div style="font-size: 0.75rem; font-weight: 800; color: #FF2B3A; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">LIVE TODAY CONTEXT</div>
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700;">
                <span>Calories: <strong style="color: #F8FAFC;">{consumed['calories']:,} / {plan['target_calories']:,}</strong> <span style="color: #94A3B8; font-size: 0.75rem;">({rem_cal:,} left)</span></span>
                <span>Protein: <strong style="color: #FF3B4D;">{consumed['protein_g']} / {plan['protein_g']}g</strong> <span style="color: #94A3B8; font-size: 0.75rem;">({rem_p}g left)</span></span>
            </div>
        </div>
        """
    )

    # Quick Action Chips
    render_html("<div style='font-size: 0.78rem; font-weight: 800; color: #94A3B8; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.05em;'>QUICK ACTION CHIPS</div>")

    chip_prompt = None
    chip_c1, chip_c2 = st.columns(2)
    with chip_c1:
        if st.button("🍗 High Protein Meal", key="chip_protein", type="secondary", use_container_width=True):
            chip_prompt = "What is a fast, high-protein meal or snack I can eat right now to help hit my protein goal?"
    with chip_c2:
        if st.button("📊 Am I On Track?", key="chip_track", type="secondary", use_container_width=True):
            chip_prompt = "Based on my consumed calories and macros today vs my target blueprint, am I on track today?"

    chip_c3, chip_c4 = st.columns(2)
    with chip_c3:
        if st.button("🥗 Under 500 Calories", key="chip_under500", type="secondary", use_container_width=True):
            chip_prompt = "Suggest a delicious dinner meal under 500 calories that fits my remaining macro budget."
    with chip_c4:
        if st.button("💡 What Should I Eat?", key="chip_eat", type="secondary", use_container_width=True):
            chip_prompt = "What should I eat for my next meal to balance my remaining calories, protein, carbs, and fat?"

    render_html("<hr style='border-color: rgba(255, 255, 255, 0.1); margin: 1rem 0;'>")

    # Chat Messages Container
    for msg in st.session_state.nutrition_chat:
        if msg["role"] == "user":
            render_html(f'<div class="chat-bubble-user">👤 <strong>You:</strong><br>{msg["content"]}</div>')
        else:
            render_html(f'<div class="chat-bubble-assistant">🧠 <strong>MacroSnap Coach:</strong><br>{msg["content"]}</div>')

    user_input = st.chat_input("Ask Coach a nutrition question...")

    prompt_to_run = user_input or chip_prompt

    if prompt_to_run:
        st.session_state.nutrition_chat.append({"role": "user", "content": prompt_to_run})

        with st.spinner("Coach is thinking..."):
            success, response_text = nutrition_ai.query_nutrition_assistant(
                user_prompt=prompt_to_run,
                user_plan=plan,
                consumed=consumed,
                today_meals=meal_storage.get_meals_for_date(today_str),
                chat_history=st.session_state.nutrition_chat[:-1],
            )

        st.session_state.nutrition_chat.append({"role": "assistant", "content": response_text})
        st.rerun()


# ==================================================
# TAB 4: MEAL HISTORY
# ==================================================

def render_history_tab(plan):
    col_hist_back, _ = st.columns([1.2, 1])
    with col_hist_back:
        if st.button("← Back to Progress", type="secondary"):
            st.session_state.active_tab = "Progress"
            st.rerun()

    render_html('<div class="section-title" style="font-size: 1.25rem; font-weight: 900; color: #F8FAFC;">📅 MEAL HISTORY</div>')
    render_html('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;">Review historical daily logs and nutrition totals</div>')

    all_dates = meal_storage.get_all_dates()
    today_str = get_today_str()

    if today_str not in all_dates:
        all_dates.insert(0, today_str)

    all_dates.sort(reverse=True)

    selected_date_str = st.selectbox(
        "Select Date",
        options=all_dates,
        index=0,
        format_func=lambda d: f"{d} (Today)" if d == today_str else d,
    )

    day_totals = meal_storage.get_daily_totals(selected_date_str)
    day_meals = meal_storage.get_meals_for_date(selected_date_str)
    target_snap = target_storage.get_target_for_date(selected_date_str)
    day_target = target_snap["plan"] if (target_snap and isinstance(target_snap, dict) and "plan" in target_snap) else plan

    # Daily Summary Card
    card_html = f"""
    <div class="glass-card glass-card-hero" style="margin-top: 1rem;">
        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF2B3A; font-weight: 800; margin-bottom: 0.4rem;">DAILY SUMMARY ({selected_date_str})</div>
        <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
            <span style="color: #94A3B8;">Daily Intake Target</span>
            <span style="color: #F8FAFC; font-weight: 700;">{day_target['target_calories']:,} kcal</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; font-size: 0.88rem;">
            <span style="color: #94A3B8;">Total Consumed</span>
            <span style="color: #FF2B3A; font-weight: 900;">{day_totals['calories']:,} kcal</span>
        </div>

        <div class="macro-cards-grid" style="margin-top: 0.85rem; margin-bottom: 0;">
            <div class="macro-glass-card macro-protein">
                <div class="macro-card-val" style="color: #FF3B4D;">{day_totals['protein_g']}g</div>
                <div class="macro-card-sub">Protein</div>
            </div>
            <div class="macro-glass-card macro-carbs">
                <div class="macro-card-val" style="color: #38BDF8;">{day_totals['carbs_g']}g</div>
                <div class="macro-card-sub">Carbs</div>
            </div>
            <div class="macro-glass-card macro-fat">
                <div class="macro-card-val" style="color: #FBBF24;">{day_totals['fat_g']}g</div>
                <div class="macro-card-sub">Fat</div>
            </div>
        </div>
    </div>
    """
    render_html(card_html)

    render_html("<div style='font-size: 0.9rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.75rem;'>Logged Meals on Selected Date</div>")

    if not day_meals:
        st.info("No meals logged on this date.")
    else:
        for meal in day_meals:
            m_type = meal.get("meal_type", "Meal")
            m_icon = "🥣" if m_type == "Breakfast" else ("🍱" if m_type == "Lunch" else ("🥗" if m_type == "Dinner" else "🍎"))
            tot = meal.get("total", {})
            cals = tot.get("calories", 0)

            time_str = ""
            if "timestamp" in meal:
                try:
                    dt = datetime.datetime.fromisoformat(meal["timestamp"])
                    time_str = dt.strftime("%I:%M %p")
                except Exception:
                    time_str = ""

            with st.expander(f"{m_icon} {m_type} • {cals:,} kcal ({time_str if time_str else 'Logged'})", expanded=False):
                st.markdown(f"**Total Macros:** P: {tot.get('protein_g', 0)}g | C: {tot.get('carbs_g', 0)}g | F: {tot.get('fat_g', 0)}g")
                st.markdown("---")
                for food in meal.get("foods", []):
                    st.markdown(
                        f"• **{food.get('name')}** ({food.get('portion', '')}) — {food.get('calories')} kcal "
                        f"_(P: {food.get('protein_g')}g, C: {food.get('carbs_g')}g, F: {food.get('fat_g')}g)_"
                    )


# ==================================================
# TAB 5: PROGRESS & ANALYTICS
# ==================================================

def render_progress_tab(plan):
    render_html('<div class="section-title" style="font-size: 1.25rem; font-weight: 900; color: #F8FAFC;">📊 YOUR PROGRESS</div>')
    render_html('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;">Historical nutrition trends, adherence, and weight tracking</div>')

    if st.button("📜 View Detailed Meal Logs & History ➔", type="secondary", use_container_width=True):
        st.session_state.active_tab = "History"
        st.rerun()

    render_html("<div style='margin-top: 0.4rem;'></div>")

    col_toggle1, col_toggle2 = st.columns(2)
    with col_toggle1:
        if st.button("7 Days", type="primary" if st.session_state.progress_days == 7 else "secondary", use_container_width=True):
            st.session_state.progress_days = 7
            st.rerun()
    with col_toggle2:
        if st.button("30 Days", type="primary" if st.session_state.progress_days == 30 else "secondary", use_container_width=True):
            st.session_state.progress_days = 30
            st.rerun()

    days = st.session_state.progress_days
    summary = analytics.get_period_summary(
        days=days,
        target_calories=plan["target_calories"],
        target_protein=plan["protein_g"],
        target_carbs=plan["carbs_g"],
        target_fat=plan["fat_g"],
        goal=plan["goal"],
        tdee=int(plan["tdee"]),
    )

    averages = summary.get("averages", {})
    cal_adh = summary.get("cal_adherence", {})
    p_adh = summary.get("p_adherence", {})
    daily_history = summary.get("history", [])

    tracked_count = averages.get("tracked_days", 0)

    if tracked_count == 0:
        empty_progress = """
        <div class="glass-card" style="text-align: center; padding: 2rem 1.25rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.3rem;">No Tracked Data Yet</div>
            <div style="font-size: 0.82rem; color: #94A3B8;">Log your first meal to start generating period trend analytics.</div>
        </div>
        """
        render_html(empty_progress)
        render_html("<br>")
        render_weight_tracking_section()
        return

    # Period Summary Card
    summary_card = f"""
    <div class="glass-card glass-card-hero">
        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF2B3A; font-weight: 800; margin-bottom: 0.4rem;">LAST {days} DAYS SUMMARY</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <span style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">Tracked Adherence</span>
            <span style="font-size: 1.25rem; font-weight: 900; color: #FF2B3A;">{tracked_count} / {days} Days Logged</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
            <span style="color: #94A3B8;">Avg Daily Calories</span>
            <span style="color: #F8FAFC; font-weight: 700;">{averages.get('avg_calories', 0):,} kcal / day</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
            <span style="color: #94A3B8;">Avg Daily Protein</span>
            <span style="color: #F8FAFC; font-weight: 700;">{averages.get('avg_protein', 0)}g / day</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
            <span style="color: #94A3B8;">Avg Daily Carbs</span>
            <span style="color: #F8FAFC; font-weight: 700;">{averages.get('avg_carbs', 0)}g / day</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; font-size: 0.88rem;">
            <span style="color: #94A3B8;">Avg Daily Fat</span>
            <span style="color: #F8FAFC; font-weight: 700;">{averages.get('avg_fat', 0)}g / day</span>
        </div>
    </div>
    """
    render_html(summary_card)

    on_target_cal = cal_adh.get("on_target_count", 0)
    reached_p = p_adh.get("reached_count", 0)
    consistency_pct = summary.get("consistency_pct", 0)
    interpretation = summary.get("interpretation", "")

    adherence_box = f"""
    <div class="glass-card" style="border-left: 3px solid #FF2B3A; font-size: 0.84rem; color: #F8FAFC; margin-bottom: 1.25rem;">
        🎯 <strong>Target Adherence Score ({consistency_pct}% Consistency):</strong> Logged <strong>{tracked_count} days</strong> with <strong>{on_target_cal} days</strong> inside target calorie range & <strong>{reached_p} days</strong> hitting protein target.<br>
        <div style="margin-top: 0.4rem; color: #94A3B8; font-size: 0.78rem;">💡 <em>{interpretation}</em></div>
    </div>
    """
    render_html(adherence_box)

    # Trend Chart Simulation
    render_html("<div style='font-size: 0.9rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.5rem;'>Daily Calorie Intake vs Target</div>")

    for entry in daily_history[-7:]:
        c_val = entry.get("calories", 0)
        t_val = entry.get("target_calories", plan["target_calories"])
        is_tracked = entry.get("tracked", False)
        pct = min(100, int((c_val / t_val) * 100)) if (t_val > 0 and is_tracked) else 0
        b_color = "#FF2B3A" if is_tracked else "#334155"
        date_lbl = entry.get("date_formatted", entry.get("date", ""))

        bar_html = f"""
        <div style="margin-bottom: 0.65rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #CBD5E1; margin-bottom: 0.15rem;">
                <span style="font-weight: 600;">{date_lbl}</span>
                <span style="font-weight: 700;">{c_val:,} / {t_val:,} kcal {' (No data)' if not is_tracked else ''}</span>
            </div>
            <div class="trend-bar-bg">
                <div style="background-color: {b_color}; height: 100%; width: {pct}%; border-radius: 8px;"></div>
            </div>
        </div>
        """
        render_html(bar_html)

    render_html("<br>")
    render_weight_tracking_section()


def render_weight_tracking_section():
    render_html("<div style='font-size: 0.9rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.5rem;'>⚖️ Body Weight Tracker</div>")

    w_history = weight_storage.load_weight_history()
    latest_entry = weight_storage.get_latest_weight()
    w_change = weight_storage.get_weight_change()

    latest_str = f"{latest_entry['weight_kg']} kg" if latest_entry else "None"
    has_prev = w_change.get("previous") is not None
    change_str = f"{w_change['change_kg']:+.1f} kg" if has_prev else "N/A"

    weight_card = f"""
    <div class="glass-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 700; text-transform: uppercase;">Latest Weight</div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #F8FAFC;">{latest_str}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 700; text-transform: uppercase;">30-Day Change</div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #FF2B3A;">{change_str}</div>
            </div>
        </div>
    </div>
    """
    render_html(weight_card)

    with st.form("add_weight_form", clear_on_submit=True):
        col_w_val, col_w_sub = st.columns([2, 1])
        with col_w_val:
            new_w = st.number_input("Log New Weight (kg)", min_value=30.0, max_value=300.0, value=75.0, step=0.1)
        with col_w_sub:
            render_html("<div style='margin-top: 1.7rem;'></div>")
            w_submitted = st.form_submit_button("⚡ Log Weight", type="primary")

        if w_submitted:
            weight_storage.add_weight_entry(weight_kg=float(new_w), date_str=get_today_str())
            st.success("Weight entry recorded!")
            st.rerun()

    if w_history:
        with st.expander("Show Logged Weight History", expanded=False):
            for entry in w_history[:10]:
                e_id = entry.get("id")
                col_w_txt, col_w_del = st.columns([3, 1])
                with col_w_txt:
                    st.markdown(f"• **{entry['weight_kg']} kg** on {entry['date']}")
                with col_w_del:
                    if st.button("🗑️", key=f"wdel_{e_id}"):
                        weight_storage.delete_weight_entry(e_id)
                        st.rerun()


# ==================================================
# TAB 6: SMART PROFILE & RECALCULATION
# ==================================================

def render_profile_tab(plan):
    render_html('<div class="section-title" style="font-size: 1.25rem; font-weight: 900; color: #F8FAFC;">👤 SMART PROFILE</div>')
    render_html('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;">Your active metrics, dynamic target recalculation & plan history</div>')

    data = st.session_state.onboarding_data
    latest_w_entry = weight_storage.get_latest_weight()
    latest_w_val = latest_w_entry["weight_kg"] if latest_w_entry else None

    # Discrepancy notice
    if latest_w_val is not None and abs(latest_w_val - data.get("weight_kg", 0)) >= 0.1:
        render_html(
            f"""
            <div class="glass-card" style="border-left: 3px solid #F59E0B; background: rgba(245, 158, 11, 0.1); font-size: 0.82rem; color: #CBD5E1;">
                ⚠️ <strong>Weight Discrepancy Notice:</strong><br>
                Your latest logged weight (<strong>{latest_w_val} kg</strong>) is different from your current profile weight (<strong>{data.get('weight_kg')} kg</strong>).
            </div>
            """
        )
        if st.button(f"⚡ Update Profile Weight to {latest_w_val} kg", type="secondary", use_container_width=True):
            st.session_state.onboarding_data["weight_kg"] = float(latest_w_val)
            new_plan = calculate_full_plan(
                age=data["age"],
                sex=data["sex"],
                height_cm=data["height_cm"],
                weight_kg=float(latest_w_val),
                activity_level=data["activity_level"],
                goal=data["goal"],
                intensity=data["intensity"],
            )
            st.session_state.pending_plan_preview = new_plan
            st.rerun()

    # Active Plan Summary Card
    render_html(
        f"""
        <div class="glass-card glass-card-hero">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF2B3A; font-weight: 800; margin-bottom: 0.4rem;">CURRENT ACTIVE PLAN</div>
            <div style="text-align: center; font-size: 1.3rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.85rem;">{plan['goal_emoji']} {plan['goal']} ({plan['intensity']})</div>

            <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                <span style="color: #94A3B8;">Age / Sex</span>
                <span style="color: #F8FAFC; font-weight: 700;">{plan['age']} yrs • {plan['sex']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                <span style="color: #94A3B8;">Height / Profile Weight</span>
                <span style="color: #F8FAFC; font-weight: 700;">{plan['height_cm']} cm • {plan['weight_kg']} kg</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                <span style="color: #94A3B8;">Activity Level</span>
                <span style="color: #F8FAFC; font-weight: 700;">{plan['activity_level']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                <span style="color: #94A3B8;">BMR (Mifflin-St Jeor)</span>
                <span style="color: #F8FAFC; font-weight: 700;">{plan['bmr']} kcal</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                <span style="color: #94A3B8;">Maintenance (TDEE)</span>
                <span style="color: #F8FAFC; font-weight: 700;">{plan['tdee']} kcal</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; padding-top: 0.75rem; border-top: 1px solid rgba(255, 43, 58, 0.3);">
                <span style="font-weight: 700; color: #F8FAFC;">Daily Calorie Target</span>
                <span style="font-size: 1.35rem; color: #FF2B3A; font-weight: 900;">{plan['target_calories']:,} kcal</span>
            </div>

            <div class="macro-cards-grid" style="margin-top: 0.85rem; margin-bottom: 0;">
                <div class="macro-glass-card macro-protein">
                    <div class="macro-card-val" style="color: #FF3B4D;">{plan['protein_g']}g</div>
                    <div class="macro-card-sub">Protein</div>
                </div>
                <div class="macro-glass-card macro-carbs">
                    <div class="macro-card-val" style="color: #38BDF8;">{plan['carbs_g']}g</div>
                    <div class="macro-card-sub">Carbs</div>
                </div>
                <div class="macro-glass-card macro-fat">
                    <div class="macro-card-val" style="color: #FBBF24;">{plan['fat_g']}g</div>
                    <div class="macro-card-sub">Fat</div>
                </div>
            </div>
        </div>
        """
    )

    # 1. PENDING PLAN PREVIEW CONFIRMATION CARD (IF RECALCULATED)
    if st.session_state.pending_plan_preview:
        p_prev = st.session_state.pending_plan_preview
        render_html("<hr style='border-color: #FF2B3A; margin: 1.5rem 0;'>")
        render_html('<div class="section-title" style="font-size: 1.2rem; font-weight: 900; color: #F8FAFC;">YOUR UPDATED PLAN</div>')
        render_html('<div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 1rem;">Review calculated targets before applying</div>')

        render_html(
            f"""
            <div class="glass-card" style="border-color: #FF2B3A;">
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF2B3A; font-weight: 800; margin-bottom: 0.4rem;">RECALCULATED BLUEPRINT</div>
                <div style="text-align: center; font-size: 1.3rem; font-weight: 800; color: #F8FAFC; margin-bottom: 0.85rem;">{p_prev['goal_emoji']} {p_prev['goal']} ({p_prev['intensity']})</div>

                <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                    <span style="color: #94A3B8;">BMR</span>
                    <span style="color: #F8FAFC; font-weight: 700;">{p_prev['bmr']} kcal</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); font-size: 0.88rem;">
                    <span style="color: #94A3B8;">TDEE (Maintenance)</span>
                    <span style="color: #F8FAFC; font-weight: 700;">{p_prev['tdee']} kcal</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; padding-top: 0.75rem; border-top: 1px solid rgba(255, 43, 58, 0.3);">
                    <span style="font-weight: 700; color: #F8FAFC;">New Calorie Target</span>
                    <span style="font-size: 1.35rem; color: #FF2B3A; font-weight: 900;">{p_prev['target_calories']:,} kcal</span>
                </div>

                <div class="macro-cards-grid" style="margin-top: 0.85rem; margin-bottom: 0;">
                    <div class="macro-glass-card macro-protein">
                        <div class="macro-card-val" style="color: #FF3B4D;">{p_prev['protein_g']}g</div>
                        <div class="macro-card-sub">Protein</div>
                    </div>
                    <div class="macro-glass-card macro-carbs">
                        <div class="macro-card-val" style="color: #38BDF8;">{p_prev['carbs_g']}g</div>
                        <div class="macro-card-sub">Carbs</div>
                    </div>
                    <div class="macro-glass-card macro-fat">
                        <div class="macro-card-val" style="color: #FBBF24;">{p_prev['fat_g']}g</div>
                        <div class="macro-card-sub">Fat</div>
                    </div>
                </div>
            </div>
            """
        )

        col_acc, col_rej = st.columns(2)
        with col_acc:
            if st.button("⚡ Apply New Blueprint", type="primary", use_container_width=True):
                st.session_state.user_plan = p_prev
                profile_storage.save_profile(st.session_state.onboarding_data)
                target_storage.create_target_snapshot(p_prev, effective_date=get_today_str())
                st.session_state.pending_plan_preview = None
                st.success("New blueprint applied successfully!")
                st.rerun()
        with col_rej:
            if st.button("Discard Changes", type="secondary", use_container_width=True):
                st.session_state.pending_plan_preview = None
                st.rerun()

    # 2. EDITABLE PROFILE METRICS FORM
    with st.expander("✏️ Edit Profile Parameters & Recalculate Blueprint", expanded=False):
        with st.form("edit_profile_parameters_form"):
            col_p_age, col_p_sex = st.columns(2)
            with col_p_age:
                e_age = st.number_input("Age", min_value=14, max_value=100, value=int(data.get("age", 25)))
            with col_p_sex:
                e_sex = st.radio("Sex", options=["Male", "Female"], index=0 if data.get("sex") == "Male" else 1, horizontal=True)

            col_p_h, col_p_w = st.columns(2)
            with col_p_h:
                e_height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=float(data.get("height_cm", 178.0)), step=0.5)
            with col_p_w:
                e_weight = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=float(data.get("weight_kg", 75.0)), step=0.5)

            act_keys = list(ACTIVITY_MULTIPLIERS.keys())
            e_act = st.selectbox("Activity Level", options=act_keys, index=act_keys.index(data.get("activity_level", "Moderately Active")))

            goal_keys = list(GOAL_CONFIG.keys())
            e_goal = st.selectbox("Fitness Goal", options=goal_keys, index=goal_keys.index(data.get("goal", "Fat Loss")))

            intensities = list(GOAL_CONFIG.get(e_goal, {}).get("intensities", {}).keys())
            if not intensities:
                intensities = ["Moderate"]
            e_int = st.selectbox("Goal Intensity", options=intensities, index=0)

            e_submitted = st.form_submit_button("⚡ Preview Recalculated Blueprint", type="primary")

            if e_submitted:
                st.session_state.onboarding_data = {
                    "age": int(e_age),
                    "sex": e_sex,
                    "height_cm": float(e_height),
                    "weight_kg": float(e_weight),
                    "activity_level": e_act,
                    "goal": e_goal,
                    "intensity": e_int,
                }
                new_plan = calculate_full_plan(
                    age=int(e_age),
                    sex=e_sex,
                    height_cm=float(e_height),
                    weight_kg=float(e_weight),
                    activity_level=e_act,
                    goal=e_goal,
                    intensity=e_int,
                )
                st.session_state.pending_plan_preview = new_plan
                st.rerun()

    # Target Snapshots History
    snapshots = target_storage.load_target_snapshots()
    if snapshots:
        with st.expander("📜 Target Blueprint History", expanded=False):
            for snap in reversed(snapshots):
                p_snap = snap.get("plan", {})
                render_html(
                    f"""
                    <div class="glass-card" style="padding: 0.75rem 0.9rem; margin-bottom: 0.5rem;">
                        <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">Effective Date: {snap.get('effective_date')}</div>
                        <div style="font-size: 0.95rem; font-weight: 800; color: #F8FAFC;">{p_snap.get('goal_emoji', '')} {p_snap.get('goal', '')} ({p_snap.get('target_calories', 0):,} kcal)</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">Macros: P: {p_snap.get('protein_g', 0)}g | C: {p_snap.get('carbs_g', 0)}g | F: {p_snap.get('fat_g', 0)}g</div>
                    </div>
                    """
                )

    render_html("<br>")
    if st.button("🔄 Reset Setup & Re-do Onboarding", type="secondary", use_container_width=True):
        st.session_state.onboarding_complete = False
        st.session_state.step = 1
        st.rerun()


# ==================================================
# MAIN ENTRYPOINT ROUTER
# ==================================================

def main():
    if not st.session_state.onboarding_complete:
        step = st.session_state.step
        render_header()
        if step == 1:
            render_screen_1_basic_info()
        elif step == 2:
            render_screen_2_activity_level()
        elif step == 3:
            render_screen_3_fitness_goal()
        elif step == 4:
            render_screen_4_goal_intensity()
        elif step == 5:
            render_screen_5_plan_confirmation()
    else:
        render_main_app(st.session_state.user_plan)


if __name__ == "__main__":
    main()
