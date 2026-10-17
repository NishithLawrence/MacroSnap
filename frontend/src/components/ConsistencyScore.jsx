import React from 'react';
import { Award, ShieldCheck } from 'lucide-react';

export default function ConsistencyScore({ scorePct }) {
  const score = Math.max(0, Math.min(100, Math.round(scorePct || 0)));

  let label = 'Building Habit';
  let badgeColor = 'text-amber-400 border-amber-500/20 bg-amber-500/10';

  if (score >= 80) {
    label = 'High Consistency';
    badgeColor = 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10';
  } else if (score >= 50) {
    label = 'Moderate Consistency';
    badgeColor = 'text-sky-400 border-sky-500/20 bg-sky-500/10';
  }

  return (
    <div className="bg-[#12141A]/80 backdrop-blur-md border border-white/[0.07] rounded-2xl p-4 space-y-3 min-w-0 shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#FF2B3A]/10 border border-[#FF2B3A]/20 flex items-center justify-center text-[#FF2B3A]">
            <Award size={15} />
          </div>
          <h2 className="text-xs font-bold text-white tracking-tight">Consistency Score</h2>
        </div>
        <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
          {label}
        </span>
      </div>

      <div className="flex items-center justify-between gap-4 pt-1">
        <div className="space-y-1">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-white tracking-tight">{score}</span>
            <span className="text-xs font-bold text-[#9297A3]">%</span>
          </div>
          <p className="text-[11px] text-[#9297A3] leading-tight">
            Backend metric measuring calorie precision & protein target achievement.
          </p>
        </div>

        {/* Circular progress visual */}
        <div className="relative w-13 h-13 shrink-0 flex items-center justify-center">
          <svg className="w-13 h-13 -rotate-90 transform" viewBox="0 0 36 36">
            <path
              className="text-zinc-800/80"
              strokeWidth="3.5"
              stroke="currentColor"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className="text-[#FF2B3A] transition-all duration-500"
              strokeDasharray={`${score}, 100`}
              strokeWidth="3.5"
              strokeLinecap="round"
              stroke="currentColor"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <ShieldCheck size={16} className="absolute text-[#FF2B3A]" />
        </div>
      </div>
    </div>
  );
}
