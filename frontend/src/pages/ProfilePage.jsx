import React, { useState, useEffect } from 'react';
import {
  User,
  Target,
  Scale,
  Flame,
  Activity,
  Sparkles,
  Check,
  Edit3,
  X,
  Info,
  ShieldAlert,
  RefreshCw,
  Sliders,
  ArrowRight,
  TrendingUp,
  Dumbbell,
  CheckCircle2,
  Calendar
} from 'lucide-react';
import { getProfile, previewProfilePlan, applyProfilePlan, logWeight } from '../lib/api';

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Active profile & plan from backend
  const [profile, setProfile] = useState(null);
  const [activePlan, setActivePlan] = useState(null);
  const [options, setOptions] = useState(null);

  // Edit Mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    age: 25,
    sex: 'Male',
    height_cm: 178,
    weight_kg: 75,
    activity_level: 'Moderately Active',
    goal: 'Fat Loss',
    intensity: 'Moderate'
  });

  // Preview state
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Weight Log Modal state
  const [isWeightModalOpen, setIsWeightModalOpen] = useState(false);
  const [logWeightVal, setLogWeightVal] = useState('');
  const [logWeightDate, setLogWeightDate] = useState(new Date().toISOString().split('T')[0]);
  const [weightSubmitting, setWeightSubmitting] = useState(false);

  // Fetch initial profile & active plan from backend
  const fetchProfileData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProfile();
      setProfile(res.profile);
      setActivePlan(res.active_plan);
      setOptions(res.options);

      // Pre-fill edit form
      if (res.profile) {
        setEditForm({
          name: res.profile.name || '',
          age: res.profile.age || 25,
          sex: res.profile.sex || 'Male',
          height_cm: res.profile.height_cm || 178,
          weight_kg: res.profile.weight_kg || 75,
          activity_level: res.profile.activity_level || 'Moderately Active',
          goal: res.profile.goal || 'Fat Loss',
          intensity: res.profile.intensity || 'Moderate'
        });
        setLogWeightVal(res.profile.weight_kg || '');
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
      setError(err.message || 'Failed to load user profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileData();
  }, []);

  // Handle goal change in edit form (auto-update intensities)
  const handleGoalChange = (newGoal) => {
    let availableIntensities = [];
    if (options && options.goals && options.goals[newGoal]) {
      availableIntensities = options.goals[newGoal].intensities || [];
    } else {
      // Fallbacks matching backend GOAL_CONFIG
      const fallbacks = {
        'Fat Loss': ['Slow', 'Moderate', 'Aggressive'],
        'Body Recomposition': ['Small deficit', 'Around maintenance'],
        'Lean Bulk': ['Conservative surplus', 'Moderate surplus'],
        'Maintenance': ['Maintenance']
      };
      availableIntensities = fallbacks[newGoal] || ['Moderate'];
    }

    const currentIntensityValid = availableIntensities.includes(editForm.intensity);
    const newIntensity = currentIntensityValid ? editForm.intensity : (availableIntensities[0] || 'Moderate');

    setEditForm((prev) => ({
      ...prev,
      goal: newGoal,
      intensity: newIntensity
    }));
  };

  // Trigger Plan Preview
  const handleCalculatePreview = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const numForm = {
        name: editForm.name ? editForm.name.trim() : '',
        age: parseInt(editForm.age, 10),
        sex: editForm.sex,
        height_cm: parseFloat(editForm.height_cm),
        weight_kg: parseFloat(editForm.weight_kg),
        activity_level: editForm.activity_level,
        goal: editForm.goal,
        intensity: editForm.intensity
      };

      const res = await previewProfilePlan(numForm);
      setPreviewData(res);
      setIsPreviewing(true);
    } catch (err) {
      console.error('Error calculating plan preview:', err);
      setError(err.message || 'Failed to calculate plan preview.');
    } finally {
      setSubmitting(false);
    }
  };

  // Confirm and Apply New Plan
  const handleApplyPlan = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const numForm = {
        name: editForm.name ? editForm.name.trim() : '',
        age: parseInt(editForm.age, 10),
        sex: editForm.sex,
        height_cm: parseFloat(editForm.height_cm),
        weight_kg: parseFloat(editForm.weight_kg),
        activity_level: editForm.activity_level,
        goal: editForm.goal,
        intensity: editForm.intensity
      };

      const res = await applyProfilePlan(numForm);
      setProfile(res.profile);
      setActivePlan(res.active_plan || res.target_snapshot);
      if (res.profile) {
        setEditForm((prev) => ({
          ...prev,
          name: res.profile.name || '',
          age: res.profile.age,
          sex: res.profile.sex,
          height_cm: res.profile.height_cm,
          weight_kg: res.profile.weight_kg,
          activity_level: res.profile.activity_level,
          goal: res.profile.goal,
          intensity: res.profile.intensity
        }));
      }
      setIsPreviewing(false);
      setIsEditing(false);
      setSuccessMsg('New nutrition plan applied successfully! New target snapshot recorded.');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      console.error('Error applying plan:', err);
      setError(err.message || 'Failed to apply new nutrition plan.');
    } finally {
      setSubmitting(false);
    }
  };

  // Quick Log Weight submission
  const handleLogWeightSubmit = async (e) => {
    e.preventDefault();
    if (!logWeightVal || isNaN(parseFloat(logWeightVal)) || parseFloat(logWeightVal) <= 0) {
      setError('Please enter a valid weight in kg.');
      return;
    }

    setWeightSubmitting(true);
    setError(null);
    try {
      await logWeight(parseFloat(logWeightVal), logWeightDate);
      setIsWeightModalOpen(false);
      setSuccessMsg(`Weight recorded (${parseFloat(logWeightVal)} kg).`);
      setTimeout(() => setSuccessMsg(null), 4000);
      // Refresh profile data to sync current weight
      await fetchProfileData();
    } catch (err) {
      console.error('Error logging weight:', err);
      setError(err.message || 'Failed to log weight.');
    } finally {
      setWeightSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw size={32} className="text-[#EF233C] animate-spin" />
        <p className="text-xs font-semibold text-zinc-400">Loading Profile & Nutrition Plan...</p>
      </div>
    );
  }

  // Get active targets for rendering
  const activeCalories = activePlan?.calorie_target ?? activePlan?.target_calories ?? 2000;
  const activeProtein = activePlan?.protein_target ?? activePlan?.protein_g ?? 150;
  const activeCarbs = activePlan?.carbs_target ?? activePlan?.carbs_g ?? 200;
  const activeFat = activePlan?.fat_target ?? activePlan?.fat_g ?? 65;
  const activeBmr = activePlan?.bmr ?? 1750;
  const activeTdee = activePlan?.tdee ?? 2500;
  const effectiveDate = activePlan?.effective_date ?? activePlan?.created_at?.split('T')[0] ?? 'Active';

  return (
    <div className="space-y-5 min-w-0 pb-24">
      {/* Header Banner */}
      <div className="flex items-center justify-between gap-3 bg-zinc-900/60 backdrop-blur-md border border-white/10 p-4 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-zinc-800 to-zinc-900 border border-white/10 flex items-center justify-center text-white font-bold shadow-inner">
            <User size={22} className="text-[#EF233C]" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">
              {profile?.name ? `${profile.name}'s Profile & Plan` : 'Profile & Plan'}
            </h1>
            <p className="text-xs text-zinc-400">Personal stats, BMR/TDEE & target targets</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsWeightModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-zinc-800/80 hover:bg-zinc-800 text-zinc-200 border border-white/10 rounded-xl text-xs font-semibold transition-all active:scale-95"
            title="Log weight entry"
          >
            <Scale size={14} className="text-[#EF233C]" />
            <span className="hidden sm:inline">Log Weight</span>
          </button>

          <button
            onClick={() => {
              setIsEditing(!isEditing);
              setIsPreviewing(false);
            }}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all active:scale-95 shadow-md ${
              isEditing
                ? 'bg-zinc-800 text-zinc-300 border border-white/10'
                : 'bg-[#EF233C] text-white hover:bg-red-600'
            }`}
          >
            {isEditing ? (
              <>
                <X size={14} />
                <span>Cancel</span>
              </>
            ) : (
              <>
                <Edit3 size={14} />
                <span>Edit Profile</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successMsg && (
        <div className="flex items-center gap-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-3.5 rounded-xl text-xs font-medium animate-fadeIn">
          <CheckCircle2 size={16} className="shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Error Notification Banner */}
      {error && (
        <div className="flex items-center justify-between gap-2.5 bg-red-500/10 border border-red-500/30 text-red-400 p-3.5 rounded-xl text-xs font-medium">
          <div className="flex items-center gap-2">
            <ShieldAlert size={16} className="shrink-0 text-[#EF233C]" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="p-1 hover:bg-red-500/20 rounded-md transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* ================================================================= */}
      {/* EDIT PROFILE & PLAN PREVIEW MODAL / DRAWER */}
      {/* ================================================================= */}
      {isEditing && (
        <div className="bg-zinc-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-6 space-y-5 shadow-2xl animate-fadeIn">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <Sliders size={18} className="text-[#EF233C]" />
              <h2 className="text-sm font-bold text-white tracking-wide">
                {isPreviewing ? 'Review Proposed Nutrition Plan' : 'Edit Personal Profile'}
              </h2>
            </div>
            <span className="text-[11px] font-semibold text-zinc-400 bg-zinc-800/60 px-2.5 py-1 rounded-lg border border-white/5">
              {isPreviewing ? 'Step 2 of 2: Preview' : 'Step 1 of 2: Parameters'}
            </span>
          </div>

          {!isPreviewing ? (
            /* EDIT FORM */
            <form onSubmit={handleCalculatePreview} className="space-y-6">
              {/* GROUP 1: PERSONAL */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-[#EF233C] tracking-wider uppercase">
                  <User size={14} />
                  <span>Personal Characteristics</span>
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Your Name (optional)</label>
                  <input
                    type="text"
                    maxLength={100}
                    placeholder="e.g. Alex"
                    value={editForm.name || ''}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-[#EF233C] placeholder:text-zinc-500 text-xs transition-colors"
                  />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Age (years)</label>
                    <input
                      type="number"
                      min="10"
                      max="120"
                      required
                      value={editForm.age}
                      onChange={(e) => setEditForm({ ...editForm, age: e.target.value })}
                      className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Biological Sex</label>
                    <select
                      value={editForm.sex}
                      onChange={(e) => setEditForm({ ...editForm, sex: e.target.value })}
                      className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Height (cm)</label>
                    <input
                      type="number"
                      step="0.5"
                      min="100"
                      max="250"
                      required
                      value={editForm.height_cm}
                      onChange={(e) => setEditForm({ ...editForm, height_cm: e.target.value })}
                      className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Current Weight (kg)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="30"
                      max="300"
                      required
                      value={editForm.weight_kg}
                      onChange={(e) => setEditForm({ ...editForm, weight_kg: e.target.value })}
                      className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                    />
                  </div>
                </div>
              </div>

              {/* GROUP 2: ACTIVITY & GOAL */}
              <div className="space-y-3 border-t border-white/5 pt-4">
                <div className="flex items-center gap-2 text-xs font-bold text-[#EF233C] tracking-wider uppercase">
                  <Activity size={14} />
                  <span>Activity & Fitness Goal</span>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Activity Level</label>
                    <select
                      value={editForm.activity_level}
                      onChange={(e) => setEditForm({ ...editForm, activity_level: e.target.value })}
                      className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2.5 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                    >
                      {options && options.activity_levels ? (
                        options.activity_levels.map((lvl) => (
                          <option key={lvl.name} value={lvl.name}>
                            {lvl.name} — {lvl.description}
                          </option>
                        ))
                      ) : (
                        <>
                          <option value="Sedentary">Sedentary (Little or no exercise)</option>
                          <option value="Lightly Active">Lightly Active (Exercise 1–3 days/wk)</option>
                          <option value="Moderately Active">Moderately Active (Exercise 3–5 days/wk)</option>
                          <option value="Very Active">Very Active (Exercise 6–7 days/wk)</option>
                          <option value="Extremely Active">Extremely Active (Hard training / physical job)</option>
                        </>
                      )}
                    </select>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Primary Fitness Goal</label>
                      <select
                        value={editForm.goal}
                        onChange={(e) => handleGoalChange(e.target.value)}
                        className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2.5 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                      >
                        <option value="Fat Loss">🔥 Fat Loss</option>
                        <option value="Body Recomposition">⚖️ Body Recomposition</option>
                        <option value="Lean Bulk">💪 Lean Bulk</option>
                        <option value="Maintenance">⚖️ Maintenance</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Goal Intensity</label>
                      <select
                        value={editForm.intensity}
                        onChange={(e) => setEditForm({ ...editForm, intensity: e.target.value })}
                        className="w-full bg-zinc-800/80 border border-white/10 rounded-xl px-3 py-2.5 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                      >
                        {options && options.goals && options.goals[editForm.goal] ? (
                          options.goals[editForm.goal].intensities.map((intName) => {
                            const details = options.goals[editForm.goal].intensity_details?.[intName];
                            return (
                              <option key={intName} value={intName}>
                                {details?.label || intName}
                              </option>
                            );
                          })
                        ) : (
                          <option value={editForm.intensity}>{editForm.intensity}</option>
                        )}
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* ACTION BUTTONS */}
              <div className="flex items-center justify-end gap-3 border-t border-white/10 pt-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-300 hover:bg-zinc-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#EF233C] hover:bg-red-600 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-lg active:scale-95"
                >
                  {submitting ? (
                    <RefreshCw size={14} className="animate-spin" />
                  ) : (
                    <Sparkles size={14} />
                  )}
                  <span>Calculate Plan Preview</span>
                </button>
              </div>
            </form>
          ) : (
            /* PLAN PREVIEW CARD */
            <div className="space-y-5">
              <div className="bg-zinc-800/40 p-3.5 rounded-xl border border-white/5 text-xs text-zinc-300 leading-relaxed">
                <p className="font-semibold text-white">Review proposed targets</p>
                <p className="text-[11px] text-zinc-400">
                  Calculated by MacroSnap's deterministic engine using Mifflin-St Jeor formula. Active targets will NOT change until you explicitly confirm.
                </p>
              </div>

              {previewData && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {/* CURRENT PLAN COLUMN */}
                  <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/10 space-y-3">
                    <div className="flex items-center justify-between border-b border-white/10 pb-2">
                      <span className="font-bold text-zinc-400 uppercase text-[10px]">CURRENT PLAN</span>
                      <span className="text-[10px] text-zinc-500 font-mono">{effectiveDate}</span>
                    </div>

                    <div className="space-y-2">
                      <div>
                        <span className="text-[10px] text-zinc-400 block">Daily Target</span>
                        <span className="text-base font-bold text-zinc-200">
                          {(previewData.current_plan?.calorie_target || previewData.current_plan?.target_calories)?.toLocaleString()} kcal
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-1 pt-1 text-[11px]">
                        <div>
                          <span className="text-zinc-500 text-[9px] block">Protein</span>
                          <span className="font-bold text-zinc-300">{previewData.current_plan?.protein_target || previewData.current_plan?.protein_g}g</span>
                        </div>
                        <div>
                          <span className="text-zinc-500 text-[9px] block">Carbs</span>
                          <span className="font-bold text-zinc-300">{previewData.current_plan?.carbs_target || previewData.current_plan?.carbs_g}g</span>
                        </div>
                        <div>
                          <span className="text-zinc-500 text-[9px] block">Fat</span>
                          <span className="font-bold text-zinc-300">{previewData.current_plan?.fat_target || previewData.current_plan?.fat_g}g</span>
                        </div>
                      </div>
                      <div className="text-[10px] text-zinc-500 border-t border-white/5 pt-2">
                        BMR: {Math.round(previewData.current_plan?.bmr || 0)} kcal • TDEE: {Math.round(previewData.current_plan?.tdee || 0)} kcal
                      </div>
                    </div>
                  </div>

                  {/* PROPOSED PLAN COLUMN */}
                  <div className="bg-zinc-900/90 p-4 rounded-xl border border-[#EF233C]/40 space-y-3 relative overflow-hidden shadow-lg">
                    <div className="absolute top-0 right-0 bg-[#EF233C] text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg">
                      PROPOSED
                    </div>

                    <div className="flex items-center justify-between border-b border-white/10 pb-2">
                      <span className="font-bold text-[#EF233C] uppercase text-[10px]">NEW PLAN</span>
                      <span className="text-[10px] text-zinc-400 font-medium">{editForm.goal}</span>
                    </div>

                    <div className="space-y-2">
                      <div>
                        <span className="text-[10px] text-zinc-400 block">Daily Target</span>
                        <div className="flex items-baseline gap-2">
                          <span className="text-lg font-extrabold text-white">
                            {previewData.proposed_plan?.target_calories?.toLocaleString()} kcal
                          </span>
                          {(() => {
                            const cur = previewData.current_plan?.calorie_target || previewData.current_plan?.target_calories || 0;
                            const prop = previewData.proposed_plan?.target_calories || 0;
                            const diff = prop - cur;
                            if (diff === 0) return null;
                            return (
                              <span className={`text-[10px] font-bold ${diff > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                ({diff > 0 ? `+${diff}` : diff} kcal)
                              </span>
                            );
                          })()}
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-1 pt-1 text-[11px]">
                        <div>
                          <span className="text-zinc-400 text-[9px] block">Protein</span>
                          <span className="font-bold text-white">{previewData.proposed_plan?.protein_g}g</span>
                        </div>
                        <div>
                          <span className="text-zinc-400 text-[9px] block">Carbs</span>
                          <span className="font-bold text-white">{previewData.proposed_plan?.carbs_g}g</span>
                        </div>
                        <div>
                          <span className="text-zinc-400 text-[9px] block">Fat</span>
                          <span className="font-bold text-white">{previewData.proposed_plan?.fat_g}g</span>
                        </div>
                      </div>

                      <div className="text-[10px] text-zinc-400 border-t border-white/5 pt-2">
                        BMR: {Math.round(previewData.proposed_plan?.bmr || 0)} kcal • TDEE: {Math.round(previewData.proposed_plan?.tdee || 0)} kcal
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ACTION CONFIRMATION BUTTONS */}
              <div className="flex items-center justify-between border-t border-white/10 pt-4 gap-3">
                <button
                  type="button"
                  onClick={() => setIsPreviewing(false)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-400 hover:bg-zinc-800 transition-colors"
                >
                  ← Edit Parameters
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsPreviewing(false);
                      setIsEditing(false);
                    }}
                    className="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-300 hover:bg-zinc-800 transition-colors"
                  >
                    Cancel
                  </button>

                  <button
                    type="button"
                    onClick={handleApplyPlan}
                    disabled={submitting}
                    className="flex items-center gap-2 px-5 py-2.5 bg-[#EF233C] hover:bg-red-600 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-lg active:scale-95"
                  >
                    {submitting ? (
                      <RefreshCw size={14} className="animate-spin" />
                    ) : (
                      <Check size={14} />
                    )}
                    <span>Apply New Plan</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ================================================================= */}
      {/* DISPLAY 1: CURRENT PROFILE INFORMATION */}
      {/* ================================================================= */}
      {profile && (
        <div className="bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 sm:p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-white/5 pb-2.5">
            <div className="flex items-center gap-2">
              <User size={16} className="text-[#EF233C]" />
              <h2 className="text-xs font-bold text-white tracking-wide uppercase">Profile Attributes</h2>
            </div>
            <span className="text-[10px] text-zinc-400 font-mono">Persisted Data</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* PERSONAL STATS */}
            <div className="bg-zinc-900/80 p-3.5 rounded-xl border border-white/5 space-y-2.5">
              <span className="text-[10px] font-bold text-[#EF233C] uppercase tracking-wider block">PERSONAL</span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {profile.name && (
                  <div className="col-span-2 pb-1.5 border-b border-white/5">
                    <span className="text-zinc-500 text-[10px] block">Name</span>
                    <span className="font-semibold text-white">{profile.name}</span>
                  </div>
                )}
                <div>
                  <span className="text-zinc-500 text-[10px] block">Age</span>
                  <span className="font-semibold text-zinc-200">{profile.age} years</span>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] block">Sex</span>
                  <span className="font-semibold text-zinc-200">{profile.sex}</span>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] block">Height</span>
                  <span className="font-semibold text-zinc-200">{profile.height_cm} cm</span>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] block">Current Weight</span>
                  <span className="font-semibold text-white">{profile.weight_kg} kg</span>
                </div>
              </div>
            </div>

            {/* ACTIVITY & GOAL */}
            <div className="bg-zinc-900/80 p-3.5 rounded-xl border border-white/5 space-y-2.5">
              <span className="text-[10px] font-bold text-[#EF233C] uppercase tracking-wider block">ACTIVITY & GOAL</span>
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500 text-[10px]">Activity Level:</span>
                  <span className="font-semibold text-zinc-200">{profile.activity_level}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500 text-[10px]">Fitness Goal:</span>
                  <span className="font-semibold text-white">{profile.goal}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500 text-[10px]">Goal Intensity:</span>
                  <span className="font-semibold text-zinc-300">{profile.intensity}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* DISPLAY 2: ACTIVE NUTRITION PLAN */}
      {/* ================================================================= */}
      <div className="bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 sm:p-5 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/5 pb-2.5">
          <div className="flex items-center gap-2">
            <Target size={16} className="text-[#EF233C]" />
            <h2 className="text-xs font-bold text-white tracking-wide uppercase">Active Nutrition Plan</h2>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-400 font-mono bg-zinc-800/60 px-2 py-0.5 rounded-md border border-white/5">
            <Calendar size={11} className="text-[#EF233C]" />
            <span>Effective: {effectiveDate}</span>
          </div>
        </div>

        {/* METRICS ROW (BMR, TDEE, DAILY TARGET) */}
        <div className="grid grid-cols-3 gap-2.5 text-xs">
          <div className="bg-zinc-900/80 p-3 rounded-xl border border-white/5">
            <span className="text-zinc-400 text-[10px] block">Estimated BMR</span>
            <span className="text-sm font-bold text-zinc-200 mt-0.5 block">
              {Math.round(activeBmr).toLocaleString()} <span className="text-[10px] font-normal text-zinc-500">kcal</span>
            </span>
          </div>

          <div className="bg-zinc-900/80 p-3 rounded-xl border border-white/5">
            <span className="text-zinc-400 text-[10px] block font-medium">TDEE (Maintenance)</span>
            <span className="text-sm font-bold text-zinc-200 mt-0.5 block">
              {Math.round(activeTdee).toLocaleString()} <span className="text-[10px] font-normal text-zinc-500">kcal</span>
            </span>
          </div>

          <div className="bg-gradient-to-br from-zinc-900 via-zinc-900 to-[#EF233C]/20 p-3 rounded-xl border border-[#EF233C]/40 shadow-md">
            <span className="text-[#EF233C] text-[10px] font-bold block uppercase tracking-tight">Daily Calorie Target</span>
            <span className="text-base font-extrabold text-white mt-0.5 block">
              {Math.round(activeCalories).toLocaleString()} <span className="text-[10px] font-normal text-zinc-300">kcal</span>
            </span>
          </div>
        </div>

        {/* MACRONUTRIENT BREAKDOWN GRID */}
        <div className="space-y-2">
          <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Recommended Macro Breakdown</span>
          <div className="grid grid-cols-3 gap-2.5 text-xs">
            <div className="bg-zinc-900/80 p-3 rounded-xl border border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px]">Protein</span>
                <span className="text-[9px] text-emerald-400 font-mono">4 kcal/g</span>
              </div>
              <span className="text-sm font-bold text-white mt-1 block">{activeProtein} g</span>
              <span className="text-[10px] text-zinc-500 block font-mono">{activeProtein * 4} kcal</span>
            </div>

            <div className="bg-zinc-900/80 p-3 rounded-xl border border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px]">Carbohydrates</span>
                <span className="text-[9px] text-blue-400 font-mono">4 kcal/g</span>
              </div>
              <span className="text-sm font-bold text-white mt-1 block">{activeCarbs} g</span>
              <span className="text-[10px] text-zinc-500 block font-mono">{activeCarbs * 4} kcal</span>
            </div>

            <div className="bg-zinc-900/80 p-3 rounded-xl border border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px]">Fats</span>
                <span className="text-[9px] text-amber-400 font-mono">9 kcal/g</span>
              </div>
              <span className="text-sm font-bold text-white mt-1 block">{activeFat} g</span>
              <span className="text-[10px] text-zinc-500 block font-mono">{activeFat * 9} kcal</span>
            </div>
          </div>
        </div>

        {/* NUTRITION DISCLAIMER */}
        <div className="flex items-start gap-2.5 bg-zinc-900/40 p-3 rounded-xl border border-white/5 text-[11px] text-zinc-400 leading-relaxed">
          <Info size={16} className="text-zinc-400 shrink-0 mt-0.5" />
          <p>
            <span className="font-semibold text-zinc-300">Nutrition Disclaimer:</span> MacroSnap estimations are calculated deterministically using standard Mifflin-St Jeor energy formulas for informational purposes only. Consult a qualified medical practitioner or registered dietitian before undertaking any diet or exercise program.
          </p>
        </div>
      </div>

      {/* ================================================================= */}
      {/* QUICK WEIGHT LOG MODAL */}
      {/* ================================================================= */}
      {isWeightModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-zinc-900 border border-white/10 rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Scale size={18} className="text-[#EF233C]" />
                <h3 className="text-sm font-bold text-white">Log Current Weight</h3>
              </div>
              <button
                onClick={() => setIsWeightModalOpen(false)}
                className="p-1 text-zinc-400 hover:text-white rounded-lg transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleLogWeightSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Body Weight (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  min="30"
                  max="300"
                  required
                  autoFocus
                  placeholder="e.g. 75.5"
                  value={logWeightVal}
                  onChange={(e) => setLogWeightVal(e.target.value)}
                  className="w-full bg-zinc-800 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm font-bold focus:outline-none focus:border-[#EF233C]"
                />
              </div>

              <div>
                <label className="block text-[11px] text-zinc-400 mb-1 font-semibold">Date</label>
                <input
                  type="date"
                  required
                  value={logWeightDate}
                  onChange={(e) => setLogWeightDate(e.target.value)}
                  className="w-full bg-zinc-800 border border-white/10 rounded-xl px-3 py-2 text-white font-semibold focus:outline-none focus:border-[#EF233C]"
                />
              </div>

              <p className="text-[10px] text-zinc-500">
                Logging a new weight updates your weight history while preserving previous logs.
              </p>

              <div className="flex items-center justify-end gap-2 border-t border-white/10 pt-3">
                <button
                  type="button"
                  onClick={() => setIsWeightModalOpen(false)}
                  className="px-3.5 py-2 rounded-xl text-zinc-400 hover:bg-zinc-800 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={weightSubmitting}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#EF233C] hover:bg-red-600 disabled:opacity-50 text-white font-bold rounded-xl shadow-lg active:scale-95"
                >
                  {weightSubmitting ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
                  <span>Save Log</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
