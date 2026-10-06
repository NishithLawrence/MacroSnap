import React from 'react';
import { Flame, Dumbbell, Sparkles } from 'lucide-react';

export default function CoachContext({ contextData }) {
  if (!contextData) return null;

  const {
    target_calories = 2380,
    consumed_calories = 0,
    remaining_calories = 2380,
    target_protein = 144,
    consumed_protein = 0,
    remaining_protein = 144,
  } = contextData;

  return (
    <div className="bg-stone-900/70 backdrop-blur-md border border-white/10 rounded-2xl p-3.5 shadow-lg space-y-2.5 min-w-0">
      <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-red-400">
        <span className="flex items-center gap-1.5">
          <Sparkles size={12} className="text-red-400" /> Today's Context
        </span>
        <span className="text-[10px] text-stone-400 font-mono">Live Snapshot</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* Calories Card */}
        <div className="bg-stone-800/50 rounded-xl p-2.5 border border-white/5 space-y-1">
          <div className="flex items-center gap-1 text-[11px] text-stone-400">
            <Flame size={12} className="text-amber-400" /> Calories
          </div>
          <div className="text-sm font-extrabold text-white">
            {consumed_calories.toLocaleString()}{' '}
            <span className="text-[11px] font-normal text-stone-400">/ {target_calories.toLocaleString()}</span>
          </div>
          <div className="text-[10px] text-amber-400/90 font-medium">
            {remaining_calories.toLocaleString()} kcal left
          </div>
        </div>

        {/* Protein Card */}
        <div className="bg-stone-800/50 rounded-xl p-2.5 border border-white/5 space-y-1">
          <div className="flex items-center gap-1 text-[11px] text-stone-400">
            <Dumbbell size={12} className="text-red-400" /> Protein
          </div>
          <div className="text-sm font-extrabold text-white">
            {consumed_protein}g{' '}
            <span className="text-[11px] font-normal text-stone-400">/ {target_protein}g</span>
          </div>
          <div className="text-[10px] text-red-400/90 font-medium">
            {remaining_protein}g left
          </div>
        </div>
      </div>
    </div>
  );
}
