import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Camera, Bot, User } from 'lucide-react';

export default function BottomNav() {
  const navItems = [
    { to: '/home', label: 'Home', icon: Home },
    { to: '/snap', label: 'Snap', icon: Camera },
    { to: '/coach', label: 'Coach', icon: Bot },
    { to: '/profile', label: 'Profile', icon: User },
  ];

  return (
    <nav className="w-full shrink-0 pointer-events-auto px-4 pb-3 pt-1">
      <div className="nav-blur border border-white/[0.07] rounded-2xl grid grid-cols-4 py-2 px-1 shadow-2xl">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center py-1 transition-colors duration-150 min-w-0 ${
                isActive
                  ? 'text-[#FF2B3A]'
                  : 'text-[#9297A3] hover:text-[#F5F5F5]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className="relative">
                  <Icon size={20} strokeWidth={isActive ? 2.3 : 1.8} />
                  {isActive && (
                    <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-[#FF2B3A] rounded-full" />
                  )}
                </div>
                <span className="text-[11px] font-medium mt-1 truncate tracking-tight">
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
