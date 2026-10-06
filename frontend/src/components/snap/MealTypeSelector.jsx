import React from 'react';

const MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

export default function MealTypeSelector({ selected = 'Lunch', onChange }) {
  return (
    <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] p-1 rounded-2xl flex items-center justify-between gap-1 min-w-0 shadow-lg">
      {MEAL_TYPES.map((type) => {
        const isActive = selected === type;
        return (
          <button
            key={type}
            type="button"
            onClick={() => onChange(type)}
            className={`flex-1 py-2 px-1 text-[12px] font-semibold rounded-xl transition-all duration-150 truncate focus:outline-none ${
              isActive
                ? 'bg-[#FF2B3A] text-white shadow-md shadow-[#FF2B3A]/25'
                : 'text-[#9297A3] hover:text-[#F5F5F5] hover:bg-white/[0.04]'
            }`}
          >
            {type}
          </button>
        );
      })}
    </div>
  );
}
