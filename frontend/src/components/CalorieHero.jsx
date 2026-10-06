import React from 'react';

export default function CalorieHero({
  consumed = 540,
  target = 2380
}) {
  const remaining = Math.max(0, target - consumed);
  const progressPercent = Math.min(100, Math.round((consumed / (target || 1)) * 100));

  return (
    <div className="bg-[#0E1015]/75 backdrop-blur-xl border border-white/[0.1] border-t-white/15 rounded-[18px] p-5 relative overflow-hidden space-y-4 shadow-2xl">
      <div className="space-y-1 min-w-0">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#9297A3] block">
          Calories Remaining
        </span>
        <div className="flex items-baseline gap-1.5">
          <span className="text-[46px] font-extrabold text-[#F5F5F5] tracking-tight leading-none">
            {remaining.toLocaleString()}
          </span>
          <span className="text-xs font-semibold text-[#9297A3]">kcal</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="w-full h-2.5 bg-[#171A20]/90 rounded-full overflow-hidden border border-white/[0.04]">
          <div
            className="h-full bg-gradient-to-r from-[#FF2B3A] to-[#E02231] rounded-full transition-all duration-500 ease-out shadow-sm shadow-[#FF2B3A]/40"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Metrics Row */}
        <div className="flex items-center justify-between text-[13px] text-[#9297A3] font-medium pt-0.5">
          <span>{consumed.toLocaleString()} consumed</span>
          <span className="text-[#626875]">·</span>
          <span>{target.toLocaleString()} goal</span>
        </div>
      </div>
    </div>
  );
}
