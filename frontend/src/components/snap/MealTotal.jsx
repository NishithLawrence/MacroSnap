import React from 'react';
import { Flame } from 'lucide-react';

export default function MealTotal({ total }) {
  return (
    <div className="bg-[#111318]/90 backdrop-blur-md border border-[#FF2B3A]/30 rounded-[18px] p-4 space-y-3 shadow-xl">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5">
        <div className="flex items-center gap-2">
          <Flame size={18} className="text-[#FF2B3A]" />
          <h3 className="text-[14px] font-extrabold uppercase tracking-wider text-[#F5F5F5]">
            MEAL TOTAL
          </h3>
        </div>
        <div className="text-right">
          <span className="text-[22px] font-extrabold text-[#F5F5F5] tracking-tight">
            {total.calories}{' '}
            <span className="text-xs font-semibold text-[#9297A3]">kcal</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="bg-[#171A20] p-2 rounded-xl border border-white/5">
          <span className="text-[10px] text-[#9297A3] font-semibold uppercase block">Protein</span>
          <span className="text-sm font-bold text-[#F5F5F5] mt-0.5 block">{total.protein_g}g</span>
        </div>
        <div className="bg-[#171A20] p-2 rounded-xl border border-white/5">
          <span className="text-[10px] text-[#9297A3] font-semibold uppercase block">Carbs</span>
          <span className="text-sm font-bold text-[#F5F5F5] mt-0.5 block">{total.carbs_g}g</span>
        </div>
        <div className="bg-[#171A20] p-2 rounded-xl border border-white/5">
          <span className="text-[10px] text-[#9297A3] font-semibold uppercase block">Fat</span>
          <span className="text-sm font-bold text-[#F5F5F5] mt-0.5 block">{total.fat_g}g</span>
        </div>
      </div>
    </div>
  );
}
