import React from 'react';
import { Flame, Info } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine } from 'recharts';

export default function CalorieTrend({ historyRecords = [], averages = {}, calAdherence = {}, targetCalories = 2000 }) {
  const avgCals = averages.avg_calories || 0;
  const trackedCount = averages.tracked_days || 0;
  const totalDays = averages.total_days || historyRecords.length || 7;
  const adherencePct = calAdherence.adherence_pct || 0;

  // Chart data mapping (untracked days are null so line doesn't drop to 0)
  const chartData = historyRecords.map((r) => ({
    date: r.date_formatted || r.date,
    dayName: r.day_name || r.date,
    calories: r.tracked ? r.calories : null,
    target: r.target_calories || targetCalories,
    tracked: r.tracked,
  }));

  // Smart Y-Axis domain calculation so intake line isn't squished flat
  const trackedValues = chartData
    .filter((d) => d.tracked && typeof d.calories === 'number' && d.calories > 0)
    .map((d) => d.calories);

  let minY = 0;
  let maxY = Math.ceil((targetCalories * 1.15) / 100) * 100;

  if (trackedValues.length > 0) {
    const minVal = Math.min(...trackedValues, targetCalories);
    const maxVal = Math.max(...trackedValues, targetCalories);
    const range = maxVal - minVal;
    const padding = Math.max(120, Math.round(range * 0.25));
    minY = Math.max(0, Math.floor((minVal - padding) / 100) * 100);
    maxY = Math.ceil((maxVal + padding) / 100) * 100;
  }

  return (
    <div className="bg-[#12141A]/80 backdrop-blur-md border border-white/[0.07] rounded-2xl p-4 space-y-3.5 min-w-0 shadow-md">
      {/* Header & Title */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#FF2B3A]/10 border border-[#FF2B3A]/20 flex items-center justify-center text-[#FF2B3A]">
            <Flame size={15} />
          </div>
          <div>
            <h2 className="text-xs font-bold text-white tracking-tight">Calorie Adherence & Trend</h2>
            <p className="text-[10px] text-[#9297A3]">Intake vs daily target</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs font-extrabold text-[#F5F5F5] block">{adherencePct}%</span>
          <span className="text-[10px] text-emerald-400 font-medium">On Target</span>
        </div>
      </div>

      {/* Metrics Row — Explicit Data Clarity */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.05]">
          <span className="text-[10px] text-[#9297A3] block font-medium">Daily Target</span>
          <span className="text-xs font-bold text-white mt-0.5 block">{targetCalories.toLocaleString()} kcal</span>
        </div>
        <div className="bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.05]">
          <span className="text-[10px] text-[#9297A3] block font-medium">Avg Tracked Intake</span>
          <span className="text-xs font-bold text-[#FF2B3A] mt-0.5 block">
            {avgCals > 0 ? `${avgCals.toLocaleString()} kcal` : '--'}
          </span>
        </div>
        <div className="bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.05]">
          <span className="text-[10px] text-[#9297A3] block font-medium">Tracked Days</span>
          <span className="text-xs font-bold text-zinc-200 mt-0.5 block">
            {trackedCount} / {totalDays} days
          </span>
        </div>
      </div>

      {/* Recharts Chart — Scaled & Legible */}
      <div className="h-44 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 16, right: 10, left: -22, bottom: 0 }}>
            <defs>
              <linearGradient id="calorieGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FF2B3A" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#FF2B3A" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="dayName" stroke="#626875" fontSize={9} tickLine={false} />
            <YAxis domain={[minY, maxY]} stroke="#626875" fontSize={9} tickLine={false} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-[#111318] border border-white/10 p-2.5 rounded-xl text-[11px] shadow-2xl space-y-1">
                      <p className="font-bold text-white">{data.date}</p>
                      {data.tracked && data.calories !== null ? (
                        <p className="text-[#FF2B3A] font-bold">{data.calories} kcal</p>
                      ) : (
                        <p className="text-zinc-400 italic">No entry (Untracked)</p>
                      )}
                      <p className="text-[#9297A3] text-[10px]">Target: {data.target} kcal</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine
              y={targetCalories}
              stroke="#FF2B3A"
              strokeDasharray="4 4"
              strokeOpacity={0.75}
              label={{
                value: `Target: ${targetCalories} kcal`,
                fill: '#FF2B3A',
                fontSize: 9,
                position: 'top',
                offset: 4,
                fontWeight: 600,
              }}
            />
            <Area
              type="monotone"
              dataKey="calories"
              stroke="#FF2B3A"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#calorieGrad)"
              connectNulls={true}
              dot={(props) => {
                const { cx, cy, payload } = props;
                if (payload && payload.tracked && typeof payload.calories === 'number' && payload.calories > 0) {
                  return (
                    <circle
                      key={`dot-${cx}-${cy}`}
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill="#FF2B3A"
                      stroke="#FFFFFF"
                      strokeWidth={1.5}
                    />
                  );
                }
                return null;
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Explanatory Data Clarity Subtext */}
      <div className="flex items-center gap-1.5 pt-1 text-[10px] text-[#9297A3]">
        <Info size={12} className="shrink-0 text-zinc-400" />
        <span>
          Average intake calculated over {trackedCount} tracked day{trackedCount === 1 ? '' : 's'} (untracked days excluded from average).
        </span>
      </div>
    </div>
  );
}

