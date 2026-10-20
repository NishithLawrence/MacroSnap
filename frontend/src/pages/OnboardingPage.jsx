import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Activity,
  Target,
  ArrowRight,
  AlertCircle,
  Sparkles,
  Check,
  RefreshCw
} from 'lucide-react';
import { useProfile } from '../context/ProfileContext';
import { previewProfilePlan } from '../lib/api';

const DEFAULT_GOAL_CONFIG = {
  'Fat Loss': {
    emoji: '🔥',
    description: 'Reduce body fat with a controlled calorie deficit.',
    protein_per_kg: 1.8,
    intensities: ['Slow', 'Moderate', 'Aggressive'],
    intensity_labels: {
      Slow: '10% deficit (Slow)',
      Moderate: '15% deficit (Moderate)',
      Aggressive: '20% deficit (Aggressive)'
    }
  },
  'Body Recomposition': {
    emoji: '⚖️',
    description: 'Reduce body fat while building/maintaining muscle.',
    protein_per_kg: 2.0,
    intensities: ['Small deficit', 'Around maintenance'],
    intensity_labels: {
      'Small deficit': '5% deficit',
      'Around maintenance': '0% deficit'
    }
  },
  'Lean Bulk': {
    emoji: '💪',
    description: 'Build muscle with controlled weight gain.',
    protein_per_kg: 1.8,
    intensities: ['Conservative surplus', 'Moderate surplus'],
    intensity_labels: {
      'Conservative surplus': '5% surplus',
      'Moderate surplus': '10% surplus'
    }
  },
  'Maintenance': {
    emoji: '⚖️',
    description: 'Maintain current body weight and metabolic equilibrium.',
    protein_per_kg: 1.6,
    intensities: ['Maintenance'],
    intensity_labels: {
      Maintenance: '0% adjustment'
    }
  }
};

const ACTIVITY_OPTIONS = [
  { level: 'Sedentary', title: 'Sedentary', desc: 'Desk job, little to no exercise (1.2x)' },
  { level: 'Lightly Active', title: 'Lightly Active', desc: '1–3 workouts / light movement (1.375x)' },
  { level: 'Moderately Active', title: 'Moderately Active', desc: '3–5 moderate workouts / week (1.55x)' },
  { level: 'Very Active', title: 'Very Active', desc: '6–7 hard workouts / active lifestyle (1.725x)' },
  { level: 'Extremely Active', title: 'Extremely Active', desc: 'Daily intense training / physical job (1.9x)' }
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { hasProfile, options, loading, connectionError, refreshProfile, saveAndApplyPlan } = useProfile();

  // If user already has a profile, redirect to home
  useEffect(() => {
    if (hasProfile) {
      navigate('/home', { replace: true });
    }
  }, [hasProfile, navigate]);

  const [form, setForm] = useState({
    name: '',
    age: '25',
    sex: 'Male',
    height_cm: '178',
    weight_kg: '75',
    activity_level: 'Moderately Active',
    goal: 'Fat Loss',
    intensity: 'Moderate'
  });

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Live Plan Preview state
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Active goal options derived from backend or fallback
  const goalConfig = useMemo(() => {
    if (options && options.goals) {
      return options.goals;
    }
    return DEFAULT_GOAL_CONFIG;
  }, [options]);

  // Handle goal change (reset intensity to valid default)
  const handleGoalChange = (newGoal) => {
    const availableIntensities = goalConfig[newGoal]?.intensities || ['Moderate'];
    setForm((prev) => ({
      ...prev,
      goal: newGoal,
      intensity: availableIntensities[0] || 'Moderate'
    }));
  };

  // Validate form fields (Adult user scope: 18-120, height 100-250cm, weight 30-350kg)
  const validateForm = () => {
    const newErrors = {};
    const ageNum = parseInt(form.age, 10);
    const heightNum = parseFloat(form.height_cm);
    const weightNum = parseFloat(form.weight_kg);

    if (form.name && form.name.length > 100) {
      newErrors.name = 'Name must be 100 characters or fewer.';
    }

    if (!form.age || isNaN(ageNum) || ageNum < 18 || ageNum > 120) {
      newErrors.age = 'Age must be between 18 and 120 (MacroSnap is designed for adults).';
    }

    if (!form.sex || !['Male', 'Female'].includes(form.sex)) {
      newErrors.sex = 'Please select your biological sex for BMR calculation.';
    }

    if (!form.height_cm || isNaN(heightNum) || heightNum < 100 || heightNum > 250) {
      newErrors.height_cm = 'Please enter a valid height between 100 and 250 cm.';
    }

    if (!form.weight_kg || isNaN(weightNum) || weightNum < 30 || weightNum > 350) {
      newErrors.weight_kg = 'Please enter a valid weight between 30 and 350 kg.';
    }

    if (!form.activity_level) {
      newErrors.activity_level = 'Please select your activity level.';
    }

    if (!form.goal) {
      newErrors.goal = 'Please select your primary fitness goal.';
    }

    if (!form.intensity) {
      newErrors.intensity = 'Please select a goal intensity.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Fetch plan preview when valid inputs change
  useEffect(() => {
    let isCancelled = false;
    const ageNum = parseInt(form.age, 10);
    const heightNum = parseFloat(form.height_cm);
    const weightNum = parseFloat(form.weight_kg);

    if (ageNum >= 18 && ageNum <= 120 && heightNum >= 100 && heightNum <= 250 && weightNum >= 30 && weightNum <= 350 && form.goal && form.intensity) {
      const payload = {
        name: form.name.trim(),
        age: ageNum,
        sex: form.sex,
        height_cm: heightNum,
        weight_kg: weightNum,
        activity_level: form.activity_level,
        goal: form.goal,
        intensity: form.intensity
      };

      setPreviewLoading(true);
      previewProfilePlan(payload)
        .then((res) => {
          if (!isCancelled && res?.proposed_plan) {
            setPreview(res.proposed_plan);
          }
        })
        .catch(() => {
          // Silent fallback on calculation preview
        })
        .finally(() => {
          if (!isCancelled) setPreviewLoading(false);
        });
    }

    return () => {
      isCancelled = true;
    };
  }, [form.age, form.sex, form.height_cm, form.weight_kg, form.activity_level, form.goal, form.intensity, form.name]);

  // Form submit handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: form.name.trim(),
        age: parseInt(form.age, 10),
        sex: form.sex,
        height_cm: parseFloat(form.height_cm),
        weight_kg: parseFloat(form.weight_kg),
        activity_level: form.activity_level,
        goal: form.goal,
        intensity: form.intensity
      };

      await saveAndApplyPlan(payload);
      // Navigate directly to dashboard with personalized profile initialized
      navigate('/home', { replace: true });
    } catch (err) {
      console.error('Failed to save profile during onboarding:', err);
      setSubmitError(err.message || 'Failed to save profile. Please check your connection and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 py-2 min-w-0 pb-16">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#EF233C] to-[#9D0208] flex items-center justify-center text-white font-black text-xl mx-auto shadow-xl shadow-[#EF233C]/20">
          MS
        </div>
        <h1 className="text-2xl font-black text-white tracking-tight">
          Welcome to Macro<span className="text-[#EF233C]">Snap</span>
        </h1>
        <p className="text-xs text-zinc-400 max-w-xs mx-auto">
          Precision nutrition calculation powered by scientific equations and AI vision.
          Let's configure your personalized profile.
        </p>
      </div>

      {connectionError && (
        <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0 text-[#EF233C]" />
            <span>{connectionError}. Live nutrition calculations and options cannot be verified.</span>
          </div>
          <button
            type="button"
            onClick={refreshProfile}
            className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white rounded-lg text-[11px] font-bold flex items-center gap-1 shrink-0"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {submitError && (
        <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0 text-[#EF233C]" />
          <span>{submitError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* SECTION 1: PERSONAL BIOMETRICS */}
        <div className="app-card p-4 sm:p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-2.5">
            <User size={16} className="text-[#EF233C]" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              1. Biometrics & Personal Info
            </h2>
          </div>

          <div className="space-y-3.5">
            {/* Name (Optional) */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-zinc-300">Name</label>
                <span className="text-[10px] text-zinc-500 uppercase">Optional</span>
              </div>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Alex"
                className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-[#EF233C] transition-colors"
              />
              {errors.name && <p className="text-[11px] text-red-400 mt-1">{errors.name}</p>}
            </div>

            {/* Sex Toggle */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1">Biological Sex</label>
              <div className="grid grid-cols-2 gap-2">
                {['Male', 'Female'].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setForm({ ...form, sex: s })}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all ${
                      form.sex === s
                        ? 'bg-[#EF233C] border-[#EF233C] text-white shadow-md shadow-[#EF233C]/20'
                        : 'bg-zinc-900 border-white/10 text-zinc-400 hover:text-white'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
              {errors.sex && <p className="text-[11px] text-red-400 mt-1">{errors.sex}</p>}
            </div>

            {/* Age, Height, Weight Grid */}
            <div className="grid grid-cols-3 gap-2.5">
              <div>
                <label className="text-xs font-medium text-zinc-300 block mb-1">Age (18+)</label>
                <div className="relative">
                  <input
                    type="number"
                    value={form.age}
                    onChange={(e) => setForm({ ...form, age: e.target.value })}
                    className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-[#EF233C] transition-colors"
                  />
                  <span className="absolute right-2.5 top-2.5 text-[10px] text-zinc-500">yrs</span>
                </div>
                {errors.age && <p className="text-[10px] text-red-400 mt-1">{errors.age}</p>}
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-300 block mb-1">Height</label>
                <div className="relative">
                  <input
                    type="number"
                    value={form.height_cm}
                    onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
                    className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-[#EF233C] transition-colors"
                  />
                  <span className="absolute right-2.5 top-2.5 text-[10px] text-zinc-500">cm</span>
                </div>
                {errors.height_cm && <p className="text-[10px] text-red-400 mt-1">{errors.height_cm}</p>}
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-300 block mb-1">Weight</label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.1"
                    value={form.weight_kg}
                    onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
                    className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-[#EF233C] transition-colors"
                  />
                  <span className="absolute right-2.5 top-2.5 text-[10px] text-zinc-500">kg</span>
                </div>
                {errors.weight_kg && <p className="text-[10px] text-red-400 mt-1">{errors.weight_kg}</p>}
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 2: ACTIVITY LEVEL */}
        <div className="app-card p-4 sm:p-5 space-y-3.5">
          <div className="flex items-center gap-2 border-b border-white/5 pb-2.5">
            <Activity size={16} className="text-[#EF233C]" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              2. Activity Level
            </h2>
          </div>

          <div className="space-y-2">
            {ACTIVITY_OPTIONS.map((act) => {
              const isSelected = form.activity_level === act.level;
              return (
                <div
                  key={act.level}
                  onClick={() => setForm({ ...form, activity_level: act.level })}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#EF233C]/10 border-[#EF233C] shadow-sm shadow-[#EF233C]/10'
                      : 'bg-zinc-900/60 border-white/5 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-zinc-300'}`}>
                      {act.title}
                    </span>
                    {isSelected && <Check size={14} className="text-[#EF233C]" />}
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-0.5">{act.desc}</p>
                </div>
              );
            })}
          </div>
          {errors.activity_level && <p className="text-[11px] text-red-400">{errors.activity_level}</p>}
        </div>

        {/* SECTION 3: FITNESS GOAL & INTENSITY */}
        <div className="app-card p-4 sm:p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-2.5">
            <Target size={16} className="text-[#EF233C]" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              3. Fitness Goal & Target Rate
            </h2>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {Object.entries(goalConfig).map(([goalName, cfg]) => {
              const isSelected = form.goal === goalName;
              return (
                <button
                  key={goalName}
                  type="button"
                  onClick={() => handleGoalChange(goalName)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    isSelected
                      ? 'bg-[#EF233C]/15 border-[#EF233C] text-white shadow-sm shadow-[#EF233C]/10'
                      : 'bg-zinc-900/60 border-white/5 text-zinc-400 hover:text-white'
                  }`}
                >
                  <div className="text-base mb-1">{cfg.emoji || '🎯'}</div>
                  <div className="text-xs font-bold text-white">{goalName}</div>
                  <div className="text-[10px] text-zinc-400 line-clamp-2 mt-0.5">
                    {cfg.description}
                  </div>
                </button>
              );
            })}
          </div>
          {errors.goal && <p className="text-[11px] text-red-400">{errors.goal}</p>}

          {/* Intensity Selection */}
          <div className="pt-2 border-t border-white/5">
            <label className="text-xs font-medium text-zinc-300 block mb-2">
              Deficit / Surplus Intensity
            </label>
            <div className="grid grid-cols-1 gap-2">
              {(goalConfig[form.goal]?.intensities || ['Moderate']).map((intensityName) => {
                const isSelected = form.intensity === intensityName;
                const label =
                  goalConfig[form.goal]?.intensity_details?.[intensityName]?.label ||
                  goalConfig[form.goal]?.intensity_labels?.[intensityName] ||
                  DEFAULT_GOAL_CONFIG[form.goal]?.intensity_labels?.[intensityName] ||
                  intensityName;
                return (
                  <button
                    key={intensityName}
                    type="button"
                    onClick={() => setForm({ ...form, intensity: intensityName })}
                    className={`py-2.5 px-3 rounded-xl border text-xs text-left flex items-center justify-between transition-all ${
                      isSelected
                        ? 'bg-zinc-800 border-[#EF233C] text-white'
                        : 'bg-zinc-900/60 border-white/5 text-zinc-400 hover:text-white'
                    }`}
                  >
                    <span>{label}</span>
                    {isSelected && <Check size={14} className="text-[#EF233C]" />}
                  </button>
                );
              })}
            </div>
            {errors.intensity && <p className="text-[11px] text-red-400 mt-1">{errors.intensity}</p>}
          </div>
        </div>

        {/* SECTION 4: LIVE SCIENTIFIC TARGET PREVIEW */}
        {preview && (
          <div className="bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-950 p-4 sm:p-5 rounded-2xl border border-[#EF233C]/30 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-[#EF233C]" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Target Plan Calculation
                </span>
                {previewLoading && <RefreshCw size={12} className="animate-spin text-zinc-400" />}
              </div>
              <span className="text-[10px] text-zinc-400 font-mono">Mifflin-St Jeor</span>
            </div>

            <div className="flex items-baseline justify-between pt-1">
              <div>
                <span className="text-[11px] text-zinc-400 block">Daily Calorie Target</span>
                <span className="text-2xl font-black text-white tracking-tight">
                  {preview.target_calories?.toLocaleString()} <span className="text-sm font-bold text-[#EF233C]">kcal</span>
                </span>
              </div>
              <div className="text-right text-[11px] text-zinc-400">
                <div>BMR: <span className="font-semibold text-zinc-200">{Math.round(preview.bmr || 0)}</span> kcal</div>
                <div>TDEE: <span className="font-semibold text-zinc-200">{Math.round(preview.tdee || 0)}</span> kcal</div>
                {preview.bmi && (
                  <div className="text-[10px] text-zinc-400">BMI: <span className="font-semibold text-zinc-200">{preview.bmi}</span> ({preview.bmi_category})</div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-center">
              <div className="bg-zinc-900/80 p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-zinc-400 block">Protein</span>
                <span className="text-xs font-bold text-white">{preview.protein_g}g</span>
              </div>
              <div className="bg-zinc-900/80 p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-zinc-400 block">Carbs</span>
                <span className="text-xs font-bold text-white">{preview.carbs_g}g</span>
              </div>
              <div className="bg-zinc-900/80 p-2 rounded-xl border border-white/5">
                <span className="text-[10px] text-zinc-400 block">Fat</span>
                <span className="text-xs font-bold text-white">{preview.fat_g}g</span>
              </div>
            </div>

            {/* HEALTH / CLINICAL ADVISORIES */}
            {preview.health_advisories && preview.health_advisories.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-white/10 text-left">
                {preview.health_advisories.map((adv, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                      adv.severity === 'critical'
                        ? 'bg-red-500/10 border-red-500/30 text-red-300'
                        : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    }`}
                  >
                    <AlertCircle size={16} className={`shrink-0 mt-0.5 ${adv.severity === 'critical' ? 'text-red-400' : 'text-amber-400'}`} />
                    <div className="space-y-0.5">
                      <span className="font-bold uppercase tracking-wider text-[10px]">
                        {adv.severity === 'critical' ? 'Clinical Advisory' : 'Health Advisory'}
                      </span>
                      <p className="text-[11px] leading-relaxed text-zinc-300">{adv.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SUBMIT BUTTON */}
        <button
          type="submit"
          disabled={submitting || Boolean(connectionError)}
          className="w-full py-4 px-4 rounded-xl bg-[#EF233C] hover:bg-[#D90429] disabled:opacity-50 text-white text-xs font-extrabold flex items-center justify-center gap-2 shadow-xl shadow-[#EF233C]/25 transition-all active:scale-[0.98]"
        >
          {submitting ? (
            <>
              <RefreshCw size={16} className="animate-spin" />
              <span>Calculating & Saving Plan...</span>
            </>
          ) : connectionError ? (
            <>
              <AlertCircle size={16} />
              <span>Backend Disconnected — Reconnecting...</span>
            </>
          ) : (
            <>
              <span>Activate My Nutrition Plan</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
