import React from 'react';

export default function MacroSummary({
  protein = { current: 82, target: 144 },
  carbs = { current: 180, target: 302 },
  fat = { current: 42, target: 66 }
}) {
  const macros = [
    { label: 'PROTEIN', current: protein.current, target: protein.target, unit: 'g' },
    { label: 'CARBS', current: carbs.current, target: carbs.target, unit: 'g' },
    { label: 'FAT', current: fat.current, target: fat.target, unit: 'g' },
  ];

  return (
    <div className="grid grid-cols-3 gap-2 sm:gap-3 min-w-0">
      {macros.map((m) => {
        const percent = Math.min(100, Math.round((m.current / (m.target || 1)) * 100));
        return (
          <div
            key={m.label}
            className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[16px] p-3 flex flex-col justify-between space-y-2 min-w-0 shadow-lg"
          >
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#9297A3] block truncate">
                {m.label}
              </span>
              <div className="text-[12px] sm:text-[13px] font-bold text-[#F5F5F5] mt-1 tracking-tight truncate">
                {m.current} <span className="text-[#9297A3] font-normal text-[11px]">/ {m.target}{m.unit}</span>
              </div>
            </div>

            {/* Subtle Progress Bar */}
            <div className="w-full h-1.5 bg-[#171A20]/90 rounded-full overflow-hidden border border-white/[0.04]">
              <div
                className="h-full bg-[#FF2B3A] rounded-full transition-all duration-300"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
