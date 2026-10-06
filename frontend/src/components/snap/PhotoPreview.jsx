import React from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';

export default function PhotoPreview({ imageSrc, onRetake, onAnalyze }) {
  return (
    <div className="space-y-4 min-w-0">
      {/* Image Preview Container */}
      <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[20px] p-3 shadow-2xl relative overflow-hidden">
        <div className="w-full max-h-[280px] rounded-xl overflow-hidden bg-black/40 border border-white/5 flex items-center justify-center">
          <img
            src={imageSrc}
            alt="Selected Meal Preview"
            className="w-full h-full max-h-[280px] object-cover rounded-xl"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-2 text-center">
        <button
          type="button"
          onClick={onAnalyze}
          className="w-full h-[52px] bg-[#FF2B3A] hover:bg-[#E02231] active:scale-[0.99] text-white font-bold text-[14px] tracking-wide rounded-[16px] shadow-lg shadow-[#FF2B3A]/25 transition-all duration-150 flex items-center justify-center gap-2 focus:outline-none"
        >
          <Sparkles size={19} strokeWidth={2.2} />
          <span>ANALYZE MEAL</span>
        </button>

        <button
          type="button"
          onClick={onRetake}
          className="inline-flex items-center gap-1.5 text-[13px] text-[#9297A3] hover:text-[#F5F5F5] font-medium py-1.5 px-3 transition-colors focus:outline-none"
        >
          <RefreshCw size={14} />
          <span>Retake photo</span>
        </button>
      </div>
    </div>
  );
}
