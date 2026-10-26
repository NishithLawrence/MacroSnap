import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getProfile, applyProfilePlan, resetProfile } from '../lib/api';

const ProfileContext = createContext(null);

export function ProfileProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [connectionError, setConnectionError] = useState(null);
  const [hasProfile, setHasProfile] = useState(false);
  const [profile, setProfile] = useState(null);
  const [activePlan, setActivePlan] = useState(null);
  const [options, setOptions] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setConnectionError(null);
    try {
      const res = await getProfile();
      // res is { has_profile, profile, active_plan, options }
      setHasProfile(Boolean(res.has_profile && res.profile));
      setProfile(res.profile || null);
      setActivePlan(res.active_plan || null);
      setOptions(res.options || null);
      return res;
    } catch (err) {
      console.error('[ProfileContext] Failed to connect to backend:', err);
      setConnectionError(err.message || 'Unable to connect to Revelation backend');
      setHasProfile(false);
      setProfile(null);
      setActivePlan(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const saveAndApplyPlan = useCallback(async (payload) => {
    const res = await applyProfilePlan(payload);
    if (res && res.status === 'ok') {
      setHasProfile(true);
      setProfile(res.profile);
      setActivePlan(res.active_plan || res.target_snapshot);
    }
    return res;
  }, []);

  const resetProfileData = useCallback(async () => {
    try {
      await resetProfile();
      setHasProfile(false);
      setProfile(null);
      setActivePlan(null);
      return true;
    } catch (err) {
      console.error('[ProfileContext] Failed to reset profile:', err);
      throw err;
    }
  }, []);

  const value = {
    loading,
    connectionError,
    hasProfile,
    profile,
    activePlan,
    options,
    refreshProfile: loadData,
    saveAndApplyPlan,
    resetProfileData,
  };

  return (
    <ProfileContext.Provider value={value}>
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  const context = useContext(ProfileContext);
  if (!context) {
    throw new Error('useProfile must be used within a ProfileProvider');
  }
  return context;
}
