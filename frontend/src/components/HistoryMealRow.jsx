import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Edit2, Trash2, Coffee, Sun, Moon, Cookie } from 'lucide-react';
import MealDetails from './MealDetails';

const MEAL_ICONS = {
  Breakfast: Coffee,
  Lunch: Sun,
  Dinner: Moon,
  Snack: Cookie,
};

const MEAL_COLORS = {
  Breakfast: 'text-amber-400 bg-amber-400/10 border-amber-400/25',
  Lunch: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/25',
  Dinner: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/25',
  Snack: 'text-rose-400 bg-rose-400/10 border-rose-400/25',
};

export default function HistoryMealRow({ meal, onEdit, onDelete }) {
  const [expanded, setExpanded] = useState(false);

  const mealType = meal.meal_type || 'Lunch';
  const IconComponent = MEAL_ICONS[mealType] || Sun;
  const colorClasses = MEAL_COLORS[mealType] || MEAL_COLORS.Lunch;

  let timeStr = 'Logged Meal';
  if (meal.timestamp) {
    try {
      const d = new Date(meal.timestamp);
      timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      timeStr = meal.timestamp;
    }
  }

  const totals = meal.total || {
    calories: meal.calories || 0,
    protein_g: meal.protein || 0,
    carbs_g: meal.carbs || 0,
    fat_g: meal.fat || 0,
  };

  const foodCount = (meal.foods || []).length;
  const mainFoodName = meal.foods && meal.foods.length ? meal.foods[0].name : meal.name || 'Meal item';

  return (
    <div className="bg-[#151722]/95 border border-white/[0.10] rounded-xl p-3.5 space-y-3 transition-all hover:border-white/20 shadow-sm">
      {/* Header Row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className={`p-2 rounded-xl border ${colorClasses} shrink-0`}>
            <IconComponent size={16} />
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-tight">{mealType}</span>
              <span className="text-[10px] text-zinc-400 font-mono">{timeStr}</span>
            </div>
            <p className="text-[11px] text-zinc-200 truncate mt-0.5 font-medium">
              {mainFoodName} {foodCount > 1 ? `+ ${foodCount - 1} more` : ''}
            </p>
          </div>
        </div>

        {/* Macro Pill & Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          <div className="text-right">
            <span className="text-xs font-extrabold text-[#FF2B3A] block">{totals.calories} kcal</span>
            <span className="text-[10px] text-sky-400 font-bold block">P: {totals.protein_g}g</span>
          </div>

          <div className="flex items-center gap-1 pl-1.5 border-l border-white/[0.10]">
            <button
              type="button"
              onClick={() => onEdit(meal)}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors focus:outline-none"
              title="Edit Meal"
            >
              <Edit2 size={14} />
            </button>
            <button
              type="button"
              onClick={() => onDelete(meal)}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors focus:outline-none"
              title="Delete Meal"
            >
              <Trash2 size={14} />
            </button>
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors focus:outline-none"
              title={expanded ? 'Collapse' : 'Expand'}
            >
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Food Details */}
      {expanded && (
        <div className="pt-2 border-t border-white/[0.08]">
          <MealDetails foods={meal.foods} />
        </div>
      )}
    </div>
  );
}

