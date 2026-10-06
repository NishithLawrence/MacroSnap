import React from 'react';
import { Info } from 'lucide-react';

export default function MealDisclaimer() {
  return (
    <div className="flex items-start gap-2 p-3 rounded-xl bg-zinc-900/40 border border-white/[0.04] text-[11px] text-[#9297A3] leading-relaxed">
      <Info size={14} className="shrink-0 text-zinc-500 mt-0.5" />
      <p>
        Nutrition values are AI-generated estimates based on visible food and estimated portions. Actual values can vary depending on ingredients and preparation method.
      </p>
    </div>
  );
}
