import React from 'react';
import { Calendar } from 'lucide-react';
import DailyTotals from './DailyTotals';
import HistoryMealRow from './HistoryMealRow';

export default function HistoryDateGroup({ dateGroup, onEditMeal, onDeleteMeal }) {
  const { date, date_formatted, totals, meals } = dateGroup;

  // Categorize meals by meal_type: Breakfast, Lunch, Dinner, Snack
  const categories = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

  // Only show categories that have meals
  const groupedMeals = categories.reduce((acc, cat) => {
    const catMeals = (meals || []).filter((m) => (m.meal_type || 'Lunch') === cat);
    if (catMeals.length > 0) {
      acc[cat] = catMeals;
    }
    return acc;
  }, {});

  return (
    <div className="bg-[#12141A]/92 border border-white/[0.09] rounded-2xl p-4 space-y-3.5 min-w-0 shadow-lg backdrop-blur-sm">
      {/* Date Header & Totals */}
      <div className="flex flex-col gap-2 border-b border-white/[0.08] pb-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-zinc-900/90 border border-white/10 text-zinc-300">
              <Calendar size={15} />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white tracking-tight">{date_formatted || date}</h2>
              <span className="text-[10px] text-zinc-400">{(meals || []).length} meals logged</span>
            </div>
          </div>

          <DailyTotals totals={totals} />
        </div>
      </div>

      {/* Meal Groups inside Date */}
      <div className="space-y-3 pt-0.5">
        {Object.entries(groupedMeals).map(([catName, catMeals]) => (
          <div key={catName} className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-wider">
                {catName}
              </span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            <div className="space-y-2">
              {catMeals.map((meal) => (
                <HistoryMealRow
                  key={meal.meal_id}
                  meal={meal}
                  onEdit={onEditMeal}
                  onDelete={onDeleteMeal}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

