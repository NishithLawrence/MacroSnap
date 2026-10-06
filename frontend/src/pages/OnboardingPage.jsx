import React from 'react';
import { Flame, ArrowRight, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function OnboardingPage() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6 py-4 min-w-0">
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#EF233C] to-[#9D0208] flex items-center justify-center text-white font-black text-xl mx-auto shadow-xl shadow-[#EF233C]/20">
          MS
        </div>
        <h1 className="text-2xl font-black text-white tracking-tight">
          Macro<span className="text-[#EF233C]">Snap</span>
        </h1>
        <p className="text-xs text-zinc-400 max-w-[280px] mx-auto">
          Precision nutrition calculation powered by AI vision and scientific equations.
        </p>
      </div>

      <div className="app-card p-5 space-y-4">
        <h2 className="text-xs font-bold text-white uppercase tracking-wider text-center">
          Onboarding Setup Placeholder
        </h2>

        <div className="space-y-3">
          <div className="bg-zinc-900/60 p-3 rounded-xl border border-white/5 flex items-center gap-3">
            <ShieldCheck size={18} className="text-[#EF233C] shrink-0" />
            <span className="text-xs text-zinc-300">Automatic BMR & TDEE calculation formula</span>
          </div>
          <div className="bg-zinc-900/60 p-3 rounded-xl border border-white/5 flex items-center gap-3">
            <Flame size={18} className="text-[#EF233C] shrink-0" />
            <span className="text-xs text-zinc-300">Custom macro goal split selection</span>
          </div>
        </div>
      </div>

      <button
        onClick={() => navigate('/home')}
        className="w-full py-3.5 px-4 rounded-xl bg-[#EF233C] hover:bg-[#D90429] text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-[#EF233C]/25 transition-all"
      >
        <span>Get Started</span>
        <ArrowRight size={16} />
      </button>
    </div>
  );
}
