const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const TOKEN_STORAGE_KEY = 'macrosnap_demo_token';

/**
 * Retrieves the short-lived access token from sessionStorage only.
 * Never reads or writes from localStorage, cookies, or persistent stores.
 */
export function getStoredToken() {
  try {
    return sessionStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (e) {
    return null;
  }
}

/**
 * Stores the short-lived access token in sessionStorage only.
 */
export function setStoredToken(token) {
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch (e) {}
}

/**
 * Clears the stored token from sessionStorage.
 */
export function clearStoredToken() {
  try {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (e) {}
}

/**
 * Listens for auth expiration events dispatched when a 401 response occurs.
 */
export function onAuthExpired(callback) {
  if (typeof window === 'undefined') return () => {};
  const handler = () => callback();
  window.addEventListener('macrosnap:auth_expired', handler);
  return () => window.removeEventListener('macrosnap:auth_expired', handler);
}

function notifyAuthExpired() {
  clearStoredToken();
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('macrosnap:auth_expired'));
  }
}

/**
 * Centralized fetch wrapper that automatically injects the Authorization Bearer token,
 * handles common headers, and triggers session expiration handlers on 401 responses.
 */
export async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  const token = getStoredToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const fetchOptions = {
    ...options,
    headers,
  };

  const response = await fetch(url, fetchOptions);

  if (response.status === 401) {
    notifyAuthExpired();
  }

  return response;
}

/**
 * Public reviewer login endpoint.
 * Validates demo passcode with the backend and stores the short-lived token in sessionStorage.
 * @param {string} password - Reviewer demo passcode
 */
export async function loginReviewer(password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ password }),
  });

  if (!response.ok) {
    let errorMsg = 'Authentication failed. Please check your passcode.';
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  const data = await response.json();
  if (data.access_token) {
    setStoredToken(data.access_token);
  }
  return data;
}

/**
 * Verifies active session token validity against the backend.
 */
export async function verifyAuth() {
  const response = await apiFetch('/api/auth/verify', {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Session is not authenticated.');
  }

  return await response.json();
}

/**
 * Explicit logout action. Clears sessionStorage token and dispatches event.
 */
export function logoutReviewer() {
  notifyAuthExpired();
}

/**
 * Health check endpoint against the MacroSnap backend (public, non-sensitive).
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
 * Protected route: uses apiFetch to pass Authorization header.
 * @param {File} file - Image file object from file input / camera
 * @param {string} mealType - Breakfast | Lunch | Dinner | Snack
 * @returns {Promise<Object>} Structured meal analysis JSON
 */
export async function scanMeal(file, mealType = 'Lunch') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('meal_type', mealType);

  const response = await apiFetch('/api/meals/scan', {
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
  const response = await apiFetch('/api/meals', {
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
  const response = await apiFetch('/api/coach/context', {
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
  const response = await apiFetch('/api/coach/chat', {
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
  const response = await apiFetch('/api/meals/history', {
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
  const response = await apiFetch(`/api/meals/${mealId}`, {
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
  const response = await apiFetch(`/api/meals/${mealId}`, {
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
  const response = await apiFetch(`/api/progress/analytics?days=${days}`, {
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

  const response = await apiFetch('/api/progress/weight', {
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
 * @returns {Promise<{has_profile: boolean, profile: Object, active_plan: Object, options: Object}>}
 */
export async function getProfile() {
  const response = await apiFetch('/api/profile', {
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
  const response = await apiFetch('/api/profile/preview', {
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
  const response = await apiFetch('/api/profile/apply', {
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
