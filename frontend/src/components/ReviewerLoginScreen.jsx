import React, { useState } from 'react';
import { Lock, Eye, EyeOff, ShieldAlert, Sparkles, RefreshCw, Info } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import RevelationLogo from './RevelationLogo';

export default function ReviewerLoginScreen() {
  const { login, authError, setAuthError } = useAuth();
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim()) {
      setLocalError('Please enter the reviewer passcode.');
      return;
    }

    setSubmitting(true);
    setLocalError(null);
    if (setAuthError) setAuthError(null);

    try {
      await login(password.trim());
    } catch (err) {
      setLocalError(err.message || 'Authentication failed. Please verify the passcode.');
    } finally {
      setSubmitting(false);
    }
  };

  const activeError = localError || authError;

  return (
    <div className="w-full h-screen h-[100dvh] bg-[#040406] flex justify-center items-center p-4 antialiased selection:bg-[#EF233C]/30 selection:text-white">
      <div className="w-full max-w-[420px] bg-[#0A0A0E] border border-white/[0.08] rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 relative overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-48 h-48 bg-[#EF233C]/20 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="text-center space-y-2 relative">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-[#EF233C] to-[#9D0208] text-white shadow-lg shadow-[#EF233C]/25 mb-1">
            <RevelationLogo size={28} variant="white" />
          </div>
          <h1 className="text-lg font-black text-white tracking-tight">
            REVEL<span className="text-[#EF233C]">ATION</span>
          </h1>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-[11px] font-semibold text-zinc-400">
            <Lock size={12} className="text-[#EF233C]" />
            <span>Restricted Demo Reviewer Access</span>
          </div>
        </div>

        {/* Sandbox Notice */}
        <div className="bg-zinc-900/60 border border-white/[0.06] rounded-2xl p-3.5 space-y-1.5 text-xs text-zinc-400 leading-relaxed">
          <div className="flex items-center gap-1.5 text-zinc-300 font-semibold text-[11px]">
            <Info size={14} className="text-[#EF233C] shrink-0" />
            <span>Shared Synthetic Demo Sandbox</span>
          </div>
          <p className="text-[11px]">
            This student portfolio demonstration uses a shared synthetic sandbox with demo profiles, simulated AI meal scans, and historical data. Please enter the reviewer passcode provided for evaluation.
          </p>
        </div>

        {/* Error Banner */}
        {activeError && (
          <div className="flex items-start gap-2.5 bg-red-500/10 border border-red-500/30 text-red-300 p-3.5 rounded-xl text-xs font-medium animate-fadeIn">
            <ShieldAlert size={16} className="text-[#EF233C] shrink-0 mt-0.5" />
            <span className="leading-snug">{activeError}</span>
          </div>
        )}

        {/* Passcode Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-zinc-300">
              Reviewer Passcode
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                autoFocus
                required
                placeholder="Enter demo passcode"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-zinc-900/80 border border-white/10 rounded-xl px-4 py-3 pr-11 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#EF233C] transition-colors font-medium"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 p-1 transition-colors"
                title={showPassword ? 'Hide passcode' : 'Show passcode'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 px-4 bg-gradient-to-r from-[#EF233C] to-[#B01728] hover:from-red-600 hover:to-red-700 disabled:opacity-50 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-[#EF233C]/20 transition-all active:scale-[0.98]"
          >
            {submitting ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Validating Passcode...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} />
                <span>Unlock Demo Access</span>
              </>
            )}
          </button>
        </form>

        {/* Security Footnote */}
        <div className="text-center pt-2 border-t border-white/[0.05]">
          <p className="text-[10px] text-zinc-500 leading-normal">
            Short-lived authorization tokens are held in session storage only and expire automatically. No personal data is stored.
          </p>
        </div>
      </div>
    </div>
  );
}
