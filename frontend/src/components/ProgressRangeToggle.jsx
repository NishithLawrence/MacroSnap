import React from 'react';

export default function ProgressRangeToggle({ selectedRange, onRangeChange }) {
  const options = ['7D', '30D'];

  return (
    <div className="inline-flex items-center p-1 rounded-xl bg-zinc-900/80 border border-white/10 shadow-inner">
      {options.map((opt) => {
        const isActive = selectedRange === opt;
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onRangeChange(opt)}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all duration-150 ${
              isActive
                ? 'bg-[#EF233C] text-white shadow-md shadow-[#EF233C]/30'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
