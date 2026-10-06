import React from 'react';
import { TrendingUp, BarChart2 } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

const dummyData = [
  { day: 'Mon', weight: 75.2 },
  { day: 'Tue', weight: 75.0 },
  { day: 'Wed', weight: 74.8 },
  { day: 'Thu', weight: 74.9 },
  { day: 'Fri', weight: 74.5 },
  { day: 'Sat', weight: 74.3 },
  { day: 'Sun', weight: 74.2 },
];

export default function ProgressPage() {
  return (
    <div className="space-y-5 min-w-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Progress & Trends</h1>
          <p className="text-xs text-zinc-400 mt-0.5">Weight logs and calorie consistency</p>
        </div>
        <div className="p-2 rounded-xl bg-zinc-900 border border-white/5 text-[#EF233C]">
          <TrendingUp size={18} />
        </div>
      </div>

      {/* Recharts Chart Placeholder */}
      <div className="app-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-white flex items-center gap-1.5">
            <BarChart2 size={15} className="text-[#EF233C]" />
            Weight Trend (7 Days)
          </h2>
          <span className="text-[10px] text-emerald-400 font-semibold">-1.0 kg</span>
        </div>

        <div className="h-44 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dummyData}>
              <defs>
                <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#EF233C" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#EF233C" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="#5a5a66" fontSize={10} tickLine={false} />
              <YAxis domain={['dataMin - 1', 'dataMax + 1']} hide />
              <Tooltip
                contentStyle={{ backgroundColor: '#13131A', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '11px' }}
                itemStyle={{ color: '#EF233C' }}
              />
              <Area type="monotone" dataKey="weight" stroke="#EF233C" strokeWidth={2} fillOpacity={1} fill="url(#weightGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
