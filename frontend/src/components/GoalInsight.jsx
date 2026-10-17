import React from 'react';
import { Target, Info, Sparkles } from 'lucide-react';

export default function GoalInsight({ goal = 'Fat Loss', interpretation = '' }) {
  return (
    <div className="bg-[#12141A]/80 backdrop-blur-md border border-white/[0.07] rounded-2xl p-4 space-y-3 min-w-0 shadow-md">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Target size={15} />
          </div>
          <div>
            <h2 className="text-xs font-bold text-white tracking-tight">Goal-Aware Progress Insight</h2>
            <p className="text-[10px] text-[#9297A3]">Active Goal: <span className="font-semibold text-emerald-400">{goal}</span></p>
          </div>
        </div>
        <Sparkles size={15} className="text-emerald-400" />
      </div>

      <div className="bg-black/30 p-3 rounded-xl border border-white/[0.05] space-y-2">
        <p className="text-xs text-zinc-200 leading-relaxed font-medium">
          {interpretation || 'Log meals to generate personalized goal feedback.'}
        </p>
        <div className="flex items-center gap-1.5 pt-1 text-[10px] text-[#9297A3] border-t border-white/[0.05]">
          <Info size={12} className="shrink-0 text-zinc-400" />
          <span>Non-medical informational insight based on your target plan and recorded daily intake.</span>
        </div>
      </div>
    </div>
  );
}
