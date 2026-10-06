import React from 'react';
import { Camera, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function PrimaryAction({ onQuickAdd }) {
  return (
    <div className="space-y-2 text-center">
      {/* Primary Dominant Button */}
      <Link
        to="/snap"
        className="w-full h-[52px] bg-[#FF2B3A] hover:bg-[#E02231] active:scale-[0.99] text-white font-bold text-[14px] tracking-wide rounded-[16px] shadow-lg shadow-[#FF2B3A]/20 transition-all duration-150 flex items-center justify-center gap-2 focus:outline-none"
      >
        <Camera size={19} strokeWidth={2.2} />
        <span>+ LOG YOUR MEAL</span>
      </Link>

      {/* Subtle Secondary Action */}
      <button
        type="button"
        onClick={onQuickAdd}
        className="inline-flex items-center gap-1.5 text-[13px] text-[#9297A3] hover:text-[#F5F5F5] font-medium py-1.5 px-3 rounded-lg transition-colors focus:outline-none"
      >
        <Plus size={14} />
        <span>Quick Add</span>
      </button>
    </div>
  );
}
