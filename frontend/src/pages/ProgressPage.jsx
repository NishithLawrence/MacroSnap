import React, { useEffect, useState } from 'react';
import { TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import { getProgressAnalytics, logWeight } from '../lib/api';
import ProgressRangeToggle from '../components/ProgressRangeToggle';
import ConsistencyScore from '../components/ConsistencyScore';
import CalorieTrend from '../components/CalorieTrend';
import ProteinTrend from '../components/ProteinTrend';
import WeightTrend from '../components/WeightTrend';
import GoalInsight from '../components/GoalInsight';

export default function ProgressPage() {
  const [selectedRange, setSelectedRange] = useState('7D');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const daysPeriod = selectedRange === '30D' ? 30 : 7;

  const fetchAnalytics = async (days) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProgressAnalytics(days);
      setData(res);
    } catch (err) {
      console.error('Failed to load progress analytics:', err);
      setError(err.message || 'Unable to load progress analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(daysPeriod);
  }, [selectedRange]);

  const handleLogWeight = async (weightKg) => {
    await logWeight(weightKg);
    // Refresh analytics after weight update
    fetchAnalytics(daysPeriod);
  };

  return (
    <div className="space-y-5 min-w-0 pb-6">
      {/* Top Bar Header */}
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Progress & Analytics</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">Adherence, trends & macro consistency</p>
        </div>
        <ProgressRangeToggle
          selectedRange={selectedRange}
          onRangeChange={(r) => setSelectedRange(r)}
        />
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => fetchAnalytics(daysPeriod)}
            className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-semibold rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton / Spinner */}
      {loading && !data && (
        <div className="app-card p-8 text-center space-y-3">
          <RefreshCw size={24} className="animate-spin text-[#EF233C] mx-auto" />
          <p className="text-xs font-semibold text-zinc-400">Fetching {selectedRange} analytics...</p>
        </div>
      )}

      {/* Analytics Content */}
      {data && (
        <div className="space-y-4">
          <ConsistencyScore scorePct={data.consistency_pct} />

          <CalorieTrend
            historyRecords={data.history}
            averages={data.averages}
            calAdherence={data.cal_adherence}
            targetCalories={data.targets?.calories || 2000}
          />

          <ProteinTrend
            historyRecords={data.history}
            averages={data.averages}
            pAdherence={data.p_adherence}
            targetProtein={data.targets?.protein || 150}
          />

          <WeightTrend
            weightHistory={data.weight_history}
            weightChange={data.weight_change}
            onLogWeight={handleLogWeight}
          />

          <GoalInsight
            goal={data.goal}
            interpretation={data.interpretation}
          />
        </div>
      )}
    </div>
  );
}
