import React from 'react';
import { Bell, User, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RevelationLogo from './RevelationLogo';

export default function AppHeader() {
  const { logout } = useAuth();

  return (
    <header className="h-[60px] px-4 flex items-center justify-between border-b border-white/[0.06] bg-[#08090C]/80 backdrop-blur-md sticky top-0 z-40">
      {/* Brand logo */}
      <Link to="/home" className="flex items-center gap-2 focus:outline-none group">
        <RevelationLogo size={22} className="shrink-0 group-hover:scale-105 transition-transform" />
        <span className="font-extrabold text-[17px] tracking-tight text-[#F5F5F5]">
          REVEL<span className="text-[#FF2B3A]">ATION</span>
        </span>
      </Link>

      {/* Action Icons */}
      <div className="flex items-center gap-2.5">
        <button
          type="button"
          onClick={logout}
          className="w-9 h-9 rounded-full bg-[#171A20]/80 border border-white/[0.08] text-[#9297A3] hover:text-[#EF233C] flex items-center justify-center transition-colors focus:outline-none"
          title="End Reviewer Demo Session (Log Out)"
        >
          <LogOut size={16} />
        </button>
        <button
          type="button"
          className="w-9 h-9 rounded-full bg-[#171A20]/80 border border-white/[0.08] text-[#9297A3] hover:text-[#F5F5F5] flex items-center justify-center transition-colors focus:outline-none"
          title="Notifications"
        >
          <Bell size={17} />
        </button>
        <Link
          to="/profile"
          className="w-9 h-9 rounded-full bg-[#171A20]/80 border border-white/[0.08] text-[#9297A3] hover:text-[#F5F5F5] flex items-center justify-center transition-colors focus:outline-none"
          title="Profile"
        >
          <User size={17} />
        </Link>
      </div>
    </header>
  );
}
