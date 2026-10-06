import React, { useEffect, useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';

const SCAN_STEPS = [
  'Scanning food items...',
  'Estimating portions...',
  'Calculating nutrition...',
];

export default function ScanProgress({ imageSrc }) {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % SCAN_STEPS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4 min-w-0">
      <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[20px] p-4 text-center space-y-4 shadow-2xl relative overflow-hidden">
        {/* Image Preview with Scanning Overlay */}
        <div className="relative w-full max-h-[260px] rounded-xl overflow-hidden border border-white/10 bg-black/50">
          <img
            src={imageSrc}
            alt="Meal Scanning"
            className="w-full h-full max-h-[260px] object-cover opacity-60"
          />
          {/* Animated Scanning Beam Line */}
          <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-[#FF2B3A] to-transparent animate-pulse shadow-lg shadow-[#FF2B3A] top-1/2 -translate-y-1/2" />
        </div>

        {/* Progress Text */}
        <div className="space-y-2 py-1">
          <div className="flex items-center justify-center gap-2 text-[#FF2B3A]">
            <Loader2 size={18} className="animate-spin" />
            <h3 className="text-[15px] font-bold text-[#F5F5F5] tracking-tight">
              ANALYZING YOUR MEAL
            </h3>
          </div>
          <p className="text-[13px] text-[#9297A3] font-mono h-5">
            {SCAN_STEPS[stepIndex]}
          </p>
        </div>
      </div>
    </div>
  );
}
