const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Health check endpoint against the MacroSnap backend.
 */
export async function getHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch API health status:', error);
    throw error;
  }
}

/**
 * Sends a meal image file to the server-side Gemini Vision endpoint.
 * @param {File} file - Image file object from file input / camera
 * @param {string} mealType - Breakfast | Lunch | Dinner | Snack
 * @returns {Promise<Object>} Structured meal analysis JSON
 */
export async function scanMeal(file, mealType = 'Lunch') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('meal_type', mealType);

  const response = await fetch(`${API_BASE_URL}/api/meals/scan`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorMsg = 'Unable to analyze this meal.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Persists a confirmed meal into storage.
 * @param {Object} mealData - Meal structure with foods, totals, meal_type, date, etc.
 * @returns {Promise<Object>} Confirmation response from backend
 */
export async function createMeal(mealData) {
  const response = await fetch(`${API_BASE_URL}/api/meals`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(mealData),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to save meal.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Fetches current live daily context (profile, targets, consumed, remaining, meals).
 * @returns {Promise<Object>} Context breakdown object
 */
export async function getCoachContext() {
  const response = await fetch(`${API_BASE_URL}/api/coach/context`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch Coach context');
  }

  return await response.json();
}

/**
 * Sends prompt and optional conversation history to backend Coach endpoint.
 * @param {string} message - User question or prompt
 * @param {Array} conversation - Current session history items
 * @returns {Promise<Object>} { success, response, error }
 */
export async function chatWithCoach(message, conversation = []) {
  const response = await fetch(`${API_BASE_URL}/api/coach/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation,
    }),
  });

  if (!response.ok) {
    let errorMsg = 'Coach is temporarily unavailable.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Fetches meal history grouped by date with daily totals.
 * @returns {Promise<Object>} { dates: Array }
 */
export async function getMealHistory() {
  const response = await fetch(`${API_BASE_URL}/api/meals/history`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch meal history');
  }

  return await response.json();
}

/**
 * Deletes a meal record by ID.
 * @param {string} mealId
 * @returns {Promise<Object>} { status: 'ok', deleted: mealId }
 */
export async function deleteMeal(mealId) {
  const response = await fetch(`${API_BASE_URL}/api/meals/${mealId}`, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    let errorMsg = 'Failed to delete meal.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Updates an existing meal record.
 * @param {string} mealId
 * @param {Object} updatedMeal
 * @returns {Promise<Object>} { status: 'ok', meal: updatedMeal }
 */
export async function updateMeal(mealId, updatedMeal) {
  const response = await fetch(`${API_BASE_URL}/api/meals/${mealId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(updatedMeal),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to update meal.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Fetches progress analytics summary for 7D or 30D period.
 * @param {number} days - 7 or 30
 * @returns {Promise<Object>} Analytics period summary object
 */
export async function getProgressAnalytics(days = 7) {
  const response = await fetch(`${API_BASE_URL}/api/progress/analytics?days=${days}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch progress analytics');
  }

  return await response.json();
}

/**
 * Logs a body weight entry.
 * @param {number} weightKg
 * @param {string} [date] - YYYY-MM-DD
 * @returns {Promise<Object>} { status: 'ok', weight_change: Object }
 */
export async function logWeight(weightKg, date = null) {
  const payload = { weight_kg: weightKg };
  if (date) payload.date = date;

  const response = await fetch(`${API_BASE_URL}/api/progress/weight`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to log weight.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Fetches saved user profile, active target plan snapshot, and goal/activity options.
 * @returns {Promise<{profile: Object, active_plan: Object, options: Object}>}
 */
export async function getProfile() {
  const response = await fetch(`${API_BASE_URL}/api/profile`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    let errorMsg = 'Failed to fetch user profile.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Calculates a preview of the proposed plan without persisting changes.
 * @param {Object} profilePayload
 * @returns {Promise<{current_profile: Object, current_plan: Object, proposed_profile: Object, proposed_plan: Object}>}
 */
export async function previewProfilePlan(profilePayload) {
  const response = await fetch(`${API_BASE_URL}/api/profile/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(profilePayload),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to calculate proposed plan preview.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}

/**
 * Saves profile, logs weight entry, and applies new target snapshot.
 * @param {Object} profilePayload
 * @returns {Promise<{status: string, profile: Object, target_snapshot: Object, active_plan: Object}>}
 */
export async function applyProfilePlan(profilePayload) {
  const response = await fetch(`${API_BASE_URL}/api/profile/apply`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(profilePayload),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to apply new nutrition plan.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  return await response.json();
}


