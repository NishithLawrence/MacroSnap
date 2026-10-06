import React from 'react';

const QUICK_PROMPTS = [
  { label: '🍗 High Protein Meal', prompt: 'Give me a high-protein meal' },
  { label: '📊 Am I On Track?', prompt: 'Am I on track today?' },
  { label: '🥗 Under 500 Calories', prompt: 'Give me something under 500 calories' },
  { label: '💡 What Should I Eat?', prompt: 'What should I eat next?' },
  { label: '🔥 Dinner Idea', prompt: 'Suggest a dinner for me' },
  { label: '💪 Protein Left', prompt: 'How much protein do I have left?' },
];

export default function QuickActions({ onSelectPrompt, disabled }) {
  return (
    <div className="space-y-2 min-w-0">
      <div className="text-[11px] font-bold uppercase tracking-wider text-stone-400 px-0.5">
        Quick Actions
      </div>
      <div className="grid grid-cols-2 gap-2">
        {QUICK_PROMPTS.map((item, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectPrompt(item.prompt)}
            disabled={disabled}
            className="bg-stone-900/50 hover:bg-stone-800/80 active:scale-[0.98] border border-white/10 text-stone-200 text-xs font-medium px-3 py-2.5 rounded-xl text-left transition-all flex items-center justify-between min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            <span className="truncate">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
