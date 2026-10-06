import React from 'react';
import { Send } from 'lucide-react';

export default function ChatComposer({ value, onChange, onSubmit, disabled }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value || !value.trim() || disabled) return;
    onSubmit(value);
  };

  return (
    <form onSubmit={handleSubmit} className="relative min-w-0">
      <div className="bg-stone-900/90 backdrop-blur-md border border-white/15 rounded-2xl p-1.5 flex items-center gap-2 shadow-2xl">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ask your Coach..."
          disabled={disabled}
          className="flex-1 bg-transparent text-xs sm:text-sm text-white placeholder-stone-400 outline-none px-3 min-w-0 py-2.5 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!value || !value.trim() || disabled}
          className="bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white p-2.5 rounded-xl font-bold flex items-center justify-center active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 min-h-[42px] min-w-[42px]"
          aria-label="Send message"
        >
          <Send size={16} />
        </button>
      </div>
    </form>
  );
}
