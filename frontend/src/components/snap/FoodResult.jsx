import React from 'react';
import { X } from 'lucide-react';

export default function FoodResult({ food, index, onChange, onDelete }) {
  const handleFieldChange = (field, value) => {
    let parsed = value;
    if (['calories', 'protein_g', 'carbs_g', 'fat_g'].includes(field)) {
      parsed = Math.max(0, parseInt(value, 10) || 0);
    }
    onChange(index, { ...food, [field]: parsed });
  };

  const confidenceColor =
    food.confidence === 'high'
      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
      : food.confidence === 'low'
      ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
      : 'bg-amber-500/15 text-amber-400 border-amber-500/30';

  return (
    <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[16px] p-3.5 space-y-3 shadow-lg relative min-w-0">
      {/* Header: Name + Portion + Confidence + Remove Button */}
      <div className="flex items-start justify-between gap-2 min-w-0">
        <div className="flex-1 space-y-1 min-w-0">
          <input
            type="text"
            value={food.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            className="w-full bg-transparent font-bold text-[14px] text-[#F5F5F5] outline-none border-b border-transparent focus:border-[#FF2B3A] transition-colors truncate"
            placeholder="Food name"
          />
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={food.portion}
              onChange={(e) => handleFieldChange('portion', e.target.value)}
              className="text-[12px] text-[#9297A3] bg-transparent outline-none border-b border-transparent focus:border-[#FF2B3A] w-28"
              placeholder="Portion (e.g. 200g)"
            />
            {food.confidence && (
              <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold border uppercase tracking-wider ${confidenceColor}`}>
                {food.confidence}
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={() => onDelete(index)}
          className="w-7 h-7 rounded-lg bg-zinc-800/60 hover:bg-rose-500/20 text-zinc-400 hover:text-rose-400 flex items-center justify-center transition-colors shrink-0"
          title="Remove item"
        >
          <X size={15} />
        </button>
      </div>

      {/* Macro Grid Inputs */}
      <div className="grid grid-cols-4 gap-2 pt-1 border-t border-white/[0.05] text-center">
        <div>
          <label className="text-[9px] font-bold uppercase text-[#9297A3] block mb-0.5">Calories</label>
          <input
            type="number"
            value={food.calories}
            onChange={(e) => handleFieldChange('calories', e.target.value)}
            className="w-full bg-[#171A20] border border-white/5 rounded-lg py-1 px-1 text-center font-bold text-[12px] text-[#F5F5F5] outline-none focus:border-[#FF2B3A]"
          />
        </div>
        <div>
          <label className="text-[9px] font-bold uppercase text-[#9297A3] block mb-0.5">Protein</label>
          <input
            type="number"
            value={food.protein_g}
            onChange={(e) => handleFieldChange('protein_g', e.target.value)}
            className="w-full bg-[#171A20] border border-white/5 rounded-lg py-1 px-1 text-center font-semibold text-[12px] text-[#F5F5F5] outline-none focus:border-[#FF2B3A]"
          />
        </div>
        <div>
          <label className="text-[9px] font-bold uppercase text-[#9297A3] block mb-0.5">Carbs</label>
          <input
            type="number"
            value={food.carbs_g}
            onChange={(e) => handleFieldChange('carbs_g', e.target.value)}
            className="w-full bg-[#171A20] border border-white/5 rounded-lg py-1 px-1 text-center font-semibold text-[12px] text-[#F5F5F5] outline-none focus:border-[#FF2B3A]"
          />
        </div>
        <div>
          <label className="text-[9px] font-bold uppercase text-[#9297A3] block mb-0.5">Fat</label>
          <input
            type="number"
            value={food.fat_g}
            onChange={(e) => handleFieldChange('fat_g', e.target.value)}
            className="w-full bg-[#171A20] border border-white/5 rounded-lg py-1 px-1 text-center font-semibold text-[12px] text-[#F5F5F5] outline-none focus:border-[#FF2B3A]"
          />
        </div>
      </div>
    </div>
  );
}
