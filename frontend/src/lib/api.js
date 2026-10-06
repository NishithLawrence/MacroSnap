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

