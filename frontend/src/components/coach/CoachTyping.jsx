import React from 'react';
import { Bot } from 'lucide-react';

export default function CoachTyping() {
  return (
    <div className="flex items-start gap-2.5 my-2.5 pr-4 min-w-0">
      <div className="w-8 h-8 rounded-xl bg-red-600/20 border border-red-500/30 text-red-400 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
        <Bot size={16} />
      </div>
      <div className="bg-stone-900/80 backdrop-blur-md border border-white/10 text-stone-300 rounded-2xl rounded-tl-sm px-4 py-3 text-xs sm:text-sm shadow-lg flex items-center gap-2">
        <span className="font-medium text-stone-300">Coach is thinking</span>
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-bounce [animation-delay:-0.3s]"></span>
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-bounce [animation-delay:-0.15s]"></span>
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-bounce"></span>
        </span>
      </div>
    </div>
  );
}
