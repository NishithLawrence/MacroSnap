import React from 'react';
import { User, Target, Scale, Settings, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ProfilePage() {
  return (
    <div className="space-y-5 min-w-0">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-zinc-800 to-zinc-900 border border-white/10 flex items-center justify-center text-white font-bold text-lg">
          <User size={24} className="text-[#EF233C]" />
        </div>
        <div>
          <h1 className="text-base font-bold text-white tracking-tight">User Profile</h1>
          <p className="text-xs text-zinc-400">Target Macros & Physical Stats</p>
        </div>
      </div>

      {/* Target Macros Card */}
      <div className="app-card p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <div className="flex items-center gap-2">
            <Target size={16} className="text-[#EF233C]" />
            <h2 className="text-xs font-bold text-white">Current Daily Targets</h2>
          </div>
          <span className="text-[10px] text-zinc-400">Default Target</span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-zinc-900/50 p-2.5 rounded-xl border border-white/5">
            <span className="text-zinc-400 text-[10px] block">Daily Calories</span>
            <span className="text-sm font-bold text-white mt-0.5 block">2,000 kcal</span>
          </div>
          <div className="bg-zinc-900/50 p-2.5 rounded-xl border border-white/5">
            <span className="text-zinc-400 text-[10px] block">Protein</span>
            <span className="text-sm font-bold text-white mt-0.5 block">150 g</span>
          </div>
          <div className="bg-zinc-900/50 p-2.5 rounded-xl border border-white/5">
            <span className="text-zinc-400 text-[10px] block">Carbs</span>
            <span className="text-sm font-bold text-white mt-0.5 block">200 g</span>
          </div>
          <div className="bg-zinc-900/50 p-2.5 rounded-xl border border-white/5">
            <span className="text-zinc-400 text-[10px] block">Fats</span>
            <span className="text-sm font-bold text-white mt-0.5 block">65 g</span>
          </div>
        </div>
      </div>

      {/* Profile Actions */}
      <div className="app-card divide-y divide-white/5 overflow-hidden">
        <Link to="/progress" className="p-3.5 flex items-center justify-between hover:bg-zinc-900/40 transition-colors">
          <div className="flex items-center gap-3">
            <Scale size={18} className="text-zinc-400" />
            <span className="text-xs font-semibold text-zinc-200">Weight & Analytics</span>
          </div>
          <ChevronRight size={16} className="text-zinc-500" />
        </Link>
        <Link to="/onboarding" className="p-3.5 flex items-center justify-between hover:bg-zinc-900/40 transition-colors">
          <div className="flex items-center gap-3">
            <Settings size={18} className="text-zinc-400" />
            <span className="text-xs font-semibold text-zinc-200">Re-run Onboarding</span>
          </div>
          <ChevronRight size={16} className="text-zinc-500" />
        </Link>
      </div>
    </div>
  );
}
