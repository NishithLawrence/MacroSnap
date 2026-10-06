import React from 'react';
import { Utensils } from 'lucide-react';

export default function MealList({ meals = [] }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-[16px] font-semibold text-[#F5F5F5] tracking-tight">
          Today's meals
        </h2>
        {meals.length > 0 && (
          <span className="text-[12px] text-[#9297A3] font-medium">
            {meals.length} {meals.length === 1 ? 'item' : 'items'}
          </span>
        )}
      </div>

      {meals.length === 0 ? (
        /* Empty State */
        <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[16px] p-5 text-center space-y-2 shadow-lg">
          <div className="w-10 h-10 rounded-full bg-[#171A20] text-[#9297A3] flex items-center justify-center mx-auto">
            <Utensils size={18} />
          </div>
          <div>
            <h3 className="text-[14px] font-semibold text-[#F5F5F5]">
              No meals logged yet
            </h3>
            <p className="text-[12px] text-[#9297A3] mt-0.5">
              Start by snapping your first meal.
            </p>
          </div>
        </div>
      ) : (
        /* Meals List with Translucent Surface & Subtle Dividers */
        <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[16px] divide-y divide-white/[0.05] overflow-hidden shadow-lg">
          {meals.map((meal, idx) => (
            <div
              key={meal.id || idx}
              className="p-3.5 flex items-center justify-between hover:bg-white/[0.03] transition-colors"
            >
              <div className="space-y-0.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-[#9297A3] block">
                  {meal.meal_type || 'Meal'}
                </span>
                <h4 className="text-[14px] font-medium text-[#F5F5F5]">
                  {meal.name}
                </h4>
              </div>

              <div className="text-right">
                <span className="text-[14px] font-bold text-[#F5F5F5]">
                  {meal.calories} <span className="text-[11px] font-normal text-[#9297A3]">kcal</span>
                </span>
                {meal.protein ? (
                  <span className="block text-[11px] text-[#9297A3]">
                    {meal.protein}g protein
                  </span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
