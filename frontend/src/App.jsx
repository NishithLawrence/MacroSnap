import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MobileShell from './components/MobileShell';
import HomePage from './pages/HomePage';
import SnapPage from './pages/SnapPage';
import CoachPage from './pages/CoachPage';
import ProfilePage from './pages/ProfilePage';
import HistoryPage from './pages/HistoryPage';
import ProgressPage from './pages/ProgressPage';
import OnboardingPage from './pages/OnboardingPage';

export default function App() {
  return (
    <Router>
      <MobileShell>
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/snap" element={<SnapPage />} />
          <Route path="/coach" element={<CoachPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="*" element={<Navigate to="/home" replace />} />
        </Routes>
      </MobileShell>
    </Router>
  );
}
