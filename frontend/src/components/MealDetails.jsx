import React from 'react';
import { Utensils } from 'lucide-react';

export default function MealDetails({ foods = [] }) {
  if (!foods || foods.length === 0) {
    return (
      <div className="p-3 text-[11px] text-zinc-500 italic bg-black/30 rounded-xl">
        No food items specified for this meal.
      </div>
    );
  }

  return (
    <div className="bg-black/40 rounded-xl p-3 border border-white/5 space-y-2 text-xs">
      <div className="flex items-center gap-1.5 text-[10px] text-zinc-400 font-bold uppercase tracking-wider">
        <Utensils size={12} className="text-[#EF233C]" />
        <span>Food Breakdown ({foods.length} items)</span>
      </div>

      <div className="divide-y divide-white/5">
        {foods.map((item, idx) => (
          <div key={item.id || idx} className="py-2 flex items-center justify-between gap-2">
            <div className="min-w-0">
              <span className="font-medium text-zinc-200 block truncate">{item.name}</span>
              {item.portion && (
                <span className="text-[10px] text-zinc-400 block truncate">{item.portion}</span>
              )}
            </div>

            <div className="text-right shrink-0 text-[10px] space-x-1.5 font-mono">
              <span className="font-bold text-white">{item.calories || 0} kcal</span>
              <span className="text-sky-400">P:{item.protein_g || 0}g</span>
              <span className="text-amber-400">C:{item.carbs_g || 0}g</span>
              <span className="text-rose-400">F:{item.fat_g || 0}g</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
