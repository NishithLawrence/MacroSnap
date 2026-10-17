import React, { useState } from 'react';
import { Scale, Plus, TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export default function WeightTrend({ weightHistory = [], weightChange = {}, onLogWeight }) {
  const [newWeight, setNewWeight] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const current = weightChange.current;
  const previous = weightChange.previous;
  const diff = weightChange.change_kg;
  const trendStr = weightChange.trend;

  const chartData = (weightHistory || [])
    .filter((entry) => entry && typeof entry.weight_kg === 'number' && entry.weight_kg > 0)
    .map((entry) => {
      let dateLabel = entry.date;
      try {
        const d = new Date(entry.date + 'T00:00:00');
        dateLabel = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } catch (e) {}
      return {
        date: entry.date,
        dateLabel,
        weight: entry.weight_kg,
      };
    });

  const weights = chartData.map((d) => d.weight);
  const minW = weights.length ? Math.floor(Math.min(...weights) - 1) : 60;
  const maxW = weights.length ? Math.ceil(Math.max(...weights) + 1) : 80;

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    const val = parseFloat(newWeight);
    if (isNaN(val) || val <= 0 || val > 300) {
      setErrorMsg('Enter a valid weight in kg');
      return;
    }

    try {
      setSubmitting(true);
      await onLogWeight(val);
      setNewWeight('');
      setIsAdding(false);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to log weight');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-[#12141A]/80 backdrop-blur-md border border-white/[0.07] rounded-2xl p-4 space-y-3.5 min-w-0 shadow-md">
      {/* Header & Title */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#FF2B3A]/10 border border-[#FF2B3A]/20 flex items-center justify-center text-[#FF2B3A]">
            <Scale size={15} />
          </div>
          <div>
            <h2 className="text-xs font-bold text-white tracking-tight">Weight Trend</h2>
            <p className="text-[10px] text-[#9297A3]">Body weight logs</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsAdding(!isAdding)}
          className="px-2.5 py-1 text-[11px] font-semibold text-zinc-200 bg-white/[0.05] border border-white/10 rounded-lg hover:border-white/20 transition-colors flex items-center gap-1 focus:outline-none"
        >
          <Plus size={13} className="text-[#FF2B3A]" />
          Log Weight
        </button>
      </div>

      {/* Inline Log Weight Form */}
      {isAdding && (
        <form onSubmit={handleAddSubmit} className="bg-black/40 p-3 rounded-xl border border-white/10 space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="number"
              step="0.1"
              placeholder="e.g. 74.5"
              value={newWeight}
              onChange={(e) => setNewWeight(e.target.value)}
              className="flex-1 px-3 py-1.5 bg-black/50 border border-white/10 rounded-lg text-xs text-white placeholder-zinc-500 focus:outline-none"
              disabled={submitting}
            />
            <span className="text-xs text-[#9297A3] font-medium">kg</span>
            <button
              type="submit"
              disabled={submitting}
              className="px-3 py-1.5 bg-[#FF2B3A] text-white text-xs font-bold rounded-lg shadow-md hover:bg-[#e02231] transition-colors disabled:opacity-50"
            >
              {submitting ? 'Saving...' : 'Save'}
            </button>
          </div>
          {errorMsg && <p className="text-[10px] text-rose-400">{errorMsg}</p>}
        </form>
      )}

      {/* Weight Summary Cards */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.05]">
          <span className="text-[10px] text-[#9297A3] block font-medium">Current</span>
          <span className="text-xs font-bold text-white mt-0.5 block">
            {current !== null && current !== undefined ? `${current} kg` : '--'}
          </span>
        </div>
        <div className="bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.05]">
          <span className="text-[10px] text-[#9297A3] block font-medium">Previous</span>
          <span className="text-xs font-bold text-zinc-300 mt-0.5 block">
            {previous !== null && previous !== undefined ? `${previous} kg` : '--'}
          </span>
        </div>
        <div className="bg-white/[0.03] p-2.5 rounded-xl border border-white/[0.05]">
          <span className="text-[10px] text-[#9297A3] block font-medium">Change</span>
          <div className="flex items-center justify-center gap-0.5 mt-0.5">
            {diff < 0 ? (
              <TrendingDown size={12} className="text-emerald-400" />
            ) : diff > 0 ? (
              <TrendingUp size={12} className="text-rose-400" />
            ) : (
              <Minus size={12} className="text-[#9297A3]" />
            )}
            <span
              className={`text-xs font-bold ${
                diff < 0 ? 'text-emerald-400' : diff > 0 ? 'text-rose-400' : 'text-zinc-300'
              }`}
            >
              {trendStr || '0 kg'}
            </span>
          </div>
        </div>
      </div>

      {/* Chart */}
      {chartData.length === 0 ? (
        <div className="p-5 text-center bg-black/20 rounded-xl border border-white/[0.05]">
          <p className="text-xs text-[#9297A3]">No weight entries logged yet.</p>
          <p className="text-[10px] text-zinc-500 mt-1">Tap "Log Weight" above to record your baseline weight.</p>
        </div>
      ) : (
        <div className="h-40 w-full pt-1">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 12, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FF2B3A" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#FF2B3A" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="dateLabel" stroke="#626875" fontSize={9} tickLine={false} />
              <YAxis domain={[minW, maxW]} stroke="#626875" fontSize={9} tickLine={false} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-[#111318] border border-white/10 p-2.5 rounded-xl text-[11px] shadow-2xl">
                        <p className="font-bold text-white">{data.date}</p>
                        <p className="text-[#FF2B3A] font-bold">{data.weight} kg</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="monotone"
                dataKey="weight"
                stroke="#FF2B3A"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#weightGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
