import React from 'react';

export default function DailyTotals({ totals = {} }) {
  const cals = totals.calories || 0;
  const p = totals.protein_g || 0;
  const c = totals.carbs_g || 0;
  const f = totals.fat_g || 0;

  return (
    <div className="flex items-center gap-1.5 text-[10px] flex-wrap">
      <span className="px-2 py-0.5 rounded-md bg-[#EF233C]/10 border border-[#EF233C]/20 font-bold text-[#EF233C]">
        {cals} kcal
      </span>
      <span className="px-2 py-0.5 rounded-md bg-sky-500/10 border border-sky-500/20 font-semibold text-sky-400">
        P: {p}g
      </span>
      <span className="px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 font-semibold text-amber-400">
        C: {c}g
      </span>
      <span className="px-2 py-0.5 rounded-md bg-rose-500/10 border border-rose-500/20 font-semibold text-rose-400">
        F: {f}g
      </span>
    </div>
  );
}
