import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import MobileShell from './components/MobileShell';
import HomePage from './pages/HomePage';
import SnapPage from './pages/SnapPage';
import CoachPage from './pages/CoachPage';
import ProfilePage from './pages/ProfilePage';
import HistoryPage from './pages/HistoryPage';
import ProgressPage from './pages/ProgressPage';
import OnboardingPage from './pages/OnboardingPage';
import ConnectionErrorScreen from './components/ConnectionErrorScreen';
import ReviewerLoginScreen from './components/ReviewerLoginScreen';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProfileProvider, useProfile } from './context/ProfileContext';

function AuthenticatedApp() {
  const { loading, connectionError, hasProfile, refreshProfile } = useProfile();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0E] flex flex-col items-center justify-center p-4 space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#EF233C] to-[#9D0208] flex items-center justify-center text-white font-black text-xl shadow-xl shadow-[#EF233C]/20 animate-pulse">
          MS
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-zinc-400">
          <RefreshCw size={14} className="animate-spin text-[#EF233C]" />
          <span>Connecting to MacroSnap...</span>
        </div>
      </div>
    );
  }

  // Handle unreachable backend: Do not mistake network failure for a new user
  if (connectionError) {
    return (
      <MobileShell>
        <ConnectionErrorScreen error={connectionError} onRetry={refreshProfile} />
      </MobileShell>
    );
  }

  // First-time user with no saved profile: Force onboarding flow
  if (!hasProfile) {
    return (
      <MobileShell>
        <Routes>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="*" element={<Navigate to="/onboarding" replace />} />
        </Routes>
      </MobileShell>
    );
  }

  // Returning user with valid saved profile
  return (
    <MobileShell>
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/snap" element={<SnapPage />} />
        <Route path="/coach" element={<CoachPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/onboarding" element={<Navigate to="/home" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </MobileShell>
  );
}

function AppContent() {
  const { isAuthenticated, checkingAuth } = useAuth();

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-[#0A0A0E] flex flex-col items-center justify-center p-4 space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#EF233C] to-[#9D0208] flex items-center justify-center text-white font-black text-xl shadow-xl shadow-[#EF233C]/20 animate-pulse">
          MS
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-zinc-400">
          <RefreshCw size={14} className="animate-spin text-[#EF233C]" />
          <span>Verifying Reviewer Access...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <ReviewerLoginScreen />;
  }

  return (
    <ProfileProvider>
      <AuthenticatedApp />
    </ProfileProvider>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}
