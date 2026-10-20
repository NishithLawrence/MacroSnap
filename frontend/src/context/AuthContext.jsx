import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  getStoredToken,
  loginReviewer,
  verifyAuth,
  logoutReviewer,
  onAuthExpired,
} from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Validate existing session token on initial mount
  useEffect(() => {
    let isMounted = true;

    async function checkSession() {
      const token = getStoredToken();
      if (!token) {
        if (isMounted) {
          setIsAuthenticated(false);
          setCheckingAuth(false);
        }
        return;
      }

      try {
        await verifyAuth();
        if (isMounted) {
          setIsAuthenticated(true);
          setAuthError(null);
        }
      } catch {
        if (isMounted) {
          setIsAuthenticated(false);
          setAuthError('Your previous session has expired. Please log in again.');
        }
      } finally {
        if (isMounted) {
          setCheckingAuth(false);
        }
      }
    }

    checkSession();

    // Subscribe to 401 expiration events from api client
    const unsubscribe = onAuthExpired(() => {
      if (isMounted) {
        setIsAuthenticated(false);
        setAuthError('Your demo session has expired. Please enter the passcode to continue.');
      }
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (password) => {
    setAuthError(null);
    try {
      const res = await loginReviewer(password);
      setIsAuthenticated(true);
      return res;
    } catch (err) {
      setAuthError(err.message || 'Authentication failed. Please verify your passcode.');
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    logoutReviewer();
    setIsAuthenticated(false);
    setAuthError(null);
  }, []);

  const value = {
    isAuthenticated,
    checkingAuth,
    authError,
    setAuthError,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
