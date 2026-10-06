import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Clock, TrendingUp } from 'lucide-react';
import { getHealth } from '../lib/api';

export default function Header() {
  const [apiStatus, setApiStatus] = useState('checking');
  const location = useLocation();

  useEffect(() => {
    getHealth()
      ? setApiStatus('online')
      : setApiStatus('offline');
    getHealth()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-[#0A0A0E]/90 backdrop-blur-md border-b border-white/5 px-4 py-3.5 flex items-center justify-between">
      {/* Brand Logo */}
      <Link to="/home" className="flex items-center gap-2 group">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#EF233C] to-[#9D0208] flex items-center justify-center shadow-lg shadow-[#EF233C]/20">
          <span className="font-extrabold text-white text-sm tracking-tighter">MS</span>
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-base tracking-tight text-white leading-none">
            Macro<span className="text-[#EF233C]">Snap</span>
          </span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className={`w-1.5 h-1.5 rounded-full ${apiStatus === 'online' ? 'bg-emerald-500 animate-pulse' : apiStatus === 'offline' ? 'bg-rose-500' : 'bg-amber-500'}`} />
            <span className="text-[10px] text-zinc-400 font-mono uppercase tracking-wider">
              {apiStatus === 'online' ? 'API Online' : apiStatus === 'offline' ? 'API Offline' : 'Connecting'}
            </span>
          </div>
        </div>
      </Link>

      {/* Quick navigation icons for History & Progress */}
      <div className="flex items-center gap-2">
        <Link
          to="/history"
          className={`p-2 rounded-xl border transition-colors ${
            location.pathname === '/history'
              ? 'bg-[#EF233C]/10 border-[#EF233C]/40 text-[#EF233C]'
              : 'bg-zinc-900/60 border-white/5 text-zinc-400 hover:text-zinc-200'
          }`}
          title="History"
        >
          <Clock size={18} />
        </Link>
        <Link
          to="/progress"
          className={`p-2 rounded-xl border transition-colors ${
            location.pathname === '/progress'
              ? 'bg-[#EF233C]/10 border-[#EF233C]/40 text-[#EF233C]'
              : 'bg-zinc-900/60 border-white/5 text-zinc-400 hover:text-zinc-200'
          }`}
          title="Progress"
        >
          <TrendingUp size={18} />
        </Link>
      </div>
    </header>
  );
}
