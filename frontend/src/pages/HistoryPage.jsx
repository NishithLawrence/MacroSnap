import React from 'react';
import { Clock, Calendar, Utensils } from 'lucide-react';

export default function HistoryPage() {
  return (
    <div className="space-y-5 min-w-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Meal History</h1>
          <p className="text-xs text-zinc-400 mt-0.5">Past logged meals and daily summaries</p>
        </div>
        <div className="p-2 rounded-xl bg-zinc-900 border border-white/5 text-zinc-400">
          <Calendar size={18} />
        </div>
      </div>

      <div className="app-card p-6 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-zinc-900 border border-white/5 flex items-center justify-center text-zinc-400 mx-auto">
          <Utensils size={22} />
        </div>
        <h2 className="text-xs font-bold text-zinc-300">History Placeholder</h2>
        <p className="text-[11px] text-zinc-400 max-w-[260px] mx-auto">
          Logged meals, dates, calorie breakdowns, and edit capabilities will be displayed here in Phase 2.
        </p>
      </div>
    </div>
  );
}
